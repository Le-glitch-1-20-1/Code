#!/usr/bin/env bash
# Detect Manager — Linux
# Detects available package managers / installation methods, their versions,
# the system and the desktop environment.
set -o pipefail

VERSION="1.1.0"
readonly VERSION

# >>> STYLE BEGIN v1.0 — shared console style, keep this block identical in every script >>>
# Reference: STYLE-GUIDE.md. Needs bash >= 4.3 (namerefs).

# UTF-8 locale: without it ${#var} counts bytes instead of characters and breaks
# every box, rule and table.
if [[ "$(locale charmap 2>/dev/null)" != "UTF-8" ]]; then
	for _candidate in C.UTF-8 C.utf8 en_US.UTF-8 en_US.utf8; do
		locale -a 2>/dev/null | grep -qix "$_candidate" && { export LC_ALL="$_candidate"; break; }
	done
	unset _candidate
fi

# Colors: disabled when stdout is not a terminal or NO_COLOR is set
if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
	RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; CYAN=$'\033[0;36m'
	MAGENTA=$'\033[0;35m'; BOLD=$'\033[1m'; DIM=$'\033[2m'; RESET=$'\033[0m'
	HIDE_CURSOR=$'\033[?25l'; SHOW_CURSOR=$'\033[?25h'
else
	RED=''; GREEN=''; YELLOW=''; CYAN=''; MAGENTA=''; BOLD=''; DIM=''; RESET=''
	HIDE_CURSOR=''; SHOW_CURSOR=''
fi
readonly RED GREEN YELLOW CYAN MAGENTA BOLD DIM RESET HIDE_CURSOR SHOW_CURSOR

# Pass "$SEP" as an option of select_menu to draw a non-selectable divider line
readonly SEP="---sep---"

# ── Messages ─────────────────────────────────────────────────────────────────
msg_ok()   { echo -e "  ${GREEN}✔${RESET} $*"; }
msg_err()  { echo -e "  ${RED}✗ $*${RESET}" >&2; }
msg_warn() { echo -e "  ${YELLOW}⚠ $*${RESET}"; }
msg_info() { echo -e "  ${CYAN}•${RESET} $*"; }
msg_dim()  { echo -e "  ${DIM}$*${RESET}"; }
die()      { msg_err "$*"; exit 1; }

# ── Small helpers ────────────────────────────────────────────────────────────
have() { command -v "$1" &>/dev/null; }

# Repeat string $1 $2 times, without forking
rep() { local s; printf -v s '%*s' "$2" ''; printf '%s' "${s// /$1}"; }

term_width() { tput cols 2>/dev/null || echo 80; }

# Center plain text (no ANSI codes) inside a field of the given width
pad_center() {
	local text="$1"; local -i width="$2" len=${#1}
	local -i left=$(( (width - len) / 2 )) right
	(( left < 0 )) && left=0
	right=$(( width - len - left )); (( right < 0 )) && right=0
	printf '%*s%s%*s' "$left" "" "$text" "$right" ""
}

# ── Layout: banner, rules, key/value, list items ─────────────────────────────
# Rounded panel shown once at startup. Usage: banner "Title" ["Subtitle"]
banner() {
	local title="$1" subtitle="${2:-}"
	local -i width; width=$(term_width)
	local -i min_box=${#title}
	(( ${#subtitle} > min_box )) && min_box=${#subtitle}
	min_box+=4; (( min_box < 44 )) && min_box=44
	local -i box=$(( width > 70 ? 60 : width - 10 ))
	(( box < min_box )) && box=$min_box
	local border; border=$(rep '─' "$box")
	echo
	echo -e "  ${CYAN}╭${border}╮${RESET}"
	echo -e "  ${CYAN}│$(pad_center "" "$box")│${RESET}"
	echo -e "  ${CYAN}│${BOLD}$(pad_center "$title" "$box")${RESET}${CYAN}│${RESET}"
	echo -e "  ${CYAN}│${RESET}${DIM}$(pad_center "$subtitle" "$box")${RESET}${CYAN}│${RESET}"
	echo -e "  ${CYAN}│$(pad_center "" "$box")│${RESET}"
	echo -e "  ${CYAN}╰${border}╯${RESET}"
	echo
}

# Horizontal rule, with an optional embedded title. Usage: hr ["Title"]
hr() {
	local label="${1:-}" width; width=$(( $(term_width) - 2 ))
	if [[ -n "$label" ]]; then
		local head="── ${label} "
		local -i pad=$(( width - ${#head} )); (( pad < 0 )) && pad=0
		echo -e "  ${MAGENTA}${BOLD}${head}$(rep '─' "$pad")${RESET}"
	else
		echo -e "  ${MAGENTA}$(rep '─' "$width")${RESET}"
	fi
}

# Titled block: blank line, rule with title, blank line
section() { echo; hr "$1"; echo; }

# "Label         : value" line. Usage: kv "Label" "value"
kv() { printf '  %-14s: %s%s%s\n' "$1" "$BOLD" "$2" "$RESET"; }

# "✔ name  detail  extra" line for detected / found things. Usage: item_ok name [detail] [extra]
item_ok() {
	printf '  %s✔%s %-12s %s%-30s%s%s\n' "$GREEN" "$RESET" "$1" "$DIM" "${2:-}" "$RESET" "${3:+  $3}"
}

# ── Tables ───────────────────────────────────────────────────────────────────
# Split a TAB-separated row into the array named $2 (non-collapsing, keeps empty fields)
split_row() {
	local -n _out="$2"
	IFS=$'\x1f' read -ra _out <<< "${1//$'\t'/$'\x1f'}"
}

# Bordered table. Usage: print_table $'Col1\tCol2' rows_array_name
# Each element of the rows array is a TAB-separated line.
print_table() {
	local header="$1"; local -n _rows="$2"
	local -a headers=() cols=() widths=()
	local -i ncol i len
	split_row "$header" headers
	ncol=${#headers[@]}
	if (( ${#_rows[@]} == 0 )); then
		echo -e "  ${DIM}(no entries found)${RESET}\n"
		return
	fi
	for ((i = 0; i < ncol; i++)); do widths[i]=${#headers[i]}; done
	local row cell line
	for row in "${_rows[@]}"; do
		split_row "$row" cols
		for ((i = 0; i < ncol; i++)); do
			len=${#cols[i]}
			(( len > widths[i] )) && widths[i]=$len
		done
	done
	local top="┌" mid="├" bot="└" seg
	for ((i = 0; i < ncol; i++)); do
		seg=$(rep '─' $(( widths[i] + 2 )))
		top+="$seg"; mid+="$seg"; bot+="$seg"
		if (( i < ncol - 1 )); then top+="┬"; mid+="┼"; bot+="┴"; else top+="┐"; mid+="┤"; bot+="┘"; fi
	done
	echo -e "  ${DIM}${top}${RESET}"
	line="  │"
	for ((i = 0; i < ncol; i++)); do
		printf -v cell '%s%*s' "${headers[i]}" $(( widths[i] - ${#headers[i]} )) ''
		line+=" ${BOLD}${CYAN}${cell}${RESET} │"
	done
	echo -e "$line"
	echo -e "  ${DIM}${mid}${RESET}"
	for row in "${_rows[@]}"; do
		split_row "$row" cols
		line="  │"
		for ((i = 0; i < ncol; i++)); do
			printf -v cell '%s%*s' "${cols[i]:-}" $(( widths[i] - ${#cols[i]} )) ''
			line+=" ${cell} │"
		done
		printf '%s\n' "$line"
	done
	echo -e "  ${DIM}${bot}${RESET}\n"
}

# ── Spinner ──────────────────────────────────────────────────────────────────
SPIN_PID=""

spin_start() {
	[[ -t 1 ]] || return 0
	local msg="$1"
	(
		local frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏' i=0
		printf '%s' "$HIDE_CURSOR"
		while true; do
			printf '\r  %s%s%s %s' "$CYAN" "${frames:i++%${#frames}:1}" "$RESET" "$msg"
			sleep 0.08
		done
	) &
	SPIN_PID=$!
	disown
}

spin_stop() {
	[[ -n "$SPIN_PID" ]] || return 0
	kill "$SPIN_PID" 2>/dev/null
	wait "$SPIN_PID" 2>/dev/null
	SPIN_PID=""
	printf '\r\033[K%s' "$SHOW_CURSOR"
}

# Run a command behind a spinner, then show ✔ / ✗. Usage: run_task "Message" cmd args...
run_task() {
	local msg="$1" rc; shift
	spin_start "$msg"
	"$@" >/dev/null 2>&1; rc=$?
	spin_stop
	if (( rc == 0 )); then msg_ok "$msg"; else msg_err "$msg"; fi
	return $rc
}

# Restore the terminal (spinner + cursor). Call it from the EXIT trap.
ui_restore() { spin_stop 2>/dev/null; printf '%s' "$SHOW_CURSOR"; }

# ── Single-choice menu ───────────────────────────────────────────────────────
# Usage: select_menu "Prompt" "Option 1" "Option 2" "$SEP" "Quit" || return 1
# Sets $SELECTED to the chosen 0-based index. Arrows or j/k to move, Enter to validate.
SELECTED=0
_MENU_OPTS=(); _MENU_IDX=0

_menu_step() {		# move to the next selectable entry (+1 / -1), skipping dividers
	local -i n=${#_MENU_OPTS[@]} guard=0
	while :; do
		(( _MENU_IDX = (_MENU_IDX + $1 + n) % n ))
		[[ "${_MENU_OPTS[_MENU_IDX]}" != "$SEP" ]] && break
		(( ++guard > n )) && break
	done
}

_menu_draw() {
	local i
	for i in "${!_MENU_OPTS[@]}"; do
		printf '\033[2K'
		if [[ "${_MENU_OPTS[i]}" == "$SEP" ]]; then
			echo -e "  ${DIM}$(rep '─' 28)${RESET}"
		elif (( i == _MENU_IDX )); then
			echo -e "  ${CYAN}${BOLD}» ${_MENU_OPTS[i]}${RESET}"
		else
			echo -e "    ${_MENU_OPTS[i]}"
		fi
	done
}

select_menu() {
	if [[ ! -t 0 || ! -t 1 ]]; then
		msg_err "An interactive terminal is required."
		return 1
	fi
	local prompt="$1"; shift
	_MENU_OPTS=("$@"); _MENU_IDX=0
	local -i count=${#_MENU_OPTS[@]}
	local key
	[[ "${_MENU_OPTS[0]}" == "$SEP" ]] && _menu_step 1
	printf '%s' "$HIDE_CURSOR"
	echo -e "  ${CYAN}?${RESET} ${BOLD}${prompt}${RESET} ${DIM}(Use arrow keys)${RESET}"
	_menu_draw
	while true; do
		IFS= read -rsn1 key || { printf '%s' "$SHOW_CURSOR"; return 1; }
		if [[ "$key" == $'\033' ]]; then
			IFS= read -rsn2 -t 0.05 key
			case "$key" in
				'[A') _menu_step -1 ;;
				'[B') _menu_step 1 ;;
			esac
		elif [[ "$key" == k ]]; then _menu_step -1
		elif [[ "$key" == j ]]; then _menu_step 1
		elif [[ -z "$key" ]]; then break
		fi
		printf '\033[%dA' "$count"
		_menu_draw
	done
	printf '\033[%dA\033[J' $(( count + 1 ))
	echo -e "  ${GREEN}✔${RESET} ${BOLD}${prompt}${RESET} ${CYAN}${_MENU_OPTS[_MENU_IDX]}${RESET}"
	printf '%s' "$SHOW_CURSOR"
	SELECTED=$_MENU_IDX
}

# ── Multi-choice menu ────────────────────────────────────────────────────────
# Usage: checkbox_menu "Prompt" "Option 1" "Option 2" ... || return 1
# Sets the array $SELECTED_IDX to the checked 0-based indices (possibly empty).
# Arrows or j/k to move, Space to toggle, Enter to validate.
SELECTED_IDX=()
_CB_OPTS=(); _CB_ON=(); _CB_IDX=0

_cb_draw() {
	local i box
	for i in "${!_CB_OPTS[@]}"; do
		printf '\033[2K'
		if (( _CB_ON[i] )); then box="[${GREEN}✔${RESET}]"; else box="[ ]"; fi
		if (( i == _CB_IDX )); then
			echo -e "  ${CYAN}${BOLD}»${RESET} ${box} ${CYAN}${BOLD}${_CB_OPTS[i]}${RESET}"
		else
			echo -e "    ${box} ${_CB_OPTS[i]}"
		fi
	done
}

checkbox_menu() {
	if [[ ! -t 0 || ! -t 1 ]]; then
		msg_err "An interactive terminal is required."
		return 1
	fi
	local prompt="$1"; shift
	_CB_OPTS=("$@"); _CB_ON=(); _CB_IDX=0
	local -i count=${#_CB_OPTS[@]} i
	local key
	for ((i = 0; i < count; i++)); do _CB_ON[i]=0; done
	printf '%s' "$HIDE_CURSOR"
	echo -e "  ${CYAN}?${RESET} ${BOLD}${prompt}${RESET} ${DIM}(space: toggle, enter: confirm)${RESET}"
	_cb_draw
	while true; do
		IFS= read -rsn1 key || { printf '%s' "$SHOW_CURSOR"; return 1; }
		case "$key" in
			$'\033')
				IFS= read -rsn2 -t 0.05 key
				case "$key" in
					'[A') (( _CB_IDX = (_CB_IDX - 1 + count) % count )) ;;
					'[B') (( _CB_IDX = (_CB_IDX + 1) % count )) ;;
				esac ;;
			k) (( _CB_IDX = (_CB_IDX - 1 + count) % count )) ;;
			j) (( _CB_IDX = (_CB_IDX + 1) % count )) ;;
			' ') _CB_ON[_CB_IDX]=$(( 1 - _CB_ON[_CB_IDX] )) ;;
			'') break ;;
		esac
		printf '\033[%dA' "$count"
		_cb_draw
	done
	printf '\033[%dA\033[J' $(( count + 1 ))
	SELECTED_IDX=()
	local joined="" n
	for ((i = 0; i < count; i++)); do
		(( _CB_ON[i] )) || continue
		SELECTED_IDX+=("$i")
		joined+="${joined:+, }${_CB_OPTS[i]}"
	done
	[[ -n "$joined" ]] && echo -e "  ${GREEN}✔${RESET} ${BOLD}${prompt}${RESET} ${CYAN}${joined}${RESET}"
	printf '%s' "$SHOW_CURSOR"
}

# ── Prompts ──────────────────────────────────────────────────────────────────
# Yes/no prompt, auto-accepted when AUTO_YES=true (--yes)
confirm() {
	[[ "${AUTO_YES:-false}" == true ]] && return 0
	local answer
	read -rp "  $1 [y/N]: " answer || return 1
	[[ "$answer" =~ ^[oOyY]$ ]]
}

pause() { echo; read -rp "  Press [Enter] to continue..." _; }
# <<< STYLE END <<<

# ──────────────────────────────────────────────────────────────────────────────
#  Global state
# ──────────────────────────────────────────────────────────────────────────────
FOUND=0				# total number of tools detected
GROUP_HITS=0		# tools detected in the current group

trap ui_restore EXIT
trap 'echo -e "${RESET}\n  ${YELLOW}Interrupted.${RESET}"; exit 130' INT

# ──────────────────────────────────────────────────────────────────────────────
#  Detection helpers
# ──────────────────────────────────────────────────────────────────────────────
# First useful line of a tool's version output.
# stdin is closed and a timeout is applied so nothing can block.
get_version() {		# $1 = command, $2 = version option(s)
	local out
	# shellcheck disable=SC2086
	if have timeout; then
		out=$(timeout 3 "$1" $2 </dev/null 2>&1 | head -n 1)
	else
		out=$("$1" $2 </dev/null 2>&1 | head -n 1)
	fi
	printf '%s' "$out" | sed 's/^[[:space:]]*//' | cut -c1-80
}

group_begin() { section "$1"; GROUP_HITS=0; }
group_end()   { (( GROUP_HITS )) || msg_dim "(none)"; }

# Print one detected tool and update the counters. Usage: report name path version
report() {
	item_ok "$1" "$2" "$3"
	(( FOUND++ )); (( GROUP_HITS++ ))
}

# Usage: check "display name" command [version option, default --version]
check() {
	have "$2" || return 0
	local path; path=$(command -v "$2")
	report "$1" "$path" "$(get_version "$2" "${3:---version}")"
}

# cpan: read the version in CPAN.pm without launching cpan (no configuration needed)
check_cpan() {
	have cpan || return 0
	local ver=""
	if have perl; then
		ver=$(perl -e '
			for $d (@INC) {
				$f = "$d/CPAN.pm";
				next unless -f $f;
				open(F, "<", $f) or next;
				while (<F>) {
					if (/\$(?:CPAN::)?VERSION\s*=\s*["\x27]?([0-9._]+)/) {
						print "CPAN $1";
						exit;
					}
				}
			}
		' 2>/dev/null </dev/null)
		# Fallback: Perl version if CPAN.pm cannot be found
		[[ -z "$ver" ]] && ver=$(perl -e 'print "perl $^V"' 2>/dev/null </dev/null)
	fi
	report cpan "$(command -v cpan)" "$ver"
}

# ──────────────────────────────────────────────────────────────────────────────
#  Detection
# ──────────────────────────────────────────────────────────────────────────────
detect_tools() {
	group_begin "System package managers"
	check apt		apt
	check apt-get	apt-get
	check dpkg		dpkg
	check dnf		dnf
	check yum		yum
	check rpm		rpm
	check zypper	zypper
	check pacman	pacman
	check apk		apk			--version
	check emerge	emerge
	check xbps		xbps-install
	check nix		nix-env
	check guix		guix
	check eopkg		eopkg
	check slackpkg	slackpkg	-h
	check pkg		pkg			-v
	group_end

	group_begin "Universal formats"
	check snap		snap
	check flatpak	flatpak
	check appimage	appimagetool
	check brew		brew
	group_end

	group_begin "Languages"
	check pip		pip
	check pip3		pip3
	check pipx		pipx
	check uv		uv
	check conda		conda
	check npm		npm
	check yarn		yarn
	check pnpm		pnpm
	check gem		gem
	check cargo		cargo
	check go		go			version
	check_cpan
	check composer	composer
	check luarocks	luarocks
	check opam		opam
	check mix		mix
	check dotnet	dotnet
	group_end

	group_begin "Build from source"
	check make		make
	check cmake		cmake
	check gcc		gcc
	check meson		meson
	check git		git
	group_end

	group_begin "Download tools"
	check curl		curl
	check wget		wget
	group_end

	echo
	hr
	if (( FOUND == 0 )); then
		msg_warn "No package manager detected."
	else
		kv "Total detected" "$FOUND"
	fi
}

detect_system() {
	section "System"
	if [[ -r /etc/os-release ]]; then
		# Parsed, not sourced: sourcing would overwrite our own VERSION variable
		local distro; distro=$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release | tr -d '"')
		kv "Distribution" "${distro:-unknown}"
	fi
	kv "Kernel" "$(uname -sr)"
}

detect_desktop() {
	section "Desktop environment"

	# DE name: XDG_CURRENT_DESKTOP is the most reliable
	local de="${XDG_CURRENT_DESKTOP:-${DESKTOP_SESSION:-}}" p
	# Fallback: look at the running processes
	if [[ -z "$de" ]]; then
		for p in gnome-shell plasmashell xfce4-session cinnamon mate-session lxqt-session lxsession budgie-panel cosmic-session; do
			if pgrep -x "$p" >/dev/null 2>&1; then de="$p"; break; fi
		done
	fi

	if [[ -z "$de" ]]; then
		kv "Desktop" "none detected (TTY / server?)"
	else
		kv "Desktop" "$de"
		# Version, depending on the detected DE
		local dever=""
		case "$de" in
			*GNOME*|*gnome*|*Unity*|*ubuntu*)
				have gnome-shell && dever=$(gnome-shell --version 2>/dev/null) ;;
			*KDE*|*plasma*)
				have plasmashell && dever=$(plasmashell --version 2>/dev/null) ;;
			*XFCE*|*xfce*)
				have xfce4-session && dever=$(xfce4-session --version 2>/dev/null | head -n 1) ;;
			*Cinnamon*|*cinnamon*)
				have cinnamon && dever=$(cinnamon --version 2>/dev/null) ;;
			*MATE*|*mate*)
				have mate-session && dever=$(mate-session --version 2>/dev/null) ;;
			*LXQt*|*lxqt*)
				have lxqt-session && dever=$(lxqt-session --version 2>/dev/null | head -n 1) ;;
			*Budgie*|*budgie*)
				have budgie-desktop && dever=$(budgie-desktop --version 2>/dev/null | head -n 1) ;;
		esac
		[[ -n "$dever" ]] && kv "DE version" "$dever"
	fi

	# Session type (Wayland / X11)
	if [[ -n "${XDG_SESSION_TYPE:-}" ]]; then
		kv "Session" "$XDG_SESSION_TYPE"
	elif [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
		kv "Session" "wayland"
	elif [[ -n "${DISPLAY:-}" ]]; then
		kv "Session" "x11"
	fi

	# Window manager / compositor (under GNOME, mutter lives inside the gnome-shell process)
	local wm=""
	for p in gnome-shell mutter kwin_wayland kwin_x11 xfwm4 marco muffin openbox i3 sway hyprland bspwm awesome dwm river labwc wayfire; do
		if pgrep -x "$p" >/dev/null 2>&1; then wm="$p"; break; fi
	done
	if [[ "$wm" == gnome-shell ]]; then
		kv "Window mgr" "mutter (via gnome-shell)"
	elif [[ -n "$wm" ]]; then
		kv "Window mgr" "$wm"
	fi

	# Display manager: read from systemd first
	local dm=""
	if [[ -e /etc/systemd/system/display-manager.service ]]; then
		dm=$(basename "$(readlink -f /etc/systemd/system/display-manager.service)" .service)
	else
		for p in gdm gdm3 sddm lightdm lxdm ly greetd; do
			if pgrep -x "$p" >/dev/null 2>&1; then dm="$p"; break; fi
		done
	fi
	[[ -n "$dm" ]] && kv "Display mgr" "$dm"
	echo
}

# ──────────────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────────────
usage() {
	cat <<EOF
    Detect Manager v${VERSION} — CLI usage
    Detects package managers, build tools, system and desktop environment.

        -v, --version               Show the program version and exit
        -h, --help                  Show this help

    Example:
        ./Detect-manager.sh
        NO_COLOR=1 ./Detect-manager.sh > report.txt
EOF
}

main() {
	local bad=false
	while [[ $# -gt 0 ]]; do
		case "$1" in
			-v|--version)	echo "Detect Manager v${VERSION}"; exit 0 ;;
			-h|--help)		usage; exit 0 ;;
			*)				msg_err "Unknown option: $1"; bad=true ;;
		esac
		shift
	done
	if $bad; then usage; exit 1; fi

	banner "Detect Manager v${VERSION}" "Package managers, tools & desktop environment"
	detect_tools
	detect_system
	detect_desktop
}

main "$@"