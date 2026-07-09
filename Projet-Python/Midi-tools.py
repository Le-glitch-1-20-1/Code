#!/usr/bin/env python3
"""Outils MIDI (monitor + test couleurs APC) structurés autour d'une interface commune."""
from __future__ import annotations
import argparse
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
import mido
import questionary
import rtmidi
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TaskID, TextColumn, TimeElapsedColumn

console: Console = Console()
VERSION: str = "1.0.0"
MENU_STYLE: questionary.Style = questionary.Style([
	("selected", "fg:cyan bold"),
	("pointer", "fg:cyan bold"),
	("highlighted", "fg:cyan"),
	("answer", "fg:green bold"),
	("question", "bold"),
])

class MidiTool(ABC):
	# Interface commune que doit respecter tout outil MIDI du programme
	@abstractmethod
	def run(self) -> None:
		# Point d'entree de l'outil
		raise NotImplementedError

class MidiMonitor(MidiTool):
	# Écoute tous les ports MIDI d'entrée disponibles et affiche chaque message reçu
	def __init__(self) -> None:
		self.stop_event: threading.Event = threading.Event()
		self.threads: list[threading.Thread] = []

	def listen_port(self, port_name: str) -> None:
		# Ouvre un port MIDI et affiche chaque message reçu jusqu'à l'arrêt
		try:
			with mido.open_input(port_name) as inport:
				print(f"[+] Listening started on: {port_name}")
				msg: mido.Message
				while not self.stop_event.is_set():
					for msg in inport.iter_pending():
						timestamp: str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
						print(f"[{timestamp}] {port_name:<25} -> {msg}")
					time.sleep(0.001)
		except Exception as e:
			print(f"[!] Error on port '{port_name}': {e}")

	def run(self) -> None:
		# Point d'entree de l'outil "monitor"
		ports: list[str] = mido.get_input_names()
		if not ports:
			print("No MIDI input port detected.")
			print("Check that a MIDI device is properly connected / enabled.")
			return
		print("=== MIDI ports detected ===")
		p: str
		for p in ports:
			print(f"  - {p}")
		print("============================\n")
		port: str
		for port in ports:
			t: threading.Thread = threading.Thread(target=self.listen_port, args=(port,), daemon=True)
			t.start()
			self.threads.append(t)
		print("Listening on all ports. Ctrl+C to stop.\n")
		try:
			while True:
				time.sleep(0.5)
		except KeyboardInterrupt:
			print("\n[!] Stop requested, closing ports...")
			self.stop_event.set()
			for t in self.threads:
				t.join(timeout=1)
			print("Done.")

class ColorTest(MidiTool):
	# Envoie toutes les couleurs (0 à 127) à un pad de l'APC pour tester le rendu couleur
	def __init__(self, note: int, port_substring: str, delay: float) -> None:
		self.note: int = note
		self.port_substring: str = port_substring
		self.delay: float = delay

	def run(self) -> None:
		# Point d'entree de l'outil "colortest"
		midi_out: rtmidi.MidiOut = rtmidi.MidiOut()
		ports: list[str] = midi_out.get_ports()
		idx: int | None = next(
			(i for i, p in enumerate(ports) if self.port_substring in p and "Control" in p),
			None,
		)
		if idx is None:
			print(f"[!] Aucun port trouvé contenant '{self.port_substring}' et 'Control'.")
			print("Ports disponibles :")
			for p in ports:
				print(f"  - {p}")
			return
		midi_out.open_port(idx)
		with Progress(
			TextColumn("[bold blue]Test couleurs"),
			BarColumn(bar_width=40),
			"[progress.percentage]{task.percentage:>3.0f}%",
			TextColumn("{task.fields[color]:>3}/127"),
			TimeElapsedColumn(),
		) as progress:
			task: TaskID = progress.add_task("colortest", total=128, color=0)
			for color in range(128):
				midi_out.send_message([0x90, self.note, color])
				progress.update(task, advance=1, color=color)
				time.sleep(self.delay)

def print_banner() -> None:
	# Efface la console puis affiche le panneau de bienvenue du programme
	console.clear()
	console.print(Panel(
		f"[bold cyan]  MIDI Toolkit v{VERSION}  [/]\n"
		"[dim]Monitor de ports MIDI et test de couleurs APC[/]",
		border_style="cyan",
		padding=(1, 8),
	))

def build_parser() -> argparse.ArgumentParser:
	# Construit le parseur d'arguments en ligne de commande (sous-commande optionnelle)
	parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Outils MIDI (monitor + test couleurs APC)")
	subparsers: argparse._SubParsersAction = parser.add_subparsers(dest="command", required=False)
	subparsers.add_parser("monitor", help="Écoute tous les ports MIDI d'entrée")
	colortest_parser: argparse.ArgumentParser = subparsers.add_parser("colortest", help="Teste les couleurs d'un pad APC")
	colortest_parser.add_argument("--note", type=int, default=33, help="Note MIDI du pad à tester (défaut: 33 = A1/GIMP)")
	colortest_parser.add_argument("--port", type=str, default="APC", help="Sous-chaîne du nom de port à rechercher (défaut: 'APC')")
	colortest_parser.add_argument("--delay", type=float, default=0.5, help="Délai en secondes entre chaque couleur (défaut: 0.5)")
	return parser

def build_tool(args: argparse.Namespace) -> MidiTool:
	# Instancie l'outil MIDI correspondant à la commande demandée
	if args.command == "monitor":
		return MidiMonitor()
	if args.command == "colortest":
		return ColorTest(note=args.note, port_substring=args.port, delay=args.delay)
	raise ValueError(f"Commande inconnue: {args.command}")

def prompt_colortest_params() -> ColorTest:
	# Demande interactivement les paramètres du test de couleurs
	note_str: str | None = questionary.text("Note MIDI du pad à tester ?", default="33").ask()
	port_str: str | None = questionary.text("Sous-chaîne du nom de port ?", default="APC").ask()
	delay_str: str | None = questionary.text("Délai entre chaque couleur (s) ?", default="0.5").ask()
	return ColorTest(note=int(note_str), port_substring=port_str, delay=float(delay_str))

def select_tool_interactively() -> MidiTool | None:
	# Affiche un menu interactif permettant de choisir l'outil MIDI à lancer
	choice: str | None = questionary.select(
		"Que voulez-vous faire ?",
		choices=["Ecouter les ports MIDI (monitor)", "Tester les couleurs d'un pad APC", "Quitter"],
		style=MENU_STYLE,
	).ask()
	if choice is None or choice == "Quitter":
		return None
	if choice.startswith("Ecouter"):
		return MidiMonitor()
	return prompt_colortest_params()

def main() -> None:
	# Point d'entree : parse les arguments, affiche la banniere, choisit l'outil (CLI ou menu interactif), puis le lance
	parser: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = parser.parse_args()
	print_banner()
	tool: MidiTool | None = build_tool(args) if args.command is not None else select_tool_interactively()
	if tool is not None:
		tool.run()

if __name__ == "__main__":
	main()
