from pathlib import Path

# Fichiers
input_file = Path("trad/input.txt")
hex_file = Path("trad/output_hex.txt")
bin_file = Path("trad/output_bin.txt")
bin3_file = Path("trad/output_bin3.txt")

# Lecture binaire
data = input_file.read_bytes()

# 1️⃣ Hexadécimal par octet
hex_content = '\n'.join(f"{byte:02x}" for byte in data)
hex_file.write_text(hex_content)

# 2️⃣ Binaire standard 8 bits par octet
bin_content = '\n'.join(f"{byte:08b}" for byte in data)
bin_file.write_text(bin_content)

# 3️⃣ Binaire collé, découpé en 3 bits par ligne
all_bits = ''.join(f"{byte:08b}" for byte in data)
bin3_content = '\n'.join(all_bits[i:i+3] for i in range(0, len(all_bits), 3))
bin3_file.write_text(bin3_content)

print("Conversion terminée : 3 fichiers générés.")
