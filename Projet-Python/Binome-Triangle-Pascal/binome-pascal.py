#!/usr/bin/env python3

import argparse
import sys
from math	import comb
from sympy	import sympify, expand, latex, SympifyError

def int_to_superscript(n: int) -> str:
	supers = "⁰¹²³⁴⁵⁶⁷⁸⁹"
	if not isinstance(n, int):
		raise TypeError(f"Expected int, got {type(n).__name__}.")
	negative = n < 0
	result = "".join(supers[int(d)] for d in str(abs(n)))
	return ("⁻" if negative else "") + result

def format_expr_unicode(expr: str) -> str:
	if not isinstance(expr, str):
		raise TypeError(f"Expected str, got {type(expr).__name__}.")
	s = expr.replace("**", "^")
	result = ""
	i = 0
	while i < len(s):
		if s[i] == "^":
			i += 1
			exp = ""
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
	if not isinstance(n, int) or not isinstance(k, int):
		raise TypeError("n and k must be integers.")
	if n < 0 or k < 0:
		raise ValueError("n and k must be non-negative integers.")
	return comb(n, k)

def display_pascal_row(n: int) -> None:
	if not isinstance(n, int):
		raise TypeError("Row number must be an integer.")
	if n < 0:
		print("[ERROR] Row number must be a non-negative integer.", file=sys.stderr)
		return
	row = [coef_binomial(n, k) for k in range(n + 1)]
	print(" | ".join(map(str, row)))

def expand_binomial(a_input: str, b_input: str, n: int, use_latex: bool = False) -> None:
	if not isinstance(a_input, str) or not isinstance(b_input, str):
		raise TypeError("a and b must be strings.")
	if not isinstance(n, int):
		raise TypeError("n must be an integer.")
	if n < 0:
		print("[ERROR] n must be a non-negative integer.", file=sys.stderr)
		return
	try:
		a_sym = sympify(a_input)
	except (SympifyError, SyntaxError, TypeError):
		print(f"[ERROR] '{a_input}' is not a valid mathematical expression.", file=sys.stderr)
		return
	try:
		b_sym = sympify(b_input)
	except (SympifyError, SyntaxError, TypeError):
		print(f"[ERROR] '{b_input}' is not a valid mathematical expression.", file=sys.stderr)
		return
	try:
		expr = sympify(f"({a_input} + {b_input})**{n}")
		res = expand(expr)
	except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
		print(f"[ERROR] Could not expand expression: {exc}", file=sys.stderr)
		return
	b_stripped = b_input.lstrip()
	try:
		if b_stripped.startswith("-"):
			inner_b = b_stripped[1:].lstrip()
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
		print(f"[ERROR] Could not format expression for display: {exc}", file=sys.stderr)
		return
	terms = []
	for k in range(n + 1):
		c = comb(n, k)
		try:
			term_expr = sympify(f"{c} * ({a_input})**{n - k} * ({b_input})**{k}")
			term_expanded = expand(term_expr)
			terms.append(format_expr_unicode(str(term_expanded)))
		except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
			print(f"[ERROR] Could not compute term k={k}: {exc}", file=sys.stderr)
			return
	print(f"{base_unicode} = " + " + ".join(terms))
	try:
		res_unicode = format_expr_unicode(str(res))
	except (TypeError, ValueError) as exc:
		print(f"[ERROR] Could not format result: {exc}", file=sys.stderr)
		return
	print(f"{' ' * len(base_unicode)} = {res_unicode}")
	if use_latex:
		try:
			print(f"\nLaTeX: {latex(res)}")
		except Exception as exc:
			print(f"[ERROR] Could not generate LaTeX output: {exc}", file=sys.stderr)

def prompt(message: str) -> str:
	try:
		return input(message).strip()
	except (EOFError, KeyboardInterrupt):
		print("\nAborted.", file=sys.stderr)
		sys.exit(1)

def interactive_menu(
	preset_mode: str	| None = None,
	preset_n: int		| None = None,
	preset_a: str		| None = None,
	preset_b: str		| None = None,
	preset_latex: bool	= False,
) -> None:
	print("=== MENU ===")
	print("1 - Display a row of Pascal's triangle")
	print("2 - Expand a binomial (a + b)ⁿ")
	if preset_mode is not None:
		choice = preset_mode
		print(f"Mode (pre-selected): {choice}")
	else:
		choice = prompt("Your choice (1 or 2): ")
	if choice == "1":
		if preset_n is not None:
			n = preset_n
			print(f"Row number (pre-selected): {n}")
		else:
			raw = prompt("Row number: ")
			if not raw:
				print("[ERROR] No value entered.", file=sys.stderr)
				return
			try:
				n = int(raw)
			except ValueError:
				print(f"[ERROR] '{raw}' is not a valid integer.", file=sys.stderr)
				return
		print()
		display_pascal_row(n)
	elif choice == "2":
		if preset_a is not None:
			a_input = preset_a
			print(f"Value for a (pre-selected): {a_input}")
		else:
			a_input = prompt("Value or symbol for a: ") or "a"
		if preset_b is not None:
			b_input = preset_b
			print(f"Value for b (pre-selected): {b_input}")
		else:
			b_input = prompt("Value or symbol for b: ") or "b"
		if preset_n is not None:
			n = preset_n
			print(f"Value of n (pre-selected): {n}")
		else:
			raw_n = prompt("Value of n: ")
			if not raw_n:
				print("[ERROR] No value entered for n.", file=sys.stderr)
				return
			try:
				n = int(raw_n)
			except ValueError:
				print(f"[ERROR] '{raw_n}' is not a valid integer.", file=sys.stderr)
				return
		if preset_latex:
			use_latex = True
			print("LaTeX output (pre-selected): yes")
		else:
			latex_answer = prompt("Also display in LaTeX? (y/n): ")
			use_latex = latex_answer == "y"
		print()
		expand_binomial(a_input, b_input, n, use_latex=use_latex)
	else:
		print(f"[ERROR] '{choice}' is not a valid choice. Please enter 1 or 2.", file=sys.stderr)

def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("--triangle",		type=int, metavar="N",				help="Display row N of Pascal's triangle (N >= 0).")
	parser.add_argument("--binomial",		nargs=3,  metavar=("A", "B", "N"),	help="Expand the binomial (A + B)^N.")
	parser.add_argument("--latex",			action="store_true",				help="Also print the result in LaTeX notation.")
	parser.add_argument("--interactive",	action="store_true",				help="Force interactive menu, pre-filling values from other flags.")
	try:
		args = parser.parse_args()
	except SystemExit:
		sys.exit(1)
	if args.triangle is not None and not args.interactive and not args.binomial:
		if args.triangle < 0:
			print("[ERROR] N must be a non-negative integer.", file=sys.stderr)
			sys.exit(1)
		display_pascal_row(args.triangle)
		return
	if args.binomial and not args.interactive:
		a_input, b_input, n_str = args.binomial
		if not n_str:
			print("[ERROR] N must not be empty.", file=sys.stderr)
			sys.exit(1)
		try:
			n = int(n_str)
		except ValueError:
			print(f"[ERROR] '{n_str}' is not a valid integer for N.", file=sys.stderr)
			sys.exit(1)
		expand_binomial(a_input, b_input, n, use_latex=args.latex)
		return
	preset_mode		= None
	preset_n		= None
	preset_a		= None
	preset_b		= None
	if args.triangle is not None:
		preset_mode		= "1"
		preset_n		= args.triangle
	if args.binomial:
		preset_mode = "2"
		preset_a, preset_b, n_str = args.binomial
		try:
			preset_n = int(n_str)
		except ValueError:
			print(f"[ERROR] '{n_str}' is not a valid integer for N.", file=sys.stderr)
			sys.exit(1)
	interactive_menu(
		preset_mode		= preset_mode,
		preset_n		= preset_n,
		preset_a		= preset_a,
		preset_b		= preset_b,
		preset_latex	= args.latex,
	)

if __name__ == "__main__":
	main()
