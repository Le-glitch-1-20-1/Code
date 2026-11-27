#!/usr/bin/env python3
import argparse
import hashlib
import logging
import os
import shutil
import subprocess
import sys
import warnings
import pillow_heif
import time
from abc							import ABC, abstractmethod
from collections					import defaultdict
from datetime						import datetime
from pathlib						import Path
from types							import SimpleNamespace
from typing							import Optional
from moviepy.video.io.VideoFileClip	import VideoFileClip
from PIL							import ExifTags, Image, UnidentifiedImageError

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

import json
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

VERSION: str = "1.0.0"
IMAGE_TARGET_EXTENSIONS: set[str] = {".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif", ".jpeg"}
DUPLICATE_SCAN_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
VIDEO_EXTENSIONS: tuple[str, ...] = (
	".mov", ".mkv", ".avi", ".wmv", ".flv", ".webm",
	".m4v", ".3gp", ".mpg", ".mpeg", ".m2ts", ".mts", ".vob",
)
RENAME_EXTENSIONS: set[str] = IMAGE_TARGET_EXTENSIONS | {".jpg", ".jpeg", ".gif"} | set(VIDEO_EXTENSIONS) | {".mp4"}
MENU_CHOICES: list[str] = [
	"Convert images to JPEG",
	"Convert videos to MP4",
	"Detect duplicate images",
	"Rename files by capture date",
	"Quit",
]
logger: logging.Logger = logging.getLogger("media_toolkit")
logger.setLevel(logging.WARNING)
logger.propagate = False
warnings.filterwarnings("ignore", category=UserWarning)
pillow_heif.register_heif_opener()

def info(message: str) -> None:
	# Show a normal message in the console
	ui.info(message)

def warn(message: str) -> None:
	# Show a warning and write it to the log file
	ui.warning(message)
	logger.warning(message)

def error(message: str) -> None:
	# Show an error and write it to the log file
	ui.error(message)
	logger.error(message)

def print_banner() -> None:
	# Show the program header
	ui.banner(f"Media Toolkit v{VERSION}", "Image and video conversion and duplicate detection")

def resolve_path(raw: str) -> Path:
	# Expand "~" and resolve a raw path to an absolute path
	return Path(raw).expanduser().resolve()

def validate_folder(path: Path) -> None:
	# Exit the program if the path is missing, invalid or unreadable
	if not path.exists():
		error(f"The path does not exist: '{path}'")
		sys.exit(1)
	if not path.is_dir():
		error(f"The path is not a folder: '{path}'")
		sys.exit(1)
	if not os.access(path, os.R_OK):
		error(f"No read permission on: '{path}'")
		sys.exit(1)

def print_summary(prefix: str, counts: dict[str, int]) -> None:
	# Show a summary table of the results
	if prefix:
		ui.info(prefix)
	ui.table(["Succeeded", "Ignored", "Failures"], [[counts["success"], counts["skipped"], counts["error"]]])

def hash_image(image_path: Path) -> Optional[str]:
	# Compute an MD5 hash of an image's decoded pixel content
	try:
		with Image.open(image_path) as img:
			img_bytes: bytes = img.convert("RGB").tobytes()
		return hashlib.md5(img_bytes).hexdigest()
	except FileNotFoundError:
		warn(f"File not found: '{image_path}'")
	except PermissionError:
		warn(f"Permission denied: '{image_path}'")
	except UnidentifiedImageError:
		warn(f"Unrecognised image format: '{image_path.name}'")
	except OSError as e:
		warn(f"System error on '{image_path.name}': {e}")
	except Exception as e:
		warn(f"Unexpected error on '{image_path.name}': {e}")
	return None

def load_hashes(hash_file: Path) -> dict[str, dict[str, str]]:
	# Load the image hash database from disk, tolerating malformed lines
	# and lines from an old format (2 fields: hash|file_name, without folder).
	if not hash_file.exists():
		return {}
	hashes: dict[str, dict[str, str]] = defaultdict(dict)
	malformed_count: int = 0
	malformed_examples: list[int] = []
	legacy_count: int = 0
	try:
		with hash_file.open("r", encoding="utf-8") as f:
			for line_num, line in enumerate(f, 1):
				stripped: str = line.strip()
				if not stripped:
					continue
				parts: list[str] = stripped.split("|", 2)
				if len(parts) == 3:
					folder_key, hash_value, file_name = parts
					hashes[folder_key][hash_value] = file_name
				elif len(parts) == 2:
					# Old format without folder_key: store it in the global scope.
					hash_value, file_name = parts
					hashes["_global_"][hash_value] = file_name
					legacy_count += 1
				else:
					malformed_count += 1
					if len(malformed_examples) < 3:
						malformed_examples.append(line_num)
	except PermissionError:
		warn(f"Cannot read the hash file (permission denied): '{hash_file}'.")
	except UnicodeDecodeError:
		warn(f"Hash file encoding error: '{hash_file}'.")
	except OSError as e:
		warn(f"System error while reading the hash file: {e}.")
	if legacy_count:
		warn(f"{legacy_count} line(s) in an old hash file format, converted to global scope.")
	if malformed_count:
		examples: str = ", ".join(str(n) for n in malformed_examples)
		suffix: str = "..." if malformed_count > len(malformed_examples) else ""
		warn(f"{malformed_count} malformed line(s) in the hash file, ignored (e.g. lines {examples}{suffix}).")
	return hashes

def save_hashes(hashes: dict[str, dict[str, str]], hash_file: Path) -> bool:
	# Save the image hash database to disk through a temporary file
	tmp_file: Path = hash_file.with_suffix(".tmp")
	try:
		with tmp_file.open("w", encoding="utf-8") as f:
			for folder_key, folder_hashes in hashes.items():
				for hash_value, file_name in folder_hashes.items():
					f.write(f"{folder_key}|{hash_value}|{file_name}\n")
		tmp_file.replace(hash_file)
		return True
	except PermissionError:
		error(f"Permission denied to write the hash file: '{hash_file}'.")
	except OSError as e:
		error(f"System error while saving the hash file: {e}")
	except Exception as e:
		error(f"Unexpected error while saving the hash file: {e}")
	finally:
		if tmp_file.exists():
			try:
				tmp_file.unlink()
			except OSError:
				pass
	return False

def get_unique_destination(dest_folder: Path, filename: str) -> Path:
	# Build a collision-free destination path by adding a numeric suffix
	dest: Path = dest_folder / filename
	if not dest.exists():
		return dest
	stem: str
	suffix: str
	stem, suffix = Path(filename).stem, Path(filename).suffix
	counter: int = 1
	while dest.exists():
		dest = dest_folder / f"{stem}_{counter}{suffix}"
		counter += 1
	return dest

def resolve_copies_dest(file_path: Path, root_folder: Path, copies_folder: Path, flat: bool) -> Path:
	# Compute the destination folder of a duplicate, mirrored unless "flat"
	if flat:
		return copies_folder
	try:
		relative: Path = file_path.parent.relative_to(root_folder)
		mirrored: Path = copies_folder / relative
		mirrored.mkdir(parents=True, exist_ok=True)
		return mirrored
	except ValueError:
		warn(f"Cannot reproduce the path for '{file_path.name}', falling back to flat.")
		return copies_folder
	except PermissionError:
		warn("Permission denied to create the mirror folder, falling back to flat.")
		return copies_folder
	except OSError as e:
		warn(f"System error while creating the mirror folder: {e}. Falling back to flat.")
		return copies_folder

def safe_move(src: Path, dst: Path) -> bool:
	# Move a file to its destination, log it and return False on failure
	try:
		shutil.move(str(src), dst)
		return True
	except PermissionError:
		error(f"Permission denied to move '{src.name}'.")
	except shutil.Error as e:
		error(f"Move failed for '{src.name}': {e}")
	except OSError as e:
		error(f"System error while moving '{src.name}': {e}")
	except Exception as e:
		error(f"Unexpected error while moving '{src.name}': {e}")
	return False

class MediaProcessor(ABC):
	# Common interface for every media processor of the toolkit
	@abstractmethod
	def collect(self, root: Path, recursive: bool) -> list:
		# List the files to process in the given folder
		raise NotImplementedError

	@abstractmethod
	def run(self, args: argparse.Namespace) -> None:
		# Entry point of the matching subcommand
		raise NotImplementedError

class ImageConverter(MediaProcessor):
	# Convert the supported images of a folder to JPEG
	def collect(self, root: Path, recursive: bool) -> list[Path]:
		# Walk the folder (recursively or not) looking for images to convert
		pattern: str = "**/*" if recursive else "*"
		found: list[Path] = []
		with ui.progress(None, "Scanning (files found)") as progress:
			for p in root.glob(pattern):
				try:
					if p.is_file() and p.suffix.lower() in IMAGE_TARGET_EXTENSIONS:
						found.append(p)
						progress.advance()
				except PermissionError:
					warn(f"Access denied: {p}")
				except OSError as e:
					warn(f"System error on {p}: {e}")
		return found

	def convert_one(self, file_path: Path, quality: int, delete_original: bool, dry_run: bool) -> str:
		# Convert a single image to JPEG, delete the original if requested
		target_path: Path = file_path.with_suffix(".jpg")
		if target_path.exists() and target_path != file_path:
			return "skipped"
		if dry_run:
			return "success"
		try:
			with Image.open(file_path) as img:
				rgb = img.convert("RGB")
				rgb.save(target_path, "JPEG", quality=quality, optimize=True)
			if delete_original and file_path != target_path:
				file_path.unlink()
			return "success"
		except Exception as exc:
			error(f"Failed on {file_path}: {exc}")
			return "error"

	def run(self, args: argparse.Namespace) -> None:
		# Entry point of the "images" subcommand
		root: Path = resolve_path(args.path)
		validate_folder(root)
		if not (1 <= args.quality <= 95):
			error("Quality must be between 1 and 95.")
			sys.exit(1)
		files: list[Path] = self.collect(root, args.recursive)
		if not files:
			info("No file to convert in this folder.")
			return
		prefix: str = tr("[DRY RUN] ") if args.dry_run else ""
		info(f"\n{prefix}Processing {len(files)} file(s)")
		counts: dict[str, int] = {"success": 0, "skipped": 0, "error": 0}
		try:
			with ui.progress(len(files), "Conversion") as progress:
				for file_path in files:
					progress.set_value(description=file_path.name[:30])
					result: str = self.convert_one(file_path, args.quality, args.delete, args.dry_run)
					counts[result] += 1
					progress.advance()
		except KeyboardInterrupt:
			info("\nKeyboard interrupt detected. Stopping.")
		print_summary(prefix, counts)
		if counts["error"]:
			info("Details in the log if the option was enabled.")

class VideoConverter(MediaProcessor):
	# Convert the supported videos of a folder to MP4
	def collect(self, root: Path, recursive: bool) -> list[str]:
		# Walk the folder (recursively or not) looking for videos to convert
		found: list[str] = []
		with ui.progress(None, "Scanning (files found)") as progress:
			if recursive:
				for dirpath, _, files in os.walk(root):
					for filename in files:
						ext: str = os.path.splitext(filename)[1].lower()
						if ext in VIDEO_EXTENSIONS:
							found.append(os.path.join(dirpath, filename))
							progress.advance()
			else:
				for filename in os.listdir(root):
					ext = os.path.splitext(filename)[1].lower()
					if ext in VIDEO_EXTENSIONS:
						found.append(os.path.join(root, filename))
						progress.advance()
		return found

	def convert_one(self, file_path: str, dry_run: bool, delete_original: bool) -> str:
		# Convert a single video to MP4 (H.264 + AAC), delete the original if requested
		directory: str = os.path.dirname(file_path)
		name_part: str = os.path.splitext(os.path.basename(file_path))[0]
		target_path: str = os.path.join(directory, f"{name_part}.mp4")
		if os.path.exists(target_path):
			return "skipped"
		if dry_run:
			return "success"
		try:
			with VideoFileClip(file_path) as clip:
				clip.write_videofile(target_path, codec="libx264", audio_codec="aac", logger=None)
			if delete_original:
				os.remove(file_path)
			return "success"
		except Exception as e:
			error(f"Failed on {file_path}: {e}")
			return "error"

	def run(self, args: argparse.Namespace) -> None:
		# Entry point of the "videos" subcommand
		root: Path = resolve_path(args.path)
		validate_folder(root)
		videos: list[str] = self.collect(root, args.recursive)
		if not videos:
			info("No video found in this folder.")
			return
		prefix: str = tr("[DRY RUN] ") if args.dry_run else ""
		info(f"\n{prefix}Processing {len(videos)} video(s)")
		counts: dict[str, int] = {"success": 0, "skipped": 0, "error": 0}
		try:
			with ui.progress(len(videos), "Conversion") as progress:
				for file_path in videos:
					progress.set_value(description=os.path.basename(file_path)[:30])
					result: str = self.convert_one(file_path, args.dry_run, args.delete)
					counts[result] += 1
					progress.advance()
		except KeyboardInterrupt:
			info("\nKeyboard interrupt detected. Stopping.")
		print_summary(prefix, counts)
		if counts["error"]:
			info("Details in the log if the option was enabled.")

class DuplicateDetector(MediaProcessor):
	# Detect duplicate images by pixel content hash and move them to "copies/"
	def collect(self, root: Path, recursive: bool) -> list[Path]:
		# Walk the folder looking for images to check for duplicates
		found: list[Path] = []
		pattern: str = "**/*" if recursive else "*"
		with ui.progress(None, "Scanning (files found)") as progress:
			for p in root.glob(pattern):
				try:
					if p.is_file() and p.suffix.lower() in DUPLICATE_SCAN_EXTENSIONS:
						found.append(p)
						progress.advance()
				except PermissionError:
					warn(f"Access denied: '{p}'")
				except OSError as e:
					warn(f"System error on '{p}': {e}")
		return found

	def detect_and_move(
		self,
		folder_path: Path,
		recursive: bool = False,
		flat: bool = True,
		dry_run: bool = False,
		global_scope: bool = False,
	) -> None:
		# Detect duplicate images (by pixel content hash) and move the extras to "copies/"
		copies_folder: Path = folder_path / "copies"
		try:
			copies_folder.mkdir(exist_ok=True)
		except PermissionError:
			error(f"Cannot create the 'copies' folder: permission denied in '{folder_path}'.")
			return
		except OSError as e:
			error(f"Cannot create the 'copies' folder: {e}")
			return
		hash_file: Path = copies_folder / "image_hashes.txt"
		error_log: Path = copies_folder / "errors-report.txt"
		file_handler: Optional[logging.FileHandler] = None
		try:
			error_log.write_text("", encoding="utf-8")
			file_handler = logging.FileHandler(error_log, encoding="utf-8")
			file_handler.setLevel(logging.WARNING)
			logger.addHandler(file_handler)
		except PermissionError:
			warn("Cannot write the error log (permission denied).")
		except OSError as e:
			warn(f"Cannot create the error log: {e}.")
		hashes: dict[str, dict[str, str]] = defaultdict(dict, load_hashes(hash_file))
		try:
			info("Looking for image files...")
			files: list[Path] = []
			pattern: str = "**/*" if recursive else "*"
			try:
				with ui.progress(None, "Scanning (files found)") as progress:
					for p in folder_path.glob(pattern):
						try:
							if (
								p.is_file()
								and p.suffix.lower() in DUPLICATE_SCAN_EXTENSIONS
								and copies_folder not in p.parents
								and p.parent != copies_folder
							):
								files.append(p)
								progress.advance()
						except PermissionError:
							warn(f"Access denied: '{p}'")
						except OSError as e:
							warn(f"System error on '{p}': {e}")
			except PermissionError:
				error(f"Cannot list the folder '{folder_path}' : permission denied.")
			except OSError as e:
				error(f"System error while walking the folder: {e}")
			if not files:
				info("No image file found.")
				return
			mode_label: str = "recursive" if recursive else "root folder only"
			dest_label: str = "flat" if flat else "mirror structure"
			scope_label: str = "global (all folders)" if global_scope else "per folder"
			prefix: str = tr("[DRY RUN] ") if dry_run else ""
			info(
				f"\n{prefix}Processing {len(files)} image(s) "
				f"[mode: {mode_label} | copies: {dest_label} | detection: {scope_label}]"
			)
			counts: dict[str, int] = {"success": 0, "skipped": 0, "error": 0}
			moved_details: list[str] = []
			with ui.progress(len(files), "Analysis") as progress:
				for file_path in files:
					progress.set_value(description=file_path.name[:30])
					image_hash: Optional[str] = hash_image(file_path)
					if image_hash is None:
						counts["error"] += 1
						progress.advance()
						continue
					folder_key: str = "_global_" if global_scope else str(file_path.parent.relative_to(folder_path))
					folder_hashes: dict[str, str] = hashes[folder_key]
					if image_hash in folder_hashes:
						dest_dir: Path = resolve_copies_dest(file_path, folder_path, copies_folder, flat)
						dest: Path = get_unique_destination(dest_dir, file_path.name)
						rel_src: Path = file_path.relative_to(folder_path)
						rel_dst: Path = dest.relative_to(folder_path)
						original: str = folder_hashes[image_hash]
						if not dry_run:
							if safe_move(file_path, dest):
								counts["success"] += 1
								moved_details.append(f"{rel_src} -> {rel_dst}  (original: {original})")
							else:
								counts["error"] += 1
						else:
							counts["success"] += 1
							moved_details.append(f"{rel_src} -> {rel_dst}  (original: {original})")
					else:
						folder_hashes[image_hash] = file_path.name
						counts["skipped"] += 1
					progress.advance()
			if not dry_run:
				if not save_hashes(hashes, hash_file):
					warn("The hash file could not be saved. Progress may be lost.")
			if moved_details:
				action: str = "detected" if dry_run else "moved"
				ui.info(f"\n{prefix}{len(moved_details)} duplicate(s) {action} :")
				for f in moved_details:
					info(f"  - {f}")
			print_summary(prefix, counts)
			if counts["error"]:
				info(f"Details: {error_log}")
			ui.success("Done.")
		except KeyboardInterrupt:
			info("\nKeyboard interrupt detected. Saving hashes...")
			if not dry_run:
				save_hashes(hashes, hash_file)
			info("Hashes saved. Clean exit.")
		except Exception as e:
			error(f"\nUnexpected fatal error: {e}")
			if not dry_run:
				info("Trying to save the hashes before exiting...")
				save_hashes(hashes, hash_file)
			raise
		finally:
			if file_handler:
				logger.removeHandler(file_handler)
				try:
					file_handler.close()
				except Exception:
					pass

	def run(self, args: argparse.Namespace) -> None:
		# Entry point of the "duplicates" subcommand
		folder_path: Path = resolve_path(args.path)
		validate_folder(folder_path)
		self.detect_and_move(
			folder_path,
			recursive=args.recursive,
			flat=args.flat,
			dry_run=args.dry_run,
			global_scope=args.global_scope,
		)

def get_image_datetime(file_path: Path) -> Optional[datetime]:
	# Read the capture date from an image's EXIF metadata
	try:
		with Image.open(file_path) as img:
			exif = img.getexif()
			date_str: Optional[str] = None
			try:
				exif_ifd: dict = exif.get_ifd(ExifTags.IFD.Exif)
				date_str = exif_ifd.get(36867) or exif_ifd.get(36868)  # DateTimeOriginal, DateTimeDigitized
			except Exception:
				pass
			if not date_str:
				date_str = exif.get(306)  # DateTime (standard tag)
			if date_str:
				return datetime.strptime(str(date_str).strip(), "%Y:%m:%d %H:%M:%S")
	except Exception:
		pass
	return None

def get_video_datetime(file_path: Path) -> Optional[datetime]:
	# Read a video's creation date with ffprobe (already used by moviepy/ffmpeg)
	try:
		result = subprocess.run(
			[
				"ffprobe", "-v", "quiet",
				"-show_entries", "format_tags=creation_time",
				"-of", "default=noprint_wrappers=1:nokey=1",
				str(file_path),
			],
			capture_output=True, text=True, timeout=15,
		)
		value: str = result.stdout.strip()
		if value:
			return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
	except Exception:
		pass
	return None

def get_capture_datetime(file_path: Path) -> datetime:
	# Determine a file's capture date: metadata if possible, otherwise modification date
	ext: str = file_path.suffix.lower()
	dt: Optional[datetime] = None
	if ext in VIDEO_EXTENSIONS or ext == ".mp4":
		dt = get_video_datetime(file_path)
	else:
		dt = get_image_datetime(file_path)
	if dt is None:
		try:
			dt = datetime.fromtimestamp(file_path.stat().st_mtime)
		except Exception:
			dt = datetime.now()
	return dt

def format_date_key(dt: datetime) -> str:
	# Format a date as "DD-MM-YYYY_HHhMM", e.g. 12-12-2009_12h05
	return dt.strftime("%d-%m-%Y_%Hh%M")

class MediaRenamer(MediaProcessor):
	# Rename media files by capture date (photo/video), with a -N suffix on ties
	def collect(self, root: Path, recursive: bool) -> list[Path]:
		# Walk the folder (recursively or not) looking for files to rename
		pattern: str = "**/*" if recursive else "*"
		found: list[Path] = []
		with ui.progress(None, "Scanning (files found)") as progress:
			for p in root.glob(pattern):
				try:
					if p.is_file() and p.suffix.lower() in RENAME_EXTENSIONS:
						found.append(p)
						progress.advance()
				except PermissionError:
					warn(f"Access denied: '{p}'")
				except OSError as e:
					warn(f"System error on '{p}': {e}")
		return found

	def rename_all(self, folder_path: Path, recursive: bool, dry_run: bool) -> None:
		# Rename every file found by its capture date, adding "-N" when several
		# files share the same date and minute.
		info("Looking for files to rename...")
		files: list[Path] = self.collect(folder_path, recursive)
		if not files:
			info("No file to rename in this folder.")
			return
		prefix: str = tr("[DRY RUN] ") if dry_run else ""
		info(f"\n{prefix}Processing {len(files)} file(s)")
		groups: dict[tuple[Path, str], list[Path]] = defaultdict(list)
		for f in files:
			date_key: str = format_date_key(get_capture_datetime(f))
			groups[(f.parent, date_key)].append(f)
		for group_files in groups.values():
			group_files.sort(key=lambda p: (p.stat().st_mtime if p.exists() else 0, p.name))
		counts: dict[str, int] = {"success": 0, "skipped": 0, "error": 0}
		renamed_details: list[str] = []
		try:
			with ui.progress(len(files), "Renaming") as progress:
				for (parent, date_key), group_files in groups.items():
					use_suffix: bool = len(group_files) > 1
					for index, file_path in enumerate(group_files, start=1):
						progress.set_value(description=file_path.name[:30])
						suffix: str = f"-{index}" if use_suffix else ""
						new_name: str = f"{date_key}{suffix}{file_path.suffix}"
						dest: Path = parent / new_name
						if dest == file_path:
							counts["skipped"] += 1
							progress.advance()
							continue
						if dest.exists():
							dest = get_unique_destination(parent, new_name)
						if dry_run:
							counts["success"] += 1
							renamed_details.append(f"{file_path.name} -> {dest.name}")
						else:
							try:
								file_path.rename(dest)
								counts["success"] += 1
								renamed_details.append(f"{file_path.name} -> {dest.name}")
							except PermissionError:
								error(f"Permission denied to rename '{file_path.name}'.")
								counts["error"] += 1
							except OSError as e:
								error(f"System error while renaming '{file_path.name}': {e}")
								counts["error"] += 1
						progress.advance()
		except KeyboardInterrupt:
			info("\nKeyboard interrupt detected. Stopping.")
		if renamed_details:
			action: str = "detected" if dry_run else "renamed"
			ui.info(f"\n{prefix}{len(renamed_details)} file(s) {action} :")
			for line in renamed_details:
				info(f"  - {line}")
		print_summary(prefix, counts)

	def run(self, args: argparse.Namespace) -> None:
		# Entry point of the "rename" subcommand
		folder_path: Path = resolve_path(args.path)
		validate_folder(folder_path)
		self.rename_all(folder_path, recursive=args.recursive, dry_run=args.dry_run)

IMAGE_CONVERTER: ImageConverter = ImageConverter()
VIDEO_CONVERTER: VideoConverter = VideoConverter()
DUPLICATE_DETECTOR: DuplicateDetector = DuplicateDetector()
MEDIA_RENAMER: MediaRenamer = MediaRenamer()

def run_images_interactive() -> None:
	# Collect the image conversion options
	path: Optional[str] = ui.ask_path("Path of the folder to process")
	if not path:
		return
	quality = ui.ask_number("JPEG quality, 1-95", 95, minimum=1, maximum=95)
	if quality is None:
		return
	recursive: Optional[bool] = ui.confirm("Also scan subfolders?", default=True)
	delete: Optional[bool] = ui.confirm("Delete the originals after conversion?", default=False)
	dry_run: Optional[bool] = ui.confirm("Simulate without converting any file?", default=False)
	IMAGE_CONVERTER.run(SimpleNamespace(path=path, quality=int(quality), recursive=bool(recursive), delete=bool(delete), dry_run=bool(dry_run)))

def run_videos_interactive() -> None:
	# Collect the video conversion options
	path: Optional[str] = ui.ask_path("Path of the folder to process")
	if not path:
		return
	recursive: Optional[bool] = ui.confirm("Also scan subfolders?", default=True)
	delete: Optional[bool] = ui.confirm("Delete the originals after conversion?", default=False)
	dry_run: Optional[bool] = ui.confirm("Simulate without converting any file?", default=False)
	VIDEO_CONVERTER.run(SimpleNamespace(path=path, recursive=bool(recursive), delete=bool(delete), dry_run=bool(dry_run)))

def show_flat_vs_mirror_trees() -> None:
	# Illustrate, with two trees, the difference between
	# the "flat" and "mirrored" ways of storing duplicates.
	ui.info("Example: duplicates found here...")
	ui.tree("photos/", [("vacances/", ["plage.jpg"]), ("famille/", ["noel.jpg"])])
	ui.info()
	ui.info("...will be stored like this:")
	ui.tree("copies/  (flat)", ["plage.jpg", "noel.jpg"])
	ui.info()
	ui.tree("copies/  (mirrored)", [("vacances/", ["plage.jpg"]), ("famille/", ["noel.jpg"])])
	ui.info()

def run_duplicates_interactive() -> None:
	# Collect the duplicate detection options
	path: Optional[str] = ui.ask_path("Path of the folder to scan")
	if not path:
		return
	recursive: Optional[bool] = ui.confirm("Also scan subfolders?", default=False)
	show_flat_vs_mirror_trees()
	flat: Optional[bool] = ui.confirm(
		"Move duplicates flat (a single 'copies/' folder) rather than mirrored (subfolders reproduced)?",
		default=True,
	)
	global_scope: Optional[bool] = ui.confirm("Detect duplicates across all folders at once?", default=False)
	dry_run: Optional[bool] = ui.confirm("Simulate without moving any file?", default=False)
	DUPLICATE_DETECTOR.run(SimpleNamespace(path=path, recursive=bool(recursive), flat=flat is not False, global_scope=bool(global_scope), dry_run=bool(dry_run)))

def run_rename_interactive() -> None:
	# Collect the renaming options
	path: Optional[str] = ui.ask_path("Path of the folder to process")
	if not path:
		return
	recursive: Optional[bool] = ui.confirm("Also scan subfolders?", default=True)
	ui.info("Format: DD-MM-YYYY_HHhMM, e.g. 12-12-2009_12h05 (a -N number is added on ties).")
	dry_run: Optional[bool] = ui.confirm("Simulate without renaming any file?", default=False)
	MEDIA_RENAMER.run(SimpleNamespace(path=path, recursive=bool(recursive), dry_run=bool(dry_run)))

def run_interactive_menu() -> None:
	# Interactive menu shown when the script is run without a subcommand
	choice: Optional[str] = ui.choose("What would you like to do?", MENU_CHOICES)
	if choice is None or "Quit" in choice:
		ui.success("See you soon!")
		sys.exit(0)
	ui.info()
	if "duplicate" in choice:
		run_duplicates_interactive()
	elif "Rename" in choice:
		run_rename_interactive()
	elif "images" in choice:
		run_images_interactive()
	elif "videos" in choice:
		run_videos_interactive()

def build_parser() -> argparse.ArgumentParser:
	# Build the argparse CLI: global options and images/videos/duplicates subcommands
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		prog="media_toolkit.py",
		description="Convert images to JPEG, videos to MP4, detect/move duplicate images, or rename files by capture date.",
		epilog=(
			"Examples:\n"
			"  media_toolkit.py images /path/to/folder\n"
			"  media_toolkit.py videos /path/to/folder --no-recursive\n"
			"  media_toolkit.py duplicates /path/to/folder --recursive --dry-run\n"
			"  media_toolkit.py rename /path/to/folder --recursive\n"
		),
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}", help="Print the program version and exit.")
	parser.add_argument("--no-ui", action="store_true", help="Disable the optional display layer (display_layer.py).")
	parser.add_argument("--lang", choices=["en", "fr"], help="Select the language of the messages (en or fr).")
	subparsers = parser.add_subparsers(dest="command", required=False, metavar="{images,videos,duplicates,rename}")
	images_parser: argparse.ArgumentParser = subparsers.add_parser(
		"images",
		help="Convert images (PNG, WEBP, BMP, TIFF, HEIC/HEIF, ...) to JPEG.",
		description="Convert every supported image in a folder to JPEG.",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	)
	images_parser.add_argument("path", help="Path of the folder to process.")
	images_parser.add_argument("--quality", type=int, default=95, metavar="N", help="JPEG quality, 1-95.")
	images_parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True, help="Also scan subfolders.")
	images_parser.add_argument("--delete", action=argparse.BooleanOptionalAction, default=False, help="Delete the originals after conversion.")
	images_parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=False, help="Simulate without converting any file.")
	images_parser.set_defaults(func=IMAGE_CONVERTER.run)
	videos_parser: argparse.ArgumentParser = subparsers.add_parser(
		"videos",
		help="Convert videos (MOV, MKV, AVI, WMV, ...) to MP4.",
		description="Convert every supported video in a folder to MP4 (H.264 + AAC).",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	)
	videos_parser.add_argument("path", help="Path of the folder to process.")
	videos_parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True, help="Also scan subfolders.")
	videos_parser.add_argument("--delete", action=argparse.BooleanOptionalAction, default=False, help="Delete the originals after conversion.")
	videos_parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=False, help="Simulate without converting any file.")
	videos_parser.set_defaults(func=VIDEO_CONVERTER.run)
	duplicates_parser: argparse.ArgumentParser = subparsers.add_parser(
		"duplicates",
		help="Detect duplicate images and move them to a 'copies' subfolder.",
		description="Detect visually identical images (pixel content hash) and move the extras to 'copies'.",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	)
	duplicates_parser.add_argument("path", help="Path of the folder to scan.")
	duplicates_parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=False, help="Also scan subfolders.")
	duplicates_parser.add_argument(
		"--flat",
		action=argparse.BooleanOptionalAction,
		default=True,
		help=(
			"Move duplicates flat, all grouped in 'copies/' (default), "
			"rather than mirrored, where 'copies/' reproduces the same subfolder tree "
			"as the one where each duplicate was found."
		),
	)
	duplicates_parser.add_argument("--global-scope", action=argparse.BooleanOptionalAction, default=False, help="Detect duplicates across all folders at once.")
	duplicates_parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=False, help="Simulate without moving any file.")
	duplicates_parser.set_defaults(func=DUPLICATE_DETECTOR.run)
	rename_parser: argparse.ArgumentParser = subparsers.add_parser(
		"rename",
		help="Rename photos/videos by capture date (DD-MM-YYYY_HHhMM).",
		description="Rename every media file by its capture date (EXIF for photos, ffprobe metadata for videos, otherwise modification date). Adds a -N suffix when several files share the same date and minute.",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	)
	rename_parser.add_argument("path", help="Path of the folder to process.")
	rename_parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True, help="Also scan subfolders.")
	rename_parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=False, help="Simulate without renaming any file.")
	rename_parser.set_defaults(func=MEDIA_RENAMER.run)
	return parser

def main() -> None:
	# Entry point: parse the arguments, show the banner, then run the chosen command
	parser: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = parser.parse_args()
	print_banner()
	if not args.command:
		run_interactive_menu()
		return
	args.func(args)

if __name__ == "__main__":
	main()
