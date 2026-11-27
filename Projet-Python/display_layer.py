#!/usr/bin/env python3
"""
Optional display layer for the Projet-Python scripts.

If this file is next to a script, the script imports it and uses it instead
of its basic console display (print / input). It brings colours, panels,
tables, arrow-key menus (questionary), progress bars (rich) and, for
Aco-tsp.py, the matplotlib animation.

The scripts work perfectly well without it. To disable it:
  - set ACTIVE = False below
  - or run a script with --no-ui
  - or set the environment variable PROJECT_NO_UI=1
  - or simply delete / rename this file

If rich or questionary are not installed, the import fails and the scripts
automatically fall back to the plain console display.

Texts go through the script's translator (fallback.tr), so --lang fr also
applies here.
"""
import random
import time
from typing import Any

import questionary
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

# Set to False to disable the display layer without deleting the file
ACTIVE: bool = True

STYLE_MENU: questionary.Style = questionary.Style([
	("selected", "fg:cyan bold"),
	("pointer", "fg:cyan bold"),
	("highlighted", "fg:cyan"),
	("answer", "fg:green bold"),
	("question", "bold"),
])

LOG_COLORS: dict[str, str] = {"INFO": "cyan", "DEBUG": "white", "WARNING": "yellow", "ERROR": "red"}


class _RichProgress:
	# Rich progress bar with the same interface as the console version
	def __init__(self, console: Console, total: float | None, description: str, tr: Any) -> None:
		self._tr: Any = tr
		self._progress: Progress = Progress(
			SpinnerColumn(),
			TextColumn("[bold blue]{task.description}"),
			BarColumn(bar_width=30),
			MofNCompleteColumn(),
			TimeElapsedColumn(),
			console=console,
		)
		self._total: float | None = total
		self._description: str = tr(description)
		self._task: Any = None

	def __enter__(self) -> "_RichProgress":
		self._progress.__enter__()
		self._task = self._progress.add_task(escape(self._description), total=self._total)
		return self

	def __exit__(self, *exc: object) -> None:
		self._progress.__exit__(*exc)

	def advance(self, n: float = 1, description: str | None = None) -> None:
		if description is not None:
			self._progress.update(self._task, description=escape(self._tr(description)))
		self._progress.advance(self._task, n)

	def set_value(self, done: float | None = None, total: float | None = None, description: str | None = None) -> None:
		options: dict[str, Any] = {}
		if done is not None:
			options["completed"] = done
		if total is not None:
			options["total"] = total
		if description is not None:
			options["description"] = escape(self._tr(description))
		self._progress.update(self._task, **options)


class _RichMultiProgress:
	# Several rich bars in parallel
	COLORS: list[str] = ["red", "green", "blue", "magenta", "cyan", "yellow"]

	def __init__(self, console: Console, tasks: list[tuple[str, float]], tr: Any) -> None:
		self._progress: Progress = Progress(
			SpinnerColumn(),
			TextColumn("[bold]{task.description:<20}"),
			BarColumn(bar_width=30),
			MofNCompleteColumn(),
			TimeElapsedColumn(),
			console=console,
		)
		self._definition: list[tuple[str, float]] = [(tr(name), total) for name, total in tasks]
		self._ids: list[Any] = []

	def __enter__(self) -> "_RichMultiProgress":
		self._progress.__enter__()
		for i, (name, total) in enumerate(self._definition):
			color: str = self.COLORS[i % len(self.COLORS)]
			self._ids.append(self._progress.add_task(f"[{color}]{escape(name)}", total=total))
		return self

	def __exit__(self, *exc: object) -> None:
		self._progress.__exit__(*exc)

	def advance(self, index: int, n: float = 1) -> None:
		task = next(t for t in self._progress.tasks if t.id == self._ids[index])
		self._progress.advance(self._ids[index], min(n, (task.total or 0) - task.completed))

	def finished(self) -> bool:
		return self._progress.finished


class RichDisplay:
	# Display implementation with rich + questionary.
	# Any method not defined here is delegated to the base console display.
	def __init__(self, fallback: Any) -> None:
		self._fallback: Any = fallback
		self.console: Console = Console()
		self.tr: Any = getattr(fallback, "tr", lambda text: text)
		self.lang: str = getattr(fallback, "lang", "en")

	def __getattr__(self, name: str) -> Any:
		return getattr(self._fallback, name)

	# --- Messages -----------------------------------------------------------
	def clear(self) -> None:
		self.console.clear()

	def banner(self, title: str, subtitle: str = "") -> None:
		self.console.clear()
		title, subtitle = self.tr(title), self.tr(subtitle)
		content: str = f"[bold cyan]  {escape(title)}  [/]"
		if subtitle:
			content += f"\n[dim]{escape(subtitle)}[/]"
		self.console.print(Panel(content, border_style="cyan", padding=(1, 8)))
		self.console.print()

	def section(self, title: str) -> None:
		self.console.print(Rule(f"[bold yellow]{escape(self.tr(title))}[/]"))

	def info(self, message: str = "") -> None:
		self.console.print(escape(self.tr(message)))

	def muted(self, message: str) -> None:
		self.console.print(f"[dim]{escape(self.tr(message))}[/]")

	def success(self, message: str) -> None:
		self.console.print(f"[bold green]✓ {escape(self.tr(message))}[/]")

	def warning(self, message: str) -> None:
		self.console.print(f"[yellow]⚠ {escape(self.tr(message))}[/]")

	def error(self, message: str) -> None:
		self.console.print(f"[bold red]✗ {escape(self.tr(message))}[/]")

	# --- Structured blocks --------------------------------------------------
	def block(self, text: str, title: str | None = None) -> None:
		self.console.print(Panel(escape(self.tr(text)), title=f"[bold]{escape(self.tr(title))}[/]" if title else None, border_style="cyan"))

	def key_values(self, pairs: list[tuple[str, object]], title: str | None = None) -> None:
		table: Table = Table(box=None, show_header=False, padding=(0, 2))
		table.add_column("Key", style="cyan")
		table.add_column("Value", style="bold white")
		for key, value in pairs:
			table.add_row(escape(str(self.tr(str(key)))), escape(str(self.tr(value))))
		self.console.print(Panel(table, title=f"[bold]{escape(self.tr(title))}[/]" if title else None, border_style="cyan"))

	def table(self, columns: list[str], rows: list[list[object]], title: str | None = None) -> None:
		table: Table = Table(title=self.tr(title), header_style="bold magenta", border_style="bright_black")
		for i, column in enumerate(columns):
			table.add_column(escape(str(self.tr(str(column)))), style="cyan" if i == 0 else None)
		for row in rows:
			table.add_row(*[escape(str(self.tr(c))) for c in row])
		self.console.print(table)

	def tree(self, root: str, children: list) -> None:
		tree: Tree = Tree(f"[bold cyan]{escape(self.tr(root))}[/]")
		self._tree(tree, children)
		self.console.print(tree)

	def _tree(self, node: Tree, children: list) -> None:
		for child in children:
			if isinstance(child, tuple):
				self._tree(node.add(f"[bold]{escape(self.tr(child[0]))}[/]"), child[1])
			else:
				node.add(escape(str(self.tr(child))))

	def code(self, text: str, language: str = "", title: str | None = None) -> None:
		syntax: Syntax = Syntax(text, language or "text", theme="monokai", line_numbers=True)
		self.console.print(Panel(syntax, border_style="bright_black", title=self.tr(title)))

	def markdown(self, text: str) -> None:
		self.console.print(Markdown(self.tr(text)))

	def log(self, level: str, message: str) -> None:
		row: Text = Text()
		row.append(f"[{time.strftime('%H:%M:%S')}] ", style="dim")
		row.append(f"{level:<8}", style=LOG_COLORS.get(level, "white"))
		row.append(self.tr(message))
		self.console.print(row)

	# --- Input --------------------------------------------------------------
	def ask(self, question: str, default: str | None = None) -> str | None:
		answer: str | None = questionary.text(self.tr(question), default=default or "", style=STYLE_MENU).ask()
		return None if answer is None else answer.strip()

	def ask_path(self, question: str, default: str | None = None) -> str | None:
		answer: str | None = questionary.path(self.tr(question), default=default or "", style=STYLE_MENU).ask()
		return None if answer is None else answer.strip()

	def ask_number(self, question: str, default: float | None = None, integer: bool = True, minimum: float | None = None, maximum: float | None = None) -> float | int | None:
		def validate(text: str) -> bool | str:
			try:
				value: float = int(text) if integer else float(text)
			except ValueError:
				return self.tr("Invalid number")
			if minimum is not None and value < minimum:
				return self.tr(f"Must be >= {minimum}")
			if maximum is not None and value > maximum:
				return self.tr(f"Must be <= {maximum}")
			return True
		answer: str | None = questionary.text(self.tr(question), default="" if default is None else str(default), validate=validate, style=STYLE_MENU).ask()
		if answer is None:
			return None
		return int(answer) if integer else float(answer)

	def confirm(self, question: str, default: bool = False) -> bool | None:
		if self.lang == "en":
			return questionary.confirm(question, default=default, style=STYLE_MENU).ask()
		# questionary.confirm only understands y/n: other languages use a Yes/No menu
		choices: list[questionary.Choice] = [questionary.Choice(self.tr("Yes"), value=True), questionary.Choice(self.tr("No"), value=False)]
		return questionary.select(self.tr(question), choices=choices, default=choices[0] if default else choices[1], instruction=" ", style=STYLE_MENU).ask()

	def choose(self, question: str, options: list[str], default: str | None = None) -> str | None:
		if not options:
			return None
		# The translated label is shown, the original option is returned
		choices: list[questionary.Choice] = [questionary.Choice(self.tr(o), value=o) for o in options]
		return questionary.select(self.tr(question), choices=choices, default=default if default in options else None, instruction=self.tr("(Use arrow keys)"), style=STYLE_MENU).ask()

	def choose_many(self, question: str, options: list[str], checked: list[str] | None = None) -> list[str] | None:
		choice: list[questionary.Choice] = [questionary.Choice(self.tr(o), value=o, checked=bool(checked and o in checked)) for o in options]
		return questionary.checkbox(self.tr(question), choices=choice, instruction=self.tr("(Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)"), style=STYLE_MENU).ask()

	def pause(self, message: str = "Press Enter to continue...") -> None:
		try:
			self.console.input(f"\n[dim]  [ {escape(self.tr(message))} ][/]")
		except (EOFError, KeyboardInterrupt):
			pass

	# --- Progress -----------------------------------------------------------
	def progress(self, total: float | None, description: str = "") -> _RichProgress:
		return _RichProgress(self.console, total, description, self.tr)

	def multi_progress(self, tasks: list[tuple[str, float]]) -> _RichMultiProgress:
		return _RichMultiProgress(self.console, tasks, self.tr)

	def status(self, message: str) -> Any:
		status: Any = self.console.status(f"[cyan]{escape(self.tr(message))}...[/]")
		original_update: Any = status.update
		status.update = lambda m: original_update(f"[cyan]{escape(self.tr(m))}...[/]")
		return status

	# --- Extensions specific to some scripts --------------------------------
	def dashboard(self, title: str, generate_pairs: Any, iterations: int = 12, interval: float = 0.5) -> None:
		# Live-updated panel (Interface.py)
		def rendered() -> Panel:
			table: Table = Table(box=None, show_header=False, padding=(0, 2))
			table.add_column("Key", style="cyan")
			table.add_column("Value", style="bold white")
			for key, value in generate_pairs():
				table.add_row(self.tr(key), self.tr(value))
			return Panel(table, title=f"[bold cyan]{escape(self.tr(title))}", border_style="cyan", padding=(1, 2))
		try:
			with Live(rendered(), refresh_per_second=4, console=self.console) as live:
				for _ in range(iterations):
					time.sleep(interval)
					live.update(rendered())
		except KeyboardInterrupt:
			pass

	def visualize_aco(self, colony: Any) -> None:
		# Matplotlib animation of the ant colony (Aco-tsp.py)
		try:
			import matplotlib.pyplot as plt
			from matplotlib.animation import FuncAnimation
		except ImportError:
			self.warning("matplotlib is not installed: running without animation.")
			raise
		figure, (map_ax, curve_ax) = plt.subplots(1, 2, figsize=(12, 5))
		state: dict[str, int] = {"iteration": 0}

		def update(_frame: int) -> None:
			if state["iteration"] >= colony.iterations:
				return
			colony.run_iteration()
			state["iteration"] += 1
			map_ax.clear()
			cities = colony.graph.cities
			map_ax.scatter([v.x for v in cities], [v.y for v in cities], c="black", zorder=3)
			if colony.best_tour is not None:
				tour = colony.best_tour
				for i in range(len(tour)):
					a = cities[tour[i]]
					b = cities[tour[(i + 1) % len(tour)]]
					map_ax.plot([a.x, b.x], [a.y, b.y], c="crimson", linewidth=2, zorder=2)
			map_ax.set_title(self.tr(f"Best tour — iteration {state['iteration']} — length {colony.best_length:.2f}"))
			curve_ax.clear()
			curve_ax.plot(colony.length_history, c="steelblue")
			curve_ax.set_title("Convergence")
			curve_ax.set_xlabel(self.tr("Iteration"))
			curve_ax.set_ylabel(self.tr("Best tour length"))

		import warnings
		warnings.filterwarnings("ignore", message="Animation was deleted")
		animation = FuncAnimation(figure, update, frames=colony.iterations, interval=100, repeat=False)
		plt.tight_layout()
		plt.show()
		# If the window is closed before the end, finish the remaining iterations
		while state["iteration"] < colony.iterations:
			colony.run_iteration()
			state["iteration"] += 1
		del animation


def create_display(fallback: Any) -> RichDisplay | None:
	# Entry point called by the scripts; None = keep the console display
	if not ACTIVE:
		return None
	return RichDisplay(fallback)
