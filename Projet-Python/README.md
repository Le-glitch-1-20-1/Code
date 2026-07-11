# Projet-Python

Collection de scripts Python indépendants, chacun autonome (un fichier = un outil),
la plupart avec une interface interactive ([questionary](https://github.com/tmbo/questionary) /
[rich](https://github.com/Textualize/rich)) doublée d'un mode CLI complet via `argparse`.

---

## Scripts

| Script | Description | Usage rapide |
|---|---|---|
| `Aco-tsp.py` | Résout le problème du voyageur de commerce (TSP) par colonie de fourmis (ACO), avec animation matplotlib | `python3 Aco-tsp.py --villes 25 --fourmis 30 --iterations 100` |
| `Folder-report.py` | Scanne les partitions disque et génère un rapport HTML des fichiers (utilise `Template/file-report`) | `python3 Folder-report.py -e pdf jpg png -o rapport.html` |
| `Gen-depmap.py` | Génère une carte de dépendances HTML interactive depuis les sources C/C++ d'un projet (utilise `Template/depmap`) | `python3 Gen-depmap.py -s ./mon_projet -o Dependency_map.html` |
| `Interface.py` | Démo d'interface terminal interactive (menus, tableaux, barres de progression) avec Rich & Questionary | `python3 Interface.py --list-demos` |
| `Maze-bot.py` | Générateur de labyrinthes + bot de résolution automatique (capture d'écran / navigateur via Selenium) | `python3 Maze-bot.py generate --size mini` |
| `Media-toolkit.py` | Convertit des images en JPEG, des vidéos en MP4, ou détecte/déplace les doublons d'images | `python3 Media-toolkit.py images ./dossier --quality 90` |
| `Midi-tools.py` | Monitore les ports MIDI d'entrée, ou teste les couleurs des pads d'un contrôleur APC | `python3 Midi-tools.py monitor` |
| `Minecraft-toolkit.py` | Analyse une sauvegarde Minecraft : calcul de superficie de map, recherche de l'œuf de dragon | `python3 Minecraft-toolkit.py --mode egg --dir ./monde` |
| `Pascal-triangle-binomial.py` | Affiche une ligne du triangle de Pascal ou développe un binôme (a + b)^n, avec sortie LaTeX optionnelle | `python3 Pascal-triangle-binomial.py --triangle 5` |
| `Steganography.py` | Cache ou révèle un message texte dans les bits de poids faible des canaux couleur d'une image | `python3 Steganography.py hide "secret" --image photo.png` |

Chaque script est également utilisable sans argument : il lance alors un menu interactif.
Le détail complet des options est disponible via `python3 <script>.py --help` (ou `-h`).

## Structure

```
Projet-Python/
├── Aco-tsp.py
├── Folder-report.py
├── Gen-depmap.py
├── Interface.py
├── Maze-bot.py
├── Media-toolkit.py
├── Midi-tools.py
├── Minecraft-toolkit.py
├── Pascal-triangle-binomial.py
├── Steganography.py
├── Dependency_map.html		← exemple de sortie de Gen-depmap.py
├── Images/						← images d'exemple/test (dont un exemple de stéganographie)
└── Template/
    ├── depmap/					← template HTML/CSS/JS utilisé par Gen-depmap.py
    └── file-report/			← template HTML/CSS/JS utilisé par Folder-report.py
```

## Dépendances

Aucun `requirements.txt` n'est fourni. Selon les scripts utilisés, il faut installer :

```bash
pip install numpy matplotlib questionary rich psutil sympy \
            pillow pillow-heif moviepy opencv-python selenium mido python-rtmidi
```

- `Aco-tsp.py` : `numpy`, `matplotlib`
- `Folder-report.py`, `Gen-depmap.py`, `Interface.py`, `Minecraft-toolkit.py` : `questionary`, `rich`, `psutil` (pour Folder-report.py)
- `Maze-bot.py` : `opencv-python`, `numpy`, `pillow` (optionnel), `selenium` (optionnel)
- `Media-toolkit.py` : `pillow`, `pillow-heif`, `moviepy`, `questionary`, `rich`
- `Midi-tools.py` : `mido`, `python-rtmidi`, `questionary`, `rich`
- `Pascal-triangle-binomial.py` : `sympy`, `questionary`, `rich`
- `Steganography.py` : `pillow`, `questionary`, `rich`

## Auteurs

Scripts réalisés dans le cadre de projets personnels.
