# Projet-Python

[Version française](README.fr.md)

A collection of independent Python scripts, each self-contained (one file = one tool).
Every script works with a plain console interface (`print` / `input`) and also offers
a full command-line mode through `argparse`.

An optional display layer (`display_layer.py`, based on
[rich](https://github.com/Textualize/rich) and [questionary](https://github.com/tmbo/questionary))
adds colours, panels, tables, arrow-key menus and progress bars when it is present.

---

## Scripts

| Script | Description | Quick usage |
|---|---|---|
| `Aco-tsp.py` | Solves the travelling salesman problem (TSP) with an ant colony (ACO), with a matplotlib animation when the display layer is active | `python3 Aco-tsp.py --cities 25 --ants 30 --iterations 100` |
| `Folder-report.py` | Scans the disk partitions and generates an HTML report of the files (uses `Template/file-report`) | `python3 Folder-report.py -e pdf jpg png -o report.html` |
| `Gen-depmap.py` | Generates an interactive HTML dependency map from the C/C++ sources of a project (uses `Template/depmap`) | `python3 Gen-depmap.py -s ./my_project -o Dependency_map.html` |
| `Interface.py` | Terminal interface demo (menus, tables, progress bars, forms...) | `python3 Interface.py --list-demos` |
| `Matrix.py` | Matrix calculator: +, -, *, /, power, determinant, cofactor matrix, transpose, inverse, Gauss and Gauss-Jordan elimination (exact fractions) | `python3 Matrix.py` |
| `Maze-bot.py` | Maze generator + automatic solving bot (browser capture with Selenium) | `python3 Maze-bot.py generate --size mini` |
| `Media-toolkit.py` | Converts images to JPEG, videos to MP4, detects/moves duplicate images, or renames files by capture date | `python3 Media-toolkit.py images ./folder --quality 90` |
| `Minecraft-toolkit.py` | Analyses a Minecraft save: map area, dragon egg search | `python3 Minecraft-toolkit.py --mode egg --dir ./world` |
| `Pascal-triangle-binomial.py` | Shows a row of Pascal's triangle or expands a binomial (a + b)^n, with optional LaTeX output | `python3 Pascal-triangle-binomial.py --triangle 5` |
| `Steganography.py` | Hides or reveals a text message in the colour channel parities of an image | `python3 Steganography.py hide "secret" --image photo.png` |

Most scripts can also be run without arguments: they then open an interactive menu.
The full list of options is available with `python3 <script>.py --help` (or `-h`).

## Language

The scripts are written in English. To get the messages in French, keep
`lang_fr.json` next to the scripts and either:

- add `--lang fr` (or `--lang=fr`) to the command line,
- or set the environment variable `PROJECT_LANG=fr`.

```bash
python3 Pascal-triangle-binomial.py --lang fr --triangle 5
PROJECT_LANG=fr python3 Interface.py
```

Without `lang_fr.json`, the scripts simply stay in English. The translation only
changes the displayed messages (menus, questions, results, `--help`); the code,
the options and the generated file names stay the same (except `Folder-report.py`,
which also has its own `-l/--lang` option for the report itself).

## Optional display layer

`display_layer.py` is loaded automatically when it is next to a script and when
`rich` and `questionary` are installed. The scripts work perfectly without it.
To disable it:

- run a script with `--no-ui`,
- or set the environment variable `PROJECT_NO_UI=1`,
- or set `ACTIVE = False` at the top of `display_layer.py`,
- or delete / rename `display_layer.py`.

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
├── display_layer.py      ← optional display layer (rich + questionary)
├── lang_fr.json          ← French translation of the messages
├── image/                ← sample/test images (including a steganography example)
└── Template/
    ├── depmap/           ← HTML/CSS/JS template used by Gen-depmap.py
    └── file-report/      ← HTML/CSS/JS template used by Folder-report.py
```

## Dependencies

```bash
pip install -r Requirements.txt
```

- `Aco-tsp.py`: `numpy` (`matplotlib` for the animation)
- `Folder-report.py`: `psutil`
- `Maze-bot.py`: `opencv-python`, `numpy`, `pillow`, `selenium` + `webdriver-manager` (browser capture), `pynput` (keyboard control)
- `Media-toolkit.py`: `pillow`, `pillow-heif`, `moviepy`
- `Pascal-triangle-binomial.py`: `sympy`
- `Matrix.py`: `sympy` (only for complex or symbolic entries)
- `Steganography.py`: `pillow`
- `Gen-depmap.py`, `Interface.py`, `Minecraft-toolkit.py`: standard library only
- Optional display layer: `rich`, `questionary`

## Authors

Scripts made as personal projects.
