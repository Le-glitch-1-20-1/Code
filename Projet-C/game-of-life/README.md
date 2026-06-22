# Jeu de la Vie — Conway's Game of Life (C + raylib)

Implémentation en C du Jeu de la Vie de Conway, avec rendu temps réel via **raylib 5.0**.
Grille infinie, interface graphique complète, sauvegarde/chargement de patterns au format RLE.

---

## Structure du projet

```
game-of-life/
├── CMakeLists.txt
├── keys.cfg								← genere automatiquement au premier lancement
├── game-of-life							← executable
├── assets/
│   └── patterns/							← fichiers .rle
└── src/
    ├── main.c
    ├── app.h / app_init.c / app_undo.c
    ├── app_draw-*.c
    ├── app_input-*.c
    ├── app_map-*.c
    ├── app_screens-*.c
    ├── chunk.h
    ├── chunk_map.h / chunk_map-*.c
    ├── config.h							← raccourcis clavier
    ├── renderer.h							← rendu raylib
    ├── save.h / save-*.c					← RLE + JSON
    ├── simulation.h / simulation.c
    └── ui.h / ui_*.c						← interface
```

---

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

---

## Raccourcis clavier

| Touche              | Action                     |
|---------------------|----------------------------|
| Espace              | Pause / Reprendre          |
| →                   | Avancer d'un pas           |
| Molette             | Zoom centre sur la souris  |
| Z / Q / S / D       | Pan — AZERTY natif         |
| Clic gauche         | Dessiner                   |
| Clic droit          | Effacer                    |
| Clic milieu + drag  | Pan a la souris            |
| ↑ / ↓               | Vitesse +/-                |
| G                   | Grille on/off              |
| H                   | HUD on/off                 |
| F                   | Recentrer sur l'origine    |
| E                   | Remplissage aleatoire      |
| S                   | Sauvegarder zone           |
| L                   | Charger un pattern         |
| X                   | Effacer toute la grille    |
| Ctrl+Z              | Annuler                    |
| Ctrl+C              | Copier une zone            |
| Ctrl+V              | Coller                     |
| Ctrl+X              | Effacer une zone           |
| R                   | Rotation 90°               |
| T                   | Theme suivant              |
| Echap               | Ouvrir/fermer le menu      |
| TAB                 | Debug chunks on/off        |

> **Note AZERTY** : raylib detecte Z comme KEY_W et Q comme KEY_A.
> Les touches sont deja configurees pour fonctionner nativement sur AZERTY.
> Elles sont entierement reconfigurables via le menu → Touches, et sauvegardees dans `keys.cfg`.

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

---

## Chargement et sauvegarde de patterns

- Les fichiers `.rle` sont lus depuis `assets/patterns/` et `saves/`
- La sauvegarde ecrit dans `assets/patterns/`
- Format **RLE standard** compatible Golly / LifeWiki

### Telecharger des patterns

Le site <https://conwaylife.com/wiki> fournit des centaines de motifs.
Placez les `.rle` dans `assets/patterns/` pour les voir dans le navigateur.

### Remplissage aleatoire

1. Appuyez sur **E** ou cliquez le bouton aleatoire dans la toolbar
2. Dessinez un rectangle sur la grille avec clic+drag
3. Reglez la densite (curseur 0–100 %)
4. Confirmez avec **Remplir**

---

## Notes d'architecture

- **Grille infinie**   : seuls les chunks contenant des cellules vivantes sont alloues.
- **Simulation**       : ne visite que les chunks actifs + leurs 8 voisins directs.
- **Dessin continu**   : algorithme de Bresenham entre chaque frame — pas de trous.
- **Zoom**             : bloque le scroll aux limites min/max (2–128 px/cellule).
- **Echap**            : ne ferme jamais le jeu — il ouvre le menu et met en pause.
- **Pan milieu**       : le pan a la souris (clic milieu) fonctionne dans tous les ecrans.
- **Cache miniature**  : la preview RLE dans le browser n'est rechargee que si le fichier change.

---

## Détail des modules (`src/`)

### Point d'entrée

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `main.c         ` | Point d'entrée. Initialise la fenêtre raylib (1600×900, redimensionnable, 60 FPS), lance la boucle principale `update()` + `draw_frame()`, libère les ressources à la fermeture.                                                                        |

### Module `app` — État global et logique principale

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `app.h        `   | Header principal. Définit la structure centrale `t_app` (état complet : map, caméra, clavier, écran actif, sélections, clipboard, undo stack, historique de population…) et déclare toutes les fonctions du module.                                     |
| `app_init.c     ` | Allocation et initialisation de `t_app` (valeurs par défaut, chargement du fichier `keys.cfg`, init des maps). Contient aussi `app_cleanup()` pour libérer toute la mémoire.                                                                            |
| `app_undo.c     ` | Stack d'annulation circulaire (20 niveaux). `push_undo()` sauvegarde l'état courant de la map, `pop_undo()` restaure le dernier état enregistré.                                                                                                        |

### Module `app_draw` — Rendu des overlays

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `app_draw‑1.c   ` | Dessin de la prévisualisation de placement de pattern (rectangle + cellules en surbrillance) et de la boîte d'info de sélection (titre, dimensions, nombre de cellules vivantes). Contient aussi `stamp_pattern()` pour imprimer un pattern sur la map. |
| `app_draw‑2.c   ` | Comptage des cellules vivantes dans un rectangle (`count_cells_in_rect`), dessin de l'overlay de sélection générique (`draw_select_overlay`), et overlay de sélection "Effacer" (rouge).                                                                |
| `app_draw‑3.c   ` | Normalisation des coordonnées de la sélection copie (`minmax_copy`) et overlay de sélection "Copier" (bleu). Dispatch global `draw_selections()`.                                                                                                       |

### Module `app_input` — Gestion des entrées

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `app_input‑1.c  ` | Zoom à la molette (centré sur le curseur, bornes min/max) et pan de la caméra (touches directionnelles + clic molette).                                                                                                                                 |
| `app_input‑2.c  ` | Dessin de cellules à la souris (clic gauche = vivant, clic droit = mort, drag continu). Remplissage aléatoire d'une zone (`apply_random_fill`).                                                                                                         |
| `app_input‑3.c  ` | Sélection rectangulaire par drag pour effacement de zone (`handle_clear_select`) et pour copie dans le clipboard (`handle_copy_select` + `copy_select_fill`).                                                                                           |
| `app_input‑4.c  ` | Raccourcis clavier : Échap (annuler / ouvrir menu), Ctrl+Z/C/V/X (undo, copier zone, coller, effacer zone), touches sans Ctrl (play/pause, step, grille, HUD, thème…).                                                                                  |
| `app_input‑5.c  ` | Actions clavier sans Ctrl : ouverture de l'écran random, de l'écran save, effacement complet de la grille, recentrage de la vue.                                                                                                                        |
| `app_input‑6.c  ` | Point d'entrée principal de la gestion des inputs en mode jeu : `handle_game_input()`. Orchestre zoom, pan, dessin, raccourcis, vitesse, sélections.                                                                                                    |
| `app_input‑7.c  ` | Algorithme de Bresenham pour tracer une ligne continue de cellules entre deux coordonnées (`draw_line_cells`).                                                                                                                                          |
| `app_input‑8.c  ` | Gestion du drag de sélection pour la copie et application finale dans le clipboard (`handle_copy_select`).                                                                                                                                              |

### Module `app_map` — Transformations de map

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `app_map‑1.c    ` | Centrage d'une map sur l'origine (`center_map`) et rotation à 90° d'un pattern (`rotate_map_90`).                                                                                                                                                       |
| `app_map‑2.c    ` | Export d'une zone rectangulaire de la map en fichier RLE (`save_zone_rle`).                                                                                                                                                                             |

### Module `app_screens` — Écrans et toolbar

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `app_screens‑1.c` | Actions déclenchées par la toolbar : play/step, clear, ouvrir les écrans save/load/random, coller, toggles grille/HUD/thème. Contient `handle_toolbar_act1()` et `handle_toolbar_toggle()`.                                                             |
| `app_screens‑2.c` | Affichage du HUD en mode jeu (génération, vitesse, population), de l'écran principal `draw_screen_game()`, et de l'overlay de sélection random. Utilitaire `fill_pop_buf()` pour l'historique de population.                                            |
| `app_screens‑3.c` | Gestion des sélections depuis la toolbar (copie/effacement de zone, paste), actions menu/centrage/undo, et dispatcher général `handle_toolbar_action()`.                                                                                                |
| `app_screens‑4.c` | Écrans : remplissage aléatoire (`SCREEN_RANDOM`), sauvegarde de zone RLE (`SCREEN_SAVE_ZONE`), et placement/rotation de pattern (`SCREEN_PLACE`).                                                                                                       |
| `app_screens‑5.c` | Écrans : chargement de fichier RLE (`SCREEN_LOAD`), menu principal (`draw_frame_menu`), dispatcher global des écrans (`draw_frame_screens`), boucle de rendu `draw_frame()` et boucle de simulation `update()`.                                         |

### Module `chunk` — Structure de données de la grille

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `chunk.h        ` | Définit `t_chunk` : bloc 16×16 cellules encodées en bitfield (`uint16_t cells[16]`, 1 bit = 1 cellule, 32 octets/chunk). Accesseurs inline : `chunk_get`, `chunk_set`, `chunk_clear`, `chunk_is_dead`.                                                  |
| `chunk_map.h    ` | Définit `t_chunk_map` : hashmap ouverte (4096 buckets, chainage par liste chaînée) de chunks. Déclare toutes les fonctions d'accès, d'itération et de copie.                                                                                            |
| `chunk_map‑1.c  ` | Hash des coordonnées de chunk, `map_init`, `map_free`, `map_get`, `map_get_or_create`.                                                                                                                                                                  |
| `chunk_map‑2.c  ` | Division euclidienne correcte pour coordonnées négatives (`floor_div`/`floor_mod`), suppression d'un chunk (`map_remove`), nettoyage des chunks vides (`map_remove_dead`), comptage des cellules vivantes (`map_alive_count`).                          |
| `chunk_map‑3.c  ` | Itérateurs `map_first` / `map_next` pour parcourir tous les chunks, et `map_copy` pour dupliquer une map entière.                                                                                                                                       |
| `chunk_map‑4.c  ` | Accès global aux cellules par coordonnées monde : `get_cell_global` et `set_cell_global` (traduit coordonnées → chunk + offset local).                                                                                                                  |

### Module `config` — Configuration clavier

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `config.h       ` | Header-only. Définit `t_key_config` (tous les raccourcis clavier), les valeurs par défaut (compatibles AZERTY), et les fonctions inline de lecture (`load_key_config`) et d'écriture (`save_key_config`) du fichier `keys.cfg`.                         |

### Module `renderer` — Rendu graphique

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `renderer.h     ` | Header-only. Définit 5 thèmes de couleurs (Violet, Vert, Ambre, Cyan, Blanc), la caméra 2D simplifiée `t_camera2d_gol`, les conversions écran↔cellule, et toutes les fonctions inline de rendu : grille, chunks, croix d'origine.                       |

### Module `save` — Sauvegarde et chargement

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `save.h         ` | Déclare toutes les fonctions du module : bounding box, encodage/décodage RLE, sauvegarde/chargement JSON.                                                                                                                                               |
| `save‑1.c       ` | Calcul de la bounding box des cellules vivantes (`map_bounding_box`), écriture de tokens RLE avec retour à la ligne automatique, et écriture d'une ligne RLE dans un fichier.                                                                           |
| `save‑2.c       ` | Recherche du dernier pixel vivant d'une ligne, écriture complète d'un fichier `.rle` (`save_rle`), parsing des tags RLE (`o`/`b`/`$`/`!`) et chargement d'un fichier `.rle` (`load_rle`).                                                               |
| `save‑3.c       ` | Sauvegarde et chargement au format JSON minimal `{"name":"…","cells":[[x,y],…]}` (`save_json` / `load_json`).                                                                                                                                           |

### Module `simulation` — Moteur de simulation

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `simulation.h   ` | Header-only. Comptage des 8 voisins d'une cellule (`count_neighbors`), collecte des chunks à traiter avec déduplication par hashset (`sim_collect_todo`). Déclare `simulation_step`.                                                                    |
| `simulation.c   ` | Applique les règles B3/S23 sur tous les chunks actifs et leurs voisins immédiats. Génère la map de la prochaine génération, remplace l'ancienne et nettoie les chunks vides.                                                                            |

### Module `ui` — Interface utilisateur

| Fichier           | Rôle / Explication                                                                                                                                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ui.h           ` | Header UI central. Définit tous les enums (`t_screen`, `t_btn_state`, `t_ui_action`, `t_menu_action`) et les structures d'état (`t_save_zone_state`, `t_place_state`, `t_random_state`). Déclare toutes les fonctions UI.                               |
| `ui_shared.h    ` | Constantes partagées entre tous les fichiers UI : palette de couleurs (`C_BG`, `C_HI`, `C_PANEL`…), tailles de fonte (`FS`, `FM`, `FL`, `FXL`), et déclarations des fonctions utilitaires de base.                                                      |
| `ui.c           ` | Fonctions UI de base : `panel_draw`, `text_c` (texte centré), `overlay` (fond semi-transparent), `draw_tooltip`, et `ui_button` (bouton cliquable avec états idle/hover/active).                                                                        |
| `ui_hud.c       ` | Barre HUD en bas d'écran : statut run/pause, génération, nombre de cellules vivantes, vitesse, FPS, position curseur, graphe d'historique de population. Aussi `ui_draw_message()` pour les messages temporaires.                                       |
| `ui_browser‑1.c ` | Chargement de la liste des fichiers `.rle` depuis `assets/patterns/` et `saves/`, filtrage par recherche textuelle (insensible à la casse), prévisualisation d'un pattern avec mise en cache, barre de recherche interactive.                           |
| `ui_browser‑2.c ` | Liste scrollable de fichiers avec scrollbar, affichage du dossier source, prévisualisation au survol, et fenêtre complète `ui_draw_load_browser()`.                                                                                                     |
| `ui_icons.h     ` | Déclare le type `t_icon_draw` (fonction de dessin d'icône vectorielle) et toutes les icônes disponibles, ainsi que `icon_button()`.                                                                                                                     |
| `ui_icons‑1.c   ` | `icon_button()` : bouton avec icône vectorielle, gestion hover/active/tooltip.                                                                                                                                                                          |
| `ui_icons‑2.c   ` | Icônes vectorielles : save (disquette), load (dossier), random (grille de points), menu (hamburger), grid (quadrillage).                                                                                                                                |
| `ui_icons‑3.c   ` | Icônes vectorielles : HUD (barres), chunk debug (carrés imbriqués), undo (flèche circulaire), copy (doubles rectangles), clear zone (rectangle + croix).                                                                                                |                                                       
| `ui_icons‑4.c   ` | Icônes vectorielles : play (triangle), pause (deux barres), step (triangle + barre), clear (croix).                                                                                                                                                     |
| `ui_icons‑5.c   ` | Icône vectorielle : paste (presse-papier avec flèche).                                                                                                                                                                                                  |
| `ui_keybinds‑1.c` | Table des 28 raccourcis configurables (`g_kb_table`) organisée par catégories. Fonctions de nommage des touches : `kname`, `kname_mod`, `kname_arrow`, `kname_fn`.                                                                                      |
| `ui_keybinds‑2.c` | Dessin des séparateurs de catégorie, des lignes de raccourci avec badge de touche, scrollbar, gestion du scroll, et capture d'une nouvelle touche (`kb_capture`).                                                                                       |
| `ui_keybinds‑3.c` | Fenêtre complète de configuration des touches (`ui_draw_keybinds`) : panel scrollable, scissor mode, clic sur badge pour reconfigurer, bouton Retour.                                                                                                   |
| `ui_menu‑1.c    ` | Menu principal : items (Reprendre / Touches / Crédits / Quitter), dessin du panel, et initialisation/dessin des lignes de crédits.                                                                                                                      |
| `ui_menu‑2.c    ` | Fenêtre des crédits (`ui_draw_credits`) : affiche les infos du projet (moteur, langage, format de save…).                                                                                                                                               |
| `ui_random.c    ` | Overlay de remplissage aléatoire en deux phases : phase 0 = sélection de zone par drag sur la grille, phase 1 = panneau avec slider de densité, boutons Remplir/Annuler.                                                                                |
| `ui_savezone‑1.c` | Phase 0 de la sauvegarde de zone : sélection rectangulaire par drag, dessin de l'overlay et de la boîte d'info. Édition du nom de fichier (`sz_name_edit`).                                                                                             |
| `ui_savezone‑2.c` | Phase 1 de la sauvegarde de zone : panneau avec affichage des coordonnées, champ de saisie du nom, boutons Sauvegarder/Annuler. Fonction principale `ui_draw_save_zone()`.                                                                              |
| `ui_toolbar‑1.c ` | Groupes de boutons de la toolbar : simulation (play/pause, step, clear, undo), fichiers (save, load), outils (random, copy, paste, clear zone), et bouton de recentrage.                                                                                |
| `ui_toolbar‑2.c ` | Groupes vue (grille, HUD, debug chunks, sélecteur de thème avec aperçu couleur) et slider de vitesse. Fonction principale `ui_draw_toolbar()` qui assemble toute la barre.                                                                              |

---

## Formats de fichiers

| Format                    | Extension  | Utilisation                                                                                                          |
|---------------------------|------------|----------------------------------------------------------------------------------------------------------------------|
| RLE (Run-Length Encoding) | `.rle`     | Format standard compatible Golly. Sauvegarde et chargement de patterns. Stocké dans `assets/patterns/` ou `saves/`.  |
| JSON minimal              | `.json`    | Format alternatif `{"name":"…","cells":[[x,y],…]}`.                                                                  |
| Config clavier            | `keys.cfg` | Généré automatiquement au premier lancement. Paires `nom=valeur` (codes raylib).                                     |

---

## Dépendances

- **raylib 5.0** — fenêtre, rendu 2D, inputs souris/clavier
- **C11** — standard C utilisé
- Bibliothèques standard : `stdlib`, `stdio`, `string`, `math`, `time`, `dirent`

---
