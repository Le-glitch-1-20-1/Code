#!/usr/bin/env python3

import sys
import os
import warnings
import logging
import argparse
from pathlib					import Path
from moviepy.video.io.VideoFileClip	import VideoFileClip
from tqdm					import tqdm

warnings.filterwarnings("ignore", category=UserWarning)
VIDEO_EXTENSIONS = (
	".mov", ".mkv", ".avi", ".wmv", ".flv", ".webm",
	".m4v", ".3gp", ".mpg", ".mpeg", ".m2ts", ".mts", ".vob"
)

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

def resolve_path(raw: str) -> Path:
	return Path(raw).expanduser().resolve()

def collect_files(root: Path, recursive: bool) -> list[str]:
	found = []
	with tqdm(desc="Scanning", unit="file", leave=False) as pbar:
		if recursive:
			for dirpath, _, files in os.walk(root):
				for filename in files:
					ext = os.path.splitext(filename)[1].lower()
					if ext in VIDEO_EXTENSIONS:
						found.append(os.path.join(dirpath, filename))
						pbar.update(1)
		else:
			for filename in os.listdir(root):
				ext = os.path.splitext(filename)[1].lower()
				if ext in VIDEO_EXTENSIONS:
					found.append(os.path.join(root, filename))
					pbar.update(1)
	return found

def convert_file(file_path: str, dry_run: bool, delete_original: bool) -> str:
	directory	= os.path.dirname(file_path)
	name_part	= os.path.splitext(os.path.basename(file_path))[0]
	target_path	= os.path.join(directory, f"{name_part}.mp4")
	if os.path.exists(target_path):
		return "skipped"
	if dry_run:
		return "success"
	try:
		with VideoFileClip(file_path) as clip:
			clip.write_videofile(
				target_path,
				codec="libx264",
				audio_codec="aac",
				logger=None,
			)
		if delete_original:
			os.remove(file_path)
		return "success"
	except Exception as e:
		logging.error("Failed on %s: %s", file_path, e)
		return "error"

def run(root: Path, dry_run: bool, delete_original: bool, recursive: bool) -> None:
	videos = collect_files(root, recursive)
	if not videos:
		logger.info("No video files found in this folder.")
		return
	prefix = "[DRY RUN] " if dry_run else ""
	logger.info(f"\n{prefix}Processing {len(videos)} video(s) to convert")
	counts = {"success": 0, "skipped": 0, "error": 0}
	bar_fmt = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
	try:
		with tqdm(videos, desc="Converting", unit="vid", bar_format=bar_fmt) as pbar:
			for file_path in pbar:
				pbar.set_postfix_str(os.path.basename(file_path)[:35], refresh=False)
				result = convert_file(file_path, dry_run, delete_original)
				counts[result] += 1
	except KeyboardInterrupt:
		logger.info("\nKeyboard interrupt detected. Exiting.")
	logger.info(f"\n{prefix}{counts['success']} succeeded, {counts['skipped']} skipped, {counts['error']} failed.")
	if counts["error"]:
		logger.info("Details: video_errors.log")

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
	delete_original	= ask("Delete originals after conversion?", default=False)
	dry_run			= ask("Simulate without converting files?", default=False)
	return dict(root=root, dry_run=dry_run, delete_original=delete_original, recursive=recursive)

def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser()
	parser.add_argument("--link",			metavar="PATH",			help="Path to the folder to process (skips interactive prompt)")
	parser.add_argument("--delete",			action="store_true",	help="Delete original files after conversion (skips interactive prompt)")
	parser.add_argument("--no-delete",		action="store_true",	help="Keep original files after conversion (skips interactive prompt)")
	parser.add_argument("--dry-run",		action="store_true",	help="Simulate without modifying any file (skips interactive prompt)")
	parser.add_argument("--no-dry-run",		action="store_true",	help="Actually convert files (skips interactive prompt)")
	parser.add_argument("--recursive",		action="store_true",	help="Include subfolders (skips interactive prompt)")
	parser.add_argument("--no-recursive",	action="store_true",	help="Current folder only, no subfolders (skips interactive prompt)")
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
		delete_original	= True if args.delete else False if args.no_delete else True
		dry_run			= True if args.dry_run else False if args.no_dry_run else False
		recursive		= True if args.recursive else False if args.no_recursive else True
		run(root=root, dry_run=dry_run, delete_original=delete_original, recursive=recursive)
	else:
		cfg = interactive_wizard()
		run(**cfg)

if __name__ == "__main__":
	main()
