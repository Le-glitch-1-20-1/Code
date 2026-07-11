# Projet-sh

Scripts Bash autonomes avec interface interactive en ligne de commande (menus, couleurs,
détection automatique des outils disponibles) doublée d'un mode CLI complet.

---

## Scripts

### `App-manager.sh` — Gestionnaire d'applications Linux

Interface unifiée pour lister, rechercher, installer, supprimer et mettre à jour des paquets
à travers plusieurs gestionnaires (système/apt, snap, flatpak, appimage, pip, npm, cargo).
Détecte automatiquement les gestionnaires disponibles sur la machine.

```bash
./App-manager.sh                                   # menu interactif
./App-manager.sh --list snap                        # lister les paquets snap
./App-manager.sh --search vlc --manager flatpak      # rechercher un paquet
./App-manager.sh --install htop --manager system -y  # installer sans confirmation
./App-manager.sh --remove htop --manager system --yes
./App-manager.sh --update-manager npm                # mettre à jour un seul gestionnaire
./App-manager.sh --update-all --yes                  # tout mettre à jour
./App-manager.sh --check-updates                     # lister les mises à jour dispo (sans rien changer)
./App-manager.sh --export                            # exporter la liste des apps installées
./App-manager.sh --help
```

### `Midi-tester.sh` — Testeur de ports MIDI

Écoute et affiche en direct les messages reçus sur les ports MIDI détectés.

```bash
./Midi-tester.sh                # écoute tous les ports détectés
./Midi-tester.sh --list         # liste les ports/périphériques sans écouter
./Midi-tester.sh --port 20:0    # écoute un port précis (option répétable)
./Midi-tester.sh -p 20:0 -p 24:0
./Midi-tester.sh --help
```

## Structure

```
Projet-sh/
├── App-manager.sh
└── Midi-tester.sh
```

## Prérequis

- Bash
- Selon les fonctionnalités utilisées : `apt`/`dpkg`, `snap`, `flatpak`, `pip3`, `npm`, `cargo`
  (`App-manager.sh` détecte automatiquement ce qui est disponible)
- Pour `Midi-tester.sh` : ALSA (`amidi`/`aconnect`, environnement Linux avec MIDI)

## Auteurs

Scripts réalisés dans le cadre de projets personnels.
