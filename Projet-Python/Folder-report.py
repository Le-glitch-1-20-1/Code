#!/usr/bin/env python3
"""Scan disk partitions and generate an HTML file report using Template/."""
import argparse
import gzip
import io
import json
import os
import shutil
import sys
import time
import psutil
from abc			import ABC, abstractmethod
from datetime		import datetime
from typing			import Any

if sys.stdout.encoding.lower() != "utf-8":
	sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ============================================================================
# DISPLAY
# By default the script only uses print() and input() (ConsoleDisplay class).
# If the file "display_layer.py" is next to the script, it is loaded
# automatically and adds a display layer (colours, menus, bars...).
# To prevent it from loading:
#   - run the script with the  --no-ui  option
#   - or set the environment variable  PROJECT_NO_UI=1
#   - or set ACTIVE = False in display_layer.py (or delete the file)
#
# LANGUAGE
# Messages are in English by default. To get them in French, the file
# "lang_fr.json" must be next to the script, then:
#   - run the script with  --lang fr
#   - or set the environment variable  PROJECT_LANG=fr
# ============================================================================

import re

_LINE_OPEN: list[bool] = [False]


def _pick_language() -> str:
	# Read (and remove) --lang xx / --lang=xx from the command line, then PROJECT_LANG
	lang: str = os.environ.get("PROJECT_LANG", "en").strip().lower() or "en"
	args: list[str] = sys.argv
	i: int = 1
	while i < len(args):
		if args[i] == "--lang" and i + 1 < len(args):
			lang = args[i + 1].strip().lower()
			del args[i:i + 2]
			continue
		if args[i].startswith("--lang="):
			lang = args[i].split("=", 1)[1].strip().lower()
			del args[i]
			continue
		i += 1
	return lang


class _Translator:
	# Translates English messages using lang_<code>.json; returns the text unchanged otherwise
	def __init__(self, lang: str) -> None:
		self.lang: str = "en"
		self.exact: dict[str, str] = {}
		self.patterns: list[tuple[re.Pattern[str], list]] = []
		if lang == "en":
			return
		path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"lang_{lang}.json")
		try:
			with open(path, encoding="utf-8") as handle:
				data: dict = json.load(handle)
		except (OSError, ValueError):
			return
		self.lang = lang
		self.exact = data.get("exact", {})
		for source, target in data.get("patterns", []):
			literal: str = "".join(p for p in source if isinstance(p, str))
			if len(literal.strip()) < 3:
				continue
			regex: str = "".join(re.escape(p) if isinstance(p, str) else f"(?P<p{p}>.*?)" for p in source)
			self.patterns.append((re.compile(regex + r"\Z", re.DOTALL), target, len(literal)))
		self.patterns.sort(key=lambda item: -item[2])

	def __call__(self, text: object) -> object:
		if self.lang == "en" or not isinstance(text, str) or not text:
			return text
		found: str | None = self._lookup(text)
		if found is not None:
			return found
		if "\n" in text:
			return "\n".join(self._lookup(row) or row for row in text.split("\n"))
		return text

	def _exact(self, text: str) -> str | None:
		if text in self.exact:
			return self.exact[text]
		stripped: str = text.strip()
		if stripped and stripped != text and stripped in self.exact:
			start: int = text.index(stripped)
			return text[:start] + self.exact[stripped] + text[start + len(stripped):]
		return None

	def _lookup(self, text: str) -> str | None:
		found: str | None = self._exact(text)
		if found is not None:
			return found
		for regex, target, _ in self.patterns:
			match = regex.match(text)
			if match:
				values: dict[str, str] = match.groupdict()
				# Inserted values (e.g. a "[DRY RUN] " prefix) are translated too if known
				return "".join(p if isinstance(p, str) else (self._exact(values.get(f"p{p}", "")) or values.get(f"p{p}", "")) for p in target)
		return None


tr: _Translator = _Translator(_pick_language())


def _translate_argparse() -> None:
	# Translate the help texts given to argparse (descriptions, options, epilogs)
	if tr.lang == "en":
		return
	import argparse
	original_init = argparse.ArgumentParser.__init__
	original_add = argparse._ActionsContainer.add_argument
	original_group = argparse._ActionsContainer.add_argument_group

	def init(self, *args, **kwargs):
		for key in ("description", "epilog"):
			if key in kwargs:
				kwargs[key] = tr(kwargs[key])
		original_init(self, *args, **kwargs)

	def add_argument(self, *args, **kwargs):
		if "help" in kwargs:
			kwargs["help"] = tr(kwargs["help"])
		return original_add(self, *args, **kwargs)

	def add_argument_group(self, *args, **kwargs):
		args = tuple(tr(a) for a in args)
		if "description" in kwargs:
			kwargs["description"] = tr(kwargs["description"])
		return original_group(self, *args, **kwargs)

	argparse.ArgumentParser.__init__ = init
	argparse._ActionsContainer.add_argument = add_argument
	argparse._ActionsContainer.add_argument_group = add_argument_group
	original_parser = argparse._SubParsersAction.add_parser

	def add_parser(self, name, **kwargs):
		if "help" in kwargs:
			kwargs["help"] = tr(kwargs["help"])
		return original_parser(self, name, **kwargs)

	argparse._SubParsersAction.add_parser = add_parser


_translate_argparse()


def _write(*args: object, **kwargs: object) -> None:
	# print() that first breaks the line if a progress bar is using the current line
	if _LINE_OPEN[0]:
		print()
		_LINE_OPEN[0] = False
	print(*args, **kwargs)


def _input(prompt: str) -> str:
	# input() that first breaks the line if a progress bar is using the current line
	if _LINE_OPEN[0]:
		print()
		_LINE_OPEN[0] = False
	return input(prompt)


class _ConsoleProgress:
	# Simple text progress bar (a single line rewritten with \r)
	def __init__(self, total: float | None, description: str = "") -> None:
		self.total: float | None = total
		self.done: float = 0
		self.description: str = tr(description)
		self._last: int = -1
		self._length: int = 0

	def __enter__(self) -> "_ConsoleProgress":
		self._display(force=True)
		return self

	def __exit__(self, *exc: object) -> None:
		self._display(force=True)
		print()
		_LINE_OPEN[0] = False

	def advance(self, n: float = 1, description: str | None = None) -> None:
		self.done += n
		if description is not None:
			self.description = tr(description)
		self._display()

	def set_value(self, done: float | None = None, total: float | None = None, description: str | None = None) -> None:
		if done is not None:
			self.done = done
		if total is not None:
			self.total = total
		if description is not None:
			self.description = tr(description)
		self._display()

	def _display(self, force: bool = False) -> None:
		if self.total:
			percent: int = int(min(self.done, self.total) * 100 / self.total)
			if percent == self._last and not force:
				return
			self._last = percent
			row: str = f"{self.description} : {percent:3d}% ({int(self.done)}/{int(self.total)})"
		else:
			row = f"{self.description} : {int(self.done)}"
		# The spaces erase what is left of a longer previous line
		if not _LINE_OPEN[0]:
			self._length = 0
		print("\r" + row.ljust(self._length), end="", flush=True)
		self._length = len(row)
		_LINE_OPEN[0] = True


class _ConsoleMultiProgress:
	# Several tasks tracked at once, shown on a single line
	def __init__(self, tasks: list[tuple[str, float]]) -> None:
		self.tasks: list[list] = [[tr(name), float(total), 0.0] for name, total in tasks]

	def __enter__(self) -> "_ConsoleMultiProgress":
		return self

	def __exit__(self, *exc: object) -> None:
		self._display()
		print()
		_LINE_OPEN[0] = False

	def advance(self, index: int, n: float = 1) -> None:
		task: list = self.tasks[index]
		task[2] = min(task[1], task[2] + n)
		self._display()

	def finished(self) -> bool:
		return all(t[2] >= t[1] for t in self.tasks)

	def _display(self) -> None:
		pieces: list[str] = [f"{name} {int(done * 100 / total) if total else 100:3d}%" for name, total, done in self.tasks]
		print("\r" + " | ".join(pieces), end="", flush=True)
		_LINE_OPEN[0] = True


class _ConsoleStatus:
	# "In progress..." message shown before a long operation
	def __init__(self, message: str) -> None:
		self.message: str = tr(message)

	def __enter__(self) -> "_ConsoleStatus":
		_write(f"{self.message} ...", flush=True)
		return self

	def __exit__(self, *exc: object) -> None:
		pass

	def update(self, message: str) -> None:
		_write(f"{tr(message)} ...", flush=True)


class ConsoleDisplay:
	# Minimal display: only _write() and _input(), no dependency
	def __init__(self) -> None:
		self.tr: _Translator = tr
		self.lang: str = tr.lang

	def clear(self) -> None:
		_write()

	def banner(self, title: str, subtitle: str = "") -> None:
		title, subtitle = tr(title), tr(subtitle)
		width: int = max(len(title), len(subtitle)) + 4
		_write("=" * width)
		_write(f"  {title}")
		if subtitle:
			_write(f"  {subtitle}")
		_write("=" * width)
		_write()

	def section(self, title: str) -> None:
		_write()
		_write(f"--- {tr(title)} ---")

	def info(self, message: str = "") -> None:
		_write(tr(message))

	def muted(self, message: str) -> None:
		_write(tr(message))

	def success(self, message: str) -> None:
		_write(f"[OK] {tr(message)}")

	def warning(self, message: str) -> None:
		_write(f"{tr('[WARNING]')} {tr(message)}")

	def error(self, message: str) -> None:
		_write(f"{tr('[ERROR]')} {tr(message)}", file=sys.stderr)

	def block(self, text: str, title: str | None = None) -> None:
		# Framed text (equivalent of a panel)
		if title:
			_write(f"[{tr(title)}]")
		_write(tr(text))
		_write()

	def key_values(self, pairs: list[tuple[str, object]], title: str | None = None) -> None:
		# Aligned "key: value" list
		if title:
			_write(f"[{tr(title)}]")
		pairs = [(tr(str(key)), tr(value)) for key, value in pairs]
		width: int = max((len(key) for key, _ in pairs), default=0)
		for key, value in pairs:
			_write(f"  {key:<{width}} : {value}")
		_write()

	def table(self, columns: list[str], rows: list[list[object]], title: str | None = None) -> None:
		# Text table with aligned columns
		columns = [tr(str(c)) for c in columns]
		cells: list[list[str]] = [[str(tr(c)) for c in row] for row in rows]
		widths: list[int] = [len(c) for c in columns]
		for row in cells:
			for i, c in enumerate(row):
				if i < len(widths):
					widths[i] = max(widths[i], len(c))
		if title:
			_write(tr(title))
		_write(" | ".join(c.ljust(widths[i]) for i, c in enumerate(columns)))
		_write("-+-".join("-" * w for w in widths))
		for row in cells:
			_write(" | ".join(c.ljust(widths[i]) if i < len(widths) else c for i, c in enumerate(row)))
		_write()

	def tree(self, root: str, children: list) -> None:
		# children: list of str or of (name, sub_children) tuples
		_write(tr(root))
		self._tree(children, "")

	def _tree(self, children: list, prefix: str) -> None:
		for i, child in enumerate(children):
			last: bool = i == len(children) - 1
			name: str = child[0] if isinstance(child, tuple) else str(child)
			_write(f"{prefix}{'`-- ' if last else '|-- '}{tr(name)}")
			if isinstance(child, tuple):
				self._tree(child[1], prefix + ("    " if last else "|   "))

	def code(self, text: str, language: str = "", title: str | None = None) -> None:
		if title:
			_write(f"[{tr(title)}]")
		for number, row in enumerate(text.splitlines(), 1):
			_write(f"{number:3d} | {row}")
		_write()

	def markdown(self, text: str) -> None:
		_write(tr(text))
		_write()

	def log(self, level: str, message: str) -> None:
		_write(f"[{time.strftime('%H:%M:%S')}] {level:<8} {tr(message)}")

	def ask(self, question: str, default: str | None = None) -> str | None:
		# Returns None if the user cancels (Ctrl+C / Ctrl+D)
		suffix: str = f" [{default}]" if default else ""
		try:
			answer: str = _input(f"{tr(question)}{suffix} : ").strip()
		except (EOFError, KeyboardInterrupt):
			_write()
			return None
		return answer if answer else (default if default is not None else "")

	def ask_path(self, question: str, default: str | None = None) -> str | None:
		return self.ask(question, default)

	def ask_number(self, question: str, default: float | None = None, integer: bool = True, minimum: float | None = None, maximum: float | None = None) -> float | int | None:
		# Ask again until the input is a valid number
		while True:
			raw_value: str | None = self.ask(question, None if default is None else str(default))
			if raw_value is None:
				return None
			try:
				value: float | int = int(raw_value) if integer else float(raw_value)
			except ValueError:
				_write(tr("  Invalid value, try again."))
				continue
			if minimum is not None and value < minimum:
				_write(tr(f"  Value must be >= {minimum}."))
				continue
			if maximum is not None and value > maximum:
				_write(tr(f"  Value must be <= {maximum}."))
				continue
			return value

	def confirm(self, question: str, default: bool = False) -> bool | None:
		hint: str = tr("Y/n") if default else tr("y/N")
		while True:
			try:
				answer: str = _input(f"{tr(question)} ({hint}) : ").strip().lower()
			except (EOFError, KeyboardInterrupt):
				_write()
				return None
			if not answer:
				return default
			if answer in ("y", "yes", "o", "oui"):
				return True
			if answer in ("n", "no", "non"):
				return False
			_write(tr("  Answer y or n."))

	def choose(self, question: str, options: list[str], default: str | None = None) -> str | None:
		# Numbered menu; returns the chosen option (untranslated) or None if cancelled
		if not options:
			return None
		_write(tr(question))
		for i, option in enumerate(options, 1):
			_write(f"  {i}. {tr(option)}")
		default_index: int | None = options.index(default) + 1 if default in options else None
		while True:
			try:
				raw_value: str = _input(tr(f"Your choice (1-{len(options)})") + (f" [{default_index}]" if default_index else "") + " : ").strip()
			except (EOFError, KeyboardInterrupt):
				_write()
				return None
			if not raw_value and default_index:
				return options[default_index - 1]
			if raw_value.isdigit() and 1 <= int(raw_value) <= len(options):
				return options[int(raw_value) - 1]
			_write(tr("  Invalid choice."))

	def choose_many(self, question: str, options: list[str], checked: list[str] | None = None) -> list[str] | None:
		# Multiple selection: comma-separated numbers
		_write(tr(question))
		for i, option in enumerate(options, 1):
			mark: str = "*" if checked and option in checked else " "
			_write(f"  {i}. [{mark}] {tr(option)}")
		while True:
			try:
				raw_value: str = _input(tr("Comma-separated numbers (empty = default selection, 'all' = everything): ")).strip().lower()
			except (EOFError, KeyboardInterrupt):
				_write()
				return None
			if not raw_value:
				return list(checked or [])
			if raw_value in ("all", "tout", "*"):
				return list(options)
			try:
				indices: list[int] = [int(x) for x in raw_value.replace(" ", "").split(",") if x]
			except ValueError:
				_write(tr("  Invalid input."))
				continue
			if all(1 <= i <= len(options) for i in indices):
				return [options[i - 1] for i in dict.fromkeys(indices)]
			_write(tr("  Number out of range."))

	def pause(self, message: str = "Press Enter to continue...") -> None:
		try:
			_input(f"\n{tr(message)}")
		except (EOFError, KeyboardInterrupt):
			_write()

	def progress(self, total: float | None, description: str = "") -> _ConsoleProgress:
		return _ConsoleProgress(total, description)

	def multi_progress(self, tasks: list[tuple[str, float]]) -> _ConsoleMultiProgress:
		return _ConsoleMultiProgress(tasks)

	def status(self, message: str) -> _ConsoleStatus:
		return _ConsoleStatus(message)


def load_display() -> ConsoleDisplay:
	# Load the optional display layer (display_layer.py) if it is present and allowed
	simple_console: ConsoleDisplay = ConsoleDisplay()
	if "--no-ui" in sys.argv:
		sys.argv.remove("--no-ui")
		return simple_console
	if os.environ.get("PROJECT_NO_UI", "").strip() not in ("", "0"):
		return simple_console
	folder: str = os.path.dirname(os.path.abspath(__file__))
	if folder not in sys.path:
		sys.path.insert(0, folder)
	if not os.path.isfile(os.path.join(folder, "display_layer.py")):
		return simple_console
	try:
		import display_layer
		return display_layer.create_display(simple_console) or simple_console
	except Exception as exc:
		# The layer is present but could not start: say why, then use the plain console
		missing: str | None = getattr(exc, "name", None) if isinstance(exc, ImportError) else None
		if missing:
			simple_console.muted(tr(f"display_layer.py not loaded: the '{missing}' module is missing (pip install rich questionary)."))
		else:
			simple_console.muted(tr(f"display_layer.py not loaded: {exc}"))
		simple_console.muted(tr("Plain console display used (add --no-ui to hide this message)."))
		return simple_console


ui: ConsoleDisplay = load_display()
# ============================================================================

VERSION: str = "2.0.0"

TEMPLATE_DIR: str = os.path.join("Template", "file-report")
TEMPLATE_HTML_PATH: str = os.path.join(TEMPLATE_DIR, "file-report.html")

TEXTS: dict[str, dict[str, str]] = {
	"en": {
		"scanning": "Scanning",
		"folders": "folders",
		"title": "All-Files Report Generator",
		"report_generated": "Report generated",
		"compressed": "Compressed version",
		"errors_encountered": "Errors encountered",
		"errors_suffix": "errors",
		"errors_file": "errors-report.txt",
		"errors_header": "=== Error Report ===",
		"generated_on": "Generated on",
		"total_errors": "Total number of errors",
		"access_denied_folder": "Access denied to a folder in",
		"path_not_found": "Path not found",
		"error_folder": "Error while processing folder",
		"access_denied_partition": "Access denied to partition",
		"error_partition": "Error while processing partition",
		"template_missing": "Error: HTML template file",
		"default_output": "result.html",
	},
	"fr": {
		"scanning": "Analyse de",
		"folders": "dossiers",
		"title": "Générateur de Rapport de Tous les Fichiers",
		"report_generated": "Rapport généré",
		"compressed": "Version compressée",
		"errors_encountered": "Erreurs rencontrées",
		"errors_suffix": "erreurs",
		"errors_file": "errors-report.txt",
		"errors_header": "=== Rapport d'erreurs ===",
		"generated_on": "Généré le",
		"total_errors": "Nombre total d'erreurs",
		"access_denied_folder": "Accès refusé à un dossier dans",
		"path_not_found": "Le chemin d'accès est introuvable",
		"error_folder": "Erreur lors du traitement du dossier",
		"access_denied_partition": "Accès refusé à la partition",
		"error_partition": "Erreur lors du traitement de la partition",
		"template_missing": "Erreur : le fichier template HTML",
		"default_output": "Resultat.html",
	},
}

# ── Display ──────────────────────────────────────────────────────────────────
def splash_screen() -> None:
	# Show the welcome panel
	ui.banner(f"Folder Report Generator v{VERSION}", "Generate an HTML report of every file on the partitions")

class ReportGeneratorInterface(ABC):
	# Abstract interface defining the contract every report generator must follow
	@abstractmethod
	def scan(self, extensions: list[str]) -> tuple[dict[str, Any], list[str]]:
		...

	@abstractmethod
	def build_html(self, results: dict[str, Any]) -> str | None:
		...

	@abstractmethod
	def write_report(self, html: str, output_path: str) -> None:
		...

	@abstractmethod
	def write_errors(self, errors: list[str], output_dir: str) -> None:
		...

	@abstractmethod
	def run(self, extensions: list[str], output_path: str) -> None:
		...

class FolderReportGenerator(ReportGeneratorInterface):
	# Concrete implementation that scans disk partitions and builds an HTML report
	def __init__(self, lang: str) -> None:
		self.lang: str = lang
		self.texts: dict[str, str] = TEXTS[lang]

	def format_size(self, size_bytes: float) -> tuple[str, str]:
		# Convert a raw byte count into a human readable value and unit
		units: list[str] = ["o", "Ko", "Mo", "Go", "To", "Po"] if self.lang == "fr" else ["B", "KB", "MB", "GB", "TB", "PB"]
		if size_bytes == 0:
			return "0.00", units[0]
		for unit in units:
			if size_bytes < 1024:
				return f"{size_bytes:.2f}", unit
			size_bytes /= 1024
		return f"{size_bytes:.2f}", units[-1]

	def flatten_tree(self, tree: dict[str, Any], path: str = "") -> list[dict[str, str]]:
		# Turn the nested folder tree into a flat list of file rows
		rows: list[dict[str, str]] = []
		for name, content in tree.items():
			if name == "_files":
				for file_name, size in content:
					base_name, ext = os.path.splitext(file_name)
					ext = ext.lstrip(".")
					value, unit = self.format_size(size)
					rows.append({"n": base_name, "e": ext, "t": value, "u": unit, "p": path})
			else:
				sub_path: str = f"{path}/{name}" if path else name
				rows += self.flatten_tree(content, sub_path)
		return rows

	def extract_extensions(self, rows: list[dict[str, str]]) -> list[str]:
		# Collect the sorted set of distinct file extensions present in the rows
		return sorted({item["e"] for item in rows if item["e"]})

	def scan(self, extensions: list[str]) -> tuple[dict[str, Any], list[str]]:
		# Walk every mounted partition and collect files matching the extension filter
		partitions: list[Any] = psutil.disk_partitions(all=False)
		results: dict[str, Any] = {}
		errors: list[str] = []
		for partition in partitions:
			mountpoint: str = partition.mountpoint
			results[mountpoint] = {}
			try:
				total_folders: int = sum(len(dirs) for _, dirs, _ in os.walk(mountpoint, onerror=lambda e: None))
				ui.info(f"{self.texts['scanning']} {mountpoint:<40} | {total_folders:>10} {self.texts['folders']}")
				for folder, _subfolders, files in os.walk(mountpoint, onerror=lambda e: None):
					try:
						filtered_files: list[tuple[str, int]] = [
							(f, os.path.getsize(os.path.join(folder, f)))
							for f in files
							if not extensions or os.path.splitext(f)[1].lower().lstrip(".") in extensions
						]
						if filtered_files:
							sub_tree: dict[str, Any] = results.setdefault(mountpoint, {})
							sub_paths: list[str] = folder[len(mountpoint):].strip(os.sep).split(os.sep)
							for sub_folder in sub_paths:
								if sub_folder:
									sub_tree = sub_tree.setdefault(sub_folder, {})
							sub_tree["_files"] = filtered_files
					except PermissionError:
						errors.append(f"{self.texts['access_denied_folder']}: {folder}")
					except FileNotFoundError:
						errors.append(f"{self.texts['path_not_found']}: {folder}")
					except Exception as exc:
						errors.append(f"{self.texts['error_folder']} {folder}: {exc}")
			except PermissionError:
				errors.append(f"{self.texts['access_denied_partition']}: {mountpoint}")
			except Exception as exc:
				errors.append(f"{self.texts['error_partition']} {mountpoint}: {exc}")
		return results, errors

	def build_html(self, results: dict[str, Any]) -> str | None:
		# Load the external template and inject the scan results into it
		try:
			with open(TEMPLATE_HTML_PATH, "r", encoding="utf-8") as handle:
				template: str = handle.read()
		except FileNotFoundError:
			ui.error(f"{self.texts['template_missing']} '{TEMPLATE_HTML_PATH}'")
			return None
		partitions_data: dict[str, list[dict[str, str]]] = {}
		for mountpoint, content in results.items():
			label: str = f"🖥️ {mountpoint}"
			partitions_data[label] = self.flatten_tree(content)
		all_rows: list[dict[str, str]] = [item for rows in partitions_data.values() for item in rows]
		available_extensions: list[str] = self.extract_extensions(all_rows)
		json_data: str = json.dumps(partitions_data, ensure_ascii=False, separators=(",", ":"))
		extensions_json: str = json.dumps(available_extensions, ensure_ascii=False, separators=(",", ":"))
		html: str = template.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		html = html.replace("{{DATA_JSON}}", json_data)
		html = html.replace("{{EXTENSIONS_JSON}}", extensions_json)
		return html

	def write_report(self, html: str, output_path: str) -> None:
		# Write the HTML report to disk and produce a gzip-compressed copy
		with open(output_path, "w", encoding="utf-8") as handle:
			handle.write(html)
		size_mb: float = os.path.getsize(output_path) / (1024 * 1024)
		ui.success(f"{self.texts['report_generated']} : {output_path}  ({size_mb:.2f} Mo)")
		gz_path: str = output_path + ".gz"
		with open(output_path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
			shutil.copyfileobj(f_in, f_out)
		size_gz: float = os.path.getsize(gz_path) / (1024 * 1024)
		ui.muted(f"{self.texts['compressed']} : {gz_path}  ({size_gz:.2f} Mo)")

	def write_errors(self, errors: list[str], output_dir: str) -> None:
		# Write the collected scan errors to a dedicated text report
		if not errors:
			return
		ui.warning(f"{self.texts['errors_encountered']:<40} | {len(errors):>10} {self.texts['errors_suffix']}")
		os.makedirs(output_dir, exist_ok=True)
		error_path: str = os.path.join(output_dir, self.texts["errors_file"])
		digits: int = len(str(len(errors)))
		with open(error_path, "w", encoding="utf-8") as handle:
			handle.write(f"{self.texts['errors_header']}\n")
			handle.write(f"{self.texts['generated_on']} : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
			handle.write(f"{self.texts['total_errors']} : {len(errors)}\n\n")
			for index, error in enumerate(errors, 1):
				if ":" in error:
					left, right = error.split(":", 1)
					handle.write(f"{index:0{digits}d}. {left.strip():<40}: {right.strip()}\n")
				else:
					handle.write(f"{index:0{digits}d}. {error}\n")

	def run(self, extensions: list[str], output_path: str) -> None:
		# Orchestrate scanning, HTML generation and error reporting
		ui.section(self.texts['title'])
		ui.info()
		results, errors = self.scan(extensions)
		html: str | None = None
		with ui.progress(2, "Building the HTML report") as progress:
			html = self.build_html(results)
			progress.advance()
			if html is not None:
				progress.set_value(description="Writing the output files")
				self.write_report(html, output_path)
			progress.advance()
		self.write_errors(errors, "src")
		if html is None:
			return
		ui.info()
		ui.key_values([
			("Language", self.lang),
			("Extensions", ", ".join(extensions) if extensions else "(all)"),
			("Report", output_path),
			("Compressed report", output_path + ".gz"),
			("Errors", len(errors)),
		], title="Report generated successfully")

# ── Command line & interactive interface (same style as Interface.py) ──────
def build_arg_parser() -> argparse.ArgumentParser:
	# Build the command line argument parser for the report generator
	epilog: str = (
		"All the options above can also be entered through the interactive\n"
		"form: just run the script without arguments to open it\n"
		"(or add -i / --interactive to force it even with other options)."
	)
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		description="Generate an HTML file report for all mounted partitions, using Template/.",
		epilog=epilog,
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}", help="Print the program version and exit.")
	parser.add_argument("-l", "--lang", choices=["en", "fr"], default=ui.lang if ui.lang in ("en", "fr") else "en", help="Output language for console messages and file names (default: the --lang / PROJECT_LANG language).")
	parser.add_argument("-e", "--extensions", nargs="*", default=[], help="list of file extensions to include, e.g. -e pdf jpg png")
	parser.add_argument("-o", "--output", default=None, help="path of the generated HTML report")
	parser.add_argument("--no-ui", action="store_true", help="Disable the optional display layer (display_layer.py)")
	parser.add_argument("-i", "--interactive", action="store_true", help="Force the interactive form to open even with other options")
	return parser

def interactive_form(defaults: argparse.Namespace) -> argparse.Namespace:
	# Interactive form exposing every parseable parameter
	ui.section("Report settings")
	ui.info()

	lang_label: str | None = ui.choose(
		"Output language / Langue des messages:",
		["Français", "English"],
		default="Français" if defaults.lang == "fr" else "English",
	)
	if lang_label is None:
		ui.warning("Cancelled.")
		sys.exit(0)
	lang: str = "fr" if lang_label == "Français" else "en"

	ext_text: str | None = ui.ask(
		"Extensions to include (comma-separated, empty = all)",
		", ".join(defaults.extensions),
	)
	if ext_text is None:
		ui.warning("Cancelled.")
		sys.exit(0)
	extensions: list[str] = [e.strip().lower().lstrip(".") for e in ext_text.split(",") if e.strip()]

	default_output: str = defaults.output or TEXTS[lang]["default_output"]
	output: str | None = ui.ask_path("Output file", default_output)
	if output is None:
		ui.warning("Cancelled.")
		sys.exit(0)

	ui.info()
	ui.key_values([
		("Language", lang),
		("Extensions", ", ".join(extensions) if extensions else "(all)"),
		("Output file", output),
	], title="Settings summary")

	confirmed: bool | None = ui.confirm("Start the scan with these settings?", default=True)
	if not confirmed:
		ui.warning("Cancelled.")
		sys.exit(0)

	defaults.lang = lang
	defaults.extensions = extensions
	defaults.output = output
	return defaults

def parse_args() -> argparse.Namespace:
	parser: argparse.ArgumentParser = build_arg_parser()
	args: argparse.Namespace = parser.parse_args()

	# Without any argument (or with -i/--interactive), open the full form
	# exposing every parameter — same logic as the Interface.py menu
	# when no demo is given directly with -d.
	if args.interactive or len(sys.argv) == 1:
		splash_screen()
		args = interactive_form(args)
	else:
		splash_screen()

	return args

def main() -> None:
	# Parse arguments and run the report generator
	args: argparse.Namespace = parse_args()
	extensions: list[str] = [ext.lower().lstrip(".") for ext in args.extensions]
	generator: FolderReportGenerator = FolderReportGenerator(args.lang)
	output_path: str = args.output if args.output else generator.texts["default_output"]
	generator.run(extensions, output_path)

main()
