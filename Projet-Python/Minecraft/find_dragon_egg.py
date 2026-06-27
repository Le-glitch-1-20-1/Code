#!/usr/bin/env python3
"""
find_dragon_egg.py
──────────────────
Scanne tous les fichiers .mca d'un dossier de région Minecraft
et trouve l'œuf de dragon (minecraft:dragon_egg) :
  • posé comme bloc dans le monde
  • à l'intérieur d'un contenant (shulker box, coffre, tonneau,
    ender chest, hopper, dropper, dispenser, chest minecart…)

Usage :
    python3 find_dragon_egg.py <chemin/vers/dossier/region>

Exemple :
    python3 find_dragon_egg.py ~/.minecraft/saves/MonMonde/region
"""

import sys
import os
import struct
import zlib
import io

TARGET = "minecraft:dragon_egg"

# Blocs qui sont des contenants (block entities avec inventaire)
CONTAINER_TYPES = {
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

# ── Couleurs terminal ───────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
PURPLE = "\033[35m"
GOLD   = "\033[33m"
GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"

# ── Lecture NBT minimale ────────────────────────────────────────────────────
TAG_END        = 0
TAG_BYTE       = 1
TAG_SHORT      = 2
TAG_INT        = 3
TAG_LONG       = 4
TAG_FLOAT      = 5
TAG_DOUBLE     = 6
TAG_BYTE_ARRAY = 7
TAG_STRING     = 8
TAG_LIST       = 9
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
    if tag_type == TAG_BYTE:         buf.read(1)
    elif tag_type == TAG_SHORT:      buf.read(2)
    elif tag_type == TAG_INT:        buf.read(4)
    elif tag_type == TAG_LONG:       buf.read(8)
    elif tag_type == TAG_FLOAT:      buf.read(4)
    elif tag_type == TAG_DOUBLE:     buf.read(8)
    elif tag_type == TAG_BYTE_ARRAY:
        n = read_fmt(buf, ">i"); buf.read(n)
    elif tag_type == TAG_STRING:
        read_string(buf)
    elif tag_type == TAG_LIST:
        elem_type = read_fmt(buf, ">b")
        count     = read_fmt(buf, ">i")
        for _ in range(count):
            skip_payload(buf, elem_type)
    elif tag_type == TAG_COMPOUND:
        while True:
            t = read_fmt(buf, ">b")
            if t == TAG_END: break
            read_string(buf)
            skip_payload(buf, t)
    elif tag_type == TAG_INT_ARRAY:
        n = read_fmt(buf, ">i"); buf.read(n * 4)
    elif tag_type == TAG_LONG_ARRAY:
        n = read_fmt(buf, ">i"); buf.read(n * 8)

def parse_compound(buf):
    result = {}
    while True:
        tag_type = read_fmt(buf, ">b")
        if tag_type == TAG_END:
            break
        name = read_string(buf)
        result[name] = parse_payload(buf, tag_type)
    return result

def parse_payload(buf, tag_type):
    if tag_type == TAG_BYTE:         return read_fmt(buf, ">b")
    elif tag_type == TAG_SHORT:      return read_fmt(buf, ">h")
    elif tag_type == TAG_INT:        return read_fmt(buf, ">i")
    elif tag_type == TAG_LONG:       return read_fmt(buf, ">q")
    elif tag_type == TAG_FLOAT:      return read_fmt(buf, ">f")
    elif tag_type == TAG_DOUBLE:     return read_fmt(buf, ">d")
    elif tag_type == TAG_BYTE_ARRAY:
        n = read_fmt(buf, ">i"); return buf.read(n)
    elif tag_type == TAG_STRING:
        return read_string(buf)
    elif tag_type == TAG_LIST:
        elem_type = read_fmt(buf, ">b")
        count     = read_fmt(buf, ">i")
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
    read_string(buf)
    return parse_payload(buf, tag_type)

# ── Décodage palette + block_states (Minecraft 1.16+) ──────────────────────
def decode_section(section: dict):
    block_states = section.get("block_states") or section
    palette = block_states.get("palette") or block_states.get("Palette") or []
    data    = block_states.get("data")    or block_states.get("Data")

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
        return [names[0]] * 4096

    bits_per_block = max(4, (len(palette) - 1).bit_length())
    mask = (1 << bits_per_block) - 1

    blocks = []
    for long_val in data:
        if long_val < 0:
            long_val += (1 << 64)
        num_per_long = 64 // bits_per_block
        for i in range(num_per_long):
            idx = (long_val >> (i * bits_per_block)) & mask
            blocks.append(names[idx] if idx < len(names) else "minecraft:air")
            if len(blocks) == 4096:
                break
        if len(blocks) >= 4096:
            break

    return blocks[:4096]

def block_index_to_local(index: int):
    y = (index >> 8) & 0xF
    z = (index >> 4) & 0xF
    x =  index       & 0xF
    return x, y, z

# ── Lecture fichier .mca ────────────────────────────────────────────────────
def iter_chunks(mca_path: str):
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
            length    = struct.unpack(">I", f.read(4))[0]
            comp_type = struct.unpack(">B", f.read(1))[0]
            raw       = f.read(length - 1)
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

# ── Recherche dans les inventaires (récursif) ───────────────────────────────
def search_items_for_egg(items, path=""):
    """
    Parcourt récursivement une liste d'items NBT.
    Retourne True si l'œuf de dragon est trouvé quelque part.
    """
    if not isinstance(items, list):
        return False
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id") or item.get("Id") or ""
        if item_id == TARGET:
            return True
        # Conteneur imbriqué : tag.BlockEntityTag.Items ou tag.Items
        tag = item.get("tag") or item.get("Tag") or {}
        if isinstance(tag, dict):
            sub_be = tag.get("BlockEntityTag") or {}
            if isinstance(sub_be, dict):
                sub_items = sub_be.get("Items") or sub_be.get("items") or []
                if search_items_for_egg(sub_items):
                    return True
            sub_items = tag.get("Items") or tag.get("items") or []
            if search_items_for_egg(sub_items):
                return True
        # Inventaire direct dans l'item (shulker box posée dans un coffre, etc.)
        direct = item.get("Items") or item.get("items") or []
        if search_items_for_egg(direct):
            return True
    return False

# ── Scan d'un chunk ─────────────────────────────────────────────────────────
def scan_chunk(nbt: dict, found_block: list, found_container: list):
    level = nbt.get("Level") or nbt
    cx = level.get("xPos") or level.get("XPos") or 0
    cz = level.get("zPos") or level.get("ZPos") or 0

    # ── 1. Cherche l'œuf posé comme bloc ────────────────────────────────────
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
            if name == TARGET:
                lx, ly, lz = block_index_to_local(idx)
                found_block.append((cx * 16 + lx, sy * 16 + ly, cz * 16 + lz))

    # ── 2. Cherche l'œuf dans les block entities (contenants) ───────────────
    be_list = (
        level.get("block_entities")
        or level.get("TileEntities")
        or level.get("tileEntities")
        or []
    )
    for be in be_list:
        if not isinstance(be, dict):
            continue
        be_id = be.get("id") or be.get("Id") or ""
        # Normalise : "minecraft:chest" ou juste "Chest"
        if not be_id.startswith("minecraft:"):
            be_id = "minecraft:" + be_id.lower()

        if be_id not in CONTAINER_TYPES:
            continue

        items = be.get("Items") or be.get("items") or []
        if search_items_for_egg(items):
            bx = be.get("x") or be.get("X") or 0
            by = be.get("y") or be.get("Y") or 0
            bz = be.get("z") or be.get("Z") or 0
            container_name = be_id.replace("minecraft:", "")
            found_container.append((container_name, bx, by, bz))

# ── Détection structure Vanilla / Paper ────────────────────────────────────
DIMS_VANILLA = [
    ("🌍 Overworld", "region"),
    ("🔥 Nether",    os.path.join("DIM-1", "region")),
    ("🌌 End",       os.path.join("DIM1",  "region")),
]
DIMS_PAPER = [
    ("🌍 Overworld", os.path.join("world",         "region")),
    ("🔥 Nether",    os.path.join("world_nether",  "DIM-1", "region")),
    ("🌌 End",       os.path.join("world_the_end", "DIM1",  "region")),
]

def detect_dims(save_dir: str):
    if os.path.isdir(os.path.join(save_dir, "world")):
        return DIMS_PAPER, "Paper/Spigot"
    if os.path.isdir(os.path.join(save_dir, "region")):
        return DIMS_VANILLA, "Vanilla"
    return DIMS_PAPER, "inconnu"

def scan_region_dir(region_dir: str, dim_label: str, all_blocks: list, all_containers: list):
    """Scanne un dossier region/ et ajoute les résultats aux listes globales."""
    if not os.path.isdir(region_dir):
        print(f"  {CYAN}(absent){RESET}")
        return

    mca_files = [f for f in os.listdir(region_dir) if f.endswith(".mca")]
    if not mca_files:
        print(f"  {CYAN}(aucun .mca){RESET}")
        return

    dim_blocks     = []
    dim_containers = []

    for mca_file in sorted(mca_files):
        path = os.path.join(region_dir, mca_file)
        b, c = [], []
        for chunk_data in iter_chunks(path):
            try:
                nbt = parse_nbt_root(chunk_data)
                scan_chunk(nbt, b, c)
            except Exception:
                continue
        if b or c:
            print(f"    📦 {mca_file} → {len(b)} bloc(s), {len(c)} contenant(s)")
        dim_blocks.extend(b)
        dim_containers.extend(c)

    # Tagguer chaque résultat avec la dimension
    for coords in dim_blocks:
        all_blocks.append((dim_label,) + coords)
    for entry in dim_containers:
        all_containers.append((dim_label,) + entry)

    if not dim_blocks and not dim_containers:
        print(f"    {CYAN}Rien trouvé.{RESET}")

# ── Programme principal ─────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(f"{BOLD}Usage :{RESET}  python3 find_dragon_egg.py <chemin/sauvegarde>")
        print(f"Vanilla : python3 find_dragon_egg.py ~/.minecraft/saves/MonMonde")
        print(f"Paper   : python3 find_dragon_egg.py ~/Downloads/minecraft/map-3")
        sys.exit(1)

    save_dir = sys.argv[1]
    if not os.path.isdir(save_dir):
        print(f"{RED}Erreur :{RESET} '{save_dir}' n'est pas un dossier valide.")
        sys.exit(1)

    dims, server_type = detect_dims(save_dir)

    print(f"\n{BOLD}{PURPLE}🥚 Recherche de l'œuf de dragon — toutes dimensions{RESET}")
    print(f"{CYAN}Structure : {server_type}{RESET}\n")

    all_blocks     = []   # (dim, x, y, z)
    all_containers = []   # (dim, ctype, x, y, z)

    for dim_label, rel_path in dims:
        region_dir = os.path.join(save_dir, rel_path)
        print(f"{BOLD}{dim_label}{RESET}  {CYAN}({rel_path}){RESET}")
        scan_region_dir(region_dir, dim_label, all_blocks, all_containers)
        print()

    if not all_blocks and not all_containers:
        print(f"{GOLD}Aucun œuf de dragon trouvé dans aucune dimension.{RESET}\n")
        return

    # ── Résultats : œuf posé ────────────────────────────────────────────────
    if all_blocks:
        print(f"{BOLD}{'─'*60}{RESET}")
        print(f"{BOLD}{PURPLE}  🥚 Œuf de dragon posé dans le monde{RESET}")
        print(f"{BOLD}{'─'*60}{RESET}")
        print(f"{BOLD}  {'Dimension':<16} {'X':>8}  {'Y':>5}  {'Z':>8}{RESET}")
        print(f"{'─'*60}")
        for (dim, x, y, z) in sorted(all_blocks, key=lambda r: (r[1], r[3])):
            print(f"  {PURPLE}{dim:<16}{RESET} {BOLD}{x:>8}{RESET}  {y:>5}  {BOLD}{z:>8}{RESET}")
        print(f"{BOLD}{'─'*60}{RESET}\n")

    # ── Résultats : œuf dans un contenant ───────────────────────────────────
    if all_containers:
        print(f"{BOLD}{'─'*68}{RESET}")
        print(f"{BOLD}{GOLD}  🗃  Œuf de dragon dans un contenant{RESET}")
        print(f"{BOLD}{'─'*68}{RESET}")
        print(f"{BOLD}  {'Dimension':<16} {'Contenant':<22} {'X':>8}  {'Y':>5}  {'Z':>8}{RESET}")
        print(f"{'─'*68}")
        for (dim, ctype, x, y, z) in sorted(all_containers, key=lambda r: (r[2], r[4])):
            print(f"  {GOLD}{dim:<16}{RESET} {ctype:<22} {BOLD}{x:>8}{RESET}  {y:>5}  {BOLD}{z:>8}{RESET}")
        print(f"{BOLD}{'─'*68}{RESET}\n")

    total = len(all_blocks) + len(all_containers)
    print(f"{BOLD}{GREEN}✅ Total : {total} emplacement(s) trouvé(s){RESET}\n")

if __name__ == "__main__":
    main()
