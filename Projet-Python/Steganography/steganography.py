#!/usr/bin/env python3

import math
import os
import random
import sys

from PIL import Image

IMAGE_DIR = "image"
DEFAULT_OUTPUT_NAME = "hidden_message.png"
MAX_ROW_WIDTH = 800
SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp")

ALLOWED_EXTRA_BYTES = (9, 10, 13)
ALLOWED_RANGE = range(32, 127)

LENGTH_HEADER_BITS = 32
MAX_MESSAGE_BYTES = (2 ** LENGTH_HEADER_BITS) - 1

ESCAPE_SEQUENCES = {
	"\\n": "\n",
	"\\t": "\t",
	"\\r": "\r",
}

def parity_digit(value: int) -> int:
	while value >= 10:
		value = sum(int(digit) for digit in str(value))
	return 0 if value % 2 == 0 else 1

def build_value_pools() -> tuple[list, list]:
	even_values = [v for v in range(256) if parity_digit(v) == 0]
	odd_values = [v for v in range(256) if parity_digit(v) == 1]
	return even_values, odd_values

def nearest_value_with_parity(value: int, target_bit: str) -> int:
	target = 1 if target_bit == "1" else 0
	if parity_digit(value) == target:
		return value
	delta = 1
	while True:
		lower = value - delta
		upper = value + delta
		if lower >= 0 and parity_digit(lower) == target:
			return lower
		if upper <= 255 and parity_digit(upper) == target:
			return upper
		if lower < 0 and upper > 255:
			raise ValueError("No suitable byte value found (unexpected).")
		delta += 1

def build_bit_stream(message_bytes: bytes) -> str:
	if len(message_bytes) > MAX_MESSAGE_BYTES:
		raise ValueError(f"Message too long (max {MAX_MESSAGE_BYTES} bytes).")
	header_bits = format(len(message_bytes), f"0{LENGTH_HEADER_BITS}b")
	message_bits = "".join(f"{byte:08b}" for byte in message_bytes)
	return header_bits + message_bits

def interpret_escapes(raw_message: str) -> str:
	message = raw_message
	for literal, real_char in ESCAPE_SEQUENCES.items():
		message = message.replace(literal, real_char)
	return message

def validate_message(message: str) -> bytes:
	if not message:
		raise ValueError("The message is empty.")
	invalid_chars = sorted({
		c for c in message
		if ord(c) not in ALLOWED_RANGE and ord(c) not in ALLOWED_EXTRA_BYTES
	})
	if invalid_chars:
		raise ValueError(
			"The message contains characters that can't be decoded later: "
			f"{invalid_chars}. Only printable ASCII, tab and newline are supported."
		)
	return message.encode("ascii")

def choose_dimensions(pixel_count_needed: int) -> tuple[int, int]:
	if pixel_count_needed <= MAX_ROW_WIDTH:
		return pixel_count_needed, 1
	width = MAX_ROW_WIDTH
	height = math.ceil(pixel_count_needed / width)
	return width, height

def hide_message(message: str, output_path: str) -> Image.Image:
	message_bytes = validate_message(message)
	bit_string = build_bit_stream(message_bytes)
	pixel_count_needed = math.ceil(len(bit_string) / 3)
	width, height = choose_dimensions(pixel_count_needed)
	bit_string = bit_string.ljust(width * height * 3, "0")
	even_values, odd_values = build_value_pools()
	rng = random.Random()
	image = Image.new("RGB", (width, height))
	pixels = image.load()
	bit_index = 0
	for y in range(height):
		for x in range(width):
			channel_values = []
			for _ in range(3):
				bit = bit_string[bit_index]
				bit_index += 1
				pool = odd_values if bit == "1" else even_values
				channel_values.append(rng.choice(pool))
			pixels[x, y] = tuple(channel_values)
	os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
	image.save(output_path)
	return image

def hide_message_in_existing_image(message: str, source_path: str, output_path: str) -> dict:
	message_bytes = validate_message(message)
	bit_string = build_bit_stream(message_bytes)
	pixel_count_needed = math.ceil(len(bit_string) / 3)
	bit_string = bit_string.ljust(pixel_count_needed * 3, "0")
	with Image.open(source_path) as img:
		image = img.convert("RGB")
	width, height = image.size
	total_pixels = width * height
	if pixel_count_needed > total_pixels:
		raise ValueError(
			f"This image is too small: it has {total_pixels} pixels but the "
			f"message needs at least {pixel_count_needed}. Use a bigger image "
			f"or a shorter message."
		)
	pixels = image.load()
	bit_index = 0
	channels_changed = 0
	max_delta = 0
	delta_sum = 0
	remaining_pixels = pixel_count_needed
	for y in range(height):
		if remaining_pixels <= 0:
			break
		for x in range(width):
			if remaining_pixels <= 0:
				break
			r, g, b = pixels[x, y]
			new_channels = []
			for original in (r, g, b):
				target_bit = bit_string[bit_index]
				bit_index += 1
				new_value = nearest_value_with_parity(original, target_bit)
				delta = abs(new_value - original)
				if delta:
					channels_changed += 1
					delta_sum += delta
					max_delta = max(max_delta, delta)
				new_channels.append(new_value)
			pixels[x, y] = tuple(new_channels)
			remaining_pixels -= 1
	if not output_path.lower().endswith(".png"):
		output_path = os.path.splitext(output_path)[0] + ".png"
	os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
	image.save(output_path)
	return {
		"output_path": output_path,
		"width": width,
		"height": height,
		"pixels_used": pixel_count_needed,
		"total_pixels": total_pixels,
		"channels_changed": channels_changed,
		"channels_touched_total": pixel_count_needed * 3,
		"max_delta": max_delta,
		"avg_delta": (delta_sum / channels_changed) if channels_changed else 0.0,
	}

def reveal_message(image_path: str) -> str:
	with Image.open(image_path) as img:
		image = img.convert("RGB")
		width, height = image.size
		pixels = image.load()
	bit_buffer = []
	message_length = None
	total_bits_needed = LENGTH_HEADER_BITS
	for y in range(height):
		for x in range(width):
			r, g, b = pixels[x, y]
			bit_buffer.append(parity_digit(r))
			bit_buffer.append(parity_digit(g))
			bit_buffer.append(parity_digit(b))
			if message_length is None and len(bit_buffer) >= LENGTH_HEADER_BITS:
				header_bits = "".join(map(str, bit_buffer[:LENGTH_HEADER_BITS]))
				message_length = int(header_bits, 2)
				total_bits_needed = LENGTH_HEADER_BITS + message_length * 8
			if len(bit_buffer) >= total_bits_needed and message_length is not None:
				data_bits = bit_buffer[LENGTH_HEADER_BITS:total_bits_needed]
				data_bits_str = "".join(map(str, data_bits))
				message_bytes = bytes(
					int(data_bits_str[i:i + 8], 2)
					for i in range(0, len(data_bits_str), 8)
				)
				return message_bytes.decode("ascii", errors="replace")
	raise ValueError(
		"Could not fully read a hidden message from this image "
		"(it may not contain one, or the image is too small/corrupted)."
	)

def list_images() -> list:
	if not os.path.isdir(IMAGE_DIR):
		return []
	return sorted(f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(SUPPORTED_EXTENSIONS))

def run_hide_flow() -> None:
	print("\n1 - Hide in a brand-new image")
	print("2 - Hide in an existing image (keeps its appearance)")
	sub_choice = input("Your choice: ").strip()
	raw_message = input("Enter the message to hide (\\n, \\t, \\r are supported): ")
	message = interpret_escapes(raw_message)
	if sub_choice == "2":
		images = list_images()
		if not images:
			print(f"No image found in '{IMAGE_DIR}/'. Put an image there first.")
			return
		print("\nAvailable images:")
		for i, name in enumerate(images):
			print(f"  {i} - {name}")
		choice = input("\nSelect the image to hide the message in: ").strip()
		if not choice.isdigit() or int(choice) not in range(len(images)):
			print("Invalid selection.")
			return
		source_path = os.path.join(IMAGE_DIR, images[int(choice)])
		output_path = os.path.join(IMAGE_DIR, DEFAULT_OUTPUT_NAME)
		try:
			stats = hide_message_in_existing_image(message, source_path, output_path)
		except (ValueError, OSError) as e:
			print(f"Error: {e}")
			return
		print(f"\nMessage hidden in '{source_path}' -> saved as '{stats['output_path']}'")
		print(f"Image size: {stats['width']}x{stats['height']} "
			  f"({stats['pixels_used']}/{stats['total_pixels']} pixels touched)")
		print(f"Channels changed: {stats['channels_changed']}/{stats['channels_touched_total']} "
			  f"(avg change: {stats['avg_delta']:.2f}, max change: {stats['max_delta']}) — "
			  f"visually indistinguishable from the original.")
		recovered = reveal_message(stats["output_path"])
		if recovered == message:
			print("Self-check passed: the message can be recovered from this image.")
		else:
			print("WARNING: self-check failed, the message did not round-trip correctly.")
		return
	try:
		output_path = os.path.join(IMAGE_DIR, DEFAULT_OUTPUT_NAME)
		image = hide_message(message, output_path)
	except ValueError as e:
		print(f"Error: {e}")
		return
	except OSError as e:
		print(f"Error while saving the image: {e}")
		return
	print(f"\nMessage hidden in a {image.size[0]}x{image.size[1]} image.")
	print(f"Saved to: {output_path}")
	recovered = reveal_message(output_path)
	if recovered == message:
		print("Self-check passed: the message can be recovered from this image.")
	else:
		print("WARNING: self-check failed, the message did not round-trip correctly.")

def run_reveal_flow() -> None:
	images = list_images()
	if not images:
		print(f"No image found in '{IMAGE_DIR}/'.")
		return
	print("\nAvailable images:")
	for i, name in enumerate(images):
		print(f"  {i} - {name}")
	choice = input("\nSelect image index: ").strip()
	if not choice.isdigit() or int(choice) not in range(len(images)):
		print("Invalid selection.")
		return
	image_path = os.path.join(IMAGE_DIR, images[int(choice)])
	try:
		message = reveal_message(image_path)
	except (OSError, ValueError) as e:
		print(f"Error while reading '{image_path}': {e}")
		return
	print(f"\nHidden message:\n{message}")

def main() -> None:
	args = sys.argv[1:]
	if args and args[0] == "hide":
		message_parts = args[1:]
		source_path = None
		if len(message_parts) >= 2 and os.path.isfile(message_parts[-1]):
			source_path = message_parts[-1]
			message_parts = message_parts[:-1]
		raw_message = " ".join(message_parts) or input("Enter the message to hide: ")
		message = interpret_escapes(raw_message)
		if source_path:
			output_path = os.path.join(IMAGE_DIR, DEFAULT_OUTPUT_NAME)
			try:
				stats = hide_message_in_existing_image(message, source_path, output_path)
			except (ValueError, OSError) as e:
				print(f"Error: {e}")
				sys.exit(1)
			print(f"Saved to: {stats['output_path']} ({stats['width']}x{stats['height']}, "
				  f"{stats['channels_changed']}/{stats['channels_touched_total']} channels "
				  f"nudged by {stats['avg_delta']:.2f} on average, max {stats['max_delta']})")
			return
		output_path = os.path.join(IMAGE_DIR, DEFAULT_OUTPUT_NAME)
		try:
			image = hide_message(message, output_path)
		except ValueError as e:
			print(f"Error: {e}")
			sys.exit(1)
		print(f"Saved to: {output_path} ({image.size[0]}x{image.size[1]})")
		return
	if args and args[0] == "reveal":
		if len(args) < 2:
			print("Usage: python3 steganography.py reveal <path/to/image>")
			sys.exit(1)
		try:
			print(reveal_message(args[1]))
		except (OSError, ValueError) as e:
			print(f"Error: {e}")
			sys.exit(1)
		return
	while True:
		print("\n=== Steganography tool ===")
		print("1 - Hide a message in an image")
		print("2 - Reveal a message from an existing image")
		print("0 - Quit")
		choice = input("\nYour choice: ").strip()
		if choice == "1":
			run_hide_flow()
		elif choice == "2":
			run_reveal_flow()
		elif choice == "0":
			break
		else:
			print("Invalid choice.")

if __name__ == "__main__":
	main()
