/*
 * ============================================================
 *   Notre histoire d'amour - Version graphique avec Raylib
 * ============================================================
 *
 *   Affiche une fenetre avec :
 *	 - Un fond degrade rose/violet
 *	 - Des coeurs qui flottent en arriere-plan
 *	 - Le compte a rebours avant le prochain 24 aout
 *	 - Le nombre d'annees ensemble
 *
 *   A FAIRE AVANT DE COMPILER :
 *   Modifie ANNEE_MISE_EN_COUPLE avec l'annee de ta mise en couple.
 *
 *   INSTALLATION DE RAYLIB :
 *
 *   -- Linux (Debian/Ubuntu) --
 *	 sudo apt install libraylib-dev
 *	 (si pas dispo, voir https://github.com/raysan5/raylib/wiki/Working-on-GNU-Linux)
 *
 *   -- macOS (avec Homebrew) --
 *	 brew install raylib
 *
 *   -- Windows --
 *	 Le plus simple : installer via w64devkit ou MSYS2
 *	 Voir https://github.com/raysan5/raylib/wiki/Working-on-Windows
 *
 *   COMPILATION :
 *
 *   -- Linux / macOS --
 *	 gcc amour_raylib.c -o amour_raylib -lraylib -lm -lpthread -ldl -lrt -lX11
 *	 (sur macOS, remplace -lX11 par les frameworks : voir doc raylib)
 *
 *   -- Windows (MSYS2/w64devkit) --
 *	 gcc amour_raylib.c -o amour_raylib.exe -lraylib -lopengl32 -lgdi32 -lwinmm
 *
 *   EXECUTION :
 *	 ./amour_raylib
 * ============================================================
 */

#include "raylib.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

/* ---- A PERSONNALISER ---- */
#define ANNEE_MISE_EN_COUPLE 2024   /* <-- Change cette valeur ! */
#define JOUR_ANNIVERSAIRE 24
#define MOIS_ANNIVERSAIRE 8		  /* Aout = 8 */
/* -------------------------- */

#define NB_COEURS 40

typedef struct {
	float x, y;
	float vitesse;
	float taille;
	float alpha;
} Coeur;

int est_bissextile(int annee) {
	return (annee % 4 == 0 && annee % 100 != 0) || (annee % 400 == 0);
}

/* Dessine un coeur avec deux cercles (lobes du haut) + un carre tourne a 45
 * degres (pointe du bas). C'est la technique classique pour un coeur plein
 * et bien proportionne avec raylib. */
void DessinerCoeur(float x, float y, float taille, Color couleur) {
	float rayon = taille * 0.30f;

	/* Les deux bosses du haut */
	DrawCircleV((Vector2){ x - rayon, y }, rayon, couleur);
	DrawCircleV((Vector2){ x + rayon, y }, rayon, couleur);

	/* La pointe du bas : un carre tourne a 45 degres, cale sous les cercles */
	float cote = taille * 0.62f;
	Rectangle rectangle = { x, y + cote * 0.18f, cote, cote };
	Vector2 origine = { cote / 2.0f, cote / 2.0f };
	DrawRectanglePro(rectangle, origine, 45.0f, couleur);
}

int main(void) {
	const int largeurEcran = 900;
	const int hauteurEcran = 650;

	InitWindow(largeurEcran, hauteurEcran, "Notre histoire d'amour <3");
	SetTargetFPS(60);

	srand((unsigned int)time(NULL));

	/* Initialisation des coeurs flottants */
	Coeur coeurs[NB_COEURS];
	for (int i = 0; i < NB_COEURS; i++) {
		coeurs[i].x = (float)(rand() % largeurEcran);
		coeurs[i].y = (float)(rand() % hauteurEcran);
		coeurs[i].vitesse = 20.0f + (float)(rand() % 40);
		coeurs[i].taille = 10.0f + (float)(rand() % 20);
		coeurs[i].alpha = 0.15f + (float)(rand() % 30) / 100.0f;
	}

	/* Calcul de la date cible (une seule fois au demarrage) */
	time_t maintenant = time(NULL);
	struct tm aujourdhui = *localtime(&maintenant);

	int annee_actuelle = aujourdhui.tm_year + 1900;
	int mois_actuel = aujourdhui.tm_mon + 1;
	int jour_actuel = aujourdhui.tm_mday;

	int annee_cible = annee_actuelle;
	if (mois_actuel > MOIS_ANNIVERSAIRE ||
		(mois_actuel == MOIS_ANNIVERSAIRE && jour_actuel > JOUR_ANNIVERSAIRE)) {
		annee_cible = annee_actuelle + 1;
	}

	struct tm date_cible = {0};
	date_cible.tm_year = annee_cible - 1900;
	date_cible.tm_mon = MOIS_ANNIVERSAIRE - 1;
	date_cible.tm_mday = JOUR_ANNIVERSAIRE;
	time_t temps_cible = mktime(&date_cible);

	struct tm aujourdhui_minuit = aujourdhui;
	aujourdhui_minuit.tm_hour = 0;
	aujourdhui_minuit.tm_min = 0;
	aujourdhui_minuit.tm_sec = 0;
	time_t temps_aujourdhui = mktime(&aujourdhui_minuit);

	(void)temps_aujourdhui; /* plus utilise : on recalcule en temps reel plus bas */

	int annees_ensemble = annee_actuelle - ANNEE_MISE_EN_COUPLE;
	if (mois_actuel < MOIS_ANNIVERSAIRE ||
		(mois_actuel == MOIS_ANNIVERSAIRE && jour_actuel < JOUR_ANNIVERSAIRE)) {
		annees_ensemble -= 1;
	}

	char texteJours[64] = "";

	char texteAnnees[64];
	snprintf(texteAnnees, sizeof(texteAnnees), "%d an%s ensemble",
			 annees_ensemble, (annees_ensemble > 1) ? "s" : "");

	Color rose = (Color){ 255, 105, 180, 255 };
	Color roseClair = (Color){ 255, 192, 203, 255 };
	Color violet = (Color){ 147, 112, 219, 255 };

	float temps = 0.0f;

	while (!WindowShouldClose()) {
		float dt = GetFrameTime();
		temps += dt;

		/* Mise a jour des coeurs flottants */
		for (int i = 0; i < NB_COEURS; i++) {
			coeurs[i].y -= coeurs[i].vitesse * dt;
			if (coeurs[i].y < -20) {
				coeurs[i].y = hauteurEcran + 20;
				coeurs[i].x = (float)(rand() % largeurEcran);
			}
		}

		/* Recalcul du temps restant en temps reel (jours/heures/min/sec) */
		time_t maintenant_frame = time(NULL);
		double secondes_restantes = difftime(temps_cible, maintenant_frame);
		if (secondes_restantes < 0) {
			secondes_restantes = 0;
		}

		long total_secondes = (long)secondes_restantes;
		int jours   = (int)(total_secondes / 86400);
		int heures  = (int)((total_secondes % 86400) / 3600);
		int minutes = (int)((total_secondes % 3600) / 60);
		int secondes = (int)(total_secondes % 60);

		if (total_secondes <= 0) {
			snprintf(texteJours, sizeof(texteJours), "C'est aujourd'hui !!");
		} else {
			snprintf(texteJours, sizeof(texteJours), "%dj  %02dh  %02dmin  %02ds",
					 jours, heures, minutes, secondes);
		}

		BeginDrawing();

		/* Fond degrade */
		DrawRectangleGradientV(0, 0, largeurEcran, hauteurEcran, roseClair, violet);

		/* Coeurs flottants en arriere-plan */
		for (int i = 0; i < NB_COEURS; i++) {
			Color c = WHITE;
			c.a = (unsigned char)(coeurs[i].alpha * 255);
			DessinerCoeur(coeurs[i].x, coeurs[i].y, coeurs[i].taille, c);
		}

		/* Coeur central pulsant */
		float pulsation = 1.0f + 0.08f * sinf(temps * 2.0f);
		DessinerCoeur(largeurEcran / 2.0f, 160, 70.0f * pulsation, rose);

		/* Titre */
		const char *titre = "Notre histoire d'amour";
		int largeurTitre = MeasureText(titre, 40);
		DrawText(titre, (largeurEcran - largeurTitre) / 2, 260, 40, WHITE);

		/* Compte a rebours */
		int largeurJours = MeasureText(texteJours, 42);
		DrawText(texteJours, (largeurEcran - largeurJours) / 2, 345, 42, WHITE);

		/* Annees ensemble */
		int largeurAnnees = MeasureText(texteAnnees, 30);
		DrawText(texteAnnees, (largeurEcran - largeurAnnees) / 2, 430, 30, WHITE);

		/* Petit texte en bas */
		const char *soustitre = "avant notre anniversaire de couple";
		int largeurSous = MeasureText(soustitre, 20);
		DrawText(soustitre, (largeurEcran - largeurSous) / 2, 405, 20, WHITE);

		EndDrawing();
	}

	CloseWindow();
	return 0;
}
