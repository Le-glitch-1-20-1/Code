#!/usr/bin/env python3
"""
map_area_calculator.py
─────────────────
Counts the number of generated chunks in each Minecraft dimension
and converts it into block area (1 chunk = 16×16 = 256 blocks²).

Compatible with Vanilla AND Paper/Spigot (multi-world structure auto-detected).

Usage:
    python3 map_area_calculator.py <path/to/save/folder>

Vanilla  → python3 map_area_calculator.py ~/.minecraft/saves/MyWorld
Paper    → python3 map_area_calculator.py ~/Downloads/minecraft/map-3
"""

import sys
import os
import struct

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
GOLD   = "\033[33m"
PURPLE = "\033[35m"
RED    = "\033[35m"
GRAY   = "\033[90m"
DIM_COLOR = {
    "Overworld": "\033[92m",   # green
    "Nether":    "\033[91m",   # red
    "End":       "\033[35m",   # purple
}

# Possible structures detected automatically:
#   Vanilla  → save/region  +  save/DIM-1/region  +  save/DIM1/region
#   Paper    → world/region + world_nether/DIM-1/region + world_the_end/DIM1/region
# The script tests both and uses whichever exists.

DIMS_VANILLA = [
    ("Overworld", "region"),
    ("Nether",    os.path.join("DIM-1", "region")),
    ("End",       os.path.join("DIM1",  "region")),
]

DIMS_PAPER = [
    ("Overworld", os.path.join("world",         "region")),
    ("Nether",    os.path.join("world_nether",  "DIM-1", "region")),
    ("End",       os.path.join("world_the_end", "DIM1",  "region")),
]

def detect_dims(save_dir: str):
    """Returns the DIMS list matching the save's structure."""
    # Test Paper first (world/ present in the folder)
    if os.path.isdir(os.path.join(save_dir, "world")):
        return DIMS_PAPER, "Paper/Spigot"
    # Otherwise Vanilla (region/ directly)
    if os.path.isdir(os.path.join(save_dir, "region")):
        return DIMS_VANILLA, "Vanilla"
    # None: return Paper for a clean error message
    return DIMS_PAPER, "unknown"

def count_chunks_in_mca(mca_path: str) -> int:
    """Counts the chunks present (non-empty) in an .mca file."""
    count = 0
    try:
        with open(mca_path, "rb") as f:
            header = f.read(4096)
        if len(header) < 4096:
            return 0
        for i in range(1024):
            b = header[i*4 : i*4+4]
            offset  = (b[0] << 16) | (b[1] << 8) | b[2]
            sectors =  b[3]
            if offset != 0 or sectors != 0:
                count += 1
    except Exception:
        pass
    return count

def scan_dimension(save_dir: str, rel_path: str):
    """
    Returns (chunks, min_cx, max_cx, min_cz, max_cz, mca_count)
    for a given dimension.
    """
    region_dir = os.path.join(save_dir, rel_path)
    if not os.path.isdir(region_dir):
        return None

    mca_files = [f for f in os.listdir(region_dir) if f.endswith(".mca")]
    if not mca_files:
        return None

    total_chunks = 0
    min_rx = min_rz =  999999
    max_rx = max_rz = -999999

    for mca_file in mca_files:
        # Filename format: r.RX.RZ.mca
        parts = mca_file.split(".")
        try:
            rx = int(parts[1])
            rz = int(parts[2])
        except (IndexError, ValueError):
            continue
        min_rx = min(min_rx, rx)
        max_rx = max(max_rx, rx)
        min_rz = min(min_rz, rz)
        max_rz = max(max_rz, rz)

        path = os.path.join(region_dir, mca_file)
        total_chunks += count_chunks_in_mca(path)

    # Bounds in blocks (chunk = 16 blocks, region = 32 chunks)
    min_bx = min_rx * 32 * 16
    max_bx = (max_rx + 1) * 32 * 16 - 1
    min_bz = min_rz * 32 * 16
    max_bz = (max_rz + 1) * 32 * 16 - 1

    return {
        "chunks":     total_chunks,
        "blocks":     total_chunks * 16 * 16,
        "mca_count":  len(mca_files),
        "min_bx": min_bx, "max_bx": max_bx,
        "min_bz": min_bz, "max_bz": max_bz,
        "span_x": max_bx - min_bx + 1,
        "span_z": max_bz - min_bz + 1,
    }

def fmt_big(n: int) -> str:
    """Formats a large number with a space separator."""
    return f"{n:,}".replace(",", " ")

def bar(ratio: float, width: int = 30) -> str:
    """ASCII progress bar."""
    filled = round(ratio * width)
    return "█" * filled + "░" * (width - filled)

def main():
    if len(sys.argv) < 2:
        print(f"{BOLD}Usage:{RESET}  python3 map_area_calculator.py <path/to/save>")
        print(f"Vanilla: python3 map_area_calculator.py ~/.minecraft/saves/MyWorld")
        print(f"Paper  : python3 map_area_calculator.py ~/Downloads/minecraft/map-3")
        sys.exit(1)

    save_dir = sys.argv[1]
    if not os.path.isdir(save_dir):
        print(f"\033[91mError:\033[0m '{save_dir}' is not a valid folder.")
        sys.exit(1)

    dims, server_type = detect_dims(save_dir)

    print(f"\n{BOLD}🗺  Map area analysis{RESET}")
    print(f"{GRAY}{save_dir}{RESET}")
    print(f"{GRAY}Detected structure: {server_type}{RESET}\n")

    results = {}
    for dim_name, rel_path in dims:
        data = scan_dimension(save_dir, rel_path)
        if data:
            results[dim_name] = data

    if not results:
        print(f"\033[93mNo dimension found in this save folder.\033[0m\n")
        sys.exit(1)

    max_chunks = max(r["chunks"] for r in results.values()) or 1

    for dim_name, data in results.items():
        color = DIM_COLOR.get(dim_name, CYAN)
        chunks = data["chunks"]
        blocks = data["blocks"]
        ratio  = chunks / max_chunks

        print(f"{BOLD}{color}{'─'*54}{RESET}")
        print(f"{BOLD}{color}  {'🌍' if dim_name=='Overworld' else '🔥' if dim_name=='Nether' else '🌌'} {dim_name}{RESET}")
        print(f"{BOLD}{color}{'─'*54}{RESET}")
        print(f"  .mca files           : {BOLD}{fmt_big(data['mca_count'])}{RESET}")
        print(f"  Generated chunks     : {BOLD}{fmt_big(chunks)}{RESET}")
        print(f"  Area                 : {BOLD}{color}{fmt_big(blocks)} blocks²{RESET}  ({fmt_big(blocks // 1_000_000)} M)")
        print(f"  In km²               : {BOLD}{blocks / 1_000_000:.2f} km²{RESET}  (1 block = 1 m)")
        print(f"  X extent             : {data['min_bx']:>8}  →  {data['max_bx']}  (±{data['span_x']//2} blocks)")
        print(f"  Z extent             : {data['min_bz']:>8}  →  {data['max_bz']}  (±{data['span_z']//2} blocks)")
        print(f"  {GRAY}{bar(ratio)} {ratio*100:.1f}%{RESET}")
        print()

    # ── Overall summary ─────────────────────────────────────────────────────
    total_chunks = sum(r["chunks"] for r in results.values())
    total_blocks = sum(r["blocks"] for r in results.values())

    print(f"{BOLD}{'═'*54}{RESET}")
    print(f"{BOLD}  ✅ TOTAL across all dimensions{RESET}")
    print(f"{BOLD}{'═'*54}{RESET}")
    print(f"  Total chunks         : {BOLD}{GREEN}{fmt_big(total_chunks)}{RESET}")
    print(f"  Total area           : {BOLD}{GREEN}{fmt_big(total_blocks)} blocks²{RESET}")
    print(f"  In km²               : {BOLD}{GREEN}{total_blocks / 1_000_000:.2f} km²{RESET}")
    print(f"{BOLD}{'═'*54}{RESET}\n")

if __name__ == "__main__":
    main()
