#!/usr/bin/env python3
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import argparse
import random
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.axes import Axes
from matplotlib.figure import Figure


@dataclass
class Ville:
	# Représente une ville par son identifiant et ses coordonnées cartésiennes
	identifiant: int
	x: float
	y: float


class GrapheTSP:
	# Contient les distances euclidiennes et la matrice de phéromones entre chaque paire de villes
	def __init__(self, villes: list[Ville]) -> None:
		self.villes: list[Ville] = villes
		self.nombre_villes: int = len(villes)
		self.distances: np.ndarray = self._calculer_distances()
		self.pheromones: np.ndarray = np.ones((self.nombre_villes, self.nombre_villes))

	def _calculer_distances(self) -> np.ndarray:
		# Construit la matrice symétrique des distances euclidiennes entre chaque ville
		matrice: np.ndarray = np.zeros((self.nombre_villes, self.nombre_villes))
		for i in range(self.nombre_villes):
			for j in range(self.nombre_villes):
				dx: float = self.villes[i].x - self.villes[j].x
				dy: float = self.villes[i].y - self.villes[j].y
				matrice[i][j] = (dx ** 2 + dy ** 2) ** 0.5
		return matrice

	def longueur_trajet(self, trajet: list[int]) -> float:
		# Calcule la longueur totale d'un trajet fermé passant par toutes les villes
		total: float = 0.0
		for indice in range(len(trajet)):
			ville_actuelle: int = trajet[indice]
			ville_suivante: int = trajet[(indice + 1) % len(trajet)]
			total += self.distances[ville_actuelle][ville_suivante]
		return total


class StrategieChoixVille(ABC):
	# Interface abstraite définissant comment une fourmi choisit sa prochaine ville
	@abstractmethod
	def choisir_prochaine_ville(self, graphe: GrapheTSP, ville_courante: int, villes_non_visitees: list[int], alpha: float, beta: float) -> int:
		raise NotImplementedError


class StrategieProbabiliste(StrategieChoixVille):
	# Implémente la règle probabiliste classique de l'ACO basée sur phéromones et visibilité
	def choisir_prochaine_ville(self, graphe: GrapheTSP, ville_courante: int, villes_non_visitees: list[int], alpha: float, beta: float) -> int:
		poids: list[float] = []
		for ville_candidate in villes_non_visitees:
			pheromone: float = graphe.pheromones[ville_courante][ville_candidate] ** alpha
			distance: float = graphe.distances[ville_courante][ville_candidate]
			visibilite: float = (1.0 / distance) ** beta if distance > 0 else 0.0
			poids.append(pheromone * visibilite)
		total_poids: float = sum(poids)
		if total_poids == 0:
			return random.choice(villes_non_visitees)
		probabilites: list[float] = [poids_individuel / total_poids for poids_individuel in poids]
		return random.choices(villes_non_visitees, weights=probabilites, k=1)[0]


@dataclass
class Fourmi:
	# Représente une fourmi effectuant un trajet complet sur le graphe
	trajet: list[int] = field(default_factory=list)
	longueur: float = 0.0

	def reinitialiser(self, ville_depart: int) -> None:
		# Remet la fourmi à zéro pour une nouvelle itération en partant d'une ville donnée
		self.trajet = [ville_depart]
		self.longueur = 0.0

	def construire_trajet(self, graphe: GrapheTSP, strategie: StrategieChoixVille, alpha: float, beta: float) -> None:
		# Fait parcourir à la fourmi toutes les villes une par une selon la stratégie fournie
		villes_non_visitees: list[int] = [ville.identifiant for ville in graphe.villes if ville.identifiant != self.trajet[0]]
		while villes_non_visitees:
			ville_courante: int = self.trajet[-1]
			prochaine_ville: int = strategie.choisir_prochaine_ville(graphe, ville_courante, villes_non_visitees, alpha, beta)
			self.trajet.append(prochaine_ville)
			villes_non_visitees.remove(prochaine_ville)
		self.longueur = graphe.longueur_trajet(self.trajet)


class ColonieACO:
	# Orchestre l'ensemble des itérations de l'algorithme de colonie de fourmis
	def __init__(self, graphe: GrapheTSP, nombre_fourmis: int, alpha: float, beta: float, evaporation: float, iterations: int) -> None:
		self.graphe: GrapheTSP = graphe
		self.nombre_fourmis: int = nombre_fourmis
		self.alpha: float = alpha
		self.beta: float = beta
		self.evaporation: float = evaporation
		self.iterations: int = iterations
		self.strategie: StrategieChoixVille = StrategieProbabiliste()
		self.meilleur_trajet: Optional[list[int]] = None
		self.meilleure_longueur: float = float("inf")
		self.historique_longueurs: list[float] = []

	def _deposer_pheromones(self, fourmis: list[Fourmi]) -> None:
		# Évapore les phéromones existantes puis dépose de nouvelles traces selon la qualité des trajets
		self.graphe.pheromones *= (1.0 - self.evaporation)
		for fourmi in fourmis:
			depot: float = 1.0 / fourmi.longueur
			for indice in range(len(fourmi.trajet)):
				ville_actuelle: int = fourmi.trajet[indice]
				ville_suivante: int = fourmi.trajet[(indice + 1) % len(fourmi.trajet)]
				self.graphe.pheromones[ville_actuelle][ville_suivante] += depot
				self.graphe.pheromones[ville_suivante][ville_actuelle] += depot

	def executer_iteration(self) -> list[Fourmi]:
		# Exécute une itération complète : chaque fourmi construit un trajet, puis les phéromones sont mises à jour
		fourmis: list[Fourmi] = []
		for _ in range(self.nombre_fourmis):
			fourmi: Fourmi = Fourmi()
			ville_depart: int = random.randint(0, self.graphe.nombre_villes - 1)
			fourmi.reinitialiser(ville_depart)
			fourmi.construire_trajet(self.graphe, self.strategie, self.alpha, self.beta)
			fourmis.append(fourmi)
			if fourmi.longueur < self.meilleure_longueur:
				self.meilleure_longueur = fourmi.longueur
				self.meilleur_trajet = fourmi.trajet.copy()
		self._deposer_pheromones(fourmis)
		self.historique_longueurs.append(self.meilleure_longueur)
		return fourmis


class VisualiseurACO:
	# Gère l'affichage graphique en direct de la convergence de la colonie
	def __init__(self, colonie: ColonieACO) -> None:
		self.colonie: ColonieACO = colonie
		self.figure: Figure
		self.axe_carte: Axes
		self.axe_courbe: Axes
		self.figure, (self.axe_carte, self.axe_courbe) = plt.subplots(1, 2, figsize=(12, 5))
		self.iteration_actuelle: int = 0

	def _dessiner_carte(self) -> None:
		# Redessine les villes, le meilleur trajet courant et l'intensité des phéromones
		self.axe_carte.clear()
		xs: list[float] = [ville.x for ville in self.colonie.graphe.villes]
		ys: list[float] = [ville.y for ville in self.colonie.graphe.villes]
		self.axe_carte.scatter(xs, ys, c="black", zorder=3)
		if self.colonie.meilleur_trajet is not None:
			for indice in range(len(self.colonie.meilleur_trajet)):
				ville_a: Ville = self.colonie.graphe.villes[self.colonie.meilleur_trajet[indice]]
				ville_b: Ville = self.colonie.graphe.villes[self.colonie.meilleur_trajet[(indice + 1) % len(self.colonie.meilleur_trajet)]]
				self.axe_carte.plot([ville_a.x, ville_b.x], [ville_a.y, ville_b.y], c="crimson", linewidth=2, zorder=2)
		self.axe_carte.set_title(f"Meilleur trajet — itération {self.iteration_actuelle} — longueur {self.colonie.meilleure_longueur:.2f}")

	def _dessiner_courbe(self) -> None:
		# Redessine la courbe de convergence de la meilleure longueur au fil des itérations
		self.axe_courbe.clear()
		self.axe_courbe.plot(self.colonie.historique_longueurs, c="steelblue")
		self.axe_courbe.set_title("Convergence")
		self.axe_courbe.set_xlabel("Itération")
		self.axe_courbe.set_ylabel("Longueur du meilleur trajet")

	def _mettre_a_jour(self, frame: int) -> None:
		# Callback appelé à chaque frame de l'animation pour avancer l'algorithme d'une itération
		if self.iteration_actuelle >= self.colonie.iterations:
			return
		self.colonie.executer_iteration()
		self.iteration_actuelle += 1
		self._dessiner_carte()
		self._dessiner_courbe()

	def lancer(self) -> None:
		# Démarre l'animation matplotlib qui pilote l'exécution de la colonie
		animation: FuncAnimation = FuncAnimation(self.figure, self._mettre_a_jour, frames=self.colonie.iterations, interval=100, repeat=False)
		plt.tight_layout()
		plt.show()


def generer_villes_aleatoires(nombre: int, largeur: float, hauteur: float) -> list[Ville]:
	# Génère un ensemble de villes avec des coordonnées aléatoires dans une zone rectangulaire
	return [Ville(identifiant=i, x=random.uniform(0, largeur), y=random.uniform(0, hauteur)) for i in range(nombre)]


def construire_parser() -> argparse.ArgumentParser:
	# Construit le parseur d'arguments en ligne de commande avec tous les paramètres réglables
	parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Résolution du TSP par colonie de fourmis (ACO)")
	parser.add_argument("--villes", type=int, default=25, help="Nombre de villes générées aléatoirement")
	parser.add_argument("--fourmis", type=int, default=30, help="Nombre de fourmis par itération")
	parser.add_argument("--alpha", type=float, default=1.0, help="Poids de l'influence des phéromones")
	parser.add_argument("--beta", type=float, default=3.0, help="Poids de l'influence de la visibilité (1/distance)")
	parser.add_argument("--evaporation", type=float, default=0.5, help="Taux d'évaporation des phéromones (0 à 1)")
	parser.add_argument("--iterations", type=int, default=100, help="Nombre d'itérations de l'algorithme")
	parser.add_argument("--graine", type=int, default=None, help="Graine aléatoire pour reproduire un résultat")
	return parser


def menu_interactif() -> argparse.Namespace:
	# Propose un menu console reprenant tous les paramètres disponibles en CLI
	print("=== Configuration interactive ACO-TSP ===")
	villes: int = int(input("Nombre de villes [25] : ") or 25)
	fourmis: int = int(input("Nombre de fourmis [30] : ") or 30)
	alpha: float = float(input("Alpha (poids phéromones) [1.0] : ") or 1.0)
	beta: float = float(input("Beta (poids visibilité) [3.0] : ") or 3.0)
	evaporation: float = float(input("Taux d'évaporation [0.5] : ") or 0.5)
	iterations: int = int(input("Nombre d'itérations [100] : ") or 100)
	graine_entree: str = input("Graine aléatoire (vide pour aléatoire) : ")
	graine: Optional[int] = int(graine_entree) if graine_entree else None
	return argparse.Namespace(villes=villes, fourmis=fourmis, alpha=alpha, beta=beta, evaporation=evaporation, iterations=iterations, graine=graine)


def main() -> None:
	parser: argparse.ArgumentParser = construire_parser()
	if len(sys.argv) > 1:
		arguments: argparse.Namespace = parser.parse_args()
	else:
		arguments = menu_interactif()
	if arguments.graine is not None:
		random.seed(arguments.graine)
	villes: list[Ville] = generer_villes_aleatoires(arguments.villes, 100.0, 100.0)
	graphe: GrapheTSP = GrapheTSP(villes)
	colonie: ColonieACO = ColonieACO(graphe, arguments.fourmis, arguments.alpha, arguments.beta, arguments.evaporation, arguments.iterations)
	visualiseur: VisualiseurACO = VisualiseurACO(colonie)
	visualiseur.lancer()
	print(f"Meilleure longueur trouvée : {colonie.meilleure_longueur:.2f}")
	print(f"Meilleur trajet : {colonie.meilleur_trajet}")


if __name__ == "__main__":
	main()
