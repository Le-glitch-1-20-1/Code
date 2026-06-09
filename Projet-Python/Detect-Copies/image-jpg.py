#!/usr/bin/env python3

import sys
import logging
import warnings
import argparse
import os
import pillow_heif
from pathlib	import Path
from PIL		import Image
from tqdm		import tqdm

warnings.filterwarnings("ignore", category=UserWarning)
pillow_heif.register_heif_opener()
TARGET_EXTENSIONS = {".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif", ".jpeg"}

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def ask(question: str, default: bool = False) -> bool:
	hint = "[y/n]"
	try:
		answer = input(f"{question} {hint}: ").strip().lower()
	except (EOFError, KeyboardInterrupt):
		print()
		logger.info("Input interrupted. Using default value.")
		return default
	if not answer:
		return default
	return answer in ("y", "yes")

def ask_int(question: str, min_val: int, max_val: int, default: int) -> int:
	while True:
		try:
			raw = input(f"{question} [{min_val}-{max_val}] (default: {default}): ").strip()
		except (EOFError, KeyboardInterrupt):
			print()
			logger.info("Input interrupted. Using default value.")
			return default
		if not raw:
			return default
		try:
			val = int(raw)
			if min_val <= val <= max_val:
				return val
			logger.warning(f"[ERROR] Value must be between {min_val} and {max_val}.")
		except ValueError:
			logger.warning("[ERROR] Invalid value.")

def resolve_path(raw: str) -> Path:
	return Path(raw).expanduser().resolve()

def collect_files(root: Path, recursive: bool) -> list[Path]:
	pattern = "**/*" if recursive else "*"
	found = []
	with tqdm(desc="Scanning", unit="file", leave=False) as pbar:
		for p in root.glob(pattern):
			try:
				if p.is_file() and p.suffix.lower() in TARGET_EXTENSIONS:
					found.append(p)
					pbar.update(1)
			except PermissionError:
				logging.error("Permission denied accessing: %s", p)
			except OSError as e:
				logging.error("OS error accessing %s: %s", p, e)
	return found

def convert_file(file_path: Path, quality: int, delete_original: bool, dry_run: bool) -> str:
	target_path = file_path.with_suffix(".jpg")
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
		logging.error("Failed on %s: %s", file_path, exc)
		return "error"

def run(root: Path, quality: int, delete_original: bool, dry_run: bool, recursive: bool) -> None:
	files = collect_files(root, recursive)
	if not files:
		logger.info("No files to convert in this folder.")
		return
	prefix = "[DRY RUN] " if dry_run else ""
	logger.info(f"\n{prefix}Processing {len(files)} file(s) to convert")
	counts = {"success": 0, "skipped": 0, "error": 0}
	bar_fmt = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
	try:
		with tqdm(files, desc="Converting", unit="img", bar_format=bar_fmt) as pbar:
			for file_path in pbar:
				pbar.set_postfix_str(file_path.name[:35], refresh=False)
				result = convert_file(file_path, quality, delete_original, dry_run)
				counts[result] += 1
	except KeyboardInterrupt:
		logger.info("\nKeyboard interrupt detected. Exiting.")
	logger.info(f"\n{prefix}{counts['success']} succeeded, {counts['skipped']} skipped, {counts['error']} failed.")
	if counts["error"]:
		logger.info("Details: image_errors.log")

def interactive_wizard() -> dict:
	try:
		folder_input = input("Path to the folder to analyse: ").strip()
	except (EOFError, KeyboardInterrupt):
		print()
		logger.info("Aborted.")
		sys.exit(0)
	if not folder_input:
		logger.error("[ERROR] No path provided.")
		sys.exit(1)
	root = resolve_path(folder_input)
	if not root.exists():
		logger.error(f"[ERROR] Path does not exist: '{root}'")
		sys.exit(1)
	if not root.is_dir():
		logger.error(f"[ERROR] Path is not a directory: '{root}'")
		sys.exit(1)
	if not os.access(root, os.R_OK):
		logger.error(f"[ERROR] No read permission on: '{root}'")
		sys.exit(1)
	recursive		= ask("Also scan subfolders?", default=True)
	quality			= ask_int("JPEG quality", min_val=1, max_val=95, default=95)
	delete_original	= ask("Delete originals after conversion?", default=False)
	dry_run			= ask("Simulate without converting files?", default=False)
	return dict(root=root, quality=quality, delete_original=delete_original, dry_run=dry_run, recursive=recursive)

def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser()
	parser.add_argument("--link",			metavar="PATH",							help="Path to the folder to process (resolves symlinks)")
	parser.add_argument("--quality",		type=int, default=None, metavar="N",	help="JPEG quality 1-95 (default: 95)")
	parser.add_argument("--no-delete",		action="store_true",					help="Keep original files after conversion (skips interactive prompt)")
	parser.add_argument("--delete",			action="store_true",					help="Delete original files after conversion (skips interactive prompt)")
	parser.add_argument("--dry-run",		action="store_true",					help="Simulate without modifying any file (skips interactive prompt)")
	parser.add_argument("--no-dry-run",		action="store_true",					help="Actually convert files (skips interactive prompt)")
	parser.add_argument("--recursive",		action="store_true",					help="Include subfolders (skips interactive prompt)")
	parser.add_argument("--no-recursive",	action="store_true",					help="Current folder only, no subfolders (skips interactive prompt)")
	return parser.parse_args()

def main():
	args = parse_args()
	if args.link:
		root = resolve_path(args.link)
		if not root.exists():
			logger.error(f"[ERROR] Path does not exist: '{root}'")
			sys.exit(1)
		if not root.is_dir():
			logger.error(f"[ERROR] Path is not a directory: '{root}'")
			sys.exit(1)
		if not os.access(root, os.R_OK):
			logger.error(f"[ERROR] No read permission on: '{root}'")
			sys.exit(1)
		quality = args.quality if args.quality is not None else 95
		if not (1 <= quality <= 95):
			logger.error("[ERROR] Quality must be between 1 and 95.")
			sys.exit(1)
		delete_original	= True if args.delete else False if args.no_delete else True
		dry_run			= True if args.dry_run else False if args.no_dry_run else False
		recursive		= True if args.recursive else False if args.no_recursive else True
		run(root=root, quality=quality, delete_original=delete_original, dry_run=dry_run, recursive=recursive)
	else:
		cfg = interactive_wizard()
		run(**cfg)

if __name__ == "__main__":
	main()
