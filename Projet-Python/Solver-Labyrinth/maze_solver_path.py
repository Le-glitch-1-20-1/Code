import cv2
import numpy as np
from collections import deque

DEFAULT_CONFIG = {
	"INPUT_IMAGE":			"labyrinthe/mini.png",
	"OUTPUT_IMAGE":			"labyrinthe/maze_solved.png",
	"INFO_FILE":			"labyrinthe/maze_info.txt",
	"PATH_FILE":			"labyrinthe/maze_path.txt",
	"INTERSECTION_COLOR":	(0, 0, 0),
	"TOL":					30,
}

def parse_info(file_path: str) -> dict:
	if not file_path:
		raise ValueError("Info file path is empty.")
	if not __import__("os").path.exists(file_path):
		raise FileNotFoundError(
			f"Info file not found: {file_path}\n"
			"Run maze generation or capture first."
		)
	info = {}
	with open(file_path, "r", encoding="utf-8") as f:
		for lineno, line in enumerate(f, 1):
			line = line.strip()
			if not line:
				continue
			if ":" not in line:
				raise ValueError(
					f"Malformed info file (line {lineno}): {line!r}\n"
					"Expected format:  Key: value"
				)
			key, value = line.split(":", 1)
			info[key.strip()] = value.strip()
	return info

def _is_black(pixel: np.ndarray, tol: int, target: np.ndarray) -> bool:
	return bool(np.all(np.abs(pixel.astype(int) - target.astype(int)) <= tol))

def build_grid(img_path: str, cell_size: int, tol: int, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
	if not __import__("os").path.exists(img_path):
		raise FileNotFoundError(
			f"Maze image not found: {img_path}\n"
			"Run generation or capture first."
		)
	if cell_size < 1:
		raise ValueError(f"cell_size must be >= 1 (got {cell_size})")
	img  = cv2.imread(img_path)
	if img is None:
		raise OSError(f"OpenCV could not read image: {img_path}")
	h, w = img.shape[:2]
	rows = h // cell_size
	cols = w // cell_size
	if rows == 0 or cols == 0:
		raise ValueError(
			f"Image ({w}x{h}) is too small for cell_size={cell_size}. "
			"The maze may not have been generated correctly."
		)
	grid = np.zeros((rows, cols), dtype=int)
	for r in range(rows):
		for c in range(cols):
			cell	  = img[r * cell_size:(r + 1) * cell_size,
							c * cell_size:(c + 1) * cell_size]
			black_mask = np.apply_along_axis(
				lambda px: _is_black(px, tol, target), 2, cell
			)
			grid[r, c] = 1 if np.sum(black_mask) > (cell_size * cell_size) // 2 else 0
	return grid, img

def _can_connect(cell1: tuple, cell2: tuple, img: np.ndarray, cell_size: int, tol: int) -> bool:
	x1, y1 = cell1
	x2, y2 = cell2
	cx1 = x1 * cell_size + cell_size // 2
	cy1 = y1 * cell_size + cell_size // 2
	cx2 = x2 * cell_size + cell_size // 2
	cy2 = y2 * cell_size + cell_size // 2
	segment	= img[min(cy1, cy2):max(cy1, cy2) + 1,
					 min(cx1, cx2):max(cx1, cx2) + 1]
	black_mask = np.all(
		np.abs(segment.astype(int) - np.array([0, 0, 0])) <= tol,
		axis=2,
	)
	return not np.any(black_mask)

def build_graph(grid: np.ndarray, img: np.ndarray, cell_size: int, tol: int) -> dict:
	rows, cols = grid.shape
	graph	  = {}
	for r in range(rows):
		for c in range(cols):
			if grid[r, c] == 1:
				continue
			neighbors = []
			for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
				nx, ny = c + dx, r + dy
				if 0 <= nx < cols and 0 <= ny < rows and grid[ny, nx] == 0:
					if _can_connect((c, r), (nx, ny), img, cell_size, tol):
						neighbors.append((nx, ny))
			graph[(c, r)] = neighbors
	return graph

def shortest_path(graph: dict, start: tuple, end: tuple) -> list | None:
	if start not in graph:
		raise ValueError(
			f"Start cell {start} is not in the graph. "
			"It may be a wall or outside the maze."
		)
	if end not in graph:
		raise ValueError(
			f"End cell {end} is not in the graph. "
			"It may be a wall or outside the maze."
		)
	visited = set()
	parent  = {}
	queue   = deque([start])
	visited.add(start)
	while queue:
		node = queue.popleft()
		if node == end:
			path = []
			while node != start:
				path.append(node)
				node = parent[node]
			path.append(start)
			path.reverse()
			return path
		for nb in graph.get(node, []):
			if nb not in visited:
				visited.add(nb)
				parent[nb] = node
				queue.append(nb)
	return None

def draw_path(original_img: np.ndarray, path: list, cell_size: int, wall_thickness: int) -> np.ndarray:
	img	= np.ones_like(original_img) * 255
	offset = wall_thickness // 2
	for (x, y) in path:
		cv2.rectangle(
			img,
			(x * cell_size + offset,			y * cell_size + offset),
			(x * cell_size + cell_size - offset, y * cell_size + cell_size - offset),
			(0, 0, 255),
			-1,
		)
	mask = np.all(original_img <= np.array([180, 180, 180]), axis=2)
	for c in range(3):
		img[:, :, c][mask] = original_img[:, :, c][mask]
	return img

def run_path_solver(config_overrides: dict | None = None) -> list | None:
	cfg = DEFAULT_CONFIG.copy()
	if config_overrides:
		cfg.update(config_overrides)
	info		   = parse_info(cfg["INFO_FILE"])
	cell_size	  = int(info.get("Cell size",	  info.get("Taille case",	   20)))
	wall_thickness = int(info.get("Wall thickness", info.get("Epaisseur lignes",   2)))
	tol			= int(cfg["TOL"])
	target		 = np.array(cfg["INTERSECTION_COLOR"])
	start_raw = info.get("Start cell", info.get("Cellule depart", "0,0"))
	end_raw   = info.get("End cell",   info.get("Cellule fraise", "0,0"))
	try:
		start_cell = tuple(map(int, start_raw.split(",")))
		end_cell   = tuple(map(int, end_raw.split(",")))
	except ValueError as exc:
		raise ValueError(
			f"Cannot parse cell coordinates from info file: {exc}\n"
			f"  Start cell raw: {start_raw!r}\n"
			f"  End cell raw:   {end_raw!r}"
		) from exc
	grid, img = build_grid(cfg["INPUT_IMAGE"], cell_size, tol, target)
	graph	 = build_graph(grid, img, cell_size, tol)
	path = shortest_path(graph, start_cell, end_cell)
	if path is None:
		return None
	import os
	path_dir = os.path.dirname(cfg["PATH_FILE"])
	if path_dir:
		os.makedirs(path_dir, exist_ok=True)
	with open(cfg["PATH_FILE"], "w", encoding="utf-8") as f:
		for cell in path:
			f.write(f"{cell[0]},{cell[1]}\n")
	solved_img = draw_path(img, path, cell_size, wall_thickness)
	out_dir	= os.path.dirname(cfg["OUTPUT_IMAGE"])
	if out_dir:
		os.makedirs(out_dir, exist_ok=True)
	if not cv2.imwrite(cfg["OUTPUT_IMAGE"], solved_img):
		raise OSError(f"Failed to write solved image to: {cfg['OUTPUT_IMAGE']}")
	return path
