#!/usr/bin/env python3
import argparse
import os
import sys
import time
from abc			import ABC, abstractmethod
from math			import comb
from typing			import Any
from sympy			import SympifyError, expand, latex, sympify

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
SUPERSCRIPT_DIGITS: str = "⁰¹²³⁴⁵⁶⁷⁸⁹"
MENU_CHOICES: list[str] = [
	"Show a row of Pascal's triangle",
	"Expand a binomial (a + b)^n",
	"Quit",
]
def info(message: str) -> None:
	# Show a normal message in the console
	ui.info(message)

def error(message: str) -> None:
	# Show an error
	ui.error(message)

def print_banner() -> None:
	# Show the program header
	ui.banner(f"Pascal & Binome Toolkit v{VERSION}", "Pascal's triangle and binomial expansion")

def int_to_superscript(n: int) -> str:
	# Convert an integer to Unicode superscript digits
	if not isinstance(n, int):
		raise TypeError(f"Expected int, got {type(n).__name__}.")
	negative: bool = n < 0
	result: str = "".join(SUPERSCRIPT_DIGITS[int(d)] for d in str(abs(n)))
	return ("⁻" if negative else "") + result

def format_expr_unicode(expr: str) -> str:
	# Replace the "**exponent" parts of a sympy expression with Unicode superscript digits
	if not isinstance(expr, str):
		raise TypeError(f"Expected str, got {type(expr).__name__}.")
	s: str = expr.replace("**", "^")
	result: str = ""
	i: int = 0
	while i < len(s):
		if s[i] == "^":
			i += 1
			if i < len(s) and s[i] == "(":
				# Exponent in parentheses, e.g. ^(-2)
				depth: int = 1
				j: int = i + 1
				while j < len(s) and depth > 0:
					if s[j] == "(":
						depth += 1
					elif s[j] == ")":
						depth -= 1
					j += 1
				inner: str = s[i + 1:j - 1]
				if inner.lstrip("-").isdigit():
					result += int_to_superscript(int(inner))
				else:
					result += "^" + s[i:j]
				i = j
				continue
			exp: str = ""
			if i < len(s) and s[i] == "-":
				exp += "-"
				i += 1
			while i < len(s) and s[i].isdigit():
				exp += s[i]
				i += 1
			if not exp or exp == "-":
				result += "^" + exp
			else:
				result += int_to_superscript(int(exp))
		else:
			result += s[i]
			i += 1
	return result

def binomial_coef(n: int, k: int) -> int:
	# Compute the binomial coefficient C(n, k)
	if not isinstance(n, int) or not isinstance(k, int):
		raise TypeError("n and k must be integers.")
	if n < 0 or k < 0:
		raise ValueError("n and k must be non-negative integers.")
	return comb(n, k)

def display_pascal_row(n: int) -> None:
	# Show row n of Pascal's triangle in a table
	if not isinstance(n, int):
		raise TypeError("Row number must be an integer.")
	if n < 0:
		error("Row number must be a non-negative integer.")
		return
	row: list[int] = [binomial_coef(n, k) for k in range(n + 1)]
	ui.table([f"k={k}" for k in range(n + 1)], [row], title=f"Row {n} of Pascal's triangle")

def expand_binomial(a_input: str, b_input: str, n: int, use_latex: bool = False) -> None:
	# Expand (a + b)^n and show each term as well as the result
	if not isinstance(a_input, str) or not isinstance(b_input, str):
		raise TypeError("a and b must be strings.")
	if not isinstance(n, int):
		raise TypeError("n must be an integer.")
	if n < 0:
		error("n must be a non-negative integer.")
		return
	try:
		sympify(a_input)
	except (SympifyError, SyntaxError, TypeError):
		error(f"'{a_input}' is not a valid mathematical expression.")
		return
	try:
		sympify(b_input)
	except (SympifyError, SyntaxError, TypeError):
		error(f"'{b_input}' is not a valid mathematical expression.")
		return
	try:
		expr: Any = sympify(f"({a_input} + {b_input})**{n}")
		res: Any = expand(expr)
	except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
		error(f"Could not expand expression: {exc}")
		return
	b_stripped: str = b_input.lstrip()
	base_unicode: str
	try:
		if b_stripped.startswith("-"):
			inner_b: str = b_stripped[1:].lstrip()
			base_unicode = (
				f"({format_expr_unicode(a_input)} - {format_expr_unicode(inner_b)})"
				f"{int_to_superscript(n)}"
			)
		else:
			base_unicode = (
				f"({format_expr_unicode(a_input)} + {format_expr_unicode(b_input)})"
				f"{int_to_superscript(n)}"
			)
	except (TypeError, ValueError) as exc:
		error(f"Could not format expression for display: {exc}")
		return
	terms: list[str] = []
	k: int
	for k in range(n + 1):
		c: int = comb(n, k)
		try:
			term_expr: Any = sympify(f"{c} * ({a_input})**{n - k} * ({b_input})**{k}")
			term_expanded: Any = expand(term_expr)
			terms.append(format_expr_unicode(str(term_expanded)))
		except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
			error(f"Could not compute term k={k}: {exc}")
			return
	# The first term is shown without a sign, the following ones with + or -
	joined: str = ""
	idx: int
	term: str
	for idx, term in enumerate(terms):
		stripped: str = term.lstrip()
		if stripped.startswith("-"):
			body: str = stripped[1:].lstrip()
			joined += f"-{body}" if idx == 0 else f" - {body}"
		else:
			joined += stripped if idx == 0 else f" + {stripped}"
	info(f"{base_unicode} = " + joined)
	try:
		res_unicode: str = format_expr_unicode(str(res))
	except (TypeError, ValueError) as exc:
		error(f"Could not format result: {exc}")
		return
	info(f"{' ' * len(base_unicode)} = {res_unicode}")
	if use_latex:
		try:
			ui.block(latex(res), title="LaTeX")
		except Exception as exc:
			error(f"Could not generate LaTeX output: {exc}")

class Command(ABC):
	# Common interface every command of the program must follow
	@abstractmethod
	def run(self) -> None:
		# Command entry point
		raise NotImplementedError

class TriangleCommand(Command):
	# Command that prints a row of Pascal's triangle
	def __init__(self, n: int) -> None:
		self.n: int = n

	def run(self) -> None:
		display_pascal_row(self.n)

class BinomialCommand(Command):
	# Command that expands a binomial (a + b)^n
	def __init__(self, a_input: str, b_input: str, n: int, use_latex: bool) -> None:
		self.a_input: str = a_input
		self.b_input: str = b_input
		self.n: int = n
		self.use_latex: bool = use_latex

	def run(self) -> None:
		expand_binomial(self.a_input, self.b_input, self.n, use_latex=self.use_latex)

def run_triangle_interactive() -> None:
	# Collect the row number through a prompt then print the row
	raw: str | None = ui.ask("Row number")
	if raw is None:
		return
	if not raw:
		error("No value entered.")
		return
	n: int
	try:
		n = int(raw)
	except ValueError:
		error(f"'{raw}' is not a valid integer.")
		return
	ui.info()
	TriangleCommand(n).run()

def run_binomial_interactive() -> None:
	# Collect a, b, n and the LaTeX option through prompts then expand the binomial
	a_input: str = ui.ask("Value or symbol for a", "a") or "a"
	b_input: str = ui.ask("Value or symbol for b", "b") or "b"
	raw_n: str | None = ui.ask("Value of n")
	if not raw_n:
		error("No value entered for n.")
		return
	n: int
	try:
		n = int(raw_n)
	except ValueError:
		error(f"'{raw_n}' is not a valid integer.")
		return
	use_latex: bool | None = ui.confirm("Also show in LaTeX?", default=False)
	ui.info()
	BinomialCommand(a_input, b_input, n, use_latex=bool(use_latex)).run()

def run_interactive_menu(
	preset_mode: str | None = None,
	preset_n: int | None = None,
	preset_a: str | None = None,
	preset_b: str | None = None,
	preset_latex: bool = False,
) -> None:
	# Interactive menu, prefilled with the values already given as arguments
	if preset_mode == "1":
		info(f"Mode (preselected): {MENU_CHOICES[0]}")
		if preset_n is not None:
			info(f"Row number (preselected): {preset_n}")
			ui.info()
			TriangleCommand(preset_n).run()
			return
		run_triangle_interactive()
		return
	if preset_mode == "2":
		info(f"Mode (preselected): {MENU_CHOICES[1]}")
		if preset_a is not None and preset_b is not None and preset_n is not None:
			info(f"a = {preset_a}, b = {preset_b}, n = {preset_n} (preselected)")
			ui.info()
			BinomialCommand(preset_a, preset_b, preset_n, use_latex=preset_latex).run()
			return
		run_binomial_interactive()
		return
	choice: str | None = ui.choose("What would you like to do?", MENU_CHOICES)
	if choice is None or "Quit" in choice:
		ui.success("See you soon!")
		return
	ui.info()
	if "triangle" in choice:
		run_triangle_interactive()
	elif "binomial" in choice:
		run_binomial_interactive()

def parse_binomial_arg(raw: str) -> tuple[str, str, str] | None:
	# Parse the "A,B,N" format of --binomial, show an error and return None if invalid
	parts: list[str] = raw.split(",")
	if len(parts) != 3:
		error(f"'--binomial' expects the format \"A,B,N\", got '{raw}'.")
		return None
	return parts[0].strip(), parts[1].strip(), parts[2].strip()

def build_parser() -> argparse.ArgumentParser:
	# Build the argparse CLI: options for the triangle, the binomial, LaTeX and interactive mode
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		prog="pascal_triangle_binomial.py",
		description="Print a row of Pascal's triangle or expand a binomial (a + b)^n.",
		epilog=(
			"Examples:\n"
			"  pascal_triangle_binomial.py --triangle 5\n"
			"  pascal_triangle_binomial.py --binomial \"x,y,3\" --latex\n"
		),
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}", help="Print the program version and exit.")
	parser.add_argument("--triangle", type=int, metavar="N", help="Print row N of Pascal's triangle (N >= 0).")
	parser.add_argument("--binomial", metavar="A,B,N", help="Expand the binomial (A + B)^N, e.g. --binomial \"x,-y,3\".")
	parser.add_argument("--latex", action="store_true", help="Also print the result in LaTeX notation.")
	parser.add_argument("--no-ui", action="store_true", help="Disable the optional display layer (display_layer.py).")
	parser.add_argument("--lang", choices=["en", "fr"], help="Select the language of the messages (en or fr).")
	parser.add_argument("--interactive", action="store_true", help="Force the interactive menu, prefilled with the other options.")
	return parser

def main() -> None:
	# Entry point: parse the arguments, show the banner, then run the chosen mode
	parser: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = parser.parse_args()
	print_banner()
	if args.triangle is not None and not args.interactive and not args.binomial:
		if args.triangle < 0:
			error("N must be a non-negative integer.")
			sys.exit(1)
		TriangleCommand(args.triangle).run()
		return
	if args.binomial and not args.interactive:
		parsed: tuple[str, str, str] | None = parse_binomial_arg(args.binomial)
		if parsed is None:
			sys.exit(1)
		a_input: str
		b_input: str
		n_str: str
		a_input, b_input, n_str = parsed
		n: int
		try:
			n = int(n_str)
		except ValueError:
			error(f"'{n_str}' is not a valid integer for N.")
			sys.exit(1)
		BinomialCommand(a_input, b_input, n, use_latex=args.latex).run()
		return
	preset_mode: str | None = None
	preset_n: int | None = None
	preset_a: str | None = None
	preset_b: str | None = None
	if args.triangle is not None:
		preset_mode = "1"
		preset_n = args.triangle
	if args.binomial:
		parsed = parse_binomial_arg(args.binomial)
		if parsed is None:
			sys.exit(1)
		preset_mode = "2"
		n_str2: str
		preset_a, preset_b, n_str2 = parsed
		try:
			preset_n = int(n_str2)
		except ValueError:
			error(f"'{n_str2}' is not a valid integer for N.")
			sys.exit(1)
	run_interactive_menu(
		preset_mode=preset_mode,
		preset_n=preset_n,
		preset_a=preset_a,
		preset_b=preset_b,
		preset_latex=args.latex,
	)

if __name__ == "__main__":
	main()
