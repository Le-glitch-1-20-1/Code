#!/bin/bash
# Exit code of a pipeline is the last command that failed, not just the last command
set -o pipefail

# Program version, mirrors the VERSION constant of the Python interface
VERSION="2.0.0"

# Color codes used for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'
HIDE_CURSOR='\033[?25l'
SHOW_CURSOR='\033[?25h'

# Detect which optional package managers are available on this system
HAS_SNAP=false;		command -v snap &>/dev/null && HAS_SNAP=true
HAS_FLATPAK=false;	command -v flatpak &>/dev/null && HAS_FLATPAK=true
HAS_PIP=false;		command -v pip3 &>/dev/null && HAS_PIP=true
HAS_NPM=false;		command -v npm &>/dev/null && HAS_NPM=true
HAS_CARGO=false;	command -v cargo &>/dev/null && HAS_CARGO=true
HAS_APPIMAGE=true
# CLI flags and option variables, populated by argument parsing
AUTO_YES=false
NONINTERACTIVE=false
DO_LIST=false; LIST_MANAGER=""
DO_CHECK=false
DO_UPDATE_ALL=false
UPDATE_MANAGER=""
SEARCH_PKG=""
INSTALL_PKG=""
REMOVE_PKG=""
ACTION_MANAGER=""
DO_EXPORT=false
SHOW_HELP=false
BAD_ARGS=false

# Print a short message and exit cleanly on Ctrl+C
trap 'printf "${SHOW_CURSOR}"; echo -e "${RESET}\n  ${YELLOW}Interrupted.${RESET}"; exit 130' INT
trap 'printf "${SHOW_CURSOR}"' EXIT

# Detect the system package manager and store it in PM
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

# Look for AppImage files in common locations
find_appimages() {
	local dirs=("$HOME" "$HOME/Applications" "$HOME/AppImages" "/opt" "/usr/local/bin")
	find "${dirs[@]}" -maxdepth 3 -name "*.AppImage" 2>/dev/null
}

# Current terminal width, with a sane fallback
term_width() {
	tput cols 2>/dev/null || echo 80
}

# Full-width titled separator, mirroring rich.rule.Rule
hr() {
	local label="${1:-}"
	local width; width=$(term_width)
	if [[ -n "$label" ]]; then
		local head="── ${label} "
		local pad=$(( width - ${#head} ))
		(( pad < 0 )) && pad=0
		echo -e "  ${MAGENTA}${BOLD}${head}$(printf '─%.0s' $(seq 1 "$pad") 2>/dev/null)${RESET}"
	else
		echo -e "  ${MAGENTA}$(printf '─%.0s' $(seq 1 "$width") 2>/dev/null)${RESET}"
	fi
}

# Render a bordered ASCII table, mirroring rich.table.Table.
# Usage: print_table "Col1\tCol2\t..." rows_array_name
# Rows are TAB-separated strings; rows_array_name is the *name* of an array variable.
print_table() {
	local header="$1"; local -n _rows="$2"
	local -a headers; IFS=$'\t' read -ra headers <<< "$header"
	local ncol=${#headers[@]}
	if (( ${#_rows[@]} == 0 )); then
		echo -e "  ${DIM}(no entries found)${RESET}\n"
		return
	fi
	local -a widths
	local i
	for ((i = 0; i < ncol; i++)); do widths[i]=${#headers[i]}; done
	local row
	for row in "${_rows[@]}"; do
		local -a cols; IFS=$'\t' read -ra cols <<< "$row"
		for ((i = 0; i < ncol; i++)); do
			local len=${#cols[i]}
			(( len > widths[i] )) && widths[i]=$len
		done
	done
	local top="┌" mid="├" bot="└" seg
	for ((i = 0; i < ncol; i++)); do
		seg=$(printf '─%.0s' $(seq 1 $((widths[i] + 2))))
		top+="$seg"; mid+="$seg"; bot+="$seg"
		if (( i < ncol - 1 )); then top+="┬"; mid+="┼"; bot+="┴"; else top+="┐"; mid+="┤"; bot+="┘"; fi
	done
	echo -e "  ${DIM}${top}${RESET}"
	local hline="  │"
	for ((i = 0; i < ncol; i++)); do
		hline+=$(printf " %b%-${widths[i]}s%b │" "${BOLD}${CYAN}" "${headers[i]}" "${RESET}")
	done
	echo -e "$hline"
	echo -e "  ${DIM}${mid}${RESET}"
	for row in "${_rows[@]}"; do
		local -a cols; IFS=$'\t' read -ra cols <<< "$row"
		local line="  │"
		for ((i = 0; i < ncol; i++)); do
			line+=$(printf " %-${widths[i]}s │" "${cols[i]:-}")
		done
		echo -e "$line"
	done
	echo -e "  ${DIM}${bot}${RESET}"
	echo
}

_SPIN_PID=""

# Start a spinner with a message, mirroring rich.progress's SpinnerColumn
spin_start() {
	local msg="$1"
	(
		local frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
		local i=0
		printf "${HIDE_CURSOR}"
		while true; do
			printf "\r  ${CYAN}%s${RESET} %s" "${frames:i++%${#frames}:1}" "$msg"
			sleep 0.08
		done
	) &
	_SPIN_PID=$!
	disown
}

# Stop the running spinner and clear its line
spin_stop() {
	[[ -n "$_SPIN_PID" ]] || return
	kill "$_SPIN_PID" 2>/dev/null
	wait "$_SPIN_PID" 2>/dev/null
	_SPIN_PID=""
	printf "\r\033[K${SHOW_CURSOR}"
}

# Interactive arrow-key menu, mirroring questionary.select (cyan bold pointer/selection).
# Usage: select_menu "Prompt" "Option 1" "Option 2" ...
# Sets $SELECTED to the chosen 0-based index.
select_menu() {
	local prompt="$1"; shift
	local -a options=("$@")
	local count=${#options[@]}
	local idx=0 i key

	draw_options() {
		for ((i = 0; i < count; i++)); do
			printf "\033[2K"
			if (( i == idx )); then
				echo -e "  ${CYAN}${BOLD}» ${options[i]}${RESET}"
			else
				echo -e "    ${options[i]}"
			fi
		done
	}

	printf "${HIDE_CURSOR}"
	echo -e "  ${CYAN}?${RESET} ${BOLD}${prompt}${RESET} ${DIM}(Use arrow keys)${RESET}"
	draw_options
	while true; do
		key=""
		IFS= read -rsn1 key
		if [[ "$key" == $'\x1b' ]]; then
			key=""
			IFS= read -rsn2 -t 0.01 key
			case "$key" in
				'[A') (( idx = (idx - 1 + count) % count )) ;;
				'[B') (( idx = (idx + 1) % count )) ;;
			esac
		elif [[ -z "$key" ]]; then
			break
		fi
		printf "\033[%dA" "$count"
		draw_options
	done
	printf "\033[%dA" "$count"
	for ((i = 0; i < count; i++)); do printf "\033[2K\n"; done
	printf "\033[%dA" "$count"
	echo -e "  ${GREEN}✔${RESET} ${BOLD}${prompt}${RESET} ${CYAN}${options[idx]}${RESET}"
	printf "${SHOW_CURSOR}"
	SELECTED=$idx
}

# Center plain text (no ANSI codes) inside a field of the given width
pad_center() {
	local text="$1"
	local width="$2"
	local len=${#text}
	local left=$(( (width - len) / 2 ))
	local right=$(( width - len - left ))
	[ "$left" -lt 0 ] && left=0
	[ "$right" -lt 0 ] && right=0
	printf "%*s%s%*s" "$left" "" "$text" "$right" ""
}

# Print the program banner, mirroring rich.panel.Panel with centered title/subtitle
banner() {
	local title="MyApp Console v${VERSION} — Linux Application Manager"
	local subtitle="Bash interface for system, snap, flatpak, pip, npm & cargo"
	local width; width=$(term_width)
	local box=$(( width > 70 ? 60 : width - 10 ))
	(( box < 44 )) && box=44
	local border; border=$(printf -- '─%.0s' $(seq 1 "$box"))
	echo
	echo -e "  ${CYAN}╭${border}╮${RESET}"
	echo -e "  ${CYAN}│$(pad_center "" "$box")│${RESET}"
	echo -e "  ${CYAN}│${BOLD}$(pad_center "$title" "$box")${RESET}${CYAN}│${RESET}"
	echo -e "  ${CYAN}│${RESET}${DIM}$(pad_center "$subtitle" "$box")${RESET}${CYAN}│${RESET}"
	echo -e "  ${CYAN}│$(pad_center "" "$box")│${RESET}"
	echo -e "  ${CYAN}╰${border}╯${RESET}"
	echo
}

# Print the list of detected package managers
show_managers() {
	echo -e "  ${DIM}Detected managers:${RESET}"
	[[ -n "$PM" ]]	&& echo -e "  ${GREEN}✔${RESET} System    : ${BOLD}$PM${RESET}"
	$HAS_SNAP		&& echo -e "  ${GREEN}✔${RESET} Snap"
	$HAS_FLATPAK	&& echo -e "  ${GREEN}✔${RESET} Flatpak"
	$HAS_APPIMAGE	&& echo -e "  ${GREEN}✔${RESET} AppImage"
	$HAS_PIP		&& echo -e "  ${GREEN}✔${RESET} pip"
	$HAS_NPM		&& echo -e "  ${GREEN}✔${RESET} npm"
	$HAS_CARGO		&& echo -e "  ${GREEN}✔${RESET} cargo"
	echo
}

# Count and print the number of installed packages per manager
count_totals() {
	spin_start "Counting installed packages..."
	local total=0
	if [[ -n "$PM" ]]; then
		case "$PM" in
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
	spin_stop
	local -a rows=()
	rows+=("System packages"$'\t'"$total")
	$HAS_SNAP		&& rows+=("Snaps"$'\t'"$snap_count")
	$HAS_FLATPAK	&& rows+=("Flatpaks"$'\t'"$flat_count")
	$HAS_APPIMAGE	&& rows+=("AppImages"$'\t'"$ai_count")
	$HAS_PIP		&& rows+=("pip packages"$'\t'"$pip_count")
	$HAS_NPM		&& rows+=("npm -g packages"$'\t'"$npm_count")
	$HAS_CARGO		&& rows+=("cargo binaries"$'\t'"$cargo_count")
	print_table $'Manager\tInstalled' rows
}

# Wait for the user to press Enter before returning to the menu
pause() {
	echo; read -rp "  Press [Enter] to continue..."
}

# Print a section header
section() {
	echo
	hr "$1"
	echo
}

# Pipe through "less" when attached to a terminal, otherwise just "cat"
pager() {
	if [[ -t 1 ]]; then
		less -R
	else
		cat
	fi
}

# List installed system packages
list_system() {
	[[ -z "$PM" ]] && { echo -e "  ${RED}No system package manager detected.${RESET}"; return; }
	section "System packages ($PM)"
	local -a rows=()
	case "$PM" in
		apt)	 mapfile -t rows < <(dpkg-query -W -f='${Package}\t${Version}\n' 2>/dev/null | sort) ;;
		dnf|yum) mapfile -t rows < <(rpm -qa --qf "%{NAME}\t%{VERSION}\n" 2>/dev/null | sort) ;;
		pacman)  mapfile -t rows < <(pacman -Q 2>/dev/null | awk '{print $1"\t"$2}') ;;
		zypper)  mapfile -t rows < <(zypper se --installed-only 2>/dev/null | tail -n +5 | awk '{print $2"\t"$4}') ;;
		apk)	 mapfile -t rows < <(apk info -v 2>/dev/null | sort | awk '{print $0"\t"}') ;;
	esac
	print_table $'Package\tVersion' rows
}

# List installed Snap packages
list_snap() {
	$HAS_SNAP || { echo -e "  ${DIM}Snap not available.${RESET}"; return; }
	section "Installed Snaps"
	local -a rows=()
	mapfile -t rows < <(snap list 2>/dev/null | tail -n +2 | awk '{print $1"\t"$2"\t"$NF}')
	print_table $'Name\tVersion\tNotes' rows
}

# List installed Flatpak packages
list_flatpak() {
	$HAS_FLATPAK || { echo -e "  ${DIM}Flatpak not available.${RESET}"; return; }
	section "Installed Flatpaks"
	local -a rows=()
	mapfile -t rows < <(flatpak list --columns=application,name,version,installation 2>/dev/null | awk -F'\t' '{print $1"\t"$2"\t"$3}')
	print_table $'Application\tName\tVersion' rows
}

# List detected AppImage files with their size
list_appimage() {
	$HAS_APPIMAGE || { echo -e "  ${DIM}No AppImage found.${RESET}"; return; }
	section "Detected AppImages"
	local -a rows=()
	local f size
	while read -r f; do
		size=$(du -sh "$f" 2>/dev/null | cut -f1)
		rows+=("$f"$'\t'"$size")
	done < <(find_appimages)
	print_table $'Path\tSize' rows
}

# List installed pip packages
list_pip() {
	$HAS_PIP || { echo -e "  ${DIM}pip not available.${RESET}"; return; }
	section "pip packages (Python)"
	local -a rows=()
	mapfile -t rows < <(pip3 list 2>/dev/null | tail -n +3 | awk '{print $1"\t"$2}')
	print_table $'Package\tVersion' rows
}

# List globally installed npm packages
list_npm() {
	$HAS_NPM || { echo -e "  ${DIM}npm not available.${RESET}"; return; }
	section "Global npm packages"
	local -a rows=()
	mapfile -t rows < <(npm list -g --depth=0 2>/dev/null | tail -n +2 | sed 's/[├└─]//g' | awk '{print $NF}')
	print_table $'Package' rows
}

# List cargo-installed Rust binaries
list_cargo() {
	$HAS_CARGO || { echo -e "  ${DIM}cargo not available.${RESET}"; return; }
	section "Rust binaries (cargo)"
	local -a rows=()
	mapfile -t rows < <(cargo install --list 2>/dev/null | grep -E "^[a-z]")
	print_table $'Package' rows
}

# List everything from every available manager, through the pager
list_all() {
	{
		list_system
		list_snap
		list_flatpak
		list_appimage
		list_pip
		list_npm
		list_cargo
	} | pager
}

# Dispatch to the right list_* function based on a manager name
list_by_name() {
	local m="${1,,}"
	case "$m" in
		""|all)		list_all ;;
		system)		list_system ;;
		snap)		list_snap ;;
		flatpak)	list_flatpak ;;
		appimage)	list_appimage ;;
		pip|pip3)	list_pip ;;
		npm)		list_npm ;;
		cargo)		list_cargo ;;
		*)			echo -e "  ${RED}Unknown manager: $1${RESET}"; return 1 ;;
	esac
}

# Check for available updates on every manager, without installing anything
check_updates() {
	echo -e "${YELLOW}🔄 Checking for updates...${RESET}\n"
	if [[ -n "$PM" ]]; then
		section "System ($PM)"
		case "$PM" in
			apt)
				sudo apt update -qq 2>/dev/null
				local n; n=$(apt list --upgradable 2>/dev/null | grep -c upgradable)
				echo -e "  ${GREEN}$n package(s) to update:${RESET}"
				apt list --upgradable 2>/dev/null | grep upgradable | awk -F'/' '{printf "  %-35s %s\n", $1, $2}' ;;
			dnf|yum)	sudo $PM check-update 2>/dev/null ;;
			pacman)		sudo pacman -Sy &>/dev/null; pacman -Qu 2>/dev/null ;;
			zypper)		sudo zypper refresh -q 2>/dev/null; zypper list-updates 2>/dev/null ;;
			apk)		sudo apk update -q 2>/dev/null; apk list --upgradable 2>/dev/null ;;
		esac
	fi
	if $HAS_SNAP; then
		section "Snap"
		snap refresh --list 2>/dev/null || echo -e "  ${GREEN}Already up to date.${RESET}"
	fi
	if $HAS_FLATPAK; then
		section "Flatpak"
		flatpak remote-ls --updates 2>/dev/null || echo -e "  ${GREEN}Already up to date.${RESET}"
	fi
	if $HAS_PIP; then
		section "pip (Python - venv)"
		local outdated

		# Chemin direct vers le pip de ton venv
		local PY_ENV_PIP="/home/le-glitch/code/py/bin/pip"

		if [[ -x "$PY_ENV_PIP" ]]; then
			outdated=$("$PY_ENV_PIP" list --outdated 2>/dev/null | tail -n +3)
			if [[ -n "$outdated" ]]; then
				echo "$outdated" | awk '{printf "  %-30s current: %-10s available: %s\n", $1, $2, $3}'
			else
				echo -e "  ${GREEN}Already up to date.${RESET}"
			fi
		else
			echo -e "  ${RED}Environnement virtuel non trouvé dans /home/le-glitch/code/py${RESET}"
		fi
	fi
	if $HAS_NPM; then
		section "npm (global)"
		npm outdated -g --depth=0 2>/dev/null || echo -e "  ${GREEN}Already up to date.${RESET}"
	fi
}

# Upgrade all packages managed by the detected system package manager
run_system_upgrade() {
	case "$PM" in
		apt)	sudo apt update && sudo apt upgrade -y ;;
		dnf)	sudo dnf upgrade -y ;;
		yum)	sudo yum update -y ;;
		pacman)	sudo pacman -Syu ;;
		zypper)	sudo zypper update -y ;;
		apk)	sudo apk upgrade ;;
	esac
}

# Update every available manager (system, snap, flatpak, pip, npm)
update_all() {
	echo -e "${YELLOW}Full system update...${RESET}\n"
	echo -e "${RED}${BOLD}sudo privileges may be required.${RESET}\n"
	echo -e "  Managers that will be updated:"
	[[ -n "$PM" ]]	&& echo -e "  ${CYAN}•${RESET} System ($PM)"
	$HAS_SNAP		&& echo -e "  ${CYAN}•${RESET} Snap"
	$HAS_FLATPAK	&& echo -e "  ${CYAN}•${RESET} Flatpak"
	$HAS_PIP		&& echo -e "  ${CYAN}•${RESET} pip"
	$HAS_NPM		&& echo -e "  ${CYAN}•${RESET} npm"
	echo
	if ! $AUTO_YES; then
		read -rp "  Confirm the global update? [y/N]: " confirm
		[[ "$confirm" =~ ^[oOyY]$ ]] || { echo "  Cancelled."; return; }
	fi
	if [[ -n "$PM" ]]; then
		section "System update ($PM)"
		run_system_upgrade
	fi
	$HAS_SNAP	&& { section "Snap";	sudo snap refresh; }
	$HAS_FLATPAK && { section "Flatpak"; flatpak update -y; }
	local PY_ENV_PIP="/home/le-glitch/code/py/bin/pip"
	$HAS_PIP && [[ -x "$PY_ENV_PIP" ]] && { 
		section "pip (venv)"
		"$PY_ENV_PIP" list --outdated 2>/dev/null | tail -n +3 | awk '{print $1}' | xargs -r "$PY_ENV_PIP" install --upgrade 2>/dev/null
		echo -e "  ${GREEN}pip packages up to date.${RESET}"
	}
	$HAS_NPM	 && { section "npm"; npm update -g 2>/dev/null
		echo -e "  ${GREEN}npm up to date.${RESET}"; }
	echo -e "\n  ${GREEN}${BOLD}All updates are complete.${RESET}"
}

# Update only one chosen manager
update_selective() {
	echo -e "${YELLOW}Selective update${RESET}\n"
	local target
	if [[ -n "${1:-}" ]]; then
		resolve_manager "$1"
		target="$CHOSEN"
		if [[ -z "$target" ]]; then
			echo -e "  ${RED}Manager '$1' is unknown or unavailable.${RESET}"
			return 1
		fi
	else
		choose_manager
		target="$CHOSEN"
		[[ -z "$target" ]] && { echo -e "  ${RED}Invalid choice.${RESET}"; return 1; }
	fi
	case "$target" in
		system)
			if ! $AUTO_YES; then
				read -rp "  Confirm? [y/n]: " c; [[ "$c" =~ ^[oOyY]$ ]] || return
			fi
			run_system_upgrade ;;
		snap)		sudo snap refresh ;;
		flatpak)	flatpak update -y ;;
		pip)		pip3 list --outdated 2>/dev/null | tail -n +3 | awk '{print $1}' | xargs -r pip3 install --upgrade ;;
		npm)		npm update -g ;;
		cargo)
			echo -e "  ${YELLOW}Cargo does not update automatically.${RESET}"
			echo -e "  ${DIM}Reinstall manually: cargo install <package>${RESET}" ;;
		*)			echo -e "  ${RED}Invalid choice.${RESET}"; return 1 ;;
	esac
	echo -e "\n  ${GREEN}Done.${RESET}"
}

# Interactively ask the user to pick one of the available managers
choose_manager() {
	local prompt="${1:-Choose the manager}"
	local -a opts=() labels=()
	[[ -n "$PM" ]]	&& { labels+=("System ($PM)"); opts+=("system"); }
	$HAS_SNAP		&& { labels+=("Snap");			opts+=("snap"); }
	$HAS_FLATPAK	&& { labels+=("Flatpak");		opts+=("flatpak"); }
	$HAS_PIP		&& { labels+=("pip");			opts+=("pip"); }
	$HAS_NPM		&& { labels+=("npm (global)");	opts+=("npm"); }
	$HAS_CARGO		&& { labels+=("cargo");			opts+=("cargo"); }
	if [[ ${#labels[@]} -eq 0 ]]; then
		CHOSEN=""
		echo -e "  ${RED}No manager available.${RESET}"
		return
	fi
	select_menu "$prompt" "${labels[@]}"
	echo
	CHOSEN="${opts[$SELECTED]:-}"
}

# Resolve a manager name passed as an argument into CHOSEN, if available
resolve_manager() {
	local want="${1,,}"
	CHOSEN=""
	case "$want" in
		system|"${PM,,}")	[[ -n "$PM" ]]	&& CHOSEN="system" ;;
		snap)				$HAS_SNAP		&& CHOSEN="snap" ;;
		flatpak)			$HAS_FLATPAK	&& CHOSEN="flatpak" ;;
		pip|pip3)			$HAS_PIP		&& CHOSEN="pip" ;;
		npm)				$HAS_NPM		&& CHOSEN="npm" ;;
		cargo)				$HAS_CARGO		&& CHOSEN="cargo" ;;
	esac
}

# Search for a package by name in the chosen manager
search_app() {
	local pkg="${1:-}"
	local manager="${2:-}"
	if [[ -z "$pkg" ]]; then
		read -rp "  Name to search for: " pkg
	fi
	if [[ -z "$pkg" ]]; then
		echo -e "  ${RED}Empty name, search cancelled.${RESET}"
		return 1
	fi
	if [[ -n "$manager" ]]; then
		resolve_manager "$manager"
		if [[ -z "$CHOSEN" ]]; then
			echo -e "  ${RED}Manager '$manager' is unknown or unavailable.${RESET}"
			return 1
		fi
	else
		choose_manager "In which manager?"
	fi
	case "$CHOSEN" in
		system) case "$PM" in
					 apt)		apt-cache search "$pkg" 2>/dev/null | awk '{printf "  %-35s %s\n",$1,substr($0,index($0,$2))}' | pager ;;
					 dnf|yum)	$PM search "$pkg" 2>/dev/null | pager ;;
					 pacman)	pacman -Ss "$pkg" 2>/dev/null | pager ;;
					 zypper)	zypper search "$pkg" 2>/dev/null | pager ;;
					 apk)		apk search "$pkg" 2>/dev/null | pager ;;
				 esac ;;
		snap)		snap find "$pkg" 2>/dev/null | pager ;;
		flatpak)	flatpak search "$pkg" 2>/dev/null | pager ;;
		pip)		pip3 index versions "$pkg" 2>/dev/null | pager ;;
		npm)		npm search "$pkg" 2>/dev/null | pager ;;
		cargo)
			echo -e "  ${DIM}(cargo search relies on the crates.io API, results may be limited)${RESET}"
			cargo search "$pkg" 2>/dev/null | pager ;;
		*)			echo -e "  ${RED}Invalid choice.${RESET}"; return 1 ;;
	esac
}

# Install a package with the chosen manager
install_app() {
	local pkg="${1:-}"
	local manager="${2:-}"
	if [[ -z "$pkg" ]]; then
		read -rp "  Name of the package to install: " pkg
	fi
	if [[ -z "$pkg" ]]; then
		echo -e "  ${RED}Empty name, installation cancelled.${RESET}"
		return 1
	fi
	if [[ -n "$manager" ]]; then
		resolve_manager "$manager"
		if [[ -z "$CHOSEN" ]]; then
			echo -e "  ${RED}Manager '$manager' is unknown or unavailable.${RESET}"
			return 1
		fi
	else
		choose_manager "Via which manager?"
	fi
	case "$CHOSEN" in
		system) case "$PM" in
					 apt)		sudo apt install -y "$pkg" ;;
					 dnf|yum)	sudo $PM install -y "$pkg" ;;
					 pacman)	sudo pacman -S "$pkg" ;;
					 zypper)	sudo zypper install -y "$pkg" ;;
					 apk)		sudo apk add "$pkg" ;;
				 esac ;;
		snap)		sudo snap install "$pkg" ;;
		flatpak)	flatpak install -y "$pkg" ;;
		pip)		pip3 install "$pkg" ;;
		npm)		sudo npm install -g "$pkg" ;;
		cargo)		cargo install "$pkg" ;;
		*)			echo -e "  ${RED}Invalid choice.${RESET}"; return 1 ;;
	esac
}

# Remove a package with the chosen manager, asking confirmation unless AUTO_YES
remove_app() {
	local pkg="${1:-}"
	local manager="${2:-}"
	if [[ -z "$pkg" ]]; then
		read -rp "  Name of the package to remove: " pkg
	fi
	if [[ -z "$pkg" ]]; then
		echo -e "  ${RED}Empty name, removal cancelled.${RESET}"
		return 1
	fi
	if [[ -n "$manager" ]]; then
		resolve_manager "$manager"
		if [[ -z "$CHOSEN" ]]; then
			echo -e "  ${RED}Manager '$manager' is unknown or unavailable.${RESET}"
			return 1
		fi
	else
		choose_manager "Via which manager?"
	fi
	echo -e "  ${RED}Removing: ${BOLD}$pkg${RESET}"
	if ! $AUTO_YES; then
		read -rp "  Confirm? [y/N]: " c
		[[ "$c" =~ ^[oOyY]$ ]] || { echo "  Cancelled."; return; }
	fi
	case "$CHOSEN" in
		system) case "$PM" in
					 apt)		sudo apt remove -y "$pkg" ;;
					 dnf|yum)	sudo $PM remove -y "$pkg" ;;
					 pacman)	sudo pacman -R "$pkg" ;;
					 zypper)	sudo zypper remove -y "$pkg" ;;
					 apk)		sudo apk del "$pkg" ;;
				 esac ;;
		snap)		sudo snap remove "$pkg" ;;
		flatpak)	flatpak uninstall -y "$pkg" ;;
		pip)		pip3 uninstall -y "$pkg" ;;
		npm)		sudo npm uninstall -g "$pkg" ;;
		cargo)		cargo uninstall "$pkg" ;;
		*)			echo -e "  ${RED}Invalid choice.${RESET}"; return 1 ;;
	esac
}

# Export the full installed-app list to a timestamped text file
export_list() {
	local file
	file="apps_$(hostname)_$(date +%Y%m%d_%H%M%S).txt"
	echo -e "${YELLOW}Exporting to ${BOLD}$file${RESET}...\n"
	{
		echo "=========================================="
		echo "  Applications installed on $(hostname)"
		echo "  Date: $(date)"
		echo "=========================================="
		if [[ -n "$PM" ]]; then
			echo -e "\n── System ($PM) ──────────────────────"
			case "$PM" in
				apt)	 dpkg-query -W -f='${Package}\t${Version}\n' 2>/dev/null | sort ;;
				dnf|yum) rpm -qa --qf "%{NAME}\t%{VERSION}\n" 2>/dev/null | sort ;;
				pacman)  pacman -Q 2>/dev/null | sort ;;
				zypper)  zypper se --installed-only 2>/dev/null | tail -n +5 | awk '{print $2"\t"$4}' ;;
				apk)	 apk info -v 2>/dev/null | sort ;;
			esac
		fi
		$HAS_SNAP		&& { echo -e "\n── Snap ───────────────────────────"; snap list 2>/dev/null | tail -n +2; }
		$HAS_FLATPAK	&& { echo -e "\n── Flatpak ────────────────────────"; flatpak list 2>/dev/null; }
		$HAS_APPIMAGE	&& { echo -e "\n── AppImages ──────────────────────"; find_appimages; }
		$HAS_PIP		&& { echo -e "\n── pip ────────────────────────────"; pip3 list 2>/dev/null | tail -n +3; }
		$HAS_NPM		&& { echo -e "\n── npm global ─────────────────────"; npm list -g --depth=0 2>/dev/null | tail -n +2; }
		$HAS_CARGO		&& { echo -e "\n── cargo ──────────────────────────"; cargo install --list 2>/dev/null; }
	} > "$file"
	if [[ -s "$file" ]]; then
		echo -e "  ${GREEN}Exported: ${BOLD}$(pwd)/$file${RESET}"
	else
		echo -e "  ${RED}✗ Export failed (is the current directory writable?).${RESET}"
	fi
}

# Interactively ask which manager to list, mirroring the -l/--list CLI options
choose_list_target() {
	local -a opts=("all") labels=("All")
	[[ -n "$PM" ]]	&& { labels+=("System ($PM)"); opts+=("system"); }
	$HAS_SNAP		&& { labels+=("Snap");			opts+=("snap"); }
	$HAS_FLATPAK	&& { labels+=("Flatpak");		opts+=("flatpak"); }
	$HAS_APPIMAGE	&& { labels+=("AppImage");		opts+=("appimage"); }
	$HAS_PIP		&& { labels+=("pip");			opts+=("pip"); }
	$HAS_NPM		&& { labels+=("npm (global)");	opts+=("npm"); }
	$HAS_CARGO		&& { labels+=("cargo");			opts+=("cargo"); }
	select_menu "Which manager do you want to list?" "${labels[@]}"
	echo
	CHOSEN="${opts[$SELECTED]:-}"
}

# Interactive menu loop shown when no CLI option is given
menu() {
	detect_pkg_manager
	local -a main_options=(
		"List all applications"
		"Search for an application"
		"Check for updates"
		"Update the WHOLE system"
		"Update a specific manager"
		"Install an application"
		"Remove an application"
		"Export the full list to a text file"
		"Quit"
	)
	while true; do
		clear
		banner
		show_managers
		count_totals
		echo
		select_menu "What would you like to do?" "${main_options[@]}"
		echo
		case "$SELECTED" in
			0)	choose_list_target; list_by_name "$CHOSEN" ;;
			1)	search_app				; pause ;;
			2)	check_updates | pager	; pause ;;
			3)	update_all				; pause ;;
			4)	update_selective		; pause ;;
			5)	install_app				; pause ;;
			6)	remove_app				; pause ;;
			7)	export_list				; pause ;;
			8)	echo -e "  ${GREEN}See you soon!${RESET}\n"; exit 0 ;;
		esac
	done
}

# Print CLI usage / help text
usage() {
	cat <<-EOF
	    Linux Application Manager — CLI usage
	    Without any option, the interactive menu is shown (as before).
	    Every action available in the menu can also be triggered directly:

	        -l, --list [MANAGER]        List apps. MANAGER is optional:
	                                    system|snap|flatpak|appimage|pip|npm|cargo
	                                    (default: all)
	        -c, --check-updates         Check for available updates (no changes made)
	        -U, --update-all            Update everything (asks to confirm unless -y)
	        -m, --update-manager MGR    Update a single manager:
	                                    system|snap|flatpak|pip|npm|cargo
	        -s, --search NAME           Search for a package
	        -i, --install NAME          Install a package
	        -r, --remove NAME           Remove a package (asks to confirm unless -y)
	            --manager MGR           Manager to use with -s/-i/-r
	                                    (if omitted, you'll be prompted)
	        -e, --export                Export the full installed-app list to a file
	        -y, --yes                   Auto-confirm any prompt (non-interactive)
	        -v, --version               Show the program version and exit
	        -h, --help                  Show this help

	    Examples:
	        ./app_manager.sh --list snap
	        ./app_manager.sh --search vlc --manager flatpak
	        ./app_manager.sh --install htop --manager system -y
	        ./app_manager.sh --remove htop --manager system --yes
	        ./app_manager.sh --update-manager npm
	        ./app_manager.sh --update-all --yes
	EOF
}

# Entry point: parse CLI arguments, then run non-interactively or show the menu
main() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
			-l|--list)
				DO_LIST=true
				if [[ -n "${2:-}" && "$2" != -* ]]; then LIST_MANAGER="$2"; shift; fi
				;;
			-c|--check-updates)		DO_CHECK=true ;;
			-u|--update-all)		DO_UPDATE_ALL=true ;;
			-um|--update-manager)	UPDATE_MANAGER="${2:-}"; shift ;;
			-s|--search)			SEARCH_PKG="${2:-}"; shift ;;
			-i|--install)			INSTALL_PKG="${2:-}"; shift ;;
			-r|--remove)			REMOVE_PKG="${2:-}"; shift ;;
			-e|--export)			DO_EXPORT=true ;;
			-y|--yes)				AUTO_YES=true ;;
			-v|--version)			echo "App Manager v${VERSION}"; exit 0 ;;
			-h|--help)				SHOW_HELP=true ;;
			*) echo -e "${RED}Unknown option: $1${RESET}"; BAD_ARGS=true ;;
		esac
		shift
	done
	# Show help and exit immediately if requested
	if $SHOW_HELP; then
		usage
		exit 0
	fi
	# Stop on invalid arguments
	if $BAD_ARGS; then
		usage
		exit 1
	fi
	# Any action flag switches the script to non-interactive mode
	if $DO_LIST || $DO_CHECK || $DO_UPDATE_ALL || [[ -n "$UPDATE_MANAGER" ]] || [[ -n "$SEARCH_PKG" ]] || [[ -n "$INSTALL_PKG" ]] || [[ -n "$REMOVE_PKG" ]] || $DO_EXPORT; then
		NONINTERACTIVE=true
	fi
	detect_pkg_manager
	# Run each requested action once, then exit with the combined status
	if $NONINTERACTIVE; then
		STATUS=0
		$DO_LIST && { list_by_name "$LIST_MANAGER" || STATUS=1; }
		$DO_CHECK && check_updates
		$DO_UPDATE_ALL && update_all
		[[ -n "$UPDATE_MANAGER" ]] && { update_selective "$UPDATE_MANAGER" || STATUS=1; }
		[[ -n "$SEARCH_PKG" ]] && { search_app "$SEARCH_PKG" "$ACTION_MANAGER" || STATUS=1; }
		[[ -n "$INSTALL_PKG" ]] && { install_app "$INSTALL_PKG" "$ACTION_MANAGER" || STATUS=1; }
		[[ -n "$REMOVE_PKG" ]] && { remove_app "$REMOVE_PKG" "$ACTION_MANAGER" || STATUS=1; }
		$DO_EXPORT && export_list
		exit $STATUS
	fi
	# No action flag given: fall back to the interactive menu
	menu
}

main "$@"
