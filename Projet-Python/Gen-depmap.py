#!/usr/bin/env python3

import argparse
import colorsys
import io
import json
import os
import re
import shutil
import sys
import time
from abc			import ABC, abstractmethod
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

SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR: str = os.path.join(SCRIPT_DIR, "Template", "depmap")
TEMPLATE_PATH: str = os.path.join(TEMPLATE_DIR, "depmap.html")

DEFAULT_EXTENSIONS: set[str] = {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"}
HEADER_EXTENSIONS: set[str] = {".h", ".hpp", ".hh", ".hxx"}
SKIP_KEYWORDS: set[str] = {"if", "while", "for", "switch", "return", "sizeof", "typedef", "else", "do", "catch"}

NODE_W: int = 200
NODE_H: int = 42
NODE_GAP: int = 30
GRID_X: int = NODE_W + NODE_GAP
GRID_Y: int = NODE_H + NODE_GAP
COLS: int = 6
ROW_GAP: int = 2

FUNC_START_RE = re.compile(r'^(?:(?:static|inline|virtual|explicit|constexpr|void|int|bool|float|double|char|short|long|const|unsigned|signed|size_t|auto|[A-Za-z_]\w*(?:::\w+)?)\s+\*?)+(\w+)\s*\(')
CALL_RE = re.compile(r'\b(\w+)\s*\(')
# "Bare" reference to an identifier: used to spot function pointers
# passed as arguments (e.g. toolbar_btn(x, g, icon_hud, "HUD")), which are
# never followed by a parenthesis and therefore invisible to CALL_RE.
BAREREF_RE = re.compile(r'\b(\w+)\b(?!\s*\()')

def resolve_scan_roots(root: str) -> list[str]:
	# Many C/C++ projects keep their sources (src/) apart from their headers
	# (include/). If the folder given with --src contains one and/or the other,
	# these subfolders are scanned (each recursively) rather than the root
	# folder itself. Otherwise (no src/ or include/), the folder
	# given directly — historical behaviour unchanged for projects
	# that do not follow this convention.
	candidates: list[str] = []
	for name in ("src", "include"):
		d: str = os.path.join(root, name)
		if os.path.isdir(d):
			candidates.append(d)
	return candidates if candidates else [root]

class DependencyMapGeneratorInterface(ABC):
	# Abstract interface defining the contract every dependency map generator must follow.
	@abstractmethod
	def scan_files(self, src_dir: str, extensions: set[str], recursive: bool) -> tuple[list[str], dict[str, str]]:
		...

	@abstractmethod
	def build_nodes(self, files: list[str], path_of: dict[str, str], overrides: dict[str, str]) -> dict[str, dict[str, Any]]:
		...

	@abstractmethod
	def build_edges(self, nodes: dict[str, dict[str, Any]], path_of: dict[str, str], func_defined_in: dict[str, list[str]]) -> list[dict[str, Any]]:
		...

	@abstractmethod
	def compute_layout(self, nodes: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, str]]]:
		...

	@abstractmethod
	def inject_html(self, output_path: str, title: str, subtitle: str, nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]], colors: dict[str, dict[str, str]], positions: dict[str, dict[str, int]], backup: bool) -> bool:
		...

	@abstractmethod
	def run(self, args: argparse.Namespace) -> None:
		...

class DependencyMapGenerator(DependencyMapGeneratorInterface):
	# Concrete implementation: scans the C/C++ sources and builds the HTML map.
	def scan_files(self, src_dir: str, extensions: set[str], recursive: bool) -> tuple[list[str], dict[str, str]]:
		# Return the list of files found, as (basename -> absolute path).
		# The node is identified by its basename (like local #include "..."),
		# with a warning if two project files share the same name.
		# Scan src/ and/or include/ under src_dir if they exist (see resolve_scan_roots),
		# otherwise src_dir directly.
		found: dict[str, str] = {}
		dupes: list[str] = []
		for root_dir in resolve_scan_roots(src_dir):
			walker: Any = os.walk(root_dir) if recursive else [(root_dir, [], os.listdir(root_dir))]
			for root, _dirs, filenames in walker:
				for fn in filenames:
					if os.path.splitext(fn)[1] not in extensions:
						continue
					full: str = os.path.join(root, fn)
					if fn in found and found[fn] != full:
						dupes.append(fn)
					found[fn] = full
		if dupes:
			ui.warning(f"{len(set(dupes))} duplicate file name(s) in the tree "
				f"(only the last one found is kept, local #includes may become ambiguous):")
			for d in sorted(set(dupes)):
				ui.info(f"   - {d}")
		files: list[str] = sorted(found.keys(), key=lambda f: (0 if os.path.splitext(f)[1] in HEADER_EXTENSIONS else 1, f))
		return files, found

	def build_nodes(self, files: list[str], path_of: dict[str, str], overrides: dict[str, str]) -> dict[str, dict[str, Any]]:
		nodes: dict[str, dict[str, Any]] = {}
		for f in files:
			path: str = path_of[f]
			is_header: bool = os.path.splitext(f)[1] in HEADER_EXTENSIONS
			incs: list[str] = get_includes(path)
			if is_header:
				funcs: list[str] = get_declared_funcs(path)
				declared: list[str] = funcs
			else:
				funcs = get_defined_funcs(path)
				declared = []
			nodes[f] = {"group": get_group(f, overrides), "funcs": funcs, "includes": incs, "is_header": is_header, "declared": declared}
		return nodes

	def compute_func_defined_in(self, nodes: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
		# func -> file(s) that define it
		func_defined_in: dict[str, list[str]] = {}
		for f, info in nodes.items():
			if not info["is_header"]:
				for fn in info["funcs"]:
					func_defined_in.setdefault(fn, []).append(f)
		return func_defined_in

	def build_edges(self, nodes: dict[str, dict[str, Any]], path_of: dict[str, str], func_defined_in: dict[str, list[str]]) -> list[dict[str, Any]]:
		edges: list[dict[str, Any]] = []
		added_edges: set[tuple[str, str, str]] = set()

		def add_edge(src: str, tgt: str, etype: str, fns: list[str] | None = None, count: int = 0, pairs: list[dict[str, Any]] | None = None) -> None:
			key: tuple[str, str, str] = (src, tgt, etype)
			if key in added_edges:
				for e in edges:
					if e["src"] == src and e["tgt"] == tgt and e["type"] == etype:
						if fns:
							for fn in fns:
								if fn not in e["fns"]:
									e["fns"].append(fn)
									e["count"] += 1
						if pairs:
							e.setdefault("pairs", []).extend(pairs)
				return
			added_edges.add(key)
			e: dict[str, Any] = {"src": src, "tgt": tgt, "type": etype, "fns": fns or [], "count": count}
			if pairs is not None:
				e["pairs"] = pairs
			edges.append(e)

		# include / h_includes_h
		for f, info in nodes.items():
			for inc in info["includes"]:
				inc_base: str = os.path.basename(inc)
				if inc_base in nodes:
					etype: str = "h_includes_h" if info["is_header"] else "include"
					add_edge(f, inc_base, etype)

		# call edges
		known_funcs: set[str] = set(func_defined_in.keys())
		for f, info in nodes.items():
			if info["is_header"]:
				continue
			callee_callers: dict[str, set[str]] = get_calls_with_caller(path_of[f], known_funcs)
			tgt_pairs: dict[str, list[tuple[str, str]]] = {}
			for callee, callers in callee_callers.items():
				for tgt in func_defined_in.get(callee, []):
					if tgt != f:
						for caller in callers:
							tgt_pairs.setdefault(tgt, []).append((caller, callee))
			for tgt, pair_list in tgt_pairs.items():
				seen: dict[str, set[str]] = {}
				for caller, callee in pair_list:
					seen.setdefault(callee, set()).add(caller)
				fns: list[str] = list(seen.keys())
				pairs: list[dict[str, Any]] = [{"caller": caller, "callee": callee, "callee_defined_in": func_defined_in.get(callee, []), "callee_multi_def": len(func_defined_in.get(callee, [])) > 1} for callee, callers in seen.items() for caller in sorted(callers)]
				add_edge(f, tgt, "call", fns, len(pairs), pairs)

		# implements edges
		for f, info in nodes.items():
			if info["is_header"]:
				continue
			defined: set[str] = set(info["funcs"])
			for inc in info["includes"]:
				inc_base = os.path.basename(inc)
				if inc_base in nodes and nodes[inc_base]["is_header"]:
					impl: list[str] = list(defined & set(nodes[inc_base]["declared"]))
					if impl:
						add_edge(f, inc_base, "implements", impl, len(impl))

		return edges

	def build_colors(self, groups: set[str]) -> dict[str, dict[str, str]]:
		others: list[str] = sorted(g for g in groups if g not in ("main", "other"))
		colors: dict[str, dict[str, str]] = {}
		n: int = max(len(others), 1)
		for i, g in enumerate(others):
			hue: float = i * 360.0 / n
			colors[g] = {"bg": hsl_to_hex(hue, 0.55, 0.88), "border": hsl_to_hex(hue, 0.55, 0.46), "text": hsl_to_hex(hue, 0.60, 0.28)}
		if "main" in groups:
			colors["main"] = {"bg": "#f0f0f0", "border": "#888888", "text": "#333333"}
		colors["other"] = {"bg": "#f5f5f5", "border": "#aaaaaa", "text": "#444444"}
		return colors

	def compute_layout(self, nodes: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, str]]]:
		all_groups: set[str] = {info["group"] for info in nodes.values()}
		# "main" first if it exists, then alphabetical, "other" last
		groups_order: list[str] = []
		if "main" in all_groups:
			groups_order.append("main")
		groups_order += sorted(g for g in all_groups if g not in ("main", "other"))
		if "other" in all_groups:
			groups_order.append("other")

		group_nodes: dict[str, list[str]] = {g: [] for g in groups_order}
		for f in sorted(nodes.keys(), key=lambda f: (0 if os.path.splitext(f)[1] in HEADER_EXTENSIONS else 1, f)):
			group_nodes.setdefault(nodes[f]["group"], []).append(f)

		init_pos: dict[str, dict[str, int]] = {}
		row_start: int = 1
		for g in groups_order:
			gn: list[str] = group_nodes.get(g, [])
			if not gn:
				continue
			for i, f in enumerate(gn):
				col: int = (i % COLS) + 1
				row: int = row_start + (i // COLS)
				init_pos[f] = {"x": col * GRID_X, "y": row * GRID_Y}
			rows_used: int = (len(gn) - 1) // COLS + 1
			row_start += rows_used + ROW_GAP

		colors: dict[str, dict[str, str]] = self.build_colors(all_groups)
		return init_pos, colors

	def inject_html(self, output_path: str, title: str, subtitle: str, nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]], colors: dict[str, dict[str, str]], positions: dict[str, dict[str, int]], backup: bool) -> bool:
		# Scaffold: create the output file from the template if missing
		if not os.path.isfile(output_path):
			if not os.path.isfile(TEMPLATE_PATH):
				ui.error(f"Error: neither {output_path} nor the template {TEMPLATE_PATH} exists.")
				ui.error("The Template/depmap/ folder (with depmap.html, depmap.css, depmap.js) must be shipped next to this script.")
				return False
			shutil.copyfile(TEMPLATE_PATH, output_path)
			ui.muted(f"→ New file created from the template: {output_path}")

		with open(output_path, encoding='utf-8') as f:
			html: str = f.read()

		nodes_json: str = json.dumps(nodes, ensure_ascii=False)
		edges_json: str = json.dumps(edges, ensure_ascii=False)
		pos_json: str = json.dumps(positions, ensure_ascii=False)
		colors_json: str = json.dumps(colors, ensure_ascii=False)
		title_json: str = json.dumps(title, ensure_ascii=False)
		subtitle_json: str = json.dumps(subtitle, ensure_ascii=False)

		subs: list[tuple[str, str]] = [(r'const PROJECT_TITLE\s*=\s*".*?";', f'const PROJECT_TITLE = {title_json};'), (r'const PROJECT_SUBTITLE\s*=\s*".*?";', f'const PROJECT_SUBTITLE = {subtitle_json};'), (r'const NODES_DATA = \{.*?\};', f'const NODES_DATA = {nodes_json};'), (r'const EDGES_DATA = \[.*?\];', f'const EDGES_DATA = {edges_json};'), (r'const COLORS\s*=\s*\{.*?\};', f'const COLORS = {colors_json};'), (r'const INIT_POS\s*=\s*\{.*?\};', f'const INIT_POS = {pos_json};')]

		missing: list[str] = []
		for pattern, replacement in subs:
			html, n = re.subn(pattern, replacement, html, count=1, flags=re.DOTALL)
			if n == 0:
				missing.append(pattern)

		if missing:
			ui.error(f"Error: block(s) not found in {output_path} :")
			for m in missing:
				ui.info(f"   - {m}")
			ui.error("The HTML file was not modified — check that the template contains these 'const' declarations.")
			return False

		# Backup disabled by default: only create a .bak when explicitly requested (--backup)
		if backup:
			backup_path: str = output_path + ".bak"
			try:
				with open(backup_path, 'w', encoding='utf-8') as f:
					f.write(open(output_path, encoding='utf-8').read())
				ui.muted(f"→ Backup created: {backup_path}")
			except OSError:
				ui.warning(f"Cannot create the backup {backup_path}")

		with open(output_path, 'w', encoding='utf-8') as f:
			f.write(html)

		return True

	def print_consistency_report(self, nodes: dict[str, dict[str, Any]], func_defined_in: dict[str, list[str]]) -> None:
		multi_def: dict[str, list[str]] = {fn: fs for fn, fs in func_defined_in.items() if len(fs) > 1}
		if multi_def:
			ui.info()
			ui.warning(f"{len(multi_def)} function(s) defined in several files (ambiguous call resolution):")
			for fn, fs in sorted(multi_def.items()):
				ui.info(f"   - {fn}() → {', '.join(fs)}")

		empty_c: list[str] = [f for f, info in nodes.items() if not info["is_header"] and not info["funcs"]]
		if empty_c:
			ui.info()
			ui.warning(f"{len(empty_c)} source file(s) with no detected function (check the signature style):")
			for f in empty_c:
				ui.info(f"   - {f}")

	def run(self, args: argparse.Namespace) -> None:
		src: str = args.src
		output: str = args.output

		if not os.path.isdir(src):
			ui.error(f"Error: source folder not found: {src}")
			sys.exit(1)

		extensions: set[str] = DEFAULT_EXTENSIONS
		if args.ext:
			extensions = {e if e.startswith(".") else "." + e for e in args.ext.split(",")}

		overrides: dict[str, str] = load_group_overrides(args.groups)

		ui.section("Generating the dependency map")
		ui.info()

		scan_roots: list[str] = resolve_scan_roots(src)
		if scan_roots != [src]:
			ui.muted(f"→ src/ and/or include/ detected, scanning: {', '.join(scan_roots)}")
		ui.info()

		ok: bool = False
		with ui.progress(5, "Scanning source files") as progress:

			files, path_of = self.scan_files(src, extensions, args.recursive)
			if not files:
				ui.error(f"Error: no file ({', '.join(sorted(extensions))}) found in {src}")
				sys.exit(1)
			progress.advance()

			progress.set_value(description="Analysing functions and includes")
			nodes: dict[str, dict[str, Any]] = self.build_nodes(files, path_of, overrides)
			progress.advance()

			progress.set_value(description="Building dependencies")
			func_defined_in: dict[str, list[str]] = self.compute_func_defined_in(nodes)
			edges: list[dict[str, Any]] = self.build_edges(nodes, path_of, func_defined_in)
			progress.advance()

			progress.set_value(description="Computing the layout")
			positions, colors = self.compute_layout(nodes)
			progress.advance()

			progress.set_value(description="Generating the HTML file")
			title: str = args.title or os.path.basename(os.path.abspath(src).rstrip(os.sep))
			n_c_files: int = sum(1 for i in nodes.values() if not i["is_header"])
			subtitle: str = f"{os.path.abspath(src)} · {len(nodes)} files ({n_c_files} .c) · {len(edges)} links (recomputed from the source code)"

			ok = self.inject_html(output, title, subtitle, nodes, edges, colors, positions, args.backup)
			progress.advance()

		if not ok:
			sys.exit(1)

		all_groups: set[str] = {info["group"] for info in nodes.values()}

		ui.info()
		ui.key_values([
			("Nodes", len(nodes)),
			("Edges", len(edges)),
			("Groups", len(all_groups)),
			("Output", output),
			(".bak backup", "yes" if args.backup else "no"),
		], title="Map generated successfully")

		self.print_consistency_report(nodes, func_defined_in)

# ── Generic helper functions (independent of any instance) ──────────────────
def hsl_to_hex(h: float, s: float, l: float) -> str:
	rgb: tuple[float, float, float] = colorsys.hls_to_rgb((h % 360) / 360.0, l, s)
	r: float
	g: float
	b: float
	r, g, b = rgb
	return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))

def load_group_overrides(path: str | None) -> dict[str, str]:
	if not path:
		return {}
	with open(path, encoding="utf-8") as f:
		return json.load(f)

def auto_group(name: str) -> str:
	# Infer a generic group name from the file name.
	# Supported convention: "module_part-N.ext" or "module_part.ext"
	# → group = "module". Works for any C/C++ project that
	# follows a per-module prefix convention, without a fixed list.
	n: str = os.path.splitext(name)[0]
	# remove a "-1", "_2"... suffix
	n = re.sub(r"[-_]\d+$", "", n)
	# prefix before the first separator
	n = re.split(r"[_\-]", n, maxsplit=1)[0]
	n = n.strip()
	return n.lower() if n else "other"

def get_group(name: str, overrides: dict[str, str]) -> str:
	stem: str = os.path.splitext(name)[0]
	for key, group in overrides.items():
		if stem == key or stem.startswith(key) or re.match(key, stem):
			return group
	return auto_group(name)

def strip_comments(src: str) -> str:
	src = re.sub(r'//[^\n]*', '', src)
	src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
	src = re.sub(r'"[^"]*"', '""', src)
	return src

def get_includes(path: str) -> list[str]:
	incs: list[str] = []
	for line in open(path, encoding='utf-8', errors='replace'):
		m: re.Match[str] | None = re.match(r'\s*#\s*include\s+"([^"]+)"', line)
		if m:
			incs.append(m.group(1))
	return incs

def get_defined_funcs(path: str) -> list[str]:
	lines: list[str] = strip_comments(open(path, encoding='utf-8', errors='replace').read()).split('\n')
	funcs: list[str] = []
	i: int = 0
	while i < len(lines):
		m: re.Match[str] | None = FUNC_START_RE.match(lines[i].strip())
		if m:
			fn: str = m.group(1)
			if fn not in SKIP_KEYWORDS and not fn.startswith('_'):
				found_open: bool = False
				found_semi: bool = False
				for j in range(i, min(i + 20, len(lines))):
					chunk: str = lines[j].strip()
					if '{' in chunk:
						found_open = True
						break
					if ';' in chunk:
						found_semi = True
						break
				if found_open and not found_semi:
					funcs.append(fn)
		i += 1
	return list(dict.fromkeys(funcs))

def get_declared_funcs(path: str) -> list[str]:
	funcs: list[str] = []
	for line in strip_comments(open(path, encoding='utf-8', errors='replace').read()).split('\n'):
		line = line.strip()
		if not (';' in line and '(' in line):
			continue
		m: re.Match[str] | None = FUNC_START_RE.match(line)
		if m:
			fn: str = m.group(1)
			if fn not in SKIP_KEYWORDS and not fn.startswith('_'):
				funcs.append(fn)
	return list(dict.fromkeys(funcs))

def get_calls_with_caller(path: str, known_funcs: set[str] | None = None) -> dict[str, set[str]]:
	# Return {callee: set(callers)} by following the brace depth.
	# known_funcs (optional): set of every function defined in
	# the project. When given, a bare identifier that matches a known
	# but is NOT followed by "(" is also counted as a reference
	# (e.g. a function pointer passed as an argument: toolbar_btn(x, g,
	# icon_hud, "HUD") — "icon_hud" is never called with parentheses
	# here, so CALL_RE alone does not see it).
	lines: list[str] = strip_comments(open(path, encoding='utf-8', errors='replace').read()).split('\n')
	result: dict[str, set[str]] = {}
	current_func: str | None = None
	brace_depth: int = 0
	for line in lines:
		s: str = line.strip()
		if brace_depth == 0:
			m: re.Match[str] | None = FUNC_START_RE.match(s)
			if m:
				fn: str = m.group(1)
				if fn not in SKIP_KEYWORDS and not fn.startswith('_'):
					current_func = fn
			brace_depth += s.count('{') - s.count('}')
			continue
		brace_depth += s.count('{') - s.count('}')
		if current_func:
			for m in CALL_RE.finditer(s):
				callee: str = m.group(1)
				if callee not in SKIP_KEYWORDS and not callee.startswith('_'):
					result.setdefault(callee, set()).add(current_func)
			if known_funcs:
				for m in BAREREF_RE.finditer(s):
					callee = m.group(1)
					if callee == current_func:
						continue
					if callee not in SKIP_KEYWORDS and not callee.startswith('_') and callee in known_funcs:
						result.setdefault(callee, set()).add(current_func)
		if brace_depth <= 0:
			brace_depth = 0
			current_func = None
	return result

# ── Command line & interactive interface (same style as Interface.py) ──────
def build_parser() -> argparse.ArgumentParser:
	epilog: str = ("All the options above can also be entered through the interactive\nform: just run the script without --src to open it\n(or add -i / --interactive to force it even with --src).")
	p: argparse.ArgumentParser = argparse.ArgumentParser(description="Generate Dependency_map.html from a project's C/C++ sources.", epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
	p.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}", help="Print the program version and exit.")
	p.add_argument("src_pos", nargs="?", help="Source folder (positional, legacy syntax)")
	p.add_argument("output_pos", nargs="?", help="Output HTML file (positional, legacy syntax)")
	p.add_argument("-s", "--src", help="Source folder, or project root if it contains src/ and/or include/ (default: asked interactively)")
	p.add_argument("-o", "--output", help="Output HTML file (default: <script_folder>/Dependency_map.html)")
	p.add_argument("-t", "--title", help="Project name shown in the header (default: source folder name)")
	p.add_argument("-e", "--ext", help="Extensions to scan, comma-separated (default: %s)" % ",".join(sorted(DEFAULT_EXTENSIONS)))
	p.add_argument("-g", "--groups", help="Optional JSON file {\"prefix_or_regex\": \"group\"} to override automatic detection")
	p.add_argument("-r", "--recursive", dest="recursive", action="store_true", help="Scan the subfolders of src/ recursively (default: enabled)")
	p.add_argument("-nr", "--no-recursive", dest="recursive", action="store_false", help="Only scan the src/ folder directly")
	p.set_defaults(recursive=True)
	p.add_argument("-b", "--backup", dest="backup", action="store_true", help="Create a .bak file before writing the output (default: disabled)")
	p.set_defaults(backup=False)
	p.add_argument("--no-ui", action="store_true", help="Disable the optional display layer (display_layer.py)")
	p.add_argument("--lang", choices=["en", "fr"], help="Select the language of the messages (en or fr).")
	p.add_argument("-i", "--interactive", action="store_true", help="Force the interactive form to open even if --src is given")
	return p

def validate_src_dir(d: str) -> bool | str:
	# Validate the source folder entered in the interactive form
	return os.path.isdir(d) or "This folder does not exist"

def validate_groups_file(p: str) -> bool | str:
	# Validate the groups JSON file entered in the interactive form (empty = skipped)
	if not p:
		return True
	return os.path.isfile(p) or "This file does not exist"

def ask_valid(question: str, default: str, validate: Any, is_path: bool = False) -> str | None:
	# Ask again until the validation function returns True
	while True:
		answer: str | None = (ui.ask_path if is_path else ui.ask)(question, default)
		if answer is None:
			return None
		result: bool | str = validate(answer)
		if result is True:
			return answer
		ui.error(str(result))

def interactive_form(defaults: argparse.Namespace) -> argparse.Namespace:
	# Interactive form exposing every parseable parameter
	ui.section("Dependency map settings")
	ui.info()

	src: str | None = ask_valid("Folder containing the .c and .h files (project root if src/ and/or include/ exist)", defaults.src or "", validate_src_dir, is_path=True)
	if not src:
		ui.warning("Cancelled.")
		sys.exit(0)

	output: str = os.path.join(SCRIPT_DIR, "Dependency_map.html")

	title: str | None = ui.ask("Project title (Enter = source folder name)", defaults.title or "")
	if title is None:
		ui.warning("Cancelled.")
		sys.exit(0)

	default_ext_list: list[str] = (defaults.ext.split(",") if defaults.ext else sorted(DEFAULT_EXTENSIONS))
	selected_ext: list[str] | None = ui.choose_many("Extensions to scan:", sorted(DEFAULT_EXTENSIONS), checked=default_ext_list)
	if selected_ext is None:
		ui.warning("Cancelled.")
		sys.exit(0)
	if not selected_ext:
		ui.warning("No extension selected.")
		sys.exit(0)
	ext: str = ",".join(selected_ext)

	groups: str | None = ask_valid("Groups JSON file (optional, Enter to skip)", defaults.groups or "", validate_groups_file, is_path=True)
	if groups is None:
		ui.warning("Cancelled.")
		sys.exit(0)

	recursive: bool | None = ui.confirm("Scan subfolders recursively?", default=defaults.recursive)
	if recursive is None:
		ui.warning("Cancelled.")
		sys.exit(0)

	backup: bool | None = ui.confirm("Create a .bak backup file before writing the output?", default=defaults.backup)
	if backup is None:
		ui.warning("Cancelled.")
		sys.exit(0)

	ui.info()
	ui.key_values([
		("Source folder", src),
		("Output file", f"{output} (fixed)"),
		("Title", title or "(auto)"),
		("Extensions", ext),
		("Groups file", groups or "(none)"),
		("Recursive", "yes" if recursive else "no"),
		(".bak backup", "yes" if backup else "no"),
	], title="Settings summary")

	confirmed: bool | None = ui.confirm("Start the generation with these settings?", default=True)
	if not confirmed:
		ui.warning("Cancelled.")
		sys.exit(0)

	defaults.src = src
	defaults.output = output
	defaults.title = title or None
	defaults.ext = ext
	defaults.groups = groups or None
	defaults.recursive = recursive
	defaults.backup = backup
	return defaults

def parse_args() -> argparse.Namespace:
	p: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = p.parse_args()

	args.src = args.src or args.src_pos
	args.output = args.output or args.output_pos

	# Without --src (or with -i/--interactive), open the full form
	# exposing every parameter — same logic as the Interface.py menu
	# when no demo is given directly with -d.
	if args.interactive or not args.src:
		splash_screen()
		args = interactive_form(args)
	else:
		if not args.output:
			args.output = os.path.join(SCRIPT_DIR, "Dependency_map.html")
			ui.muted(f"→ output : {args.output}")
		splash_screen()

	return args

def splash_screen() -> None:
	# Clear the console and show the welcome panel
	ui.banner(f"Dependency Map Generator v{VERSION}", "Generate Dependency_map.html from C/C++ sources")

def main() -> None:
	args: argparse.Namespace = parse_args()
	generator: DependencyMapGenerator = DependencyMapGenerator()
	generator.run(args)

main()
