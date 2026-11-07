# Guide de style des scripts console (v1.0)

Ce document décrit **exactement** le style commun à `App-manager.sh`, `Midi-tester.sh` et
`Detect-manager.sh`, et comment le réappliquer à n'importe quel autre `.sh`.

Le style tient dans **un seul bloc de code**, délimité par deux marqueurs, collé à
l'identique dans chaque script (les scripts restent donc autonomes, sans fichier à sourcer) :

```
# >>> STYLE BEGIN v1.0 — ... >>>
...
# <<< STYLE END <<<
```

Le fichier `style-template.sh` est un script vierge qui contient déjà ce bloc, la structure
standard et des démos de chaque fonction. **Le plus simple pour un nouveau script : copier ce
modèle.**

---

## 1. Principes

| Règle                       | Détail                                                                                                         |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Shell                        | `#!/usr/bin/env bash`, bash ≥ 4.3 (nécessaire pour `local -n`)                                            |
| Langue de l'interface        | Anglais (messages, menus, aide). Commentaires en anglais                                                        |
| Indentation du code          | Tabulations                                                                                                     |
| Retrait à l'écran          | Toute sortie visible est décalée de **2 espaces**                                                       |
| Couleurs                     | Désactivées automatiquement si la sortie n'est pas un terminal (`                                             |
| Interactif vs CLI            | Chaque script a un menu **et** des options CLI. Toute option d'action = mode non interactif (pas de menu) |
| Sans terminal et sans option | Affiche l'aide et quitte avec le code 1                                                                         |
| Ctrl+C                       | Message jaune `Interrupted.`, code 130 (ou `Stopping listening.` / code 0 pour un script d'écoute)         |
| Fin de script                | Le curseur est toujours restauré (`trap ui_restore EXIT`)                                                    |

---

## 2. Palette et sens des couleurs

| Variable    | Code     | Utilisation                                                                                                    |
| ----------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| `CYAN`    | `0;36` | Cadre de la bannière, prompts (`?`), élément sélectionné (`»`), en-têtes de tableau, valeur choisie |
| `GREEN`   | `0;32` | Succès (`✔`), « Done », « See you soon! », élément détecté                                         |
| `YELLOW`  | `1;33` | Avertissement (`⚠`), titre d'une action en cours, message d'interruption                                    |
| `RED`     | `0;31` | Erreur (`✗`), action destructive (suppression)                                                              |
| `MAGENTA` | `0;35` | Règles horizontales et titres de section (`hr`, `section`)                                                |
| `BOLD`    | `1`    | Titres, valeurs importantes, noms                                                                              |
| `DIM`     | `2`    | Information secondaire : chemins, aides, bordures de tableau, `(none)`                                       |
| `RESET`   | `0`    | Toujours refermer une couleur avec `${RESET}`                                                                |

Variables associées : `HIDE_CURSOR`, `SHOW_CURSOR` (vides hors terminal).

## 3. Symboles

| Symbole                    | Sens                              | Fonction qui l'affiche               |
| -------------------------- | --------------------------------- | ------------------------------------ |
| `✔`                     | succès / trouvé / choix validé | `msg_ok`, `item_ok`, fin de menu |
| `✗`                     | erreur                            | `msg_err`                          |
| `⚠`                     | avertissement                     | `msg_warn`                         |
| `•`                     | information / puce de liste       | `msg_info`                         |
| `?`                      | question posée (menus)           | `select_menu`, `checkbox_menu`   |
| `»`                     | ligne sélectionnée dans un menu | menus                                |
| `○`                     | ignoré (« Skipped »)           | résumés de tableau                 |
| `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`   | spinner                           | `spin_start`, `run_task`         |
| `╭╮╰╯│─`           | cadre arrondi de la bannière     | `banner`                           |
| `┌┬┐├┼┤└┴┘│─` | tableaux                          | `print_table`                      |

---

## 4. Référence des fonctions du bloc

### Messages

| Appel                | Rendu                                         |
| -------------------- | --------------------------------------------- |
| `msg_ok "texte"`   | `  ✔ texte` (✔ vert)                      |
| `msg_err "texte"`  | `  ✗ texte` en rouge, **sur stderr** |
| `msg_warn "texte"` | `  ⚠ texte` en jaune                       |
| `msg_info "texte"` | `  • texte` (• cyan)                      |
| `msg_dim "texte"`  | `  texte` en gris (aides, « (none) »)     |
| `die "texte"`      | `msg_err` puis `exit 1`                   |

### Utilitaires

| Appel                          | Rôle                                               |
| ------------------------------ | --------------------------------------------------- |
| `have cmd`                   | Vrai si la commande existe                          |
| `rep "─" 20`                | Répète un caractère N fois (sans sous-processus) |
| `term_width`                 | Largeur du terminal (80 par défaut)                |
| `pad_center "texte" largeur` | Centre un texte (sans codes ANSI)                   |

### Mise en page

| Appel                             | Rendu                                                                                                                                           |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `banner "Titre" ["Sous-titre"]` | Cadre arrondi cyan, titre en gras, sous-titre grisé. À afficher **une fois** au démarrage (ou à chaque tour de menu après `clear`) |
| `hr ["Titre"]`                  | Règle magenta pleine largeur, avec titre intégré si fourni                                                                                   |
| `section "Titre"`               | Ligne vide + `hr "Titre"` + ligne vide. **À utiliser pour chaque bloc de sortie**                                                      |
| `kv "Libellé" "valeur"`        | `  Libellé       : valeur` (libellé sur 14 colonnes, valeur en gras)                                                                        |
| `item_ok nom [détail] [extra]` | `  ✔ nom  détail(grisé)  extra` pour un élément détecté / trouvé                                                                      |

### Tableaux

```bash
rows=($'alpha\t1.0' $'beta\t2.3')          # une ligne = colonnes séparées par TAB
print_table $'Name\tVersion' rows           # 1er arg : en-têtes (TAB), 2e : NOM du tableau
```

Largeurs de colonnes calculées automatiquement. Tableau vide → `(no entries found)`.

### Spinner et tâches

| Appel                                    | Rôle                                                                                             |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `spin_start "message"` / `spin_stop` | Spinner manuel autour d'un travail long (inactif hors terminal)                                   |
| `run_task "message" cmd args…`        | Lance la commande derrière un spinner (sortie masquée), affiche `✔`/`✗`, renvoie son code |
| `ui_restore`                           | Arrête le spinner et réaffiche le curseur. **À brancher sur `trap … EXIT`**           |

### Menu à choix unique

```bash
select_menu "What would you like to do?" "Option A" "Option B" "$SEP" "Quit" || exit 1
case "$SELECTED" in 0) … ;; 1) … ;; 3) exit 0 ;; esac   # $SELECTED = index (0-based)
```

* Flèches haut/bas ou `j`/`k`, Entrée pour valider.
* `"$SEP"` insère un séparateur grisé, non sélectionnable (il **compte** dans les index).
* Une fois validé, le menu est remplacé par une ligne `✔ prompt  choix`.
* Sans terminal : message d'erreur et code retour 1.

### Menu à choix multiples

```bash
checkbox_menu "Select port(s):" "${labels[@]}" || exit 1
for i in "${SELECTED_IDX[@]}"; do … ; done          # tableau d'index cochés (peut être vide)
```

Espace pour cocher, Entrée pour valider, flèches ou `j`/`k` pour naviguer.

### Questions

| Appel                    | Rôle                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------- |
| `confirm "Question ?"` | `[y/N]`, accepte `y/Y/o/O`. Toujours vrai si `AUTO_YES=true` (option `--yes`) |
| `pause`                | « Press [Enter] to continue… » (à la fin d'une action dans un menu)               |

---

## 5. Structure standard d'un script

Dans cet ordre (voir `style-template.sh`) :

1. `#!/usr/bin/env bash` + commentaire de 1–2 lignes + `set -o pipefail`
2. `VERSION="x.y.z"` puis `readonly VERSION`
3. **Le bloc `STYLE BEGIN … STYLE END`** (ne pas le modifier)
4. `Global state` : variables globales, `trap ui_restore EXIT`, `trap '…' INT`
5. Sections de fonctions, chacune sous un en-tête de ce type :
   ```bash
   # ──────────────────────────────────────────────────────────────────────────────
   #  Titre de la section
   # ──────────────────────────────────────────────────────────────────────────────
   ```
6. `menu()` (menu interactif), si le script en a un
7. `usage()`, `need_arg()`, `main()`, et en dernière ligne `main "$@"`

Ne pas sourcer de fichier système qui définit `VERSION` (par exemple `/etc/os-release`) :
`VERSION` est en lecture seule. Lire la valeur avec `sed` à la place.

## 6. Conventions CLI

| Élément           | Règle                                                                                                    |
| ------------------- | --------------------------------------------------------------------------------------------------------- |
| Options communes    | `-h, --help`, `-v, --version` (affiche `Nom vX.Y.Z`), `-y, --yes` si le script pose des questions |
| Option avec valeur  | `need_arg "$@" \|\| break` avant de lire `$2`                                                           |
| Option inconnue     | `msg_err "Unknown option: $1"`, affiche l'aide, code 1                                                  |
| Aide (`usage`)    | Retrait de 4 espaces, options alignées, section `Examples:` à la fin                                  |
| Mode non interactif | Dès qu'une option d'action est passée, le menu est sauté                                               |

---

## 7. Appliquer le style à un nouveau script

**Méthode A — nouveau script :** copier `style-template.sh`, le renommer, remplacer `NAME`,
écrire ses propres fonctions et son `menu()`.

**Méthode B — script existant :**

1. Passer le script en bash (`#!/usr/bin/env bash`) s'il était en `sh`.
2. Supprimer ses propres définitions de couleurs, `have`, `rep`, bannière, menus, spinner,
   tableaux, `confirm`, `pause`.
3. Coller le bloc `STYLE BEGIN … STYLE END` juste après `VERSION`.
4. Remplacer les affichages : `echo "Error…"` → `msg_err`, `echo "OK"` → `msg_ok`, titres →
   `section`, `clé : valeur` → `kv`, listes d'éléments trouvés → `item_ok`, tableaux → `print_table`.
5. Remplacer les menus maison par `select_menu` / `checkbox_menu` (résultat dans `$SELECTED` /
   `$SELECTED_IDX`).
6. Ajouter `trap ui_restore EXIT` et la gestion de `-h` / `-v`.

## 8. Vérifier / mettre à jour le bloc

Le bloc doit rester **strictement identique** partout. Vérification (les empreintes doivent
être toutes égales) :

```bash
for f in *.sh; do
  sed -n '/^# >>> STYLE BEGIN/,/^# <<< STYLE END/p' "$f" | md5sum | sed "s|-|$f|"
done
```

Pour propager une nouvelle version du bloc d'un script de référence `ref.sh` vers `autre.sh` :

```bash
blk=$(mktemp); sed -n '/^# >>> STYLE BEGIN/,/^# <<< STYLE END/p' ref.sh > "$blk"
awk -v blk="$blk" '
  /^# >>> STYLE BEGIN/ { while ((getline l < blk) > 0) print l; skip=1; next }
  /^# <<< STYLE END/   { skip=0; next }
  !skip
' autre.sh > autre.sh.new && mv autre.sh.new autre.sh
```

Penser à incrémenter le numéro de version dans la ligne `STYLE BEGIN vX.Y` quand le bloc change.

---

## 9. Où chaque élément est utilisé aujourd'hui

| Élément                      |   App-manager   | Midi-tester | Detect-manager |
| ------------------------------ | :-------------: | :---------: | :------------: |
| `banner`                     |    ✔ (menu)    |     ✔     |       ✔       |
| `section` / `hr`           |       ✔       |     ✔     |       ✔       |
| `msg_*`                      |       ✔       |     ✔     |       ✔       |
| `kv`                         |       ✔       |            |       ✔       |
| `item_ok`                    | ✔ (détection) | ✔ (ports) |       ✔       |
| `print_table`                |       ✔       |            |                |
| `select_menu`                |       ✔       |     ✔     |                |
| `checkbox_menu`              |                |     ✔     |                |
| `spin_start` / `spin_stop` |       ✔       |            |                |
| `confirm` / `pause`        |       ✔       |            |                |
| `run_task`                   |                |            |                |

`run_task` est fourni pour les prochains scripts.
