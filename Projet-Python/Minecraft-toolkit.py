#!/usr/bin/env python3
"""Minecraft world analysis toolkit: map area calculator and dragon egg finder."""
import argparse
import gzip
import io
import os
import struct
import sys
import time
import zlib
from abc			import ABC, abstractmethod
from dataclasses	import dataclass
from typing			import Optional

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

TARGET_EGG: str = "minecraft:dragon_egg"

CONTAINER_TYPES: set[str] = {
	"minecraft:chest",
	"minecraft:trapped_chest",
	"minecraft:barrel",
	"minecraft:shulker_box",
	"minecraft:white_shulker_box",
	"minecraft:light_gray_shulker_box",
	"minecraft:gray_shulker_box",
	"minecraft:black_shulker_box",
	"minecraft:brown_shulker_box",
	"minecraft:red_shulker_box",
	"minecraft:orange_shulker_box",
	"minecraft:yellow_shulker_box",
	"minecraft:lime_shulker_box",
	"minecraft:green_shulker_box",
	"minecraft:cyan_shulker_box",
	"minecraft:light_blue_shulker_box",
	"minecraft:blue_shulker_box",
	"minecraft:purple_shulker_box",
	"minecraft:magenta_shulker_box",
	"minecraft:pink_shulker_box",
	"minecraft:hopper",
	"minecraft:dropper",
	"minecraft:dispenser",
	"minecraft:furnace",
	"minecraft:blast_furnace",
	"minecraft:smoker",
	"minecraft:brewing_stand",
	"minecraft:ender_chest",
	"minecraft:chiseled_bookshelf",
	"minecraft:crafter",
}

DIMS_VANILLA: list[tuple[str, str]] = [
	("Overworld", "region"),
	("Nether", os.path.join("DIM-1", "region")),
	("End", os.path.join("DIM1", "region")),
]
DIMS_PAPER: list[tuple[str, str]] = [
	("Overworld", os.path.join("world", "region")),
	("Nether", os.path.join("world_nether", "DIM-1", "region")),
	("End", os.path.join("world_the_end", "DIM1", "region")),
]
MENU_CHOICES: list[str] = [
	"Compute the map area",
	"Find the dragon egg",
	"Quit",
]
TAG_END: int = 0
TAG_BYTE: int = 1
TAG_SHORT: int = 2
TAG_INT: int = 3
TAG_LONG: int = 4
TAG_FLOAT: int = 5
TAG_DOUBLE: int = 6
TAG_BYTE_ARRAY: int = 7
TAG_STRING: int = 8
TAG_LIST: int = 9
TAG_COMPOUND: int = 10
TAG_INT_ARRAY: int = 11
TAG_LONG_ARRAY: int = 12

@dataclass
class AreaResult:
	# Result of scanning a dimension for the area computation
	chunks: int
	blocks: int
	mca_count: int
	min_bx: int
	max_bx: int
	min_bz: int
	max_bz: int
	span_x: int
	span_z: int

@dataclass
class EggBlock:
	# Position of a dragon egg placed as a block in the world
	dimension: str
	x: int
	y: int
	z: int

@dataclass
class EggContainer:
	# Position of a dragon egg stored in a container
	dimension: str
	container: str
	x: int
	y: int
	z: int

class MinecraftTool(ABC):
	# Common interface for every tool of the toolkit

	@abstractmethod
	def run(self, save_dir: str) -> None:
		raise NotImplementedError

def detect_dims(save_dir: str) -> tuple[list[tuple[str, str]], str]:
	# Detect whether the save uses the Vanilla or Paper/Spigot layout
	if os.path.isdir(os.path.join(save_dir, "world")):
		return DIMS_PAPER, "Paper/Spigot"
	if os.path.isdir(os.path.join(save_dir, "region")):
		return DIMS_VANILLA, "Vanilla"
	return DIMS_PAPER, "unknown"

def fmt_big(n: int) -> str:
	# Format a large number with a space separator
	return f"{n:,}".replace(",", " ")

def bar(ratio: float, width: int = 30) -> str:
	# Build an ASCII progress bar
	filled: int = round(ratio * width)
	return "\u2588" * filled + "\u2591" * (width - filled)

def read_fmt(buf: io.BytesIO, fmt: str) -> int:
	# Read and decode a binary value with the given format
	size: int = struct.calcsize(fmt)
	return struct.unpack(fmt, buf.read(size))[0]

def read_string(buf: io.BytesIO) -> str:
	# Read a length-prefixed NBT string
	length: int = read_fmt(buf, ">H")
	return buf.read(length).decode("utf-8", errors="replace")

def skip_payload(buf: io.BytesIO, tag_type: int) -> None:
	# Move forward in the buffer without decoding the tag value
	if tag_type == TAG_BYTE:
		buf.read(1)
	elif tag_type == TAG_SHORT:
		buf.read(2)
	elif tag_type == TAG_INT:
		buf.read(4)
	elif tag_type == TAG_LONG:
		buf.read(8)
	elif tag_type == TAG_FLOAT:
		buf.read(4)
	elif tag_type == TAG_DOUBLE:
		buf.read(8)
	elif tag_type == TAG_BYTE_ARRAY:
		n: int = read_fmt(buf, ">i")
		buf.read(n)
	elif tag_type == TAG_STRING:
		read_string(buf)
	elif tag_type == TAG_LIST:
		elem_type: int = read_fmt(buf, ">b")
		count: int = read_fmt(buf, ">i")
		for _ in range(count):
			skip_payload(buf, elem_type)
	elif tag_type == TAG_COMPOUND:
		while True:
			t: int = read_fmt(buf, ">b")
			if t == TAG_END:
				break
			read_string(buf)
			skip_payload(buf, t)
	elif tag_type == TAG_INT_ARRAY:
		n = read_fmt(buf, ">i")
		buf.read(n * 4)
	elif tag_type == TAG_LONG_ARRAY:
		n = read_fmt(buf, ">i")
		buf.read(n * 8)

def parse_payload(buf: io.BytesIO, tag_type: int) -> object:
	# Decode the value of an NBT tag according to its type
	if tag_type == TAG_BYTE:
		return read_fmt(buf, ">b")
	if tag_type == TAG_SHORT:
		return read_fmt(buf, ">h")
	if tag_type == TAG_INT:
		return read_fmt(buf, ">i")
	if tag_type == TAG_LONG:
		return read_fmt(buf, ">q")
	if tag_type == TAG_FLOAT:
		return read_fmt(buf, ">f")
	if tag_type == TAG_DOUBLE:
		return read_fmt(buf, ">d")
	if tag_type == TAG_BYTE_ARRAY:
		n: int = read_fmt(buf, ">i")
		return buf.read(n)
	if tag_type == TAG_STRING:
		return read_string(buf)
	if tag_type == TAG_LIST:
		elem_type: int = read_fmt(buf, ">b")
		count: int = read_fmt(buf, ">i")
		return [parse_payload(buf, elem_type) for _ in range(count)]
	if tag_type == TAG_COMPOUND:
		return parse_compound(buf)
	if tag_type == TAG_INT_ARRAY:
		n = read_fmt(buf, ">i")
		return list(struct.unpack(f">{n}i", buf.read(n * 4)))
	if tag_type == TAG_LONG_ARRAY:
		n = read_fmt(buf, ">i")
		return list(struct.unpack(f">{n}q", buf.read(n * 8)))
	return None

def parse_compound(buf: io.BytesIO) -> dict[str, object]:
	# Decode an NBT compound tag into a Python dictionary
	result: dict[str, object] = {}
	while True:
		tag_type: int = read_fmt(buf, ">b")
		if tag_type == TAG_END:
			break
		name: str = read_string(buf)
		result[name] = parse_payload(buf, tag_type)
	return result

def parse_nbt_root(data: bytes) -> dict[str, object]:
	# Decode the root of an already decompressed NBT document
	buf: io.BytesIO = io.BytesIO(data)
	tag_type: int = read_fmt(buf, ">b")
	if tag_type == TAG_END:
		return {}
	read_string(buf)
	payload: object = parse_payload(buf, tag_type)
	return payload if isinstance(payload, dict) else {}

def decode_section(section: dict[str, object]) -> list[str]:
	# Decode the palette and block indices of a chunk section
	block_states: object = section.get("block_states") or section
	if not isinstance(block_states, dict):
		return []
	palette: list[object] = block_states.get("palette") or block_states.get("Palette") or []
	data: Optional[list[int]] = block_states.get("data") or block_states.get("Data")
	if not palette:
		return []
	names: list[str] = []
	entry: object
	for entry in palette:
		name: str = (entry.get("Name") or entry.get("name") or "") if isinstance(entry, dict) else str(entry)
		names.append(name)
	if data is None or len(data) == 0:
		return [names[0]] * 4096
	bits_per_block: int = max(4, (len(palette) - 1).bit_length())
	mask: int = (1 << bits_per_block) - 1
	blocks: list[str] = []
	long_val: int
	for long_val in data:
		if long_val < 0:
			long_val += 1 << 64
		num_per_long: int = 64 // bits_per_block
		i: int
		for i in range(num_per_long):
			idx: int = (long_val >> (i * bits_per_block)) & mask
			blocks.append(names[idx] if idx < len(names) else "minecraft:air")
			if len(blocks) == 4096:
				break
		if len(blocks) >= 4096:
			break
	return blocks[:4096]

def block_index_to_local(index: int) -> tuple[int, int, int]:
	# Convert a linear block index to local x, y, z coordinates
	y: int = (index >> 8) & 0xF
	z: int = (index >> 4) & 0xF
	x: int = index & 0xF
	return x, y, z

def iter_chunks(mca_path: str) -> list[bytes]:
	# Extract and decompress the NBT data of every chunk in a .mca file
	chunks: list[bytes] = []
	with open(mca_path, "rb") as f:
		header: bytes = f.read(4096)
		if len(header) < 4096:
			return chunks
		i: int
		for i in range(1024):
			offset_bytes: bytes = header[i * 4:i * 4 + 4]
			offset: int = (offset_bytes[0] << 16) | (offset_bytes[1] << 8) | offset_bytes[2]
			sectors: int = offset_bytes[3]
			if offset == 0 and sectors == 0:
				continue
			f.seek(offset * 4096)
			length: int = struct.unpack(">I", f.read(4))[0]
			comp_type: int = struct.unpack(">B", f.read(1))[0]
			raw: bytes = f.read(length - 1)
			try:
				if comp_type == 2:
					data: bytes = zlib.decompress(raw)
				elif comp_type == 1:
					data = gzip.decompress(raw)
				else:
					data = raw
				chunks.append(data)
			except Exception:
				continue
	return chunks

def search_items_for_egg(items: object) -> bool:
	# Recursively walk a list of NBT objects to find the dragon egg
	if not isinstance(items, list):
		return False
	item: object
	for item in items:
		if not isinstance(item, dict):
			continue
		item_id: str = item.get("id") or item.get("Id") or ""
		if item_id == TARGET_EGG:
			return True
		tag: object = item.get("tag") or item.get("Tag") or {}
		if isinstance(tag, dict):
			sub_be: object = tag.get("BlockEntityTag") or {}
			if isinstance(sub_be, dict):
				sub_items: object = sub_be.get("Items") or sub_be.get("items") or []
				if search_items_for_egg(sub_items):
					return True
			nested_items: object = tag.get("Items") or tag.get("items") or []
			if search_items_for_egg(nested_items):
				return True
		direct: object = item.get("Items") or item.get("items") or []
		if search_items_for_egg(direct):
			return True
	return False

class AreaCalculator(MinecraftTool):
	# Compute the area of generated chunks in each dimension

	def count_chunks_in_mca(self, mca_path: str) -> int:
		# Count the chunks present in a .mca file
		count: int = 0
		try:
			with open(mca_path, "rb") as f:
				header: bytes = f.read(4096)
			if len(header) < 4096:
				return 0
			i: int
			for i in range(1024):
				b: bytes = header[i * 4:i * 4 + 4]
				offset: int = (b[0] << 16) | (b[1] << 8) | b[2]
				sectors: int = b[3]
				if offset != 0 or sectors != 0:
					count += 1
		except Exception:
			pass
		return count

	def scan_dimension(self, save_dir: str, rel_path: str) -> Optional[AreaResult]:
		# Scan a dimension and compute its bounds and area
		region_dir: str = os.path.join(save_dir, rel_path)
		if not os.path.isdir(region_dir):
			return None
		mca_files: list[str] = [f for f in os.listdir(region_dir) if f.endswith(".mca")]
		if not mca_files:
			return None
		total_chunks: int = 0
		min_rx: int = 999999
		min_rz: int = 999999
		max_rx: int = -999999
		max_rz: int = -999999
		mca_file: str
		for mca_file in mca_files:
			parts: list[str] = mca_file.split(".")
			try:
				rx: int = int(parts[1])
				rz: int = int(parts[2])
			except (IndexError, ValueError):
				continue
			min_rx = min(min_rx, rx)
			max_rx = max(max_rx, rx)
			min_rz = min(min_rz, rz)
			max_rz = max(max_rz, rz)
			path: str = os.path.join(region_dir, mca_file)
			total_chunks += self.count_chunks_in_mca(path)
		min_bx: int = min_rx * 32 * 16
		max_bx: int = (max_rx + 1) * 32 * 16 - 1
		min_bz: int = min_rz * 32 * 16
		max_bz: int = (max_rz + 1) * 32 * 16 - 1
		return AreaResult(
			chunks=total_chunks,
			blocks=total_chunks * 16 * 16,
			mca_count=len(mca_files),
			min_bx=min_bx,
			max_bx=max_bx,
			min_bz=min_bz,
			max_bz=max_bz,
			span_x=max_bx - min_bx + 1,
			span_z=max_bz - min_bz + 1,
		)

	def run(self, save_dir: str) -> None:
		# Show the area analysis for every dimension found
		dims: list[tuple[str, str]]
		server_type: str
		dims, server_type = detect_dims(save_dir)
		ui.section("Map area")
		ui.muted(save_dir)
		ui.muted(f"Detected structure: {server_type}\n")
		results: dict[str, AreaResult] = {}
		dim_name: str
		rel_path: str
		for dim_name, rel_path in dims:
			data: Optional[AreaResult] = self.scan_dimension(save_dir, rel_path)
			if data is not None:
				results[dim_name] = data
		if not results:
			ui.warning("No dimension found in this folder.")
			return
		max_chunks: int = max(r.chunks for r in results.values()) or 1
		for dim_name, data in results.items():
			ratio: float = data.chunks / max_chunks
			ui.key_values([
				(".mca files", fmt_big(data.mca_count)),
				("Generated chunks", fmt_big(data.chunks)),
				("Area", f"{fmt_big(data.blocks)} blocks² ({data.blocks / 1_000_000:.2f} km2)"),
				("X span", f"{data.min_bx} -> {data.max_bx}"),
				("Z span", f"{data.min_bz} -> {data.max_bz}"),
				("Progression", f"{bar(ratio)} {ratio * 100:.1f}%"),
			], title=dim_name)
		total_chunks: int = sum(r.chunks for r in results.values())
		total_blocks: int = sum(r.blocks for r in results.values())
		ui.key_values([
			("Total chunks", fmt_big(total_chunks)),
			("Total area", f"{fmt_big(total_blocks)} blocks² ({total_blocks / 1_000_000:.2f} km2)"),
		], title="Total, all dimensions")

class DragonEggFinder(MinecraftTool):
	# Look for the dragon egg placed as a block or stored in a container

	def scan_chunk(self, nbt: dict[str, object], blocks_out: list[EggBlock], containers_out: list[EggContainer], dim_label: str) -> None:
		# Scan a decoded chunk looking for the dragon egg
		level: object = nbt.get("Level") or nbt
		if not isinstance(level, dict):
			return
		cx: int = level.get("xPos") or level.get("XPos") or 0
		cz: int = level.get("zPos") or level.get("ZPos") or 0
		sections: object = level.get("sections") or level.get("Sections") or []
		section: object
		if isinstance(sections, list):
			for section in sections:
				if not isinstance(section, dict):
					continue
				sy: object = section.get("Y") or section.get("y")
				if sy is None:
					continue
				blocks: list[str] = decode_section(section)
				idx: int
				name: str
				for idx, name in enumerate(blocks):
					if name == TARGET_EGG:
						lx: int
						ly: int
						lz: int
						lx, ly, lz = block_index_to_local(idx)
						blocks_out.append(EggBlock(dim_label, cx * 16 + lx, int(sy) * 16 + ly, cz * 16 + lz))
		be_list: object = level.get("block_entities") or level.get("TileEntities") or level.get("tileEntities") or []
		be: object
		if isinstance(be_list, list):
			for be in be_list:
				if not isinstance(be, dict):
					continue
				be_id: str = be.get("id") or be.get("Id") or ""
				if not be_id.startswith("minecraft:"):
					be_id = "minecraft:" + be_id.lower()
				if be_id not in CONTAINER_TYPES:
					continue
				items: object = be.get("Items") or be.get("items") or []
				if search_items_for_egg(items):
					bx: int = be.get("x") or be.get("X") or 0
					by: int = be.get("y") or be.get("Y") or 0
					bz: int = be.get("z") or be.get("Z") or 0
					containers_out.append(EggContainer(dim_label, be_id.replace("minecraft:", ""), bx, by, bz))

	def scan_region_dir(self, region_dir: str, dim_label: str, blocks_out: list[EggBlock], containers_out: list[EggContainer]) -> None:
		# Scan every .mca file of a region folder
		if not os.path.isdir(region_dir):
			return
		mca_files: list[str] = sorted(f for f in os.listdir(region_dir) if f.endswith(".mca"))
		mca_file: str
		for mca_file in mca_files:
			path: str = os.path.join(region_dir, mca_file)
			chunk_data: bytes
			for chunk_data in iter_chunks(path):
				try:
					nbt: dict[str, object] = parse_nbt_root(chunk_data)
					self.scan_chunk(nbt, blocks_out, containers_out, dim_label)
				except Exception:
					continue

	def run(self, save_dir: str) -> None:
		# Show the dragon egg locations found
		dims: list[tuple[str, str]]
		server_type: str
		dims, server_type = detect_dims(save_dir)
		ui.section("Searching for the dragon egg")
		ui.muted(f"Detected structure: {server_type}\n")
		all_blocks: list[EggBlock] = []
		all_containers: list[EggContainer] = []
		dim_label: str
		rel_path: str
		for dim_label, rel_path in dims:
			region_dir: str = os.path.join(save_dir, rel_path)
			with ui.status(f"Scanning {dim_label}"):
				self.scan_region_dir(region_dir, dim_label, all_blocks, all_containers)
		if not all_blocks and not all_containers:
			ui.warning("No dragon egg found in any dimension.")
			return
		if all_blocks:
			ui.table(
				["Dimension", "X", "Y", "Z"],
				[[eb.dimension, eb.x, eb.y, eb.z] for eb in sorted(all_blocks, key=lambda r: (r.x, r.z))],
				title="Dragon egg placed in the world",
			)
		if all_containers:
			ui.table(
				["Dimension", "Container", "X", "Y", "Z"],
				[[ec.dimension, ec.container, ec.x, ec.y, ec.z] for ec in sorted(all_containers, key=lambda r: (r.x, r.z))],
				title="Dragon egg in a container",
			)
		total: int = len(all_blocks) + len(all_containers)
		ui.success(f"Total: {total} location(s) found")

def splash_screen() -> None:
	# Show the welcome banner
	ui.banner("Minecraft Toolkit", "Minecraft save analysis")

def prompt_save_dir() -> Optional[str]:
	# Ask the user for the save folder path
	path: Optional[str] = ui.ask_path("Path of the save folder")
	if path is None:
		return None
	path = os.path.expanduser(path)
	if not os.path.isdir(path):
		ui.error(f"'{path}' is not a valid folder.")
		return None
	return path

def run_interactive_menu() -> None:
	# Main interactive menu loop
	splash_screen()
	while True:
		choice: Optional[str] = ui.choose("What do you want to do?", MENU_CHOICES)
		if choice is None or choice == "Quit":
			ui.info("Goodbye!")
			break
		save_dir: Optional[str] = prompt_save_dir()
		if save_dir is not None:
			ui.info()
			tool: MinecraftTool = AreaCalculator() if choice == MENU_CHOICES[0] else DragonEggFinder()
			tool.run(save_dir)
		ui.pause("Press Enter to return to the menu...")
		splash_screen()

def parse_args() -> argparse.Namespace:
	# Define and parse the command-line arguments
	parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Minecraft world analysis toolkit.")
	parser.add_argument("--no-ui", action="store_true", help="Disable the optional display layer (display_layer.py)")
	parser.add_argument("--lang", choices=["en", "fr"], help="Select the language of the messages (en or fr).")
	parser.add_argument("--dir", type=str, default=None, help="Path of the save folder")
	parser.add_argument("--mode", type=str, choices=["area", "egg"], default=None, help="Tool to run directly")
	return parser.parse_args()

def main() -> None:
	# Program entry point
	args: argparse.Namespace = parse_args()
	if args.dir is not None and args.mode is not None:
		save_dir: str = os.path.expanduser(args.dir)
		if not os.path.isdir(save_dir):
			ui.error(f"'{save_dir}' is not a valid folder.")
			sys.exit(1)
		tool: MinecraftTool = AreaCalculator() if args.mode == "area" else DragonEggFinder()
		tool.run(save_dir)
	else:
		run_interactive_menu()

if __name__ == "__main__":
	main()
