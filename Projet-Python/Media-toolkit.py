#!/usr/bin/env python3
from __future__						import annotations
import argparse
import hashlib
import logging
import os
import shutil
import sys
import warnings
import pillow_heif
import questionary
from abc							import ABC, abstractmethod
from collections					import defaultdict
from pathlib						import Path
from types							import SimpleNamespace
from typing							import Optional
from moviepy.video.io.VideoFileClip	import VideoFileClip
from PIL							import Image, UnidentifiedImageError
from rich.console					import Console
from rich.panel						import Panel
from rich.progress					import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table						import Table
from rich.tree						import Tree

console: Console = Console()
VERSION: str = "1.0.0"
ANSI_COLORS: dict[str, str] = {
	"red": "31",
	"green": "32",
	"yellow": "33",
	"cyan": "36",
	"magenta": "35",
	"bold": "1",
}
IMAGE_TARGET_EXTENSIONS: set[str] = {".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif", ".jpeg"}
DUPLICATE_SCAN_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
VIDEO_EXTENSIONS: tuple[str, ...] = (
	".mov", ".mkv", ".avi", ".wmv", ".flv", ".webm",
	".m4v", ".3gp", ".mpg", ".mpeg", ".m2ts", ".mts", ".vob",
)
MENU_CHOICES: list[str] = [
	"Convertir des images en JPEG",
	"Convertir des videos en MP4",
	"Detecter les doublons d'images",
	"Quitter",
]
MENU_STYLE: questionary.Style = questionary.Style([
	("selected", "fg:cyan bold"),
	("pointer", "fg:cyan bold"),
	("highlighted", "fg:cyan"),
	("answer", "fg:green bold"),
	("question", "bold"),
])
logger: logging.Logger = logging.getLogger("media_toolkit")
logger.setLevel(logging.WARNING)
logger.propagate = False
warnings.filterwarnings("ignore", category=UserWarning)
pillow_heif.register_heif_opener()

def colorize(text: str, color: str) -> str:
	# Encadre le texte avec les codes ANSI de la couleur demandee
	code: str = ANSI_COLORS.get(color, "0")
	return f"\033[{code}m{text}\033[0m"

def info(message: str) -> None:
	# Affiche un message normal dans la console
	print(message)

def warn(message: str) -> None:
	# Affiche un avertissement colore et l'ecrit dans le journal de fichier
	print(colorize(f"⚠ {message}", "yellow"))
	logger.warning(message)

def error(message: str) -> None:
	# Affiche une erreur coloree et l'ecrit dans le journal de fichier
	print(colorize(f"✗ {message}", "red"))
	logger.error(message)

def print_banner() -> None:
	# Efface la console puis affiche le panneau de bienvenue du programme
	console.clear()
	console.print(Panel(
		f"[bold cyan]  Media Toolkit v{VERSION}  [/]\n"
		"[dim]Conversion d'images, de videos et detection de doublons[/]",
		border_style="cyan",
		padding=(1, 8),
	))

def resolve_path(raw: str) -> Path:
	# Developpe "~" et resout un chemin brut en chemin absolu
	return Path(raw).expanduser().resolve()

def validate_folder(path: Path) -> None:
	# Quitte le programme si le chemin est manquant, invalide ou illisible
	if not path.exists():
		error(f"Le chemin n'existe pas : '{path}'")
		sys.exit(1)
	if not path.is_dir():
		error(f"Le chemin n'est pas un dossier : '{path}'")
		sys.exit(1)
	if not os.access(path, os.R_OK):
		error(f"Aucune permission de lecture sur : '{path}'")
		sys.exit(1)

def print_summary(prefix: str, counts: dict[str, int]) -> None:
	# Affiche un tableau recapitulatif des resultats
	table: Table = Table(show_header=True, header_style="bold magenta", border_style="bright_black")
	table.add_column("Reussis", justify="center")
	table.add_column("Ignores", justify="center")
	table.add_column("Echecs", justify="center")
	table.add_row(
		colorize(str(counts["success"]), "green"),
		colorize(str(counts["skipped"]), "yellow"),
		colorize(str(counts["error"]), "red" if counts["error"] else "green"),
	)
	if prefix:
		print(prefix)
	console.print(table)

def hash_image(image_path: Path) -> Optional[str]:
	# Calcule un hash MD5 du contenu pixel decode d'une image
	try:
		with Image.open(image_path) as img:
			img_bytes: bytes = img.convert("RGB").tobytes()
		return hashlib.md5(img_bytes).hexdigest()
	except FileNotFoundError:
		warn(f"Fichier introuvable : '{image_path}'")
	except PermissionError:
		warn(f"Permission refusee : '{image_path}'")
	except UnidentifiedImageError:
		warn(f"Format d'image non reconnu : '{image_path.name}'")
	except OSError as e:
		warn(f"Erreur systeme sur '{image_path.name}': {e}")
	except Exception as e:
		warn(f"Erreur inattendue sur '{image_path.name}': {e}")
	return None

def load_hashes(hash_file: Path) -> dict[str, dict[str, str]]:
	# Charge la base de hash d'images depuis le disque, en tolerant les lignes mal formees
	# et les lignes issues d'un ancien format (2 champs : hash|nom_fichier, sans dossier).
	if not hash_file.exists():
		return {}
	hashes: dict[str, dict[str, str]] = defaultdict(dict)
	malformed_count: int = 0
	malformed_examples: list[int] = []
	legacy_count: int = 0
	try:
		with hash_file.open("r", encoding="utf-8") as f:
			for line_num, line in enumerate(f, 1):
				stripped: str = line.strip()
				if not stripped:
					continue
				parts: list[str] = stripped.split("|", 2)
				if len(parts) == 3:
					folder_key, hash_value, file_name = parts
					hashes[folder_key][hash_value] = file_name
				elif len(parts) == 2:
					# Ancien format sans folder_key : on le range en portee globale.
					hash_value, file_name = parts
					hashes["_global_"][hash_value] = file_name
					legacy_count += 1
				else:
					malformed_count += 1
					if len(malformed_examples) < 3:
						malformed_examples.append(line_num)
	except PermissionError:
		warn(f"Impossible de lire le fichier de hash (permission refusee) : '{hash_file}'.")
	except UnicodeDecodeError:
		warn(f"Erreur d'encodage du fichier de hash : '{hash_file}'.")
	except OSError as e:
		warn(f"Erreur systeme en lisant le fichier de hash : {e}.")
	if legacy_count:
		warn(f"{legacy_count} ligne(s) au format d'un ancien fichier de hash, converties en portee globale.")
	if malformed_count:
		examples: str = ", ".join(str(n) for n in malformed_examples)
		suffix: str = "..." if malformed_count > len(malformed_examples) else ""
		warn(f"{malformed_count} ligne(s) mal formee(s) dans le fichier de hash, ignorees (ex. lignes {examples}{suffix}).")
	return hashes

def save_hashes(hashes: dict[str, dict[str, str]], hash_file: Path) -> bool:
	# Sauvegarde la base de hash d'images sur le disque via un fichier temporaire
	tmp_file: Path = hash_file.with_suffix(".tmp")
	try:
		with tmp_file.open("w", encoding="utf-8") as f:
			for folder_key, folder_hashes in hashes.items():
				for hash_value, file_name in folder_hashes.items():
					f.write(f"{folder_key}|{hash_value}|{file_name}\n")
		tmp_file.replace(hash_file)
		return True
	except PermissionError:
		error(f"Permission refusee pour ecrire le fichier de hash : '{hash_file}'.")
	except OSError as e:
		error(f"Erreur systeme en sauvant le fichier de hash : {e}")
	except Exception as e:
		error(f"Erreur inattendue en sauvant le fichier de hash : {e}")
	finally:
		if tmp_file.exists():
			try:
				tmp_file.unlink()
			except OSError:
				pass
	return False

def get_unique_destination(dest_folder: Path, filename: str) -> Path:
	# Construit un chemin de destination sans collision en ajoutant un suffixe numerique
	dest: Path = dest_folder / filename
	if not dest.exists():
		return dest
	stem: str
	suffix: str
	stem, suffix = Path(filename).stem, Path(filename).suffix
	counter: int = 1
	while dest.exists():
		dest = dest_folder / f"{stem}_{counter}{suffix}"
		counter += 1
	return dest

def resolve_copies_dest(file_path: Path, root_folder: Path, copies_folder: Path, flat: bool) -> Path:
	# Calcule le dossier de destination d'un doublon, en miroir sauf si "flat"
	if flat:
		return copies_folder
	try:
		relative: Path = file_path.parent.relative_to(root_folder)
		mirrored: Path = copies_folder / relative
		mirrored.mkdir(parents=True, exist_ok=True)
		return mirrored
	except ValueError:
		warn(f"Impossible de reproduire le chemin pour '{file_path.name}', repli sur flat.")
		return copies_folder
	except PermissionError:
		warn("Permission refusee pour creer le dossier miroir, repli sur flat.")
		return copies_folder
	except OSError as e:
		warn(f"Erreur systeme en creant le dossier miroir : {e}. Repli sur flat.")
		return copies_folder

def safe_move(src: Path, dst: Path) -> bool:
	# Deplace un fichier vers sa destination, journalise et renvoie False en cas d'echec
	try:
		shutil.move(str(src), dst)
		return True
	except PermissionError:
		error(f"Permission refusee pour deplacer '{src.name}'.")
	except shutil.Error as e:
		error(f"Deplacement echoue pour '{src.name}': {e}")
	except OSError as e:
		error(f"Erreur systeme en deplacant '{src.name}': {e}")
	except Exception as e:
		error(f"Erreur inattendue en deplacant '{src.name}': {e}")
	return False

class MediaProcessor(ABC):
	# Interface commune a tout traitement de media du toolkit
	@abstractmethod
	def collect(self, root: Path, recursive: bool) -> list:
		# Recense les fichiers a traiter dans le dossier donne
		raise NotImplementedError

	@abstractmethod
	def run(self, args: argparse.Namespace) -> None:
		# Point d'entree de la sous-commande associee
		raise NotImplementedError

class ImageConverter(MediaProcessor):
	# Convertit les images supportees d'un dossier en JPEG
	def collect(self, root: Path, recursive: bool) -> list[Path]:
		# Parcourt recursivement ou non le dossier a la recherche d'images a convertir
		pattern: str = "**/*" if recursive else "*"
		found: list[Path] = []
		with Progress(SpinnerColumn(), TextColumn("[cyan]Analyse... {task.completed} fichier(s)"), console=console, transient=True) as progress:
			task: int = progress.add_task("scan", total=None)
			for p in root.glob(pattern):
				try:
					if p.is_file() and p.suffix.lower() in IMAGE_TARGET_EXTENSIONS:
						found.append(p)
						progress.advance(task)
				except PermissionError:
					warn(f"Acces refuse : {p}")
				except OSError as e:
					warn(f"Erreur systeme sur {p}: {e}")
		return found

	def convert_one(self, file_path: Path, quality: int, delete_original: bool, dry_run: bool) -> str:
		# Convertit une image unique en JPEG, supprime l'original si demande
		target_path: Path = file_path.with_suffix(".jpg")
		if target_path.exists() and target_path != file_path:
			return "skipped"
		if dry_run:
			return "success"
		try:
			with Image.open(file_path) as img:
				rgb = img.convert("RGB")
				rgb.save(target_path, "JPEG", quality=quality, optimize=True)
			if delete_original and file_path != target_path:
				file_path.unlink()
			return "success"
		except Exception as exc:
			error(f"Echec sur {file_path}: {exc}")
			return "error"

	def run(self, args: argparse.Namespace) -> None:
		# Point d'entree de la sous-commande "images"
		root: Path = resolve_path(args.path)
		validate_folder(root)
		if not (1 <= args.quality <= 95):
			error("La qualite doit etre comprise entre 1 et 95.")
			sys.exit(1)
		files: list[Path] = self.collect(root, args.recursive)
		if not files:
			info("Aucun fichier a convertir dans ce dossier.")
			return
		prefix: str = colorize("[SIMULATION] ", "magenta") if args.dry_run else ""
		info(f"\n{prefix}Traitement de {len(files)} fichier(s)")
		counts: dict[str, int] = {"success": 0, "skipped": 0, "error": 0}
		try:
			with Progress(
				TextColumn("[bold blue]{task.fields[name]:<30}"),
				BarColumn(bar_width=30),
				MofNCompleteColumn(),
				TimeElapsedColumn(),
				console=console,
			) as progress:
				task: int = progress.add_task("images", total=len(files), name="Conversion")
				for file_path in files:
					progress.update(task, name=file_path.name[:30])
					result: str = self.convert_one(file_path, args.quality, args.delete, args.dry_run)
					counts[result] += 1
					progress.advance(task)
		except KeyboardInterrupt:
			info("\nInterruption clavier detectee. Arret.")
		print_summary(prefix, counts)
		if counts["error"]:
			info("Details dans le journal si l'option a ete activee.")

class VideoConverter(MediaProcessor):
	# Convertit les videos supportees d'un dossier en MP4
	def collect(self, root: Path, recursive: bool) -> list[str]:
		# Parcourt recursivement ou non le dossier a la recherche de videos a convertir
		found: list[str] = []
		with Progress(SpinnerColumn(), TextColumn("[cyan]Analyse... {task.completed} fichier(s)"), console=console, transient=True) as progress:
			task: int = progress.add_task("scan", total=None)
			if recursive:
				for dirpath, _, files in os.walk(root):
					for filename in files:
						ext: str = os.path.splitext(filename)[1].lower()
						if ext in VIDEO_EXTENSIONS:
							found.append(os.path.join(dirpath, filename))
							progress.advance(task)
			else:
				for filename in os.listdir(root):
					ext = os.path.splitext(filename)[1].lower()
					if ext in VIDEO_EXTENSIONS:
						found.append(os.path.join(root, filename))
						progress.advance(task)
		return found

	def convert_one(self, file_path: str, dry_run: bool, delete_original: bool) -> str:
		# Convertit une video unique en MP4 (H.264 + AAC), supprime l'original si demande
		directory: str = os.path.dirname(file_path)
		name_part: str = os.path.splitext(os.path.basename(file_path))[0]
		target_path: str = os.path.join(directory, f"{name_part}.mp4")
		if os.path.exists(target_path):
			return "skipped"
		if dry_run:
			return "success"
		try:
			with VideoFileClip(file_path) as clip:
				clip.write_videofile(target_path, codec="libx264", audio_codec="aac", logger=None)
			if delete_original:
				os.remove(file_path)
			return "success"
		except Exception as e:
			error(f"Echec sur {file_path}: {e}")
			return "error"

	def run(self, args: argparse.Namespace) -> None:
		# Point d'entree de la sous-commande "videos"
		root: Path = resolve_path(args.path)
		validate_folder(root)
		videos: list[str] = self.collect(root, args.recursive)
		if not videos:
			info("Aucune video trouvee dans ce dossier.")
			return
		prefix: str = colorize("[SIMULATION] ", "magenta") if args.dry_run else ""
		info(f"\n{prefix}Traitement de {len(videos)} video(s)")
		counts: dict[str, int] = {"success": 0, "skipped": 0, "error": 0}
		try:
			with Progress(
				TextColumn("[bold blue]{task.fields[name]:<30}"),
				BarColumn(bar_width=30),
				MofNCompleteColumn(),
				TimeElapsedColumn(),
				console=console,
			) as progress:
				task: int = progress.add_task("videos", total=len(videos), name="Conversion")
				for file_path in videos:
					progress.update(task, name=os.path.basename(file_path)[:30])
					result: str = self.convert_one(file_path, args.dry_run, args.delete)
					counts[result] += 1
					progress.advance(task)
		except KeyboardInterrupt:
			info("\nInterruption clavier detectee. Arret.")
		print_summary(prefix, counts)
		if counts["error"]:
			info("Details dans le journal si l'option a ete activee.")

class DuplicateDetector(MediaProcessor):
	# Detecte les images en double par hash du contenu pixel et les deplace dans "copies/"
	def collect(self, root: Path, recursive: bool) -> list[Path]:
		# Parcourt le dossier a la recherche d'images candidates a la detection de doublons
		found: list[Path] = []
		pattern: str = "**/*" if recursive else "*"
		with Progress(SpinnerColumn(), TextColumn("[cyan]Analyse... {task.completed} fichier(s)"), console=console, transient=True) as progress:
			task: int = progress.add_task("scan", total=None)
			for p in root.glob(pattern):
				try:
					if p.is_file() and p.suffix.lower() in DUPLICATE_SCAN_EXTENSIONS:
						found.append(p)
						progress.advance(task)
				except PermissionError:
					warn(f"Acces refuse : '{p}'")
				except OSError as e:
					warn(f"Erreur systeme sur '{p}': {e}")
		return found

	def detect_and_move(
		self,
		folder_path: Path,
		recursive: bool = False,
		flat: bool = True,
		dry_run: bool = False,
		global_scope: bool = False,
	) -> None:
		# Detecte les images en double (par hash du contenu pixel) et deplace les extras dans "copies/"
		copies_folder: Path = folder_path / "copies"
		try:
			copies_folder.mkdir(exist_ok=True)
		except PermissionError:
			error(f"Impossible de creer le dossier 'copies' : permission refusee dans '{folder_path}'.")
			return
		except OSError as e:
			error(f"Impossible de creer le dossier 'copies' : {e}")
			return
		hash_file: Path = copies_folder / "image_hashes.txt"
		error_log: Path = copies_folder / "errors-report.txt"
		file_handler: Optional[logging.FileHandler] = None
		try:
			error_log.write_text("", encoding="utf-8")
			file_handler = logging.FileHandler(error_log, encoding="utf-8")
			file_handler.setLevel(logging.WARNING)
			logger.addHandler(file_handler)
		except PermissionError:
			warn("Impossible d'ecrire le journal d'erreurs (permission refusee).")
		except OSError as e:
			warn(f"Impossible de creer le journal d'erreurs : {e}.")
		hashes: dict[str, dict[str, str]] = defaultdict(dict, load_hashes(hash_file))
		try:
			info("Recherche des fichiers image...")
			files: list[Path] = []
			pattern: str = "**/*" if recursive else "*"
			try:
				with Progress(SpinnerColumn(), TextColumn("[cyan]Analyse... {task.completed} fichier(s)"), console=console, transient=True) as progress:
					task: int = progress.add_task("scan", total=None)
					for p in folder_path.glob(pattern):
						try:
							if (
								p.is_file()
								and p.suffix.lower() in DUPLICATE_SCAN_EXTENSIONS
								and copies_folder not in p.parents
								and p.parent != copies_folder
							):
								files.append(p)
								progress.advance(task)
						except PermissionError:
							warn(f"Acces refuse : '{p}'")
						except OSError as e:
							warn(f"Erreur systeme sur '{p}': {e}")
			except PermissionError:
				error(f"Impossible de lister le dossier '{folder_path}' : permission refusee.")
			except OSError as e:
				error(f"Erreur systeme en parcourant le dossier : {e}")
			if not files:
				info("Aucun fichier image trouve.")
				return
			mode_label: str = "recursif" if recursive else "dossier racine uniquement"
			dest_label: str = "flat" if flat else "structure miroir"
			scope_label: str = "global (tous dossiers)" if global_scope else "par dossier"
			prefix: str = colorize("[SIMULATION] ", "magenta") if dry_run else ""
			info(
				f"\n{prefix}Traitement de {len(files)} image(s) "
				f"[mode: {mode_label} | copies: {dest_label} | detection: {scope_label}]"
			)
			counts: dict[str, int] = {"success": 0, "skipped": 0, "error": 0}
			moved_details: list[str] = []
			with Progress(
				TextColumn("[bold blue]{task.fields[name]:<30}"),
				BarColumn(bar_width=30),
				MofNCompleteColumn(),
				TimeElapsedColumn(),
				console=console,
			) as progress:
				task = progress.add_task("dup", total=len(files), name="Analyse")
				for file_path in files:
					progress.update(task, name=file_path.name[:30])
					image_hash: Optional[str] = hash_image(file_path)
					if image_hash is None:
						counts["error"] += 1
						progress.advance(task)
						continue
					folder_key: str = "_global_" if global_scope else str(file_path.parent.relative_to(folder_path))
					folder_hashes: dict[str, str] = hashes[folder_key]
					if image_hash in folder_hashes:
						dest_dir: Path = resolve_copies_dest(file_path, folder_path, copies_folder, flat)
						dest: Path = get_unique_destination(dest_dir, file_path.name)
						rel_src: Path = file_path.relative_to(folder_path)
						rel_dst: Path = dest.relative_to(folder_path)
						original: str = folder_hashes[image_hash]
						if not dry_run:
							if safe_move(file_path, dest):
								counts["success"] += 1
								moved_details.append(f"{rel_src} -> {rel_dst}  (original: {original})")
							else:
								counts["error"] += 1
						else:
							counts["success"] += 1
							moved_details.append(f"{rel_src} -> {rel_dst}  (original: {original})")
					else:
						folder_hashes[image_hash] = file_path.name
						counts["skipped"] += 1
					progress.advance(task)
			if not dry_run:
				if not save_hashes(hashes, hash_file):
					warn("Le fichier de hash n'a pas pu etre sauvegarde. Progres possiblement perdu.")
			if moved_details:
				action: str = "detecte(s)" if dry_run else "deplace(s)"
				info(colorize(f"\n{prefix}{len(moved_details)} doublon(s) {action} :", "cyan"))
				for f in moved_details:
					info(f"  - {f}")
			print_summary(prefix, counts)
			if counts["error"]:
				info(f"Details : {error_log}")
			info(colorize("Termine.", "green"))
		except KeyboardInterrupt:
			info("\nInterruption clavier detectee. Sauvegarde des hash...")
			if not dry_run:
				save_hashes(hashes, hash_file)
			info("Hash sauvegardes. Sortie propre.")
		except Exception as e:
			error(f"\nErreur fatale inattendue : {e}")
			if not dry_run:
				info("Tentative de sauvegarde des hash avant de quitter...")
				save_hashes(hashes, hash_file)
			raise
		finally:
			if file_handler:
				logger.removeHandler(file_handler)
				try:
					file_handler.close()
				except Exception:
					pass

	def run(self, args: argparse.Namespace) -> None:
		# Point d'entree de la sous-commande "duplicates"
		folder_path: Path = resolve_path(args.path)
		validate_folder(folder_path)
		self.detect_and_move(
			folder_path,
			recursive=args.recursive,
			flat=args.flat,
			dry_run=args.dry_run,
			global_scope=args.global_scope,
		)

IMAGE_CONVERTER: ImageConverter = ImageConverter()
VIDEO_CONVERTER: VideoConverter = VideoConverter()
DUPLICATE_DETECTOR: DuplicateDetector = DuplicateDetector()

def run_images_interactive() -> None:
	# Recueille les options de conversion d'images via des invites graphiques
	path: Optional[str] = questionary.text("Chemin du dossier a traiter :", style=MENU_STYLE).ask()
	quality_raw: Optional[str] = questionary.text("Qualite JPEG, 1-95 [95] :", style=MENU_STYLE).ask()
	quality: int
	try:
		quality = int(quality_raw) if quality_raw else 95
	except ValueError:
		quality = 95
	recursive: Optional[bool] = questionary.confirm("Analyser aussi les sous-dossiers ?", default=True, style=MENU_STYLE).ask()
	delete: Optional[bool] = questionary.confirm("Supprimer les originaux apres conversion ?", default=False, style=MENU_STYLE).ask()
	dry_run: Optional[bool] = questionary.confirm("Simuler sans convertir aucun fichier ?", default=False, style=MENU_STYLE).ask()
	IMAGE_CONVERTER.run(SimpleNamespace(path=path, quality=quality, recursive=recursive, delete=delete, dry_run=dry_run))

def run_videos_interactive() -> None:
	# Recueille les options de conversion de videos via des invites graphiques
	path: Optional[str] = questionary.text("Chemin du dossier a traiter :", style=MENU_STYLE).ask()
	recursive: Optional[bool] = questionary.confirm("Analyser aussi les sous-dossiers ?", default=True, style=MENU_STYLE).ask()
	delete: Optional[bool] = questionary.confirm("Supprimer les originaux apres conversion ?", default=False, style=MENU_STYLE).ask()
	dry_run: Optional[bool] = questionary.confirm("Simuler sans convertir aucun fichier ?", default=False, style=MENU_STYLE).ask()
	VIDEO_CONVERTER.run(SimpleNamespace(path=path, recursive=recursive, delete=delete, dry_run=dry_run))

def show_flat_vs_mirror_trees() -> None:
	# Illustre visuellement, via deux arborescences, la difference entre
	# le rangement "a plat" et le rangement "en miroir" des doublons.
	console.print(colorize("Exemple : des doublons trouves ici...", "cyan"))
	source: Tree = Tree("[bold]photos/[/]")
	vacances: Tree = source.add("[bold]vacances/[/]")
	vacances.add("plage.jpg")
	famille: Tree = source.add("[bold]famille/[/]")
	famille.add("noel.jpg")
	console.print(source)
	console.print()
	flat_tree: Tree = Tree("[bold]copies/[/]  [dim](a plat)[/]")
	flat_tree.add("plage.jpg")
	flat_tree.add("noel.jpg")
	mirror_tree: Tree = Tree("[bold]copies/[/]  [dim](en miroir)[/]")
	m_vacances: Tree = mirror_tree.add("[bold]vacances/[/]")
	m_vacances.add("plage.jpg")
	m_famille: Tree = mirror_tree.add("[bold]famille/[/]")
	m_famille.add("noel.jpg")
	console.print(colorize("...seront ranges comme ceci :", "cyan"))
	console.print(flat_tree)
	console.print()
	console.print(mirror_tree)
	console.print()

def run_duplicates_interactive() -> None:
	# Recueille les options de detection de doublons via des invites graphiques
	path: Optional[str] = questionary.text("Chemin du dossier a analyser :", style=MENU_STYLE).ask()
	recursive: Optional[bool] = questionary.confirm("Analyser aussi les sous-dossiers ?", default=False, style=MENU_STYLE).ask()
	show_flat_vs_mirror_trees()
	flat: Optional[bool] = questionary.confirm(
		"Deplacer les doublons a plat (un seul dossier 'copies/') plutot qu'en miroir (sous-dossiers reproduits) ?",
		default=True,
		style=MENU_STYLE,
	).ask()
	global_scope: Optional[bool] = questionary.confirm("Detecter les doublons sur tous les dossiers a la fois ?", default=False, style=MENU_STYLE).ask()
	dry_run: Optional[bool] = questionary.confirm("Simuler sans deplacer aucun fichier ?", default=False, style=MENU_STYLE).ask()
	DUPLICATE_DETECTOR.run(SimpleNamespace(path=path, recursive=recursive, flat=flat, global_scope=global_scope, dry_run=dry_run))

def run_interactive_menu() -> None:
	# Menu interactif affiche quand le script est lance sans sous-commande
	choice: Optional[str] = questionary.select("Que voulez-vous faire ?", choices=MENU_CHOICES, style=MENU_STYLE).ask()
	if choice is None or "Quitter" in choice:
		info(colorize("A bientot !", "green"))
		sys.exit(0)
	console.print()
	if "doublons" in choice:
		run_duplicates_interactive()
	elif "images" in choice:
		run_images_interactive()
	elif "videos" in choice:
		run_videos_interactive()

def build_parser() -> argparse.ArgumentParser:
	# Construit le CLI argparse : options globales et sous-commandes images/videos/duplicates
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		prog="media_toolkit.py",
		description="Convertit des images en JPEG, des videos en MP4, ou detecte/deplace les doublons d'images.",
		epilog=(
			"Exemples :\n"
			"  media_toolkit.py images /chemin/du/dossier\n"
			"  media_toolkit.py videos /chemin/du/dossier --no-recursive\n"
			"  media_toolkit.py duplicates /chemin/du/dossier --recursive --dry-run\n"
		),
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}", help="Affiche la version du programme et quitte.")
	subparsers = parser.add_subparsers(dest="command", required=False, metavar="{images,videos,duplicates}")
	images_parser: argparse.ArgumentParser = subparsers.add_parser(
		"images",
		help="Convertit les images (PNG, WEBP, BMP, TIFF, HEIC/HEIF, ...) en JPEG.",
		description="Convertit chaque image supportee d'un dossier au format JPEG.",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	)
	images_parser.add_argument("path", help="Chemin du dossier a traiter.")
	images_parser.add_argument("--quality", type=int, default=95, metavar="N", help="Qualite JPEG, 1-95.")
	images_parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True, help="Analyse aussi les sous-dossiers.")
	images_parser.add_argument("--delete", action=argparse.BooleanOptionalAction, default=False, help="Supprime les originaux apres conversion.")
	images_parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=False, help="Simule sans convertir aucun fichier.")
	images_parser.set_defaults(func=IMAGE_CONVERTER.run)
	videos_parser: argparse.ArgumentParser = subparsers.add_parser(
		"videos",
		help="Convertit les videos (MOV, MKV, AVI, WMV, ...) en MP4.",
		description="Convertit chaque video supportee d'un dossier en MP4 (H.264 + AAC).",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	)
	videos_parser.add_argument("path", help="Chemin du dossier a traiter.")
	videos_parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True, help="Analyse aussi les sous-dossiers.")
	videos_parser.add_argument("--delete", action=argparse.BooleanOptionalAction, default=False, help="Supprime les originaux apres conversion.")
	videos_parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=False, help="Simule sans convertir aucun fichier.")
	videos_parser.set_defaults(func=VIDEO_CONVERTER.run)
	duplicates_parser: argparse.ArgumentParser = subparsers.add_parser(
		"duplicates",
		help="Detecte les images en double et les deplace dans un sous-dossier 'copies'.",
		description="Detecte les images visuellement identiques (hash du contenu pixel) et deplace les extras dans 'copies'.",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	)
	duplicates_parser.add_argument("path", help="Chemin du dossier a analyser.")
	duplicates_parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=False, help="Analyse aussi les sous-dossiers.")
	duplicates_parser.add_argument(
		"--flat",
		action=argparse.BooleanOptionalAction,
		default=True,
		help=(
			"Deplace les doublons a plat, tous regroupes dans 'copies/' (defaut), "
			"plutot qu'en miroir ou 'copies/' reproduit la meme arborescence de "
			"sous-dossiers que celle ou chaque doublon a ete trouve."
		),
	)
	duplicates_parser.add_argument("--global-scope", action=argparse.BooleanOptionalAction, default=False, help="Detecte les doublons sur tous les dossiers a la fois.")
	duplicates_parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=False, help="Simule sans deplacer aucun fichier.")
	duplicates_parser.set_defaults(func=DUPLICATE_DETECTOR.run)
	return parser

def main() -> None:
	# Point d'entree : parse les arguments, affiche la banniere, puis lance la commande choisie
	parser: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = parser.parse_args()
	print_banner()
	if not args.command:
		run_interactive_menu()
		return
	args.func(args)

if __name__ == "__main__":
	main()
