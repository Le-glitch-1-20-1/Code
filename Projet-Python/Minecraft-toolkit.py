#!/usr/bin/env python3
"""Minecraft world analysis toolkit: map area calculator and dragon egg finder."""
from __future__ import annotations
import argparse
import gzip
import io
import os
import struct
import sys
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

console: Console = Console()
TARGET_EGG: str = "minecraft:dragon_egg"

CONTAINER_TYPES: set[str] = {
	"minecraft:chest",
	"minecraft:trapped_chest",
	"minecraft:barrel",
	"minecraft:shulker_box",
	"minecraft:white_shulker_box",
	"minecraft:light_gray_shulker_box",
	"minecraft:gray_shulker_box",
	"minecraft:black_shulker_box",
	"minecraft:brown_shulker_box",
	"minecraft:red_shulker_box",
	"minecraft:orange_shulker_box",
	"minecraft:yellow_shulker_box",
	"minecraft:lime_shulker_box",
	"minecraft:green_shulker_box",
	"minecraft:cyan_shulker_box",
	"minecraft:light_blue_shulker_box",
	"minecraft:blue_shulker_box",
	"minecraft:purple_shulker_box",
	"minecraft:magenta_shulker_box",
	"minecraft:pink_shulker_box",
	"minecraft:hopper",
	"minecraft:dropper",
	"minecraft:dispenser",
	"minecraft:furnace",
	"minecraft:blast_furnace",
	"minecraft:smoker",
	"minecraft:brewing_stand",
	"minecraft:ender_chest",
	"minecraft:chiseled_bookshelf",
	"minecraft:crafter",
}

DIMS_VANILLA: list[tuple[str, str]] = [
	("Overworld", "region"),
	("Nether", os.path.join("DIM-1", "region")),
	("End", os.path.join("DIM1", "region")),
]
DIMS_PAPER: list[tuple[str, str]] = [
	("Overworld", os.path.join("world", "region")),
	("Nether", os.path.join("world_nether", "DIM-1", "region")),
	("End", os.path.join("world_the_end", "DIM1", "region")),
]
DIM_COLOR: dict[str, str] = {
	"Overworld": "green",
	"Nether": "red",
	"End": "magenta",
}
DIM_ICON: dict[str, str] = {
	"Overworld": "\U0001F30D",
	"Nether": "\U0001F525",
	"End": "\U0001F30C",
}

MENU_CHOICES: list[str] = [
	"Calculer la superficie de la carte",
	"Chercher l'oeuf de dragon",
	"Quitter",
]
MENU_STYLE: questionary.Style = questionary.Style([
	("selected", "fg:cyan bold"),
	("pointer", "fg:cyan bold"),
	("highlighted", "fg:cyan"),
	("answer", "fg:green bold"),
	("question", "bold"),
])

TAG_END: int = 0
TAG_BYTE: int = 1
TAG_SHORT: int = 2
TAG_INT: int = 3
TAG_LONG: int = 4
TAG_FLOAT: int = 5
TAG_DOUBLE: int = 6
TAG_BYTE_ARRAY: int = 7
TAG_STRING: int = 8
TAG_LIST: int = 9
TAG_COMPOUND: int = 10
TAG_INT_ARRAY: int = 11
TAG_LONG_ARRAY: int = 12

@dataclass
class AreaResult:
	# Resultat du scan d'une dimension pour le calcul de superficie
	chunks: int
	blocks: int
	mca_count: int
	min_bx: int
	max_bx: int
	min_bz: int
	max_bz: int
	span_x: int
	span_z: int

@dataclass
class EggBlock:
	# Position d'un oeuf de dragon place comme bloc dans le monde
	dimension: str
	x: int
	y: int
	z: int

@dataclass
class EggContainer:
	# Position d'un oeuf de dragon range dans un conteneur
	dimension: str
	container: str
	x: int
	y: int
	z: int

class MinecraftTool(ABC):
	# Interface commune a tous les outils du toolkit

	@abstractmethod
	def run(self, save_dir: str) -> None:
		raise NotImplementedError

def detect_dims(save_dir: str) -> tuple[list[tuple[str, str]], str]:
	# Detecte si la sauvegarde est de structure Vanilla ou Paper/Spigot
	if os.path.isdir(os.path.join(save_dir, "world")):
		return DIMS_PAPER, "Paper/Spigot"
	if os.path.isdir(os.path.join(save_dir, "region")):
		return DIMS_VANILLA, "Vanilla"
	return DIMS_PAPER, "inconnu"

def fmt_big(n: int) -> str:
	# Formate un grand nombre avec un separateur espace
	return f"{n:,}".replace(",", " ")

def bar(ratio: float, width: int = 30) -> str:
	# Construit une barre de progression ASCII
	filled: int = round(ratio * width)
	return "\u2588" * filled + "\u2591" * (width - filled)

def read_fmt(buf: io.BytesIO, fmt: str) -> int:
	# Lit et decode une valeur binaire selon le format donne
	size: int = struct.calcsize(fmt)
	return struct.unpack(fmt, buf.read(size))[0]

def read_string(buf: io.BytesIO) -> str:
	# Lit une chaine NBT prefixee par sa longueur
	length: int = read_fmt(buf, ">H")
	return buf.read(length).decode("utf-8", errors="replace")

def skip_payload(buf: io.BytesIO, tag_type: int) -> None:
	# Avance dans le buffer sans decoder la valeur du tag
	if tag_type == TAG_BYTE:
		buf.read(1)
	elif tag_type == TAG_SHORT:
		buf.read(2)
	elif tag_type == TAG_INT:
		buf.read(4)
	elif tag_type == TAG_LONG:
		buf.read(8)
	elif tag_type == TAG_FLOAT:
		buf.read(4)
	elif tag_type == TAG_DOUBLE:
		buf.read(8)
	elif tag_type == TAG_BYTE_ARRAY:
		n: int = read_fmt(buf, ">i")
		buf.read(n)
	elif tag_type == TAG_STRING:
		read_string(buf)
	elif tag_type == TAG_LIST:
		elem_type: int = read_fmt(buf, ">b")
		count: int = read_fmt(buf, ">i")
		for _ in range(count):
			skip_payload(buf, elem_type)
	elif tag_type == TAG_COMPOUND:
		while True:
			t: int = read_fmt(buf, ">b")
			if t == TAG_END:
				break
			read_string(buf)
			skip_payload(buf, t)
	elif tag_type == TAG_INT_ARRAY:
		n = read_fmt(buf, ">i")
		buf.read(n * 4)
	elif tag_type == TAG_LONG_ARRAY:
		n = read_fmt(buf, ">i")
		buf.read(n * 8)

def parse_payload(buf: io.BytesIO, tag_type: int) -> object:
	# Decode la valeur d'un tag NBT selon son type
	if tag_type == TAG_BYTE:
		return read_fmt(buf, ">b")
	if tag_type == TAG_SHORT:
		return read_fmt(buf, ">h")
	if tag_type == TAG_INT:
		return read_fmt(buf, ">i")
	if tag_type == TAG_LONG:
		return read_fmt(buf, ">q")
	if tag_type == TAG_FLOAT:
		return read_fmt(buf, ">f")
	if tag_type == TAG_DOUBLE:
		return read_fmt(buf, ">d")
	if tag_type == TAG_BYTE_ARRAY:
		n: int = read_fmt(buf, ">i")
		return buf.read(n)
	if tag_type == TAG_STRING:
		return read_string(buf)
	if tag_type == TAG_LIST:
		elem_type: int = read_fmt(buf, ">b")
		count: int = read_fmt(buf, ">i")
		return [parse_payload(buf, elem_type) for _ in range(count)]
	if tag_type == TAG_COMPOUND:
		return parse_compound(buf)
	if tag_type == TAG_INT_ARRAY:
		n = read_fmt(buf, ">i")
		return list(struct.unpack(f">{n}i", buf.read(n * 4)))
	if tag_type == TAG_LONG_ARRAY:
		n = read_fmt(buf, ">i")
		return list(struct.unpack(f">{n}q", buf.read(n * 8)))
	return None

def parse_compound(buf: io.BytesIO) -> dict[str, object]:
	# Decode un tag composite NBT en dictionnaire Python
	result: dict[str, object] = {}
	while True:
		tag_type: int = read_fmt(buf, ">b")
		if tag_type == TAG_END:
			break
		name: str = read_string(buf)
		result[name] = parse_payload(buf, tag_type)
	return result

def parse_nbt_root(data: bytes) -> dict[str, object]:
	# Decode la racine d'un document NBT deja decompresse
	buf: io.BytesIO = io.BytesIO(data)
	tag_type: int = read_fmt(buf, ">b")
	if tag_type == TAG_END:
		return {}
	read_string(buf)
	payload: object = parse_payload(buf, tag_type)
	return payload if isinstance(payload, dict) else {}

def decode_section(section: dict[str, object]) -> list[str]:
	# Decode la palette et les indices de blocs d'une section de chunk
	block_states: object = section.get("block_states") or section
	if not isinstance(block_states, dict):
		return []
	palette: list[object] = block_states.get("palette") or block_states.get("Palette") or []
	data: Optional[list[int]] = block_states.get("data") or block_states.get("Data")
	if not palette:
		return []
	names: list[str] = []
	entry: object
	for entry in palette:
		name: str = (entry.get("Name") or entry.get("name") or "") if isinstance(entry, dict) else str(entry)
		names.append(name)
	if data is None or len(data) == 0:
		return [names[0]] * 4096
	bits_per_block: int = max(4, (len(palette) - 1).bit_length())
	mask: int = (1 << bits_per_block) - 1
	blocks: list[str] = []
	long_val: int
	for long_val in data:
		if long_val < 0:
			long_val += 1 << 64
		num_per_long: int = 64 // bits_per_block
		i: int
		for i in range(num_per_long):
			idx: int = (long_val >> (i * bits_per_block)) & mask
			blocks.append(names[idx] if idx < len(names) else "minecraft:air")
			if len(blocks) == 4096:
				break
		if len(blocks) >= 4096:
			break
	return blocks[:4096]

def block_index_to_local(index: int) -> tuple[int, int, int]:
	# Convertit un index lineaire de bloc en coordonnees locales x, y, z
	y: int = (index >> 8) & 0xF
	z: int = (index >> 4) & 0xF
	x: int = index & 0xF
	return x, y, z

def iter_chunks(mca_path: str) -> list[bytes]:
	# Extrait et decompresse les donnees NBT de chaque chunk d'un fichier .mca
	chunks: list[bytes] = []
	with open(mca_path, "rb") as f:
		header: bytes = f.read(4096)
		if len(header) < 4096:
			return chunks
		i: int
		for i in range(1024):
			offset_bytes: bytes = header[i * 4:i * 4 + 4]
			offset: int = (offset_bytes[0] << 16) | (offset_bytes[1] << 8) | offset_bytes[2]
			sectors: int = offset_bytes[3]
			if offset == 0 and sectors == 0:
				continue
			f.seek(offset * 4096)
			length: int = struct.unpack(">I", f.read(4))[0]
			comp_type: int = struct.unpack(">B", f.read(1))[0]
			raw: bytes = f.read(length - 1)
			try:
				if comp_type == 2:
					data: bytes = zlib.decompress(raw)
				elif comp_type == 1:
					data = gzip.decompress(raw)
				else:
					data = raw
				chunks.append(data)
			except Exception:
				continue
	return chunks

def search_items_for_egg(items: object) -> bool:
	# Parcourt recursivement une liste d'objets NBT pour trouver l'oeuf de dragon
	if not isinstance(items, list):
		return False
	item: object
	for item in items:
		if not isinstance(item, dict):
			continue
		item_id: str = item.get("id") or item.get("Id") or ""
		if item_id == TARGET_EGG:
			return True
		tag: object = item.get("tag") or item.get("Tag") or {}
		if isinstance(tag, dict):
			sub_be: object = tag.get("BlockEntityTag") or {}
			if isinstance(sub_be, dict):
				sub_items: object = sub_be.get("Items") or sub_be.get("items") or []
				if search_items_for_egg(sub_items):
					return True
			nested_items: object = tag.get("Items") or tag.get("items") or []
			if search_items_for_egg(nested_items):
				return True
		direct: object = item.get("Items") or item.get("items") or []
		if search_items_for_egg(direct):
			return True
	return False

class AreaCalculator(MinecraftTool):
	# Calcule la superficie de chunks generes dans chaque dimension

	def count_chunks_in_mca(self, mca_path: str) -> int:
		# Compte les chunks presents dans un fichier .mca
		count: int = 0
		try:
			with open(mca_path, "rb") as f:
				header: bytes = f.read(4096)
			if len(header) < 4096:
				return 0
			i: int
			for i in range(1024):
				b: bytes = header[i * 4:i * 4 + 4]
				offset: int = (b[0] << 16) | (b[1] << 8) | b[2]
				sectors: int = b[3]
				if offset != 0 or sectors != 0:
					count += 1
		except Exception:
			pass
		return count

	def scan_dimension(self, save_dir: str, rel_path: str) -> Optional[AreaResult]:
		# Scanne une dimension et calcule ses bornes et sa superficie
		region_dir: str = os.path.join(save_dir, rel_path)
		if not os.path.isdir(region_dir):
			return None
		mca_files: list[str] = [f for f in os.listdir(region_dir) if f.endswith(".mca")]
		if not mca_files:
			return None
		total_chunks: int = 0
		min_rx: int = 999999
		min_rz: int = 999999
		max_rx: int = -999999
		max_rz: int = -999999
		mca_file: str
		for mca_file in mca_files:
			parts: list[str] = mca_file.split(".")
			try:
				rx: int = int(parts[1])
				rz: int = int(parts[2])
			except (IndexError, ValueError):
				continue
			min_rx = min(min_rx, rx)
			max_rx = max(max_rx, rx)
			min_rz = min(min_rz, rz)
			max_rz = max(max_rz, rz)
			path: str = os.path.join(region_dir, mca_file)
			total_chunks += self.count_chunks_in_mca(path)
		min_bx: int = min_rx * 32 * 16
		max_bx: int = (max_rx + 1) * 32 * 16 - 1
		min_bz: int = min_rz * 32 * 16
		max_bz: int = (max_rz + 1) * 32 * 16 - 1
		return AreaResult(
			chunks=total_chunks,
			blocks=total_chunks * 16 * 16,
			mca_count=len(mca_files),
			min_bx=min_bx,
			max_bx=max_bx,
			min_bz=min_bz,
			max_bz=max_bz,
			span_x=max_bx - min_bx + 1,
			span_z=max_bz - min_bz + 1,
		)

	def run(self, save_dir: str) -> None:
		# Affiche l'analyse de superficie pour toutes les dimensions trouvees
		dims: list[tuple[str, str]]
		server_type: str
		dims, server_type = detect_dims(save_dir)
		console.print(Rule("[bold yellow]Superficie de la carte[/]"))
		console.print(f"[dim]{save_dir}[/]")
		console.print(f"[dim]Structure detectee : {server_type}[/]\n")
		results: dict[str, AreaResult] = {}
		dim_name: str
		rel_path: str
		for dim_name, rel_path in dims:
			data: Optional[AreaResult] = self.scan_dimension(save_dir, rel_path)
			if data is not None:
				results[dim_name] = data
		if not results:
			console.print("[yellow]Aucune dimension trouvee dans ce dossier.[/]\n")
			return
		max_chunks: int = max(r.chunks for r in results.values()) or 1
		for dim_name, data in results.items():
			color: str = DIM_COLOR.get(dim_name, "cyan")
			icon: str = DIM_ICON.get(dim_name, "")
			ratio: float = data.chunks / max_chunks
			table: Table = Table(box=None, show_header=False, padding=(0, 2))
			table.add_column("Cle", style=color)
			table.add_column("Valeur", style="bold white")
			table.add_row("Fichiers .mca", fmt_big(data.mca_count))
			table.add_row("Chunks generes", fmt_big(data.chunks))
			table.add_row("Superficie", f"{fmt_big(data.blocks)} blocs2 ({data.blocks / 1_000_000:.2f} km2)")
			table.add_row("Emprise X", f"{data.min_bx} -> {data.max_bx}")
			table.add_row("Emprise Z", f"{data.min_bz} -> {data.max_bz}")
			table.add_row("Progression", f"{bar(ratio)} {ratio * 100:.1f}%")
			console.print(Panel(table, title=f"[bold]{icon} {dim_name}[/]", border_style=color))
		total_chunks: int = sum(r.chunks for r in results.values())
		total_blocks: int = sum(r.blocks for r in results.values())
		console.print(Panel(
			f"[bold green]Chunks totaux : {fmt_big(total_chunks)}[/]\n"
			f"[bold green]Superficie totale : {fmt_big(total_blocks)} blocs2 ({total_blocks / 1_000_000:.2f} km2)[/]",
			title="[bold]Total toutes dimensions[/]",
			border_style="green",
		))

class DragonEggFinder(MinecraftTool):
	# Recherche l'oeuf de dragon place en bloc ou range dans un conteneur

	def scan_chunk(self, nbt: dict[str, object], blocks_out: list[EggBlock], containers_out: list[EggContainer], dim_label: str) -> None:
		# Analyse un chunk decode a la recherche de l'oeuf de dragon
		level: object = nbt.get("Level") or nbt
		if not isinstance(level, dict):
			return
		cx: int = level.get("xPos") or level.get("XPos") or 0
		cz: int = level.get("zPos") or level.get("ZPos") or 0
		sections: object = level.get("sections") or level.get("Sections") or []
		section: object
		if isinstance(sections, list):
			for section in sections:
				if not isinstance(section, dict):
					continue
				sy: object = section.get("Y") or section.get("y")
				if sy is None:
					continue
				blocks: list[str] = decode_section(section)
				idx: int
				name: str
				for idx, name in enumerate(blocks):
					if name == TARGET_EGG:
						lx: int
						ly: int
						lz: int
						lx, ly, lz = block_index_to_local(idx)
						blocks_out.append(EggBlock(dim_label, cx * 16 + lx, int(sy) * 16 + ly, cz * 16 + lz))
		be_list: object = level.get("block_entities") or level.get("TileEntities") or level.get("tileEntities") or []
		be: object
		if isinstance(be_list, list):
			for be in be_list:
				if not isinstance(be, dict):
					continue
				be_id: str = be.get("id") or be.get("Id") or ""
				if not be_id.startswith("minecraft:"):
					be_id = "minecraft:" + be_id.lower()
				if be_id not in CONTAINER_TYPES:
					continue
				items: object = be.get("Items") or be.get("items") or []
				if search_items_for_egg(items):
					bx: int = be.get("x") or be.get("X") or 0
					by: int = be.get("y") or be.get("Y") or 0
					bz: int = be.get("z") or be.get("Z") or 0
					containers_out.append(EggContainer(dim_label, be_id.replace("minecraft:", ""), bx, by, bz))

	def scan_region_dir(self, region_dir: str, dim_label: str, blocks_out: list[EggBlock], containers_out: list[EggContainer]) -> None:
		# Scanne tous les fichiers .mca d'un dossier region
		if not os.path.isdir(region_dir):
			return
		mca_files: list[str] = sorted(f for f in os.listdir(region_dir) if f.endswith(".mca"))
		mca_file: str
		for mca_file in mca_files:
			path: str = os.path.join(region_dir, mca_file)
			chunk_data: bytes
			for chunk_data in iter_chunks(path):
				try:
					nbt: dict[str, object] = parse_nbt_root(chunk_data)
					self.scan_chunk(nbt, blocks_out, containers_out, dim_label)
				except Exception:
					continue

	def run(self, save_dir: str) -> None:
		# Affiche les emplacements trouves de l'oeuf de dragon
		dims: list[tuple[str, str]]
		server_type: str
		dims, server_type = detect_dims(save_dir)
		console.print(Rule("[bold magenta]Recherche de l'oeuf de dragon[/]"))
		console.print(f"[dim]Structure detectee : {server_type}[/]\n")
		all_blocks: list[EggBlock] = []
		all_containers: list[EggContainer] = []
		dim_label: str
		rel_path: str
		for dim_label, rel_path in dims:
			region_dir: str = os.path.join(save_dir, rel_path)
			with console.status(f"[cyan]Analyse de {dim_label}...[/]"):
				self.scan_region_dir(region_dir, dim_label, all_blocks, all_containers)
		if not all_blocks and not all_containers:
			console.print("[gold1]Aucun oeuf de dragon trouve dans aucune dimension.[/]\n")
			return
		if all_blocks:
			table_blocks: Table = Table(title="Oeuf de dragon place dans le monde", border_style="magenta")
			table_blocks.add_column("Dimension", style="magenta")
			table_blocks.add_column("X", justify="right")
			table_blocks.add_column("Y", justify="right")
			table_blocks.add_column("Z", justify="right")
			eb: EggBlock
			for eb in sorted(all_blocks, key=lambda r: (r.x, r.z)):
				table_blocks.add_row(eb.dimension, str(eb.x), str(eb.y), str(eb.z))
			console.print(table_blocks)
		if all_containers:
			table_containers: Table = Table(title="Oeuf de dragon dans un conteneur", border_style="gold1")
			table_containers.add_column("Dimension", style="gold1")
			table_containers.add_column("Conteneur")
			table_containers.add_column("X", justify="right")
			table_containers.add_column("Y", justify="right")
			table_containers.add_column("Z", justify="right")
			ec: EggContainer
			for ec in sorted(all_containers, key=lambda r: (r.x, r.z)):
				table_containers.add_row(ec.dimension, ec.container, str(ec.x), str(ec.y), str(ec.z))
			console.print(table_containers)
		total: int = len(all_blocks) + len(all_containers)
		console.print(f"\n[bold green]Total : {total} emplacement(s) trouve(s)[/]\n")

def splash_screen() -> None:
	# Efface la console et affiche la banniere d'accueil
	console.clear()
	console.print()
	console.print(Panel(
		"[bold cyan]  Minecraft Toolkit  [/]\n"
		"[dim]Analyse de sauvegardes Minecraft[/]",
		border_style="cyan",
		padding=(1, 8),
	))
	console.print()

def prompt_save_dir() -> Optional[str]:
	# Demande a l'utilisateur le chemin du dossier de sauvegarde
	path: Optional[str] = questionary.path("Chemin du dossier de sauvegarde :").ask()
	if path is None:
		return None
	path = os.path.expanduser(path)
	if not os.path.isdir(path):
		console.print(f"[red]Erreur : '{path}' n'est pas un dossier valide.[/]")
		return None
	return path

def run_interactive_menu() -> None:
	# Boucle du menu interactif principal
	splash_screen()
	while True:
		choice: Optional[str] = questionary.select(
			"Que veux-tu faire ?", choices=MENU_CHOICES, style=MENU_STYLE
		).ask()
		if choice is None or choice == "Quitter":
			console.print("[yellow]Au revoir ![/]")
			break
		save_dir: Optional[str] = prompt_save_dir()
		if save_dir is not None:
			console.print()
			tool: MinecraftTool = AreaCalculator() if choice == MENU_CHOICES[0] else DragonEggFinder()
			tool.run(save_dir)
		input("\n  [ Appuie sur Entree pour revenir au menu... ]")
		splash_screen()

def parse_args() -> argparse.Namespace:
	# Definit et analyse les arguments de la ligne de commande
	parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Minecraft world analysis toolkit.")
	parser.add_argument("--dir", type=str, default=None, help="Chemin du dossier de sauvegarde")
	parser.add_argument("--mode", type=str, choices=["area", "egg"], default=None, help="Outil a executer directement")
	return parser.parse_args()

def main() -> None:
	# Point d'entree du programme
	args: argparse.Namespace = parse_args()
	if args.dir is not None and args.mode is not None:
		save_dir: str = os.path.expanduser(args.dir)
		if not os.path.isdir(save_dir):
			console.print(f"[red]Erreur : '{save_dir}' n'est pas un dossier valide.[/]")
			sys.exit(1)
		tool: MinecraftTool = AreaCalculator() if args.mode == "area" else DragonEggFinder()
		tool.run(save_dir)
	else:
		run_interactive_menu()

if __name__ == "__main__":
	main()
