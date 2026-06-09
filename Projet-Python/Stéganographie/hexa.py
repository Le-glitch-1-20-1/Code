import os
import sys
import shutil

# ==================================================
# CONFIGURATION
# ==================================================

INPUT_TXT_FILE = "bit_segments.txt"
OUTPUT_TXT_FILE = "hex_output_raw.txt"
INFO_DIRECTORY = "info"

# ==================================================
# UTILITY FUNCTIONS
# ==================================================

def display_progress(current: int, total: int, last_percent: int, bar_length: int = 40) -> int:
	ratio = current / total
	percent = int(ratio * 100)
	
	# Only print if the percentage has actually increased
	if percent > last_percent:
		filled = int(bar_length * ratio)
		bar = "█" * filled + "-" * (bar_length - filled)
		print(f"\rProgress: |{bar}| {percent}%", end="")
		if current == total:
			print()
	return percent

def get_repeat_count(coordinate):
	"""
	Determines how many times the bit sequence must be repeated.

	Supported formats:
	  - "(x,y)"			→ 1
	  - "([start;end],y)"  → end - start + 1
	"""
	if "[" not in coordinate:
		return 1

	try:
		content = coordinate.split("[")[1].split("]")[0]
		start, end = map(int, content.split(";"))
		return end - start + 1
	except Exception:
		raise ValueError(f"Invalid coordinate format: {coordinate}")

def read_bit_segments(input_path):
	"""
	Reads the input file and returns:
	  - list of hexadecimal bytes
	  - remaining bits (if any)
	  - total number of processed bits
	"""
	bit_buffer = ""
	hex_bytes = []

	total_bits_read = 0
	last_percent = -1

	width = height = pixel_count = None
	bits_per_pixel = None
	total_bits_expected = 0

	with open(input_path, "r", encoding="utf-8") as file:
		for line in file:
			line = line.strip()
			if not line:
				continue

			# ---------------------------------------------
			# Header parsing
			# ---------------------------------------------
			if line.startswith("WIDTH="):
				try:
					parts = line.split(";")
					width = int(parts[0].split("=")[1])
					height = int(parts[1].split("=")[1])
					pixel_count = int(parts[2].split("=")[1])
				except Exception:
					sys.exit("Error: invalid WIDTH/HEIGHT/PIXELS header.")
				continue

			if "->" not in line:
				continue

			coordinate, binary_bits = map(str.strip, line.split("->"))

			# ---------------------------------------------
			# Bits-per-pixel detection
			# ---------------------------------------------
			if bits_per_pixel is None:
				if pixel_count is None:
					sys.exit("Error: missing header before data.")
				bits_per_pixel = len(binary_bits)
				total_bits_expected = pixel_count * bits_per_pixel

			# ---------------------------------------------
			# Bit validation
			# ---------------------------------------------
			if not all(c in "01" for c in binary_bits):
				raise ValueError(f"Invalid bit sequence detected: {binary_bits}")

			# ---------------------------------------------
			# Bit repetition based on coordinates
			# ---------------------------------------------
			repeat_count = get_repeat_count(coordinate)
			repeated_bits = binary_bits * repeat_count

			bit_buffer += repeated_bits
			total_bits_read += len(repeated_bits)

			# ---------------------------------------------
			# Progress bar
			# ---------------------------------------------
			last_percent = display_progress(
				total_bits_read,
				total_bits_expected,
				last_percent
			)

			# ---------------------------------------------
			# Byte extraction
			# ---------------------------------------------
			while len(bit_buffer) >= 8:
				byte_bits = bit_buffer[:8]
				bit_buffer = bit_buffer[8:]
				hex_bytes.append(f"{int(byte_bits, 2):02x}")

	return hex_bytes, bit_buffer, total_bits_read

def write_hex_file(output_path, hex_bytes):
	"""
	Writes hexadecimal bytes to the output file (one per line).
	"""
	with open(output_path, "w", encoding="utf-8") as file:
		for byte in hex_bytes:
			file.write(byte + "\n")

def main():
	input_path = os.path.join(INFO_DIRECTORY, INPUT_TXT_FILE)
	output_path = os.path.join(INFO_DIRECTORY, OUTPUT_TXT_FILE)

	if not os.path.exists(input_path):
		sys.exit(f"Error: input file not found → {input_path}")

	hex_bytes, remaining_bits, total_bits = read_bit_segments(input_path)

	write_hex_file(output_path, hex_bytes)

	print(f"Total processed bits = {total_bits}")

	if remaining_bits:
		print(f"WARNING: {len(remaining_bits)} remaining bits ignored (incomplete byte)")
	else:
		print("Perfect alignment (no remaining bits).")

	print("\nFiles generated:")
	print(f"- {OUTPUT_TXT_FILE}")

if __name__ == "__main__":
	main()
