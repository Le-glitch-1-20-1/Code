#!/usr/bin/env python3
"""
Calculateur de droprate SkyBlock — version API
Récupère automatiquement Magic Find, Pet Luck et pet équipé
via l'API Hypixel, puis calcule ton droprate.
"""

import requests
import math

BASE_URL = "https://api.hypixel.net/v2"

# ──────────────────────────────────────────────────────
# API
# ──────────────────────────────────────────────────────

class HypixelAPI:
	def __init__(self, api_key: str):
		self.session = requests.Session()
		self.session.headers.update({"API-Key": api_key})

	def _get(self, endpoint: str, params: dict = None) -> dict:
		r = self.session.get(f"{BASE_URL}/{endpoint}", params=params)
		if r.status_code == 403:
			raise PermissionError("❌ Clé API invalide.")
		if r.status_code == 429:
			raise ConnectionError("⏳ Rate limit atteint.")
		r.raise_for_status()
		return r.json()

	def get_skyblock_profiles(self, uuid: str) -> dict:
		return self._get("skyblock/profiles", {"uuid": uuid})


def uuid_from_username(username: str) -> str:
	r = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
	if r.status_code == 200:
		return r.json()["id"]
	raise ValueError(f"Joueur '{username}' introuvable.")

def select_best_profile(profiles: list) -> dict:
	selected = [p for p in profiles if p.get("selected")]
	return selected[0] if selected else profiles[0]

def get_member(profile: dict, uuid: str) -> dict | None:
	members = profile.get("members", {})
	uuid_clean = uuid.replace("-", "")
	return members.get(uuid_clean) or next(iter(members.values()), None)


def fetch_player_stats(api_key: str, username: str) -> dict:
	"""
	Retourne un dict avec :
	  mf_without_pet  : Magic Find sans le pet
	  pl_without_pet  : Pet Luck sans le pet
	  mf_pet          : Magic Find donnée par le pet équipé
	  pl_pet          : Pet Luck donnée par le pet équipé
	  pet_name        : nom du pet équipé (ou None)
	  total_mf        : Magic Find totale
	  total_pl        : Pet Luck totale
	"""
	api = HypixelAPI(api_key)
	uuid = uuid_from_username(username)
	profiles_data = api.get_skyblock_profiles(uuid)

	profiles = profiles_data.get("profiles", [])
	if not profiles:
		return None

	profile = select_best_profile(profiles)
	member  = get_member(profile, uuid)
	if not member:
		return None

	player_stats = member.get("player_stats", {})
	raw_stats    = member.get("stats", {})

	total_mf = (player_stats.get("items", {}).get("magic_find", 0)
				or raw_stats.get("magic_find", 0))
	total_pl = (player_stats.get("items", {}).get("pet_luck", 0)
				or raw_stats.get("pet_luck", 0))

	pets_data = member.get("pets_data", {}) or member.get("pets", {})
	pet_list  = pets_data.get("pets", []) if isinstance(pets_data, dict) else (pets_data or [])
	equipped  = next((p for p in pet_list if p.get("active")), None)

	pet_name = None
	pet_mf   = 0
	pet_pl   = 0

	if equipped:
		pet_name  = equipped.get("type", "?").replace("_", " ").title()
		pet_stats = equipped.get("stats", {})
		pet_mf    = pet_stats.get("magic_find", 0)
		pet_pl    = pet_stats.get("pet_luck",   0)

	return {
		"mf_without_pet": max(0, total_mf - pet_mf),
		"pl_without_pet": max(0, total_pl - pet_pl),
		"mf_pet":         pet_mf,
		"pl_pet":         pet_pl,
		"pet_name":       pet_name,
		"total_mf":       total_mf,
		"total_pl":       total_pl,
	}


# ──────────────────────────────────────────────────────
# Helpers UI
# ──────────────────────────────────────────────────────

def ask(prompt: str, choices: list[str] | None = None) -> str:
	while True:
		val = input(prompt).strip().lower()
		if choices is None or val in choices:
			return val
		print(f"  ⚠️  Réponds par : {' / '.join(choices)}")

def ask_float(prompt: str) -> float:
	while True:
		try:
			return float(input(prompt).strip())
		except ValueError:
			print("  ⚠️  Entre un nombre valide.")

def ask_int(prompt: str) -> int:
	while True:
		try:
			return int(input(prompt).strip())
		except ValueError:
			print("  ⚠️  Entre un entier valide.")

def sep(char="─", n=54):
	print(char * n)


# ──────────────────────────────────────────────────────
# Calcul Chimera
# ──────────────────────────────────────────────────────

def get_chimera_multiplier(has_daedalus: bool) -> float:
	base = 2.0 if has_daedalus else 1.0
	has_chim = ask("As-tu Chimera sur cette arme ? (o/n) : ", ["o", "n"])
	if has_chim == "o":
		tier = ask_int("Tier de Chimera (1-5) : ")
		return base + tier * 0.2
	return base


# ──────────────────────────────────────────────────────
# Calcul MF/PL effectifs
# ──────────────────────────────────────────────────────

def compute_mf_pl(auto_stats: dict | None, item_type: str) -> tuple[float, float]:
	"""
	Retourne (mf_effectif, pl_effectif).
	Avec l'API : seules les questions sur l'arme (Daedalus + Chimera) sont posées.
	Sans l'API  : on demande aussi les valeurs MF/PL manuellement.
	"""
	has_dae = ask("\nAs-tu une Daedalus Axe ? (o/n) : ", ["o", "n"]) == "o"
	chim    = get_chimera_multiplier(has_dae)

	if auto_stats:
		# ── Toutes les stats viennent de l'API, aucune question MF/PL ──
		mf_pet    = auto_stats["mf_pet"]
		pl_pet    = auto_stats["pl_pet"]
		mf_no_pet = auto_stats["mf_without_pet"]
		pl_no_pet = auto_stats["pl_without_pet"]

		mf_pet_eff = mf_pet * chim
		pl_pet_eff = pl_pet * chim
		mft = mf_no_pet + mf_pet_eff
		plt = pl_no_pet + pl_pet_eff

		print(f"\n  📊 Stats récupérées via l'API :")
		print(f"     Magic Find (sans pet) : {mf_no_pet}")
		print(f"     Magic Find (pet ×{chim:.1f}) : {mf_pet_eff:.1f}")
		print(f"     ➜ Magic Find effectif  : {mft:.1f}")
		if item_type == "p":
			print(f"     Pet Luck  (sans pet)   : {pl_no_pet}")
			print(f"     Pet Luck  (pet ×{chim:.1f})  : {pl_pet_eff:.1f}")
			print(f"     ➜ Pet Luck effectif    : {plt:.1f}")
	else:
		# ── Mode manuel ──
		if chim > 1:
			mf_pet     = ask_float("Magic Find donnée par ton pet : ")
			mf_pet_eff = mf_pet * chim
			mf_base    = ask_float("Magic Find SANS ton pet : ")
			mft        = mf_base + mf_pet_eff
		else:
			mft = ask_float("Magic Find totale (pet inclus) : ")

		if item_type == "p":
			if chim > 1:
				pl_pet     = ask_float("Pet Luck donnée par ton pet : ")
				pl_pet_eff = pl_pet * chim
				pl_base    = ask_float("Pet Luck SANS ton pet : ")
				plt        = pl_base + pl_pet_eff
			else:
				plt = ask_float("Pet Luck totale (pet inclus) : ")
		else:
			plt = 0.0

	return mft, plt


# ──────────────────────────────────────────────────────
# Calcul du droprate final
# ──────────────────────────────────────────────────────

def calc_pet(mft: float, plt: float) -> float:
	looting = ask_int("Tier de l'enchantement Looting (0-6) : ")
	dr      = ask_float("Droprate de base du pet (% — vérifie le wiki) : ")
	return dr * (1 + (mft + plt) / 100) * (looting * 0.15 + 1)

def calc_armor(mft: float) -> float:
	looting = ask_int("Tier de l'enchantement Looting (0-6) : ")
	chance  = ask_int("Tier de l'enchantement Chance (0-5) : ")
	dr      = ask_float("Droprate de base de l'armure (% — vérifie le wiki) : ")
	return dr * (1 + mft / 100) * (looting * 0.15 + 1) * (chance * 0.05 + 1)

def calc_item(mft: float) -> float:
	looting = ask_int("Tier de l'enchantement Looting (0-6) : ")
	dr      = ask_float("Droprate de base de l'item en % (vérifie le wiki) : ")
	dr /= 100
	return dr * (1 + mft / 100) * (looting * 0.15 + 1)


# ──────────────────────────────────────────────────────
# Point d'entrée
# ──────────────────────────────────────────────────────

def main():
	sep("═")
	print("  💧 CALCULATEUR DE DROPRATE — Hypixel SkyBlock")
	sep("═")

	# ── Connexion API (optionnelle) ──
	auto_stats = None
	use_api = ask("\nVeux-tu récupérer tes stats automatiquement via l'API ? (o/n) : ", ["o", "n"])
	if use_api == "o":
		api_key  = input("Clé API Hypixel : ").strip() or "d3ff2777-05e1-4c0c-9e27-fbd69c323765"
		username = input("Pseudo Minecraft : ").strip()
		print("\n⏳ Récupération en cours...")
		try:
			auto_stats = fetch_player_stats(api_key, username)
			if auto_stats:
				pet = auto_stats.get("pet_name") or "Aucun"
				print(f"  ✅ Stats chargées ! Pet équipé : {pet}")
				print(f"     MF total : {auto_stats['total_mf']}  |  PL total : {auto_stats['total_pl']}")
			else:
				print("  ⚠️  Données introuvables — passage en mode manuel.")
		except Exception as e:
			print(f"  ⚠️  Erreur API : {e} — passage en mode manuel.")

	# ── Type d'item ──
	sep()
	print("\nType d'item :")
	print("  p  → Pet")
	print("  a  → Armure")
	print("  i  → Item")
	item_type = ask("\nTon choix (p/a/i) : ", ["p", "a", "i"])

	# ── Magic Find & Pet Luck ──
	sep()
	mft, plt = compute_mf_pl(auto_stats, item_type)

	# ── Calcul selon le type ──
	sep()
	print("\n📦 Infos sur l'item :")
	if item_type == "p":
		droprate = calc_pet(mft, plt)
	elif item_type == "a":
		droprate = calc_armor(mft)
	else:
		droprate = calc_item(mft)

	# ── Résultat ──
	sep("═")
	print(f"\n  🎯 Droprate calculé  : {droprate:.6f} %")
	if droprate > 0:
		tries = 100 / droprate
		print(f"  🎲 Kills nécessaires : ~{tries:,.0f} en moyenne")
		print(f"\n  📈 Probabilités d'obtenir l'item :")
		for pct in [25, 50, 75, 90, 99]:
			n = math.ceil(math.log(1 - pct / 100) / math.log(1 - droprate / 100))
			print(f"     {pct:>3}% de chance → {n:>10,} kills")
	print()
	print("  Bonne chance ! 🍀")
	sep("═")


if __name__ == "__main__":
	main()
