# Projet-sh

Scripts Bash autonomes avec interface interactive en ligne de commande (menus, couleurs,
détection automatique des outils disponibles) doublée d'un mode CLI complet.
Tous les scripts partagent le même style console, décrit dans [`STYLE-GUIDE.md`](STYLE-GUIDE.md).

---

## Scripts

### `App-manager.sh` — Gestionnaire d'applications Linux

Interface unifiée pour lister, rechercher, installer, supprimer et mettre à jour des paquets
à travers plusieurs gestionnaires (système/apt, snap, flatpak, appimage, pip, npm, cargo, etc.).
Détecte automatiquement les gestionnaires disponibles sur la machine.

```bash
./App-manager.sh                                   # menu interactif
./App-manager.sh --detect                           # détecter gestionnaires et outils
./App-manager.sh --list snap                        # lister les paquets snap
./App-manager.sh --list snap --filter code          # lister en filtrant par texte
./App-manager.sh --search vlc --manager flatpak      # rechercher un paquet
./App-manager.sh --install htop --manager system -y  # installer sans confirmation
./App-manager.sh --remove htop --manager system --yes
./App-manager.sh --update-manager npm                # mettre à jour un seul gestionnaire
./App-manager.sh --update-all --yes                  # tout mettre à jour
./App-manager.sh --check-updates                     # lister les mises à jour dispo (sans rien changer)
./App-manager.sh --export                            # exporter la liste des apps installées
./App-manager.sh --version
./App-manager.sh --help
```

### `Detect-manager.sh` — Détecteur d'outils et d'environnement

Affiche les gestionnaires de paquets et outils de build/téléchargement présents (avec leurs
versions), puis la distribution, le noyau et l'environnement de bureau (version, session
Wayland/X11, gestionnaire de fenêtres, gestionnaire de connexion).

```bash
./Detect-manager.sh                                  # rapport complet
NO_COLOR=1 ./Detect-manager.sh > rapport.txt         # rapport sans couleurs, dans un fichier
./Detect-manager.sh --version
./Detect-manager.sh --help
```

### `Midi-tester.sh` — Testeur de ports MIDI

Écoute et affiche en direct les messages reçus sur les ports MIDI détectés.

```bash
./Midi-tester.sh                # menu interactif (tous les ports / choix des ports / lister)
./Midi-tester.sh --list         # liste les ports/périphériques sans écouter
./Midi-tester.sh --port 20:0    # écoute un port précis (option répétable)
./Midi-tester.sh -p 20:0 -p 24:0
./Midi-tester.sh --version
./Midi-tester.sh --help
```

## Style commun

Les trois scripts embarquent le même bloc de style (couleurs, messages `✔ ✗ ⚠`, bannière,
sections, tableaux, spinner, menus à flèches). Les couleurs se désactivent seules quand la
sortie n'est pas un terminal ou si `NO_COLOR` est défini.

- [`STYLE-GUIDE.md`](STYLE-GUIDE.md) : documentation complète du style et méthode pour l'appliquer à d'autres scripts.
- [`style-template.sh`](style-template.sh) : modèle prêt à copier pour un nouveau script.

## Structure

```
Projet-sh/
├── App-manager.sh
├── Detect-manager.sh
├── Midi-tester.sh
├── style-template.sh
├── STYLE-GUIDE.md
└── README.md
```

## Prérequis

- Bash 4.3 ou plus récent, terminal compatible UTF-8
- Selon les fonctionnalités utilisées : `apt`/`dpkg`, `snap`, `flatpak`, `pip3`, `npm`, `cargo`
  (`App-manager.sh` détecte automatiquement ce qui est disponible ; `sudo` pour installer,
  supprimer ou mettre à jour ; `less` est utilisé comme pager s'il est présent)
- `Detect-manager.sh` : aucun prérequis particulier (`pgrep` pour la détection de l'environnement de bureau)
- `Midi-tester.sh` : ALSA (`aseqdump`/`aconnect`, paquet `alsa-utils`), `grep` avec l'option `-P`,
  utilisateur dans le groupe `audio`

## Auteurs

Scripts réalisés dans le cadre de projets personnels.
