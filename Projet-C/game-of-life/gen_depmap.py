#!/usr/bin/env python3
"""
Génère une carte de dépendances HTML interactive depuis les sources C/C++
d'un projet — n'importe quel projet, pas seulement celui pour lequel ce
script a été écrit à l'origine.

Utilisation la plus simple, depuis la racine du projet (ou en copiant ce
script à côté du dossier src/) :

	python3 gen_depmap.py

Options :
	python3 gen_depmap.py [src_dir] [output.html]
	                      [--src SRC] [--output OUT] [--title TITLE]
	                      [--ext .c,.h,.cpp,...] [--groups groups.json]
	                      [--recursive] [--no-backup]

Si le fichier HTML de sortie n'existe pas encore, il est généré
automatiquement à partir du template livré à côté de ce script
(dependency_map_template.html) — aucune préparation manuelle requise.

Détection des groupes (couleurs) :
	Par défaut, le "groupe" d'un fichier est déduit de son nom :
	préfixe avant le premier "_", après avoir retiré un éventuel
	suffixe "-N" (ex: "app_draw-1.c" → "app", "chunk_map-2.c" → "chunk").
	Ce découpage générique convient à la plupart des conventions de
	nommage C ("module_partie.c"). Pour un contrôle plus fin, fournissez
	un fichier --groups au format JSON : {"préfixe_ou_regex": "groupe"}.
"""

import argparse
import colorsys
import json
import os
import re
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "dependency_map_template.html")

DEFAULT_EXTENSIONS = {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"}


# ── CLI ────────────────────────────────────────────────────────────────────
def parse_args():
	p = argparse.ArgumentParser(
		description="Génère dependency_map.html depuis les sources C/C++ d'un projet.",
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	p.add_argument("src_pos", nargs="?", help="Dossier source (positionnel, compat. ancienne syntaxe)")
	p.add_argument("output_pos", nargs="?", help="Fichier HTML de sortie (positionnel, compat. ancienne syntaxe)")
	p.add_argument("--src", help="Dossier source (défaut: <dossier_du_script>/src)")
	p.add_argument("--output", help="Fichier HTML de sortie (défaut: <dossier_du_script>/dependency_map.html)")
	p.add_argument("--title", help="Nom du projet affiché dans l'en-tête (défaut: nom du dossier source)")
	p.add_argument("--ext", help="Extensions à scanner, séparées par des virgules (défaut: %s)" % ",".join(sorted(DEFAULT_EXTENSIONS)))
	p.add_argument("--groups", help="Fichier JSON optionnel {\"préfixe_ou_regex\": \"groupe\"} pour surcharger la détection auto")
	p.add_argument("--recursive", action="store_true", help="Scanne les sous-dossiers de src/ récursivement (défaut: activé)")
	p.add_argument("--no-recursive", dest="recursive", action="store_false", help="Ne scanne que le dossier src/ directement")
	p.set_defaults(recursive=True)
	p.add_argument("--no-backup", action="store_true", help="Ne pas créer de fichier .bak avant d'écrire la sortie")
	args = p.parse_args()

	src = args.src or args.src_pos
	output = args.output or args.output_pos
	if not src and not output:
		src = os.path.join(SCRIPT_DIR, "src")
		output = os.path.join(SCRIPT_DIR, "dependency_map.html")
		print(f"→ src    : {src}")
		print(f"→ output : {output}")
	elif not (src and output):
		p.error("fournir soit aucun argument (auto), soit src ET output")

	args.src = src
	args.output = output
	return args


# ── Groupes par préfixe (détection automatique, générique) ──────────────────
def load_group_overrides(path):
	if not path:
		return {}
	with open(path, encoding="utf-8") as f:
		return json.load(f)


def auto_group(name):
	"""Déduit un nom de groupe générique depuis le nom de fichier.

	Convention supportée : "module_partie-N.ext" ou "module_partie.ext"
	→ groupe = "module". Fonctionne pour n'importe quel projet C/C++ qui
	suit une convention de préfixage par module, sans liste figée.
	"""
	n = os.path.splitext(name)[0]
	n = re.sub(r"[-_]\d+$", "", n)          # retire un suffixe "-1", "_2"...
	n = re.split(r"[_\-]", n, maxsplit=1)[0]  # préfixe avant le 1er séparateur
	n = n.strip()
	return n.lower() if n else "other"


def get_group(name, overrides):
	stem = os.path.splitext(name)[0]
	for key, group in overrides.items():
		if stem == key or stem.startswith(key) or re.match(key, stem):
			return group
	return auto_group(name)


# ── Palette de couleurs générée dynamiquement (nombre de groupes arbitraire) ─
def hsl_to_hex(h, s, l):
	r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, l, s)
	return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def build_colors(groups):
	others = sorted(g for g in groups if g not in ("main", "other"))
	colors = {}
	n = max(len(others), 1)
	for i, g in enumerate(others):
		hue = (i * 360.0 / n)
		colors[g] = {
			"bg": hsl_to_hex(hue, 0.55, 0.88),
			"border": hsl_to_hex(hue, 0.55, 0.46),
			"text": hsl_to_hex(hue, 0.60, 0.28),
		}
	if "main" in groups:
		colors["main"] = {"bg": "#f0f0f0", "border": "#888888", "text": "#333333"}
	colors["other"] = {"bg": "#f5f5f5", "border": "#aaaaaa", "text": "#444444"}
	return colors


# ── Helpers de nettoyage ──────────────────────────────────────────────────────
def strip_comments(src):
	src = re.sub(r'//[^\n]*', '', src)
	src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
	src = re.sub(r'"[^"]*"', '""', src)
	return src


# ── Extraction d'includes ─────────────────────────────────────────────────────
def get_includes(path):
	incs = []
	for line in open(path, encoding='utf-8', errors='replace'):
		m = re.match(r'\s*#\s*include\s+"([^"]+)"', line)
		if m:
			incs.append(m.group(1))
	return incs


# ── Extraction de fonctions définies (corps avec {}) ─────────────────────────
FUNC_START = re.compile(
	r'^(?:(?:static|inline|virtual|explicit|constexpr|void|int|bool|float|double|'
	r'char|short|long|const|unsigned|signed|size_t|auto|[A-Za-z_]\w*(?:::\w+)?)\s+\*?)+(\w+)\s*\('
)
SKIP_KW = {'if', 'while', 'for', 'switch', 'return', 'sizeof', 'typedef', 'else', 'do', 'catch'}


def get_defined_funcs(path):
	lines = strip_comments(open(path, encoding='utf-8', errors='replace').read()).split('\n')
	funcs = []
	i = 0
	while i < len(lines):
		m = FUNC_START.match(lines[i].strip())
		if m:
			fn = m.group(1)
			if fn not in SKIP_KW and not fn.startswith('_'):
				found_open = found_semi = False
				for j in range(i, min(i + 20, len(lines))):
					chunk = lines[j].strip()
					if '{' in chunk:
						found_open = True
						break
					if ';' in chunk:
						found_semi = True
						break
				if found_open and not found_semi:
					funcs.append(fn)
		i += 1
	return list(dict.fromkeys(funcs))


# ── Extraction de prototypes déclarés dans les .h ────────────────────────────
def get_declared_funcs(path):
	funcs = []
	for line in strip_comments(open(path, encoding='utf-8', errors='replace').read()).split('\n'):
		line = line.strip()
		if not (';' in line and '(' in line):
			continue
		m = FUNC_START.match(line)
		if m:
			fn = m.group(1)
			if fn not in SKIP_KW and not fn.startswith('_'):
				funcs.append(fn)
	return list(dict.fromkeys(funcs))


# ── Extraction des appels avec leur caller ────────────────────────────────────
CALL_RE = re.compile(r'\b(\w+)\s*\(')


def get_calls_with_caller(path):
	"""Retourne {callee: set(callers)} en suivant la profondeur des accolades."""
	lines = strip_comments(open(path, encoding='utf-8', errors='replace').read()).split('\n')
	result = {}
	current_func = None
	brace_depth = 0
	for line in lines:
		s = line.strip()
		if brace_depth == 0:
			m = FUNC_START.match(s)
			if m:
				fn = m.group(1)
				if fn not in SKIP_KW and not fn.startswith('_'):
					current_func = fn
			brace_depth += s.count('{') - s.count('}')
			continue
		brace_depth += s.count('{') - s.count('}')
		if current_func:
			for m in CALL_RE.finditer(s):
				callee = m.group(1)
				if callee not in SKIP_KW and not callee.startswith('_'):
					result.setdefault(callee, set()).add(current_func)
		if brace_depth <= 0:
			brace_depth = 0
			current_func = None
	return result


# ── Scan du répertoire ────────────────────────────────────────────────────────
def scan_files(src_dir, extensions, recursive):
	"""Retourne la liste des fichiers trouvés, avec (basename -> chemin absolu).
	Le nœud est identifié par son basename (comme les #include "..." locaux),
	avec avertissement si deux fichiers du projet partagent le même nom.
	"""
	found = {}
	if recursive:
		walker = os.walk(src_dir)
	else:
		walker = [(src_dir, [], os.listdir(src_dir))]
	dupes = []
	for root, _dirs, filenames in walker:
		for fn in filenames:
			if os.path.splitext(fn)[1] not in extensions:
				continue
			full = os.path.join(root, fn)
			if fn in found and found[fn] != full:
				dupes.append(fn)
			found[fn] = full
	if dupes:
		print(f"⚠ {len(set(dupes))} nom(s) de fichier en doublon dans l'arborescence "
			  f"(seul le dernier trouvé est gardé, les #include locaux peuvent devenir ambigus) :")
		for d in sorted(set(dupes)):
			print(f"   - {d}")
	files = sorted(found.keys(), key=lambda f: (0 if os.path.splitext(f)[1] in ('.h', '.hpp', '.hh', '.hxx') else 1, f))
	return files, found


def main():
	args = parse_args()
	SRC = args.src
	OUTPUT = args.output

	if not os.path.isdir(SRC):
		print(f"Erreur : dossier source introuvable : {SRC}")
		sys.exit(1)

	extensions = DEFAULT_EXTENSIONS
	if args.ext:
		extensions = {e if e.startswith(".") else "." + e for e in args.ext.split(",")}

	overrides = load_group_overrides(args.groups)

	files, path_of = scan_files(SRC, extensions, args.recursive)
	if not files:
		print(f"Erreur : aucun fichier ({', '.join(sorted(extensions))}) trouvé dans {SRC}")
		sys.exit(1)

	header_ext = {".h", ".hpp", ".hh", ".hxx"}

	nodes = {}
	for f in files:
		path = path_of[f]
		is_header = os.path.splitext(f)[1] in header_ext
		incs = get_includes(path)
		if is_header:
			funcs = get_declared_funcs(path)
			declared = funcs
		else:
			funcs = get_defined_funcs(path)
			declared = []
		nodes[f] = {
			"group": get_group(f, overrides),
			"funcs": funcs,
			"includes": incs,
			"is_header": is_header,
			"declared": declared,
		}

	# ── func -> fichier(s) qui la définit ────────────────────────────────────
	func_defined_in = {}
	for f, info in nodes.items():
		if not info["is_header"]:
			for fn in info["funcs"]:
				func_defined_in.setdefault(fn, []).append(f)

	# ── Edges ─────────────────────────────────────────────────────────────────
	edges = []
	added_edges = set()

	def add_edge(src, tgt, etype, fns=None, count=0, pairs=None):
		key = (src, tgt, etype)
		if key in added_edges:
			for e in edges:
				if e["src"] == src and e["tgt"] == tgt and e["type"] == etype:
					if fns:
						for fn in fns:
							if fn not in e["fns"]:
								e["fns"].append(fn)
								e["count"] += 1
					if pairs:
						e.setdefault("pairs", []).extend(pairs)
			return
		added_edges.add(key)
		e = {"src": src, "tgt": tgt, "type": etype, "fns": fns or [], "count": count}
		if pairs is not None:
			e["pairs"] = pairs
		edges.append(e)

	# include / h_includes_h
	for f, info in nodes.items():
		for inc in info["includes"]:
			inc_base = os.path.basename(inc)
			if inc_base in nodes:
				etype = "h_includes_h" if info["is_header"] else "include"
				add_edge(f, inc_base, etype)

	# call edges
	for f, info in nodes.items():
		if info["is_header"]:
			continue
		callee_callers = get_calls_with_caller(path_of[f])
		tgt_pairs = {}
		for callee, callers in callee_callers.items():
			for tgt in func_defined_in.get(callee, []):
				if tgt != f:
					for caller in callers:
						tgt_pairs.setdefault(tgt, []).append((caller, callee))
		for tgt, pair_list in tgt_pairs.items():
			seen = {}
			for caller, callee in pair_list:
				seen.setdefault(callee, set()).add(caller)
			fns = list(seen.keys())
			pairs = [
				{"caller": caller, "callee": callee,
				 "callee_defined_in": func_defined_in.get(callee, []),
				 "callee_multi_def": len(func_defined_in.get(callee, [])) > 1}
				for callee, callers in seen.items()
				for caller in sorted(callers)
			]
			add_edge(f, tgt, "call", fns, len(pairs), pairs)

	# implements edges
	for f, info in nodes.items():
		if info["is_header"]:
			continue
		defined = set(info["funcs"])
		for inc in info["includes"]:
			inc_base = os.path.basename(inc)
			if inc_base in nodes and nodes[inc_base]["is_header"]:
				impl = list(defined & set(nodes[inc_base]["declared"]))
				if impl:
					add_edge(f, inc_base, "implements", impl, len(impl))

	# ── Positions initiales ───────────────────────────────────────────────────
	# Ces constantes DOIVENT rester synchronisées avec le JS du template :
	#   GRID_X = NODE_W + NODE_GAP  (230)
	#   GRID_Y = NODE_H + NODE_GAP  (72)
	NODE_W = 200
	NODE_H = 42
	NODE_GAP = 30
	GRID_X = NODE_W + NODE_GAP
	GRID_Y = NODE_H + NODE_GAP
	COLS = 6
	ROW_GAP = 2

	all_groups = sorted({info["group"] for info in nodes.values()})
	# "main" en premier s'il existe, puis alphabétique, "other" en dernier
	groups_order = []
	if "main" in all_groups:
		groups_order.append("main")
	groups_order += [g for g in all_groups if g not in ("main", "other")]
	if "other" in all_groups:
		groups_order.append("other")

	group_nodes = {g: [] for g in groups_order}
	for f in sorted(nodes.keys(), key=lambda f: (0 if os.path.splitext(f)[1] in header_ext else 1, f)):
		group_nodes.setdefault(nodes[f]["group"], []).append(f)

	init_pos = {}
	row_start = 1
	for g in groups_order:
		gn = group_nodes.get(g, [])
		if not gn:
			continue
		for i, f in enumerate(gn):
			col = (i % COLS) + 1
			row = row_start + (i // COLS)
			init_pos[f] = {"x": col * GRID_X, "y": row * GRID_Y}
		rows_used = (len(gn) - 1) // COLS + 1
		row_start += rows_used + ROW_GAP

	colors = build_colors(all_groups)

	# ── Scaffold : crée le fichier de sortie depuis le template si absent ────
	if not os.path.isfile(OUTPUT):
		if not os.path.isfile(TEMPLATE_PATH):
			print(f"Erreur : ni {OUTPUT} ni le template {TEMPLATE_PATH} n'existent.")
			print("Le template dependency_map_template.html doit être livré à côté de ce script.")
			sys.exit(1)
		shutil.copyfile(TEMPLATE_PATH, OUTPUT)
		print(f"→ Nouveau fichier créé depuis le template : {OUTPUT}")

	# ── Injection dans le HTML ────────────────────────────────────────────────
	with open(OUTPUT, encoding='utf-8') as f:
		html = f.read()

	title = args.title or os.path.basename(os.path.abspath(SRC).rstrip(os.sep))
	n_c_files = sum(1 for i in nodes.values() if not i["is_header"])
	subtitle = f"{os.path.abspath(SRC)} · {len(nodes)} fichiers ({n_c_files} .c) · {len(edges)} liens (recalculé depuis le code source)"

	nodes_json = json.dumps(nodes, ensure_ascii=False)
	edges_json = json.dumps(edges, ensure_ascii=False)
	pos_json = json.dumps(init_pos, ensure_ascii=False)
	colors_json = json.dumps(colors, ensure_ascii=False)
	title_json = json.dumps(title, ensure_ascii=False)
	subtitle_json = json.dumps(subtitle, ensure_ascii=False)

	subs = [
		(r'const PROJECT_TITLE\s*=\s*".*?";', f'const PROJECT_TITLE = {title_json};'),
		(r'const PROJECT_SUBTITLE\s*=\s*".*?";', f'const PROJECT_SUBTITLE = {subtitle_json};'),
		(r'const NODES_DATA = \{.*?\};', f'const NODES_DATA = {nodes_json};'),
		(r'const EDGES_DATA = \[.*?\];', f'const EDGES_DATA = {edges_json};'),
		(r'const COLORS\s*=\s*\{.*?\};', f'const COLORS = {colors_json};'),
		(r'const INIT_POS\s*=\s*\{.*?\};', f'const INIT_POS = {pos_json};'),
	]

	missing = []
	for pattern, replacement in subs:
		html, n = re.subn(pattern, replacement, html, count=1, flags=re.DOTALL)
		if n == 0:
			missing.append(pattern)

	if missing:
		print(f"Erreur : bloc(s) introuvable(s) dans {OUTPUT} :")
		for m in missing:
			print(f"   - {m}")
		print("Le fichier HTML n'a pas été modifié — vérifie que le template contient bien ces déclarations 'const'.")
		sys.exit(1)

	if not args.no_backup:
		backup_path = OUTPUT + ".bak"
		try:
			with open(backup_path, 'w', encoding='utf-8') as f:
				f.write(open(OUTPUT, encoding='utf-8').read())
		except OSError:
			pass

	with open(OUTPUT, 'w', encoding='utf-8') as f:
		f.write(html)

	print(f"✓ {len(nodes)} nœuds, {len(edges)} arêtes, {len(all_groups)} groupe(s) → {OUTPUT}")

	# ── Rapport de cohérence ──────────────────────────────────────────────────
	multi_def = {fn: fs for fn, fs in func_defined_in.items() if len(fs) > 1}
	if multi_def:
		print(f"\n⚠ {len(multi_def)} fonction(s) définie(s) dans plusieurs fichiers (résolution d'appel ambiguë) :")
		for fn, fs in sorted(multi_def.items()):
			print(f"   - {fn}() → {', '.join(fs)}")

	empty_c = [f for f, info in nodes.items() if not info["is_header"] and not info["funcs"]]
	if empty_c:
		print(f"\n⚠ {len(empty_c)} fichier(s) source sans fonction détectée (vérifier le style des signatures) :")
		for f in empty_c:
			print(f"   - {f}")


if __name__ == "__main__":
	main()
