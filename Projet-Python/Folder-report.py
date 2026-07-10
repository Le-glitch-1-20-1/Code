#!/usr/bin/env python3
"""Scan disk partitions and generate an HTML file report using Template/."""
from __future__		import annotations
import argparse
import gzip
import io
import json
import os
import shutil
import sys
import psutil
import questionary
from abc			import ABC, abstractmethod
from datetime		import datetime
from typing			import Any
from rich.console	import Console
from rich.panel		import Panel
from rich.progress	import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn
from rich.rule		import Rule
from rich.table		import Table

if sys.stdout.encoding.lower() != "utf-8":
	sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

console: Console = Console()

VERSION: str = "2.0.0"

ANSI_COLORS: dict[str, str] = {"red": "31", "green": "32", "yellow": "33", "blue": "34", "magenta": "35", "cyan": "36", "white": "37", "bold": "1"}

MENU_STYLE: questionary.Style = questionary.Style([("selected", "fg:cyan bold"), ("pointer", "fg:cyan bold"), ("highlighted", "fg:cyan"), ("answer", "fg:green bold"), ("question", "bold")])

TEMPLATE_DIR: str = os.path.join("Template", "file-report")
TEMPLATE_HTML_PATH: str = os.path.join(TEMPLATE_DIR, "file-report.html")

TEXTS: dict[str, dict[str, str]] = {
	"en": {
		"scanning": "Scanning",
		"folders": "folders",
		"title": "All-Files Report Generator",
		"report_generated": "Report generated",
		"compressed": "Compressed version",
		"errors_encountered": "Errors encountered",
		"errors_suffix": "errors",
		"errors_file": "errors-report.txt",
		"errors_header": "=== Error Report ===",
		"generated_on": "Generated on",
		"total_errors": "Total number of errors",
		"access_denied_folder": "Access denied to a folder in",
		"path_not_found": "Path not found",
		"error_folder": "Error while processing folder",
		"access_denied_partition": "Access denied to partition",
		"error_partition": "Error while processing partition",
		"template_missing": "Error: HTML template file",
		"default_output": "result.html",
	},
	"fr": {
		"scanning": "Analyse de",
		"folders": "dossiers",
		"title": "Générateur de Rapport de Tous les Fichiers",
		"report_generated": "Rapport généré",
		"compressed": "Version compressée",
		"errors_encountered": "Erreurs rencontrées",
		"errors_suffix": "erreurs",
		"errors_file": "errors-report.txt",
		"errors_header": "=== Rapport d'erreurs ===",
		"generated_on": "Généré le",
		"total_errors": "Nombre total d'erreurs",
		"access_denied_folder": "Accès refusé à un dossier dans",
		"path_not_found": "Le chemin d'accès est introuvable",
		"error_folder": "Erreur lors du traitement du dossier",
		"access_denied_partition": "Accès refusé à la partition",
		"error_partition": "Erreur lors du traitement de la partition",
		"template_missing": "Erreur : le fichier template HTML",
		"default_output": "Resultat.html",
	},
}

# ── Aide visuelle (Rich / Questionary, même style que Interface.py) ─────────
def colorize(text: str, color: str) -> str:
	# Encadre le texte avec les codes ANSI de la couleur demandée
	code: str = ANSI_COLORS.get(color, "0")
	return f"\033[{code}m{text}\033[0m"

def splash_screen() -> None:
	# Efface la console et affiche le panneau de bienvenue
	console.clear()
	console.print()
	console.print(Panel(f"[bold cyan]Folder Report Generator v{VERSION}[/]\n[dim]Génère un rapport HTML de tous les fichiers des partitions[/]", border_style="cyan", padding=(1, 8)))
	console.print()

class ReportGeneratorInterface(ABC):
	# Abstract interface defining the contract every report generator must follow
	@abstractmethod
	def scan(self, extensions: list[str]) -> tuple[dict[str, Any], list[str]]:
		...

	@abstractmethod
	def build_html(self, results: dict[str, Any]) -> str | None:
		...

	@abstractmethod
	def write_report(self, html: str, output_path: str) -> None:
		...

	@abstractmethod
	def write_errors(self, errors: list[str], output_dir: str) -> None:
		...

	@abstractmethod
	def run(self, extensions: list[str], output_path: str) -> None:
		...

class FolderReportGenerator(ReportGeneratorInterface):
	# Concrete implementation that scans disk partitions and builds an HTML report
	def __init__(self, lang: str) -> None:
		self.lang: str = lang
		self.texts: dict[str, str] = TEXTS[lang]

	def format_size(self, size_bytes: float) -> tuple[str, str]:
		# Convert a raw byte count into a human readable value and unit
		units: list[str] = ["o", "Ko", "Mo", "Go", "To", "Po"] if self.lang == "fr" else ["B", "KB", "MB", "GB", "TB", "PB"]
		if size_bytes == 0:
			return "0.00", units[0]
		for unit in units:
			if size_bytes < 1024:
				return f"{size_bytes:.2f}", unit
			size_bytes /= 1024
		return f"{size_bytes:.2f}", units[-1]

	def flatten_tree(self, tree: dict[str, Any], path: str = "") -> list[dict[str, str]]:
		# Turn the nested folder tree into a flat list of file rows
		rows: list[dict[str, str]] = []
		for name, content in tree.items():
			if name == "_files":
				for file_name, size in content:
					base_name, ext = os.path.splitext(file_name)
					ext = ext.lstrip(".")
					value, unit = self.format_size(size)
					rows.append({"n": base_name, "e": ext, "t": value, "u": unit, "p": path})
			else:
				sub_path: str = f"{path}/{name}" if path else name
				rows += self.flatten_tree(content, sub_path)
		return rows

	def extract_extensions(self, rows: list[dict[str, str]]) -> list[str]:
		# Collect the sorted set of distinct file extensions present in the rows
		return sorted({item["e"] for item in rows if item["e"]})

	def scan(self, extensions: list[str]) -> tuple[dict[str, Any], list[str]]:
		# Walk every mounted partition and collect files matching the extension filter
		partitions: list[Any] = psutil.disk_partitions(all=False)
		results: dict[str, Any] = {}
		errors: list[str] = []
		for partition in partitions:
			mountpoint: str = partition.mountpoint
			results[mountpoint] = {}
			try:
				total_folders: int = sum(len(dirs) for _, dirs, _ in os.walk(mountpoint, onerror=lambda e: None))
				console.print(f"[cyan]{self.texts['scanning']}[/] {mountpoint:<40} | {total_folders:>10} {self.texts['folders']}")
				for folder, _subfolders, files in os.walk(mountpoint, onerror=lambda e: None):
					try:
						filtered_files: list[tuple[str, int]] = [
							(f, os.path.getsize(os.path.join(folder, f)))
							for f in files
							if not extensions or os.path.splitext(f)[1].lower().lstrip(".") in extensions
						]
						if filtered_files:
							sub_tree: dict[str, Any] = results.setdefault(mountpoint, {})
							sub_paths: list[str] = folder[len(mountpoint):].strip(os.sep).split(os.sep)
							for sub_folder in sub_paths:
								if sub_folder:
									sub_tree = sub_tree.setdefault(sub_folder, {})
							sub_tree["_files"] = filtered_files
					except PermissionError:
						errors.append(f"{self.texts['access_denied_folder']}: {folder}")
					except FileNotFoundError:
						errors.append(f"{self.texts['path_not_found']}: {folder}")
					except Exception as exc:
						errors.append(f"{self.texts['error_folder']} {folder}: {exc}")
			except PermissionError:
				errors.append(f"{self.texts['access_denied_partition']}: {mountpoint}")
			except Exception as exc:
				errors.append(f"{self.texts['error_partition']} {mountpoint}: {exc}")
		return results, errors

	def build_html(self, results: dict[str, Any]) -> str | None:
		# Load the external template and inject the scan results into it
		try:
			with open(TEMPLATE_HTML_PATH, "r", encoding="utf-8") as handle:
				template: str = handle.read()
		except FileNotFoundError:
			console.print(f"[red]{self.texts['template_missing']} '{TEMPLATE_HTML_PATH}'[/]")
			return None
		partitions_data: dict[str, list[dict[str, str]]] = {}
		for mountpoint, content in results.items():
			label: str = f"🖥️ {mountpoint}"
			partitions_data[label] = self.flatten_tree(content)
		all_rows: list[dict[str, str]] = [item for rows in partitions_data.values() for item in rows]
		available_extensions: list[str] = self.extract_extensions(all_rows)
		json_data: str = json.dumps(partitions_data, ensure_ascii=False, separators=(",", ":"))
		extensions_json: str = json.dumps(available_extensions, ensure_ascii=False, separators=(",", ":"))
		html: str = template.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		html = html.replace("{{DATA_JSON}}", json_data)
		html = html.replace("{{EXTENSIONS_JSON}}", extensions_json)
		return html

	def write_report(self, html: str, output_path: str) -> None:
		# Write the HTML report to disk and produce a gzip-compressed copy
		with open(output_path, "w", encoding="utf-8") as handle:
			handle.write(html)
		size_mb: float = os.path.getsize(output_path) / (1024 * 1024)
		console.print(f"\n[green]{self.texts['report_generated']}[/] : {output_path}  ({size_mb:.2f} Mo)")
		gz_path: str = output_path + ".gz"
		with open(output_path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
			shutil.copyfileobj(f_in, f_out)
		size_gz: float = os.path.getsize(gz_path) / (1024 * 1024)
		console.print(f"[dim]{self.texts['compressed']} : {gz_path}  ({size_gz:.2f} Mo)[/]")

	def write_errors(self, errors: list[str], output_dir: str) -> None:
		# Write the collected scan errors to a dedicated text report
		if not errors:
			return
		console.print(f"\n[yellow]{self.texts['errors_encountered']:<40} | {len(errors):>10} {self.texts['errors_suffix']}[/]\n")
		os.makedirs(output_dir, exist_ok=True)
		error_path: str = os.path.join(output_dir, self.texts["errors_file"])
		digits: int = len(str(len(errors)))
		with open(error_path, "w", encoding="utf-8") as handle:
			handle.write(f"{self.texts['errors_header']}\n")
			handle.write(f"{self.texts['generated_on']} : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
			handle.write(f"{self.texts['total_errors']} : {len(errors)}\n\n")
			for index, error in enumerate(errors, 1):
				if ":" in error:
					left, right = error.split(":", 1)
					handle.write(f"{index:0{digits}d}. {left.strip():<40}: {right.strip()}\n")
				else:
					handle.write(f"{index:0{digits}d}. {error}\n")

	def run(self, extensions: list[str], output_path: str) -> None:
		# Orchestrate scanning, HTML generation and error reporting
		console.print(Rule(f"[bold yellow]{self.texts['title']}"))
		console.print()
		results, errors = self.scan(extensions)
		html: str | None = None
		with Progress(SpinnerColumn(), TextColumn("[bold]{task.description}"), BarColumn(bar_width=30), TimeElapsedColumn(), console=console) as progress:
			task: TaskID = progress.add_task("Construction du rapport HTML...", total=2)
			html = self.build_html(results)
			progress.advance(task)
			if html is not None:
				progress.update(task, description="Écriture des fichiers de sortie...")
				self.write_report(html, output_path)
			progress.advance(task)
		self.write_errors(errors, "src")
		if html is None:
			return
		console.print()
		summary: Table = Table(box=None, show_header=False, padding=(0, 2))
		summary.add_column("Champ", style="cyan")
		summary.add_column("Valeur", style="bold white")
		summary.add_row("Langue", self.lang)
		summary.add_row("Extensions", ", ".join(extensions) if extensions else "(toutes)")
		summary.add_row("Rapport", output_path)
		summary.add_row("Rapport compressé", output_path + ".gz")
		summary.add_row("Erreurs", str(len(errors)))
		console.print(Panel(summary, title="[bold green]✓ Rapport généré avec succès", border_style="green"))

# ── Ligne de commande & interface interactive (même style que Interface.py) ─
def build_arg_parser() -> argparse.ArgumentParser:
	# Build the command line argument parser for the report generator
	epilog: str = (
		"Tous les paramètres ci-dessus peuvent aussi être saisis via le formulaire\n"
		"interactif : lance simplement le script sans arguments pour l'ouvrir\n"
		"(ou ajoute -i / --interactive pour le forcer même avec d'autres options)."
	)
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		description="Generate an HTML file report for all mounted partitions, using Template/.",
		epilog=epilog,
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}", help="Affiche la version du programme et quitte.")
	parser.add_argument("-l", "--lang", choices=["en", "fr"], default="fr", help="output language for console messages and file names")
	parser.add_argument("-e", "--extensions", nargs="*", default=[], help="list of file extensions to include, e.g. -e pdf jpg png")
	parser.add_argument("-o", "--output", default=None, help="path of the generated HTML report")
	parser.add_argument("-i", "--interactive", action="store_true", help="Force l'ouverture du formulaire interactif même avec d'autres options")
	return parser

def interactive_form(defaults: argparse.Namespace) -> argparse.Namespace:
	# Formulaire interactif exposant tous les paramètres parseables, dans le même
	# style que FormDemo de Interface.py (questionary + résumé Rich en Panel)
	console.print(Rule("[bold yellow]Configuration du rapport"))
	console.print()

	lang_label: str | None = questionary.select(
		"Langue des messages / Output language :",
		choices=["Français", "English"],
		default="Français" if defaults.lang == "fr" else "English",
		style=MENU_STYLE,
	).ask()
	if lang_label is None:
		console.print(colorize("Annulé.", "yellow"))
		sys.exit(0)
	lang: str = "fr" if lang_label == "Français" else "en"

	ext_text: str | None = questionary.text(
		"Extensions à inclure (séparées par des virgules, vide = toutes) :",
		default=", ".join(defaults.extensions),
		style=MENU_STYLE,
	).ask()
	if ext_text is None:
		console.print(colorize("Annulé.", "yellow"))
		sys.exit(0)
	extensions: list[str] = [e.strip().lower().lstrip(".") for e in ext_text.split(",") if e.strip()]

	default_output: str = defaults.output or TEXTS[lang]["default_output"]
	output: str | None = questionary.text(
		"Fichier de sortie :",
		default=default_output,
		style=MENU_STYLE,
	).ask()
	if output is None:
		console.print(colorize("Annulé.", "yellow"))
		sys.exit(0)

	console.print()
	summary: Table = Table(box=None, show_header=False, padding=(0, 2))
	summary.add_column("Paramètre", style="cyan")
	summary.add_column("Valeur", style="bold white")
	summary.add_row("Langue", lang)
	summary.add_row("Extensions", ", ".join(extensions) if extensions else "(toutes)")
	summary.add_row("Fichier de sortie", output)
	console.print(Panel(summary, title="[bold cyan]Résumé de la configuration", border_style="cyan"))
	console.print()

	confirmed: bool | None = questionary.confirm("Lancer l'analyse avec ces paramètres ?", default=True).ask()
	if not confirmed:
		console.print(colorize("Annulé.", "yellow"))
		sys.exit(0)

	defaults.lang = lang
	defaults.extensions = extensions
	defaults.output = output
	return defaults

def parse_args() -> argparse.Namespace:
	parser: argparse.ArgumentParser = build_arg_parser()
	args: argparse.Namespace = parser.parse_args()

	# Sans aucun argument (ou avec -i/--interactive), on ouvre le formulaire complet
	# exposant tous les paramètres — même logique que le menu de Interface.py
	# lorsqu'aucune démo n'est passée en argument direct via -d.
	if args.interactive or len(sys.argv) == 1:
		splash_screen()
		args = interactive_form(args)
	else:
		splash_screen()

	return args

def main() -> None:
	# Parse arguments and run the report generator
	args: argparse.Namespace = parse_args()
	extensions: list[str] = [ext.lower().lstrip(".") for ext in args.extensions]
	generator: FolderReportGenerator = FolderReportGenerator(args.lang)
	output_path: str = args.output if args.output else generator.texts["default_output"]
	generator.run(extensions, output_path)

main()
