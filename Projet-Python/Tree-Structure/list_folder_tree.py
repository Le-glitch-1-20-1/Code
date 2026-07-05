#!/usr/bin/env python3

import os
import json
import gzip
import shutil
import psutil
from datetime	import datetime

HTML_FILE = "result.html"
TEMPLATE_HTML = "src/template.html"

def format_size_bytes(size_bytes):
	if size_bytes == 0:
		return "0.00", "B"
	for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
		if size_bytes < 1024:
			return f"{size_bytes:.2f}", unit
		size_bytes /= 1024

def flatten_tree(tree, path=""):
	rows = []
	for name, content in tree.items():
		if name == "_files":
			for file, size in content:
				base_name, ext = os.path.splitext(file)
				ext = ext.lstrip(".")
				val, unit = format_size_bytes(size)
				rows.append({
					"n": base_name,
					"e": ext,
					"t": val,
					"u": unit,
					"p": path,
				})
		else:
			sub_path = f"{path}/{name}" if path else name
			rows += flatten_tree(content, sub_path)
	return rows

def extract_extensions(rows):
	exts = sorted({item["e"] for item in rows if item["e"]})
	return exts

def list_filtered_folders_and_files(partitions, padding_value, extensions):
	results = {}
	errors = []
	for partition in partitions:
		mountpoint = partition.mountpoint
		results[mountpoint] = {}
		try:
			total_folders = sum([len(dirs) for _, dirs, _ in os.walk(mountpoint, onerror=lambda e: None)])
			print(f"Scanning {mountpoint:<{padding_value}} | {total_folders:>10} folders")
			for folder, subfolders, files in os.walk(mountpoint, onerror=lambda e: None):
				try:
					filtered_files = [
						(f, os.path.getsize(os.path.join(folder, f)))
						for f in files
						if not extensions
						or os.path.splitext(f)[1].lower().lstrip(".") in extensions
					]
					if filtered_files:
						current_folder = results.setdefault(mountpoint, {})
						sub_tree = current_folder
						sub_paths = folder[len(mountpoint):].strip(os.sep).split(os.sep)
						for sub_folder in sub_paths:
							if sub_folder:
								sub_tree = sub_tree.setdefault(sub_folder, {})
						sub_tree["_files"] = filtered_files
				except PermissionError:
					errors.append(f"Access denied to a folder in: {folder}")
				except FileNotFoundError:
					errors.append(f"Path not found: {folder}")
				except Exception as e:
					errors.append(f"Error while processing folder {folder}: {e}")
		except PermissionError:
			errors.append(f"Access denied to partition: {mountpoint}")
		except Exception as e:
			errors.append(f"Error while processing partition {mountpoint}: {e}")
	return results, errors

def convert_to_html(results, html_file):
	try:
		with open(TEMPLATE_HTML, "r", encoding="utf-8") as f:
			template = f.read()
	except FileNotFoundError:
		print(f"Error: HTML template file '{TEMPLATE_HTML}' not found.")
		return
	partitions_data = {}
	for mountpoint, content in results.items():
		label = f"🖥️ {mountpoint}"
		rows = flatten_tree(content)
		partitions_data[label] = rows
	available_extensions = extract_extensions([item for rows in partitions_data.values() for item in rows])
	json_data = json.dumps(partitions_data, ensure_ascii=False, separators=(',', ':'))
	extensions_json = json.dumps(available_extensions, ensure_ascii=False, separators=(',', ':'))
	final_html = template.replace("{{DATE}}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
	final_html = final_html.replace("{{DATA_JSON}}", json_data)
	final_html = final_html.replace("{{EXTENSIONS_JSON}}", extensions_json)
	with open(html_file, 'w', encoding='utf-8') as f:
		f.write(final_html)
	size_mb = os.path.getsize(html_file) / (1024 * 1024)
	print(f"\nReport generated: {html_file}  ({size_mb:.2f} MB)")
	gz_path = html_file + ".gz"
	with open(html_file, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
		shutil.copyfileobj(f_in, f_out)
	size_gz = os.path.getsize(gz_path) / (1024 * 1024)
	print(f"Compressed version: {gz_path}  ({size_gz:.2f} MB)")

def detect_locations_and_generate_report(extensions=None):
	partitions = psutil.disk_partitions(all=False)
	target_partition = max(partitions, key=lambda p: len(p.mountpoint))
	name = target_partition.mountpoint
	length = len(name)
	padding_value = length + 5
	if padding_value % 2 != 0:
		padding_value += 1
	padding_value += 1
	adjusted_val = len("Scanning  |  folders") + padding_value + 11
	title = "=== All-Files Report Generator ==="
	if adjusted_val < len(title):
		print(title)
	else:
		pad = int((adjusted_val - len(title)) / 2)
		print(f"\n{'=' * pad}{title}{'=' * pad}\n")
	results, errors = list_filtered_folders_and_files(partitions, padding_value, extensions or [])
	convert_to_html(results, HTML_FILE)
	if errors:
		print(f"\n{'Errors encountered':<{len('Scanning ') + padding_value}} | {len(errors):>10} errors\n")
		os.makedirs("src", exist_ok=True)
		with open("src/errors-report.txt", "w", encoding="utf-8") as f:
			f.write("=== Error Report ===\n")
			f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
			f.write(f"Total number of errors: {len(errors)}\n\n")
			n = len(str(len(errors)))
			for i, error in enumerate(errors, 1):
				if ":" in error:
					left, right = error.split(":", 1)
					f.write(f"{i:0{n}d}. {left.strip():<40}: {right.strip()}\n")
				else:
					f.write(f"{i:0{n}d}. {error}\n")

def main():
	extensions = []
	detect_locations_and_generate_report(extensions)

if __name__ == "__main__":
	main()
