#!/usr/bin/env python3
from __future__ import annotations
import argparse
import sys
from abc import ABC, abstractmethod
from math import comb
from typing import Any
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sympy import SympifyError, expand, latex, sympify

console: Console = Console()
VERSION: str = "1.0.0"
ANSI_COLORS: dict[str, str] = {
	"red": "31",
	"green": "32",
	"yellow": "33",
	"cyan": "36",
	"magenta": "35",
	"bold": "1",
}
SUPERSCRIPT_DIGITS: str = "⁰¹²³⁴⁵⁶⁷⁸⁹"
MENU_CHOICES: list[str] = [
	"Afficher une ligne du triangle de Pascal",
	"Developper un binome (a + b)^n",
	"Quitter",
]
MENU_STYLE: questionary.Style = questionary.Style([
	("selected", "fg:cyan bold"),
	("pointer", "fg:cyan bold"),
	("highlighted", "fg:cyan"),
	("answer", "fg:green bold"),
	("question", "bold"),
])

def colorize(text: str, color: str) -> str:
	# Encadre le texte avec les codes ANSI de la couleur demandee
	code: str = ANSI_COLORS.get(color, "0")
	return f"\033[{code}m{text}\033[0m"

def info(message: str) -> None:
	# Affiche un message normal dans la console
	print(message)

def error(message: str) -> None:
	# Affiche une erreur coloree sur la sortie d'erreur
	print(colorize(f"✗ {message}", "red"), file=sys.stderr)

def print_banner() -> None:
	# Efface la console puis affiche le panneau de bienvenue du programme
	console.clear()
	console.print(Panel(
		f"[bold cyan]  Pascal & Binome Toolkit v{VERSION}  [/]\n"
		"[dim]Triangle de Pascal et developpement de binomes[/]",
		border_style="cyan",
		padding=(1, 8),
	))

def int_to_superscript(n: int) -> str:
	# Convertit un entier en chiffres exposants unicode
	if not isinstance(n, int):
		raise TypeError(f"Expected int, got {type(n).__name__}.")
	negative: bool = n < 0
	result: str = "".join(SUPERSCRIPT_DIGITS[int(d)] for d in str(abs(n)))
	return ("⁻" if negative else "") + result

def format_expr_unicode(expr: str) -> str:
	# Remplace les "**exposant" d'une expression sympy par des chiffres exposants unicode
	if not isinstance(expr, str):
		raise TypeError(f"Expected str, got {type(expr).__name__}.")
	s: str = expr.replace("**", "^")
	result: str = ""
	i: int = 0
	while i < len(s):
		if s[i] == "^":
			i += 1
			if i < len(s) and s[i] == "(":
				# Exposant entre parentheses, ex: ^(-2)
				depth: int = 1
				j: int = i + 1
				while j < len(s) and depth > 0:
					if s[j] == "(":
						depth += 1
					elif s[j] == ")":
						depth -= 1
					j += 1
				inner: str = s[i + 1:j - 1]
				if inner.lstrip("-").isdigit():
					result += int_to_superscript(int(inner))
				else:
					result += "^" + s[i:j]
				i = j
				continue
			exp: str = ""
			if i < len(s) and s[i] == "-":
				exp += "-"
				i += 1
			while i < len(s) and s[i].isdigit():
				exp += s[i]
				i += 1
			if not exp or exp == "-":
				result += "^" + exp
			else:
				result += int_to_superscript(int(exp))
		else:
			result += s[i]
			i += 1
	return result

def coef_binomial(n: int, k: int) -> int:
	# Calcule le coefficient binomial C(n, k)
	if not isinstance(n, int) or not isinstance(k, int):
		raise TypeError("n and k must be integers.")
	if n < 0 or k < 0:
		raise ValueError("n and k must be non-negative integers.")
	return comb(n, k)

def display_pascal_row(n: int) -> None:
	# Affiche la ligne n du triangle de Pascal dans un tableau rich
	if not isinstance(n, int):
		raise TypeError("Row number must be an integer.")
	if n < 0:
		error("Row number must be a non-negative integer.")
		return
	row: list[int] = [coef_binomial(n, k) for k in range(n + 1)]
	table: Table = Table(show_header=True, header_style="bold magenta", border_style="bright_black")
	k: int
	for k in range(n + 1):
		table.add_column(f"k={k}", justify="center", style="cyan")
	table.add_row(*[str(v) for v in row])
	console.print(table)

def expand_binomial(a_input: str, b_input: str, n: int, use_latex: bool = False) -> None:
	# Developpe (a + b)^n et affiche le detail des termes ainsi que le resultat
	if not isinstance(a_input, str) or not isinstance(b_input, str):
		raise TypeError("a and b must be strings.")
	if not isinstance(n, int):
		raise TypeError("n must be an integer.")
	if n < 0:
		error("n must be a non-negative integer.")
		return
	try:
		sympify(a_input)
	except (SympifyError, SyntaxError, TypeError):
		error(f"'{a_input}' is not a valid mathematical expression.")
		return
	try:
		sympify(b_input)
	except (SympifyError, SyntaxError, TypeError):
		error(f"'{b_input}' is not a valid mathematical expression.")
		return
	try:
		expr: Any = sympify(f"({a_input} + {b_input})**{n}")
		res: Any = expand(expr)
	except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
		error(f"Could not expand expression: {exc}")
		return
	b_stripped: str = b_input.lstrip()
	base_unicode: str
	try:
		if b_stripped.startswith("-"):
			inner_b: str = b_stripped[1:].lstrip()
			base_unicode = (
				f"({format_expr_unicode(a_input)} - {format_expr_unicode(inner_b)})"
				f"{int_to_superscript(n)}"
			)
		else:
			base_unicode = (
				f"({format_expr_unicode(a_input)} + {format_expr_unicode(b_input)})"
				f"{int_to_superscript(n)}"
			)
	except (TypeError, ValueError) as exc:
		error(f"Could not format expression for display: {exc}")
		return
	terms: list[str] = []
	k: int
	for k in range(n + 1):
		c: int = comb(n, k)
		try:
			term_expr: Any = sympify(f"{c} * ({a_input})**{n - k} * ({b_input})**{k}")
			term_expanded: Any = expand(term_expr)
			terms.append(format_expr_unicode(str(term_expanded)))
		except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
			error(f"Could not compute term k={k}: {exc}")
			return
	# Le premier terme s'affiche sans signe devant, les suivants avec + ou -
	joined: str = ""
	idx: int
	term: str
	for idx, term in enumerate(terms):
		stripped: str = term.lstrip()
		if stripped.startswith("-"):
			body: str = stripped[1:].lstrip()
			joined += f"-{body}" if idx == 0 else f" - {body}"
		else:
			joined += stripped if idx == 0 else f" + {stripped}"
	info(f"{base_unicode} = " + joined)
	try:
		res_unicode: str = format_expr_unicode(str(res))
	except (TypeError, ValueError) as exc:
		error(f"Could not format result: {exc}")
		return
	info(f"{' ' * len(base_unicode)} = {res_unicode}")
	if use_latex:
		try:
			console.print(Panel(latex(res), title="LaTeX", border_style="cyan"))
		except Exception as exc:
			error(f"Could not generate LaTeX output: {exc}")

class Command(ABC):
	# Interface commune que doit respecter toute commande du programme
	@abstractmethod
	def run(self) -> None:
		# Point d'entree de la commande
		raise NotImplementedError

class TriangleCommand(Command):
	# Commande affichant une ligne du triangle de Pascal
	def __init__(self, n: int) -> None:
		self.n: int = n

	def run(self) -> None:
		display_pascal_row(self.n)

class BinomialCommand(Command):
	# Commande developpant un binome (a + b)^n
	def __init__(self, a_input: str, b_input: str, n: int, use_latex: bool) -> None:
		self.a_input: str = a_input
		self.b_input: str = b_input
		self.n: int = n
		self.use_latex: bool = use_latex

	def run(self) -> None:
		expand_binomial(self.a_input, self.b_input, self.n, use_latex=self.use_latex)

def run_triangle_interactive() -> None:
	# Recueille le numero de ligne via une invite graphique puis affiche la ligne
	raw: str | None = questionary.text("Numero de la ligne :", style=MENU_STYLE).ask()
	if raw is None:
		return
	if not raw:
		error("No value entered.")
		return
	n: int
	try:
		n = int(raw)
	except ValueError:
		error(f"'{raw}' is not a valid integer.")
		return
	console.print()
	TriangleCommand(n).run()

def run_binomial_interactive() -> None:
	# Recueille a, b, n et l'option LaTeX via des invites graphiques puis developpe le binome
	a_input: str = questionary.text("Valeur ou symbole pour a :", style=MENU_STYLE).ask() or "a"
	b_input: str = questionary.text("Valeur ou symbole pour b :", style=MENU_STYLE).ask() or "b"
	raw_n: str | None = questionary.text("Valeur de n :", style=MENU_STYLE).ask()
	if not raw_n:
		error("No value entered for n.")
		return
	n: int
	try:
		n = int(raw_n)
	except ValueError:
		error(f"'{raw_n}' is not a valid integer.")
		return
	use_latex: bool | None = questionary.confirm("Aussi afficher en LaTeX ?", default=False, style=MENU_STYLE).ask()
	console.print()
	BinomialCommand(a_input, b_input, n, use_latex=bool(use_latex)).run()

def run_interactive_menu(
	preset_mode: str | None = None,
	preset_n: int | None = None,
	preset_a: str | None = None,
	preset_b: str | None = None,
	preset_latex: bool = False,
) -> None:
	# Menu interactif graphique, pre-rempli avec les valeurs deja fournies en argument
	if preset_mode == "1":
		info(f"Mode (pre-selectionne) : {MENU_CHOICES[0]}")
		if preset_n is not None:
			info(f"Numero de ligne (pre-selectionne) : {preset_n}")
			console.print()
			TriangleCommand(preset_n).run()
			return
		run_triangle_interactive()
		return
	if preset_mode == "2":
		info(f"Mode (pre-selectionne) : {MENU_CHOICES[1]}")
		if preset_a is not None and preset_b is not None and preset_n is not None:
			info(f"a = {preset_a}, b = {preset_b}, n = {preset_n} (pre-selectionnes)")
			console.print()
			BinomialCommand(preset_a, preset_b, preset_n, use_latex=preset_latex).run()
			return
		run_binomial_interactive()
		return
	choice: str | None = questionary.select("Que voulez-vous faire ?", choices=MENU_CHOICES, style=MENU_STYLE).ask()
	if choice is None or "Quitter" in choice:
		info(colorize("A bientot !", "green"))
		return
	console.print()
	if "triangle" in choice:
		run_triangle_interactive()
	elif "binome" in choice:
		run_binomial_interactive()

def parse_binomial_arg(raw: str) -> tuple[str, str, str] | None:
	# Parse le format "A,B,N" de --binomial, affiche une erreur et renvoie None si invalide
	parts: list[str] = raw.split(",")
	if len(parts) != 3:
		error(f"'--binomial' expects the format \"A,B,N\", got '{raw}'.")
		return None
	return parts[0].strip(), parts[1].strip(), parts[2].strip()

def build_parser() -> argparse.ArgumentParser:
	# Construit le CLI argparse : options pour le triangle, le binome, LaTeX et le mode interactif
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		prog="pascal_triangle_binomial.py",
		description="Affiche une ligne du triangle de Pascal ou developpe un binome (a + b)^n.",
		epilog=(
			"Exemples :\n"
			"  pascal_triangle_binomial.py --triangle 5\n"
			"  pascal_triangle_binomial.py --binomial \"x,y,3\" --latex\n"
		),
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}", help="Affiche la version du programme et quitte.")
	parser.add_argument("--triangle", type=int, metavar="N", help="Affiche la ligne N du triangle de Pascal (N >= 0).")
	parser.add_argument("--binomial", metavar="A,B,N", help="Developpe le binome (A + B)^N, ex: --binomial \"x,-y,3\".")
	parser.add_argument("--latex", action="store_true", help="Affiche aussi le resultat en notation LaTeX.")
	parser.add_argument("--interactive", action="store_true", help="Force le menu interactif, pre-rempli avec les autres options.")
	return parser

def main() -> None:
	# Point d'entree : parse les arguments, affiche la banniere, puis lance le mode choisi
	parser: argparse.ArgumentParser = build_parser()
	args: argparse.Namespace = parser.parse_args()
	print_banner()
	if args.triangle is not None and not args.interactive and not args.binomial:
		if args.triangle < 0:
			error("N must be a non-negative integer.")
			sys.exit(1)
		TriangleCommand(args.triangle).run()
		return
	if args.binomial and not args.interactive:
		parsed: tuple[str, str, str] | None = parse_binomial_arg(args.binomial)
		if parsed is None:
			sys.exit(1)
		a_input: str
		b_input: str
		n_str: str
		a_input, b_input, n_str = parsed
		n: int
		try:
			n = int(n_str)
		except ValueError:
			error(f"'{n_str}' is not a valid integer for N.")
			sys.exit(1)
		BinomialCommand(a_input, b_input, n, use_latex=args.latex).run()
		return
	preset_mode: str | None = None
	preset_n: int | None = None
	preset_a: str | None = None
	preset_b: str | None = None
	if args.triangle is not None:
		preset_mode = "1"
		preset_n = args.triangle
	if args.binomial:
		parsed = parse_binomial_arg(args.binomial)
		if parsed is None:
			sys.exit(1)
		preset_mode = "2"
		n_str2: str
		preset_a, preset_b, n_str2 = parsed
		try:
			preset_n = int(n_str2)
		except ValueError:
			error(f"'{n_str2}' is not a valid integer for N.")
			sys.exit(1)
	run_interactive_menu(
		preset_mode=preset_mode,
		preset_n=preset_n,
		preset_a=preset_a,
		preset_b=preset_b,
		preset_latex=args.latex,
	)

if __name__ == "__main__":
	main()
