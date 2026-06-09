#!/bin/bash

# ============================================================
#  gestion_apps.sh — Gestionnaire d'applications Linux
#  Supporte : apt / dnf / yum / pacman / zypper / apk
#		   + snap / flatpak / appimage / pip / npm / cargo
# ============================================================

RED=		'\033[0;31m'
GREEN=		'\033[0;32m'
YELLOW=		'\033[1;33m'
BLUE=		'\033[0;34m'
CYAN=		'\033[0;36m'
MAGENTA=	'\033[0;35m'
BOLD=		'\033[1m'
DIM=		'\033[2m'
RESET=		'\033[0m'

# ── Détection ────────────────────────────────────────────────

detect_pkg_manager() {
	PM=""
	if   command -v apt	&>/dev/null;	then PM="apt"
	elif command -v dnf	&>/dev/null;	then PM="dnf"
	elif command -v yum	&>/dev/null;	then PM="yum"
	elif command -v pacman &>/dev/null;	then PM="pacman"
	elif command -v zypper &>/dev/null;	then PM="zypper"
	elif command -v apk	&>/dev/null;	then PM="apk"
	fi
}

HAS_SNAP=false;		command -v snap	&>/dev/null && HAS_SNAP=true
HAS_FLATPAK=false;	command -v flatpak &>/dev/null && HAS_FLATPAK=true
HAS_PIP=false;		command -v pip3	&>/dev/null && HAS_PIP=true
HAS_NPM=false;		command -v npm	 &>/dev/null && HAS_NPM=true
HAS_CARGO=false;	command -v cargo   &>/dev/null && HAS_CARGO=true

find_appimages() {
	local dirs=("$HOME" "$HOME/Applications" "$HOME/AppImages" "/opt" "/usr/local/bin")
	find "${dirs[@]}" -maxdepth 3 -name "*.AppImage" 2>/dev/null
}
HAS_APPIMAGE=false
[[ -n "$(find_appimages)" ]] && HAS_APPIMAGE=true

# ── Utilitaires ──────────────────────────────────────────────

banner() {
	echo -e "${BLUE}${BOLD}"
	echo "  ╔════════════════════════════════════════════╗"
	echo "  ║	   Gestionnaire d'Applications Linux	 ║"
	echo "  ╚════════════════════════════════════════════╝"
	echo -e "${RESET}"
}

afficher_gestionnaires() {
	echo -e "  ${DIM}Gestionnaires détectés :${RESET}"
	[[ -n "$PM" ]]	&& echo -e "  ${GREEN}✔${RESET} Système   : ${BOLD}$PM${RESET}"
	$HAS_SNAP		&& echo -e "  ${GREEN}✔${RESET} Snap"
	$HAS_FLATPAK	&& echo -e "  ${GREEN}✔${RESET} Flatpak"
	$HAS_APPIMAGE	&& echo -e "  ${GREEN}✔${RESET} AppImage"
	$HAS_PIP		&& echo -e "  ${GREEN}✔${RESET} pip (Python)"
	$HAS_NPM		&& echo -e "  ${GREEN}✔${RESET} npm (Node.js)"
	$HAS_CARGO		&& echo -e "  ${GREEN}✔${RESET} cargo (Rust)"
	echo
}

compter_total() {
	local total=0
	if [[ -n "$PM" ]]; then
		case $PM in
			apt)		total=$(dpkg-query -W -f='${Status}\n' 2>/dev/null | grep -c "install ok installed") ;;
			dnf|yum)	total=$(rpm -qa 2>/dev/null | wc -l) ;;
			pacman)		total=$(pacman -Q 2>/dev/null | wc -l) ;;
			zypper)		total=$(zypper se --installed-only 2>/dev/null | tail -n +5 | wc -l) ;;
			apk)		total=$(apk info 2>/dev/null | wc -l) ;;
		esac
	fi
	local snap_count=0;		$HAS_SNAP		&& snap_count=$(snap list 2>/dev/null | tail -n +2 | wc -l)
	local flat_count=0;		$HAS_FLATPAK	&& flat_count=$(flatpak list 2>/dev/null | wc -l)
	local ai_count=0;		$HAS_APPIMAGE	&& ai_count=$(find_appimages | wc -l)
	local pip_count=0;		$HAS_PIP		&& pip_count=$(pip3 list 2>/dev/null | tail -n +3 | wc -l)
	local npm_count=0;		$HAS_NPM		&& npm_count=$(npm list -g --depth=0 2>/dev/null | tail -n +2 | wc -l)
	local cargo_count=0;	$HAS_CARGO		&& cargo_count=$(cargo install --list 2>/dev/null | grep -c "^[a-z]")

	echo -e "  ${GREEN}Paquets système   : ${BOLD}$total${RESET}"
	$HAS_SNAP		&& echo -e "  ${GREEN}Snaps				: ${BOLD}$snap_count${RESET}"
	$HAS_FLATPAK	&& echo -e "  ${GREEN}Flatpaks			: ${BOLD}$flat_count${RESET}"
	$HAS_APPIMAGE	&& echo -e "  ${GREEN}AppImages			: ${BOLD}$ai_count${RESET}"
	$HAS_PIP		&& echo -e "  ${GREEN}Paquets pip		: ${BOLD}$pip_count${RESET}"
	$HAS_NPM		&& echo -e "  ${GREEN}Paquets npm -g	: ${BOLD}$npm_count${RESET}"
	$HAS_CARGO		&& echo -e "  ${GREEN}Binaires cargo	: ${BOLD}$cargo_count${RESET}"
}

pause() { echo; read -rp "  Appuyez sur [Entrée] pour continuer..."; }
section() { echo -e "\n  ${MAGENTA}${BOLD}── $1 ──${RESET}\n"; }

# ── Lister ───────────────────────────────────────────────────

lister_systeme() {
	[[ -z "$PM" ]] && { echo -e "  ${RED}Aucun gestionnaire système détecté.${RESET}"; return; }
	section "Paquets système ($PM)"
	case $PM in
		apt)	 dpkg-query -W -f='${Package}\t${Version}\n' 2>/dev/null | awk '{printf "  %-40s %s\n", $1, $2}' | sort ;;
		dnf|yum) rpm -qa --qf "  %-40{NAME} %{VERSION}\n" 2>/dev/null | sort ;;
		pacman)  pacman -Q 2>/dev/null | awk '{printf "  %-40s %s\n", $1, $2}' ;;
		zypper)  zypper se --installed-only 2>/dev/null | tail -n +5 | awk '{printf "  %-40s %s\n", $2, $4}' ;;
		apk)	 apk info -v 2>/dev/null | sort ;;
	esac
}

lister_snap() {
	$HAS_SNAP || { echo -e "  ${DIM}Snap non disponible.${RESET}"; return; }
	section "Snaps installés"
	snap list 2>/dev/null | tail -n +2 \
		| awk '{printf "  %-35s %-15s %s\n", $1, $2, $NF}'
}

lister_flatpak() {
	$HAS_FLATPAK || { echo -e "  ${DIM}Flatpak non disponible.${RESET}"; return; }
	section "Flatpaks installés"
	flatpak list --columns=application,name,version,installation 2>/dev/null \
		| awk '{printf "  %-50s %-20s %s\n", $1, $2, $3}'
}

lister_appimage() {
	$HAS_APPIMAGE || { echo -e "  ${DIM}Aucune AppImage trouvée.${RESET}"; return; }
	section "AppImages détectées"
	find_appimages | while read -r f; do
		local size
		size=$(du -sh "$f" 2>/dev/null | cut -f1)
		printf "  %-60s %s\n" "$f" "$size"
	done
}

lister_pip() {
	$HAS_PIP || { echo -e "  ${DIM}pip non disponible.${RESET}"; return; }
	section "Paquets pip (Python)"
	pip3 list 2>/dev/null | tail -n +3 \
		| awk '{printf "  %-35s %s\n", $1, $2}'
}

lister_npm() {
	$HAS_NPM || { echo -e "  ${DIM}npm non disponible.${RESET}"; return; }
	section "Paquets npm globaux"
	npm list -g --depth=0 2>/dev/null | tail -n +2 \
		| sed 's/[├└─]//g' | awk '{printf "  %s\n", $NF}'
}

lister_cargo() {
	$HAS_CARGO || { echo -e "  ${DIM}cargo non disponible.${RESET}"; return; }
	section "Binaires Rust (cargo)"
	cargo install --list 2>/dev/null | grep -E "^[a-z]" \
		| awk '{printf "  %s\n", $0}'
}

lister_tout() {
	{
		lister_systeme
		lister_snap
		lister_flatpak
		lister_appimage
		lister_pip
		lister_npm
		lister_cargo
	} | less -R
}

# ── Mises à jour ─────────────────────────────────────────────

verifier_mises_a_jour() {
	echo -e "${YELLOW}🔄 Vérification des mises à jour...${RESET}\n"

	if [[ -n "$PM" ]]; then
		section "Système ($PM)"
		case $PM in
			apt)
				sudo apt update -qq 2>/dev/null
				local n; n=$(apt list --upgradable 2>/dev/null | grep -c upgradable)
				echo -e "  ${GREEN}$n paquet(s) à mettre à jour :${RESET}"
				apt list --upgradable 2>/dev/null | grep upgradable | awk -F'/' '{printf "  %-35s %s\n", $1, $2}' ;;
			dnf|yum) sudo $PM check-update 2>/dev/null ;;
			pacman)  sudo pacman -Sy &>/dev/null; pacman -Qu 2>/dev/null ;;
			zypper)  sudo zypper refresh -q 2>/dev/null; zypper list-updates 2>/dev/null ;;
			apk)	 sudo apk update -q 2>/dev/null; apk list --upgradable 2>/dev/null ;;
		esac
	fi

	if $HAS_SNAP; then
		section "Snap"
		snap refresh --list 2>/dev/null || echo -e "  ${GREEN}Tout est à jour.${RESET}"
	fi

	if $HAS_FLATPAK; then
		section "Flatpak"
		flatpak remote-ls --updates 2>/dev/null || echo -e "  ${GREEN}Tout est à jour.${RESET}"
	fi

	if $HAS_PIP; then
		section "pip (Python)"
		local outdated
		outdated=$(pip3 list --outdated 2>/dev/null | tail -n +3)
		if [[ -n "$outdated" ]]; then
			echo "$outdated" | awk '{printf "  %-30s actuel: %-10s dispo: %s\n", $1, $2, $3}'
		else
			echo -e "  ${GREEN}Tout est à jour.${RESET}"
		fi
	fi

	if $HAS_NPM; then
		section "npm (global)"
		npm outdated -g --depth=0 2>/dev/null || echo -e "  ${GREEN}Tout est à jour.${RESET}"
	fi
}

mettre_a_jour_tout() {
	echo -e "${YELLOW}Mise à jour complète du système...${RESET}\n"
	echo -e "${RED}${BOLD}Des droits sudo peuvent être requis.${RESET}\n"
	echo -e "  Gestionnaires qui seront mis à jour :"
	[[ -n "$PM" ]]	&& echo -e "  ${CYAN}•${RESET} Système ($PM)"
	$HAS_SNAP		&& echo -e "  ${CYAN}•${RESET} Snap"
	$HAS_FLATPAK	&& echo -e "  ${CYAN}•${RESET} Flatpak"
	$HAS_PIP		&& echo -e "  ${CYAN}•${RESET} pip"
	$HAS_NPM		&& echo -e "  ${CYAN}•${RESET} npm"
	echo
	read -rp "  Confirmer la mise à jour globale ? [o/N] : " confirm
	[[ "$confirm" =~ ^[oOyY]$ ]] || { echo "  Annulé."; return; }

	if [[ -n "$PM" ]]; then
		section "Mise à jour système ($PM)"
		case $PM in
			apt)	sudo apt update && sudo apt upgrade -y ;;
			dnf)	sudo dnf upgrade -y ;;
			yum)	sudo yum update -y ;;
			pacman) sudo pacman -Syu ;;
			zypper) sudo zypper update -y ;;
			apk)	sudo apk upgrade ;;
		esac
	fi
	$HAS_SNAP	&& { section "Snap";	sudo snap refresh; }
	$HAS_FLATPAK && { section "Flatpak"; flatpak update -y; }
	$HAS_PIP	 && { section "pip";
		pip3 list --outdated 2>/dev/null | tail -n +3 | awk '{print $1}' \
			| xargs -r pip3 install --upgrade 2>/dev/null
		echo -e "  ${GREEN}pip à jour.${RESET}"; }
	$HAS_NPM	 && { section "npm"; npm update -g 2>/dev/null
		echo -e "  ${GREEN}npm à jour.${RESET}"; }

	echo -e "\n  ${GREEN}${BOLD}Toutes les mises à jour sont terminées.${RESET}"
}

mettre_a_jour_selectif() {
	echo -e "${YELLOW}⬆️  Mise à jour sélective${RESET}\n"
	echo -e "  Choisissez le gestionnaire :\n"
	local i=1; local opts=()
	[[ -n "$PM" ]]	&& { echo -e "  ${CYAN}$i)${RESET} Système ($PM)"; opts+=("systeme"); ((i++)); }
	$HAS_SNAP		&& { echo -e "  ${CYAN}$i)${RESET} Snap";		  opts+=("snap");	((i++)); }
	$HAS_FLATPAK	&& { echo -e "  ${CYAN}$i)${RESET} Flatpak";	   opts+=("flatpak"); ((i++)); }
	$HAS_PIP		&& { echo -e "  ${CYAN}$i)${RESET} pip";		   opts+=("pip");	 ((i++)); }
	$HAS_NPM		&& { echo -e "  ${CYAN}$i)${RESET} npm";		   opts+=("npm");	 ((i++)); }
	$HAS_CARGO		&& { echo -e "  ${CYAN}$i)${RESET} cargo";		 opts+=("cargo");   ((i++)); }
	echo -e "  ${CYAN}0)${RESET} Retour"; echo
	read -rp "  Votre choix : " sel
	[[ "$sel" == "0" ]] && return
	local idx=$(( sel - 1 ))
	local cible="${opts[$idx]:-}"
	case "$cible" in
		systeme)
			read -rp "  Confirmer ? [o/n] : " c; [[ "$c" =~ ^[oOyY]$ ]] || return
			case $PM in
				apt)	sudo apt update && sudo apt upgrade -y ;;
				dnf)	sudo dnf upgrade -y ;;
				yum)	sudo yum update -y ;;
				pacman) sudo pacman -Syu ;;
				zypper) sudo zypper update -y ;;
				apk)	sudo apk upgrade ;;
			esac ;;
		snap)	sudo snap refresh ;;
		flatpak) flatpak update -y ;;
		pip)	 pip3 list --outdated 2>/dev/null | tail -n +3 | awk '{print $1}' \
					 | xargs -r pip3 install --upgrade ;;
		npm)	 npm update -g ;;
		cargo)   echo -e "  ${YELLOW}Cargo ne met pas à jour automatiquement.${RESET}"
				 echo -e "  ${DIM}Réinstallez manuellement : cargo install <paquet>${RESET}" ;;
		*)	   echo -e "  ${RED}Choix invalide.${RESET}" ;;
	esac
	echo -e "\n  ${GREEN}✅ Terminé.${RESET}"
}

# ── Recherche / Install / Suppression ────────────────────────

choisir_gestionnaire() {
	local i=1; local opts=()
	[[ -n "$PM" ]] && { echo -e "  ${CYAN}$i)${RESET} Système ($PM)"; opts+=("systeme"); ((i++)); }
	$HAS_SNAP	  && { echo -e "  ${CYAN}$i)${RESET} Snap";		  opts+=("snap");	((i++)); }
	$HAS_FLATPAK   && { echo -e "  ${CYAN}$i)${RESET} Flatpak";	   opts+=("flatpak"); ((i++)); }
	$HAS_PIP	   && { echo -e "  ${CYAN}$i)${RESET} pip";		   opts+=("pip");	 ((i++)); }
	$HAS_NPM	   && { echo -e "  ${CYAN}$i)${RESET} npm (global)";  opts+=("npm");	 ((i++)); }
	$HAS_CARGO	 && { echo -e "  ${CYAN}$i)${RESET} cargo";		 opts+=("cargo");   ((i++)); }
	echo; read -rp "  Choix : " sel; echo
	local idx=$(( sel - 1 ))
	CHOSEN="${opts[$idx]:-}"
}

chercher_app() {
	read -rp "  Nom à rechercher : " pkg
	echo -e "\n  Dans quel gestionnaire ?\n"
	choisir_gestionnaire
	case "$CHOSEN" in
		systeme) case $PM in
					 apt)	 apt-cache search "$pkg" 2>/dev/null | awk '{printf "  %-35s %s\n",$1,substr($0,index($0,$2))}' | less -R ;;
					 dnf|yum) $PM search "$pkg" 2>/dev/null | less -R ;;
					 pacman)  pacman -Ss "$pkg" 2>/dev/null | less -R ;;
					 zypper)  zypper search "$pkg" 2>/dev/null | less -R ;;
					 apk)	 apk search "$pkg" 2>/dev/null | less -R ;;
				 esac ;;
		snap)	snap find "$pkg" 2>/dev/null | less -R ;;
		flatpak) flatpak search "$pkg" 2>/dev/null | less -R ;;
		pip)	 pip3 index versions "$pkg" 2>/dev/null | less -R ;;
		npm)	 npm search "$pkg" 2>/dev/null | less -R ;;
		*)	   echo -e "  ${RED}Choix invalide.${RESET}" ;;
	esac
}

installer_app() {
	read -rp "  Nom du paquet à installer : " pkg
	echo -e "\n  Via quel gestionnaire ?\n"
	choisir_gestionnaire
	case "$CHOSEN" in
		systeme) case $PM in
					 apt)	 sudo apt install -y "$pkg" ;;
					 dnf|yum) sudo $PM install -y "$pkg" ;;
					 pacman)  sudo pacman -S "$pkg" ;;
					 zypper)  sudo zypper install -y "$pkg" ;;
					 apk)	 sudo apk add "$pkg" ;;
				 esac ;;
		snap)	sudo snap install "$pkg" ;;
		flatpak) flatpak install -y "$pkg" ;;
		pip)	 pip3 install "$pkg" ;;
		npm)	 sudo npm install -g "$pkg" ;;
		cargo)   cargo install "$pkg" ;;
		*)	   echo -e "  ${RED}Choix invalide.${RESET}" ;;
	esac
}

supprimer_app() {
	read -rp "  Nom du paquet à supprimer : " pkg
	echo -e "\n  Via quel gestionnaire ?\n"
	choisir_gestionnaire
	echo -e "  ${RED}⚠️  Suppression de : ${BOLD}$pkg${RESET}"
	read -rp "  Confirmer ? [o/N] : " c
	[[ "$c" =~ ^[oOyY]$ ]] || { echo "  Annulé."; return; }
	case "$CHOSEN" in
		systeme) case $PM in
					 apt)	 sudo apt remove -y "$pkg" ;;
					 dnf|yum) sudo $PM remove -y "$pkg" ;;
					 pacman)  sudo pacman -R "$pkg" ;;
					 zypper)  sudo zypper remove -y "$pkg" ;;
					 apk)	 sudo apk del "$pkg" ;;
				 esac ;;
		snap)	sudo snap remove "$pkg" ;;
		flatpak) flatpak uninstall -y "$pkg" ;;
		pip)	 pip3 uninstall -y "$pkg" ;;
		npm)	 sudo npm uninstall -g "$pkg" ;;
		cargo)   cargo uninstall "$pkg" ;;
		*)	   echo -e "  ${RED}Choix invalide.${RESET}" ;;
	esac
}

# ── Export ───────────────────────────────────────────────────

exporter_liste() {
	local fichier="apps_$(hostname)_$(date +%Y%m%d_%H%M%S).txt"
	echo -e "${YELLOW}💾 Export vers ${BOLD}$fichier${RESET}...\n"
	{
		echo "=========================================="
		echo "  Applications installées sur $(hostname)"
		echo "  Date : $(date)"
		echo "=========================================="

		if [[ -n "$PM" ]]; then
			echo -e "\n── Système ($PM) ──────────────────────"
			case $PM in
				apt)	 dpkg-query -W -f='${Package}\t${Version}\n' 2>/dev/null | sort ;;
				dnf|yum) rpm -qa --qf "%{NAME}\t%{VERSION}\n" 2>/dev/null | sort ;;
				pacman)  pacman -Q 2>/dev/null | sort ;;
				zypper)  zypper se --installed-only 2>/dev/null | tail -n +5 | awk '{print $2"\t"$4}' ;;
				apk)	 apk info -v 2>/dev/null | sort ;;
			esac
		fi
		$HAS_SNAP	 && { echo -e "\n── Snap ───────────────────────────────"; snap list 2>/dev/null | tail -n +2; }
		$HAS_FLATPAK  && { echo -e "\n── Flatpak ────────────────────────────"; flatpak list 2>/dev/null; }
		$HAS_APPIMAGE && { echo -e "\n── AppImages ──────────────────────────"; find_appimages; }
		$HAS_PIP	  && { echo -e "\n── pip (Python) ───────────────────────"; pip3 list 2>/dev/null | tail -n +3; }
		$HAS_NPM	  && { echo -e "\n── npm global ─────────────────────────"; npm list -g --depth=0 2>/dev/null | tail -n +2; }
		$HAS_CARGO	&& { echo -e "\n── cargo (Rust) ───────────────────────"; cargo install --list 2>/dev/null; }
	} > "$fichier"
	echo -e "  ${GREEN}✅ Exporté : ${BOLD}$(pwd)/$fichier${RESET}"
}

# ── Menu principal ───────────────────────────────────────────

menu() {
	detect_pkg_manager
	while true; do
		clear
		banner
		afficher_gestionnaires
		compter_total
		echo
		echo -e "  ${BOLD}Que souhaitez-vous faire ?${RESET}\n"
		echo -e "  ${CYAN}1)${RESET} 📋 Lister toutes les applications (tous gestionnaires)"
		echo -e "  ${CYAN}2)${RESET} 🔍 Rechercher une application"
		echo -e "  ${CYAN}3)${RESET} 🔄 Vérifier les mises à jour (tous gestionnaires)"
		echo -e "  ${CYAN}4)${RESET} ⬆️  Mettre à jour TOUT le système"
		echo -e "  ${CYAN}5)${RESET} 🎯 Mettre à jour un gestionnaire spécifique"
		echo -e "  ${CYAN}6)${RESET} 📥 Installer une application"
		echo -e "  ${CYAN}7)${RESET} 🗑️  Supprimer une application"
		echo -e "  ${CYAN}8)${RESET} 💾 Exporter la liste complète en fichier texte"
		echo -e "  ${CYAN}0)${RESET} 🚪 Quitter"
		echo
		read -rp "  Votre choix : " choix
		echo
		case $choix in
			1) lister_tout ;;
			2) chercher_app			 ; pause ;;
			3) verifier_mises_a_jour | less -R ; pause ;;
			4) mettre_a_jour_tout	   ; pause ;;
			5) mettre_a_jour_selectif   ; pause ;;
			6) installer_app			; pause ;;
			7) supprimer_app			; pause ;;
			8) exporter_liste		   ; pause ;;
			0) echo -e "  ${GREEN}À bientôt ! 👋${RESET}\n"; exit 0 ;;
			*) echo -e "  ${RED}Choix invalide.${RESET}"; sleep 1 ;;
		esac
	done
}

menu
