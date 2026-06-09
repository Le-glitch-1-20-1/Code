import time

try:
	from pynput.keyboard import Key, Controller
	_PYNPUT_AVAILABLE = True
except ImportError:
	_PYNPUT_AVAILABLE = False

def _check_pynput() -> None:
	if not _PYNPUT_AVAILABLE:
		raise ImportError(
			"pynput is required for keyboard control.\n"
			"  Install with: pip install pynput"
		)

def read_coords(filename: str) -> list[tuple[int, int]]:
	import os
	if not os.path.exists(filename):
		raise FileNotFoundError(
			f"Path file not found: {filename}\n"
			"Run maze solving first."
		)
	coords = []
	with open(filename, "r", encoding="utf-8") as f:
		for lineno, line in enumerate(f, 1):
			line = line.strip()
			if not line:
				continue
			parts = line.split(",")
			if len(parts) != 2:
				raise ValueError(
					f"Malformed path file at line {lineno}: {line!r}\n"
					"Expected format: col,row"
				)
			try:
				x, y = int(parts[0]), int(parts[1])
			except ValueError:
				raise ValueError(f"Non-integer values at line {lineno}: {line!r}")
			coords.append((x, y))
	if not coords:
		raise ValueError(f"Path file is empty: {filename}")
	return coords

def get_direction(p1: tuple, p2: tuple):
	_check_pynput()
	dx, dy = p2[0] - p1[0], p2[1] - p1[1]
	if   dx ==  1 and dy == 0: return Key.right
	if   dx == -1 and dy == 0: return Key.left
	if   dy ==  1 and dx == 0: return Key.down
	if   dy == -1 and dx == 0: return Key.up
	return None

def execute_moves(path_file: str = "labyrinthe/maze_path.txt", speed: float = 0.1) -> None:
	_check_pynput()
	if speed < 0:
		raise ValueError(f"Speed must be >= 0 (got {speed})")
	coords   = read_coords(path_file)
	keyboard = Controller()
	for i in range(len(coords) - 1):
		direction = get_direction(coords[i], coords[i + 1])
		if direction is None:
			continue
		keyboard.press(direction)
		keyboard.release(direction)
		if speed > 0:
			time.sleep(speed)
