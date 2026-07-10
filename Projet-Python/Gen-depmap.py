#!/usr/bin/env python3

from __future__		import annotations
import argparse
import colorsys
import io
import json
import os
import re
import shutil
import sys
import questionary
from abc			import ABC, abstractmethod
from typing			import Any
from rich.console	import Console
from rich.panel		import Panel
from rich.progress	import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn
from rich.rule		import Rule
from rich.table		import Table

if sys.stdout.encoding.lower() != "utf-8":
	sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

console: Console = Console()

VERSION: str = "2.0.0"

MENU_STYLE: questionary.Style = questionary.Style([("selected", "fg:cyan bold"), ("pointer", "fg:cyan bold"), ("highlighted", "fg:cyan"), ("answer", "fg:green bold"), ("question", "bold")])

SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR: str = os.path.join(SCRIPT_DIR, "Template", "depmap")
TEMPLATE_PATH: str = os.path.join(TEMPLATE_DIR, "depmap.html")

DEFAULT_EXTENSIONS: set[str] = {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"}
HEADER_EXTENSIONS: set[str] = {".h", ".hpp", ".hh", ".hxx"}
SKIP_KEYWORDS: set[str] = {"if", "while", "for", "switch", "return", "sizeof", "typedef", "else", "do", "catch"}

NODE_W: int = 200
NODE_H: int = 42
NODE_GAP: int = 30
GRID_X: int = NODE_W + NODE_GAP
GRID_Y: int = NODE_H + NODE_GAP
COLS: int = 6
ROW_GAP: int = 2

FUNC_START_RE = re.compile(r'^(?:(?:static|inline|virtual|explicit|constexpr|void|int|bool|float|double|char|short|long|const|unsigned|signed|size_t|auto|[A-Za-z_]\w*(?:::\w+)?)\s+\*?)+(\w+)\s*\(')
CALL_RE = re.compile(r'\b(\w+)\s*\(')

def resolve_scan_roots(root: str) -> list[str]:
	# Beaucoup de projets C/C++ séparent leurs sources (src/) de leurs headers
	# (include/). Si le dossier passé en --src contient l'un et/ou l'autre,
	# on scanne ces sous-dossiers (chacun récursivement) plutôt que le dossier
	# racine lui-même. Sinon (pas de src/ ni include/), on scanne le dossier
	# donné directement — comportement historique inchangé pour les projets
	# qui n'ont pas cette convention.
	candidates: list[str] = []
	for name in ("src", "include"):
		d: str = os.path.join(root, name)
		if os.path.isdir(d):
			candidates.append(d)
	return candidates if candidates else [root]

class DependencyMapGeneratorInterface(ABC):
	# Interface abstraite définissant le contrat que tout générateur de carte de dépendances doit suivre.
	@abstractmethod
	def scan_files(self, src_dir: str, extensions: set[str], recursive: bool) -> tuple[list[str], dict[str, str]]:
		...

	@abstractmethod
	def build_nodes(self, files: list[str], path_of: dict[str, str], overrides: dict[str, str]) -> dict[str, dict[str, Any]]:
		...

	@abstractmethod
	def build_edges(self, nodes: dict[str, dict[str, Any]], path_of: dict[str, str], func_defined_in: dict[str, list[str]]) -> list[dict[str, Any]]:
		...

	@abstractmethod
	def compute_layout(self, nodes: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, str]]]:
		...

	@abstractmethod
	def inject_html(self, output_path: str, title: str, subtitle: str, nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]], colors: dict[str, dict[str, str]], positions: dict[str, dict[str, int]], backup: bool) -> bool:
		...

	@abstractmethod
	def run(self, args: argparse.Namespace) -> None:
		...

class DependencyMapGenerator(DependencyMapGeneratorInterface):
	# Implémentation concrète : scanne les sources C/C++ et construit la carte HTML.
	def scan_files(self, src_dir: str, extensions: set[str], recursive: bool) -> tuple[list[str], dict[str, str]]:
		# Retourne la liste des fichiers trouvés, avec (basename -> chemin absolu).
		# Le nœud est identifié par son basename (comme les #include "..." locaux),
		# avec avertissement si deux fichiers du projet partagent le même nom.
		# Scanne src/ et/ou include/ sous src_dir s'ils existent (cf. resolve_scan_roots),
		# sinon src_dir directement.
		found: dict[str, str] = {}
		dupes: list[str] = []
		for root_dir in resolve_scan_roots(src_dir):
			walker: Any = os.walk(root_dir) if recursive else [(root_dir, [], os.listdir(root_dir))]
			for root, _dirs, filenames in walker:
				for fn in filenames:
					if os.path.splitext(fn)[1] not in extensions:
						continue
					full: str = os.path.join(root, fn)
					if fn in found and found[fn] != full:
						dupes.append(fn)
					found[fn] = full
		if dupes:
			console.print(f"[yellow]{len(set(dupes))} nom(s) de fichier en doublon dans l'arborescence "
				f"(seul le dernier trouvé est gardé, les #include locaux peuvent devenir ambigus) :[/]")
			for d in sorted(set(dupes)):
				console.print(f"   [yellow]- {d}[/]")
		files: list[str] = sorted(found.keys(), key=lambda f: (0 if os.path.splitext(f)[1] in HEADER_EXTENSIONS else 1, f))
		return files, found

	def build_nodes(self, files: list[str], path_of: dict[str, str], overrides: dict[str, str]) -> dict[str, dict[str, Any]]:
		nodes: dict[str, dict[str, Any]] = {}
		for f in files:
			path: str = path_of[f]
			is_header: bool = os.path.splitext(f)[1] in HEADER_EXTENSIONS
			incs: list[str] = get_includes(path)
			if is_header:
				funcs: list[str] = get_declared_funcs(path)
				declared: list[str] = funcs
			else:
				funcs = get_defined_funcs(path)
				declared = []
			nodes[f] = {"group": get_group(f, overrides), "funcs": funcs, "includes": incs, "is_header": is_header, "declared": declared}
		return nodes

	def compute_func_defined_in(self, nodes: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
		# func -> fichier(s) qui la définit
		func_defined_in: dict[str, list[str]] = {}
		for f, info in nodes.items():
			if not info["is_header"]:
				for fn in info["funcs"]:
					func_defined_in.setdefault(fn, []).append(f)
		return func_defined_in

	def build_edges(self, nodes: dict[str, dict[str, Any]], path_of: dict[str, str], func_defined_in: dict[str, list[str]]) -> list[dict[str, Any]]:
		edges: list[dict[str, Any]] = []
		added_edges: set[tuple[str, str, str]] = set()

		def add_edge(src: str, tgt: str, etype: str, fns: list[str] | None = None, count: int = 0, pairs: list[dict[str, Any]] | None = None) -> None:
			key: tuple[str, str, str] = (src, tgt, etype)
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
			e: dict[str, Any] = {"src": src, "tgt": tgt, "type": etype, "fns": fns or [], "count": count}
			if pairs is not None:
				e["pairs"] = pairs
			edges.append(e)

		# include / h_includes_h
		for f, info in nodes.items():
			for inc in info["includes"]:
				inc_base: str = os.path.basename(inc)
				if inc_base in nodes:
					etype: str = "h_includes_h" if info["is_header"] else "include"
					add_edge(f, inc_base, etype)

		# call edges
		for f, info in nodes.items():
			if info["is_header"]:
				continue
			callee_callers: dict[str, set[str]] = get_calls_with_caller(path_of[f])
			tgt_pairs: dict[str, list[tuple[str, str]]] = {}
			for callee, callers in callee_callers.items():
				for tgt in func_defined_in.get(callee, []):
					if tgt != f:
						for caller in callers:
							tgt_pairs.setdefault(tgt, []).append((caller, callee))
			for tgt, pair_list in tgt_pairs.items():
				seen: dict[str, set[str]] = {}
				for caller, callee in pair_list:
					seen.setdefault(callee, set()).add(caller)
				fns: list[str] = list(seen.keys())
				pairs: list[dict[str, Any]] = [{"caller": caller, "callee": callee, "callee_defined_in": func_defined_in.get(callee, []), "callee_multi_def": len(func_defined_in.get(callee, [])) > 1} for callee, callers in seen.items() for caller in sorted(callers)]
				add_edge(f, tgt, "call", fns, len(pairs), pairs)

		# implements edges
		for f, info in nodes.items():
			if info["is_header"]:
				continue
			defined: set[str] = set(info["funcs"])
			for inc in info["includes"]:
				inc_base = os.path.basename(inc)
				if inc_base in nodes and nodes[inc_base]["is_header"]:
					impl: list[str] = list(defined & set(nodes[inc_base]["declared"]))
					if impl:
						add_edge(f, inc_base, "implements", impl, len(impl))

		return edges

	def build_colors(self, groups: set[str]) -> dict[str, dict[str, str]]:
		others: list[str] = sorted(g for g in groups if g not in ("main", "other"))
		colors: dict[str, dict[str, str]] = {}
		n: int = max(len(others), 1)
		for i, g in enumerate(others):
			hue: float = i * 360.0 / n
			colors[g] = {"bg": hsl_to_hex(hue, 0.55, 0.88), "border": hsl_to_hex(hue, 0.55, 0.46), "text": hsl_to_hex(hue, 0.60, 0.28)}
		if "main" in groups:
			colors["main"] = {"bg": "#f0f0f0", "border": "#888888", "text": "#333333"}
		colors["other"] = {"bg": "#f5f5f5", "border": "#aaaaaa", "text": "#444444"}
		return colors

	def compute_layout(self, nodes: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, str]]]:
		all_groups: set[str] = {info["group"] for info in nodes.values()}
		# "main" en premier s'il existe, puis alphabétique, "other" en dernier
		groups_order: list[str] = []
		if "main" in all_groups:
			groups_order.append("main")
		groups_order += sorted(g for g in all_groups if g not in ("main", "other"))
		if "other" in all_groups:
			groups_order.append("other")

		group_nodes: dict[str, list[str]] = {g: [] for g in groups_order}
		for f in sorted(nodes.keys(), key=lambda f: (0 if os.path.splitext(f)[1] in HEADER_EXTENSIONS else 1, f)):
			group_nodes.setdefault(nodes[f]["group"], []).append(f)

		init_pos: dict[str, dict[str, int]] = {}
		row_start: int = 1
		for g in groups_order:
			gn: list[str] = group_nodes.get(g, [])
			if not gn:
				continue
			for i, f in enumerate(gn):
				col: int = (i % COLS) + 1
				row: int = row_start + (i // COLS)
				init_pos[f] = {"x": col * GRID_X, "y": row * GRID_Y}
			rows_used: int = (len(gn) - 1) // COLS + 1
			row_start += rows_used + ROW_GAP

		colors: dict[str, dict[str, str]] = self.build_colors(all_groups)
		return init_pos, colors

	def inject_html(self, output_path: str, title: str, subtitle: str, nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]], colors: dict[str, dict[str, str]], positions: dict[str, dict[str, int]], backup: bool) -> bool:
		# Scaffold : crée le fichier de sortie depuis le template si absent
		if not os.path.isfile(output_path):
			if not os.path.isfile(TEMPLATE_PATH):
				console.print(f"[red]Erreur : ni {output_path} ni le template {TEMPLATE_PATH} n'existent.[/]")
				console.print("[red]Le dossier Template/depmap/ (avec depmap.html, depmap.css, depmap.js) doit être livré à côté de ce script.[/]")
				return False
			shutil.copyfile(TEMPLATE_PATH, output_path)
			console.print(f"[dim]→ Nouveau fichier créé depuis le template : {output_path}[/]")

		with open(output_path, encoding='utf-8') as f:
			html: str = f.read()

		nodes_json: str = json.dumps(nodes, ensure_ascii=False)
		edges_json: str = json.dumps(edges, ensure_ascii=False)
		pos_json: str = json.dumps(positions, ensure_ascii=False)
		colors_json: str = json.dumps(colors, ensure_ascii=False)
		title_json: str = json.dumps(title, ensure_ascii=False)
		subtitle_json: str = json.dumps(subtitle, ensure_ascii=False)

		subs: list[tuple[str, str]] = [(r'const PROJECT_TITLE\s*=\s*".*?";', f'const PROJECT_TITLE = {title_json};'), (r'const PROJECT_SUBTITLE\s*=\s*".*?";', f'const PROJECT_SUBTITLE = {subtitle_json};'), (r'const NODES_DATA = \{.*?\};', f'const NODES_DATA = {nodes_json};'), (r'const EDGES_DATA = \[.*?\];', f'const EDGES_DATA = {edges_json};'), (r'const COLORS\s*=\s*\{.*?\};', f'const COLORS = {colors_json};'), (r'const INIT_POS\s*=\s*\{.*?\};', f'const INIT_POS = {pos_json};')]

		missing: list[str] = []
		for pattern, replacement in subs:
			html, n = re.subn(pattern, replacement, html, count=1, flags=re.DOTALL)
			if n == 0:
				missing.append(pattern)

		if missing:
			console.print(f"[red]Erreur : bloc(s) introuvable(s) dans {output_path} :[/]")
			for m in missing:
				console.print(f"   [red]- {m}[/]")
			console.print("[red]Le fichier HTML n'a pas été modifié — vérifie que le template contient bien ces déclarations 'const'.[/]")
			return False

		# Backup désactivé par défaut : ne crée un .bak que si explicitement demandé (--backup)
		if backup:
			backup_path: str = output_path + ".bak"
			try:
				with open(backup_path, 'w', encoding='utf-8') as f:
					f.write(open(output_path, encoding='utf-8').read())
				console.print(f"[dim]→ Sauvegarde créée : {backup_path}[/]")
			except OSError:
				console.print(f"[yellow]Impossible de créer la sauvegarde {backup_path}[/]")

		with open(output_path, 'w', encoding='utf-8') as f:
			f.write(html)

		return True

	def print_consistency_report(self, nodes: dict[str, dict[str, Any]], func_defined_in: dict[str, list[str]]) -> None:
		multi_def: dict[str, list[str]] = {fn: fs for fn, fs in func_defined_in.items() if len(fs) > 1}
		if multi_def:
			console.print(f"\n[yellow]{len(multi_def)} fonction(s) définie(s) dans plusieurs fichiers (résolution d'appel ambiguë) :[/]")
			for fn, fs in sorted(multi_def.items()):
				console.print(f"   [yellow]- {fn}() → {', '.join(fs)}[/]")

		empty_c: list[str] = [f for f, info in nodes.items() if not info["is_header"] and not info["funcs"]]
		if empty_c:
			console.print(f"\n[yellow]{len(empty_c)} fichier(s) source sans fonction détectée (vérifier le style des signatures) :[/]")
			for f in empty_c:
				console.print(f"   [yellow]- {f}[/]")

	def run(self, args: argparse.Namespace) -> None:
		src: str = args.src
		output: str = args.output

		if not os.path.isdir(src):
			console.print(f"[red]Erreur : dossier source introuvable : {src}[/]")
			sys.exit(1)

		extensions: set[str] = DEFAULT_EXTENSIONS
		if args.ext:
			extensions = {e if e.startswith(".") else "." + e for e in args.ext.split(",")}

		overrides: dict[str, str] = load_group_overrides(args.groups)

		console.print(Rule("[bold yellow]Génération de la carte de dépendances"))
		console.print()

		scan_roots: list[str] = resolve_scan_roots(src)
		if scan_roots != [src]:
			console.print(f"[dim]→ src/ et/ou include/ détectés, scan de : {', '.join(scan_roots)}[/]")
		console.print()

		ok: bool = False
		with Progress(SpinnerColumn(), TextColumn("[bold]{task.description}"), BarColumn(bar_width=30), TimeElapsedColumn(), console=console) as progress:
			task: TaskID = progress.add_task("Scan des fichiers sources...", total=5)

			files, path_of = self.scan_files(src, extensions, args.recursive)
			if not files:
				progress.stop()
				console.print(f"[red]Erreur : aucun fichier ({', '.join(sorted(extensions))}) trouvé dans {src}[/]")
				sys.exit(1)
			progress.advance(task)

			progress.update(task, description="Analyse des fonctions et includes...")
			nodes: dict[str, dict[str, Any]] = self.build_nodes(files, path_of, overrides)
			progress.advance(task)

			progress.update(task, description="Construction des dépendances...")
			func_defined_in: dict[str, list[str]] = self.compute_func_defined_in(nodes)
			edges: list[dict[str, Any]] = self.build_edges(nodes, path_of, func_defined_in)
			progress.advance(task)

			progress.update(task, description="Calcul de la disposition (layout)...")
			positions, colors = self.compute_layout(nodes)
			progress.advance(task)

			progress.update(task, description="Génération du fichier HTML...")
			title: str = args.title or os.path.basename(os.path.abspath(src).rstrip(os.sep))
			n_c_files: int = sum(1 for i in nodes.values() if not i["is_header"])
			subtitle: str = f"{os.path.abspath(src)} · {len(nodes)} fichiers ({n_c_files} .c) · {len(edges)} liens (recalculé depuis le code source)"

			ok = self.inject_html(output, title, subtitle, nodes, edges, colors, positions, args.backup)
			progress.advance(task)

		if not ok:
			sys.exit(1)

		all_groups: set[str] = {info["group"] for info in nodes.values()}

		console.print()
		summary: Table = Table(box=None, show_header=False, padding=(0, 2))
		summary.add_column("Champ", style="cyan")
		summary.add_column("Valeur", style="bold white")
		summary.add_row("Nœuds", str(len(nodes)))
		summary.add_row("Arêtes", str(len(edges)))
		summary.add_row("Groupes", str(len(all_groups)))
		summary.add_row("Sortie", output)
		summary.add_row("Sauvegarde .bak", "oui" if args.backup else "non")
		console.print(Panel(summary, title="[bold green]✓ Carte générée avec succès", border_style="green"))

		self.print_consistency_report(nodes, func_defined_in)

# ── Fonctions utilitaires génériques (indépendantes de toute instance) ──────
def hsl_to_hex(h: float, s: float, l: float) -> str:
	rgb: tuple[float, float, float] = colorsys.hls_to_rgb((h % 360) / 360.0, l, s)
	r: float
	g: float
	b: float
	r, g, b = rgb
	return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))

def load_group_overrides(path: str | None) -> dict[str, str]:
	if not path:
		return {}
	with open(path, encoding="utf-8") as f:
		return json.load(f)

def auto_group(name: str) -> str:
	# Déduit un nom de groupe générique depuis le nom de fichier.
	# Convention supportée : "module_partie-N.ext" ou "module_partie.ext"
	# → groupe = "module". Fonctionne pour n'importe quel projet C/C++ qui
	# suit une convention de préfixage par module, sans liste figée.
	n: str = os.path.splitext(name)[0]
	# retire un suffixe "-1", "_2"...
	n = re.sub(r"[-_]\d+$", "", n)
	# préfixe avant le 1er séparateur
	n = re.split(r"[_\-]", n, maxsplit=1)[0]
	n = n.strip()
	return n.lower() if n else "other"

def get_group(name: str, overrides: dict[str, str]) -> str:
	stem: str = os.path.splitext(name)[0]
	for key, group in overrides.items():
		if stem == key or stem.startswith(key) or re.match(key, stem):
			return group
	return auto_group(name)

def strip_comments(src: str) -> str:
	src = re.sub(r'//[^\n]*', '', src)
	src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
	src = re.sub(r'"[^"]*"', '""', src)
	return src

def get_includes(path: str) -> list[str]:
	incs: list[str] = []
	for line in open(path, encoding='utf-8', errors='replace'):
		m: re.Match[str] | None = re.match(r'\s*#\s*include\s+"([^"]+)"', line)
		if m:
			incs.append(m.group(1))
	return incs

def get_defined_funcs(path: str) -> list[str]:
	lines: list[str] = strip_comments(open(path, encoding='utf-8', errors='replace').read()).split('\n')
	funcs: list[str] = []
	i: int = 0
	while i < len(lines):
		m: re.Match[str] | None = FUNC_START_RE.match(lines[i].strip())
		if m:
			fn: str = m.group(1)
			if fn not in SKIP_KEYWORDS and not fn.startswith('_'):
				found_open: bool = False
				found_semi: bool = False
				for j in range(i, min(i + 20, len(lines))):
					chunk: str = lines[j].strip()
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

def get_declared_funcs(path: str) -> list[str]:
	funcs: list[str] = []
	for line in strip_comments(open(path, encoding='utf-8', errors='replace').read()).split('\n'):
		line = line.strip()
		if not (';' in line and '(' in line):
			continue
		m: re.Match[str] | None = FUNC_START_RE.match(line)
		if m:
			fn: str = m.group(1)
			if fn not in SKIP_KEYWORDS and not fn.startswith('_'):
				funcs.append(fn)
	return list(dict.fromkeys(funcs))

def get_calls_with_caller(path: str) -> dict[str, set[str]]:
	# Retourne {callee: set(callers)} en suivant la profondeur des accolades.
	lines: list[str] = strip_comments(open(path, encoding='utf-8', errors='replace').read()).split('\n')
	result: dict[str, set[str]] = {}
	current_func: str | None = None
	brace_depth: int = 0
	for line in lines:
		s: str = line.strip()
		if brace_depth == 0:
			m: re.Match[str] | None = FUNC_START_RE.match(s)
			if m:
				fn: str = m.group(1)
				if fn not in SKIP_KEYWORDS and not fn.startswith('_'):
					current_func = fn
			brace_depth += s.count('{') - s.count('}')
			continue
		brace_depth += s.count('{') - s.count('}')
		if current_func:
			for m in CALL_RE.finditer(s):
				callee: str = m.group(1)
				if callee not in SKIP_KEYWORDS and not callee.startswith('_'):
					result.setdefault(callee, set()).add(current_func)
		if brace_depth <= 0:
			brace_depth = 0
			current_func = None
	return result

# ── Ligne de commande & interface interactive (même style que Interface.py) ─
def build_parser() -> argparse.ArgumentParser:
	epilog: str = ("Tous les paramètres ci-dessus peuvent aussi être saisis via le formulaire\ninteractif : lance simplement le script sans --src pour l'ouvrir\n(ou ajoute -i / --interactive pour le forcer même avec --src).")
	p: argparse.ArgumentParser = argparse.ArgumentParser(description="Génère Dependency_map.html depuis les sources C/C++ d'un projet.", epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
	p.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}", help="Affiche la version du programme et quitte.")
	p.add_argument("src_pos", nargs="?", help="Dossier source (positionnel, compat. ancienne syntaxe)")
	p.add_argument("output_pos", nargs="?", help="Fichier HTML de sortie (positionnel, compat. ancienne syntaxe)")
	p.add_argument("-s", "--src", help="Dossier source, ou racine du projet si elle contient src/ et/ou include/ (défaut: demandé interactivement)")
	p.add_argument("-o", "--output", help="Fichier HTML de sortie (défaut: <dossier_du_script>/Dependency_map.html)")
	p.add_argument("-t", "--title", help="Nom du projet affiché dans l'en-tête (défaut: nom du dossier source)")
	p.add_argument("-e", "--ext", help="Extensions à scanner, séparées par des virgules (défaut: %s)" % ",".join(sorted(DEFAULT_EXTENSIONS)))
	p.add_argument("-g", "--groups", help="Fichier JSON optionnel {\"préfixe_ou_regex\": \"groupe\"} pour surcharger la détection auto")
	p.add_argument("-r", "--recursive", dest="recursive", action="store_true", help="Scanne les sous-dossiers de src/ récursivement (défaut: activé)")
	p.add_argument("-nr", "--no-recursive", dest="recursive", action="store_false", help="Ne scanne que le dossier src/ directement")
	p.set_defaults(recursive=True)
	p.add_argument("-b", "--backup", dest="backup", action="store_true", help="Crée un fichier .bak avant d'écrire la sortie (défaut: désactivé)")
	p.set_defaults(backup=False)
	p.add_argument("-i", "--interactive", action="store_true", help="Force l'ouverture du formulaire interactif même si --src est fourni")
	return p

def validate_src_dir(d: str) -> bool | str:
	# Valide le dossier source saisi dans le formulaire interactif
	return os.path.isdir(d) or "Ce dossier n'existe pas"

def validate_groups_file(p: str) -> bool | str:
	# Valide le fichier JSON de groupes saisi dans le formulaire interactif (vide = ignoré)
	if not p:
		return True
	return os.path.isfile(p) or "Ce fichier n'existe pas"

def interactive_form(defaults: argparse.Namespace) -> argparse.Namespace:
	# Formulaire interactif exposant tous les paramètres parseables, dans le même
	# style que FormDemo de Interface.py (questionary + résumé Rich en Panel).
	console.print(Rule("[bold yellow]Configuration de la carte de dépendances"))
	console.print()

	src: str | None = questionary.path("Dossier contenant les fichiers .c et .h (racine du projet si src/ et/ou include/ existent) :", only_directories=True, default=defaults.src or "", validate=validate_src_dir, style=MENU_STYLE).ask()
	if not src:
		console.print("[yellow]Annulé.[/]")
		sys.exit(0)

	output: str = os.path.join(SCRIPT_DIR, "Dependency_map.html")

	title: str | None = questionary.text("Titre du projet (Entrée = nom du dossier source) :", default=defaults.title or "", style=MENU_STYLE).ask()
	if title is None:
		console.print("[yellow]Annulé.[/]")
		sys.exit(0)

	default_ext_list: list[str] = (defaults.ext.split(",") if defaults.ext else sorted(DEFAULT_EXTENSIONS))
	ext_choices: list[questionary.Choice] = [questionary.Choice(title=e, checked=e in default_ext_list) for e in sorted(DEFAULT_EXTENSIONS)]
	selected_ext: list[str] | None = questionary.checkbox("Extensions à scanner :", choices=ext_choices, style=MENU_STYLE).ask()
	if selected_ext is None:
		console.print("[yellow]Annulé.[/]")
		sys.exit(0)
	if not selected_ext:
		console.print("[yellow]Aucune extension sélectionnée.[/]")
		sys.exit(0)
	ext: str = ",".join(selected_ext)

	groups: str | None = questionary.text("Fichier JSON de groupes (optionnel, Entrée pour ignorer) :", default=defaults.groups or "", validate=validate_groups_file, style=MENU_STYLE).ask()
	if groups is None:
		console.print("[yellow]Annulé.[/]")
		sys.exit(0)

	recursive: bool | None = questionary.confirm("Scanner les sous-dossiers récursivement ?", default=defaults.recursive).ask()
	if recursive is None:
		console.print("[yellow]Annulé.[/]")
		sys.exit(0)

	backup: bool | None = questionary.confirm("Créer un fichier de sauvegarde .bak avant d'écrire la sortie ?", default=defaults.backup).ask()
	if backup is None:
		console.print("[yellow]Annulé.[/]")
		sys.exit(0)

	console.print()
	summary: Table = Table(box=None, show_header=False, padding=(0, 2))
	summary.add_column("Paramètre", style="cyan")
	summary.add_column("Valeur", style="bold white")
	summary.add_row("Dossier source", src)
	summary.add_row("Fichier de sortie", f"{output} [dim](fixe)[/]")
	summary.add_row("Titre", title or "(auto)")
	summary.add_row("Extensions", ext)
	summary.add_row("Fichier de groupes", groups or "(aucun)")
	summary.add_row("Récursif", "oui" if recursive else "non")
	summary.add_row("Sauvegarde .bak", "oui" if backup else "non")
	console.print(Panel(summary, title="[bold cyan]Résumé de la configuration", border_style="cyan"))
	console.print()

	confirmed: bool | None = questionary.confirm("Lancer la génération avec ces paramètres ?", default=True).ask()
	if not confirmed:
		console.print("[yellow]Annulé.[/]")
		sys.exit(0)

	defaults.src = src
	defaults.output = output
	defaults.title = title or None
	defaults.ext = ext
	defaults.groups = groups or None
	defaults.recursive = recursive
	defaults.backup = backup
	return defaults

def parse_args() -> argparse.Namespace:
	p: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = p.parse_args()

	args.src = args.src or args.src_pos
	args.output = args.output or args.output_pos

	# Sans --src (ou avec -i/--interactive), on ouvre le formulaire complet
	# exposant tous les paramètres — même logique que le menu de Interface.py
	# lorsqu'aucune démo n'est passée en argument direct via -d.
	if args.interactive or not args.src:
		splash_screen()
		args = interactive_form(args)
	else:
		if not args.output:
			args.output = os.path.join(SCRIPT_DIR, "Dependency_map.html")
			console.print(f"[dim]→ output : {args.output}[/]")
		splash_screen()

	return args

def splash_screen() -> None:
	# Efface la console et affiche le panneau de bienvenue
	console.clear()
	console.print()
	console.print(Panel(f"[bold cyan]Dependency Map Generator v{VERSION}[/]\n[dim]Génère Dependency_map.html depuis des sources C/C++[/]", border_style="cyan", padding=(1, 8)))
	console.print()

def main() -> None:
	args: argparse.Namespace = parse_args()
	generator: DependencyMapGenerator = DependencyMapGenerator()
	generator.run(args)

main()
