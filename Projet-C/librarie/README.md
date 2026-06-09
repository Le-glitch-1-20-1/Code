# 📚 Ma Bibliothèque — Application de bureau Windows

Application locale de gestion de bibliothèque personnelle.
Les données sont sauvegardées dans : `Documents\MaBibliotheque\livres.json`

---

## 🚀 Installation rapide (pour lancer l'appli)

### Prérequis
- **Node.js** : https://nodejs.org (télécharge la version LTS, puis installe-le)
- Ouvre un terminal après l'installation et vérifie avec : `node --version`

### Étapes

1. **Pour lancer sous linux**
```
npx electron . --no-sandbox
```

2. **Compile Windows**
```
cp -r "/media/le-glitch/Code/Programation/Projet-C/librarie" ~/Documents/
cd ~/Documents/librarie
rm -rf node_modules package-lock.json dist
npm install
npm install --save-dev electron-builder
npm run build
```

---

## 📦 Compiler un .exe Windows (optionnel)

Pour avoir un vrai fichier `.exe` installable :


npm run build
```

Le fichier `.exe` sera dans le dossier `dist/`.
- `Ma Bibliothèque Setup.exe` → installateur classique
- `Ma Bibliothèque Portable.exe` → portable, aucune installation requise

---

## ✨ Fonctionnalités

- ➕ Ajouter, modifier, supprimer des livres
- 🖼 Couverture personnalisée (photo depuis ton PC)
- 🔍 Recherche instantanée (titre, auteur, genre, ISBN)
- 📂 Filtres : En cours, Lus, Non lus, Prêtés, Favoris, par Genre
- 🔢 Tri par titre, auteur, année, note, date d'ajout
- ⭐ Notes de 0 à 5 étoiles
- 📋 Vue grille ou liste
- 💾 Sauvegarde automatique dans un fichier JSON
- ⬆ Export / ⬇ Import JSON
- 📁 Accès direct au dossier de données
- Raccourcis : `Ctrl+N` (nouveau), `Ctrl+F` (recherche), `Echap` (fermer)

---

## 📁 Où sont mes données ?

```
C:\Users\TonNom\Documents\MaBibliotheque\
  ├── livres.json        ← tous tes livres
  └── couvertures\       ← tes photos de couverture
```

Tu peux sauvegarder ce dossier sur une clé USB ou un cloud pour ne jamais perdre tes données.
