#!/usr/bin/env python3

import time
import random
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
	Progress, SpinnerColumn, BarColumn,
	TextColumn, TimeElapsedColumn, MofNCompleteColumn
)
from rich.rule import Rule
from rich.syntax import Syntax
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

console = Console()

def splash_screen():
	console.clear()
	console.print()
	console.print(Panel(
		"[bold cyan]  MyApp Console  [/]\n"
		"[dim]Python interface with Rich & Questionary[/]",
		border_style="cyan",
		padding=(1, 8),
	))
	console.print()

def demo_simple_bar():
	console.print(Rule("[bold yellow]Simple loading bar"))
	console.print()

	with Progress(
		TextColumn("[bold blue]{task.description}"),
		BarColumn(bar_width=40),
		"[progress.percentage]{task.percentage:>3.0f}%",
		TimeElapsedColumn(),
	) as progress:
		task = progress.add_task("Loading...", total=100)
		while not progress.finished:
			progress.advance(task, random.randint(1, 4))
			time.sleep(0.04)
	console.print("[green]✓ Done![/]\n")
	time.sleep(0.5)

def demo_multi_bars():
	console.print(Rule("[bold yellow]Multiple bars in parallel"))
	console.print()
	with Progress(
		SpinnerColumn(),
		TextColumn("[bold]{task.description:<20}"),
		BarColumn(bar_width=30),
		MofNCompleteColumn(),
		TimeElapsedColumn(),
	) as progress:
		t1 = progress.add_task("[red]Download", total=60)
		t2 = progress.add_task("[green]Processing", total=40)
		t3 = progress.add_task("[blue]Saving    ", total=20)
		while not progress.finished:
			progress.advance(t1, random.randint(0, 3))
			progress.advance(t2, random.randint(0, 2))
			progress.advance(t3, random.randint(0, 1))
			time.sleep(0.06)
	console.print("[green]✓ All tasks completed![/]\n")
	time.sleep(0.5)

def demo_table():
	console.print(Rule("[bold yellow]Formatted table"))
	console.print()
	table = Table(
		title="Test results",
		show_header=True,
		header_style="bold magenta",
		border_style="bright_black",
		show_lines=True,
	)
	table.add_column("Name",	style="cyan",   no_wrap=True)
	table.add_column("Status", justify="center")
	table.add_column("Score",  justify="right")
	table.add_column("Time",  justify="right", style="dim")
	data = [
		("Alice",   True,  98, "0.42s"),
		("Bob",	 False, 34, "1.21s"),
		("Carla",   True,  87, "0.67s"),
		("David",   True,  91, "0.38s"),
		("Emma",	False, 52, "0.99s"),
	]
	for name, ok, score, elapsed in data:
		status = "[bold green]✓ OK[/]" if ok else "[bold red]✗ FAIL[/]"
		score_str = f"[bold]{score}[/]" if ok else f"[red]{score}[/]"
		table.add_row(name, status, score_str, elapsed)
	console.print(table)
	console.print()
	time.sleep(0.5)

def demo_dashboard():
	console.print(Rule("[bold yellow]Real-time dashboard"))
	console.print("[dim]Updated every 0.5s — Ctrl+C to stop\n")
	time.sleep(1)
	def make_stats_table():
		t = Table(box=None, show_header=False, padding=(0, 2))
		t.add_column("Key",	style="cyan")
		t.add_column("Value", style="bold white")
		cpu  = random.randint(10, 95)
		ram  = random.randint(30, 85)
		disk = random.randint(40, 70)
		t.add_row("CPU",  f"{'█' * (cpu  // 10)}{'░' * (10 - cpu  // 10)} {cpu}%")
		t.add_row("RAM",  f"{'█' * (ram  // 10)}{'░' * (10 - ram  // 10)} {ram}%")
		t.add_row("Disk", f"{'█' * (disk // 10)}{'░' * (10 - disk // 10)} {disk}%")
		t.add_row("Uptime", f"{random.randint(1,9)}h {random.randint(10,59)}m")
		return t
	try:
		with Live(refresh_per_second=2) as live:
			for _ in range(12):
				panel = Panel(
					make_stats_table(),
					title="[bold cyan]  System Monitor",
					border_style="cyan",
					padding=(1, 2),
				)
				live.update(panel)
				time.sleep(0.5)
	except KeyboardInterrupt:
		pass
	console.print("\n[green]✓ Dashboard closed.[/]\n")
	time.sleep(0.3)

def main():
	splash_screen()

	while True:
		choice = questionary.select(
			"What would you like to see?",
			choices=[
				"📊  Simple loading bar",
				"🔄  Multiple bars in parallel",
				"📋  Formatted table",
				"🖥️   Real-time dashboard",
				"🚪  Quit",
			],
			style=questionary.Style([
				("selected",		"fg:cyan bold"),
				("pointer",		 "fg:cyan bold"),
				("highlighted",	 "fg:cyan"),
				("answer",		  "fg:green bold"),
				("question",		"bold"),
			])
		).ask()
		if choice is None or "Quit" in choice:
			console.print("\n[bold yellow]Goodbye! 👋[/]\n")
			break
		console.print()
		if "Simple" in choice:
			demo_simple_bar()
		elif "parallel" in choice:
			demo_multi_bars()
		elif "table" in choice:
			demo_table()
		elif "dashboard" in choice:
			demo_dashboard()
		input("\n  [ Press Enter to return to the menu... ]")
		console.clear()
		splash_screen()

if __name__ == "__main__":
	main()
