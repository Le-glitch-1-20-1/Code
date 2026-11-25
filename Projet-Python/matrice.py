#!/usr/bin/env python3

from fractions import Fraction
import sympy as sp

MAX_COFACTOR_DIM = 10

def _est_complexe_tuple(val):
    return isinstance(val, tuple) and len(val) == 2

def _valider_reel_float(x):
    if x != x or abs(x) == float("inf"):
        raise ValueError("Les valeurs NaN et infinies ne sont pas autorisées.")

def _fraction_si_rationnel(expr):
    if isinstance(expr, sp.Integer):
        return Fraction(int(expr), 1)
    if isinstance(expr, sp.Rational):
        return Fraction(int(expr.p), int(expr.q))
    return expr

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
        re = sp.Rational(Fraction(str(val.real)))
        im = sp.Rational(Fraction(str(val.imag)))
        expr = sp.simplify(re + sp.I * im)
        if expr.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
            raise ValueError("Les valeurs NaN et infinies ne sont pas autorisées.")
        return _fraction_si_rationnel(expr)
    if _est_complexe_tuple(val):
        re = to_sympy(val[0])
        im = to_sympy(val[1])
        expr = sp.simplify(re + sp.I * im)
        if expr.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
            raise ValueError("Les valeurs NaN et infinies ne sont pas autorisées.")
        return _fraction_si_rationnel(expr)
    if isinstance(val, sp.Basic):
        if val.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
            raise ValueError("Les valeurs NaN et infinies ne sont pas autorisées.")
        expr = sp.simplify(val)
        return _fraction_si_rationnel(expr)
    if isinstance(val, str):
        texte = val.strip()
        if not texte:
            raise ValueError("Chaîne vide non autorisée.")
        try:
            return Fraction(texte)
        except ValueError:
            pass
        try:
            expr = sp.sympify(texte, locals={"i": sp.I})
        except Exception as exc:
            raise ValueError(f"Valeur invalide : {val!r}") from exc
        if expr.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
            raise ValueError("Les valeurs NaN et infinies ne sont pas autorisées.")
        expr = sp.simplify(expr)
        return _fraction_si_rationnel(expr)
    raise TypeError(f"Type non supporté : {type(val).__name__}")

def to_sympy(val):
    v = to_exact_val(val)
    if isinstance(v, Fraction):
        return sp.Rational(v.numerator, v.denominator)
    return v

def _est_nul(val):
    v = to_exact_val(val)
    if isinstance(v, Fraction):
        return v == 0
    return bool(sp.simplify(v) == 0)

def _cle_pivot(val):
    v = to_exact_val(val)
    if _est_nul(v):
        return (-1, 0.0)
    if isinstance(v, Fraction):
        return (2, float(abs(v)))
    if v.is_number and not v.has(sp.Symbol):
        try:
            return (2, float(sp.Abs(v).evalf()))
        except Exception:
            pass
    return (1, -float(sp.count_ops(v)))

def _c_add(a, b):
    va, vb = to_exact_val(a), to_exact_val(b)
    if isinstance(va, Fraction) and isinstance(vb, Fraction):
        return va + vb
    return _fraction_si_rationnel(sp.simplify(to_sympy(va) + to_sympy(vb)))

def _c_sous(a, b):
    va, vb = to_exact_val(a), to_exact_val(b)
    if isinstance(va, Fraction) and isinstance(vb, Fraction):
        return va - vb
    return _fraction_si_rationnel(sp.simplify(to_sympy(va) - to_sympy(vb)))

def _c_mult(a, b):
    va, vb = to_exact_val(a), to_exact_val(b)
    if isinstance(va, Fraction) and isinstance(vb, Fraction):
        return va * vb
    return _fraction_si_rationnel(sp.simplify(to_sympy(va) * to_sympy(vb)))

def _c_div(a, b):
    va, vb = to_exact_val(a), to_exact_val(b)
    if isinstance(va, Fraction) and isinstance(vb, Fraction):
        if vb == 0:
            raise ZeroDivisionError("Division par zéro.")
        return va / vb
    num, den = to_sympy(va), to_sympy(vb)
    if _est_nul(den):
        raise ZeroDivisionError("Division par zéro.")
    return _fraction_si_rationnel(sp.simplify(num / den))

def fmt_val(val):
    v = to_exact_val(val)
    if isinstance(v, Fraction):
        return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    return str(v).replace("**", "^").replace("*", "") if v.is_Atom else str(v)

def valider_scalaire(val, nom="scalaire", autoriser_zero=True):
    v = to_exact_val(val)
    if not autoriser_zero and _est_nul(v):
        raise ZeroDivisionError(f"Le paramètre '{nom}' ne peut pas être nul.")
    return v

def _matrice(l, c, remplir):
    return [[remplir(i, j) for j in range(c)] for i in range(l)]

def _dimensions(mat):
    return len(mat), len(mat[0])

def valider_matrice_2d(M, nom="M"):
    if isinstance(M, sp.MatrixBase):
        if M.rows == 0 or M.cols == 0:
            raise ValueError(f"'{nom}' doit être une matrice non vide à 2 dimensions.")
        return _matrice(M.rows, M.cols, lambda i, j: to_exact_val(M[i, j]))
    if not isinstance(M, (list, tuple)) or len(M) == 0:
        raise ValueError(f"'{nom}' doit être une matrice non vide à 2 dimensions.")
    l = len(M)
    if not all(isinstance(ligne, (list, tuple)) and len(ligne) == len(M[0]) and len(ligne) > 0 for ligne in M):
        raise ValueError(f"'{nom}' doit être une matrice rectangulaire non vide à 2 dimensions.")
    c = len(M[0])
    return _matrice(l, c, lambda i, j: to_exact_val(M[i][j]))

def valider_matrice_carree(M, nom="M"):
    mat = valider_matrice_2d(M, nom=nom)
    l, c = _dimensions(mat)
    if l != c:
        raise ValueError(f"'{nom}' doit être une matrice carrée (reçu {(l, c)}).")
    return mat

def identite(n):
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError("La taille de la matrice identité doit être un entier strictement positif.")
    return _matrice(n, n, lambda i, j: Fraction(1, 1) if i == j else Fraction(0, 1))

def _op_terme_a_terme(A, B, op, nom_op):
    mat_A = valider_matrice_2d(A, "A")
    mat_B = valider_matrice_2d(B, "B")
    dim_A = _dimensions(mat_A)
    dim_B = _dimensions(mat_B)
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
    return mult(mat_A, inverse(B))

def afficher_matrice(titre, M, sep=None):
    if isinstance(M, (int, float, complex, Fraction, sp.Basic)) or _est_complexe_tuple(M):
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
    return [
        [mat[i][j] for j in range(c) if j != col]
        for i in range(l)
        if i != ligne
    ]

def det(M, max_dim=MAX_COFACTOR_DIM):
    mat = valider_matrice_carree(M, "M")
    n, _ = _dimensions(mat)
    if n > max_dim:
        raise ValueError(f"Dimension {n} supérieure à la limite sécurisée ({max_dim}) pour le calcul par cofacteurs.")
    if n == 1:
        return to_exact_val(mat[0][0])
    if n == 2:
        return _c_sous(_c_mult(mat[0][0], mat[1][1]), _c_mult(mat[1][0], mat[0][1]))
    total = Fraction(0, 1)
    for l in range(n):
        coeff = to_exact_val(mat[l][0])
        if not _est_nul(coeff):
            signe = Fraction(-1 if l % 2 else 1, 1)
            mineur = det(sous_matrice(mat, l, 0), max_dim=max_dim)
            total = _c_add(total, _c_mult(_c_mult(signe, coeff), mineur))
    return _fraction_si_rationnel(sp.simplify(to_sympy(total))) if isinstance(total, sp.Basic) else total

def cof(M, max_dim=MAX_COFACTOR_DIM):
    mat = valider_matrice_carree(M, "M")
    n, _ = _dimensions(mat)
    if n > max_dim:
        raise ValueError(f"Dimension {n} supérieure à la limite sécurisée ({max_dim}) pour la comatrice.")
    if n == 1:
        return _matrice(1, 1, lambda i, j: Fraction(1, 1))
    if n == 2:
        a, b = to_exact_val(mat[0][0]), to_exact_val(mat[0][1])
        c_val, d_val = to_exact_val(mat[1][0]), to_exact_val(mat[1][1])
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
    return _matrice(c, l, lambda j, i: to_exact_val(mat[i][j]))

def inverse(M, max_dim=MAX_COFACTOR_DIM):
    mat = valider_matrice_carree(M, "M")
    d = det(mat, max_dim=max_dim)
    if _est_nul(d):
        raise ValueError("La matrice n'est pas inversible (déterminant nul).")
    adj = transposee(cof(mat, max_dim=max_dim))
    n, _ = _dimensions(adj)
    return _matrice(n, n, lambda l, c: _c_div(adj[l][c], d))

def _pivot_augmentee(M):
    mat = valider_matrice_carree(M, "M")
    n, _ = _dimensions(mat)
    B = []
    for i in range(n):
        ligne = [to_exact_val(mat[i][j]) for j in range(n)]
        ligne.extend(Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(n))
        B.append(ligne)
    return B, n

def _finaliser_augmentee(B, n):
    for i in range(n):
        for j in range(2 * n):
            val = to_exact_val(B[i][j])
            if isinstance(val, sp.Basic):
                val = _fraction_si_rationnel(sp.simplify(val))
            B[i][j] = val
    return B, n

def gauss_jordan(M):
    B, n = _pivot_augmentee(M)
    for k in range(n):
        pivot_row = max(range(k, n), key=lambda r: _cle_pivot(B[r][k]))
        if _est_nul(B[pivot_row][k]):
            raise ValueError("La matrice est singulière (non inversible).")
        if pivot_row != k:
            B[k], B[pivot_row] = B[pivot_row], B[k]
        pivot = B[k][k]
        B[k] = [_c_div(val, pivot) for val in B[k]]
        for i in range(n):
            if i != k and not _est_nul(B[i][k]):
                facteur = B[i][k]
                B[i] = [_c_sous(B[i][j], _c_mult(facteur, B[k][j])) for j in range(2 * n)]
    return _finaliser_augmentee(B, n)

def gauss(M):
    B, n = _pivot_augmentee(M)
    for k in range(n):
        pivot_row = max(range(k, n), key=lambda r: _cle_pivot(B[r][k]))
        if _est_nul(B[pivot_row][k]):
            raise ValueError("La matrice est singulière (non inversible).")
        if pivot_row != k:
            B[k], B[pivot_row] = B[pivot_row], B[k]
        pivot = B[k][k]
        for i in range(k + 1, n):
            if not _est_nul(B[i][k]):
                facteur = _c_div(B[i][k], pivot)
                B[i] = [_c_sous(B[i][j], _c_mult(facteur, B[k][j])) for j in range(2 * n)]
    return _finaliser_augmentee(B, n)

def factorielle_rapide(m: int) -> int:
    if not isinstance(m, int) or isinstance(m, bool) or m < 0:
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
    n_sym = to_sympy(n_exact)
    prod_num = sp.Integer(1)
    for i in range(k):
        prod_num *= n_sym - i
    expr = sp.Mul(sp.Rational(1, fact_k), prod_num, evaluate=False)
    if factoriser_fin:
        return _fraction_si_rationnel(sp.factor(expr))
    return _fraction_si_rationnel(sp.simplify(expr) if not n_sym.is_Symbol else expr)

def indice_nilpotence_matrice(N, max_k=8):
    n, _ = _dimensions(N)
    courante = identite(n)
    for k in range(1, max_k + 1):
        courante = mult(courante, N)
        if all(_est_nul(courante[i][j]) for i in range(n) for j in range(n)):
            return k
    return None

def puissance_n_symbolique(A, sym_n=sp.Symbol("n", integer=True, nonnegative=True), max_k=8):
    mat = valider_matrice_carree(A, "A")
    n, _ = _dimensions(mat)
    lam = mat[0][0]
    diagonale_constante = all(_est_nul(_c_sous(mat[i][i], lam)) for i in range(1, n))
    if diagonale_constante:
        N = sous(mat, mult(identite(n), scalaire=lam))
        idx = indice_nilpotence_matrice(N, max_k=max_k)
        if idx is not None:
            resultat = _matrice(n, n, lambda i, j: Fraction(0, 1))
            lam_sym = to_sympy(lam)
            for k in range(idx):
                coeff_binom = to_sympy(k_parmi_n_factorise_base(sym_n, k))
                facteur = sp.simplify(coeff_binom * (lam_sym ** (sym_n - k)))
                terme = mult(puissance(N, k), scalaire=facteur)
                resultat = add(resultat, terme)
            return resultat, f"Binôme de Newton (A = {fmt_val(lam)}*I + N, N^{idx} = 0)"
    sp_mat = sp.Matrix(n, n, lambda i, j: to_sympy(mat[i][j]))
    try:
        res_sp = sp.simplify(sp_mat ** sym_n)
        resultat = _matrice(n, n, lambda i, j: to_exact_val(res_sp[i, j]))
        return resultat, "Diagonalisation / Forme de Jordan (SymPy)"
    except Exception as exc:
        raise ValueError(f"Impossible de calculer A^n symboliquement : {exc}") from exc

def _demander_dimensions(nom="M", carree=False, lignes_imposees=None, cols_imposees=None):
    while True:
        try:
            if carree:
                if lignes_imposees is not None:
                    l = c = int(lignes_imposees)
                    print(f"Dimension imposée pour {nom} (carrée) : {l}x{c}")
                    return l, c
                n = int(input(f"Taille n de la matrice carrée {nom} (n x n) : ").strip())
                if n <= 0:
                    print("La taille doit être strictement positive.")
                    continue
                return n, n
            if lignes_imposees is not None:
                l = int(lignes_imposees)
                print(f"Nombre de lignes imposé pour {nom} : {l}")
            else:
                l = int(input(f"Nombre de lignes de {nom} : ").strip())
            if cols_imposees is not None:
                c = int(cols_imposees)
                print(f"Nombre de colonnes imposé pour {nom} : {c}")
            else:
                c = int(input(f"Nombre de colonnes de {nom} : ").strip())
            if l <= 0 or c <= 0:
                print("Les dimensions doivent être strictement positives.")
                continue
            return l, c
        except ValueError:
            print("Veuillez entrer des entiers valides.")

def saisir_matrice_manuellement(nom="M", carree=False, lignes_imposees=None, cols_imposees=None):
    contrainte = "carrée" if carree else "rectangulaire (2D)"
    print(f"\n--- Saisie de la matrice {nom} [{contrainte}] ---")
    l, c = _demander_dimensions(nom=nom, carree=carree, lignes_imposees=lignes_imposees, cols_imposees=cols_imposees)
    print("Entre chaque ligne (ex: 'a b', '1 -2 3/4' ou '1 + 2*i, 0, -i') :")
    lignes = []
    for i in range(l):
        while True:
            brute = input(f"Ligne {i + 1}/{l} : ").strip()
            elements = [el.strip() for el in (brute.split(",") if "," in brute else brute.split()) if el.strip()]
            if len(elements) != c:
                print(f"Attendu {c} élément(s), reçu {len(elements)}. Réessaie.")
                continue
            try:
                ligne_validee = [to_exact_val(el) for el in elements]
                lignes.append(ligne_validee)
                break
            except Exception as exc:
                print(f"Valeur invalide ({exc}). Réessaie la ligne.")
    mat = valider_matrice_2d(lignes, nom=nom)
    if carree:
        return valider_matrice_carree(mat, nom=nom)
    return mat

def _demander_scalaire(nom="scalaire", autoriser_zero=True):
    while True:
        saisie = input(f"Entrez le {nom} (ex: 'a', '2', '-3/4', '1+i') : ").strip()
        try:
            return valider_scalaire(saisie, nom=nom, autoriser_zero=autoriser_zero)
        except Exception as exc:
            print(f"Valeur invalide ({exc}). Réessaie.")

def _demander_entier(message):
    while True:
        try:
            return int(input(message).strip())
        except ValueError:
            print("Veuillez entrer un entier valide.")

def executer_operation_menu(choix):
    if choix == "1":
        print("\n[add] A + B : deux matrices de mêmes dimensions (l x c).")
        A = saisir_matrice_manuellement("A")
        l_A, c_A = _dimensions(A)
        B = saisir_matrice_manuellement("B", lignes_imposees=l_A, cols_imposees=c_A)
        afficher_matrice("A + B", add(A, B))
    elif choix == "2":
        print("\n[sous] A - B : deux matrices de mêmes dimensions (l x c).")
        A = saisir_matrice_manuellement("A")
        l_A, c_A = _dimensions(A)
        B = saisir_matrice_manuellement("B", lignes_imposees=l_A, cols_imposees=c_A)
        afficher_matrice("A - B", sous(A, B))
    elif choix == "3":
        print("\n[mult] Multiplication : (A * B) ou (A * scalaire).")
        print("  1. Matrice A (l x c) * Matrice B (c x m)")
        print("  2. Matrice A (l x c) * Scalaire")
        sous_choix = input("Type de multiplication : ").strip()
        A = saisir_matrice_manuellement("A")
        _, c_A = _dimensions(A)
        if sous_choix == "1":
            B = saisir_matrice_manuellement("B", lignes_imposees=c_A)
            afficher_matrice("A * B", mult(A, B=B))
        elif sous_choix == "2":
            s = _demander_scalaire("scalaire", autoriser_zero=True)
            afficher_matrice(f"A * ({fmt_val(s)})", mult(A, scalaire=s))
        else:
            print("Sous-choix invalide.")
    elif choix == "4":
        print("\n[div] Division : (A * B^(-1)) ou (A / scalaire).")
        print("  1. Matrice A (l x c) / Matrice carrée inversible B (m x m)")
        print("  2. Matrice A (l x c) / Scalaire non nul")
        sous_choix = input("Type de division : ").strip()
        A = saisir_matrice_manuellement("A")
        if sous_choix == "1":
            B = saisir_matrice_manuellement("B", carree=True)
            afficher_matrice("A / B", div(A, B=B))
        elif sous_choix == "2":
            s = _demander_scalaire("scalaire", autoriser_zero=False)
            afficher_matrice(f"A / ({fmt_val(s)})", div(A, scalaire=s))
        else:
            print("Sous-choix invalide.")
    elif choix == "5":
        print("\n[puissance] M^k : matrice M obligatoirement carrée (n x n) et exposant entier k.")
        M = saisir_matrice_manuellement("M", carree=True)
        k = _demander_entier("Exposant entier k (positif, nul ou négatif si inversible) : ")
        afficher_matrice(f"M^({k})", puissance(M, k))
    elif choix == "6":
        print("\n[det] Déterminant : matrice M obligatoirement carrée (n x n).")
        M = saisir_matrice_manuellement("M", carree=True)
        afficher_matrice("Déterminant det(M)", det(M))
    elif choix == "7":
        print("\n[cof] Comatrice : matrice M obligatoirement carrée (n x n).")
        M = saisir_matrice_manuellement("M", carree=True)
        afficher_matrice("Comatrice cof(M)", cof(M))
    elif choix == "8":
        print("\n[transposee] Transposée : n'importe quelle matrice.")
        M = saisir_matrice_manuellement("M", carree=False)
        afficher_matrice("Transposée M^T", transposee(M))
    elif choix == "9":
        print("\n[inverse] Inverse : matrice carrée (n x n).")
        M = saisir_matrice_manuellement("M", carree=True)
        afficher_matrice("Inverse", inverse(M))
    elif choix == "10":
        print("\n[gauss] Gauss : matrice carrée (n x n).")
        M = saisir_matrice_manuellement("M", carree=True)
        g, sep = gauss(M)
        afficher_matrice("Gauss", g, sep=sep)
    elif choix == "11":
        print("\n[gauss_jordan] Gauss-Jordan : matrice carrée (n x n).")
        M = saisir_matrice_manuellement("M", carree=True)
        gj, sep = gauss_jordan(M)
        afficher_matrice("Gauss-Jordan", gj, sep=sep)
    elif choix == "12":
        print("\n[puissance_n] Calcul de A ^ n : matrice carrée (n x n).")
        A = saisir_matrice_manuellement("A", carree=True)
        sym_n = sp.Symbol("n", integer=True, nonnegative=True)
        An, methode = puissance_n_symbolique(A, sym_n=sym_n)
        print(f"Méthode utilisée : {methode}")
        afficher_matrice("A ^ n", An)

def main():
    while True:
        print("\n=== Menu des opérations ===")
        print("  1. add          -> A + B")
        print("  2. sous         -> A - B")
        print("  3. mult         -> A * B | A * k")
        print("  4. div          -> A / B | A / k")
        print("  5. puissance    -> M ^ k")
        print("  6. det          -> Déterminant")
        print("  7. cof          -> Comatrice")
        print("  8. transposee   -> Transposée")
        print("  9. inverse      -> Inverse")
        print(" 10. gauss        -> Pivot de Gauss")
        print(" 11. gauss_jordan -> Gauss-Jordan")
        print(" 12. puissance_n  -> A ^ n")
        print("  0. Quitter")
        choix = input("Choix de l'opération : ").strip()
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

