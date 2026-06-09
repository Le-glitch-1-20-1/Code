import os
import random
import cv2
import numpy		as np
from collections	import deque

SIZES = {
	"mini":			{"cols": 10,  "rows": 10,  "cell": 20, "wall": 2},
	"medium":		{"cols": 20,  "rows": 20,  "cell": 18, "wall": 2},
	"mighty":		{"cols": 30,  "rows": 30,  "cell": 16, "wall": 2},
	"mega":			{"cols": 40,  "rows": 40,  "cell": 14, "wall": 2},
	"monolithic":	{"cols": 50,  "rows": 50,  "cell": 12, "wall": 2},
	"magnificent":	{"cols": 60,  "rows": 60,  "cell": 10, "wall": 2},
	"maligned":		{"cols": 70,  "rows": 70,  "cell":  8, "wall": 2},
	"monstrous":	{"cols": 100, "rows": 100, "cell":  6, "wall": 2},
	"mammoth":		{"cols": 120, "rows": 120, "cell":  5, "wall": 2},
	"megalomaniac":	{"cols": 150, "rows": 150, "cell":  4, "wall": 2},
}

MAZE_URLS = {name: f"https://maze.toys/mazes/{name}/" for name in SIZES}
DAILY_URLS = {name: f"https://maze.toys/mazes/{name}/daily/" for name in SIZES}
DEFAULT_INFO_FILE  = "labyrinthe/maze_info.txt"
DEFAULT_OUTPUT_IMG = "labyrinthe/mini.png"
COLOR_WALL  = (0,   0,   0)
COLOR_START = (0,   0,   200)
COLOR_END   = (0,   0,   200)


def make_maze(cols: int, rows: int, seed: int | None = None) -> set:
	if cols < 1 or rows < 1:
		raise ValueError(f"Invalid maze dimensions: {cols}x{rows} (must be >= 1)")
	if seed is not None:
		random.seed(seed)
	visited, passages = set(), set()

	def neighbors(c, r):
		out = []
		if c + 1 < cols: out.append((c + 1, r, "E"))
		if c - 1 >= 0:   out.append((c - 1, r, "W"))
		if r + 1 < rows: out.append((c, r + 1, "S"))
		if r - 1 >= 0:   out.append((c, r - 1, "N"))
		return out
	stack = [(0, 0)]
	visited.add((0, 0))
	while stack:
		c, r = stack[-1]
		nbrs = [(nc, nr, d) for nc, nr, d in neighbors(c, r) if (nc, nr) not in visited]
		if not nbrs:
			stack.pop()
			continue
		nc, nr, d = random.choice(nbrs)
		if   d == "E": passages.add((c,  r,  "E"))
		elif d == "W": passages.add((nc, nr, "E"))
		elif d == "S": passages.add((c,  r,  "S"))
		elif d == "N": passages.add((nc, nr, "S"))
		visited.add((nc, nr))
		stack.append((nc, nr))
	return passages

def pick_far_cell(cols: int, rows: int, sc: int, sr: int, passages: set) -> tuple:
	def adj(c, r):
		nbrs = []
		if (c, r,   "E") in passages and c + 1 < cols: nbrs.append((c + 1, r))
		if (c - 1, r, "E") in passages and c - 1 >= 0:   nbrs.append((c - 1, r))
		if (c, r,   "S") in passages and r + 1 < rows: nbrs.append((c, r + 1))
		if (c, r - 1, "S") in passages and r - 1 >= 0:   nbrs.append((c, r - 1))
		return nbrs
	dist  = {(sc, sr): 0}
	queue = deque([(sc, sr)])
	while queue:
		c, r = queue.popleft()
		for nc, nr in adj(c, r):
			if (nc, nr) not in dist:
				dist[(nc, nr)] = dist[(c, r)] + 1
				queue.append((nc, nr))
	return max(dist, key=dist.get)

def draw_maze(passages: set, cols: int, rows: int, cell_size: int, wall_thick: int) -> np.ndarray:
	t   = wall_thick
	img = np.ones((rows * cell_size + t, cols * cell_size + t, 3), dtype=np.uint8) * 255
	img[0:t, :] = img[-t:, :] = img[:, 0:t] = img[:, -t:] = COLOR_WALL
	for r in range(rows):
		for c in range(cols):
			if r < rows - 1 and (c, r, "S") not in passages:
				img[(r + 1) * cell_size:(r + 1) * cell_size + t,
					c * cell_size:(c + 1) * cell_size + t] = COLOR_WALL
			if c < cols - 1 and (c, r, "E") not in passages:
				img[r * cell_size:(r + 1) * cell_size + t,
					(c + 1) * cell_size:(c + 1) * cell_size + t] = COLOR_WALL
	return img

def place_marker(img: np.ndarray, col: int, row: int, cell_size: int, wall_thick: int, color: tuple) -> None:
	t  = wall_thick
	x0 = col * cell_size + t
	y0 = row * cell_size + t
	img[y0:y0 + cell_size - t, x0:x0 + cell_size - t] = color

def generate(
	cols: int,
	rows: int,
	cell_size: int,
	wall_thick: int,
	output_img: str = DEFAULT_OUTPUT_IMG,
	info_file: str  = DEFAULT_INFO_FILE,
	seed: int | None = None,
) -> tuple[str, str]:
	if cols < 2 or rows < 2:
		raise ValueError(f"Maze must be at least 2x2 (got {cols}x{rows})")
	if cell_size < 4:
		raise ValueError(f"Cell size must be at least 4px (got {cell_size})")
	if wall_thick < 1:
		raise ValueError(f"Wall thickness must be at least 1px (got {wall_thick})")
	if wall_thick >= cell_size:
		raise ValueError(f"Wall thickness ({wall_thick}) must be smaller than cell size ({cell_size})")
	out_dir = os.path.dirname(output_img)
	if out_dir:
		os.makedirs(out_dir, exist_ok=True)
	info_dir = os.path.dirname(info_file)
	if info_dir:
		os.makedirs(info_dir, exist_ok=True)
	passages			= make_maze(cols, rows, seed=seed)
	end_col, end_row	= pick_far_cell(cols, rows, 0, 0, passages)
	img				 = draw_maze(passages, cols, rows, cell_size, wall_thick)
	place_marker(img, 0, 0, cell_size, wall_thick, COLOR_START)
	place_marker(img, end_col, end_row, cell_size, wall_thick, COLOR_END)
	if not cv2.imwrite(output_img, img):
		raise OSError(f"Failed to write image to: {output_img}")
	cx_s = cell_size // 2
	cy_s = cell_size // 2
	cx_e = end_col * cell_size + cell_size // 2
	cy_e = end_row * cell_size + cell_size // 2
	with open(info_file, "w", encoding="utf-8") as f:
		f.write(f"Wall thickness: {wall_thick}\n")
		f.write(f"Cell size: {cell_size}\n")
		f.write(f"Offset X: 0\n")
		f.write(f"Offset Y: 0\n")
		f.write(f"Start coord: {cx_s}, {cy_s}\n")
		f.write(f"End coord: {cx_e}, {cy_e}\n")
		f.write(f"Start cell: 0,0\n")
		f.write(f"End cell: {end_col},{end_row}\n")
	return output_img, info_file
