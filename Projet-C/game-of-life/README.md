# Jeu de la Vie — C + raylib + grille infinie

## Structure du projet

```
game-of-life/
├── CMakeLists.txt
├── keys.cfg                ← genere automatiquement au premier lancement
├── game-of-life            ← executable (cree a la racine, pas dans build/)
├── assets/
│   └── patterns/           ← fichiers .rle (glider.rle, gun.rle, ...)
└── src/
    ├── main.c
    ├── chunk.h
    ├── chunk_map.h / .c
    ├── simulation.h        ← regles Conway (header-only)
    ├── renderer.h          ← rendu raylib (header-only)
    ├── save.h              ← RLE + JSON (header-only)
    ├── ui.h / .c           ← interface (toolbar, menus, dialogues)
    └── config.h            ← raccourcis clavier
```

## Compilation

```bash
rm -rf build && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j$(nproc)
cd ..
./game-of-life
```

## Recompilation

```bash
cmake --build build -j$(nproc) && ./game-of-life
```

## Raccourcis clavier

| Touche              | Action                                    |
|---------------------|-------------------------------------------|
| Espace              | Pause / Reprendre                         |
| →                   | Avancer d'un pas (en pause)               |
| Molette             | Zoom centre sur la souris                 |
| Z / Q / S / D       | Pan (deplacer la vue) — AZERTY natif      |
| Clic gauche         | Dessiner (ligne continue Bresenham)       |
| Clic droit          | Effacer                                   |
| Clic milieu + drag  | Pan a la souris (tous les ecrans)         |
| ↑ / ↓               | Vitesse +/-                               |
| G                   | Grille on/off                             |
| H                   | HUD on/off                                |
| F                   | Recentrer sur l'origine                   |
| E                   | Remplissage aleatoire (selectionner zone) |
| S                   | Sauvegarder zone (RLE)                    |
| L                   | Charger un pattern (browser RLE)          |
| X                   | Effacer toute la grille                   |
| Ctrl+Z              | Annuler (undo)                            |
| Ctrl+C              | Copier une zone                           |
| Ctrl+V              | Coller                                    |
| Ctrl+X              | Effacer une zone                          |
| R                   | Rotation 90° (mode placement)             |
| T                   | Theme suivant                             |
| Echap               | Ouvrir/fermer le menu (met en pause)      |
| TAB                 | Debug chunks on/off                       |

> **Note AZERTY** : raylib detecte Z comme KEY_W et Q comme KEY_A.
> Les touches sont deja configurees pour fonctionner nativement sur AZERTY.

## Toolbar (pictogrammes)

| Icone | Action              | Raccourci |
|-------|---------------------|-----------|
| ▶     | Play                | Espace    |
| ⏸     | Pause               | Espace    |
| ⏭     | Pas suivant         | →         |
| ✕     | Effacer la grille   | X         |
| ↩     | Annuler             | Ctrl+Z    |
| 💾    | Sauvegarder zone    | S         |
| 📂    | Charger RLE         | L         |
| ░░    | Aleatoire           | E         |
| ⎘     | Copier zone         | Ctrl+C    |
| ⎙     | Coller              | Ctrl+V    |
| ☒     | Effacer zone        | Ctrl+X    |
| ≡     | Menu                | Echap     |

## Chargement et sauvegarde de patterns

- Les fichiers `.rle` sont lus depuis `assets/patterns/` et `saves/`
- La sauvegarde ecrit dans `assets/patterns/`
- Format **RLE standard** compatible Golly / LifeWiki

### Telecharger des patterns

Le site <https://conwaylife.com/wiki> fournit des centaines de motifs.
Placez les `.rle` dans `assets/patterns/` pour les voir dans le navigateur.

## Remplissage aleatoire

1. Appuyez sur **E** ou cliquez le bouton aleatoire dans la toolbar
2. Dessinez un rectangle sur la grille avec clic+drag
3. Reglez la densite (curseur 0–100 %)
4. Confirmez avec **Remplir**

## Notes d'architecture

- **Grille infinie** : seuls les chunks contenant des cellules vivantes sont alloues.
- **Simulation** : ne visite que les chunks actifs + leurs 8 voisins directs.
- **Dessin continu** : algorithme de Bresenham entre chaque frame — pas de trous.
- **Zoom** : bloque le scroll aux limites min/max (2–128 px/cellule).
- **Echap** ne ferme jamais le jeu — il ouvre le menu et met en pause.
- **Pan milieu** : le pan a la souris (clic milieu) fonctionne dans tous les ecrans.
- **Cache miniature** : la preview RLE dans le browser n'est rechargee que si le fichier change.
