#!/usr/bin/env python3

import os
import sys
import time
from fractions import Fraction

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

_SP = None

def _sp():
	global _SP
	if _SP is None:
		import sympy as sp
		_SP = sp
	return _SP

def _is_complex_tuple(val):
	return isinstance(val, tuple) and len(val) == 2

def _validate_real_float(x):
	if x != x or abs(x) == float("inf"):
		raise ValueError("NaN and infinite values are not allowed.")

def _fraction_if_rational(expr):
	sp = _sp()
	if isinstance(expr, sp.Integer):
		return Fraction(int(expr), 1)
	if isinstance(expr, sp.Rational):
		return Fraction(int(expr.p), int(expr.q))
	return expr

def _strict_positive_int(val, msg):
	if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
		raise ValueError(msg)
	return val

def _expr_to_exact(expr):
	sp = _sp()
	if expr.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
		raise ValueError("NaN and infinite values are not allowed.")
	return _fraction_if_rational(expr)

def _is_sympy(val):
	return _SP is not None and isinstance(val, _SP.Basic)

def to_exact_val(val):
	if isinstance(val, bool):
		raise ValueError("Booleans are not allowed.")
	if isinstance(val, Fraction):
		return val
	if isinstance(val, int):
		return Fraction(val, 1)
	if isinstance(val, float):
		_validate_real_float(val)
		return Fraction(str(val))
	if isinstance(val, complex):
		_validate_real_float(val.real)
		_validate_real_float(val.imag)
		sp = _sp()
		re = sp.Rational(Fraction(str(val.real)))
		im = sp.Rational(Fraction(str(val.imag)))
		return _expr_to_exact(re + sp.I * im)
	if _is_complex_tuple(val):
		sp = _sp()
		return _expr_to_exact(to_sympy(val[0]) + sp.I * to_sympy(val[1]))
	if _is_sympy(val):
		return _expr_to_exact(val)
	if isinstance(val, str):
		text = val.strip()
		if not text:
			raise ValueError("Empty string not allowed.")
		try:
			return Fraction(text)
		except ValueError:
			pass
		sp = _sp()
		try:
			expr = sp.sympify(text, locals={"i": sp.I})
		except Exception as exc:
			raise ValueError(f"Invalid value: {val!r}") from exc
		return _expr_to_exact(expr)
	raise TypeError(f"Unsupported type: {type(val).__name__}")

def to_sympy(val):
	v = to_exact_val(val)
	if isinstance(v, Fraction):
		return _sp().Rational(v.numerator, v.denominator)
	return v

def _is_zero_norm(v):
	if isinstance(v, Fraction):
		return v == 0
	return bool(_sp().simplify(v) == 0)

def _is_zero(val):
	return _is_zero_norm(to_exact_val(val))

def _pivot_key(val):
	v = to_exact_val(val)
	if _is_zero_norm(v):
		return (-1, 0.0)
	if isinstance(v, Fraction):
		return (2, float(abs(v)))
	sp = _sp()
	if v.is_number and not v.has(sp.Symbol):
		try:
			return (2, float(sp.Abs(v).evalf()))
		except Exception:
			pass
	return (1, -float(sp.count_ops(v)))

def _scalar_op(a, b, f_op, sp_op, division=False):
	va, vb = to_exact_val(a), to_exact_val(b)
	if isinstance(va, Fraction) and isinstance(vb, Fraction):
		if division and vb == 0:
			raise ZeroDivisionError("Division by zero.")
		return f_op(va, vb)
	sp = _sp()
	sa, sb = to_sympy(va), to_sympy(vb)
	if division and _is_zero_norm(sb):
		raise ZeroDivisionError("Division by zero.")
	return _fraction_if_rational(sp.simplify(sp_op(sa, sb)))

def _c_add(a, b):
	return _scalar_op(a, b, lambda x, y: x + y, lambda x, y: x + y)

def _c_sub(a, b):
	return _scalar_op(a, b, lambda x, y: x - y, lambda x, y: x - y)

def _c_mult(a, b):
	return _scalar_op(a, b, lambda x, y: x * y, lambda x, y: x * y)

def _c_div(a, b):
	return _scalar_op(a, b, lambda x, y: x / y, lambda x, y: x / y, division=True)

def fmt_val(val):
	v = to_exact_val(val)
	if isinstance(v, Fraction):
		return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
	return str(v).replace("**", "^").replace("*", "") if v.is_Atom else str(v)

def validate_scalar(val, name="scalar", allow_zero=True):
	v = to_exact_val(val)
	if not allow_zero and _is_zero_norm(v):
		raise ZeroDivisionError(f"The parameter '{name}' cannot be zero.")
	return v

def _matrix(l, c, fill):
	return [[fill(i, j) for j in range(c)] for i in range(l)]

def _dimensions(mat):
	return len(mat), len(mat[0])

def validate_matrix_2d(M, name="M"):
	if _is_sympy(M) and hasattr(M, "rows") and hasattr(M, "cols"):
		if M.rows == 0 or M.cols == 0:
			raise ValueError(f"'{name}' must be a non-empty 2D matrix.")
		return _matrix(M.rows, M.cols, lambda i, j: to_exact_val(M[i, j]))
	if not isinstance(M, (list, tuple)) or len(M) == 0:
		raise ValueError(f"'{name}' must be a non-empty 2D matrix.")
	nb_cols = len(M[0])
	if not all(isinstance(row, (list, tuple)) and len(row) == nb_cols and nb_cols > 0 for row in M):
		raise ValueError(f"'{name}' must be a non-empty rectangular 2D matrix.")
	return _matrix(len(M), nb_cols, lambda i, j: to_exact_val(M[i][j]))

def validate_square_matrix(M, name="M"):
	mat = validate_matrix_2d(M, name=name)
	l, c = _dimensions(mat)
	if l != c:
		raise ValueError(f"'{name}' must be a square matrix (got {(l, c)}).")
	return mat

def identity(n):
	_strict_positive_int(n, "The identity matrix size must be a strictly positive integer.")
	return _matrix(n, n, lambda i, j: Fraction(1, 1) if i == j else Fraction(0, 1))

def _elementwise_op(A, B, op, op_name):
	mat_A = validate_matrix_2d(A, "A")
	mat_B = validate_matrix_2d(B, "B")
	dim_A, dim_B = _dimensions(mat_A), _dimensions(mat_B)
	if dim_A != dim_B:
		raise ValueError(f"Incompatible dimensions for {op_name} : {dim_A} and {dim_B}.")
	l, c = dim_A
	return _matrix(l, c, lambda i, j: op(mat_A[i][j], mat_B[i][j]))

def add(A, B):
	return _elementwise_op(A, B, _c_add, "addition")

def sub(A, B):
	return _elementwise_op(A, B, _c_sub, "subtraction")

def mult(A, B=None, scalar=None):
	mat_A = validate_matrix_2d(A, "A")
	if B is None and scalar is None:
		raise ValueError("You must provide a matrix 'B' or a 'scalar'.")
	factor = Fraction(1, 1) if scalar is None else validate_scalar(scalar, "scalar")
	l, c = _dimensions(mat_A)
	if B is None:
		return _matrix(l, c, lambda i, j: _c_mult(mat_A[i][j], factor))
	mat_B = validate_matrix_2d(B, "B")
	n, m = _dimensions(mat_B)
	if c != n:
		raise ValueError(f"Incompatible dimensions for matrix multiplication: {(l, c)} and {(n, m)}.")

	def product(i, j):
		total_sum = Fraction(0, 1)
		for k in range(c):
			total_sum = _c_add(total_sum, _c_mult(mat_A[i][k], mat_B[k][j]))
		return _c_mult(total_sum, factor)

	return _matrix(l, m, product)

def power(M, n):
	if isinstance(n, bool) or not isinstance(n, int):
		raise ValueError("The exponent must be an integer.")
	mat = validate_square_matrix(M, "M")
	size, _ = _dimensions(mat)
	result = identity(size)
	if n == 0:
		return result
	base = inverse(mat) if n < 0 else mat
	exp = abs(n)
	while exp > 0:
		if exp % 2 == 1:
			result = mult(result, base)
		exp //= 2
		if exp > 0:
			base = mult(base, base)
	return result

def div(A, B=None, scalar=None):
	mat_A = validate_matrix_2d(A, "A")
	if scalar is not None and B is not None:
		raise ValueError("Specify either 'B' (matrix) or 'scalar', not both.")
	if scalar is not None:
		s = validate_scalar(scalar, "scalar", allow_zero=False)
		l, c = _dimensions(mat_A)
		return _matrix(l, c, lambda i, j: _c_div(mat_A[i][j], s))
	if B is None:
		raise ValueError("You must provide a matrix 'B' or a 'scalar'.")
	mat_B = validate_square_matrix(B, "B")
	_, c_A = _dimensions(mat_A)
	n_B, _ = _dimensions(mat_B)
	if c_A != n_B:
		raise ValueError(f"Incompatible dimensions for matrix division: {_dimensions(mat_A)} and {(n_B, n_B)}.")
	return mult(mat_A, inverse(mat_B))

def display_matrix(title, M, sep=None):
	if isinstance(M, (int, float, complex, Fraction)) or _is_complex_tuple(M) or _is_sympy(M):
		ui.info()
		ui.success(f"{title} : {fmt_val(M)}")
		return
	arr = validate_matrix_2d(M, title)
	l, c = _dimensions(arr)
	cells = [[fmt_val(x) for x in row] for row in arr]
	widths = [max(len(cells[i][j]) for i in range(l)) for j in range(c)]
	text_lines = []
	for row in cells:
		parts = []
		for j, val in enumerate(row):
			if sep is not None and j == sep:
				parts.append("|")
			parts.append(val.rjust(widths[j]))
		text_lines.append(f"[ {'  '.join(parts)} ]")
	ui.info()
	ui.block("\n".join(text_lines), title=title)

def submatrix(m, row, col):
	mat = validate_matrix_2d(m, "m")
	l, c = _dimensions(mat)
	if l <= 2 or c <= 2:
		raise ValueError("submatrix must only be called on a matrix of at least 3x3 to produce at least a 2x2.")
	if not (0 <= row < l) or not (0 <= col < c):
		raise IndexError(f"Indices ({row}, {col}) out of range for a matrix of size {(l, c)}.")
	return [[mat[i][j] for j in range(c) if j != col] for i in range(l) if i != row]

def _check_max_dim(n, max_dim):
	if max_dim is not None and n > max_dim:
		raise ValueError(f"Dimension {n} above the limit ({max_dim}).")

def det(M, max_dim=None):
	mat = validate_square_matrix(M, "M")
	n, _ = _dimensions(mat)
	_check_max_dim(n, max_dim)
	if n == 1:
		return mat[0][0]
	if n == 2:
		return _c_sub(_c_mult(mat[0][0], mat[1][1]), _c_mult(mat[1][0], mat[0][1]))
	total = Fraction(0, 1)
	for l in range(n):
		coeff = mat[l][0]
		if not _is_zero_norm(coeff):
			sign = Fraction(-1 if l % 2 else 1, 1)
			minor = det(submatrix(mat, l, 0), max_dim=max_dim)
			total = _c_add(total, _c_mult(_c_mult(sign, coeff), minor))
	return _fraction_if_rational(_sp().simplify(to_sympy(total))) if _is_sympy(total) else total

def cof(M, max_dim=None):
	mat = validate_square_matrix(M, "M")
	n, _ = _dimensions(mat)
	_check_max_dim(n, max_dim)
	if n == 1:
		return _matrix(1, 1, lambda i, j: Fraction(1, 1))
	if n == 2:
		a, b = mat[0][0], mat[0][1]
		c_val, d_val = mat[1][0], mat[1][1]
		values = [d_val, _c_mult(Fraction(-1, 1), c_val), _c_mult(Fraction(-1, 1), b), a]
		return _matrix(2, 2, lambda i, j: values[i * 2 + j])

	def cofactor(l, c):
		sign = Fraction(-1 if (l + c) % 2 else 1, 1)
		minor = det(submatrix(mat, l, c), max_dim=max_dim)
		return _c_mult(sign, minor)

	return _matrix(n, n, cofactor)

def transpose(M):
	mat = validate_matrix_2d(M, "M")
	l, c = _dimensions(mat)
	return _matrix(c, l, lambda j, i: mat[i][j])

def inverse(M):
	mat = validate_square_matrix(M, "M")
	n, _ = _dimensions(mat)
	B = [list(mat[i]) + [Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(n)] for i in range(n)]
	reduced, _ = gauss_jordan(B, system_columns=n)
	if any(_is_zero_norm(reduced[i][i]) for i in range(n)):
		raise ValueError("The matrix is not invertible (zero determinant).")
	return [row[n:] for row in reduced]

def _generic_pivot(M, system_columns=None, reduce_full=False):
	mat = validate_matrix_2d(M, "M")
	l, c = _dimensions(mat)
	if system_columns is None:
		nb_cols = c
	else:
		_strict_positive_int(system_columns, f"'system_columns' must be an integer between 1 and {c}.")
		if system_columns > c:
			raise ValueError(f"'system_columns' must be an integer between 1 and {c}.")
		nb_cols = system_columns
	B = [list(row) for row in mat]
	pivot_index = 0
	for col in range(nb_cols):
		if pivot_index >= l:
			break
		pivot_row = max(range(pivot_index, l), key=lambda r: _pivot_key(B[r][col]))
		if _is_zero_norm(B[pivot_row][col]):
			continue
		if pivot_row != pivot_index:
			B[pivot_index], B[pivot_row] = B[pivot_row], B[pivot_index]
		if reduce_full:
			pivot = B[pivot_index][col]
			B[pivot_index] = [_c_div(val, pivot) for val in B[pivot_index]]
			target_rows = (i for i in range(l) if i != pivot_index)
		else:
			target_rows = range(pivot_index + 1, l)
		pivot = B[pivot_index][col]
		for i in target_rows:
			if not _is_zero_norm(B[i][col]):
				factor = _c_div(B[i][col], pivot)
				B[i] = [_c_sub(B[i][j], _c_mult(factor, B[pivot_index][j])) for j in range(c)]
		pivot_index += 1
	for i in range(l):
		for j in range(c):
			val = B[i][j]
			if _is_sympy(val):
				B[i][j] = _fraction_if_rational(_sp().simplify(val))
	return B, (nb_cols if nb_cols < c else None)

def gauss(M, system_columns=None):
	return _generic_pivot(M, system_columns=system_columns, reduce_full=False)

def gauss_jordan(M, system_columns=None):
	return _generic_pivot(M, system_columns=system_columns, reduce_full=True)

def fast_factorial(m: int) -> int:
	if isinstance(m, bool) or not isinstance(m, int) or m < 0:
		raise ValueError("m must be a non-negative integer.")
	res = 1
	for i in range(2, m + 1):
		res *= i
	return res

def k_choose_n_factored_base(n, k: int, factor_tail: bool = True):
	if not isinstance(k, int) or isinstance(k, bool):
		raise TypeError("k must be a concrete integer.")
	if k < 0:
		return Fraction(0, 1)
	if k == 0:
		return Fraction(1, 1)
	n_exact = to_exact_val(n)
	fact_k = fast_factorial(k)
	if isinstance(n_exact, Fraction):
		prod_num = Fraction(1, 1)
		for i in range(k):
			prod_num *= (n_exact - Fraction(i, 1))
		return prod_num / Fraction(fact_k, 1)
	sp = _sp()
	n_sym = to_sympy(n_exact)
	prod_num = sp.Integer(1)
	for i in range(k):
		prod_num *= n_sym - i
	expr = sp.Mul(sp.Rational(1, fact_k), prod_num, evaluate=False)
	if factor_tail:
		return _fraction_if_rational(sp.factor(expr))
	return _fraction_if_rational(sp.simplify(expr) if not n_sym.is_Symbol else expr)

def matrix_nilpotency_index(N, max_k=None):
	mat = validate_square_matrix(N, "N")
	n, _ = _dimensions(mat)
	limit = n if max_k is None else max_k
	current = identity(n)
	for k in range(1, limit + 1):
		current = mult(current, mat)
		if all(_is_zero_norm(current[i][j]) for i in range(n) for j in range(n)):
			return k
	return None

def symbolic_power_n(A, sym_n=None, max_k=None):
	sp = _sp()
	if sym_n is None:
		sym_n = sp.Symbol("n", integer=True, nonnegative=True)
	mat = validate_square_matrix(A, "A")
	n, _ = _dimensions(mat)
	lam = mat[0][0]
	if all(_is_zero_norm(_c_sub(mat[i][i], lam)) for i in range(1, n)):
		N = sub(mat, mult(identity(n), scalar=lam))
		idx = matrix_nilpotency_index(N, max_k=max_k)
		if idx is not None:
			result = _matrix(n, n, lambda i, j: Fraction(0, 1))
			lam_sym = to_sympy(lam)
			for k in range(idx):
				coeff_binom = to_sympy(k_choose_n_factored_base(sym_n, k))
				factor = sp.simplify(coeff_binom * (lam_sym ** (sym_n - k)))
				result = add(result, mult(power(N, k), scalar=factor))
			return result, f"Binomial theorem (A = {fmt_val(lam)}*I + N, N^{idx} = 0)"
	sp_mat = sp.Matrix(n, n, lambda i, j: to_sympy(mat[i][j]))
	try:
		res_sp = sp.simplify(sp_mat ** sym_n)
		return _matrix(n, n, lambda i, j: to_exact_val(res_sp[i, j])), "Diagonalisation / Jordan form (SymPy)"
	except Exception as exc:
		raise ValueError(f"Cannot compute A^n symbolically: {exc}") from exc

def _read_input(message):
	# Input through the display layer; exits cleanly if the user cancels
	answer = ui.ask(message.rstrip(" :"))
	if answer is None:
		sys.exit(0)
	return answer

def _ask_int(message):
	while True:
		try:
			return int(_read_input(message).strip())
		except ValueError:
			ui.error("Invalid integer.")

def _ask_positive_int(message):
	while True:
		val = _ask_int(message)
		if val > 0:
			return val
		ui.error("Integer > 0 required.")

def input_matrix_manually(name="M", l=None, c=None):
	if l is None and c is None:
		n = _ask_positive_int(f"Size {name} (n x n) : ")
		l = c = n
	elif l is None:
		l = _ask_positive_int(f"Rows {name} : ")
	elif c is None:
		c = _ask_positive_int(f"Columns {name} : ")
	ui.section(f"{name} ({l}x{c}) | '1 -2 3/4' or '1+2*i, 0, a'")
	rows = []
	for i in range(l):
		while True:
			raw_line = _read_input(f"L{i + 1}/{l} : ").strip()
			elements = [el.strip() for el in (raw_line.split(",") if "," in raw_line else raw_line.split()) if el.strip()]
			if len(elements) != c:
				ui.error(f"Expected {c}, got {len(elements)}.")
				continue
			try:
				rows.append([to_exact_val(el) for el in elements])
				break
			except Exception as exc:
				ui.error(f"{exc}")
	return validate_matrix_2d(rows, name=name)

def _ask_scalar(name="k", allow_zero=True):
	while True:
		user_input = _read_input(f"Scalar {name} : ").strip()
		try:
			return validate_scalar(user_input, name=name, allow_zero=allow_zero)
		except Exception as exc:
			ui.error(f"{exc}")

def _ask_separator_columns(nb_cols):
	if nb_cols <= 1:
		return None
	answer = _read_input(f"Columns left of '|' (Enter = none, 1..{nb_cols - 1}) : ").strip()
	if not answer:
		return None
	val = int(answer)
	if not (1 <= val < nb_cols):
		raise ValueError(f"Separator between 1 and {nb_cols - 1} required.")
	return val

def run_menu_operation(choice):
	if choice in {"1", "2"}:
		l = _ask_positive_int("Number of rows of A and B: ")
		c = _ask_positive_int("Number of columns of A and B: ")
		A = input_matrix_manually("A", l=l, c=c)
		B = input_matrix_manually("B", l=l, c=c)
		if choice == "1":
			display_matrix("A + B", add(A, B))
		else:
			display_matrix("A - B", sub(A, B))
	elif choice == "3":
		ui.section("[mult] 1: A * B | 2: A * k")
		sub_choice = _read_input("Mode : ").strip()
		if sub_choice == "1":
			l = _ask_positive_int("Number of rows of A: ")
			c = _ask_positive_int("Number of columns of A | Number of rows of B: ")
			m = _ask_positive_int("Number of columns of B: ")
			A = input_matrix_manually("A", l=l, c=c)
			B = input_matrix_manually("B", l=c, c=m)
			display_matrix("A * B", mult(A, B=B))
		elif sub_choice == "2":
			l = _ask_positive_int("Number of rows of A: ")
			c = _ask_positive_int("Number of columns of A: ")
			A = input_matrix_manually("A", l=l, c=c)
			s = _ask_scalar("k", allow_zero=True)
			display_matrix(f"A * ({fmt_val(s)})", mult(A, scalar=s))
		else:
			ui.error("Invalid mode.")
	elif choice == "4":
		ui.section("[div] 1: A / B | 2: A / k")
		sub_choice = _read_input("Mode : ").strip()
		if sub_choice == "1":
			A = input_matrix_manually("A")
			B = input_matrix_manually("B")
			display_matrix("A / B", div(A, B=B))
		elif sub_choice == "2":
			A = input_matrix_manually("A")
			s = _ask_scalar("k", allow_zero=False)
			display_matrix(f"A / ({fmt_val(s)})", div(A, scalar=s))
		else:
			ui.error("Invalid mode.")
	elif choice == "5":
		ui.section("[power] A ^ k")
		A = input_matrix_manually("A")
		k = _ask_int("Exponent k: ")
		display_matrix(f"A ^ ({k})", power(A, k))
	elif choice == "6":
		ui.section("[det] det(A)")
		A = input_matrix_manually("A")
		display_matrix("det(A)", det(A))
	elif choice == "7":
		ui.section("[cof] cof(A)")
		A = input_matrix_manually("A")
		display_matrix("cof(A)", cof(A))
	elif choice == "8":
		ui.section("[transpose] A ^ T")
		A = input_matrix_manually("A")
		display_matrix("A ^ T", transpose(A))
	elif choice == "9":
		ui.section("[inverse] A ^ (-1)")
		A = input_matrix_manually("A")
		display_matrix("A ^ (-1)", inverse(A))
	elif choice == "10":
		ui.section("[gauss] Gaussian elimination")
		A = input_matrix_manually("A")
		_, c = _dimensions(A)
		sep_in = _ask_separator_columns(c)
		g, sep = gauss(A, system_columns=sep_in)
		display_matrix("Gauss", g, sep=sep)
	elif choice == "11":
		ui.section("[gauss_jordan] Gauss-Jordan")
		A = input_matrix_manually("A")
		_, c = _dimensions(A)
		sep_in = _ask_separator_columns(c)
		gj, sep = gauss_jordan(A, system_columns=sep_in)
		display_matrix("Gauss-Jordan", gj, sep=sep)
	elif choice == "12":
		ui.section("[power_n] A ^ n")
		A = input_matrix_manually("A")
		An, method = symbolic_power_n(A)
		ui.muted(f"Method: {method}")
		display_matrix("A ^ n", An)

MENU_OPERATIONS = [
	("1", "add           --> A + B"),
	("2", "sub           --> A - B"),
	("3", "mult          --> A * B | A * k"),
	("4", "div           --> A / B | A / k"),
	("5", "power         --> A ^ k"),
	("6", "det           --> Determinant"),
	("7", "cof           --> Cofactor matrix"),
	("8", "transpose     --> Transpose"),
	("9", "inverse       --> Inverse"),
	("10", "gauss         --> Gaussian elimination"),
	("11", "gauss_jordan  --> Gauss-Jordan"),
	("12", "power_n       --> A ^ n"),
	("0", "quit"),
]

def main():
	labels = [label for _, label in MENU_OPERATIONS]
	while True:
		ui.section("Operations menu")
		label = ui.choose("Operation:", labels)
		if label is None:
			break
		choice = MENU_OPERATIONS[labels.index(label)][0]
		if choice == "0":
			break
		try:
			run_menu_operation(choice)
		except Exception as exc:
			ui.error(str(exc))

if __name__ == "__main__":
    main()
