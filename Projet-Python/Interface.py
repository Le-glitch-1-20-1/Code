#!/usr/bin/env python3

from __future__		import annotations
import sys
import io
import re
import argparse
import random
import time
import questionary
import shutil
from abc			import ABC, abstractmethod
from rich.console	import Console
from rich.live		import Live
from rich.markdown	import Markdown
from rich.panel		import Panel
from rich.progress	import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn
from rich.rule		import Rule
from rich.syntax	import Syntax
from rich.table		import Table
from rich.text		import Text
from rich.tree		import Tree

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

console: Console = Console()

VERSION: str = "2.0.0"

ANSI_COLORS: dict[str, str] = {"red": "31", "green": "32", "yellow": "33", "blue": "34", "magenta": "35", "cyan": "36", "white": "37", "bold": "1"}

MENU_STYLE: questionary.Style = questionary.Style([("selected", "fg:cyan bold"), ("pointer", "fg:cyan bold"), ("highlighted", "fg:cyan"), ("answer", "fg:green bold"), ("question", "bold")])

TABLE_DATA: list[tuple[str, bool, int, str]] = [("Alice", True, 98, "0.42s"), ("Bob", False, 34, "1.21s"), ("Carla", True, 87, "0.67s"), ("David", True, 91, "0.38s"), ("Emma", False, 52, "0.99s")]

SAMPLE_CODE: str = f"""def fibonacci(n: int) -> int:\n\t# Return the n-th Fibonacci number.\n\ta, b = 0, 1\n\tfor _ in range(n):\n\t\ta, b = b, a + b\n\treturn a"""

SAMPLE_MARKDOWN: str = f"""# Project Report\n\n## Summary\n- **Status**: On track\n- **Coverage**: 92%\n- *Next milestone*: v2.0\n\n```python\nprint("hello world")\n```"""

LOG_LEVELS: list[tuple[str, str]] = [("INFO",	"cyan"), ("DEBUG",	"white"), ("WARNING",	"yellow"), ("ERROR",	"red")]

LOG_MESSAGES: list[str] = ["Connecting to database...", "Cache warmed up successfully", "Received request GET /api/users", "Slow query detected (312ms)", "Retrying failed connection", "Background job finished", "Memory usage at 74%", "New client connected"]

class Demo(ABC):
	# Interface commune que doit respecter toute démo du programme
	@abstractmethod
	def label(self) -> str:
		# Nom affiché dans le menu et utilisable en CLI
		raise NotImplementedError

	@abstractmethod
	def run(self) -> None:
		# Point d'entrée de la démo
		raise NotImplementedError

class SimpleBarDemo(Demo):
	# Démo affichant une barre de progression simple
	def label(self) -> str:
		return "Simple loading bar"

	def run(self) -> None:
		console.print(Rule("[bold yellow]Simple loading bar"))
		console.print()
		with Progress(TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=40), "[progress.percentage]{task.percentage:>3.0f}%", TimeElapsedColumn()) as progress:
			task: TaskID = progress.add_task("Loading...", total=100)
			while not progress.finished:
				progress.advance(task, random.randint(1, 4))
				time.sleep(0.04)
		print(colorize("✓ Done!", "green"))
		time.sleep(0.5)

class MultiBarsDemo(Demo):
	# Démo affichant plusieurs barres de progression en parallèle
	def label(self) -> str:
		return "Multiple bars in parallel"

	def run(self) -> None:
		console.print(Rule("[bold yellow]Multiple bars in parallel"))
		console.print()
		with Progress(SpinnerColumn(), TextColumn("[bold]{task.description:<20}"), BarColumn(bar_width=30), MofNCompleteColumn(), TimeElapsedColumn()) as progress:
			t1: TaskID = progress.add_task("[red]Download", total=60)
			t2: TaskID = progress.add_task("[green]Processing", total=40)
			t3: TaskID = progress.add_task("[blue]Saving", total=20)
			while not progress.finished:
				progress.advance(t1, random.randint(0, 3))
				progress.advance(t2, random.randint(0, 2))
				progress.advance(t3, random.randint(0, 1))
				time.sleep(0.06)
		print(colorize("✓ All tasks completed!", "green"))
		time.sleep(0.5)

class TableDemo(Demo):
	# Démo affichant un tableau de résultats formaté
	def label(self) -> str:
		return "Formatted table"

	def run(self) -> None:
		console.print(Rule("[bold yellow]Formatted table"))
		console.print()
		table: Table = Table(title="Test results", show_header=True, header_style="bold magenta", border_style="bright_black", show_lines=True)
		table.add_column("Name", style="cyan", no_wrap=True)
		table.add_column("Status", justify="center")
		table.add_column("Score", justify="right")
		table.add_column("Time", justify="right", style="dim")
		name: str
		ok: bool
		score: int
		elapsed: str
		for name, ok, score, elapsed in TABLE_DATA:
			status: str = "[green]✓ OK[/]" if ok else "[red]✗ FAIL[/]"
			score_str: str = f"[white]{score}[/]" if ok else f"[red]{score}[/]"
			table.add_row(name, status, score_str, elapsed)
		console.print(table)
		console.print()
		time.sleep(0.5)

class DashboardDemo(Demo):
	# Démo affichant un dashboard système temps réel
	def label(self) -> str:
		return "Real-time dashboard"

	def run(self) -> None:
		console.print(Rule("[bold yellow]Real-time dashboard"))
		console.print("[dim]Updated every 0.5s — Ctrl+C to stop\n")
		time.sleep(1)
		try:
			with Live(refresh_per_second=2) as live:
				i: int
				for i in range(12):
					panel: Panel = Panel(make_stats_table(), title="[bold cyan]  System Monitor", border_style="cyan", padding=(1, 2))
					live.update(panel)
					time.sleep(0.5)
		except KeyboardInterrupt:
			pass
		print(colorize("✓ Dashboard closed.", "green"))
		time.sleep(0.3)

class TreeDemo(Demo):
	# Démo affichant une arborescence de fichiers d'exemple
	def label(self) -> str:
		return "Tree view"

	def run(self) -> None:
		console.print(Rule("[bold yellow]Tree view"))
		console.print()
		tree: Tree = Tree("[bold cyan]myapp/")
		src: Tree = tree.add("[bold]src/")
		src.add("main.py")
		src.add("interface.py")
		utils: Tree = src.add("[bold]utils/")
		utils.add("helpers.py")
		utils.add("logger.py")
		tests: Tree = tree.add("[bold]tests/")
		tests.add("test_main.py")
		tree.add("README.md")
		tree.add("requirements.txt")
		console.print(tree)
		console.print()
		print(colorize("✓ Tree rendered!", "green"))
		time.sleep(0.5)

class SyntaxDemo(Demo):
	# Démo affichant un extrait de code avec coloration syntaxique
	def label(self) -> str:
		return "Syntax highlighting"

	def run(self) -> None:
		console.print(Rule("[bold yellow]Syntax highlighting"))
		console.print()
		syntax: Syntax = Syntax(SAMPLE_CODE, "python", theme="monokai", line_numbers=True)
		console.print(Panel(syntax, border_style="bright_black", title="fibonacci.py"))
		console.print()
		time.sleep(0.5)

class MarkdownDemo(Demo):
	# Démo affichant un document Markdown
	def label(self) -> str:
		return "Markdown rendering"

	def run(self) -> None:
		console.print(Rule("[bold yellow]Markdown rendering"))
		console.print()
		console.print(Markdown(SAMPLE_MARKDOWN))
		console.print()
		time.sleep(0.5)

class FormDemo(Demo):
	# Démo faisant passer un court formulaire interactif
	def label(self) -> str:
		return "Interactive form"

	def run(self) -> None:
		console.print(Rule("[bold yellow]Interactive form"))
		console.print()
		name: str | None = questionary.text("What is your name?").ask()
		if name is None:
			return
		language: str | None = questionary.select("Favorite programming language?", choices=["Python", "JavaScript", "Rust", "Go"], style=MENU_STYLE).ask()
		features: list[str] | None = questionary.checkbox("Which features interest you?", choices=["Type hints", "Async", "Testing", "CLI tools"]).ask()
		confirmed: bool | None = questionary.confirm("Submit the form?").ask()
		console.print()
		if confirmed:
			summary: Table = Table(box=None, show_header=False, padding=(0, 2))
			summary.add_column("Field", style="cyan")
			summary.add_column("Value", style="bold white")
			summary.add_row("Name", str(name))
			summary.add_row("Language", str(language))
			summary.add_row("Features", ", ".join(features) if features else "-")
			console.print(Panel(summary, title="[bold green]Form submitted", border_style="green"))
		else:
			console.print(colorize("Form cancelled.", "yellow"))
		time.sleep(0.5)

class LogStreamDemo(Demo):
	# Démo simulant un flux de logs applicatifs en direct
	def label(self) -> str:
		return "Log stream simulation"

	def run(self) -> None:
		console.print(Rule("[bold yellow]Log stream simulation"))
		console.print("[dim]Simulating 15 log lines...\n")
		i: int
		for i in range(15):
			level: str
			color: str
			level, color = random.choice(LOG_LEVELS)
			message: str = random.choice(LOG_MESSAGES)
			timestamp: str = time.strftime("%H:%M:%S")
			line: Text = Text()
			line.append(f"[{timestamp}] ", style="dim")
			line.append(f"{level:<8}", style=color)
			line.append(message)
			console.print(line)
			time.sleep(0.15)
		print(colorize("✓ Log stream ended.", "green"))
		time.sleep(0.5)

DEMOS: list[Demo] = [SimpleBarDemo(), MultiBarsDemo(), TableDemo(), DashboardDemo(), TreeDemo(), SyntaxDemo(), MarkdownDemo(), FormDemo(), LogStreamDemo()]

DEMO_REGISTRY: dict[str, Demo] = {demo.label(): demo for demo in DEMOS}

def slugify(label: str) -> str:
	# Transforme un nom de démo ("Simple loading bar") en identifiant court
	# utilisable sans guillemets sur la ligne de commande ("simple-loading-bar")
	slug: str = label.lower()
	slug = re.sub(r"[^a-z0-9]+", "-", slug)
	return slug.strip("-")

# Associe chaque identifiant court ("bar", "table", ...) à sa démo, pour l'option -d/--demo
SLUG_REGISTRY: dict[str, Demo] = {slugify(demo.label()): demo for demo in DEMOS}

def colorize(text: str, color: str) -> str:
	# Encadre le texte avec les codes ANSI de la couleur demandée
	code: str = ANSI_COLORS.get(color, "0")
	return f"\033[{code}m{text}\033[0m"

def make_stats_table() -> Table:
	# Génère le tableau de statistiques système utilisé par le dashboard
	t: Table = Table(box=None, show_header=False, padding=(0, 2))
	t.add_column("Key", style="cyan")
	t.add_column("Value", style="bold white")
	cpu: int = random.randint(10, 95)
	ram: int = random.randint(30, 85)
	disk: int = random.randint(40, 70)
	uptime_h: int = random.randint(1, 9)
	uptime_m: int = random.randint(10, 59)
	t.add_row("CPU", f"{'█' * (cpu // 10)}{'░' * (10 - cpu // 10)} {cpu}%")
	t.add_row("RAM", f"{'█' * (ram // 10)}{'░' * (10 - ram // 10)} {ram}%")
	t.add_row("Disk", f"{'█' * (disk // 10)}{'░' * (10 - disk // 10)} {disk}%")
	t.add_row("Uptime", f"{uptime_h}h {uptime_m}m")
	return t

def build_parser() -> argparse.ArgumentParser:
	# Construit le parseur d'arguments en ligne de commande
	largeur_slug: int = max(len(slug) for slug in SLUG_REGISTRY) + 2
	demo_list: str = "\n".join(f"  {slug:<{largeur_slug}} {demo.label()}" for slug, demo in SLUG_REGISTRY.items())
	epilog: str = f"Démos disponibles pour -d/--demo :\n{demo_list}"
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		description="Interactive terminal UI demo built with Rich & Questionary.",
		epilog=epilog,
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}", help="Affiche la version du programme et quitte.")
	parser.add_argument("-d", "--demo", choices=list(SLUG_REGISTRY.keys()), metavar="DEMO", help="Lance directement une démo sans passer par le menu (voir la liste ci-dessous).")
	parser.add_argument("-ld", "--list-demos", action="store_true", help="Liste les démos disponibles et quitte.")
	return parser

def make_separator() -> questionary.Separator:
	# Crée la ligne de séparation adaptée à la largeur du terminal
	largeur_console: int = shutil.get_terminal_size(fallback=(80, 24)).columns
	return questionary.Separator("─" * largeur_console)

def splash_screen() -> None:
	# Efface la console et affiche le panneau de bienvenue
	console.clear()
	console.print()
	console.print(Panel(f"[bold cyan]MyApp Console v{VERSION}[/]\n[dim]Python interface with Rich & Questionary[/]", border_style="cyan", padding=(1, 8),))
	console.print()

def run_menu() -> None:
	# Boucle du menu interactif principal
	splash_screen()
	choices: list[str] = list(DEMO_REGISTRY.keys()) + [make_separator()] + ["Quit"]
	while True:
		choice: str | None = questionary.select("What would you like to see?", choices=choices, style=MENU_STYLE).ask()
		if choice is None or choice == "Quit":
			print(colorize("Goodbye!", "yellow"))
			break
		console.print()
		demo: Demo | None = DEMO_REGISTRY.get(choice)
		if demo is not None:
			demo.run()
		input("\n  [ Press Enter to return to the menu... ]")
		console.clear()
		splash_screen()

def main() -> None:
	# Point d'entrée : parse les arguments puis lance une démo (CLI) ou le menu interactif
	parser: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = parser.parse_args()
	if args.list_demos:
		slug: str
		largeur_slug: int = max(len(s) for s in SLUG_REGISTRY) + 2
		for slug, demo in SLUG_REGISTRY.items():
			print(f"  {slug:<{largeur_slug}} {demo.label()}")
		return
	if args.demo is not None:
		splash_screen()
		SLUG_REGISTRY[args.demo].run()
		return
	run_menu()

main()
