#!/usr/bin/env python3

import shutil
import hashlib
import logging
import sys
import os
import argparse
from collections	import defaultdict
from pathlib		import Path
from typing			import Optional
from tqdm			import tqdm
from PIL			import Image, UnidentifiedImageError
from tqdm			import tqdm

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def hash_image(image_path: Path) -> Optional[str]:
	try:
		with Image.open(image_path) as img:
			img_bytes = img.convert("RGB").tobytes()
		return hashlib.md5(img_bytes).hexdigest()
	except FileNotFoundError:
		logger.warning(f"[ERROR] File not found: '{image_path}'")
	except PermissionError:
		logger.warning(f"[ERROR] Permission denied: '{image_path}'")
	except UnidentifiedImageError:
		logger.warning(f"[ERROR] Unrecognized image format: '{image_path.name}'")
	except OSError as e:
		logger.warning(f"[ERROR] OS error reading '{image_path.name}': {e}")
	except Exception as e:
		logger.warning(f"[ERROR] Unexpected error hashing '{image_path.name}': {e}")
	return None

def load_hashes(hash_file: Path) -> dict[str, dict[str, str]]:
	if not hash_file.exists():
		return {}
	hashes: dict[str, dict[str, str]] = defaultdict(dict)
	try:
		with hash_file.open("r", encoding="utf-8") as f:
			for line_num, line in enumerate(f, 1):
				parts = line.strip().split("|", 2)
				if len(parts) == 3:
					folder_key, hash_value, file_name = parts
					hashes[folder_key][hash_value] = file_name
				elif line.strip():
					logger.warning(f"[ERROR] Malformed line {line_num} in hash file, skipping.")
	except PermissionError:
		logger.warning(f"[ERROR] Cannot read hash file (permission denied): '{hash_file}'. Starting fresh.")
	except UnicodeDecodeError:
		logger.warning(f"[ERROR] Hash file encoding error: '{hash_file}'. Starting fresh.")
	except OSError as e:
		logger.warning(f"[ERROR] OS error reading hash file: {e}. Starting fresh.")
	return hashes

def save_hashes(hashes: dict[str, dict[str, str]], hash_file: Path) -> bool:
	tmp_file = hash_file.with_suffix(".tmp")
	try:
		with tmp_file.open("w", encoding="utf-8") as f:
			for folder_key, folder_hashes in hashes.items():
				for hash_value, file_name in folder_hashes.items():
					f.write(f"{folder_key}|{hash_value}|{file_name}\n")
		tmp_file.replace(hash_file)
		return True
	except PermissionError:
		logger.error(f"[ERROR] Permission denied writing hash file: '{hash_file}'.")
	except OSError as e:
		logger.error(f"[ERROR] OS error saving hash file: {e}")
	except Exception as e:
		logger.error(f"[ERROR] Unexpected error saving hash file: {e}")
	finally:
		if tmp_file.exists():
			try:
				tmp_file.unlink()
			except OSError:
				pass
	return False

def get_unique_destination(dest_folder: Path, filename: str) -> Path:
	dest = dest_folder / filename
	if not dest.exists():
		return dest
	stem, suffix = Path(filename).stem, Path(filename).suffix
	counter = 1
	while dest.exists():
		dest = dest_folder / f"{stem}_{counter}{suffix}"
		counter += 1
	return dest

def collect_files(folder_path: Path, copies_folder: Path, recursive: bool) -> list[Path]:
	pattern = "**/*" if recursive else "*"
	collected = []
	try:
		for p in folder_path.glob(pattern):
			try:
				if (
					p.is_file()
					and p.suffix.lower() in SUPPORTED_EXTENSIONS
					and copies_folder not in p.parents
					and p.parent != copies_folder
				):
					collected.append(p)
			except PermissionError:
				logger.warning(f"[ERROR] Permission denied accessing: '{p}'")
			except OSError as e:
				logger.warning(f"[ERROR] OS error accessing '{p}': {e}")
	except PermissionError:
		logger.error(f"[ERROR] Cannot list directory '{folder_path}': permission denied.")
	except OSError as e:
		logger.error(f"[ERROR] OS error scanning directory: {e}")
	return collected

def resolve_copies_dest(file_path: Path, root_folder: Path, copies_folder: Path, flat: bool) -> Path:
	if flat:
		return copies_folder
	try:
		relative = file_path.parent.relative_to(root_folder)
		mirrored = copies_folder / relative
		mirrored.mkdir(parents=True, exist_ok=True)
		return mirrored
	except ValueError:
		logger.warning(f"[ERROR] Could not mirror path for '{file_path.name}', falling back to flat.")
		return copies_folder
	except PermissionError:
		logger.warning("[ERROR] Permission denied creating mirror dir, falling back to flat.")
		return copies_folder
	except OSError as e:
		logger.warning(f"[ERROR] OS error creating mirror dir: {e}. Falling back to flat.")
		return copies_folder

def safe_move(src: Path, dst: Path) -> bool:
	try:
		shutil.move(str(src), dst)
		return True
	except PermissionError:
		logger.error(f"[ERROR] Permission denied moving '{src.name}'.")
	except shutil.Error as e:
		logger.error(f"[ERROR] Move failed for '{src.name}': {e}")
	except OSError as e:
		logger.error(f"[ERROR] OS error moving '{src.name}': {e}")
	except Exception as e:
		logger.error(f"[ERROR] Unexpected error moving '{src.name}': {e}")
	return False

def detect_and_move_copies(
	folder_path: Path,
	recursive: bool		= False,
	flat: bool			= True,
	dry_run: bool		= False,
	global_scope: bool	= False,
) -> None:
	copies_folder = folder_path / "copies"
	try:
		copies_folder.mkdir(exist_ok=True)
	except PermissionError:
		logger.error(f"[ERROR] Cannot create 'copies' folder: permission denied in '{folder_path}'.")
		return
	except OSError as e:
		logger.error(f"[ERROR] Cannot create 'copies' folder: {e}")
		return
	hash_file = copies_folder / "image_hashes.txt"
	error_log = copies_folder / "errors-report.txt"
	file_handler = None
	try:
		error_log.write_text("", encoding="utf-8")
		file_handler = logging.FileHandler(error_log, encoding="utf-8")
		file_handler.setLevel(logging.WARNING)
		logger.addHandler(file_handler)
	except PermissionError:
		logger.warning("[ERROR] Cannot write error log (permission denied). Warnings will only appear in console.")
	except OSError as e:
		logger.warning(f"[ERROR] Cannot create error log: {e}. Warnings will only appear in console.")
	try:
		hashes: dict[str, dict[str, str]] = defaultdict(dict, load_hashes(hash_file))
		logger.info("Scanning for image files…")
		with tqdm(desc="Scanning", unit="file", leave=False) as pbar:
			files = []
			pattern = "**/*" if recursive else "*"
			try:
				for p in folder_path.glob(pattern):
					try:
						if (
							p.is_file()
							and p.suffix.lower() in SUPPORTED_EXTENSIONS
							and copies_folder not in p.parents
							and p.parent != copies_folder
						):
							files.append(p)
							pbar.update(1)
					except PermissionError:
						logger.warning(f"[ERROR] Permission denied accessing: '{p}'")
					except OSError as e:
						logger.warning(f"[ERROR] OS error accessing '{p}': {e}")
			except PermissionError:
				logger.error(f"[ERROR] Cannot list directory '{folder_path}': permission denied.")
			except OSError as e:
				logger.error(f"[ERROR] OS error scanning directory: {e}")
		if not files:
			logger.info("No image files found to process.")
			return
		mode_label		= "recursive" if recursive else "root folder only"
		dest_label		= "flat" if flat else "mirror structure"
		scope_label		= "global (all folders)" if global_scope else "per folder"
		prefix			= "[DRY RUN] " if dry_run else ""
		logger.info(
			f"\n{prefix}Processing {len(files)} image(s) "
			f"[mode: {mode_label} | copies: {dest_label} | detection: {scope_label}]"
		)
		counts			= {"success": 0, "skipped": 0, "error": 0}
		moved_details:	list[str] = []
		with tqdm(total=len(files), desc="Processing", unit="img") as pbar:
			for file_path in files:
				image_hash = hash_image(file_path)
				if image_hash is None:
					counts["error"] += 1
					pbar.update(1)
					continue
				folder_key		= "_global_" if global_scope else str(file_path.parent.relative_to(folder_path))
				folder_hashes	= hashes[folder_key]
				if image_hash in folder_hashes:
					dest_dir	= resolve_copies_dest(file_path, folder_path, copies_folder, flat)
					dest		= get_unique_destination(dest_dir, file_path.name)
					rel_src		= file_path.relative_to(folder_path)
					rel_dst		= dest.relative_to(folder_path)
					original	= folder_hashes[image_hash]
					if not dry_run:
						if safe_move(file_path, dest):
							counts["success"] += 1
							moved_details.append(f"{rel_src} → {rel_dst}  (original: {original})")
						else:
							counts["error"] += 1
					else:
						counts["success"] += 1
						moved_details.append(f"{rel_src} → {rel_dst}  (original: {original})")
				else:
					folder_hashes[image_hash] = file_path.name
					counts["skipped"] += 1
				pbar.update(1)
		if not dry_run:
			if not save_hashes(hashes, hash_file):
				logger.warning("[ERROR] Hash file could not be saved. Progress may be lost.")
		if moved_details:
			logger.info(f"\n{prefix}{len(moved_details)} duplicate(s) {'detected' if dry_run else 'moved'}:")
			for f in moved_details:
				logger.info(f"  - {f}")
		logger.info(f"\n{prefix}{counts['success']} succeeded, {counts['skipped']} skipped, {counts['error']} failed.")
		if counts["error"]:
			logger.info(f"Details: {error_log}")
		logger.info("Done.")
	except KeyboardInterrupt:
		logger.info("\nKeyboard interrupt detected. Saving hashes…")
		if not dry_run:
			save_hashes(hashes, hash_file)
		logger.info("Hashes saved. Clean exit.")
	except Exception as e:
		logger.error(f"\n[ERROR] Unexpected fatal error: {e}")
		if not dry_run:
			logger.info("Attempting to save hashes before exit…")
			save_hashes(hashes, hash_file)
		raise
	finally:
		if file_handler:
			logger.removeHandler(file_handler)
			try:
				file_handler.close()
			except Exception:
				pass

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

def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("--link",			type=str,				help="Path to the folder to analyse")
	parser.add_argument("--recursive",		action="store_true",	help="Also scan subfolders (skips interactive prompt)")
	parser.add_argument("--no-recursive",	action="store_true",	help="Do not scan subfolders (skips interactive prompt)")
	parser.add_argument("--flat",			action="store_true",	help="Copy duplicates flat into 'copies/' (skips interactive prompt)")
	parser.add_argument("--no-flat",		action="store_true",	help="Mirror folder structure inside 'copies/' (skips interactive prompt)")
	parser.add_argument("--global-scope",	action="store_true",	help="Detect duplicates across all folders (skips interactive prompt)")
	parser.add_argument("--local-scope",	action="store_true",	help="Detect duplicates per folder only (skips interactive prompt)")
	parser.add_argument("--dry-run",		action="store_true",	help="Simulate without moving any files (skips interactive prompt)")
	parser.add_argument("--no-dry-run",		action="store_true",	help="Actually move files (skips interactive prompt)")
	args = parser.parse_args()
	try:
		folder_input = args.link or input("Path to the folder to analyse: ").strip()
	except (EOFError, KeyboardInterrupt):
		print()
		logger.info("Aborted.")
		sys.exit(0)
	if not folder_input:
		logger.error("[ERROR] No path provided.")
		sys.exit(1)
	try:
		folder_path = Path(folder_input).expanduser().resolve()
	except Exception as e:
		logger.error(f"[ERROR] Invalid path '{folder_input}': {e}")
		sys.exit(1)
	if not folder_path.exists():
		logger.error(f"[ERROR] Path does not exist: '{folder_path}'")
		sys.exit(1)
	if not folder_path.is_dir():
		logger.error(f"[ERROR] Path is not a directory: '{folder_path}'")
		sys.exit(1)
	if not os.access(folder_path, os.R_OK):
		logger.error(f"[ERROR] No read permission on: '{folder_path}'")
		sys.exit(1)
	if args.recursive:
		recursive = True
	elif args.no_recursive:
		recursive = False
	else:
		recursive = ask("Also scan subfolders?", default=False)
	if recursive:
		if args.flat:
			flat = True
		elif args.no_flat:
			flat = False
		else:
			flat = ask("Copy duplicates flat into 'copies/'?", default=True)
	else:
		flat = True
	if recursive:
		if args.global_scope:
			global_scope = True
		elif args.local_scope:
			global_scope = False
		else:
			global_scope = ask("Detect duplicates across all folders?", default=False)
	else:
		global_scope = False
	if args.dry_run:
		dry_run = True
	elif args.no_dry_run:
		dry_run = False
	else:
		dry_run = ask("Simulate without moving files?", default=False)
	detect_and_move_copies(folder_path, recursive=recursive, flat=flat, dry_run=dry_run, global_scope=global_scope)

if __name__ == "__main__":
	main()
