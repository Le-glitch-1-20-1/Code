# ASCII Art — générateur de texte façon FIGlet

Petit outil en C qui affiche du texte en grand, façon [FIGlet](http://www.figlet.org/),
en utilisant des polices au format `.flf` / `.tlf`.

---

## Structure du projet

```
ascii-art/
├── Makefile
├── font.txt					← exemple de commande (voir plus bas)
├── include/
│   └── display_utils.h
├── src/
│   ├── main.c
│   ├── display_utils-1.c		← affichage / rendu des polices
│   └── display_utils-2.c		← parsing des arguments, gestion de la sortie
├── text/						← polices FIGlet utilisées par le programme (.flf, .tlf)
└── master/
    └── figlet-fonts-master/	← collection complète de polices FIGlet (source externe)
```

## Compilation

```bash
make        # compile le projet -> exécutable "ascii-art"
make clean  # supprime les fichiers objets (o/)
make fclean # supprime aussi l'exécutable
make re     # fclean + all
```

## Utilisation

```bash
./ascii-art font_name texte [o]
```

- `font_name` : nom du fichier de police à utiliser (doit être présent dans `text/`)
- `texte` : le texte à afficher (peut contenir plusieurs mots)
- `o` (optionnel) : si présent en dernier argument, le résultat est sauvegardé dans `font.txt`
  au lieu d'être affiché à l'écran

### Exemples

```bash
./ascii-art Standard.flf "Hello World"
./ascii-art Standard.flf "Hello World" o
```

### Lister / tester toutes les polices disponibles

```bash
./ascii-art font-test-txt
```

Affiche un aperçu du texte "TXT" avec chaque police du dossier `text/`.

## Polices

Le dossier `text/` contient les polices effectivement chargées par le programme
(recherchées via `FONT_FOLDER "text"`, défini dans `display_utils.h`).
Le dossier `master/figlet-fonts-master/` regroupe la collection complète
[figlet-fonts](https://github.com/xero/figlet-fonts), utilisée comme réserve
de polices supplémentaires.

## Auteurs

Projet réalisé dans le cadre de l'École 42.
