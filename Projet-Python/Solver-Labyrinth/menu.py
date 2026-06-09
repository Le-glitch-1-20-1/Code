from __future__ import annotations

import os
import sys
import threading

try:
	import questionary
	from rich.console  import Console
	from rich.panel	import Panel
	from rich.rule	 import Rule
	from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
	_RICH = True
except ImportError:
	_RICH = False

if _RICH:
	console = Console()
	_STYLE  = questionary.Style([
		("qmark",		"fg:cyan bold"),
		("question",	"bold"),
		("answer",		"fg:cyan bold"),
		("pointer",		"fg:cyan bold"),
		("highlighted",	"fg:cyan"),
		("selected",	"fg:cyan"),
		("separator",	"fg:default"),
		("instruction",	"fg:default dim"),
	])

def splash() -> None:
	if _RICH:
		console.clear()
		console.print()
		console.print(
			Panel(
				"[bold white]🧩  MAZE SOLVER[/]\n[dim]Generate · Solve · Play[/]",
				border_style="cyan",
				padding=(1, 6),
				expand=False,
			),
			justify="center",
		)
		console.print()
	else:
		print("\n=== MAZE SOLVER ===\nGenerate · Solve · Play\n")

def section(title: str) -> None:
	if _RICH:
		console.print()
		console.print(Rule(f"[dim]{title}[/]", style="cyan"))
		console.print()
	else:
		print(f"\n--- {title} ---\n")

def ok(msg: str) -> None:
	if _RICH:
		console.print(f"  [bold green]✓[/]  {msg}")
	else:
		print(f"  [OK]  {msg}")

def err(msg: str) -> None:
	if _RICH:
		console.print(f"  [bold red]✗[/]  {msg}")
	else:
		print(f"  [ERROR]  {msg}")

def info(msg: str) -> None:
	if _RICH:
		console.print(f"  [dim]{msg}[/]")
	else:
		print(f"  {msg}")

def success_panel(msg: str) -> None:
	if _RICH:
		console.print()
		console.print(Panel(msg, border_style="green", padding=(0, 2), expand=False))
		console.print()
	else:
		import re
		clean = re.sub(r"\[/?[a-zA-Z0-9_ :]+\]", "", msg)
		print(f"\n  {clean}\n")

def with_spinner(label: str, fn):
	if not _RICH:
		print(f"  {label}")
		return fn()
	result = [None]
	error  = [None]

	def worker():
		try:
			result[0] = fn()
		except Exception as exc:
			error[0] = exc
	t = threading.Thread(target=worker)
	with Progress(
		SpinnerColumn("dots", style="cyan"),
		TextColumn(f"[cyan]{label}[/]"),
		TimeElapsedColumn(),
		console=console,
		transient=True,
	) as progress:
		progress.add_task("", total=None)
		t.start()
		t.join()
	if error[0]:
		raise error[0]
	return result[0]

def move_progress(fn) -> None:
	if not _RICH:
		fn()
		return
	with Progress(
		SpinnerColumn("dots", style="cyan"),
		TextColumn("[cyan]Moving…[/]"),
		TimeElapsedColumn(),
		console=console,
		transient=True,
	) as progress:
		progress.add_task("", total=None)
		fn()

def wait_for_key(key_char: str = "m") -> None:
	try:
		from pynput.keyboard import Listener
	except ImportError:
		input(f"  Position yourself on the game window, then press Enter to start…")
		return
	if _RICH:
		console.print(
			Panel(
				f"[white]Position yourself on the game window,\n"
				f"then press [bold cyan]{key_char.upper()}[/] to start.[/]",
				border_style="dim",
				padding=(0, 2),
				expand=False,
			)
		)
		console.print()
	else:
		print(f"  Position yourself on the game window, then press {key_char.upper()} to start.")
	done = threading.Event()
	def on_press(key):
		try:
			if key.char and key.char.lower() == key_char:
				done.set()
				return False
		except AttributeError:
			pass
	with Listener(on_press=on_press):
		done.wait()

def _ask_select(prompt: str, choices: list) -> str:
	if _RICH:
		result = questionary.select(prompt, choices=choices, style=_STYLE).ask()
		if result is None:
			sys.exit(0)
		return result
	print(f"\n{prompt}")
	items = []
	for i, c in enumerate(choices, 1):
		if isinstance(c, str):
			print(f"  {i}. {c}")
			items.append(c)
		elif hasattr(c, "title") and hasattr(c, "value"):
			print(f"  {i}. {c.title}")
			items.append(c.value)
		elif isinstance(c, dict):
			label = c.get("label", "")
			value = c.get("value")
			if value is None:
				print(f"  {'─' * 20}")
			else:
				print(f"  {i}. {label}")
			items.append(value)
		else:
			items.append(None)
	while True:
		raw = input("Choice (number): ").strip()
		try:
			idx = int(raw) - 1
			if 0 <= idx < len(items) and items[idx] is not None:
				return items[idx]
		except ValueError:
			pass
		print("  Invalid choice, please try again.")

def _ask_confirm(prompt: str, default: bool = False) -> bool:
	if _RICH:
		result = questionary.confirm(prompt, default=default, style=_STYLE).ask()
		if result is None:
			sys.exit(0)
		return result
	hint = "[y/n, default y]" if default else "[y/n, default n]"
	raw  = input(f"{prompt} {hint}: ").strip().lower()
	if raw == "":
		return default
	return raw in ("y", "yes")

def _ask_text(prompt: str, default=None, validate=None) -> str:
	if _RICH:
		kw = {}
		if default is not None:
			kw["default"] = str(default)
		if validate:
			kw["validate"] = validate
		result = questionary.text(prompt, style=_STYLE, **kw).ask()
		if result is None:
			sys.exit(0)
		return result.strip()
	hint = f" [{default}]" if default is not None else ""
	while True:
		raw = input(f"{prompt}{hint}: ").strip()
		if raw == "" and default is not None:
			raw = str(default)
		if validate:
			outcome = validate(raw)
			if outcome is not True:
				print(f"  {outcome}")
				continue
		return raw

def ask_int(prompt: str, default: int | None = None) -> int:
	def validate(val):
		try:
			int(val)
			return True
		except ValueError:
			return "Please enter a whole number."
	return int(_ask_text(prompt, default=default, validate=validate))

def ask_float(prompt: str, default: float | None = None) -> float:
	def validate(val):
		try:
			float(val)
			return True
		except ValueError:
			return "Please enter a number."
	return float(_ask_text(prompt, default=default, validate=validate))

def ask_text(prompt: str, default: str | None = None, validate=None) -> str:
	return _ask_text(prompt, default=default, validate=validate)

def ask_confirm(prompt: str, default: bool = False) -> bool:
	return _ask_confirm(prompt, default=default)

def _choice(label: str, value):
	if _RICH:
		return questionary.Choice(label, value=value)
	return {"label": label, "value": value}

def _separator():
	if _RICH:
		return questionary.Separator()
	return {"label": "─" * 20, "value": None}

def menu_main() -> str:
	splash()
	return _ask_select("What would you like to do?", [
		_choice("Generate a maze",			"generate"),
		_choice("Capture from maze.toys",	"site"),
		_separator(),
		_choice("Quit",						"quit"),
	])

def menu_generate() -> dict:
	from generate_maze import SIZES
	section("Maze Settings")
	size_choices = [
		_choice(f"{name:<12} — {SIZES[name]['cols']}×{SIZES[name]['rows']}", name)
		for name in SIZES
	] + [_choice("custom", "custom")]
	size = _ask_select("Size preset", size_choices)
	cols = rows = cell = wall = None
	if size == "custom":
		print()
		cols = ask_int("Columns",		 default=20)
		rows = ask_int("Rows",			default=20)
		cell = ask_int("Cell size (px)",  default=18)
		wall = ask_int("Wall width (px)", default=2)
	seed = None
	if ask_confirm("Use a fixed random seed?"):
		seed = ask_int("Seed value")
	return dict(size=size, cols=cols, rows=rows, cell=cell, wall=wall, seed=seed)

_MAZETOYS_SIZES = [
	"mini", "medium", "mighty", "mega",
	"monolithic", "magnificent", "maligned", "monstrous",
	"mammoth", "megalomaniac",
]

def menu_site() -> dict:
	section("Maze Source")
	src = _ask_select("Source", [
		_choice("URL — maze.toys (regular)", "url"),
		_choice("URL — maze.toys (daily)",   "daily"),
		_choice("Local image file",		  "file"),
	])
	url		= None
	image_path = None
	if src in ("url", "daily"):
		size_choices = [_choice(name, name) for name in _MAZETOYS_SIZES] + \
					   [_choice("Custom URL…", "__custom__")]
		chosen = _ask_select("Maze size", size_choices)
		if chosen == "__custom__":
			url = ask_text("Full URL")
		else:
			if src == "daily":
				url = f"https://maze.toys/mazes/{chosen}/daily/"
			else:
				url = f"https://maze.toys/mazes/{chosen}/"
	else:
		image_path = ask_text("Image path")
		if not os.path.exists(image_path):
			err(f"File not found: {image_path}")
			sys.exit(1)
	tol = None
	if ask_confirm("Adjust pixel tolerance?"):
		tol = ask_int("Tolerance (0–255)", default=30)
	speed = ask_float("Delay between key presses (s)", default=0.1)
	return dict(url=url, image_path=image_path, tol=tol, speed=speed)
