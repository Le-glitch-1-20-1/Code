#!/usr/bin/env python3

from fractions import Fraction

_SP = None

def _sp():
	global _SP
	if _SP is None:
		import sympy as sp
		_SP = sp
	return _SP

def _est_complexe_tuple(val):
	return isinstance(val, tuple) and len(val) == 2

def _valider_reel_float(x):
	if x != x or abs(x) == float("inf"):
		raise ValueError("Les valeurs NaN et infinies ne sont pas autorisées.")

def _fraction_si_rationnel(expr):
	sp = _sp()
	if isinstance(expr, sp.Integer):
		return Fraction(int(expr), 1)
	if isinstance(expr, sp.Rational):
		return Fraction(int(expr.p), int(expr.q))
	return expr

def _entier_strict_positif(val, msg):
	if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
		raise ValueError(msg)
	return val

def _expr_vers_exact(expr):
	sp = _sp()
	if expr.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
		raise ValueError("Les valeurs NaN et infinies ne sont pas autorisées.")
	return _fraction_si_rationnel(expr)

def _est_sympy(val):
	return _SP is not None and isinstance(val, _SP.Basic)

def to_exact_val(val):
	if isinstance(val, bool):
		raise ValueError("Les booléens ne sont pas autorisés.")
	if isinstance(val, Fraction):
		return val
	if isinstance(val, int):
		return Fraction(val, 1)
	if isinstance(val, float):
		_valider_reel_float(val)
		return Fraction(str(val))
	if isinstance(val, complex):
		_valider_reel_float(val.real)
		_valider_reel_float(val.imag)
		sp = _sp()
		re = sp.Rational(Fraction(str(val.real)))
		im = sp.Rational(Fraction(str(val.imag)))
		return _expr_vers_exact(re + sp.I * im)
	if _est_complexe_tuple(val):
		sp = _sp()
		return _expr_vers_exact(to_sympy(val[0]) + sp.I * to_sympy(val[1]))
	if _est_sympy(val):
		return _expr_vers_exact(val)
	if isinstance(val, str):
		texte = val.strip()
		if not texte:
			raise ValueError("Chaîne vide non autorisée.")
		try:
			return Fraction(texte)
		except ValueError:
			pass
		sp = _sp()
		try:
			expr = sp.sympify(texte, locals={"i": sp.I})
		except Exception as exc:
			raise ValueError(f"Valeur invalide : {val!r}") from exc
		return _expr_vers_exact(expr)
	raise TypeError(f"Type non supporté : {type(val).__name__}")

def to_sympy(val):
	v = to_exact_val(val)
	if isinstance(v, Fraction):
		return _sp().Rational(v.numerator, v.denominator)
	return v

def _est_nul_norm(v):
	if isinstance(v, Fraction):
		return v == 0
	return bool(_sp().simplify(v) == 0)

def _est_nul(val):
	return _est_nul_norm(to_exact_val(val))

def _cle_pivot(val):
	v = to_exact_val(val)
	if _est_nul_norm(v):
		return (-1, 0.0)
	if isinstance(v, Fraction):
		return (2, float(abs(v)))
	sp = _sp()
	if v.is_number and not v.has(sp.Symbol):
		try:
			return (2, float(sp.Abs(v).evalf()))
		except Exception:
			pass
	return (1, -float(sp.count_ops(v)))

def _op_scalaire(a, b, f_op, sp_op, division=False):
	va, vb = to_exact_val(a), to_exact_val(b)
	if isinstance(va, Fraction) and isinstance(vb, Fraction):
		if division and vb == 0:
			raise ZeroDivisionError("Division par zéro.")
		return f_op(va, vb)
	sp = _sp()
	sa, sb = to_sympy(va), to_sympy(vb)
	if division and _est_nul_norm(sb):
		raise ZeroDivisionError("Division par zéro.")
	return _fraction_si_rationnel(sp.simplify(sp_op(sa, sb)))

def _c_add(a, b):
	return _op_scalaire(a, b, lambda x, y: x + y, lambda x, y: x + y)

def _c_sous(a, b):
	return _op_scalaire(a, b, lambda x, y: x - y, lambda x, y: x - y)

def _c_mult(a, b):
	return _op_scalaire(a, b, lambda x, y: x * y, lambda x, y: x * y)

def _c_div(a, b):
	return _op_scalaire(a, b, lambda x, y: x / y, lambda x, y: x / y, division=True)

def fmt_val(val):
	v = to_exact_val(val)
	if isinstance(v, Fraction):
		return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
	return str(v).replace("**", "^").replace("*", "") if v.is_Atom else str(v)

def valider_scalaire(val, nom="scalaire", autoriser_zero=True):
	v = to_exact_val(val)
	if not autoriser_zero and _est_nul_norm(v):
		raise ZeroDivisionError(f"Le paramètre '{nom}' ne peut pas être nul.")
	return v

def _matrice(l, c, remplir):
	return [[remplir(i, j) for j in range(c)] for i in range(l)]

def _dimensions(mat):
	return len(mat), len(mat[0])

def valider_matrice_2d(M, nom="M"):
	if _est_sympy(M) and hasattr(M, "rows") and hasattr(M, "cols"):
		if M.rows == 0 or M.cols == 0:
			raise ValueError(f"'{nom}' doit être une matrice non vide à 2 dimensions.")
		return _matrice(M.rows, M.cols, lambda i, j: to_exact_val(M[i, j]))
	if not isinstance(M, (list, tuple)) or len(M) == 0:
		raise ValueError(f"'{nom}' doit être une matrice non vide à 2 dimensions.")
	nb_cols = len(M[0])
	if not all(isinstance(ligne, (list, tuple)) and len(ligne) == nb_cols and nb_cols > 0 for ligne in M):
		raise ValueError(f"'{nom}' doit être une matrice rectangulaire non vide à 2 dimensions.")
	return _matrice(len(M), nb_cols, lambda i, j: to_exact_val(M[i][j]))

def valider_matrice_carree(M, nom="M"):
	mat = valider_matrice_2d(M, nom=nom)
	l, c = _dimensions(mat)
	if l != c:
		raise ValueError(f"'{nom}' doit être une matrice carrée (reçu {(l, c)}).")
	return mat

def identite(n):
	_entier_strict_positif(n, "La taille de la matrice identité doit être un entier strictement positif.")
	return _matrice(n, n, lambda i, j: Fraction(1, 1) if i == j else Fraction(0, 1))

def _op_terme_a_terme(A, B, op, nom_op):
	mat_A = valider_matrice_2d(A, "A")
	mat_B = valider_matrice_2d(B, "B")
	dim_A, dim_B = _dimensions(mat_A), _dimensions(mat_B)
	if dim_A != dim_B:
		raise ValueError(f"Dimensions incompatibles pour {nom_op} : {dim_A} et {dim_B}.")
	l, c = dim_A
	return _matrice(l, c, lambda i, j: op(mat_A[i][j], mat_B[i][j]))

def add(A, B):
	return _op_terme_a_terme(A, B, _c_add, "l'addition")

def sous(A, B):
	return _op_terme_a_terme(A, B, _c_sous, "la soustraction")

def mult(A, B=None, scalaire=None):
	mat_A = valider_matrice_2d(A, "A")
	if B is None and scalaire is None:
		raise ValueError("Vous devez fournir une matrice 'B' ou un 'scalaire'.")
	facteur = Fraction(1, 1) if scalaire is None else valider_scalaire(scalaire, "scalaire")
	l, c = _dimensions(mat_A)
	if B is None:
		return _matrice(l, c, lambda i, j: _c_mult(mat_A[i][j], facteur))
	mat_B = valider_matrice_2d(B, "B")
	n, m = _dimensions(mat_B)
	if c != n:
		raise ValueError(f"Dimensions incompatibles pour la multiplication matricielle : {(l, c)} et {(n, m)}.")

	def produit(i, j):
		somme = Fraction(0, 1)
		for k in range(c):
			somme = _c_add(somme, _c_mult(mat_A[i][k], mat_B[k][j]))
		return _c_mult(somme, facteur)

	return _matrice(l, m, produit)

def puissance(M, n):
	if isinstance(n, bool) or not isinstance(n, int):
		raise ValueError("L'exposant doit être un entier.")
	mat = valider_matrice_carree(M, "M")
	taille, _ = _dimensions(mat)
	resultat = identite(taille)
	if n == 0:
		return resultat
	base = inverse(mat) if n < 0 else mat
	exp = abs(n)
	while exp > 0:
		if exp % 2 == 1:
			resultat = mult(resultat, base)
		exp //= 2
		if exp > 0:
			base = mult(base, base)
	return resultat

def div(A, B=None, scalaire=None):
	mat_A = valider_matrice_2d(A, "A")
	if scalaire is not None and B is not None:
		raise ValueError("Spécifiez soit 'B' (matrice), soit 'scalaire', pas les deux.")
	if scalaire is not None:
		s = valider_scalaire(scalaire, "scalaire", autoriser_zero=False)
		l, c = _dimensions(mat_A)
		return _matrice(l, c, lambda i, j: _c_div(mat_A[i][j], s))
	if B is None:
		raise ValueError("Vous devez fournir une matrice 'B' ou un 'scalaire'.")
	mat_B = valider_matrice_carree(B, "B")
	_, c_A = _dimensions(mat_A)
	n_B, _ = _dimensions(mat_B)
	if c_A != n_B:
		raise ValueError(f"Dimensions incompatibles pour la division matricielle : {_dimensions(mat_A)} et {(n_B, n_B)}.")
	return mult(mat_A, inverse(mat_B))

def afficher_matrice(titre, M, sep=None):
	if isinstance(M, (int, float, complex, Fraction)) or _est_complexe_tuple(M) or _est_sympy(M):
		print(f"\n{titre} : {fmt_val(M)}")
		return
	arr = valider_matrice_2d(M, titre)
	l, c = _dimensions(arr)
	cellules = [[fmt_val(x) for x in ligne] for ligne in arr]
	largeurs = [max(len(cellules[i][j]) for i in range(l)) for j in range(c)]
	print(f"\n{titre} :")
	for ligne in cellules:
		parties = []
		for j, val in enumerate(ligne):
			if sep is not None and j == sep:
				parties.append("|")
			parties.append(val.rjust(largeurs[j]))
		print(f"  [ {'  '.join(parties)} ]")

def sous_matrice(m, ligne, col):
	mat = valider_matrice_2d(m, "m")
	l, c = _dimensions(mat)
	if l <= 2 or c <= 2:
		raise ValueError("sous_matrice ne doit être appelée que sur une matrice d'au moins 3x3 pour produire au minimum du 2x2.")
	if not (0 <= ligne < l) or not (0 <= col < c):
		raise IndexError(f"Indices ({ligne}, {col}) hors limites pour une matrice de taille {(l, c)}.")
	return [[mat[i][j] for j in range(c) if j != col] for i in range(l) if i != ligne]

def _verifier_max_dim(n, max_dim):
	if max_dim is not None and n > max_dim:
		raise ValueError(f"Dimension {n} supérieure à la limite ({max_dim}).")

def det(M, max_dim=None):
	mat = valider_matrice_carree(M, "M")
	n, _ = _dimensions(mat)
	_verifier_max_dim(n, max_dim)
	if n == 1:
		return mat[0][0]
	if n == 2:
		return _c_sous(_c_mult(mat[0][0], mat[1][1]), _c_mult(mat[1][0], mat[0][1]))
	total = Fraction(0, 1)
	for l in range(n):
		coeff = mat[l][0]
		if not _est_nul_norm(coeff):
			signe = Fraction(-1 if l % 2 else 1, 1)
			mineur = det(sous_matrice(mat, l, 0), max_dim=max_dim)
			total = _c_add(total, _c_mult(_c_mult(signe, coeff), mineur))
	return _fraction_si_rationnel(_sp().simplify(to_sympy(total))) if _est_sympy(total) else total

def cof(M, max_dim=None):
	mat = valider_matrice_carree(M, "M")
	n, _ = _dimensions(mat)
	_verifier_max_dim(n, max_dim)
	if n == 1:
		return _matrice(1, 1, lambda i, j: Fraction(1, 1))
	if n == 2:
		a, b = mat[0][0], mat[0][1]
		c_val, d_val = mat[1][0], mat[1][1]
		valeurs = [d_val, _c_mult(Fraction(-1, 1), c_val), _c_mult(Fraction(-1, 1), b), a]
		return _matrice(2, 2, lambda i, j: valeurs[i * 2 + j])

	def cofacteur(l, c):
		signe = Fraction(-1 if (l + c) % 2 else 1, 1)
		mineur = det(sous_matrice(mat, l, c), max_dim=max_dim)
		return _c_mult(signe, mineur)

	return _matrice(n, n, cofacteur)

def transposee(M):
	mat = valider_matrice_2d(M, "M")
	l, c = _dimensions(mat)
	return _matrice(c, l, lambda j, i: mat[i][j])

def inverse(M):
	mat = valider_matrice_carree(M, "M")
	n, _ = _dimensions(mat)
	B = [list(mat[i]) + [Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(n)] for i in range(n)]
	reduite, _ = gauss_jordan(B, colonnes_systeme=n)
	if any(_est_nul_norm(reduite[i][i]) for i in range(n)):
		raise ValueError("La matrice n'est pas inversible (déterminant nul).")
	return [ligne[n:] for ligne in reduite]

def _pivot_generique(M, colonnes_systeme=None, reduire_complet=False):
	mat = valider_matrice_2d(M, "M")
	l, c = _dimensions(mat)
	if colonnes_systeme is None:
		nb_cols = c
	else:
		_entier_strict_positif(colonnes_systeme, f"'colonnes_systeme' doit être un entier entre 1 et {c}.")
		if colonnes_systeme > c:
			raise ValueError(f"'colonnes_systeme' doit être un entier entre 1 et {c}.")
		nb_cols = colonnes_systeme
	B = [list(ligne) for ligne in mat]
	ligne_pivot = 0
	for col in range(nb_cols):
		if ligne_pivot >= l:
			break
		pivot_row = max(range(ligne_pivot, l), key=lambda r: _cle_pivot(B[r][col]))
		if _est_nul_norm(B[pivot_row][col]):
			continue
		if pivot_row != ligne_pivot:
			B[ligne_pivot], B[pivot_row] = B[pivot_row], B[ligne_pivot]
		if reduire_complet:
			pivot = B[ligne_pivot][col]
			B[ligne_pivot] = [_c_div(val, pivot) for val in B[ligne_pivot]]
			lignes_cibles = (i for i in range(l) if i != ligne_pivot)
		else:
			lignes_cibles = range(ligne_pivot + 1, l)
		pivot = B[ligne_pivot][col]
		for i in lignes_cibles:
			if not _est_nul_norm(B[i][col]):
				facteur = _c_div(B[i][col], pivot)
				B[i] = [_c_sous(B[i][j], _c_mult(facteur, B[ligne_pivot][j])) for j in range(c)]
		ligne_pivot += 1
	for i in range(l):
		for j in range(c):
			val = B[i][j]
			if _est_sympy(val):
				B[i][j] = _fraction_si_rationnel(_sp().simplify(val))
	return B, (nb_cols if nb_cols < c else None)

def gauss(M, colonnes_systeme=None):
	return _pivot_generique(M, colonnes_systeme=colonnes_systeme, reduire_complet=False)

def gauss_jordan(M, colonnes_systeme=None):
	return _pivot_generique(M, colonnes_systeme=colonnes_systeme, reduire_complet=True)

def factorielle_rapide(m: int) -> int:
	if isinstance(m, bool) or not isinstance(m, int) or m < 0:
		raise ValueError("m doit être un entier positif ou nul.")
	res = 1
	for i in range(2, m + 1):
		res *= i
	return res

def k_parmi_n_factorise_base(n, k: int, factoriser_fin: bool = True):
	if not isinstance(k, int) or isinstance(k, bool):
		raise TypeError("k doit être un entier concret.")
	if k < 0:
		return Fraction(0, 1)
	if k == 0:
		return Fraction(1, 1)
	n_exact = to_exact_val(n)
	fact_k = factorielle_rapide(k)
	if isinstance(n_exact, Fraction):
		prod_num = Fraction(1, 1)
		for i in range(k):
			prod_num *= (n_exact - Fraction(i, 1))
		return prod_num / Fraction(fact_k, 1)
	sp = _sp()
	n_sym = to_sympy(n_exact)
	prod_num = sp.Integer(1)
	for i in range(k):
		prod_num *= n_sym - i
	expr = sp.Mul(sp.Rational(1, fact_k), prod_num, evaluate=False)
	if factoriser_fin:
		return _fraction_si_rationnel(sp.factor(expr))
	return _fraction_si_rationnel(sp.simplify(expr) if not n_sym.is_Symbol else expr)

def indice_nilpotence_matrice(N, max_k=None):
	mat = valider_matrice_carree(N, "N")
	n, _ = _dimensions(mat)
	limite = n if max_k is None else max_k
	courante = identite(n)
	for k in range(1, limite + 1):
		courante = mult(courante, mat)
		if all(_est_nul_norm(courante[i][j]) for i in range(n) for j in range(n)):
			return k
	return None

def puissance_n_symbolique(A, sym_n=None, max_k=None):
	sp = _sp()
	if sym_n is None:
		sym_n = sp.Symbol("n", integer=True, nonnegative=True)
	mat = valider_matrice_carree(A, "A")
	n, _ = _dimensions(mat)
	lam = mat[0][0]
	if all(_est_nul_norm(_c_sous(mat[i][i], lam)) for i in range(1, n)):
		N = sous(mat, mult(identite(n), scalaire=lam))
		idx = indice_nilpotence_matrice(N, max_k=max_k)
		if idx is not None:
			resultat = _matrice(n, n, lambda i, j: Fraction(0, 1))
			lam_sym = to_sympy(lam)
			for k in range(idx):
				coeff_binom = to_sympy(k_parmi_n_factorise_base(sym_n, k))
				facteur = sp.simplify(coeff_binom * (lam_sym ** (sym_n - k)))
				resultat = add(resultat, mult(puissance(N, k), scalaire=facteur))
			return resultat, f"Binôme de Newton (A = {fmt_val(lam)}*I + N, N^{idx} = 0)"
	sp_mat = sp.Matrix(n, n, lambda i, j: to_sympy(mat[i][j]))
	try:
		res_sp = sp.simplify(sp_mat ** sym_n)
		return _matrice(n, n, lambda i, j: to_exact_val(res_sp[i, j])), "Diagonalisation / Forme de Jordan (SymPy)"
	except Exception as exc:
		raise ValueError(f"Impossible de calculer A^n symboliquement : {exc}") from exc

def _demander_entier(message):
	while True:
		try:
			return int(input(message).strip())
		except ValueError:
			print("Entier invalide.")

def _demander_entier_positif(message):
	while True:
		val = _demander_entier(message)
		if val > 0:
			return val
		print("Entier > 0 requis.")

def saisir_matrice_manuellement(nom="M", l=None, c=None):
	if l is None and c is None:
		n = _demander_entier_positif(f"Taille {nom} (n x n) : ")
		l = c = n
	elif l is None:
		l = _demander_entier_positif(f"Lignes {nom} : ")
	elif c is None:
		c = _demander_entier_positif(f"Colonnes {nom} : ")
	print(f"\n--- {nom} ({l}x{c}) | '1 -2 3/4' ou '1+2*i, 0, a' ---")
	lignes = []
	for i in range(l):
		while True:
			brute = input(f"L{i + 1}/{l} : ").strip()
			elements = [el.strip() for el in (brute.split(",") if "," in brute else brute.split()) if el.strip()]
			if len(elements) != c:
				print(f"Attendu {c}, reçu {len(elements)}.")
				continue
			try:
				lignes.append([to_exact_val(el) for el in elements])
				break
			except Exception as exc:
				print(f"Erreur : {exc}")
	return valider_matrice_2d(lignes, nom=nom)

def _demander_scalaire(nom="k", autoriser_zero=True):
	while True:
		saisie = input(f"Scalaire {nom} : ").strip()
		try:
			return valider_scalaire(saisie, nom=nom, autoriser_zero=autoriser_zero)
		except Exception as exc:
			print(f"Erreur : {exc}")

def _demander_colonnes_sep(nb_cols):
	if nb_cols <= 1:
		return None
	rep = input(f"Colonnes à gauche de '|' (Entrée = aucune, 1..{nb_cols - 1}) : ").strip()
	if not rep:
		return None
	val = int(rep)
	if not (1 <= val < nb_cols):
		raise ValueError(f"Séparateur entre 1 et {nb_cols - 1} requis.")
	return val

def executer_operation_menu(choix):
	if choix in {"1", "2"}:
        l = _demander_entier_positif("Nombre de lignes de A et B : ")
        n = _demander_entier_positif("Nombre de colones de A et B : ")
        A = saisir_matrice_manuellement("A", l=l, c=c)
		B = saisir_matrice_manuellement("B", l=l, c=c)
		if choix == "1":
			afficher_matrice("A + B", add(A, B))
		else:
			afficher_matrice("A - B", sous(A, B))
	elif choix == "3":
		print("\n[mult] 1: A * B | 2: A * k")
		sous_choix = input("Mode : ").strip()
		if sous_choix == "1":
			l = _demander_entier_positif("Nombre de lignes de A : ")
			c = _demander_entier_positif("Nombre de colonnes de A | Nombre de lignes de B : ")
			m = _demander_entier_positif("Nombre de Colonnes de B : ")
			A = saisir_matrice_manuellement("A", l=l, c=c)
			B = saisir_matrice_manuellement("B", l=c, c=m)
			afficher_matrice("A * B", mult(A, B=B))
		elif sous_choix == "2":
            l = _demander_entier_positif("Nombre de lignes de A : ")
			c = _demander_entier_positif("Nombre de colones de A : ")
			A = saisir_matrice_manuellement("A", l=l, c=c)
			s = _demander_scalaire("k", autoriser_zero=True)
			afficher_matrice(f"A * ({fmt_val(s)})", mult(A, scalaire=s))
		else:
			print("Mode invalide.")
	elif choix == "4":
		print("\n[div] 1: A / B | 2: A / k")
		sous_choix = input("Mode : ").strip()
		if sous_choix == "1":
			A = saisir_matrice_manuellement("A")
			B = saisir_matrice_manuellement("B")
			afficher_matrice("A / B", div(A, B=B))
		elif sous_choix == "2":
			A = saisir_matrice_manuellement("A")
			s = _demander_scalaire("k", autoriser_zero=False)
			afficher_matrice(f"A / ({fmt_val(s)})", div(A, scalaire=s))
		else:
			print("Mode invalide.")
	elif choix == "5":
		print("\n[puissance] A ^ k")
		A = saisir_matrice_manuellement("A")
		k = _demander_entier("Exposant k : ")
		afficher_matrice(f"A ^ ({k})", puissance(A, k))
	elif choix == "6":
		print("\n[det] det(A)")
		A = saisir_matrice_manuellement("A")
		afficher_matrice("det(A)", det(A))
	elif choix == "7":
		print("\n[cof] cof(A)")
		A = saisir_matrice_manuellement("A")
		afficher_matrice("cof(A)", cof(A))
	elif choix == "8":
		print("\n[transposee] A ^ T")
		A = saisir_matrice_manuellement("A")
		afficher_matrice("A ^ T", transposee(A))
	elif choix == "9":
		print("\n[inverse] A ^ (-1)")
		A = saisir_matrice_manuellement("A")
		afficher_matrice("A ^ (-1)", inverse(A))
	elif choix == "10":
		print("\n[gauss] Pivot de Gauss")
		A = saisir_matrice_manuellement("A")
		_, c = _dimensions(A)
		sep_in = _demander_colonnes_sep(c)
		g, sep = gauss(A, colonnes_systeme=sep_in)
		afficher_matrice("Gauss", g, sep=sep)
	elif choix == "11":
		print("\n[gauss_jordan] Gauss-Jordan")
		A = saisir_matrice_manuellement("A")
		_, c = _dimensions(A)
		sep_in = _demander_colonnes_sep(c)
		gj, sep = gauss_jordan(A, colonnes_systeme=sep_in)
		afficher_matrice("Gauss-Jordan", gj, sep=sep)
	elif choix == "12":
		print("\n[puissance_n] A ^ n")
		A = saisir_matrice_manuellement("A")
		An, methode = puissance_n_symbolique(A)
		print(f"Méthode : {methode}")
		afficher_matrice("A ^ n", An)

def main():
	while True:
		print("\n=== Menu des opérations ===")
		print("  1. add           --> A + B")
		print("  2. sous          --> A - B")
		print("  3. mult          --> A * B | A * k")
		print("  4. div           --> A / B | A / k")
		print("  5. puissance     --> A ^ k")
		print("  6. det           --> Déterminant")
		print("  7. cof           --> Comatrice")
		print("  8. transposee    --> Transposée")
		print("  9. inverse       --> Inverse")
		print(" 10. gauss         --> Pivot de Gauss")
		print(" 11. gauss_jordan  --> Gauss-Jordan")
		print(" 12. puissance_n   --> A ^ n")
		print("  0. quitter")
		choix = input("Choix : ").strip()
		if choix == "0":
			break
		if choix not in {str(i) for i in range(1, 13)}:
			print("Choix invalide.")
			continue
		try:
			executer_operation_menu(choix)
		except Exception as exc:
			print(f"\n[Erreur] {exc}")

if __name__ == "__main__":
    main()
