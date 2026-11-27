#!/usr/bin/env python3
import argparse
import math
import os
import random
import sys
import time
from abc			import ABC, abstractmethod
from typing			import Optional
from PIL			import Image

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

VERSION: str = "1.0.0"
DEFAULT_IMAGE_DIR: str = "image"
DEFAULT_OUTPUT_NAME: str = "hidden_message.png"
MAX_ROW_WIDTH: int = 800
SUPPORTED_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp")
# Byte values allowed in a message on top of printable ASCII (tab, newline, carriage return)
ALLOWED_EXTRA_BYTES: tuple[int, ...] = (9, 10, 13)
ALLOWED_RANGE: range = range(32, 127)
LENGTH_HEADER_BITS: int = 32
MAX_MESSAGE_BYTES: int = (2 ** LENGTH_HEADER_BITS) - 1
# Literal escape sequences the user can type, mapped to the real character
ESCAPE_SEQUENCES: dict[str, str] = {
	"\\n": "\n",
	"\\t": "\t",
	"\\r": "\r",
}
MENU_CHOICES: list[str] = [
	"Hide a message in an image",
	"Reveal a message from an image",
	"Quit",
]
class IStegoTool(ABC):
	# Common interface for every steganography tool of the program
	@abstractmethod
	def run(self, args: argparse.Namespace) -> None:
		raise NotImplementedError

def info(message: str) -> None:
	# Show a normal message in the console
	ui.info(message)

def warn(message: str) -> None:
	# Show a warning
	ui.warning(message)

def error(message: str) -> None:
	# Show an error
	ui.error(message)

def print_banner() -> None:
	# Show the program header
	ui.banner(f"Steganography Toolkit v{VERSION}", "Hide and reveal messages in images")

def parity_digit(value: int) -> int:
	# Reduce a byte value to a single digit by repeated digit sum, return its parity (0/1)
	while value >= 10:
		value = sum(int(digit) for digit in str(value))
	return 0 if value % 2 == 0 else 1

def build_value_pools() -> tuple[list[int], list[int]]:
	# Split the 0-255 range into two sets, one per parity value
	even_values: list[int] = [v for v in range(256) if parity_digit(v) == 0]
	odd_values: list[int] = [v for v in range(256) if parity_digit(v) == 1]
	return even_values, odd_values

def nearest_value_with_parity(value: int, target_bit: str) -> int:
	# Find the byte value closest to the original that has the target parity
	target: int = 1 if target_bit == "1" else 0
	if parity_digit(value) == target:
		return value
	delta: int = 1
	while True:
		lower: int = value - delta
		upper: int = value + delta
		if lower >= 0 and parity_digit(lower) == target:
			return lower
		if upper <= 255 and parity_digit(upper) == target:
			return upper
		if lower < 0 and upper > 255:
			raise ValueError("No suitable byte value found (unexpected).")
		delta += 1

def build_bit_stream(message_bytes: bytes) -> str:
	# Build the full bit stream: fixed-length header then message bits
	if len(message_bytes) > MAX_MESSAGE_BYTES:
		raise ValueError(f"Message too long (max {MAX_MESSAGE_BYTES} bytes).")
	header_bits: str = format(len(message_bytes), f"0{LENGTH_HEADER_BITS}b")
	message_bits: str = "".join(f"{byte:08b}" for byte in message_bytes)
	return header_bits + message_bits

def interpret_escapes(raw_message: str) -> str:
	# Replace the literal "\n", "\t", "\r" typed by the user with the real characters
	message: str = raw_message
	literal: str
	real_char: str
	for literal, real_char in ESCAPE_SEQUENCES.items():
		message = message.replace(literal, real_char)
	return message

def validate_message(message: str) -> bytes:
	# Check that the message only uses characters that can be decoded later, then encode it
	if not message:
		raise ValueError("The message is empty.")
	invalid_chars: list[str] = sorted({
		c for c in message
		if ord(c) not in ALLOWED_RANGE and ord(c) not in ALLOWED_EXTRA_BYTES
	})
	if invalid_chars:
		raise ValueError(
			"The message contains characters that cannot be decoded later: "
			f"{invalid_chars}. Only printable ASCII, tab and newline are supported."
		)
	return message.encode("ascii")

def choose_dimensions(pixel_count_needed: int) -> tuple[int, int]:
	# Choose the width/height of a new image so it holds pixel_count_needed pixels
	if pixel_count_needed <= MAX_ROW_WIDTH:
		return pixel_count_needed, 1
	width: int = MAX_ROW_WIDTH
	height: int = math.ceil(pixel_count_needed / width)
	return width, height

def hide_message(message: str, output_path: str) -> Image.Image:
	# Encode a message in a brand new image where each channel's parity carries one bit
	message_bytes: bytes = validate_message(message)
	bit_string: str = build_bit_stream(message_bytes)
	pixel_count_needed: int = math.ceil(len(bit_string) / 3)
	width: int
	height: int
	width, height = choose_dimensions(pixel_count_needed)
	bit_string = bit_string.ljust(width * height * 3, "0")
	even_values: list[int]
	odd_values: list[int]
	even_values, odd_values = build_value_pools()
	rng: random.Random = random.Random()
	image: Image.Image = Image.new("RGB", (width, height))
	pixels: object = image.load()
	bit_index: int = 0
	with ui.progress(height, "Encoding") as progress:
		y: int
		for y in range(height):
			x: int
			for x in range(width):
				channel_values: list[int] = []
				_channel: int
				for _channel in range(3):
					bit: str = bit_string[bit_index]
					bit_index += 1
					pool: list[int] = odd_values if bit == "1" else even_values
					channel_values.append(rng.choice(pool))
				pixels[x, y] = tuple(channel_values)
			progress.advance()
	os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
	image.save(output_path)
	return image

def hide_message_in_existing_image(message: str, source_path: str, output_path: str) -> dict[str, object]:
	# Encode a message in an existing image by adjusting each channel to the right parity
	message_bytes: bytes = validate_message(message)
	bit_string: str = build_bit_stream(message_bytes)
	pixel_count_needed: int = math.ceil(len(bit_string) / 3)
	bit_string = bit_string.ljust(pixel_count_needed * 3, "0")
	image: Image.Image
	with Image.open(source_path) as img:
		image = img.convert("RGB")
	width: int
	height: int
	width, height = image.size
	total_pixels: int = width * height
	if pixel_count_needed > total_pixels:
		raise ValueError(
			f"This image is too small: it has {total_pixels} pixels but the "
			f"message needs at least {pixel_count_needed}. Use a "
			f"bigger image or a shorter message."
		)
	pixels: object = image.load()
	bit_index: int = 0
	channels_changed: int = 0
	max_delta: int = 0
	delta_sum: int = 0
	remaining_pixels: int = pixel_count_needed
	if not output_path.lower().endswith(".png"):
		output_path = os.path.splitext(output_path)[0] + ".png"
	with ui.progress(height, "Encoding") as progress:
		y: int
		for y in range(height):
			if remaining_pixels <= 0:
				progress.set_value(done=height)
				break
			x: int
			for x in range(width):
				if remaining_pixels <= 0:
					break
				r: int
				g: int
				b: int
				r, g, b = pixels[x, y]
				new_channels: list[int] = []
				original: int
				for original in (r, g, b):
					target_bit: str = bit_string[bit_index]
					bit_index += 1
					new_value: int = nearest_value_with_parity(original, target_bit)
					delta: int = abs(new_value - original)
					if delta:
						channels_changed += 1
						delta_sum += delta
						max_delta = max(max_delta, delta)
					new_channels.append(new_value)
				pixels[x, y] = tuple(new_channels)
				remaining_pixels -= 1
			progress.advance()
	os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
	image.save(output_path)
	return {
		"output_path": output_path,
		"width": width,
		"height": height,
		"pixels_used": pixel_count_needed,
		"total_pixels": total_pixels,
		"channels_changed": channels_changed,
		"channels_touched_total": pixel_count_needed * 3,
		"max_delta": max_delta,
		"avg_delta": (delta_sum / channels_changed) if channels_changed else 0.0,
	}

def reveal_message(image_path: str) -> str:
	# Read back the length header then the message bits from the channel parities
	image: Image.Image
	width: int
	height: int
	pixels: object
	with Image.open(image_path) as img:
		image = img.convert("RGB")
		width, height = image.size
		pixels = image.load()
	bit_buffer: list[int] = []
	message_length: Optional[int] = None
	total_bits_needed: int = LENGTH_HEADER_BITS
	with ui.progress(height, "Decoding") as progress:
		y: int
		for y in range(height):
			x: int
			for x in range(width):
				r: int
				g: int
				b: int
				r, g, b = pixels[x, y]
				bit_buffer.append(parity_digit(r))
				bit_buffer.append(parity_digit(g))
				bit_buffer.append(parity_digit(b))
				if message_length is None and len(bit_buffer) >= LENGTH_HEADER_BITS:
					header_bits: str = "".join(map(str, bit_buffer[:LENGTH_HEADER_BITS]))
					message_length = int(header_bits, 2)
					total_bits_needed = LENGTH_HEADER_BITS + message_length * 8
				if len(bit_buffer) >= total_bits_needed and message_length is not None:
					data_bits: list[int] = bit_buffer[LENGTH_HEADER_BITS:total_bits_needed]
					data_bits_str: str = "".join(map(str, data_bits))
					message_bytes: bytes = bytes(
						int(data_bits_str[i:i + 8], 2)
						for i in range(0, len(data_bits_str), 8)
					)
					return message_bytes.decode("ascii", errors="replace")
			progress.advance()
	raise ValueError(
		"Cannot fully read a hidden message in this image "
		"(it may not contain one, or the image is too small/corrupted)."
	)

def list_images(image_dir: str) -> list[str]:
	# List the supported image files in the given folder
	if not os.path.isdir(image_dir):
		return []
	return sorted(f for f in os.listdir(image_dir) if f.lower().endswith(SUPPORTED_EXTENSIONS))

def pick_image_interactive(prompt: str, image_dir: str) -> Optional[str]:
	# Ask the user to pick an image from the given folder
	images: list[str] = list_images(image_dir)
	if not images:
		error(f"No image found in '{image_dir}/'. Put an image there first.")
		return None
	choice: Optional[str] = ui.choose(prompt, images)
	if choice is None:
		return None
	return os.path.join(image_dir, choice)

def run_hide_flow(image_dir: str) -> None:
	# Interactive flow: hide a message in a new or existing image, then self-check the result
	sub_choice: Optional[str] = ui.choose(
		"Where should the message be hidden?",
		["In a brand new image", "In an existing image (keeps its appearance)"],
	)
	if sub_choice is None:
		return
	raw_message: Optional[str] = ui.ask("Message to hide (\\n, \\t, \\r are supported)")
	if raw_message is None:
		return
	message: str = interpret_escapes(raw_message)
	output_path: str = os.path.join(image_dir, DEFAULT_OUTPUT_NAME)
	recovered: str
	if "existing" in sub_choice:
		source_path: Optional[str] = pick_image_interactive("Choose the image to hide the message in:", image_dir)
		if source_path is None:
			return
		stats: dict[str, object]
		try:
			stats = hide_message_in_existing_image(message, source_path, output_path)
		except (ValueError, OSError) as exc:
			error(str(exc))
			return
		info(f"\nMessage hidden in '{source_path}' -> saved as '{stats['output_path']}'")
		info(f"Image size: {stats['width']}x{stats['height']} "
			f"({stats['pixels_used']}/{stats['total_pixels']} pixels touched)")
		info(f"Channels changed: {stats['channels_changed']}/{stats['channels_touched_total']} "
			f"(average change: {stats['avg_delta']:.2f}, max : {stats['max_delta']}) — "
			f"visually indistinguishable from the original.")
		recovered = reveal_message(str(stats["output_path"]))
	else:
		image: Image.Image
		try:
			image = hide_message(message, output_path)
		except ValueError as exc:
			error(str(exc))
			return
		except OSError as exc:
			error(f"Error while saving the image: {exc}")
			return
		info(f"\nMessage hidden in an image of {image.size[0]}x{image.size[1]}.")
		info(f"Saving as: {output_path}")
		recovered = reveal_message(output_path)
	if recovered == message:
		ui.success("Self-check passed: the message can be recovered from this image.")
	else:
		warn("Self-check failed, the message was not recovered correctly.")

def run_reveal_flow(image_dir: str) -> None:
	# Interactive flow: reveal a message from an image picked in the given folder
	image_path: Optional[str] = pick_image_interactive("Choose the image to analyse:", image_dir)
	if image_path is None:
		return
	message: str
	try:
		message = reveal_message(image_path)
	except (OSError, ValueError) as exc:
		error(f"Error while reading '{image_path}' : {exc}")
		return
	info(f"\nHidden message:\n{message}")

def run_interactive_menu(image_dir: str) -> None:
	# Interactive menu shown when the script is run without a subcommand
	while True:
		choice: Optional[str] = ui.choose("What would you like to do?", MENU_CHOICES)
		if choice is None or "Quit" in choice:
			ui.success("See you soon!")
			return
		ui.info()
		if "Hide" in choice:
			run_hide_flow(image_dir)
		elif "Reveal" in choice:
			run_reveal_flow(image_dir)
		ui.pause("Press Enter to return to the menu...")
		print_banner()

class HideTool(IStegoTool):
	# Hide a message in a new or existing image
	def run(self, args: argparse.Namespace) -> None:
		raw_message: Optional[str] = " ".join(args.message) if args.message else ui.ask("Message to hide")
		message: str = interpret_escapes(raw_message or "")
		output_path: str = args.output or os.path.join(args.image_dir, DEFAULT_OUTPUT_NAME)
		if args.image:
			stats: dict[str, object]
			try:
				stats = hide_message_in_existing_image(message, args.image, output_path)
			except (ValueError, OSError) as exc:
				error(str(exc))
				sys.exit(1)
			info(f"Saving as: {stats['output_path']} ({stats['width']}x{stats['height']}, "
				f"{stats['channels_changed']}/{stats['channels_touched_total']} channels "
				f"adjusted by {stats['avg_delta']:.2f} on average, max {stats['max_delta']})")
			return
		image: Image.Image
		try:
			image = hide_message(message, output_path)
		except ValueError as exc:
			error(str(exc))
			sys.exit(1)
		info(f"Saving as: {output_path} ({image.size[0]}x{image.size[1]})")

class RevealTool(IStegoTool):
	# Reveal a message hidden in an image
	def run(self, args: argparse.Namespace) -> None:
		try:
			info(reveal_message(args.image))
		except (OSError, ValueError) as exc:
			error(str(exc))
			sys.exit(1)

HIDE_TOOL: HideTool = HideTool()
REVEAL_TOOL: RevealTool = RevealTool()

def build_parser() -> argparse.ArgumentParser:
	# Build the argparse CLI: global options and hide/reveal subcommands
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		prog="steganography.py",
		description="Hide or reveal a text message in the parity of an image's colour channels.",
		epilog=(
			"Examples:\n"
			"  steganography.py hide \"my secret message\"\n"
			"  steganography.py hide \"my message\" --image photo.png\n"
			"  steganography.py reveal image/hidden_message.png\n"
		),
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}", help="Print the program version and exit.")
	parser.add_argument("--no-ui", action="store_true", help="Disable the optional display layer (display_layer.py).")
	parser.add_argument("--lang", choices=["en", "fr"], help="Select the language of the messages (en or fr).")
	parser.add_argument("--image-dir", type=str, default=DEFAULT_IMAGE_DIR, metavar="PATH", help="Folder used to look for/save images (default: image/).")
	subparsers: argparse._SubParsersAction = parser.add_subparsers(dest="command", required=False, metavar="{hide,reveal}")
	hide_parser: argparse.ArgumentParser = subparsers.add_parser(
		"hide",
		help="Hide a message in a new or existing image.",
		description="Hide a text message in the parity of an image's colour channels.",
	)
	hide_parser.add_argument("message", nargs="*", help="Message to hide (prompted if omitted).")
	hide_parser.add_argument("--image", metavar="PATH", help="Existing image to hide the message in.")
	hide_parser.add_argument("--output", metavar="PATH", help="Output path (default: <image-dir>/hidden_message.png).")
	hide_parser.set_defaults(func=HIDE_TOOL.run)
	reveal_parser: argparse.ArgumentParser = subparsers.add_parser(
		"reveal",
		help="Reveal a message hidden in an image.",
		description="Reveal a text message hidden in the parity of an image's colour channels.",
	)
	reveal_parser.add_argument("image", help="Path of the image to analyse.")
	reveal_parser.set_defaults(func=REVEAL_TOOL.run)
	return parser

def main() -> None:
	# Entry point: parse the arguments, show the banner, then run the chosen command
	parser: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = parser.parse_args()
	print_banner()
	if not args.command:
		run_interactive_menu(args.image_dir)
		return
	args.func(args)

if __name__ == "__main__":
	main()
