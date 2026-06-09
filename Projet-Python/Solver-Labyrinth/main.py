#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys

_CORE_FILES = [
	"generate_maze.py",
	"maze_solver.py",
	"maze_solver_path.py",
	"mover.py",
	"menu.py",
]

def _check_files() -> None:
	missing = [f for f in _CORE_FILES if not os.path.exists(f)]
	if missing:
		print(f"[ERROR] Missing required files: {', '.join(missing)}")
		sys.exit(1)

_check_files()

try:
	from generate_maze	import generate, SIZES, MAZE_URLS, DAILY_URLS
	from maze_solver_path import run_path_solver
	from menu import (
		splash, section, ok, err, info,
		ask_int, ask_float, ask_text, ask_confirm,
		with_spinner, wait_for_key, move_progress, success_panel,
		menu_main, menu_generate, menu_site,
	)
except ImportError as exc:
	print(f"[ERROR] Internal import failed: {exc}")
	sys.exit(1)

def do_generate(p: dict) -> None:
	section("Generation")
	if p["size"] == "custom":
		for key in ("cols", "rows", "cell", "wall"):
			if not p.get(key):
				err(f"--size custom requires --{key}")
				sys.exit(1)
		params = {
			"cols": p["cols"],
			"rows": p["rows"],
			"cell": p["cell"],
			"wall": p["wall"],
		}
	else:
		if p["size"] not in SIZES:
			err(f"Unknown size: {p['size']}  (valid: {', '.join(SIZES)})")
			sys.exit(1)
		params = dict(SIZES[p["size"]])
		for key in ("cols", "rows", "cell", "wall"):
			if p.get(key):
				params[key] = p[key]
	label = (
		f"{params['cols']}×{params['rows']}  —  "
		f"cell {params['cell']}px  wall {params['wall']}px"
	)
	if p.get("seed") is not None:
		label += f"  —  seed {p['seed']}"
	info(label)
	try:
		with_spinner(
			"Generating maze…",
			lambda: generate(
				cols=params["cols"],
				rows=params["rows"],
				cell_size=params["cell"],
				wall_thick=params["wall"],
				seed=p.get("seed"),
			),
		)
	except ValueError as exc:
		err(f"Invalid parameters: {exc}")
		sys.exit(1)
	except OSError as exc:
		err(f"Could not write output files: {exc}")
		sys.exit(1)
	except Exception as exc:
		err(f"Generation failed: {exc}")
		sys.exit(1)
	ok("Maze generated")

def do_solve(tol: int | None = None) -> list | None:
	section("Solving")
	overrides = {}
	if tol is not None:
		if not (0 <= tol <= 255):
			err(f"Tolerance must be between 0 and 255 (got {tol})")
			sys.exit(1)
		overrides["TOL"] = tol
	try:
		path = with_spinner("Calculating shortest path…", lambda: run_path_solver(config_overrides=overrides))
	except FileNotFoundError as exc:
		err(f"Missing file: {exc}")
		sys.exit(1)
	except ValueError as exc:
		err(f"Data error: {exc}")
		sys.exit(1)
	except OSError as exc:
		err(f"Could not write output files: {exc}")
		sys.exit(1)
	except Exception as exc:
		err(f"Solving failed: {exc}")
		sys.exit(1)
	if path is None:
		err("No path found in this maze.")
		sys.exit(1)
	ok(f"Path found  —  {len(path)} steps")
	return path

def do_capture(url: str | None, image_path: str | None) -> None:
	try:
		from maze_solver import run_maze_solver
	except ImportError as exc:
		err(f"maze_solver module unavailable: {exc}")
		sys.exit(1)
	section("Capture")
	if image_path:
		if not os.path.exists(image_path):
			err(f"Image not found: {image_path}")
			sys.exit(1)
		info(f"Source: {image_path}")
		try:
			with_spinner("Analysing image…", lambda: run_maze_solver(img_source="file", image_path=image_path))
		except FileNotFoundError as exc:
			err(f"Missing file: {exc}")
			sys.exit(1)
		except ImportError as exc:
			err(str(exc))
			sys.exit(1)
		except RuntimeError as exc:
			err(f"Detection failed: {exc}")
			sys.exit(1)
		except Exception as exc:
			err(f"Image analysis failed: {exc}")
			sys.exit(1)
	else:
		try:
			import selenium
		except ImportError:
			err("The 'selenium' package is required for URL capture.\n  Install with: pip install selenium webdriver-manager")
			sys.exit(1)
		if not url:
			err("No URL provided.")
			sys.exit(1)
		info(f"URL: {url}")
		try:
			with_spinner("Capturing maze from browser…", lambda: run_maze_solver(img_source="url", url=url))
		except ImportError as exc:
			err(str(exc))
			sys.exit(1)
		except RuntimeError as exc:
			err(f"Detection failed: {exc}")
			sys.exit(1)
		except Exception as exc:
			err(f"Capture failed: {exc}")
			sys.exit(1)
	ok("Maze analysed")

def do_move(speed: float) -> None:
	try:
		from mover import execute_moves
	except ImportError as exc:
		err(f"mover module unavailable: {exc}")
		sys.exit(1)
	if speed < 0:
		err(f"Speed must be >= 0 (got {speed})")
		sys.exit(1)
	section("Movement")
	wait_for_key("m")
	try:
		move_progress(lambda: execute_moves(speed=speed))
	except FileNotFoundError as exc:
		err(f"Missing file: {exc}")
		sys.exit(1)
	except ImportError as exc:
		err(str(exc))
		sys.exit(1)
	except ValueError as exc:
		err(f"Data error: {exc}")
		sys.exit(1)
	except Exception as exc:
		err(f"Movement failed: {exc}")
		sys.exit(1)
	ok("Movement complete")

def run_generate(p: dict) -> None:
	do_generate(p)
	do_solve()
	success_panel("[dim]Maze solved. Image saved to [cyan]labyrinthe/maze_solved.png[/][/]")

def run_site(p: dict) -> None:
	do_capture(p["url"], p["image_path"])
	do_solve(tol=p.get("tol"))
	do_move(p["speed"])

def _build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
	sub = parser.add_subparsers(dest="mode")
	pg = sub.add_parser("generate")
	pg.add_argument("--size", choices=list(SIZES.keys()) + ["custom"], default="mini")
	pg.add_argument("--cols", type=int)
	pg.add_argument("--rows", type=int)
	pg.add_argument("--cell", type=int)
	pg.add_argument("--wall", type=int)
	pg.add_argument("--seed", type=int)
	ps = sub.add_parser("site")
	ps.add_argument("--url",   type=str,   default=None)
	ps.add_argument("--image", type=str,   default=None, dest="image_path")
	ps.add_argument("--tol",   type=int,   default=None)
	ps.add_argument("--speed", type=float, default=0.1)
	return parser

def main() -> None:
	parser = _build_parser()
	args   = parser.parse_args()
	if args.mode is None:
		try:
			mode = menu_main()
		except KeyboardInterrupt:
			print("\nInterrupted.")
			sys.exit(0)
		if mode == "quit":
			info("Goodbye.")
			sys.exit(0)
		try:
			if mode == "generate":
				p = menu_generate()
				run_generate(p)
			else:
				p = menu_site()
				run_site(p)
		except KeyboardInterrupt:
			print("\nInterrupted.")
			sys.exit(0)
		return
	if args.mode == "generate":
		if args.size == "custom" and not all([args.cols, args.rows, args.cell, args.wall]):
			parser.error("--size custom requires --cols, --rows, --cell and --wall")
		p = dict(
			size=args.size,
			cols=args.cols,
			rows=args.rows,
			cell=args.cell,
			wall=args.wall,
			seed=args.seed,
		)
		run_generate(p)
	elif args.mode == "site":
		if not args.url and not args.image_path:
			parser.error("Specify --url or --image")
		p = dict(
			url=args.url,
			image_path=args.image_path,
			tol=args.tol,
			speed=args.speed,
		)
		run_site(p)

if __name__ == "__main__":
	main()
