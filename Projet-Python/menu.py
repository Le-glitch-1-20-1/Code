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
		"[bold cyan]  MonApp Console  [/]\n"
		"[dim]Interface Python avec Rich & Questionary[/]",
		border_style="cyan",
		padding=(1, 8),
	))
	console.print()

def demo_barre_simple():
	console.print(Rule("[bold yellow]Barre de chargement simple"))
	console.print()

	with Progress(
		TextColumn("[bold blue]{task.description}"),
		BarColumn(bar_width=40),
		"[progress.percentage]{task.percentage:>3.0f}%",
		TimeElapsedColumn(),
	) as progress:
		task = progress.add_task("Chargement...", total=100)
		while not progress.finished:
			progress.advance(task, random.randint(1, 4))
			time.sleep(0.04)
	console.print("[green]✓ Terminé ![/]\n")
	time.sleep(0.5)

def demo_multi_barres():
	console.print(Rule("[bold yellow]Plusieurs barres en parallèle"))
	console.print()
	with Progress(
		SpinnerColumn(),
		TextColumn("[bold]{task.description:<20}"),
		BarColumn(bar_width=30),
		MofNCompleteColumn(),
		TimeElapsedColumn(),
	) as progress:
		t1 = progress.add_task("[red]Téléchargement", total=60)
		t2 = progress.add_task("[green]Traitement   ", total=40)
		t3 = progress.add_task("[blue]Sauvegarde   ", total=20)
		while not progress.finished:
			progress.advance(t1, random.randint(0, 3))
			progress.advance(t2, random.randint(0, 2))
			progress.advance(t3, random.randint(0, 1))
			time.sleep(0.06)
	console.print("[green]✓ Toutes les tâches terminées ![/]\n")
	time.sleep(0.5)

def demo_tableau():
	console.print(Rule("[bold yellow]Tableau formaté"))
	console.print()
	table = Table(
		title="Résultats des tests",
		show_header=True,
		header_style="bold magenta",
		border_style="bright_black",
		show_lines=True,
	)
	table.add_column("Nom",	style="cyan",   no_wrap=True)
	table.add_column("Statut", justify="center")
	table.add_column("Score",  justify="right")
	table.add_column("Temps",  justify="right", style="dim")
	donnees = [
		("Alice",   True,  98, "0.42s"),
		("Bob",	 False, 34, "1.21s"),
		("Carla",   True,  87, "0.67s"),
		("David",   True,  91, "0.38s"),
		("Emma",	False, 52, "0.99s"),
	]
	for nom, ok, score, temps in donnees:
		statut = "[bold green]✓ OK[/]" if ok else "[bold red]✗ FAIL[/]"
		score_str = f"[bold]{score}[/]" if ok else f"[red]{score}[/]"
		table.add_row(nom, statut, score_str, temps)
	console.print(table)
	console.print()
	time.sleep(0.5)

def demo_dashboard():
	console.print(Rule("[bold yellow]Dashboard en temps réel"))
	console.print("[dim]Mise à jour toutes les 0.5s — Ctrl+C pour arrêter\n")
	time.sleep(1)
	def make_stats_table():
		t = Table(box=None, show_header=False, padding=(0, 2))
		t.add_column("Clé",	style="cyan")
		t.add_column("Valeur", style="bold white")
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
					title="[bold cyan]  Moniteur Système",
					border_style="cyan",
					padding=(1, 2),
				)
				live.update(panel)
				time.sleep(0.5)
	except KeyboardInterrupt:
		pass
	console.print("\n[green]✓ Dashboard fermé.[/]\n")
	time.sleep(0.3)

def main():
	splash_screen()

	while True:
		choix = questionary.select(
			"Que voulez-vous voir ?",
			choices=[
				"📊  Barre de chargement simple",
				"🔄  Multi-barres en parallèle",
				"📋  Tableau formaté",
				"🖥️   Dashboard en temps réel",
				"🚪  Quitter",
			],
			style=questionary.Style([
				("selected",		"fg:cyan bold"),
				("pointer",		 "fg:cyan bold"),
				("highlighted",	 "fg:cyan"),
				("answer",		  "fg:green bold"),
				("question",		"bold"),
			])
		).ask()
		if choix is None or "Quitter" in choix:
			console.print("\n[bold yellow]Au revoir ! 👋[/]\n")
			break
		console.print()
		if "simple" in choix:
			demo_barre_simple()
		elif "parallèle" in choix:
			demo_multi_barres()
		elif "Tableau" in choix:
			demo_tableau()
		elif "Dashboard" in choix:
			demo_dashboard()
		input("\n  [ Appuyez sur Entrée pour revenir au menu... ]")
		console.clear()
		splash_screen()

if __name__ == "__main__":
	main()
