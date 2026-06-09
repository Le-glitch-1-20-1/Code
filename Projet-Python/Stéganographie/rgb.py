from PIL import Image
import os
import sys

# ==================================================
# CONFIGURATION
# ==================================================

IMAGE_INPUT_DIR = "image"
OUTPUT_INFO_DIR = "info"

SUPPORTED_IMAGE_EXTENSIONS = (
	".png", ".jpg", ".jpeg", ".bmp",
	".gif", ".tiff", ".webp"
)

RGB_OUTPUT_FILENAME = "rgb_segments.txt"
BIT_OUTPUT_FILENAME = "bit_segments.txt"

os.makedirs(OUTPUT_INFO_DIR, exist_ok=True)

# ==================================================
# UTILITY FUNCTIONS
# ==================================================

def parity_digit(value: int) -> int:
	"""
	Reduces a number to its digital root.
	Even -> 0 | Odd -> 1
	"""
	while value >= 10:
		value = sum(int(digit) for digit in str(value))
	return 0 if value % 2 == 0 else 1

def rgb_to_bit_triplet(red: int, green: int, blue: int) -> str:
	"""Converts an RGB pixel into a 3-bit parity string."""
	return f"{parity_digit(red)}{parity_digit(green)}{parity_digit(blue)}"

def display_progress(current: int, total: int, bar_length: int = 40) -> None:
	"""Displays a progress bar in the terminal."""
	ratio = current / total
	filled = int(bar_length * ratio)
	bar = "█" * filled + "-" * (bar_length - filled)

	print(f"\rProgress: |{bar}| {ratio * 100:.1f}%", end="")
	if current == total:
		print()

def write_compacted_segment(
	file_handle,
	row: int,
	start_x: int,
	end_x: int,
	value: str,
	alignment_width: int
) -> None:
	"""
	Writes a compacted horizontal segment to file.
	Ensures arrow alignment for readability.
	"""
	if start_x == end_x:
		coordinate = f"({start_x},{row})"
	else:
		coordinate = f"([{start_x};{end_x}],{row})"

	file_handle.write(f"{coordinate.ljust(alignment_width)} -> {value}\n")

def scan_image_directory() -> list:
	"""Scans the image directory and returns valid image metadata."""
	if not os.path.isdir(IMAGE_INPUT_DIR):
		print(f"Directory not found: {IMAGE_INPUT_DIR}")
		sys.exit(1)

	image_list = []

	for filename in os.listdir(IMAGE_INPUT_DIR):
		if filename.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
			image_path = os.path.join(IMAGE_INPUT_DIR, filename)
			try:
				with Image.open(image_path) as img:
					width, height = img.size
					image_list.append({
						"filename": filename,
						"path": image_path,
						"width": width,
						"height": height,
						"pixel_total": width * height
					})
			except Exception as error:
				print(f"Error loading {filename}: {error}")

	if not image_list:
		print("No valid images found.")
		sys.exit(1)

	return image_list

def select_image(image_list: list) -> dict:
	"""Displays available images and returns the selected one."""
	print("\nAvailable images:\n")
	for index, info in enumerate(image_list):
		print(
			f"{index} - {info['filename']} | "
			f"{info['width']}x{info['height']} | "
			f"{info['pixel_total']} pixels"
		)

	choice = input("\nSelect image index: ")

	if not choice.isdigit() or int(choice) not in range(len(image_list)):
		print("Invalid selection.")
		sys.exit(1)

	return image_list[int(choice)]

def process_selected_image(image_info: dict) -> None:
	"""Processes the image and generates RGB and bit segment files."""
	image = Image.open(image_info["path"]).convert("RGB")
	pixel_map = image.load()

	width = image_info["width"]
	height = image_info["height"]
	total_pixels = image_info["pixel_total"]

	rgb_output_path = os.path.join(OUTPUT_INFO_DIR, RGB_OUTPUT_FILENAME)
	bit_output_path = os.path.join(OUTPUT_INFO_DIR, BIT_OUTPUT_FILENAME)

	max_coordinate = f"([{width};{width}],{height})"
	alignment_width = len(max_coordinate) + 1

	processed_pixels = 0

	with open(rgb_output_path, "w", encoding="utf-8") as rgb_file, \
		 open(bit_output_path, "w", encoding="utf-8") as bit_file:

		header = f"WIDTH={width};HEIGHT={height};PIXELS={total_pixels}\n\n"
		rgb_file.write(header)
		bit_file.write(header)

		for y in range(height):
			previous_rgb = None
			previous_bits = None
			rgb_segment_start = 0
			bit_segment_start = 0

			for x in range(width):
				r, g, b = pixel_map[x, y]

				current_rgb = (
					f"R:{str(r).rjust(3,'0')} "
					f"G:{str(g).rjust(3,'0')} "
					f"B:{str(b).rjust(3,'0')}"
				)
				current_bits = rgb_to_bit_triplet(r, g, b)

				if current_rgb != previous_rgb:
					if previous_rgb is not None:
						write_compacted_segment(
							rgb_file, y,
							rgb_segment_start, x - 1,
							previous_rgb, alignment_width
						)
					previous_rgb = current_rgb
					rgb_segment_start = x

				if current_bits != previous_bits:
					if previous_bits is not None:
						write_compacted_segment(
							bit_file, y,
							bit_segment_start, x - 1,
							previous_bits, alignment_width
						)
					previous_bits = current_bits
					bit_segment_start = x

				processed_pixels += 1
				display_progress(processed_pixels, total_pixels)

			if previous_rgb is not None:
				write_compacted_segment(
					rgb_file, y,
					rgb_segment_start, width - 1,
					previous_rgb, alignment_width
				)

			if previous_bits is not None:
				write_compacted_segment(
					bit_file, y,
					bit_segment_start, width - 1,
					previous_bits, alignment_width
				)

def main():
	images = scan_image_directory()
	chosen_image = select_image(images)
	process_selected_image(chosen_image)

	print("\nFiles generated:")
	print(f"- {RGB_OUTPUT_FILENAME}")
	print(f"- {BIT_OUTPUT_FILENAME}")

if __name__ == "__main__":
	main()
