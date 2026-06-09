import os
import time
import base64
import cv2
import numpy as np

try:
	from PIL import Image
	from io  import BytesIO
	_PIL_AVAILABLE = True
except ImportError:
	_PIL_AVAILABLE = False

try:
	from selenium							import webdriver
	from selenium.webdriver.chrome.service	import Service
	from webdriver_manager.chrome			import ChromeDriverManager
	_SELENIUM_AVAILABLE = True
except ImportError:
	_SELENIUM_AVAILABLE = False

DEFAULT_CONFIG = {
	"URL":					"https://maze.toys/mazes/mini/",
	"WAIT_TIME":			2,
	"OUTPUT_PATH":			"labyrinthe/maze.png",
	"OUTPUT_IMAGE":			"labyrinthe/mini.png",
	"INFO_PATH":			"labyrinthe/maze_info.txt",
	"WHITE_THRESHOLD":		240,
	"BLACK_THRESHOLD":		50,
	"GRID_COLOR":			(180, 180, 180),
	"INTERSECTION_COLOR":	(0, 0, 0),
	"MAX_GRAY_RATIO":		0.5,
	"MAX_ITER":				15,
}

def _ensure_dirs(cfg: dict) -> None:
	for key in ("OUTPUT_PATH", "OUTPUT_IMAGE", "INFO_PATH"):
		path = cfg.get(key, "")
		directory = os.path.dirname(path)
		if directory:
			os.makedirs(directory, exist_ok=True)

def _ensure_rgb(img):
	if not _PIL_AVAILABLE:
		raise ImportError("Pillow is required. Install it with: pip install Pillow")
	if img.mode in ("RGBA", "LA"):
		bg = Image.new("RGB", img.size, (255, 255, 255))
		bg.paste(img, mask=img.split()[3])
		return bg
	return img.convert("RGB")

def _extract_canvas_b64(driver) -> bytes:
	js = (
		"var canvas = document.querySelector('canvas');"
		"if (!canvas) return null;"
		"return canvas.toDataURL('image/png').substring(22);"
	)
	data = driver.execute_script(js)
	if data is None:
		raise RuntimeError("No <canvas> element found on the page.")
	return base64.b64decode(data)

def _find_biggest_contour(mask: np.ndarray):
	cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	return max(cnts, key=cv2.contourArea) if cnts else None

def _draw_grid_mask(cell: int, thick: int, shape: tuple, ox: int, oy: int) -> np.ndarray:
	h, w = shape
	mask = np.zeros((h, w), dtype=np.uint8)
	for x in range(0, w, cell):
		for t in range(thick):
			xx = x + ox + t
			if 0 <= xx < w:
				mask[:, xx] = 1
	for y in range(0, h, cell):
		for t in range(thick):
			yy = y + oy + t
			if 0 <= yy < h:
				mask[yy, :] = 1
	return mask

def run_maze_solver(img_source: str = "url", url: str | None = None, image_path: str | None = None, config_overrides: dict | None = None) -> None:
	cfg = DEFAULT_CONFIG.copy()
	if config_overrides:
		cfg.update(config_overrides)
	_ensure_dirs(cfg)
	if img_source == "file":
		if not image_path:
			raise ValueError("image_path must be provided when img_source='file'")
		if not os.path.exists(image_path):
			raise FileNotFoundError(f"Image not found: {image_path}")
		if not _PIL_AVAILABLE:
			raise ImportError("Pillow is required. Install it with: pip install Pillow")
		pil_img = Image.open(image_path)
		pil_img = _ensure_rgb(pil_img)
		cv_img  = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
	elif img_source == "url":
		if not _SELENIUM_AVAILABLE:
			raise ImportError(
				"selenium and webdriver-manager are required for URL capture.\n"
				"  Install with: pip install selenium webdriver-manager"
			)
		if not _PIL_AVAILABLE:
			raise ImportError("Pillow is required. Install it with: pip install Pillow")
		if not url:
			url = cfg["URL"]
		options = webdriver.ChromeOptions()
		options.add_argument("--headless")
		options.add_argument("--no-sandbox")
		options.add_argument("--disable-dev-shm-usage")
		options.add_argument("--window-size=1920,1080")
		driver = webdriver.Chrome(
			service=Service(ChromeDriverManager().install()),
			options=options,
		)
		try:
			driver.get(url)
			time.sleep(cfg["WAIT_TIME"])
			png_bytes = _extract_canvas_b64(driver)
		finally:
			driver.quit()
		pil_img = Image.open(BytesIO(png_bytes))
		pil_img = _ensure_rgb(pil_img)
		cv_img  = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
	else:
		raise ValueError(f"Unknown img_source: {img_source!r}. Expected 'url' or 'file'.")
	hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
	low_r1, high_r1 = np.array([0, 100, 100]), np.array([10, 255, 255])
	mask_start  = cv2.inRange(hsv, low_r1, high_r1)
	cnt_start   = _find_biggest_contour(mask_start)
	if cnt_start is None:
		raise RuntimeError(
			"Start square not found. The image may not contain a valid maze, "
			"or the red marker is missing."
		)
	x_start_rect, y_start_rect, w_start, h_start = cv2.boundingRect(cnt_start)
	start_center = (x_start_rect + w_start // 2, y_start_rect + h_start // 2)
	img  = cv_img.copy()
	h, w = img.shape[:2]
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	mid_x	 = w // 2
	thickness = 0
	for y in range(h):
		if gray[y, mid_x] < cfg["BLACK_THRESHOLD"]:
			thickness += 1
		else:
			break
	thickness = max(thickness, 1)
	OFFSET_X = -(thickness // 2)
	OFFSET_Y = -(thickness // 2)
	line_up   = h // 2 - h // 6
	line_down = h // 2 + h // 6
	stop_x	= w - w // 6

	def measure_white_runs(scan_y: int) -> list[tuple[int, int]]:
		runs, count, start_x = [], 0, None
		for x in range(stop_x):
			if gray[scan_y, x] > cfg["WHITE_THRESHOLD"]:
				if count == 0:
					start_x = x
				count += 1
			else:
				if count > 0:
					runs.append((start_x, count))
				count = 0
		if count > 0:
			runs.append((start_x, count))
		return runs
	all_runs = sorted(
		measure_white_runs(line_up) + measure_white_runs(line_down),
		key=lambda r: r[1],
	)
	if len(all_runs) < 2:
		raise RuntimeError(
			"Could not detect cell size – not enough white regions found. "
			"The image may be too dark or not a valid maze."
		)
	_run_start, cell_size = all_runs[1]
	current_cell		  = cell_size
	white_mask		= gray > cfg["WHITE_THRESHOLD"]
	red_mask		= cv2.inRange(img, np.array([0, 0, 100]), np.array([80, 80, 255])) > 0
	mask_visible	= white_mask | red_mask
	out				= img.copy()
	for _iteration in range(cfg["MAX_ITER"]):
		temp		= img.copy()
		grid_mask	= _draw_grid_mask(current_cell, thickness, (h, w), OFFSET_X, OFFSET_Y)
		temp[mask_visible & (grid_mask == 1)] = cfg["GRID_COLOR"]
		total		= np.sum(grid_mask == 1)
		visible		= np.sum((grid_mask == 1) & mask_visible)
		if total == 0:
			break
		if visible / total <= cfg["MAX_GRAY_RATIO"]:
			out = temp
			break
		current_cell += 1
	for x in range(0, w, current_cell):
		for y in range(0, h, current_cell):
			for dx in range(thickness):
				for dy in range(thickness):
					xx, yy = x + dx + OFFSET_X, y + dy + OFFSET_Y
					if 0 <= xx < w and 0 <= yy < h:
						out[yy, xx] = cfg["INTERSECTION_COLOR"]
	out[:thickness, :]  = 0
	out[-thickness:, :] = 0
	out[:, :thickness]  = 0
	out[:, -thickness:] = 0
	low2, high2   = np.array([170, 100, 100]), np.array([180, 255, 255])
	mask_straw	= cv2.bitwise_or(
		cv2.inRange(hsv, low_r1, high_r1),
		cv2.inRange(hsv, low2,   high2),
	)
	kernel		= cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
	mask_straw	= cv2.morphologyEx(mask_straw, cv2.MORPH_CLOSE, kernel, iterations=2)
	mask_straw	= cv2.morphologyEx(mask_straw, cv2.MORPH_OPEN,  kernel, iterations=1)
	cnts, _	   = cv2.findContours(mask_straw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

	def _is_far_from_start(cnt, sx, sy, sw, sh, min_dist: int = 5) -> bool:
		x, y, cw, ch = cv2.boundingRect(cnt)
		return (
			x + cw < sx - min_dist
			or x   > sx + sw + min_dist
			or y + ch < sy - min_dist
			or y   > sy + sh + min_dist
		)
	valid_cnts = [
		c for c in cnts
		if _is_far_from_start(c, x_start_rect, y_start_rect, w_start, h_start)
	]
	if not valid_cnts:
		raise RuntimeError(
			"End marker not detected. The maze image may be missing the "
			"destination marker, or the colour thresholds need adjustment."
		)
	cnt_straw = max(valid_cnts, key=cv2.contourArea)
	M		 = cv2.moments(cnt_straw)
	if abs(M.get("m00", 0)) < 1e-6:
		x_s, y_s, w_s, h_s = cv2.boundingRect(cnt_straw)
		cx, cy = x_s + w_s // 2, y_s + h_s // 2
	else:
		cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
	cell_x = int(np.floor((cx - OFFSET_X) / float(current_cell)))
	cell_y = int(np.floor((cy - OFFSET_Y) / float(current_cell)))
	x_s, y_s, w_s, h_s = cv2.boundingRect(cnt_straw)
	x0 = max(0, cell_x * current_cell + OFFSET_X)
	y0 = max(0, cell_y * current_cell + OFFSET_Y)
	x1 = min(w, x0 + current_cell)
	y1 = min(h, y0 + current_cell)
	if x1 <= x0 or y1 <= y0:
		x0, y0 = x_s, y_s
		x1, y1 = min(w, x_s + w_s), min(h, y_s + h_s)
	cell_region = out[y0:y1, x0:x1]
	mask_fill   = (
		np.all(cell_region != cfg["GRID_COLOR"],		axis=2)
		& np.all(cell_region != cfg["INTERSECTION_COLOR"], axis=2)
	)
	cell_region[mask_fill]  = (0, 0, 255)
	out[y0:y1, x0:x1]	   = cell_region
	if not cv2.imwrite(cfg["OUTPUT_IMAGE"], out):
		raise OSError(f"Failed to write processed image to: {cfg['OUTPUT_IMAGE']}")
	with open(cfg["INFO_PATH"], "w", encoding="utf-8") as f:
		f.write(f"Wall thickness: {thickness}\n")
		f.write(f"Cell size: {current_cell}\n")
		f.write(f"Offset X: {OFFSET_X}\n")
		f.write(f"Offset Y: {OFFSET_Y}\n")
		f.write(f"Start coord: {start_center[0]}, {start_center[1]}\n")
		f.write(f"End coord: {cx}, {cy}\n")
		f.write(f"Start cell: 0,0\n")
		f.write(f"End cell: {cell_x},{cell_y}\n")
