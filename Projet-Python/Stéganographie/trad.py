import os
import sys

# ==================================================
# CONFIGURATION
# ==================================================

INPUT_HEX_FILE = "hex_output_raw.txt"
OUTPUT_TEXT_FILE = "readable_hex_output.txt"
INFO_DIRECTORY = "info"
MAX_CHARS_PER_LINE = 80

# ==================================================
# UTILITY FUNCTIONS
# ==================================================

def hex_byte_to_printable_char(hex_byte):
	"""
	Converts a hexadecimal byte into a printable ASCII character.
	Allowed: Printable ASCII (32-126), newline (10), tab (9).
	"""
	try:
		# Handle cases where the line contains multiple bytes or 0x prefixes
		hex_byte = hex_byte.strip().lower()
		if hex_byte.startswith("0x"):
			hex_byte = hex_byte[2:]
			
		value = int(hex_byte, 16)
		if 32 <= value <= 126 or value in (9, 10):
			return chr(value)
	except (ValueError, TypeError):
		return None
	return None

def display_progress(current: int, total: int, bar_length: int = 40) -> None:
	"""Displays a progress bar in the terminal."""
	if total == 0: return
	ratio = current / total
	filled = int(bar_length * ratio)
	bar = "█" * filled + "-" * (bar_length - filled)
	# Use \r to return to the beginning of the line
	sys.stdout.write(f"\rProgress: |{bar}| {ratio * 100:.1f}%")
	sys.stdout.flush()

def main():
	# Ensure the directory exists
	if not os.path.exists(INFO_DIRECTORY):
		os.makedirs(INFO_DIRECTORY)
		print(f"Directory '{INFO_DIRECTORY}' created.")

	input_path = os.path.join(INFO_DIRECTORY, INPUT_HEX_FILE)
	output_path = os.path.join(INFO_DIRECTORY, OUTPUT_TEXT_FILE)
	
	if not os.path.exists(input_path):
		print(f"Error: Input file '{input_path}' not found.")
		sys.exit(1)

	# Count lines for the progress bar
	with open(input_path, "r") as f:
		total_lines = sum(1 for _ in f)

	if total_lines == 0:
		print("The input file is empty.")
		return

	current_line_length = 0
	converted_characters = 0
	processed_lines = 0

	try:
		with open(input_path, "r") as input_file, \
			 open(output_path, "w", encoding="utf-8") as output_file:

			for line in input_file:
				processed_lines += 1
				hex_value = line.strip()

				if hex_value:
					character = hex_byte_to_printable_char(hex_value)
					if character is not None:
						output_file.write(character)
						converted_characters += 1

						if character == "\n":
							current_line_length = 0
						else:
							current_line_length += 1

						# Force a line break if the limit is reached
						if current_line_length >= MAX_CHARS_PER_LINE:
							output_file.write("\n")
							current_line_length = 0

				# Update the bar every 10 lines for performance
				if processed_lines % 10 == 0 or processed_lines == total_lines:
					display_progress(processed_lines, total_lines)

		print(f"\nTotal processed characters: {converted_characters}")

		print("\nFiles generated:")
		print(f"- {OUTPUT_TEXT_FILE}")

	except Exception as e:
		print(f"\nAn error occurred during processing: {e}")

if __name__ == "__main__":
	main()
