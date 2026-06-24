#!/usr/bin/env python3
"""
Génère dependency_map.html depuis les sources C du projet.

Utilisation depuis n'importe où :
	python3 /chemin/vers/gen_depmap.py

Ou avec arguments explicites (comportement original) :
	python3 gen_depmap.py <src_dir> <dependency_map.html>

Par défaut, le script se base sur son propre emplacement :
	src_dir	→ <dossier_du_script>/src/
	output	→ <dossier_du_script>/dependency_map.html
"""

import os, re, sys, json

# ── Résolution automatique des chemins ───────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

if len(sys.argv) == 3:
	SRC	= sys.argv[1]
	OUTPUT = sys.argv[2]
elif len(sys.argv) == 1:
	SRC	= os.path.join(SCRIPT_DIR, "src")
	OUTPUT = os.path.join(SCRIPT_DIR, "dependency_map.html")
	print(f"→ src	: {SRC}")
	print(f"→ output : {OUTPUT}")
else:
	print("Usage: python3 gen_depmap.py [<src_dir> <dependency_map.html>]")
	sys.exit(1)

if not os.path.isdir(SRC):
	print(f"Erreur : dossier source introuvable : {SRC}")
	sys.exit(1)
if not os.path.isfile(OUTPUT):
	print(f"Erreur : fichier HTML template introuvable : {OUTPUT}")
	sys.exit(1)

# ── Groupes par préfixe ───────────────────────────────────────────────────────
def get_group(name):
	n = name.replace(".c","").replace(".h","")
	if n.startswith("app"):			return "app"
	if n.startswith("chunk"):		return "chunk"
	if n.startswith("config"):		return "config"
	if n.startswith("renderer"):	return "renderer"
	if n.startswith("save"):		return "save"
	if n.startswith("sim"):			return "sim"
	if n.startswith("ui"):			return "ui"
	if n == "main":					return "main"
	return "other"

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
	r'^(?:(?:static|inline|void|int|bool|float|char|const|unsigned|t_\w+|[A-Z]\w*)\s+\*?)+(\w+)\s*\('
)
SKIP_KW = {'if','while','for','switch','return','sizeof','typedef','else','do'}

def get_defined_funcs(path):
	lines = strip_comments(open(path, encoding='utf-8', errors='replace').read()).split('\n')
	funcs = []
	i = 0
	while i < len(lines):
		m = FUNC_START.match(lines[i].strip())
		if m:
			fn = m.group(1)
			if fn not in SKIP_KW and not fn.startswith('_'):
				# Cherche { ou ; dans les lignes suivantes (signature multi-lignes)
				found_open = found_semi = False
				for j in range(i, min(i + 20, len(lines))):
					chunk = lines[j].strip()
					if '{' in chunk: found_open = True; break
					if ';' in chunk: found_semi = True; break
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
# .h en premier dans chaque groupe, puis .c triés alphabétiquement
files = sorted(
	(f for f in os.listdir(SRC) if f.endswith('.c') or f.endswith('.h')),
	key=lambda f: (0 if f.endswith('.h') else 1, f)
)

nodes = {}
for f in files:
	path = os.path.join(SRC, f)
	is_header = f.endswith('.h')
	incs = get_includes(path)
	if is_header:
		funcs	= get_declared_funcs(path)
		declared = funcs
	else:
		funcs	= get_defined_funcs(path)
		declared = []
	nodes[f] = {
		"group": get_group(f),
		"funcs": funcs,
		"includes": incs,
		"is_header": is_header,
		"declared": declared,
	}

# ── func -> fichier(s) qui la définit ────────────────────────────────────────
func_defined_in = {}
for f, info in nodes.items():
	if not info["is_header"]:
		for fn in info["funcs"]:
			func_defined_in.setdefault(fn, []).append(f)

# ── Edges ─────────────────────────────────────────────────────────────────────
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
		if inc in nodes:
			etype = "h_includes_h" if info["is_header"] else "include"
			add_edge(f, inc, etype)

# call edges
for f, info in nodes.items():
	if info["is_header"]:
		continue
	callee_callers = get_calls_with_caller(os.path.join(SRC, f))
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
		if inc in nodes and nodes[inc]["is_header"]:
			impl = list(defined & set(nodes[inc]["declared"]))
			if impl:
				add_edge(f, inc, "implements", impl, len(impl))

# ── Positions initiales ───────────────────────────────────────────────────────
# Ces constantes DOIVENT rester synchronisées avec le JS dans le HTML :
#   GRID_X = NODE_W + NODE_GAP  (230)
#   GRID_Y = NODE_H + NODE_GAP  (72)
NODE_W    = 200
NODE_H    = 42
NODE_GAP  = 30   # même valeur pour X et Y (NODE_GAP dans le JS)
GRID_X    = NODE_W + NODE_GAP  # 230
GRID_Y    = NODE_H + NODE_GAP  # 72
COLS      = 6
ROW_GAP   = 2    # lignes vides entre groupes (en unités de GRID_Y)

groups_order = ["main", "app", "chunk", "config", "renderer", "save", "sim", "ui"]
group_nodes = {g: [] for g in groups_order}
for f in sorted(nodes.keys(), key=lambda f: (0 if f.endswith('.h') else 1, f)):
	group_nodes.setdefault(nodes[f]["group"], []).append(f)

# Groupes inconnus ajoutés à la fin
for g in group_nodes:
	if g not in groups_order:
		groups_order.append(g)

init_pos = {}
row_start = 1  # ligne de grille de départ (col et row en unités de GRID)
for g in groups_order:
	gn = group_nodes.get(g, [])
	if not gn:
		continue
	for i, f in enumerate(gn):
		col = (i % COLS) + 1   # col 1-based pour laisser une marge à gauche
		row = row_start + (i // COLS)
		init_pos[f] = {"x": col * GRID_X, "y": row * GRID_Y}
	rows_used = (len(gn) - 1) // COLS + 1
	row_start += rows_used + ROW_GAP

# ── Injection dans le HTML ────────────────────────────────────────────────────
with open(OUTPUT, encoding='utf-8') as f:
	html = f.read()

nodes_json = json.dumps(nodes, ensure_ascii=False)
edges_json = json.dumps(edges, ensure_ascii=False)
pos_json = json.dumps(init_pos, ensure_ascii=False)

html, n_nodes = re.subn(r'const NODES_DATA = \{.*?\};', f'const NODES_DATA = {nodes_json};', html, flags=re.DOTALL)
html, n_edges = re.subn(r'const EDGES_DATA = \[.*?\];', f'const EDGES_DATA = {edges_json};', html, flags=re.DOTALL)
html, n_pos = re.subn(r'const INIT_POS\s*=\s*\{.*?\};', f'const INIT_POS = {pos_json};', html, flags=re.DOTALL)

missing = [name for name, n in (("NODES_DATA", n_nodes), ("EDGES_DATA", n_edges), ("INIT_POS", n_pos)) if n == 0]
if missing:
	print(f"Erreur : bloc(s) introuvable(s) dans {OUTPUT} : {', '.join(missing)}")
	print("Le fichier HTML n'a pas été modifié — vérifie que le template contient bien ces déclarations 'const'.")
	sys.exit(1)

# Sauvegarde de l'ancien fichier au cas où l'injection produirait un résultat inattendu
backup_path = OUTPUT + ".bak"
try:
	with open(backup_path, 'w', encoding='utf-8') as f:
		f.write(open(OUTPUT, encoding='utf-8').read())
except OSError:
	pass

with open(OUTPUT, 'w', encoding='utf-8') as f:
	f.write(html)

print(f"✓ {len(nodes)} nœuds, {len(edges)} arêtes → {OUTPUT}")
if os.path.isfile(backup_path):
	print(f"  (sauvegarde de l'ancienne version : {backup_path})")

# ── Rapport de cohérence ──────────────────────────────────────────────────────
# Fonctions définies dans plus d'un fichier : le mapping appel→callee est alors
# ambigu (la carte choisit une des définitions, signalé aussi via callee_multi_def
# dans les edges, mais c'est plus visible listé ici directement).
multi_def = {fn: fs for fn, fs in func_defined_in.items() if len(fs) > 1}
if multi_def:
	print(f"\n⚠ {len(multi_def)} fonction(s) définie(s) dans plusieurs fichiers (résolution d'appel ambiguë) :")
	for fn, fs in sorted(multi_def.items()):
		print(f"   - {fn}() → {', '.join(fs)}")

# Fichiers .c sans aucune fonction détectée : souvent un signe que FUNC_START
# n'a pas reconnu le style de signature utilisé (macro, type custom non listé...).
empty_c = [f for f, info in nodes.items() if not info["is_header"] and not info["funcs"]]
if empty_c:
	print(f"\n⚠ {len(empty_c)} fichier(s) .c sans fonction détectée (vérifier le style des signatures) :")
	for f in empty_c:
		print(f"   - {f}")


# Lancer depuis n'importe où :
#	python3 gen_depmap.py
#
# Ou avec chemins explicites :
#	python3 gen_depmap.py src/ dependency_map.html
