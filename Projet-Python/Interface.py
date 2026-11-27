#!/usr/bin/env python3

import sys
import io
import os
import re
import argparse
import random
import time
from abc			import ABC, abstractmethod

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

import json

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
	try:
		import display_layer
	except ImportError:
		return simple_console
	try:
		return display_layer.create_display(simple_console) or simple_console
	except Exception:
		return simple_console


ui: ConsoleDisplay = load_display()
# ============================================================================

VERSION: str = "2.0.0"

TABLE_DATA: list[tuple[str, bool, int, str]] = [("Alice", True, 98, "0.42s"), ("Bob", False, 34, "1.21s"), ("Carla", True, 87, "0.67s"), ("David", True, 91, "0.38s"), ("Emma", False, 52, "0.99s")]

SAMPLE_CODE: str = f"""def fibonacci(n: int) -> int:\n\t# Return the n-th Fibonacci number.\n\ta, b = 0, 1\n\tfor _ in range(n):\n\t\ta, b = b, a + b\n\treturn a"""

SAMPLE_MARKDOWN: str = f"""# Project Report\n\n## Summary\n- **Status**: On track\n- **Coverage**: 92%\n- *Next milestone*: v2.0\n\n```python\nprint("hello world")\n```"""

LOG_LEVELS: list[str] = ["INFO", "DEBUG", "WARNING", "ERROR"]

LOG_MESSAGES: list[str] = ["Connecting to database...", "Cache warmed up successfully", "Received request GET /api/users", "Slow query detected (312ms)", "Retrying failed connection", "Background job finished", "Memory usage at 74%", "New client connected"]

class Demo(ABC):
	# Common interface every demo of the program must follow
	@abstractmethod
	def label(self) -> str:
		# Name shown in the menu and usable from the CLI
		raise NotImplementedError

	@abstractmethod
	def run(self) -> None:
		# Demo entry point
		raise NotImplementedError

class SimpleBarDemo(Demo):
	# Demo showing a simple progress bar
	def label(self) -> str:
		return "Simple loading bar"

	def run(self) -> None:
		ui.section("Simple loading bar")
		ui.info()
		with ui.progress(100, "Loading") as bar:
			done: int = 0
			while done < 100:
				step: int = min(random.randint(1, 4), 100 - done)
				done += step
				bar.advance(step)
				time.sleep(0.04)
		ui.success("Done!")
		time.sleep(0.5)

class MultiBarsDemo(Demo):
	# Demo showing several progress bars in parallel
	def label(self) -> str:
		return "Multiple bars in parallel"

	def run(self) -> None:
		ui.section("Multiple bars in parallel")
		ui.info()
		with ui.multi_progress([("Download", 60), ("Processing", 40), ("Saving", 20)]) as bars:
			while not bars.finished():
				bars.advance(0, random.randint(0, 3))
				bars.advance(1, random.randint(0, 2))
				bars.advance(2, random.randint(0, 1))
				time.sleep(0.06)
		ui.success("All tasks completed!")
		time.sleep(0.5)

class TableDemo(Demo):
	# Demo showing a formatted results table
	def label(self) -> str:
		return "Formatted table"

	def run(self) -> None:
		ui.section("Formatted table")
		ui.info()
		rows: list[list[object]] = [
			[name, "OK" if ok else "FAIL", score, elapsed]
			for name, ok, score, elapsed in TABLE_DATA
		]
		ui.table(["Name", "Status", "Score", "Time"], rows, title="Test results")
		time.sleep(0.5)

class DashboardDemo(Demo):
	# Demo showing a real-time system dashboard
	def label(self) -> str:
		return "Real-time dashboard"

	def run(self) -> None:
		ui.section("Real-time dashboard")
		ui.muted("Updated every 0.5s — Ctrl+C to stop\n")
		time.sleep(1)
		live = getattr(ui, "dashboard", None)
		if live is not None:
			live("System Monitor", make_stats, iterations=12, interval=0.5)
		else:
			# Console version: show a few successive readings
			try:
				for i in range(4):
					ui.key_values(make_stats(), title=f"System Monitor (reading {i + 1}/4)")
					time.sleep(0.5)
			except KeyboardInterrupt:
				pass
		ui.success("Dashboard closed.")
		time.sleep(0.3)

class TreeDemo(Demo):
	# Demo showing a sample file tree
	def label(self) -> str:
		return "Tree view"

	def run(self) -> None:
		ui.section("Tree view")
		ui.info()
		ui.tree("myapp/", [
			("src/", ["main.py", "interface.py", ("utils/", ["helpers.py", "logger.py"])]),
			("tests/", ["test_main.py"]),
			"README.md",
			"requirements.txt",
		])
		ui.info()
		ui.success("Tree rendered!")
		time.sleep(0.5)

class SyntaxDemo(Demo):
	# Demo showing a code snippet
	def label(self) -> str:
		return "Syntax highlighting"

	def run(self) -> None:
		ui.section("Syntax highlighting")
		ui.info()
		ui.code(SAMPLE_CODE, "python", title="fibonacci.py")
		time.sleep(0.5)

class MarkdownDemo(Demo):
	# Demo showing a Markdown document
	def label(self) -> str:
		return "Markdown rendering"

	def run(self) -> None:
		ui.section("Markdown rendering")
		ui.info()
		ui.markdown(SAMPLE_MARKDOWN)
		time.sleep(0.5)

class FormDemo(Demo):
	# Demo running a short interactive form
	def label(self) -> str:
		return "Interactive form"

	def run(self) -> None:
		ui.section("Interactive form")
		ui.info()
		name: str | None = ui.ask("What is your name?")
		if name is None:
			return
		language: str | None = ui.choose("Favorite programming language?", ["Python", "JavaScript", "Rust", "Go"])
		features: list[str] | None = ui.choose_many("Which features interest you?", ["Type hints", "Async", "Testing", "CLI tools"])
		confirmed: bool | None = ui.confirm("Submit the form?")
		ui.info()
		if confirmed:
			ui.key_values([
				("Name", name),
				("Language", language),
				("Features", ", ".join(ui.tr(f) for f in features) if features else "-"),
			], title="Form submitted")
		else:
			ui.warning("Form cancelled.")
		time.sleep(0.5)

class LogStreamDemo(Demo):
	# Demo simulating a live application log stream
	def label(self) -> str:
		return "Log stream simulation"

	def run(self) -> None:
		ui.section("Log stream simulation")
		ui.muted("Simulating 15 log lines...\n")
		for _ in range(15):
			ui.log(random.choice(LOG_LEVELS), random.choice(LOG_MESSAGES))
			time.sleep(0.15)
		ui.success("Log stream ended.")
		time.sleep(0.5)

DEMOS: list[Demo] = [SimpleBarDemo(), MultiBarsDemo(), TableDemo(), DashboardDemo(), TreeDemo(), SyntaxDemo(), MarkdownDemo(), FormDemo(), LogStreamDemo()]

DEMO_REGISTRY: dict[str, Demo] = {demo.label(): demo for demo in DEMOS}

def slugify(label: str) -> str:
	# Turn a demo name ("Simple loading bar") into a short identifier
	# usable without quotes on the command line ("simple-loading-bar")
	slug: str = label.lower()
	slug = re.sub(r"[^a-z0-9]+", "-", slug)
	return slug.strip("-")

# Map each short identifier ("bar", "table", ...) to its demo, for the -d/--demo option
SLUG_REGISTRY: dict[str, Demo] = {slugify(demo.label()): demo for demo in DEMOS}

def make_stats() -> list[tuple[str, str]]:
	# Generate the (fake) system statistics used by the dashboard
	cpu: int = random.randint(10, 95)
	ram: int = random.randint(30, 85)
	disk: int = random.randint(40, 70)
	uptime_h: int = random.randint(1, 9)
	uptime_m: int = random.randint(10, 59)
	return [
		("CPU", f"{'█' * (cpu // 10)}{'░' * (10 - cpu // 10)} {cpu}%"),
		("RAM", f"{'█' * (ram // 10)}{'░' * (10 - ram // 10)} {ram}%"),
		("Disk", f"{'█' * (disk // 10)}{'░' * (10 - disk // 10)} {disk}%"),
		("Uptime", f"{uptime_h}h {uptime_m}m"),
	]

def build_parser() -> argparse.ArgumentParser:
	# Build the command-line argument parser
	slug_width: int = max(len(slug) for slug in SLUG_REGISTRY) + 2
	demo_list: str = "\n".join(f"  {slug:<{slug_width}} {demo.label()}" for slug, demo in SLUG_REGISTRY.items())
	epilog: str = f"Demos available for -d/--demo:\n{demo_list}"
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		description="Interactive terminal UI demo (plain console, or Rich & Questionary via display_layer.py).",
		epilog=epilog,
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}", help="Print the program version and exit.")
	parser.add_argument("-d", "--demo", choices=list(SLUG_REGISTRY.keys()), metavar="DEMO", help="Run a demo directly without the menu (see the list below).")
	parser.add_argument("--no-ui", action="store_true", help="Disable the optional display layer (display_layer.py).")
	parser.add_argument("--lang", choices=["en", "fr"], help="Select the language of the messages (en or fr).")
	parser.add_argument("-ld", "--list-demos", action="store_true", help="List the available demos and exit.")
	return parser

def splash_screen() -> None:
	# Show the welcome panel
	ui.banner(f"MyApp Console v{VERSION}", "Python interface demo")

def run_menu() -> None:
	# Main interactive menu loop
	splash_screen()
	choices: list[str] = list(DEMO_REGISTRY.keys()) + ["Quit"]
	while True:
		choice: str | None = ui.choose("What would you like to see?", choices)
		if choice is None or choice == "Quit":
			ui.info("Goodbye!")
			break
		ui.info()
		demo: Demo | None = DEMO_REGISTRY.get(choice)
		if demo is not None:
			demo.run()
		ui.pause("Press Enter to return to the menu...")
		splash_screen()

def main() -> None:
	# Entry point: parse the arguments then run a demo (CLI) or the interactive menu
	parser: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = parser.parse_args()
	if args.list_demos:
		slug: str
		slug_width: int = max(len(s) for s in SLUG_REGISTRY) + 2
		for slug, demo in SLUG_REGISTRY.items():
			print(f"  {slug:<{slug_width}} {demo.label()}")
		return
	if args.demo is not None:
		splash_screen()
		SLUG_REGISTRY[args.demo].run()
		return
	run_menu()

if __name__ == "__main__":
	main()
