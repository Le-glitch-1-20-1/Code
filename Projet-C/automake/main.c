#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <string.h>
#include <sys/stat.h>
#include <ctype.h>

/* ============================================================
 *  LISTE DES BIBLIOTHEQUES A DETECTER
 *  Pour ajouter une bibliotheque : une seule ligne a ajouter ici.
 *  Les champs *_windows sont optionnels ("" si non concerne) et
 *  servent uniquement si l'utilisateur choisit de compiler pour Windows.
 * ============================================================ */
typedef struct {
	const char *nom;              // nom affiche a l'utilisateur
	const char *header;           // fichier a rechercher dans les #include, ex "raylib.h"
	const char *ldflags_linux;    // flags d'edition de liens (build Linux) ("" si aucun)
	const char *includes_windows; // -I... vers la version Windows de la lib ("" si aucun)
	const char *libpath_windows;  // -L... vers la version Windows de la lib ("" si aucun)
	const char *ldflags_windows;  // -l... pour le build Windows ("" si aucun)
} Bibliotheque;

static const Bibliotheque BIBLIOTHEQUES[] = {
	{ "raylib", "raylib.h",
	  "$(shell pkg-config --libs raylib 2>/dev/null || echo \"-lraylib\") -lm -lpthread -ldl -lrt -lX11",
	  "-I/home/le-glitch/raylib/raylib-windows/src",
	  "-L/home/le-glitch/raylib/raylib-windows/src",
	  "-lraylib -lopengl32 -lgdi32 -lwinmm" },
	/* Exemples pour en ajouter d'autres plus tard :
	{ "SDL2",   "SDL2/SDL.h", "$(shell pkg-config --libs sdl2 2>/dev/null || echo \"-lSDL2\")" },
	{ "OpenGL", "GL/gl.h",    "-lGL" },
	*/
};
#define NB_BIBLIOTHEQUES (sizeof(BIBLIOTHEQUES) / sizeof(BIBLIOTHEQUES[0]))

/* ============================================================
 *  DETECTION D'UN #include "xxx.h" DANS UN FICHIER / DOSSIER
 * ============================================================ */

int ligne_contient_include(const char *ligne, const char *header) {
	const char *p = ligne;

	while (isspace((unsigned char)*p)) p++;
	if (*p != '#') return 0;
	p++;
	while (isspace((unsigned char)*p)) p++;
	if (strncmp(p, "include", 7) != 0) return 0;
	p += 7;
	while (isspace((unsigned char)*p)) p++;

	char motif[128];
	snprintf(motif, sizeof(motif), "\"%s\"", header);
	return (strstr(p, motif) != NULL);
}

int est_fichier_cible(const char *nom) {
	size_t len = strlen(nom);
	if (len < 3) return 0;
	return (strcmp(nom + len - 2, ".c") == 0 || strcmp(nom + len - 2, ".h") == 0);
}

int fichier_contient_include(const char *chemin, const char *header) {
	FILE *f = fopen(chemin, "r");
	if (!f) return 0;

	char ligne[512];
	int trouve = 0;

	while (fgets(ligne, sizeof(ligne), f)) {
		if (ligne_contient_include(ligne, header)) {
			trouve = 1;
			break;
		}
	}

	fclose(f);
	return trouve;
}

int dossier_contient_include(const char *path, const char *header) {
	DIR *dir = opendir(path);
	if (!dir) return 0;

	struct dirent *entry;
	int trouve = 0;

	while ((entry = readdir(dir)) != NULL) {
		if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
			continue;

		char full_path[1024];
		snprintf(full_path, sizeof(full_path), "%s/%s", path, entry->d_name);

		struct stat st;
		if (stat(full_path, &st) == 0) {
			if (S_ISDIR(st.st_mode)) {
				if (dossier_contient_include(full_path, header)) {
					trouve = 1;
				}
			} else if (S_ISREG(st.st_mode) && est_fichier_cible(entry->d_name)) {
				if (fichier_contient_include(full_path, header)) {
					trouve = 1;
				}
			}
		}
	}
	closedir(dir);
	return trouve;
}

int est_un_dossier(const char *chemin) {
	struct stat st;
	if (stat(chemin, &st) != 0)
		return 0;
	return S_ISDIR(st.st_mode);
}

// Parcourt UNIQUEMENT les .c a la racine de "chemin" (pas recursif).
// Met *a_trouve_c a 1 si au moins un .c est present a la racine.
int verifier_fichiers_c_racine(const char *chemin, const char *header, int *a_trouve_c) {
	DIR *dossier = opendir(chemin);
	struct dirent *element;
	int trouve = 0;

	*a_trouve_c = 0;

	if (dossier == NULL) {
		perror("Impossible d'ouvrir le dossier");
		return 0;
	}

	while ((element = readdir(dossier)) != NULL) {
		if (strcmp(element->d_name, ".") == 0 || strcmp(element->d_name, "..") == 0)
			continue;

		char full_path[1024];
		snprintf(full_path, sizeof(full_path), "%s/%s", chemin, element->d_name);

		struct stat st;
		if (stat(full_path, &st) != 0)
			continue;

		if (S_ISREG(st.st_mode)) {
			size_t len = strlen(element->d_name);
			if (len >= 2 && strcmp(element->d_name + len - 2, ".c") == 0) {
				*a_trouve_c = 1;
				if (fichier_contient_include(full_path, header)) {
					trouve = 1;
				}
			}
		}
	}

	closedir(dossier);
	return trouve;
}

/* ============================================================
 *  TEST 1 + TEST 2 COMBINES POUR UNE BIBLIOTHEQUE DONNEE
 * ============================================================ */
int projet_utilise(const char *chemin, const char *header) {
	int a_c_racine = 0;
	int trouve = verifier_fichiers_c_racine(chemin, header, &a_c_racine);

	if (a_c_racine) {
		return trouve;
	}

	int trouve_src = 0;
	int trouve_include = 0;
	char sous_dossier[1024];

	snprintf(sous_dossier, sizeof(sous_dossier), "%s/src", chemin);
	if (est_un_dossier(sous_dossier)) {
		trouve_src = dossier_contient_include(sous_dossier, header);
	}

	snprintf(sous_dossier, sizeof(sous_dossier), "%s/include", chemin);
	if (est_un_dossier(sous_dossier)) {
		trouve_include = dossier_contient_include(sous_dossier, header);
	}

	return (trouve_src || trouve_include);
}

/* ============================================================
 *  UTILITAIRE : nom du dossier passe en entree (pour NAME)
 * ============================================================ */
void obtenir_nom_dossier(const char *chemin, char *dest, size_t taille) {
	size_t len = strlen(chemin);

	while (len > 1 && chemin[len - 1] == '/')
		len--;

	size_t debut = len;
	while (debut > 0 && chemin[debut - 1] != '/')
		debut--;

	size_t n = len - debut;
	if (n == 0) {
		snprintf(dest, taille, "program");
		return;
	}
	if (n >= taille)
		n = taille - 1;

	memcpy(dest, chemin + debut, n);
	dest[n] = '\0';
}

/* ============================================================
 *  GENERATION DU MAKEFILE
 * ============================================================ */

// Largeur de colonne utilisee pour aligner toutes les ":=" du Makefile
#define LARGEUR_ALIGNEMENT 14

// Ecrit "NOM<espaces>:= valeur" en alignant la colonne ":=" quelle que
// soit la longueur du nom de variable (evite le probleme des tabulations
// qui ne s'alignent pas pareil selon l'editeur).
void ecrire_variable(FILE *f, const char *nom, const char *valeur) {
	fprintf(f, "%-*s:= %s\n", LARGEUR_ALIGNEMENT, nom, valeur);
}

void generer_makefile(const char *chemin_projet, const int *resultats, int veut_windows) {
	// Nom de l'executable = nom du dossier passe en entree
	char name[256];
	obtenir_nom_dossier(chemin_projet, name, sizeof(name));

	// Structure du projet
	char src_dir[1024];
	snprintf(src_dir, sizeof(src_dir), "%s/src", chemin_projet);
	int a_src = est_un_dossier(src_dir);

	char include_dir[1024];
	snprintf(include_dir, sizeof(include_dir), "%s/include", chemin_projet);
	int a_include = est_un_dossier(include_dir);

	// Construction des flags Linux (une seule fois pour toutes les libs trouvees)
	char ldflags[1024] = "";
	for (size_t i = 0; i < NB_BIBLIOTHEQUES; i++) {
		if (resultats[i] && BIBLIOTHEQUES[i].ldflags_linux[0] != '\0') {
			if (ldflags[0] != '\0')
				strcat(ldflags, " ");
			strcat(ldflags, BIBLIOTHEQUES[i].ldflags_linux);
		}
	}
	int a_ldflags = (ldflags[0] != '\0');

	// Construction des flags Windows (seulement si demandes ET libs trouvees)
	char win_includes[1024] = "";
	char win_libpath[1024] = "";
	char win_ldflags[1024] = "";
	if (veut_windows) {
		for (size_t i = 0; i < NB_BIBLIOTHEQUES; i++) {
			if (!resultats[i])
				continue;
			if (BIBLIOTHEQUES[i].includes_windows[0] != '\0') {
				if (win_includes[0] != '\0') strcat(win_includes, " ");
				strcat(win_includes, BIBLIOTHEQUES[i].includes_windows);
			}
			if (BIBLIOTHEQUES[i].libpath_windows[0] != '\0') {
				if (win_libpath[0] != '\0') strcat(win_libpath, " ");
				strcat(win_libpath, BIBLIOTHEQUES[i].libpath_windows);
			}
			if (BIBLIOTHEQUES[i].ldflags_windows[0] != '\0') {
				if (win_ldflags[0] != '\0') strcat(win_ldflags, " ");
				strcat(win_ldflags, BIBLIOTHEQUES[i].ldflags_windows);
			}
		}
	}

	// Le Makefile doit etre cree DANS le dossier du projet (chemin_projet),
	// pas dans le dossier courant d'execution du programme.
	// fopen en mode "w" efface automatiquement le contenu si le fichier existe deja.
	char makefile_path[1200];
	snprintf(makefile_path, sizeof(makefile_path), "%s/Makefile", chemin_projet);

	FILE *f = fopen(makefile_path, "w");
	if (!f) {
		perror("Erreur lors de la creation du Makefile");
		return;
	}

	// --- Variables (toutes alignees sur la meme colonne) ---
	ecrire_variable(f, "CC", "gcc");
	if (veut_windows)
		ecrire_variable(f, "CC_WIN", "x86_64-w64-mingw32-gcc");

	char cflags_val[256];
	snprintf(cflags_val, sizeof(cflags_val), "-Wall -Wextra -Werror -Wunused%s",
	         a_include ? " -I include/" : "");
	ecrire_variable(f, "CFLAGS", cflags_val);

	if (a_ldflags)
		ecrire_variable(f, "LDFLAGS", ldflags);

	if (veut_windows) {
		ecrire_variable(f, "WIN_INCLUDES", win_includes);
		ecrire_variable(f, "WIN_LIBPATH", win_libpath);
		ecrire_variable(f, "WIN_LDFLAGS", win_ldflags);
	}
	fprintf(f, "\n");

	if (a_src)
		ecrire_variable(f, "SRC_DIR", "src");
	ecrire_variable(f, "OBJ_DIR", "o");
	ecrire_variable(f, "NAME", name);
	fprintf(f, "\n");

	fprintf(f, "# Liste des .c\n");
	ecrire_variable(f, "SRC", a_src ? "$(wildcard $(SRC_DIR)/*.c)" : "$(wildcard *.c)");
	fprintf(f, "\n");

	fprintf(f, "# Transformation en .o dans o/\n");
	if (a_src)
		ecrire_variable(f, "OBJ", "$(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(SRC))");
	else
		ecrire_variable(f, "OBJ", "$(patsubst %.c, $(OBJ_DIR)/%.o, $(SRC))");
	fprintf(f, "\n");

	if (veut_windows) {
		fprintf(f, "# Regle par defaut :\n");
		fprintf(f, "#  - compile toujours Linux en premier\n");
		fprintf(f, "#  - si echec -> make s'arrete, Windows n'est PAS propose\n");
		fprintf(f, "#  - si succes -> demande si on compile aussi pour Windows\n");
		fprintf(f, "all: $(NAME)\n");
		fprintf(f, "\t@read -p \">> Compiler aussi pour Windows ? [y/N] \" rep; \\\n");
		fprintf(f, "\tif [ \"$$rep\" = \"y\" ] || [ \"$$rep\" = \"Y\" ]; then \\\n");
		fprintf(f, "\t\t$(MAKE) --no-print-directory windows; \\\n");
		fprintf(f, "\telse \\\n");
		fprintf(f, "\t\techo \">> Build Windows annule.\"; \\\n");
		fprintf(f, "\tfi\n\n");
	} else {
		fprintf(f, "# Regle par defaut\n");
		fprintf(f, "all: $(NAME)\n\n");
	}

	fprintf(f, "# Creation de l'executable Linux\n");
	fprintf(f, "$(NAME): $(OBJ)\n");
	fprintf(f, "\t$(CC) $(CFLAGS) $(OBJ) -o $(NAME)%s\n\n", a_ldflags ? " $(LDFLAGS)" : "");

	fprintf(f, "# Compilation des .c vers .o dans o/\n");
	if (a_src)
		fprintf(f, "$(OBJ_DIR)/%%.o: $(SRC_DIR)/%%.c | $(OBJ_DIR)\n");
	else
		fprintf(f, "$(OBJ_DIR)/%%.o: %%.c | $(OBJ_DIR)\n");
	fprintf(f, "\t$(CC) $(CFLAGS) -c $< -o $@\n\n");

	fprintf(f, "# Creation du dossier o/ si absent\n");
	fprintf(f, "$(OBJ_DIR):\n");
	fprintf(f, "\tmkdir -p $(OBJ_DIR)\n\n");

	if (veut_windows) {
		fprintf(f, "# Build Windows (.exe, sans console), appele uniquement si demande\n");
		fprintf(f, ".PHONY: windows\n");
		fprintf(f, "windows: $(SRC)\n");
		fprintf(f, "\t$(CC_WIN) $(CFLAGS) $(SRC) -o $(NAME).exe \\\n");
		fprintf(f, "\t\t-mwindows -Wl,--subsystem,windows \\\n");
		fprintf(f, "\t\t$(WIN_INCLUDES) $(WIN_LIBPATH) $(WIN_LDFLAGS)\n");
		fprintf(f, "\t@echo \">> Build Windows termine -> $(NAME).exe\"\n\n");
	}

	fprintf(f, "# Nettoyage\n");
	fprintf(f, "clean:\n");
	fprintf(f, "\trm -rf $(OBJ_DIR)\n\n");

	fprintf(f, "fclean: clean\n");
	fprintf(f, "\trm -f $(NAME)%s\n\n", veut_windows ? " $(NAME).exe" : "");

	fprintf(f, "re: fclean all\n\n");

	fprintf(f, ".PHONY: all clean fclean re\n");

	fclose(f);

	printf("Makefile genere avec succes dans %s (NAME = %s).\n", makefile_path, name);
}

int main(void) {
	char chemin[1024];
	int resultats[NB_BIBLIOTHEQUES];

	printf("Entrer le chemin du dossier : ");
	if (scanf("%1023s", chemin) != 1) {
		fprintf(stderr, "Erreur de saisie.\n");
		return EXIT_FAILURE;
	}

	for (size_t i = 0; i < NB_BIBLIOTHEQUES; i++) {
		resultats[i] = projet_utilise(chemin, BIBLIOTHEQUES[i].header);
		printf("%s : %s\n", BIBLIOTHEQUES[i].nom, resultats[i] ? "trouvee" : "non trouvee");
	}

	char rep = 'n';
	printf("Voulez-vous que le Makefile propose aussi la compilation pour Windows ? [y/N] ");
	if (scanf(" %c", &rep) != 1) {
		fprintf(stderr, "Erreur de saisie.\n");
		return EXIT_FAILURE;
	}
	int veut_windows = (rep == 'y' || rep == 'Y');

	generer_makefile(chemin, resultats, veut_windows);

	return 0;
}
