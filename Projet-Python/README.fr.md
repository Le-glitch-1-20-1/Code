# Projet-Python

[English version](README.md)

Collection de scripts Python indépendants, chacun autonome (un fichier = un outil).
Chaque script fonctionne avec un affichage console simple (`print` / `input`) et propose
aussi un mode ligne de commande complet via `argparse`.

Une couche d'affichage optionnelle (`display_layer.py`, basée sur
[rich](https://github.com/Textualize/rich) et [questionary](https://github.com/tmbo/questionary))
ajoute couleurs, panneaux, tableaux, menus fléchés et barres de progression quand elle est présente.

---

## Scripts

| Script | Description | Usage rapide |
|---|---|---|
| `Aco-tsp.py` | Résout le problème du voyageur de commerce (TSP) par colonie de fourmis (ACO), avec animation matplotlib si la couche d'affichage est active | `python3 Aco-tsp.py --lang fr --cities 25 --ants 30 --iterations 100` |
| `Folder-report.py` | Scanne les partitions disque et génère un rapport HTML des fichiers (utilise `Template/file-report`) | `python3 Folder-report.py --lang fr -l fr -e pdf jpg png -o rapport.html` |
| `Gen-depmap.py` | Génère une carte de dépendances HTML interactive depuis les sources C/C++ d'un projet (utilise `Template/depmap`) | `python3 Gen-depmap.py --lang fr -s ./mon_projet -o Dependency_map.html` |
| `Interface.py` | Démo d'interface terminal (menus, tableaux, barres de progression, formulaires...) | `python3 Interface.py --lang fr --list-demos` |
| `Matrix.py` | Calculatrice de matrices : +, -, *, /, puissance, déterminant, comatrice, transposée, inverse, pivot de Gauss et Gauss-Jordan (fractions exactes) | `python3 Matrix.py --lang fr` |
| `Maze-bot.py` | Générateur de labyrinthes + bot de résolution automatique (capture navigateur via Selenium) | `python3 Maze-bot.py --lang fr generate --size mini` |
| `Media-toolkit.py` | Convertit des images en JPEG, des vidéos en MP4, détecte/déplace les doublons d'images, ou renomme les fichiers par date de prise | `python3 Media-toolkit.py --lang fr images ./dossier --quality 90` |
| `Minecraft-toolkit.py` | Analyse une sauvegarde Minecraft : superficie de la carte, recherche de l'œuf de dragon | `python3 Minecraft-toolkit.py --lang fr --mode egg --dir ./monde` |
| `Pascal-triangle-binomial.py` | Affiche une ligne du triangle de Pascal ou développe un binôme (a + b)^n, avec sortie LaTeX optionnelle | `python3 Pascal-triangle-binomial.py --lang fr --triangle 5` |
| `Steganography.py` | Cache ou révèle un message texte dans les parités des canaux couleur d'une image | `python3 Steganography.py --lang fr hide "secret" --image photo.png` |

La plupart des scripts peuvent aussi être lancés sans argument : ils ouvrent alors un menu interactif.
Le détail des options est disponible via `python3 <script>.py --lang fr --help`.

## Langue

Le code et les messages sont en anglais par défaut. Pour avoir les messages en français,
il faut garder `lang_fr.json` à côté des scripts, puis :

- ajouter `--lang fr` (ou `--lang=fr`) à la ligne de commande,
- ou définir la variable d'environnement `PROJECT_LANG=fr`.

```bash
python3 Pascal-triangle-binomial.py --lang fr --triangle 5
PROJECT_LANG=fr python3 Interface.py
```

Sans `lang_fr.json`, les scripts restent simplement en anglais. La traduction ne change que
les messages affichés (menus, questions, résultats, `--help`) : le code, les options et les
noms de fichiers générés restent les mêmes (sauf `Folder-report.py`, qui a en plus sa propre
option `-l/--lang` pour le rapport lui-même).

Pour ajouter ou corriger une traduction, il suffit de modifier `lang_fr.json` :
`"exact"` associe un message anglais à sa traduction, `"patterns"` gère les messages
avec des valeurs variables (les nombres `0`, `1`... indiquent l'emplacement de chaque valeur).

## Couche d'affichage optionnelle

`display_layer.py` est chargé automatiquement s'il est à côté d'un script et si `rich` et
`questionary` sont installés. Les scripts fonctionnent très bien sans lui. Pour le désactiver :

- lancer un script avec `--no-ui`,
- ou définir la variable d'environnement `PROJECT_NO_UI=1`,
- ou mettre `ACTIVE = False` en haut de `display_layer.py`,
- ou supprimer / renommer `display_layer.py`.

## Structure

```
Projet-Python/
├── Aco-tsp.py
├── Folder-report.py
├── Gen-depmap.py
├── Interface.py
├── Matrix.py
├── Maze-bot.py
├── Media-toolkit.py
├── Minecraft-toolkit.py
├── Pascal-triangle-binomial.py
├── Steganography.py
├── display_layer.py      ← couche d'affichage optionnelle (rich + questionary)
├── lang_fr.json          ← traduction française des messages
├── image/                ← images d'exemple/test (dont un exemple de stéganographie)
└── Template/
    ├── depmap/           ← template HTML/CSS/JS utilisé par Gen-depmap.py
    └── file-report/      ← template HTML/CSS/JS utilisé par Folder-report.py
```

## Dépendances

```bash
pip install -r Requirements.txt
```

- `Aco-tsp.py` : `numpy` (`matplotlib` pour l'animation)
- `Folder-report.py` : `psutil`
- `Maze-bot.py` : `opencv-python`, `numpy`, `pillow`, `selenium` + `webdriver-manager` (capture navigateur), `pynput` (contrôle clavier)
- `Media-toolkit.py` : `pillow`, `pillow-heif`, `moviepy`
- `Pascal-triangle-binomial.py` : `sympy`
- `Matrix.py` : `sympy` (uniquement pour les valeurs complexes ou symboliques)
- `Steganography.py` : `pillow`
- `Gen-depmap.py`, `Interface.py`, `Minecraft-toolkit.py` : bibliothèque standard uniquement
- Couche d'affichage optionnelle : `rich`, `questionary`

## Auteurs

Scripts réalisés dans le cadre de projets personnels.
