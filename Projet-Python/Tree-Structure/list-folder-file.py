#!/usr/bin/env python3

import os
import json
import gzip
import shutil
import psutil
from datetime	import datetime

FICHIER_HTML = "Résultat.html"
TEMPLATE_HTML = "src/template.html"

def format_taille_octets(octets):
	if octets == 0:
		return "0.00", "o"
	for unite in ['o', 'Ko', 'Mo', 'Go', 'To', 'Po']:
		if octets < 1024:
			return f"{octets:.2f}", unite
		octets /= 1024

def aplatir_arborescence(arborescence, chemin=""):
	lignes = []
	for nom, contenu in arborescence.items():
		if nom == "_fichiers":
			for fichier, taille in contenu:
				nom_base, ext = os.path.splitext(fichier)
				ext = ext.lstrip(".")
				val, unite = format_taille_octets(taille)
				lignes.append({
					"n": nom_base,
					"e": ext,
					"t": val,
					"u": unite,
					"p": chemin,
				})
		else:
			sous_chemin = f"{chemin}/{nom}" if chemin else nom
			lignes += aplatir_arborescence(contenu, sous_chemin)
	return lignes

def extraire_extensions(lignes):
	exts = sorted({item["e"] for item in lignes if item["e"]})
	return exts

def lister_dossiers_et_fichiers_filtres(partitions, valeur_modifiee, extensions):
	resultats = {}
	erreurs = []
	for partition in partitions:
		mountpoint = partition.mountpoint
		resultats[mountpoint] = {}
		try:
			total_dossiers = sum([len(dirs) for _, dirs, _ in os.walk(mountpoint, onerror=lambda e: None)])
			print(f"Analyse de {mountpoint:<{valeur_modifiee}} | {total_dossiers:>10} dossiers")
			for dossier, sous_dossiers, fichiers in os.walk(mountpoint, onerror=lambda e: None):
				try:
					fichiers_filtres = [
						(f, os.path.getsize(os.path.join(dossier, f)))
						for f in fichiers
						if not extensions
						or os.path.splitext(f)[1].lower().lstrip(".") in extensions
					]
					if fichiers_filtres:
						dossier_courant = resultats.setdefault(mountpoint, {})
						sous_arborescence = dossier_courant
						sous_chemins = dossier[len(mountpoint):].strip(os.sep).split(os.sep)
						for sous_dossier in sous_chemins:
							if sous_dossier:
								sous_arborescence = sous_arborescence.setdefault(sous_dossier, {})
						sous_arborescence["_fichiers"] = fichiers_filtres
				except PermissionError:
					erreurs.append(f"Accès refusé à un dossier dans : {dossier}")
				except FileNotFoundError:
					erreurs.append(f"Le chemin d'accès est introuvable : {dossier}")
				except Exception as e:
					erreurs.append(f"Erreur lors du traitement du dossier {dossier} : {e}")
		except PermissionError:
			erreurs.append(f"Accès refusé à la partition : {mountpoint}")
		except Exception as e:
			erreurs.append(f"Erreur lors du traitement de la partition {mountpoint} : {e}")
	return resultats, erreurs

def convertir_en_html(resultats, fichier_html):
	try:
		with open(TEMPLATE_HTML, "r", encoding="utf-8") as f:
			template = f.read()
	except FileNotFoundError:
		print(f"Erreur : le fichier template HTML '{TEMPLATE_HTML}' est introuvable.")
		return
	partitions_data = {}
	for mountpoint, contenu in resultats.items():
		label = f"🖥️ {mountpoint}"
		lignes = aplatir_arborescence(contenu)
		partitions_data[label] = lignes
	extensions_disponibles = extraire_extensions([item for lignes in partitions_data.values() for item in lignes])
	json_data = json.dumps(partitions_data, ensure_ascii=False, separators=(',', ':'))
	extensions_json = json.dumps(extensions_disponibles, ensure_ascii=False, separators=(',', ':'))
	html_final = template.replace("{{DATE}}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
	html_final = html_final.replace("{{DATA_JSON}}", json_data)
	html_final = html_final.replace("{{EXTENSIONS_JSON}}", extensions_json)
	with open(fichier_html, 'w', encoding='utf-8') as f:
		f.write(html_final)
	taille_mo = os.path.getsize(fichier_html) / (1024 * 1024)
	print(f"\nRapport généré : {fichier_html}  ({taille_mo:.2f} Mo)")
	gz_path = fichier_html + ".gz"
	with open(fichier_html, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
		shutil.copyfileobj(f_in, f_out)
	taille_gz = os.path.getsize(gz_path) / (1024 * 1024)
	print(f"Version compressée : {gz_path}  ({taille_gz:.2f} Mo)")

def detecter_emplacements_et_generer_rapport(extensions=None):
	partitions = psutil.disk_partitions(all=False)
	partition_cible = max(partitions, key=lambda p: len(p.mountpoint))
	nom = partition_cible.mountpoint
	longueur = len(nom)
	valeur_modifiee = longueur + 5
	if valeur_modifiee % 2 != 0:
		valeur_modifiee += 1
	valeur_modifiee += 1
	val_modif = len("Analyse de  |  dossiers") + valeur_modifiee + 11
	titre = "=== Générateur de Rapport de Tous les Fichiers ==="
	if val_modif < len(titre):
		print(titre)
	else:
		pad = int((val_modif - len(titre)) / 2)
		print(f"\n{'=' * pad}{titre}{'=' * pad}\n")
	resultats, erreurs = lister_dossiers_et_fichiers_filtres(partitions, valeur_modifiee, extensions or [])
	convertir_en_html(resultats, FICHIER_HTML)
	if erreurs:
		print(f"\n{'Erreurs rencontrées':<{len('Analyse de ') + valeur_modifiee}} | {len(erreurs):>10} erreurs\n")
		os.makedirs("src", exist_ok=True)
		with open("src/errors-report.txt", "w", encoding="utf-8") as f:
			f.write("=== Rapport d'erreurs ===\n")
			f.write(f"Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
			f.write(f"Nombre total d'erreurs : {len(erreurs)}\n\n")
			n = len(str(len(erreurs)))
			for i, erreur in enumerate(erreurs, 1):
				if ":" in erreur:
					gauche, droite = erreur.split(":", 1)
					f.write(f"{i:0{n}d}. {gauche.strip():<40}: {droite.strip()}\n")
				else:
					f.write(f"{i:0{n}d}. {erreur}\n")

def main():
	extensions = []
	detecter_emplacements_et_generer_rapport(extensions)

if __name__ == "__main__":
	main()
