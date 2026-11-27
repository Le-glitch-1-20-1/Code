#!/usr/bin/env python3
import argparse
import base64
import os
import random
import sys
import threading
import time
import cv2
import numpy		as np
from abc			import ABC, abstractmethod
from collections	import deque
from io				import BytesIO
from typing			import Any, Callable, Optional


try:
	from PIL import Image
	_PIL_AVAILABLE: bool = True
except ImportError:
	_PIL_AVAILABLE: bool = False

try:
	from selenium import webdriver
	from selenium.webdriver.chrome.service import Service
	from webdriver_manager.chrome import ChromeDriverManager
	_SELENIUM_AVAILABLE: bool = True
except ImportError:
	_SELENIUM_AVAILABLE: bool = False

try:
	from pynput.keyboard import Key, Controller, Listener
	_PYNPUT_AVAILABLE: bool = True
except ImportError:
	_PYNPUT_AVAILABLE: bool = False

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

# ============================================================
# Interface section (mirrors a separate Interface.py contract)
# ============================================================

class IMazeGenerator(ABC):
	# Contract for procedural maze generation
	@abstractmethod
	def generate(self, cols: int, rows: int, cell_size: int, wall_thick: int, seed: Optional[int]) -> tuple[str, str]:
		raise NotImplementedError

class IMazeCapture(ABC):
	# Contract for acquiring a maze image from a file or a browser
	@abstractmethod
	def capture(self, img_source: str, url: Optional[str], image_path: Optional[str], tol_overrides: Optional[dict[str, int]]) -> None:
		raise NotImplementedError

class IPathSolver(ABC):
	# Contract for solving a captured or generated maze
	@abstractmethod
	def solve(self, tol: Optional[int]) -> Optional[list[tuple[int, int]]]:
		raise NotImplementedError

class IMover(ABC):
	# Contract for replaying a solved path via keyboard input
	@abstractmethod
	def move(self, speed: float) -> None:
		raise NotImplementedError

class IUserInterface(ABC):
	# Contract for the interactive console front-end
	@abstractmethod
	def run(self) -> None:
		raise NotImplementedError

# ============================================================
# Shared configuration constants
# ============================================================

SIZES: dict[str, dict[str, int]] = {
	"mini": {"cols": 10, "rows": 10, "cell": 20, "wall": 2},
	"medium": {"cols": 20, "rows": 20, "cell": 18, "wall": 2},
	"mighty": {"cols": 30, "rows": 30, "cell": 16, "wall": 2},
	"mega": {"cols": 40, "rows": 40, "cell": 14, "wall": 2},
	"monolithic": {"cols": 50, "rows": 50, "cell": 12, "wall": 2},
	"magnificent": {"cols": 60, "rows": 60, "cell": 10, "wall": 2},
	"maligned": {"cols": 70, "rows": 70, "cell": 8, "wall": 2},
	"monstrous": {"cols": 100, "rows": 100, "cell": 6, "wall": 2},
	"mammoth": {"cols": 120, "rows": 120, "cell": 5, "wall": 2},
	"megalomaniac": {"cols": 150, "rows": 150, "cell": 4, "wall": 2},
}
MAZE_URLS: dict[str, str] = {name: f"https://maze.toys/mazes/{name}/" for name in SIZES}
DAILY_URLS: dict[str, str] = {name: f"https://maze.toys/mazes/{name}/daily/" for name in SIZES}
MAZETOYS_SIZES: list[str] = ["mini", "medium", "mighty", "mega", "monolithic", "magnificent", "maligned", "monstrous", "mammoth", "megalomaniac"]
DEFAULT_WORK_DIR: str = "maze_output"

def make_capture_config(work_dir: str) -> dict[str, Any]:
	# Build the capture configuration dictionary from the chosen working folder
	return {
		"URL": "https://maze.toys/mazes/mini/",
		"WAIT_TIME": 2,
		"OUTPUT_PATH": os.path.join(work_dir, "maze.png"),
		"OUTPUT_IMAGE": os.path.join(work_dir, "mini.png"),
		"INFO_PATH": os.path.join(work_dir, "maze_info.txt"),
		"WHITE_THRESHOLD": 240,
		"BLACK_THRESHOLD": 50,
		"GRID_COLOR": (180, 180, 180),
		"INTERSECTION_COLOR": (0, 0, 0),
		"MAX_GRAY_RATIO": 0.5,
		"MAX_ITER": 15,
	}

def make_solver_config(work_dir: str) -> dict[str, Any]:
	# Build the solver configuration dictionary from the chosen working folder
	return {
		"INPUT_IMAGE": os.path.join(work_dir, "mini.png"),
		"OUTPUT_IMAGE": os.path.join(work_dir, "maze_solved.png"),
		"INFO_FILE": os.path.join(work_dir, "maze_info.txt"),
		"PATH_FILE": os.path.join(work_dir, "maze_path.txt"),
		"INTERSECTION_COLOR": (0, 0, 0),
		"TOL": 30,
	}

DEFAULT_INFO_FILE: str = os.path.join(DEFAULT_WORK_DIR, "maze_info.txt")
DEFAULT_OUTPUT_IMG: str = os.path.join(DEFAULT_WORK_DIR, "mini.png")
COLOR_WALL: tuple[int, int, int] = (0, 0, 0)
COLOR_START: tuple[int, int, int] = (0, 0, 200)
COLOR_END: tuple[int, int, int] = (0, 0, 200)
CAPTURE_CONFIG: dict[str, Any] = make_capture_config(DEFAULT_WORK_DIR)
SOLVER_CONFIG: dict[str, Any] = make_solver_config(DEFAULT_WORK_DIR)
CORE_FILES: list[str] = [__file__]

# ============================================================
# MazeGenerator implementation
# ============================================================

class MazeGenerator(IMazeGenerator):
	def _make_maze(self, cols: int, rows: int, seed: Optional[int]) -> set[tuple[int, int, str]]:
		if cols < 1 or rows < 1:
			raise ValueError(f"Invalid maze dimensions: {cols}x{rows} (must be >= 1)")
		if seed is not None:
			random.seed(seed)
		visited: set[tuple[int, int]] = set()
		passages: set[tuple[int, int, str]] = set()
		def neighbors(c: int, r: int) -> list[tuple[int, int, str]]:
			out: list[tuple[int, int, str]] = []
			if c + 1 < cols:
				out.append((c + 1, r, "E"))
			if c - 1 >= 0:
				out.append((c - 1, r, "W"))
			if r + 1 < rows:
				out.append((c, r + 1, "S"))
			if r - 1 >= 0:
				out.append((c, r - 1, "N"))
			return out
		stack: list[tuple[int, int]] = [(0, 0)]
		visited.add((0, 0))
		while stack:
			c, r = stack[-1]
			nbrs: list[tuple[int, int, str]] = [(nc, nr, d) for nc, nr, d in neighbors(c, r) if (nc, nr) not in visited]
			if not nbrs:
				stack.pop()
				continue
			nc, nr, d = random.choice(nbrs)
			if d == "E":
				passages.add((c, r, "E"))
			elif d == "W":
				passages.add((nc, nr, "E"))
			elif d == "S":
				passages.add((c, r, "S"))
			elif d == "N":
				passages.add((nc, nr, "S"))
			visited.add((nc, nr))
			stack.append((nc, nr))
		return passages

	def _pick_far_cell(self, cols: int, rows: int, sc: int, sr: int, passages: set[tuple[int, int, str]]) -> tuple[int, int]:
		def adj(c: int, r: int) -> list[tuple[int, int]]:
			nbrs: list[tuple[int, int]] = []
			if (c, r, "E") in passages and c + 1 < cols:
				nbrs.append((c + 1, r))
			if (c - 1, r, "E") in passages and c - 1 >= 0:
				nbrs.append((c - 1, r))
			if (c, r, "S") in passages and r + 1 < rows:
				nbrs.append((c, r + 1))
			if (c, r - 1, "S") in passages and r - 1 >= 0:
				nbrs.append((c, r - 1))
			return nbrs
		dist: dict[tuple[int, int], int] = {(sc, sr): 0}
		queue: deque[tuple[int, int]] = deque([(sc, sr)])
		while queue:
			c, r = queue.popleft()
			for nc, nr in adj(c, r):
				if (nc, nr) not in dist:
					dist[(nc, nr)] = dist[(c, r)] + 1
					queue.append((nc, nr))
		return max(dist, key=dist.get)

	def _draw_maze(self, passages: set[tuple[int, int, str]], cols: int, rows: int, cell_size: int, wall_thick: int) -> np.ndarray:
		t: int = wall_thick
		img: np.ndarray = np.ones((rows * cell_size + t, cols * cell_size + t, 3), dtype=np.uint8) * 255
		img[0:t, :] = img[-t:, :] = img[:, 0:t] = img[:, -t:] = COLOR_WALL
		for r in range(rows):
			for c in range(cols):
				if r < rows - 1 and (c, r, "S") not in passages:
					img[(r + 1) * cell_size:(r + 1) * cell_size + t, c * cell_size:(c + 1) * cell_size + t] = COLOR_WALL
				if c < cols - 1 and (c, r, "E") not in passages:
					img[r * cell_size:(r + 1) * cell_size + t, (c + 1) * cell_size:(c + 1) * cell_size + t] = COLOR_WALL
		return img

	def _place_marker(self, img: np.ndarray, col: int, row: int, cell_size: int, wall_thick: int, color: tuple[int, int, int]) -> None:
		t: int = wall_thick
		x0: int = col * cell_size + t
		y0: int = row * cell_size + t
		img[y0:y0 + cell_size - t, x0:x0 + cell_size - t] = color

	def generate(self, cols: int, rows: int, cell_size: int, wall_thick: int, seed: Optional[int]) -> tuple[str, str]:
		output_img: str = DEFAULT_OUTPUT_IMG
		info_file: str = DEFAULT_INFO_FILE
		if cols < 2 or rows < 2:
			raise ValueError(f"Maze must be at least 2x2 (got {cols}x{rows})")
		if cell_size < 4:
			raise ValueError(f"Cell size must be at least 4px (got {cell_size})")
		if wall_thick < 1:
			raise ValueError(f"Wall thickness must be at least 1px (got {wall_thick})")
		if wall_thick >= cell_size:
			raise ValueError(f"Wall thickness ({wall_thick}) must be smaller than cell size ({cell_size})")
		out_dir: str = os.path.dirname(output_img)
		if out_dir:
			os.makedirs(out_dir, exist_ok=True)
		info_dir: str = os.path.dirname(info_file)
		if info_dir:
			os.makedirs(info_dir, exist_ok=True)
		passages: set[tuple[int, int, str]] = self._make_maze(cols, rows, seed)
		end_col, end_row = self._pick_far_cell(cols, rows, 0, 0, passages)
		img: np.ndarray = self._draw_maze(passages, cols, rows, cell_size, wall_thick)
		self._place_marker(img, 0, 0, cell_size, wall_thick, COLOR_START)
		self._place_marker(img, end_col, end_row, cell_size, wall_thick, COLOR_END)
		if not cv2.imwrite(output_img, img):
			raise OSError(f"Failed to write image to: {output_img}")
		cx_s: int = cell_size // 2
		cy_s: int = cell_size // 2
		cx_e: int = end_col * cell_size + cell_size // 2
		cy_e: int = end_row * cell_size + cell_size // 2
		with open(info_file, "w", encoding="utf-8") as f:
			f.write(f"Wall thickness: {wall_thick}\n")
			f.write(f"Cell size: {cell_size}\n")
			f.write("Offset X: 0\n")
			f.write("Offset Y: 0\n")
			f.write(f"Start coord: {cx_s}, {cy_s}\n")
			f.write(f"End coord: {cx_e}, {cy_e}\n")
			f.write("Start cell: 0,0\n")
			f.write(f"End cell: {end_col},{end_row}\n")
		return output_img, info_file

# ============================================================
# MazeCapture implementation
# ============================================================

class MazeCapture(IMazeCapture):
	def _ensure_dirs(self, cfg: dict[str, Any]) -> None:
		for key in ("OUTPUT_PATH", "OUTPUT_IMAGE", "INFO_PATH"):
			path: str = cfg.get(key, "")
			directory: str = os.path.dirname(path)
			if directory:
				os.makedirs(directory, exist_ok=True)

	def _ensure_rgb(self, img: Any) -> Any:
		if not _PIL_AVAILABLE:
			raise ImportError("Pillow is required. Install it with: pip install Pillow")
		if img.mode in ("RGBA", "LA"):
			bg = Image.new("RGB", img.size, (255, 255, 255))
			bg.paste(img, mask=img.split()[3])
			return bg
		return img.convert("RGB")

	def _extract_canvas_b64(self, driver: Any) -> bytes:
		js: str = (
			"var canvas = document.querySelector('canvas');"
			"if (!canvas) return null;"
			"return canvas.toDataURL('image/png').substring(22);"
		)
		data: Optional[str] = driver.execute_script(js)
		if data is None:
			raise RuntimeError("No <canvas> element found on the page.")
		return base64.b64decode(data)

	def _find_biggest_contour(self, mask: np.ndarray) -> Optional[np.ndarray]:
		cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		return max(cnts, key=cv2.contourArea) if cnts else None

	def _draw_grid_mask(self, cell: int, thick: int, shape: tuple[int, int], ox: int, oy: int) -> np.ndarray:
		h, w = shape
		mask: np.ndarray = np.zeros((h, w), dtype=np.uint8)
		for x in range(0, w, cell):
			for t in range(thick):
				xx: int = x + ox + t
				if 0 <= xx < w:
					mask[:, xx] = 1
		for y in range(0, h, cell):
			for t in range(thick):
				yy: int = y + oy + t
				if 0 <= yy < h:
					mask[yy, :] = 1
		return mask

	def _is_far_from_start(self, cnt: np.ndarray, sx: int, sy: int, sw: int, sh: int, min_dist: int) -> bool:
		x, y, cw, ch = cv2.boundingRect(cnt)
		return (x + cw < sx - min_dist) or (x > sx + sw + min_dist) or (y + ch < sy - min_dist) or (y > sy + sh + min_dist)

	def capture(self, img_source: str, url: Optional[str], image_path: Optional[str], tol_overrides: Optional[dict[str, int]]) -> None:
		cfg: dict[str, Any] = CAPTURE_CONFIG.copy()
		if tol_overrides:
			cfg.update(tol_overrides)
		self._ensure_dirs(cfg)
		if img_source == "file":
			if not image_path:
				raise ValueError("image_path must be provided when img_source='file'")
			if not os.path.exists(image_path):
				raise FileNotFoundError(f"Image not found: {image_path}")
			if not _PIL_AVAILABLE:
				raise ImportError("Pillow is required. Install it with: pip install Pillow")
			pil_img: Any = Image.open(image_path)
			pil_img = self._ensure_rgb(pil_img)
			cv_img: np.ndarray = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
		elif img_source == "url":
			if not _SELENIUM_AVAILABLE:
				raise ImportError("selenium and webdriver-manager are required for URL capture.\n  Install with: pip install selenium webdriver-manager")
			if not _PIL_AVAILABLE:
				raise ImportError("Pillow is required. Install it with: pip install Pillow")
			target_url: str = url if url else cfg["URL"]
			options = webdriver.ChromeOptions()
			options.add_argument("--headless")
			options.add_argument("--no-sandbox")
			options.add_argument("--disable-dev-shm-usage")
			options.add_argument("--window-size=1920,1080")
			driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
			try:
				driver.get(target_url)
				time.sleep(cfg["WAIT_TIME"])
				png_bytes: bytes = self._extract_canvas_b64(driver)
			finally:
				driver.quit()
			pil_img = Image.open(BytesIO(png_bytes))
			pil_img = self._ensure_rgb(pil_img)
			cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
		else:
			raise ValueError(f"Unknown img_source: {img_source!r}. Expected 'url' or 'file'.")
		hsv: np.ndarray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
		low_r1, high_r1 = np.array([0, 100, 100]), np.array([10, 255, 255])
		mask_start: np.ndarray = cv2.inRange(hsv, low_r1, high_r1)
		cnt_start: Optional[np.ndarray] = self._find_biggest_contour(mask_start)
		if cnt_start is None:
			raise RuntimeError("Start square not found. The image may not contain a valid maze, or the red marker is missing.")
		x_start_rect, y_start_rect, w_start, h_start = cv2.boundingRect(cnt_start)
		start_center: tuple[int, int] = (x_start_rect + w_start // 2, y_start_rect + h_start // 2)
		img: np.ndarray = cv_img.copy()
		h, w = img.shape[:2]
		gray: np.ndarray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		mid_x: int = w // 2
		thickness: int = 0
		for y in range(h):
			if gray[y, mid_x] < cfg["BLACK_THRESHOLD"]:
				thickness += 1
			else:
				break
		thickness = max(thickness, 1)
		offset_x: int = -(thickness // 2)
		offset_y: int = -(thickness // 2)
		line_up: int = h // 2 - h // 6
		line_down: int = h // 2 + h // 6
		stop_x: int = w - w // 6
		def measure_white_runs(scan_y: int) -> list[tuple[int, int]]:
			runs: list[tuple[int, int]] = []
			count: int = 0
			start_x: Optional[int] = None
			for x in range(stop_x):
				if gray[scan_y, x] > cfg["WHITE_THRESHOLD"]:
					if count == 0:
						start_x = x
					count += 1
				else:
					if count > 0:
						runs.append((start_x, count))
					count = 0
			if count > 0:
				runs.append((start_x, count))
			return runs
		all_runs: list[tuple[int, int]] = sorted(measure_white_runs(line_up) + measure_white_runs(line_down), key=lambda r: r[1])
		if len(all_runs) < 2:
			raise RuntimeError("Could not detect cell size - not enough white regions found. The image may be too dark or not a valid maze.")
		_run_start, cell_size = all_runs[1]
		current_cell: int = cell_size
		white_mask: np.ndarray = gray > cfg["WHITE_THRESHOLD"]
		red_mask: np.ndarray = cv2.inRange(img, np.array([0, 0, 100]), np.array([80, 80, 255])) > 0
		mask_visible: np.ndarray = white_mask | red_mask
		out: np.ndarray = img.copy()
		for _iteration in range(cfg["MAX_ITER"]):
			temp: np.ndarray = img.copy()
			grid_mask: np.ndarray = self._draw_grid_mask(current_cell, thickness, (h, w), offset_x, offset_y)
			temp[mask_visible & (grid_mask == 1)] = cfg["GRID_COLOR"]
			total: int = np.sum(grid_mask == 1)
			visible: int = np.sum((grid_mask == 1) & mask_visible)
			if total == 0:
				break
			if visible / total <= cfg["MAX_GRAY_RATIO"]:
				out = temp
				break
			current_cell += 1
		for x in range(0, w, current_cell):
			for y in range(0, h, current_cell):
				for dx in range(thickness):
					for dy in range(thickness):
						xx, yy = x + dx + offset_x, y + dy + offset_y
						if 0 <= xx < w and 0 <= yy < h:
							out[yy, xx] = cfg["INTERSECTION_COLOR"]
		out[:thickness, :] = 0
		out[-thickness:, :] = 0
		out[:, :thickness] = 0
		out[:, -thickness:] = 0
		low2, high2 = np.array([170, 100, 100]), np.array([180, 255, 255])
		mask_straw: np.ndarray = cv2.bitwise_or(cv2.inRange(hsv, low_r1, high_r1), cv2.inRange(hsv, low2, high2))
		kernel: np.ndarray = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
		mask_straw = cv2.morphologyEx(mask_straw, cv2.MORPH_CLOSE, kernel, iterations=2)
		mask_straw = cv2.morphologyEx(mask_straw, cv2.MORPH_OPEN, kernel, iterations=1)
		cnts, _ = cv2.findContours(mask_straw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		valid_cnts: list[np.ndarray] = [c for c in cnts if self._is_far_from_start(c, x_start_rect, y_start_rect, w_start, h_start, 5)]
		if not valid_cnts:
			raise RuntimeError("End marker not detected. The maze image may be missing the destination marker, or the colour thresholds need adjustment.")
		cnt_straw: np.ndarray = max(valid_cnts, key=cv2.contourArea)
		m: dict[str, float] = cv2.moments(cnt_straw)
		if abs(m.get("m00", 0)) < 1e-6:
			x_s, y_s, w_s, h_s = cv2.boundingRect(cnt_straw)
			cx, cy = x_s + w_s // 2, y_s + h_s // 2
		else:
			cx, cy = int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])
		cell_x: int = int(np.floor((cx - offset_x) / float(current_cell)))
		cell_y: int = int(np.floor((cy - offset_y) / float(current_cell)))
		x_s, y_s, w_s, h_s = cv2.boundingRect(cnt_straw)
		x0: int = max(0, cell_x * current_cell + offset_x)
		y0: int = max(0, cell_y * current_cell + offset_y)
		x1: int = min(w, x0 + current_cell)
		y1: int = min(h, y0 + current_cell)
		if x1 <= x0 or y1 <= y0:
			x0, y0 = x_s, y_s
			x1, y1 = min(w, x_s + w_s), min(h, y_s + h_s)
		cell_region: np.ndarray = out[y0:y1, x0:x1]
		mask_fill: np.ndarray = np.all(cell_region != cfg["GRID_COLOR"], axis=2) & np.all(cell_region != cfg["INTERSECTION_COLOR"], axis=2)
		cell_region[mask_fill] = (0, 0, 255)
		out[y0:y1, x0:x1] = cell_region
		if not cv2.imwrite(cfg["OUTPUT_IMAGE"], out):
			raise OSError(f"Failed to write processed image to: {cfg['OUTPUT_IMAGE']}")
		with open(cfg["INFO_PATH"], "w", encoding="utf-8") as f:
			f.write(f"Wall thickness: {thickness}\n")
			f.write(f"Cell size: {current_cell}\n")
			f.write(f"Offset X: {offset_x}\n")
			f.write(f"Offset Y: {offset_y}\n")
			f.write(f"Start coord: {start_center[0]}, {start_center[1]}\n")
			f.write(f"End coord: {cx}, {cy}\n")
			f.write("Start cell: 0,0\n")
			f.write(f"End cell: {cell_x},{cell_y}\n")

# ============================================================
# PathSolver implementation
# ============================================================

class PathSolver(IPathSolver):
	def _parse_info(self, file_path: str) -> dict[str, str]:
		if not file_path:
			raise ValueError("Info file path is empty.")
		if not os.path.exists(file_path):
			raise FileNotFoundError(f"Info file not found: {file_path}\nRun maze generation or capture first.")
		info: dict[str, str] = {}
		with open(file_path, "r", encoding="utf-8") as f:
			for lineno, line in enumerate(f, 1):
				line = line.strip()
				if not line:
					continue
				if ":" not in line:
					raise ValueError(f"Malformed info file (line {lineno}): {line!r}\nExpected format:  Key: value")
				key, value = line.split(":", 1)
				info[key.strip()] = value.strip()
		return info

	def _is_black(self, pixel: np.ndarray, tol: int, target: np.ndarray) -> bool:
		return bool(np.all(np.abs(pixel.astype(int) - target.astype(int)) <= tol))

	def _build_grid(self, img_path: str, cell_size: int, tol: int, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
		if not os.path.exists(img_path):
			raise FileNotFoundError(f"Maze image not found: {img_path}\nRun generation or capture first.")
		if cell_size < 1:
			raise ValueError(f"cell_size must be >= 1 (got {cell_size})")
		img: Optional[np.ndarray] = cv2.imread(img_path)
		if img is None:
			raise OSError(f"OpenCV could not read image: {img_path}")
		h, w = img.shape[:2]
		rows: int = h // cell_size
		cols: int = w // cell_size
		if rows == 0 or cols == 0:
			raise ValueError(f"Image ({w}x{h}) is too small for cell_size={cell_size}. The maze may not have been generated correctly.")
		grid: np.ndarray = np.zeros((rows, cols), dtype=int)
		for r in range(rows):
			for c in range(cols):
				cell: np.ndarray = img[r * cell_size:(r + 1) * cell_size, c * cell_size:(c + 1) * cell_size]
				black_mask: np.ndarray = np.apply_along_axis(lambda px: self._is_black(px, tol, target), 2, cell)
				grid[r, c] = 1 if np.sum(black_mask) > (cell_size * cell_size) // 2 else 0
		return grid, img

	def _can_connect(self, cell1: tuple[int, int], cell2: tuple[int, int], img: np.ndarray, cell_size: int, tol: int) -> bool:
		x1, y1 = cell1
		x2, y2 = cell2
		cx1: int = x1 * cell_size + cell_size // 2
		cy1: int = y1 * cell_size + cell_size // 2
		cx2: int = x2 * cell_size + cell_size // 2
		cy2: int = y2 * cell_size + cell_size // 2
		segment: np.ndarray = img[min(cy1, cy2):max(cy1, cy2) + 1, min(cx1, cx2):max(cx1, cx2) + 1]
		black_mask: np.ndarray = np.all(np.abs(segment.astype(int) - np.array([0, 0, 0])) <= tol, axis=2)
		return not np.any(black_mask)

	def _build_graph(self, grid: np.ndarray, img: np.ndarray, cell_size: int, tol: int) -> dict[tuple[int, int], list[tuple[int, int]]]:
		rows, cols = grid.shape
		graph: dict[tuple[int, int], list[tuple[int, int]]] = {}
		for r in range(rows):
			for c in range(cols):
				if grid[r, c] == 1:
					continue
				neighbors: list[tuple[int, int]] = []
				for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
					nx, ny = c + dx, r + dy
					if 0 <= nx < cols and 0 <= ny < rows and grid[ny, nx] == 0:
						if self._can_connect((c, r), (nx, ny), img, cell_size, tol):
							neighbors.append((nx, ny))
				graph[(c, r)] = neighbors
		return graph

	def _shortest_path(self, graph: dict[tuple[int, int], list[tuple[int, int]]], start: tuple[int, int], end: tuple[int, int]) -> Optional[list[tuple[int, int]]]:
		if start not in graph:
			raise ValueError(f"Start cell {start} is not in the graph. It may be a wall or outside the maze.")
		if end not in graph:
			raise ValueError(f"End cell {end} is not in the graph. It may be a wall or outside the maze.")
		visited: set[tuple[int, int]] = set()
		parent: dict[tuple[int, int], tuple[int, int]] = {}
		queue: deque[tuple[int, int]] = deque([start])
		visited.add(start)
		while queue:
			node: tuple[int, int] = queue.popleft()
			if node == end:
				path: list[tuple[int, int]] = []
				while node != start:
					path.append(node)
					node = parent[node]
				path.append(start)
				path.reverse()
				return path
			for nb in graph.get(node, []):
				if nb not in visited:
					visited.add(nb)
					parent[nb] = node
					queue.append(nb)
		return None

	def _draw_path(self, original_img: np.ndarray, path: list[tuple[int, int]], cell_size: int, wall_thickness: int) -> np.ndarray:
		img: np.ndarray = np.ones_like(original_img) * 255
		offset: int = wall_thickness // 2
		for (x, y) in path:
			cv2.rectangle(
				img,
				(x * cell_size + offset, y * cell_size + offset),
				(x * cell_size + cell_size - offset, y * cell_size + cell_size - offset),
				(0, 0, 255),
				-1,
			)
		mask: np.ndarray = np.all(original_img <= np.array([180, 180, 180]), axis=2)
		for c in range(3):
			img[:, :, c][mask] = original_img[:, :, c][mask]
		return img

	def solve(self, tol: Optional[int]) -> Optional[list[tuple[int, int]]]:
		cfg: dict[str, Any] = SOLVER_CONFIG.copy()
		if tol is not None:
			cfg["TOL"] = tol
		info: dict[str, str] = self._parse_info(cfg["INFO_FILE"])
		cell_size: int = int(info.get("Cell size", info.get("Cell size", 20)))
		wall_thickness: int = int(info.get("Wall thickness", info.get("Line thickness", 2)))
		tol_val: int = int(cfg["TOL"])
		target: np.ndarray = np.array(cfg["INTERSECTION_COLOR"])
		start_raw: str = info.get("Start cell", info.get("Start cell", "0,0"))
		end_raw: str = info.get("End cell", info.get("Strawberry cell", "0,0"))
		try:
			start_cell: tuple[int, int] = tuple(map(int, start_raw.split(",")))
			end_cell: tuple[int, int] = tuple(map(int, end_raw.split(",")))
		except ValueError as exc:
			raise ValueError(f"Cannot parse cell coordinates from info file: {exc}\n  Start cell raw: {start_raw!r}\n  End cell raw:   {end_raw!r}") from exc
		grid, img = self._build_grid(cfg["INPUT_IMAGE"], cell_size, tol_val, target)
		graph: dict[tuple[int, int], list[tuple[int, int]]] = self._build_graph(grid, img, cell_size, tol_val)
		path: Optional[list[tuple[int, int]]] = self._shortest_path(graph, start_cell, end_cell)
		if path is None:
			return None
		path_dir: str = os.path.dirname(cfg["PATH_FILE"])
		if path_dir:
			os.makedirs(path_dir, exist_ok=True)
		with open(cfg["PATH_FILE"], "w", encoding="utf-8") as f:
			for cell in path:
				f.write(f"{cell[0]},{cell[1]}\n")
		solved_img: np.ndarray = self._draw_path(img, path, cell_size, wall_thickness)
		out_dir: str = os.path.dirname(cfg["OUTPUT_IMAGE"])
		if out_dir:
			os.makedirs(out_dir, exist_ok=True)
		if not cv2.imwrite(cfg["OUTPUT_IMAGE"], solved_img):
			raise OSError(f"Failed to write solved image to: {cfg['OUTPUT_IMAGE']}")
		return path

# ============================================================
# KeyboardMover implementation
# ============================================================

class KeyboardMover(IMover):
	def _check_pynput(self) -> None:
		if not _PYNPUT_AVAILABLE:
			raise ImportError("pynput is required for keyboard control.\n  Install with: pip install pynput")

	def _read_coords(self, filename: str) -> list[tuple[int, int]]:
		if not os.path.exists(filename):
			raise FileNotFoundError(f"Path file not found: {filename}\nRun maze solving first.")
		coords: list[tuple[int, int]] = []
		with open(filename, "r", encoding="utf-8") as f:
			for lineno, line in enumerate(f, 1):
				line = line.strip()
				if not line:
					continue
				parts: list[str] = line.split(",")
				if len(parts) != 2:
					raise ValueError(f"Malformed path file at line {lineno}: {line!r}\nExpected format: col,row")
				try:
					x, y = int(parts[0]), int(parts[1])
				except ValueError:
					raise ValueError(f"Non-integer values at line {lineno}: {line!r}")
				coords.append((x, y))
		if not coords:
			raise ValueError(f"Path file is empty: {filename}")
		return coords

	def _get_direction(self, p1: tuple[int, int], p2: tuple[int, int]) -> Optional[Any]:
		self._check_pynput()
		dx, dy = p2[0] - p1[0], p2[1] - p1[1]
		if dx == 1 and dy == 0:
			return Key.right
		if dx == -1 and dy == 0:
			return Key.left
		if dy == 1 and dx == 0:
			return Key.down
		if dy == -1 and dx == 0:
			return Key.up
		return None

	def move(self, speed: float) -> None:
		path_file: str = SOLVER_CONFIG["PATH_FILE"]
		self._check_pynput()
		if speed < 0:
			raise ValueError(f"Speed must be >= 0 (got {speed})")
		coords: list[tuple[int, int]] = self._read_coords(path_file)
		keyboard: Any = Controller()
		for i in range(len(coords) - 1):
			direction: Optional[Any] = self._get_direction(coords[i], coords[i + 1])
			if direction is None:
				continue
			keyboard.press(direction)
			keyboard.release(direction)
			if speed > 0:
				time.sleep(speed)

# ============================================================
# ConsoleUI implementation
# ============================================================

class ConsoleUI(IUserInterface):
	# Program front-end: relies on the global "ui" object (plain console or display_layer.py)
	def __init__(self, application: "Application") -> None:
		self.application: "Application" = application

	def splash(self) -> None:
		ui.banner("MAZE SOLVER", "Generate . Solve . Play")

	def section(self, title: str) -> None:
		ui.section(title)
		ui.info()

	def ok(self, msg: str) -> None:
		ui.success(msg)

	def err(self, msg: str) -> None:
		ui.error(msg)

	def info(self, msg: str) -> None:
		ui.muted(f"  {msg}")

	def success_panel(self, msg: str) -> None:
		ui.info()
		ui.block(msg)

	def with_spinner(self, label: str, fn: Callable[[], Any]) -> Any:
		# Run fn in a thread while the waiting message is shown
		result: list[Any] = [None]
		error: list[Optional[BaseException]] = [None]
		def worker() -> None:
			try:
				result[0] = fn()
			except Exception as exc:
				error[0] = exc
		t: threading.Thread = threading.Thread(target=worker)
		with ui.status(label.rstrip(".")):
			t.start()
			t.join()
		if error[0]:
			raise error[0]
		return result[0]

	def move_progress(self, fn: Callable[[], None]) -> None:
		with ui.status("Moving"):
			fn()

	def wait_for_key(self, key_char: str) -> None:
		if not _PYNPUT_AVAILABLE:
			ui.pause("Position yourself on the game window, then press Enter to start...")
			return
		ui.block(f"Position yourself on the game window,\nthen press {key_char.upper()} to start.")
		done: threading.Event = threading.Event()
		def on_press(key: Any) -> Optional[bool]:
			try:
				if key.char and key.char.lower() == key_char:
					done.set()
					return False
			except AttributeError:
				pass
			return None
		with Listener(on_press=on_press):
			done.wait()

	def _choice(self, label: str, value: Any) -> dict[str, Any]:
		return {"label": label, "value": value}

	def _separator(self) -> None:
		return None

	def ask_select(self, prompt: str, choices: list[Any]) -> Any:
		# Separators (None) are ignored; exits if the user cancels
		items: list[dict[str, Any]] = [c if isinstance(c, dict) else {"label": str(c), "value": c} for c in choices if c is not None]
		labels: list[str] = [c["label"] for c in items]
		result: Optional[str] = ui.choose(prompt, labels)
		if result is None:
			sys.exit(0)
		return items[labels.index(result)]["value"]

	def ask_confirm(self, prompt: str, default: bool) -> bool:
		result: Optional[bool] = ui.confirm(prompt, default=default)
		if result is None:
			sys.exit(0)
		return result

	def _ask_text(self, prompt: str, default: Optional[str], validate: Optional[Callable[[str], Any]]) -> str:
		while True:
			raw: Optional[str] = ui.ask(prompt, None if default is None else str(default))
			if raw is None:
				sys.exit(0)
			if validate:
				outcome: Any = validate(raw)
				if outcome is not True:
					ui.error(str(outcome))
					continue
			return raw

	def ask_int(self, prompt: str, default: Optional[int]) -> int:
		def validate(val: str) -> Any:
			try:
				int(val)
				return True
			except ValueError:
				return "Please enter a whole number."
		return int(self._ask_text(prompt, default, validate))

	def ask_float(self, prompt: str, default: Optional[float]) -> float:
		def validate(val: str) -> Any:
			try:
				float(val)
				return True
			except ValueError:
				return "Please enter a number."
		return float(self._ask_text(prompt, str(default) if default is not None else None, validate))

	def ask_text(self, prompt: str, default: Optional[str], validate: Optional[Callable[[str], Any]]) -> str:
		return self._ask_text(prompt, default, validate)

	def menu_main(self) -> str:
		self.splash()
		return self.ask_select("What would you like to do?", [
			self._choice("Generate a maze", "generate"),
			self._choice("Capture from maze.toys", "site"),
			self._separator(),
			self._choice("Quit", "quit"),
		])

	def menu_generate(self) -> dict[str, Any]:
		self.section("Maze Settings")
		size_choices: list[Any] = [self._choice(f"{name:<12} - {SIZES[name]['cols']}x{SIZES[name]['rows']}", name) for name in SIZES] + [self._choice("custom", "custom")]
		size: str = self.ask_select("Size preset", size_choices)
		cols = rows = cell = wall = None
		if size == "custom":
			ui.info()
			cols = self.ask_int("Columns", 20)
			rows = self.ask_int("Rows", 20)
			cell = self.ask_int("Cell size (px)", 18)
			wall = self.ask_int("Wall width (px)", 2)
		seed: Optional[int] = None
		if self.ask_confirm("Use a fixed random seed?", False):
			seed = self.ask_int("Seed value", None)
		return {"size": size, "cols": cols, "rows": rows, "cell": cell, "wall": wall, "seed": seed}

	def menu_site(self) -> dict[str, Any]:
		self.section("Maze Source")
		src: str = self.ask_select("Source", [
			self._choice("URL - maze.toys (regular)", "url"),
			self._choice("URL - maze.toys (daily)", "daily"),
			self._choice("Local image file", "file"),
		])
		url: Optional[str] = None
		image_path: Optional[str] = None
		if src in ("url", "daily"):
			size_choices: list[Any] = [self._choice(name, name) for name in MAZETOYS_SIZES] + [self._choice("Custom URL...", "__custom__")]
			chosen: str = self.ask_select("Maze size", size_choices)
			if chosen == "__custom__":
				url = self.ask_text("Full URL", None, None)
			else:
				url = f"https://maze.toys/mazes/{chosen}/daily/" if src == "daily" else f"https://maze.toys/mazes/{chosen}/"
		else:
			image_path = self.ask_text("Image path", None, None)
			if not os.path.exists(image_path):
				self.err(f"File not found: {image_path}")
				sys.exit(1)
		tol: Optional[int] = None
		if self.ask_confirm("Adjust pixel tolerance?", False):
			tol = self.ask_int("Tolerance (0-255)", 30)
		speed: float = self.ask_float("Delay between key presses (s)", 0.1)
		return {"url": url, "image_path": image_path, "tol": tol, "speed": speed}

	def run(self) -> None:
		try:
			mode: str = self.menu_main()
		except KeyboardInterrupt:
			ui.info("\nInterrupted.")
			sys.exit(0)
		if mode == "quit":
			self.info("Goodbye.")
			sys.exit(0)
		try:
			if mode == "generate":
				params: dict[str, Any] = self.menu_generate()
				self.application.run_generate(params)
			else:
				params = self.menu_site()
				self.application.run_site(params)
		except KeyboardInterrupt:
			ui.info("\nInterrupted.")
			sys.exit(0)

# ============================================================
# Application orchestrator
# ============================================================

class Application:
	def __init__(self, work_dir: str = DEFAULT_WORK_DIR) -> None:
		self.work_dir: str = work_dir
		self.generator: MazeGenerator = MazeGenerator()
		self.capture: MazeCapture = MazeCapture()
		self.solver: PathSolver = PathSolver()
		self.mover: KeyboardMover = KeyboardMover()
		self.ui: ConsoleUI = ConsoleUI(self)
		global CAPTURE_CONFIG, SOLVER_CONFIG, DEFAULT_INFO_FILE, DEFAULT_OUTPUT_IMG
		CAPTURE_CONFIG = make_capture_config(work_dir)
		SOLVER_CONFIG = make_solver_config(work_dir)
		DEFAULT_INFO_FILE = os.path.join(work_dir, "maze_info.txt")
		DEFAULT_OUTPUT_IMG = os.path.join(work_dir, "mini.png")

	def do_generate(self, p: dict[str, Any]) -> None:
		self.ui.section("Generation")
		if p["size"] == "custom":
			for key in ("cols", "rows", "cell", "wall"):
				if not p.get(key):
					self.ui.err(f"--size custom requires --{key}")
					sys.exit(1)
			params: dict[str, int] = {"cols": p["cols"], "rows": p["rows"], "cell": p["cell"], "wall": p["wall"]}
		else:
			if p["size"] not in SIZES:
				self.ui.err(f"Unknown size: {p['size']}  (valid: {', '.join(SIZES)})")
				sys.exit(1)
			params = dict(SIZES[p["size"]])
			for key in ("cols", "rows", "cell", "wall"):
				if p.get(key):
					params[key] = p[key]
		label: str = f"{params['cols']}x{params['rows']}  -  cell {params['cell']}px  wall {params['wall']}px"
		if p.get("seed") is not None:
			label += f"  -  seed {p['seed']}"
		self.ui.info(label)
		try:
			self.ui.with_spinner("Generating maze...", lambda: self.generator.generate(params["cols"], params["rows"], params["cell"], params["wall"], p.get("seed")))
		except ValueError as exc:
			self.ui.err(f"Invalid parameters: {exc}")
			sys.exit(1)
		except OSError as exc:
			self.ui.err(f"Could not write output files: {exc}")
			sys.exit(1)
		except Exception as exc:
			self.ui.err(f"Generation failed: {exc}")
			sys.exit(1)
		self.ui.ok("Maze generated")

	def do_solve(self, tol: Optional[int]) -> Optional[list[tuple[int, int]]]:
		self.ui.section("Solving")
		if tol is not None and not (0 <= tol <= 255):
			self.ui.err(f"Tolerance must be between 0 and 255 (got {tol})")
			sys.exit(1)
		try:
			path: Optional[list[tuple[int, int]]] = self.ui.with_spinner("Calculating shortest path...", lambda: self.solver.solve(tol))
		except FileNotFoundError as exc:
			self.ui.err(f"Missing file: {exc}")
			sys.exit(1)
		except ValueError as exc:
			self.ui.err(f"Data error: {exc}")
			sys.exit(1)
		except OSError as exc:
			self.ui.err(f"Could not write output files: {exc}")
			sys.exit(1)
		except Exception as exc:
			self.ui.err(f"Solving failed: {exc}")
			sys.exit(1)
		if path is None:
			self.ui.err("No path found in this maze.")
			sys.exit(1)
		self.ui.ok(f"Path found  -  {len(path)} steps")
		return path

	def do_capture(self, url: Optional[str], image_path: Optional[str], tol: Optional[int]) -> None:
		self.ui.section("Capture")
		overrides: Optional[dict[str, int]] = {"INFO_PATH": SOLVER_CONFIG["INFO_FILE"]} if False else None
		if image_path:
			if not os.path.exists(image_path):
				self.ui.err(f"Image not found: {image_path}")
				sys.exit(1)
			self.ui.info(f"Source: {image_path}")
			try:
				self.ui.with_spinner("Analysing image...", lambda: self.capture.capture("file", None, image_path, overrides))
			except FileNotFoundError as exc:
				self.ui.err(f"Missing file: {exc}")
				sys.exit(1)
			except ImportError as exc:
				self.ui.err(str(exc))
				sys.exit(1)
			except RuntimeError as exc:
				self.ui.err(f"Detection failed: {exc}")
				sys.exit(1)
			except Exception as exc:
				self.ui.err(f"Image analysis failed: {exc}")
				sys.exit(1)
		else:
			if not _SELENIUM_AVAILABLE:
				self.ui.err("The 'selenium' package is required for URL capture.\n  Install with: pip install selenium webdriver-manager")
				sys.exit(1)
			if not url:
				self.ui.err("No URL provided.")
				sys.exit(1)
			self.ui.info(f"URL: {url}")
			try:
				self.ui.with_spinner("Capturing maze from browser...", lambda: self.capture.capture("url", url, None, overrides))
			except ImportError as exc:
				self.ui.err(str(exc))
				sys.exit(1)
			except RuntimeError as exc:
				self.ui.err(f"Detection failed: {exc}")
				sys.exit(1)
			except Exception as exc:
				self.ui.err(f"Capture failed: {exc}")
				sys.exit(1)
		self.ui.ok("Maze analysed")

	def do_move(self, speed: float) -> None:
		if speed < 0:
			self.ui.err(f"Speed must be >= 0 (got {speed})")
			sys.exit(1)
		self.ui.section("Movement")
		self.ui.wait_for_key("m")
		try:
			self.ui.move_progress(lambda: self.mover.move(speed))
		except FileNotFoundError as exc:
			self.ui.err(f"Missing file: {exc}")
			sys.exit(1)
		except ImportError as exc:
			self.ui.err(str(exc))
			sys.exit(1)
		except ValueError as exc:
			self.ui.err(f"Data error: {exc}")
			sys.exit(1)
		except Exception as exc:
			self.ui.err(f"Movement failed: {exc}")
			sys.exit(1)
		self.ui.ok("Movement complete")

	def run_generate(self, p: dict[str, Any]) -> None:
		self.do_generate(p)
		self.do_solve(None)
		self.ui.success_panel("Maze solved. Image saved to maze_output/maze_solved.png")

	def run_site(self, p: dict[str, Any]) -> None:
		self.do_capture(p["url"], p["image_path"], p.get("tol"))
		self.do_solve(p.get("tol"))
		self.do_move(p["speed"])

# ============================================================
# CLI argument parsing
# ============================================================

def build_parser() -> argparse.ArgumentParser:
	parser: argparse.ArgumentParser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--no-ui", action="store_true", help="Disable the optional display layer (display_layer.py).")
	parser.add_argument("--lang", choices=["en", "fr"], help="Select the language of the messages (en or fr).")
	parser.add_argument("--output-dir", type=str, default=DEFAULT_WORK_DIR, help="Folder used to read and write the maze files.")
	sub: argparse._SubParsersAction = parser.add_subparsers(dest="mode")
	pg: argparse.ArgumentParser = sub.add_parser("generate")
	pg.add_argument("--size", choices=list(SIZES.keys()) + ["custom"], default="mini")
	pg.add_argument("--cols", type=int)
	pg.add_argument("--rows", type=int)
	pg.add_argument("--cell", type=int)
	pg.add_argument("--wall", type=int)
	pg.add_argument("--seed", type=int)
	ps: argparse.ArgumentParser = sub.add_parser("site")
	ps.add_argument("--url", type=str, default=None)
	ps.add_argument("--image", type=str, default=None, dest="image_path")
	ps.add_argument("--tol", type=int, default=None)
	ps.add_argument("--speed", type=float, default=0.1)
	return parser

def dispatch(application: Application, args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
	if args.mode is None:
		application.ui.run()
		return
	if args.mode == "generate":
		if args.size == "custom" and not all([args.cols, args.rows, args.cell, args.wall]):
			parser.error("--size custom requires --cols, --rows, --cell and --wall")
		p: dict[str, Any] = {"size": args.size, "cols": args.cols, "rows": args.rows, "cell": args.cell, "wall": args.wall, "seed": args.seed}
		application.run_generate(p)
	elif args.mode == "site":
		if not args.url and not args.image_path:
			parser.error("Specify --url or --image")
		p = {"url": args.url, "image_path": args.image_path, "tol": args.tol, "speed": args.speed}
		application.run_site(p)

# ============================================================
# Entry point
# ============================================================

def main() -> None:
	parser: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = parser.parse_args()
	application: Application = Application(args.output_dir)
	dispatch(application, args, parser)

if __name__ == "__main__":
	main()