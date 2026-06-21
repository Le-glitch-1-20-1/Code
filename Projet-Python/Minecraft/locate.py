#!/usr/bin/env python3
"""
find_shulkers.py
────────────────
Scanne tous les fichiers .mca d'un dossier de région Minecraft
et affiche les coordonnées exactes (X, Y, Z) de chaque shulker box.

Usage :
	python3 find_shulkers.py <chemin/vers/dossier/region>

Exemple :
	python3 find_shulkers.py ~/.minecraft/saves/MonMonde/region
"""

import sys
import os
import struct
import zlib
import io

# ── Tous les types de shulker box ──────────────────────────────────────────
SHULKER_TYPES = {
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
}

# ── Couleurs terminal ───────────────────────────────────────────────────────
COLOR = {
	"minecraft:shulker_box":			"\033[97m",   # blanc
	"minecraft:white_shulker_box":	  "\033[97m",
	"minecraft:light_gray_shulker_box": "\033[37m",
	"minecraft:gray_shulker_box":	   "\033[90m",
	"minecraft:black_shulker_box":	  "\033[90m",
	"minecraft:brown_shulker_box":	  "\033[33m",
	"minecraft:red_shulker_box":		"\033[91m",
	"minecraft:orange_shulker_box":	 "\033[38;5;214m",
	"minecraft:yellow_shulker_box":	 "\033[93m",
	"minecraft:lime_shulker_box":	   "\033[92m",
	"minecraft:green_shulker_box":	  "\033[32m",
	"minecraft:cyan_shulker_box":	   "\033[96m",
	"minecraft:light_blue_shulker_box": "\033[94m",
	"minecraft:blue_shulker_box":	   "\033[34m",
	"minecraft:purple_shulker_box":	 "\033[35m",
	"minecraft:magenta_shulker_box":	"\033[95m",
	"minecraft:pink_shulker_box":	   "\033[38;5;213m",
}
RESET = "\033[0m"
BOLD  = "\033[1m"

# ── Lecture NBT minimale ────────────────────────────────────────────────────
TAG_END		= 0
TAG_BYTE	   = 1
TAG_SHORT	  = 2
TAG_INT		= 3
TAG_LONG	   = 4
TAG_FLOAT	  = 5
TAG_DOUBLE	 = 6
TAG_BYTE_ARRAY = 7
TAG_STRING	 = 8
TAG_LIST	   = 9
TAG_COMPOUND   = 10
TAG_INT_ARRAY  = 11
TAG_LONG_ARRAY = 12

def read_fmt(buf, fmt):
	size = struct.calcsize(fmt)
	return struct.unpack(fmt, buf.read(size))[0]

def read_string(buf):
	length = read_fmt(buf, ">H")
	return buf.read(length).decode("utf-8", errors="replace")

def skip_payload(buf, tag_type):
	"""Saute le payload d'un tag sans le parser entièrement."""
	if tag_type == TAG_BYTE:		buf.read(1)
	elif tag_type == TAG_SHORT:	 buf.read(2)
	elif tag_type == TAG_INT:	   buf.read(4)
	elif tag_type == TAG_LONG:	  buf.read(8)
	elif tag_type == TAG_FLOAT:	 buf.read(4)
	elif tag_type == TAG_DOUBLE:	buf.read(8)
	elif tag_type == TAG_BYTE_ARRAY:
		n = read_fmt(buf, ">i"); buf.read(n)
	elif tag_type == TAG_STRING:
		read_string(buf)
	elif tag_type == TAG_LIST:
		elem_type = read_fmt(buf, ">b")
		count	 = read_fmt(buf, ">i")
		for _ in range(count):
			skip_payload(buf, elem_type)
	elif tag_type == TAG_COMPOUND:
		while True:
			t = read_fmt(buf, ">b")
			if t == TAG_END: break
			read_string(buf)   # nom
			skip_payload(buf, t)
	elif tag_type == TAG_INT_ARRAY:
		n = read_fmt(buf, ">i"); buf.read(n * 4)
	elif tag_type == TAG_LONG_ARRAY:
		n = read_fmt(buf, ">i"); buf.read(n * 8)

def parse_compound(buf):
	"""Parse un TAG_Compound et retourne un dict {nom: valeur}."""
	result = {}
	while True:
		tag_type = read_fmt(buf, ">b")
		if tag_type == TAG_END:
			break
		name = read_string(buf)
		result[name] = parse_payload(buf, tag_type)
	return result

def parse_payload(buf, tag_type):
	if tag_type == TAG_BYTE:		return read_fmt(buf, ">b")
	elif tag_type == TAG_SHORT:	 return read_fmt(buf, ">h")
	elif tag_type == TAG_INT:	   return read_fmt(buf, ">i")
	elif tag_type == TAG_LONG:	  return read_fmt(buf, ">q")
	elif tag_type == TAG_FLOAT:	 return read_fmt(buf, ">f")
	elif tag_type == TAG_DOUBLE:	return read_fmt(buf, ">d")
	elif tag_type == TAG_BYTE_ARRAY:
		n = read_fmt(buf, ">i"); return buf.read(n)
	elif tag_type == TAG_STRING:
		return read_string(buf)
	elif tag_type == TAG_LIST:
		elem_type = read_fmt(buf, ">b")
		count	 = read_fmt(buf, ">i")
		return [parse_payload(buf, elem_type) for _ in range(count)]
	elif tag_type == TAG_COMPOUND:
		return parse_compound(buf)
	elif tag_type == TAG_INT_ARRAY:
		n = read_fmt(buf, ">i"); return list(struct.unpack(f">{n}i", buf.read(n*4)))
	elif tag_type == TAG_LONG_ARRAY:
		n = read_fmt(buf, ">i"); return list(struct.unpack(f">{n}q", buf.read(n*8)))
	return None

def parse_nbt_root(data: bytes):
	buf = io.BytesIO(data)
	tag_type = read_fmt(buf, ">b")
	if tag_type == TAG_END:
		return {}
	read_string(buf)		  # nom racine (ignoré)
	return parse_payload(buf, tag_type)

# ── Décodage palette + block_states (Minecraft 1.16+) ──────────────────────
def decode_section(section: dict):
	"""
	Retourne une liste de 4096 noms de blocs (palette index → nom)
	pour une section de chunk (format 1.16+).
	"""
	block_states = section.get("block_states") or section
	palette = block_states.get("palette") or block_states.get("Palette") or []
	data	= block_states.get("data")	or block_states.get("Data")

	if not palette:
		return []

	names = []
	for entry in palette:
		if isinstance(entry, dict):
			n = entry.get("Name") or entry.get("name") or ""
		else:
			n = str(entry)
		names.append(n)

	if data is None or len(data) == 0:
		# Section remplie d'un seul bloc
		return [names[0]] * 4096

	bits_per_block = max(4, (len(palette) - 1).bit_length())
	mask = (1 << bits_per_block) - 1

	blocks = []
	for long_val in data:
		# Les longs NBT sont signés → non signé
		if long_val < 0:
			long_val += (1 << 64)
		# Minecraft 1.16+ : pas de dépassement de long
		num_per_long = 64 // bits_per_block
		for i in range(num_per_long):
			idx = (long_val >> (i * bits_per_block)) & mask
			if idx < len(names):
				blocks.append(names[idx])
			else:
				blocks.append("minecraft:air")
			if len(blocks) == 4096:
				break
		if len(blocks) >= 4096:
			break

	return blocks[:4096]

# ── Coordonnées dans le chunk ───────────────────────────────────────────────
def block_index_to_local(index: int):
	"""Retourne (local_x, local_y, local_z) dans la section (0-15)."""
	y = (index >> 8) & 0xF
	z = (index >> 4) & 0xF
	x =  index	   & 0xF
	return x, y, z

# ── Lecture fichier .mca ────────────────────────────────────────────────────
def iter_chunks(mca_path: str):
	"""Yield les données NBT décompressées de chaque chunk présent."""
	with open(mca_path, "rb") as f:
		header = f.read(4096)
		if len(header) < 4096:
			return
		for i in range(1024):
			offset_bytes = header[i*4 : i*4+4]
			offset  = (offset_bytes[0] << 16) | (offset_bytes[1] << 8) | offset_bytes[2]
			sectors =  offset_bytes[3]
			if offset == 0 and sectors == 0:
				continue
			f.seek(offset * 4096)
			length	= struct.unpack(">I", f.read(4))[0]
			comp_type = struct.unpack(">B", f.read(1))[0]
			raw	   = f.read(length - 1)
			try:
				if comp_type == 2:
					data = zlib.decompress(raw)
				elif comp_type == 1:
					import gzip
					data = gzip.decompress(raw)
				else:
					data = raw
				yield data
			except Exception:
				continue

# ── Scan d'un chunk ─────────────────────────────────────────────────────────
def scan_chunk(nbt: dict, found: list):
	"""Cherche les shulker boxes dans le chunk et ajoute les résultats à found."""

	# Support 1.18+ (Level supprimé) et 1.17-
	level = nbt.get("Level") or nbt
	cx = level.get("xPos") or level.get("XPos") or 0
	cz = level.get("zPos") or level.get("ZPos") or 0

	sections = level.get("sections") or level.get("Sections") or []

	for section in sections:
		if not isinstance(section, dict):
			continue
		sy = section.get("Y") or section.get("y")
		if sy is None:
			continue

		blocks = decode_section(section)
		if not blocks:
			continue

		for idx, name in enumerate(blocks):
			if name in SHULKER_TYPES:
				lx, ly, lz = block_index_to_local(idx)
				# Coordonnées monde
				world_x = cx * 16 + lx
				world_y = sy * 16 + ly
				world_z = cz * 16 + lz
				found.append((name, world_x, world_y, world_z))

# ── Programme principal ─────────────────────────────────────────────────────
def main():
	if len(sys.argv) < 2:
		print(f"{BOLD}Usage :{RESET}  python3 find_shulkers.py <chemin/vers/dossier/region>")
		print(f"Exemple: python3 find_shulkers.py ~/.minecraft/saves/MonMonde/region")
		sys.exit(1)

	region_dir = sys.argv[1]
	if not os.path.isdir(region_dir):
		print(f"\033[91mErreur :\033[0m '{region_dir}' n'est pas un dossier valide.")
		sys.exit(1)

	mca_files = [f for f in os.listdir(region_dir) if f.endswith(".mca")]
	if not mca_files:
		print(f"\033[91mAucun fichier .mca trouvé dans :\033[0m {region_dir}")
		sys.exit(1)

	print(f"\n{BOLD}🔍 Recherche de shulker boxes dans {len(mca_files)} fichier(s) .mca...{RESET}\n")

	all_found = []
	for mca_file in sorted(mca_files):
		path = os.path.join(region_dir, mca_file)
		chunk_found = []
		for chunk_data in iter_chunks(path):
			try:
				nbt = parse_nbt_root(chunk_data)
				scan_chunk(nbt, chunk_found)
			except Exception:
				continue
		if chunk_found:
			print(f"  📦 {mca_file} → {len(chunk_found)} shulker(s) trouvé(s)")
		all_found.extend(chunk_found)

	print()
	if not all_found:
		print(f"\033[93mAucun shulker box trouvé.\033[0m")
		return

	# Trier par coordonnées monde
	all_found.sort(key=lambda r: (r[1], r[3], r[2]))

	print(f"{BOLD}{'─'*58}{RESET}")
	print(f"{BOLD}  {'Type':<35} {'X':>6} {'Y':>5} {'Z':>6}{RESET}")
	print(f"{BOLD}{'─'*58}{RESET}")

	for (name, x, y, z) in all_found:
		color	= COLOR.get(name, "\033[97m")
		short	= name.replace("minecraft:", "")
		print(f"  {color}{short:<35}{RESET} {BOLD}{x:>6}{RESET} {y:>5} {BOLD}{z:>6}{RESET}")

	print(f"{BOLD}{'─'*58}{RESET}")
	print(f"\n{BOLD}✅ Total : {len(all_found)} shulker box(es) trouvé(s){RESET}\n")

if __name__ == "__main__":
	main()
