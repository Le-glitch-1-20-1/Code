#!/usr/bin/env python3
from __future__ import annotations
import argparse
import math
import os
import random
import sys
from abc import ABC, abstractmethod
from typing import Optional
import questionary
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

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
DEFAULT_IMAGE_DIR: str = "image"
DEFAULT_OUTPUT_NAME: str = "hidden_message.png"
MAX_ROW_WIDTH: int = 800
SUPPORTED_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp")
# Valeurs de bytes en plus de l'ASCII imprimable autorisees dans un message (tab, newline, carriage return)
ALLOWED_EXTRA_BYTES: tuple[int, ...] = (9, 10, 13)
ALLOWED_RANGE: range = range(32, 127)
LENGTH_HEADER_BITS: int = 32
MAX_MESSAGE_BYTES: int = (2 ** LENGTH_HEADER_BITS) - 1
# Sequences d'echappement litterales que l'utilisateur peut taper, mappees vers le vrai caractere
ESCAPE_SEQUENCES: dict[str, str] = {
	"\\n": "\n",
	"\\t": "\t",
	"\\r": "\r",
}
MENU_CHOICES: list[str] = [
	"Cacher un message dans une image",
	"Reveler un message d'une image",
	"Quitter",
]
MENU_STYLE: questionary.Style = questionary.Style([
	("selected", "fg:cyan bold"),
	("pointer", "fg:cyan bold"),
	("highlighted", "fg:cyan"),
	("answer", "fg:green bold"),
	("question", "bold"),
])

class IStegoTool(ABC):
	# Interface commune a tout outil de steganographie du programme
	@abstractmethod
	def run(self, args: argparse.Namespace) -> None:
		raise NotImplementedError

def colorize(text: str, color: str) -> str:
	# Encadre le texte avec les codes ANSI de la couleur demandee
	code: str = ANSI_COLORS.get(color, "0")
	return f"\033[{code}m{text}\033[0m"

def info(message: str) -> None:
	# Affiche un message normal dans la console
	print(message)

def warn(message: str) -> None:
	# Affiche un avertissement colore
	print(colorize(f"⚠ {message}", "yellow"))

def error(message: str) -> None:
	# Affiche une erreur coloree
	print(colorize(f"✗ {message}", "red"))

def print_banner() -> None:
	# Efface la console puis affiche le panneau de bienvenue du programme
	console.clear()
	console.print(Panel(
		f"[bold cyan]  Steganography Toolkit v{VERSION}  [/]\n"
		"[dim]Cacher et reveler des messages dans des images[/]",
		border_style="cyan",
		padding=(1, 8),
	))

def parity_digit(value: int) -> int:
	# Reduit une valeur de byte a un seul chiffre par somme de chiffres repetee, renvoie sa parite (0/1)
	while value >= 10:
		value = sum(int(digit) for digit in str(value))
	return 0 if value % 2 == 0 else 1

def build_value_pools() -> tuple[list[int], list[int]]:
	# Separe la plage 0-255 en deux ensembles, un par valeur de parite
	even_values: list[int] = [v for v in range(256) if parity_digit(v) == 0]
	odd_values: list[int] = [v for v in range(256) if parity_digit(v) == 1]
	return even_values, odd_values

def nearest_value_with_parity(value: int, target_bit: str) -> int:
	# Trouve la valeur de byte la plus proche de l'originale qui respecte la parite ciblee
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
			raise ValueError("Aucune valeur de byte adaptee trouvee (inattendu).")
		delta += 1

def build_bit_stream(message_bytes: bytes) -> str:
	# Construit le flux de bits complet : en-tete de longueur fixe puis bits du message
	if len(message_bytes) > MAX_MESSAGE_BYTES:
		raise ValueError(f"Message trop long (max {MAX_MESSAGE_BYTES} bytes).")
	header_bits: str = format(len(message_bytes), f"0{LENGTH_HEADER_BITS}b")
	message_bits: str = "".join(f"{byte:08b}" for byte in message_bytes)
	return header_bits + message_bits

def interpret_escapes(raw_message: str) -> str:
	# Remplace les "\n", "\t", "\r" litteraux tapes par l'utilisateur par les vrais caracteres
	message: str = raw_message
	literal: str
	real_char: str
	for literal, real_char in ESCAPE_SEQUENCES.items():
		message = message.replace(literal, real_char)
	return message

def validate_message(message: str) -> bytes:
	# Verifie que le message n'utilise que des caracteres decodables plus tard, puis l'encode
	if not message:
		raise ValueError("Le message est vide.")
	invalid_chars: list[str] = sorted({
		c for c in message
		if ord(c) not in ALLOWED_RANGE and ord(c) not in ALLOWED_EXTRA_BYTES
	})
	if invalid_chars:
		raise ValueError(
			"Le message contient des caracteres qui ne pourront pas etre decodes ensuite : "
			f"{invalid_chars}. Seul l'ASCII imprimable, la tabulation et le retour a la ligne sont supportes."
		)
	return message.encode("ascii")

def choose_dimensions(pixel_count_needed: int) -> tuple[int, int]:
	# Choisit la largeur/hauteur d'une nouvelle image pour contenir pixel_count_needed pixels
	if pixel_count_needed <= MAX_ROW_WIDTH:
		return pixel_count_needed, 1
	width: int = MAX_ROW_WIDTH
	height: int = math.ceil(pixel_count_needed / width)
	return width, height

def hide_message(message: str, output_path: str) -> Image.Image:
	# Encode un message dans une image toute neuve ou la parite de chaque canal porte un bit
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
	with Progress(
		TextColumn("[bold blue]Encodage"),
		BarColumn(bar_width=30),
		MofNCompleteColumn(),
		TimeElapsedColumn(),
		console=console,
	) as progress:
		task: int = progress.add_task("hide", total=height)
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
			progress.advance(task)
	os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
	image.save(output_path)
	return image

def hide_message_in_existing_image(message: str, source_path: str, output_path: str) -> dict[str, object]:
	# Encode un message dans une image existante en ajustant chaque canal a la bonne parite
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
			f"Cette image est trop petite : elle a {total_pixels} pixels mais le "
			f"message en necessite au moins {pixel_count_needed}. Utilisez une image "
			f"plus grande ou un message plus court."
		)
	pixels: object = image.load()
	bit_index: int = 0
	channels_changed: int = 0
	max_delta: int = 0
	delta_sum: int = 0
	remaining_pixels: int = pixel_count_needed
	if not output_path.lower().endswith(".png"):
		output_path = os.path.splitext(output_path)[0] + ".png"
	with Progress(
		TextColumn("[bold blue]Encodage"),
		BarColumn(bar_width=30),
		MofNCompleteColumn(),
		TimeElapsedColumn(),
		console=console,
	) as progress:
		task: int = progress.add_task("hide", total=height)
		y: int
		for y in range(height):
			if remaining_pixels <= 0:
				progress.update(task, completed=height)
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
			progress.advance(task)
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
	# Relit l'en-tete de longueur puis les bits du message depuis les parites des canaux
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
	with Progress(
		TextColumn("[bold blue]Decodage"),
		BarColumn(bar_width=30),
		MofNCompleteColumn(),
		TimeElapsedColumn(),
		console=console,
		transient=True,
	) as progress:
		task: int = progress.add_task("reveal", total=height)
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
			progress.advance(task)
	raise ValueError(
		"Impossible de lire completement un message cache dans cette image "
		"(elle n'en contient peut-etre pas, ou l'image est trop petite/corrompue)."
	)

def list_images(image_dir: str) -> list[str]:
	# Liste les fichiers image supportes presents dans le dossier donne
	if not os.path.isdir(image_dir):
		return []
	return sorted(f for f in os.listdir(image_dir) if f.lower().endswith(SUPPORTED_EXTENSIONS))

def pick_image_interactive(prompt: str, image_dir: str) -> Optional[str]:
	# Demande a l'utilisateur de choisir une image parmi celles du dossier donne
	images: list[str] = list_images(image_dir)
	if not images:
		error(f"Aucune image trouvee dans '{image_dir}/'. Placez-y une image d'abord.")
		return None
	choice: Optional[str] = questionary.select(prompt, choices=images, style=MENU_STYLE).ask()
	if choice is None:
		return None
	return os.path.join(image_dir, choice)

def run_hide_flow(image_dir: str) -> None:
	# Flux interactif : cache un message dans une image neuve ou existante, puis auto-verifie le resultat
	sub_choice: Optional[str] = questionary.select(
		"Ou cacher le message ?",
		choices=["Dans une image toute neuve", "Dans une image existante (garde son apparence)"],
		style=MENU_STYLE,
	).ask()
	if sub_choice is None:
		return
	raw_message: Optional[str] = questionary.text("Message a cacher (\\n, \\t, \\r sont supportes) :", style=MENU_STYLE).ask()
	if raw_message is None:
		return
	message: str = interpret_escapes(raw_message)
	output_path: str = os.path.join(image_dir, DEFAULT_OUTPUT_NAME)
	recovered: str
	if "existante" in sub_choice:
		source_path: Optional[str] = pick_image_interactive("Choisissez l'image dans laquelle cacher le message :", image_dir)
		if source_path is None:
			return
		stats: dict[str, object]
		try:
			stats = hide_message_in_existing_image(message, source_path, output_path)
		except (ValueError, OSError) as exc:
			error(str(exc))
			return
		info(f"\nMessage cache dans '{source_path}' -> sauvegarde sous '{stats['output_path']}'")
		info(f"Taille de l'image : {stats['width']}x{stats['height']} "
			f"({stats['pixels_used']}/{stats['total_pixels']} pixels touches)")
		info(f"Canaux modifies : {stats['channels_changed']}/{stats['channels_touched_total']} "
			f"(changement moyen : {stats['avg_delta']:.2f}, max : {stats['max_delta']}) — "
			f"visuellement indissociable de l'original.")
		recovered = reveal_message(str(stats["output_path"]))
	else:
		image: Image.Image
		try:
			image = hide_message(message, output_path)
		except ValueError as exc:
			error(str(exc))
			return
		except OSError as exc:
			error(f"Erreur lors de la sauvegarde de l'image : {exc}")
			return
		info(f"\nMessage cache dans une image {image.size[0]}x{image.size[1]}.")
		info(f"Sauvegarde sous : {output_path}")
		recovered = reveal_message(output_path)
	if recovered == message:
		info(colorize("Auto-verification reussie : le message peut etre recupere depuis cette image.", "green"))
	else:
		warn("L'auto-verification a echoue, le message n'a pas ete correctement recupere.")

def run_reveal_flow(image_dir: str) -> None:
	# Flux interactif : revele un message depuis une image choisie parmi celles du dossier donne
	image_path: Optional[str] = pick_image_interactive("Choisissez l'image a analyser :", image_dir)
	if image_path is None:
		return
	message: str
	try:
		message = reveal_message(image_path)
	except (OSError, ValueError) as exc:
		error(f"Erreur en lisant '{image_path}' : {exc}")
		return
	info(f"\nMessage cache :\n{message}")

def run_interactive_menu(image_dir: str) -> None:
	# Menu interactif affiche quand le script est lance sans sous-commande
	while True:
		choice: Optional[str] = questionary.select("Que voulez-vous faire ?", choices=MENU_CHOICES, style=MENU_STYLE).ask()
		if choice is None or "Quitter" in choice:
			info(colorize("A bientot !", "green"))
			return
		console.print()
		if "Cacher" in choice:
			run_hide_flow(image_dir)
		elif "Reveler" in choice:
			run_reveal_flow(image_dir)
		input("\nAppuyez sur Entree pour revenir au menu...")
		print_banner()

class HideTool(IStegoTool):
	# Cache un message dans une image neuve ou existante
	def run(self, args: argparse.Namespace) -> None:
		raw_message: Optional[str] = " ".join(args.message) if args.message else questionary.text("Message a cacher :", style=MENU_STYLE).ask()
		message: str = interpret_escapes(raw_message or "")
		output_path: str = args.output or os.path.join(args.image_dir, DEFAULT_OUTPUT_NAME)
		if args.image:
			stats: dict[str, object]
			try:
				stats = hide_message_in_existing_image(message, args.image, output_path)
			except (ValueError, OSError) as exc:
				error(str(exc))
				sys.exit(1)
			info(f"Sauvegarde sous : {stats['output_path']} ({stats['width']}x{stats['height']}, "
				f"{stats['channels_changed']}/{stats['channels_touched_total']} canaux "
				f"ajustes de {stats['avg_delta']:.2f} en moyenne, max {stats['max_delta']})")
			return
		image: Image.Image
		try:
			image = hide_message(message, output_path)
		except ValueError as exc:
			error(str(exc))
			sys.exit(1)
		info(f"Sauvegarde sous : {output_path} ({image.size[0]}x{image.size[1]})")

class RevealTool(IStegoTool):
	# Revele un message cache dans une image
	def run(self, args: argparse.Namespace) -> None:
		try:
			info(reveal_message(args.image))
		except (OSError, ValueError) as exc:
			error(str(exc))
			sys.exit(1)

HIDE_TOOL: HideTool = HideTool()
REVEAL_TOOL: RevealTool = RevealTool()

def build_parser() -> argparse.ArgumentParser:
	# Construit le CLI argparse : options globales et sous-commandes hide/reveal
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		prog="steganography.py",
		description="Cache ou revele un message texte dans les parites des canaux couleur d'une image.",
		epilog=(
			"Exemples :\n"
			"  steganography.py hide \"mon message secret\"\n"
			"  steganography.py hide \"mon message\" --image photo.png\n"
			"  steganography.py reveal image/hidden_message.png\n"
		),
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}", help="Affiche la version du programme et quitte.")
	parser.add_argument("--image-dir", type=str, default=DEFAULT_IMAGE_DIR, metavar="PATH", help="Dossier utilise pour chercher/enregistrer les images (defaut : image/).")
	subparsers: argparse._SubParsersAction = parser.add_subparsers(dest="command", required=False, metavar="{hide,reveal}")
	hide_parser: argparse.ArgumentParser = subparsers.add_parser(
		"hide",
		help="Cache un message dans une image neuve ou existante.",
		description="Cache un message texte dans les parites des canaux couleur d'une image.",
	)
	hide_parser.add_argument("message", nargs="*", help="Message a cacher (invite si omis).")
	hide_parser.add_argument("--image", metavar="PATH", help="Image existante dans laquelle cacher le message.")
	hide_parser.add_argument("--output", metavar="PATH", help="Chemin de sortie (defaut : <image-dir>/hidden_message.png).")
	hide_parser.set_defaults(func=HIDE_TOOL.run)
	reveal_parser: argparse.ArgumentParser = subparsers.add_parser(
		"reveal",
		help="Revele un message cache dans une image.",
		description="Revele un message texte cache dans les parites des canaux couleur d'une image.",
	)
	reveal_parser.add_argument("image", help="Chemin de l'image a analyser.")
	reveal_parser.set_defaults(func=REVEAL_TOOL.run)
	return parser

def main() -> None:
	# Point d'entree : parse les arguments, affiche la banniere, puis lance la commande choisie
	parser: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = parser.parse_args()
	print_banner()
	if not args.command:
		run_interactive_menu(args.image_dir)
		return
	args.func(args)

if __name__ == "__main__":
	main()
