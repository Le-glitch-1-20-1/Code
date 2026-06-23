#!/usr/bin/env python3
"""
Génère dependency_map.html depuis les sources C du projet.
Usage: python3 gen_depmap.py <src_dir> <dependency_map.html>
"""

import os, re, sys, json

if len(sys.argv) != 3:
    print("Usage: python3 gen_depmap.py <src_dir> <dependency_map.html>")
    sys.exit(1)

SRC    = sys.argv[1]
OUTPUT = sys.argv[2]  # utilisé aussi comme template (modifié sur place)

# ── Groupes par préfixe ───────────────────────────────────────────────────────
def get_group(name):
    n = name.replace(".c","").replace(".h","")
    if n.startswith("app"):      return "app"
    if n.startswith("chunk"):    return "chunk"
    if n.startswith("config"):   return "config"
    if n.startswith("renderer"): return "renderer"
    if n.startswith("save"):     return "save"
    if n.startswith("sim"):      return "sim"
    if n.startswith("ui"):       return "ui"
    if n == "main":              return "main"
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
    for line in open(path):
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
    lines = strip_comments(open(path).read()).split('\n')
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
                    if '{' in chunk: found_open = True;  break
                    if ';' in chunk: found_semi = True; break
                if found_open and not found_semi:
                    funcs.append(fn)
        i += 1
    return list(dict.fromkeys(funcs))

# ── Extraction de prototypes déclarés dans les .h ────────────────────────────
def get_declared_funcs(path):
    funcs = []
    for line in strip_comments(open(path).read()).split('\n'):
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
    lines  = strip_comments(open(path).read()).split('\n')
    result = {}
    current_func = None
    brace_depth  = 0
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
            brace_depth  = 0
            current_func = None
    return result

# ── Scan du répertoire ────────────────────────────────────────────────────────
files = sorted(f for f in os.listdir(SRC) if f.endswith('.c') or f.endswith('.h'))

nodes = {}
for f in files:
    path      = os.path.join(SRC, f)
    is_header = f.endswith('.h')
    incs      = get_includes(path)
    if is_header:
        funcs    = get_declared_funcs(path)
        declared = funcs
    else:
        funcs    = get_defined_funcs(path)
        declared = []
    nodes[f] = {
        "group":     get_group(f),
        "funcs":     funcs,
        "includes":  incs,
        "is_header": is_header,
        "declared":  declared,
    }

# ── func -> fichier(s) qui la définit ────────────────────────────────────────
func_defined_in = {}
for f, info in nodes.items():
    if not info["is_header"]:
        for fn in info["funcs"]:
            func_defined_in.setdefault(fn, []).append(f)

# ── Edges ─────────────────────────────────────────────────────────────────────
edges      = []
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
        fns   = list(seen.keys())
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
groups_order = ["main", "app", "chunk", "config", "renderer", "save", "sim", "ui"]
group_nodes  = {g: [] for g in groups_order}
for f in sorted(nodes.keys()):
    group_nodes.setdefault(nodes[f]["group"], []).append(f)

init_pos = {}
y = 80
for g in groups_order:
    gn = group_nodes.get(g, [])
    if not gn:
        continue
    x, row = 140.0, 0
    for f in gn:
        init_pos[f] = {"x": x, "y": y}
        x += 184.0
        row += 1
        if row >= 6:
            x, y, row = 140.0, y + 46, 0
    y += 100

# ── Injection dans le HTML ────────────────────────────────────────────────────
with open(OUTPUT) as f:
    html = f.read()

html = re.sub(r'const NODES_DATA = \{.*?\};',
              f'const NODES_DATA = {json.dumps(nodes, ensure_ascii=False)};',
              html, flags=re.DOTALL)
html = re.sub(r'const EDGES_DATA = \[.*?\];',
              f'const EDGES_DATA = {json.dumps(edges, ensure_ascii=False)};',
              html, flags=re.DOTALL)
html = re.sub(r'const INIT_POS\s*=\s*\{.*?\};',
              f'const INIT_POS   = {json.dumps(init_pos, ensure_ascii=False)};',
              html, flags=re.DOTALL)

with open(OUTPUT, 'w') as f:
    f.write(html)

print(f"✓ {len(nodes)} nœuds, {len(edges)} arêtes → {OUTPUT}")


# lacer : python3 gen_depmap.py src/ dependency_map.html