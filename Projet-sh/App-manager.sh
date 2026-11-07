#!/usr/bin/env bash
# MyApp Console — Linux Application Manager
# Detects every package manager / install method on the system, then lets you
# list, search, install, remove and (above all) upgrade everything from one place.
set -o pipefail


VERSION="2.3.0"
readonly VERSION

# Namerefs (local -n) need bash >= 4.3: fail early with a clear message
(( BASH_VERSINFO[0] > 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] >= 3) )) \
	|| { echo "bash >= 4.3 is required (found ${BASH_VERSION})." >&2; exit 1; }

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
AUTO_YES=false
DO_LIST=false
LIST_MANAGER=""
FILTER=""					# text filter applied when listing
DO_CHECK=false
DO_UPDATE_ALL=false
DO_EXPORT=false
DO_DETECT=false
SHOW_HELP=false
BAD_ARGS=false
UPDATE_MANAGER=""
SEARCH_PKG=""
INSTALL_PKG=""
REMOVE_PKG=""
ACTION_MANAGER=""

PM=""						# primary system package manager
CHOSEN=""					# result of resolve_manager / choose_manager
STALE=1						# package counts need recomputing
SUDO_KEEPALIVE_PID=""
declare -a MANAGERS=()		# ordered ids of the managers available on this system
declare -a RESULTS=()		# per-manager upgrade results
declare -a COUNT_ROWS=()	# cached package counts
declare -A LABEL=() BIN=()

cleanup() {
	drop_sudo
	ui_restore
}
trap cleanup EXIT
trap 'echo -e "${RESET}\n  ${YELLOW}Interrupted.${RESET}"; exit 130' INT


# Does manager $1 implement capability $2 (rows, outdated, upgrade, search, install, remove)?
cap() { declare -F "${1}_${2}" >/dev/null; }

# Run a command as root (directly if already root, through sudo otherwise)
as_root() {
	if (( EUID == 0 )); then
		"$@"
	elif have sudo; then
		sudo "$@"
	else
		msg_err "Root privileges required but sudo was not found."
		return 1
	fi
}

# Ask for the sudo password once and keep the ticket alive during long upgrades
prime_sudo() {
	(( EUID == 0 )) && return 0
	have sudo || return 0
	[[ -t 0 ]] || return 0
	sudo -v || return 0
	[[ -n "$SUDO_KEEPALIVE_PID" ]] && return 0
	( while true; do sudo -n true 2>/dev/null; sleep 50; kill -0 "$$" 2>/dev/null || exit; done ) &
	SUDO_KEEPALIVE_PID=$!
	disown
}

# Stop the sudo keep-alive and drop the cached ticket, so a sudo credential never outlives the action
drop_sudo() {
	[[ -n "$SUDO_KEEPALIVE_PID" ]] || return 0
	pkill -P "$SUDO_KEEPALIVE_PID" 2>/dev/null
	kill "$SUDO_KEEPALIVE_PID" 2>/dev/null
	SUDO_KEEPALIVE_PID=""
	sudo -k 2>/dev/null
	return 0
}

# Ask before escalating to root for a language ecosystem. Ignores --yes on purpose.
# $1 = tool, $2 = how to avoid root
confirm_root() {
	local answer
	msg_warn "$1: the global install directory is not writable by your user."
	msg_dim "Safer: $2"
	msg_dim "Running as root also runs the packages' install scripts as root."
	[[ -t 0 && -t 1 ]] || return 1
	read -rp "  Continue as root anyway? [y/N]: " answer || return 1
	[[ "$answer" =~ ^[oOyY]$ ]]
}

# Warn when the whole script runs as root (user-level managers would act on root's files)
root_warning() {
	if (( EUID == 0 )); then
		msg_warn "Running as root: pip, npm, cargo... will act on root's files. Prefer your normal user (sudo is asked when needed)."
	fi
	return 0
}

# Input validation: refuse anything that could be read as an option or expanded as a pattern.
# Package names: letters, digits and . _ + : = @ / ~ -   never starting with "-", no wildcards.
valid_pkg() { [[ "$1" =~ ^[[:alnum:]@][[:alnum:]._+:=@/~-]*$ ]]; }
# Search text: free text, but not an option and without control characters.
valid_query() { [[ -n "$1" && "$1" != -* && "$1" != *[[:cntrl:]]* ]]; }
bad_pkg() { msg_err "Invalid package name (allowed: letters, digits and . _ + : = @ / ~ - ; no leading '-', no wildcards)."; }

# Pipe through a pager when attached to a terminal
pager() { if [[ -t 1 ]]; then less -RFX; else cat; fi; }

# Prefix each line with two spaces, or say that there is nothing to show
indent_or_ok() {
	local out; out=$(cat)
	if [[ -z "${out//[[:space:]]/}" ]]; then
		echo -e "  ${GREEN}Already up to date.${RESET}"
	else
		sed 's/^/  /' <<< "$out"
	fi
}

# ──────────────────────────────────────────────────────────────────────────────
#  Detection
# ──────────────────────────────────────────────────────────────────────────────
register() { MANAGERS+=("$1"); LABEL[$1]="$2"; BIN[$1]="${3:-}"; }

detect_system() {
	PM=""
	local c
	for c in apt dnf yum pacman zypper apk xbps-install emerge eopkg; do
		have "$c" && { PM="$c"; break; }
	done
	[[ "$PM" == xbps-install ]] && PM="xbps"
	return 0
}

pip_bin() {
	if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/pip" ]]; then
		echo "${VIRTUAL_ENV}/bin/pip"
	elif have pip3; then echo "pip3"
	elif have pip;  then echo "pip"
	fi
}

# Single source of truth for detection: "group|name|command|manager-id|label".
# A non-empty id means this script manages it (rows/upgrade/... functions exist);
# entries without id are only reported by --detect.
DETECT_TABLE=(
	"System managers|apt|apt||"
	"System managers|apt-get|apt-get||"
	"System managers|dpkg|dpkg||"
	"System managers|dnf|dnf||"
	"System managers|yum|yum||"
	"System managers|rpm|rpm||"
	"System managers|zypper|zypper||"
	"System managers|pacman|pacman||"
	"System managers|apk|apk||"
	"System managers|emerge|emerge||"
	"System managers|xbps|xbps-install||"
	"System managers|nix|nix-env|nix|Nix"
	"System managers|guix|guix||"
	"System managers|eopkg|eopkg||"
	"System managers|slackpkg|slackpkg||"
	"System managers|pkg|pkg||"
	"Universal formats|snap|snap|snap|Snap"
	"Universal formats|flatpak|flatpak|flatpak|Flatpak"
	"Universal formats|appimage|appimagetool|appimage|AppImage"
	"Universal formats|brew|brew|brew|Homebrew"
	"Languages|pip|pip|pip|pip"
	"Languages|pip3|pip3|pip|pip"
	"Languages|pipx|pipx|pipx|pipx"
	"Languages|uv|uv|uv|uv tools"
	"Languages|conda|conda|conda|conda"
	"Languages|npm|npm|npm|npm (global)"
	"Languages|yarn|yarn|yarn|yarn (global)"
	"Languages|pnpm|pnpm|pnpm|pnpm (global)"
	"Languages|gem|gem|gem|RubyGems"
	"Languages|cargo|cargo|cargo|cargo"
	"Languages|rustup|rustup|rustup|rustup"
	"Languages|go|go||"
	"Languages|composer|composer|composer|composer (global)"
	"Languages|cpan|cpan||"
	"Languages|luarocks|luarocks||"
	"Languages|opam|opam||"
	"Languages|mix|mix||"
	"Languages|dotnet|dotnet||"
	"Build from source|make|make||"
	"Build from source|cmake|cmake||"
	"Build from source|gcc|gcc||"
	"Build from source|meson|meson||"
	"Build from source|git|git||"
	"Download tools|curl|curl||"
	"Download tools|wget|wget||"
)

# Build MANAGERS from the detection table
detect_managers() {
	MANAGERS=()
	detect_system
	if [[ -n "$PM" ]]; then
		register system "System ($PM)" "$([[ "$PM" == xbps ]] && echo xbps-install || echo "$PM")"
	fi
	local entry group name cmd id label
	for entry in "${DETECT_TABLE[@]}"; do
		IFS='|' read -r group name cmd id label <<< "$entry"
		[[ -n "$id" ]] || continue
		have "$cmd" || continue
		[[ -n "${LABEL[$id]:-}" ]] && continue		# already registered (e.g. pip / pip3)
		case "$id" in
			yarn) [[ "$(yarn --version 2>/dev/null)" == 1.* ]] || continue ;;
			pip)  [[ -n "$(pip_bin)" ]] || continue; cmd=$(pip_bin) ;;
		esac
		register "$id" "$label" "$cmd"
	done
	return 0
}

show_detection() {
	local entry group name cmd id label path g any total=0
	local -a groups=(); local -A seen=()
	for entry in "${DETECT_TABLE[@]}"; do
		group="${entry%%|*}"
		[[ -n "${seen[$group]:-}" ]] || { seen[$group]=1; groups+=("$group"); }
	done
	for g in "${groups[@]}"; do
		section "$g"; any=false
		for entry in "${DETECT_TABLE[@]}"; do
			IFS='|' read -r group name cmd id label <<< "$entry"
			[[ "$group" == "$g" ]] || continue
			path=$(command -v "$cmd" 2>/dev/null) || continue
			local tag=""
			[[ -n "$id" && -n "${LABEL[$id]:-}" ]] && tag="${GREEN}managed${RESET}"
			item_ok "$name" "$path" "$tag"
			(( ++total )); any=true
		done
		$any || echo -e "  ${DIM}(none)${RESET}"
	done
	echo
	hr
	kv "Total detected" "$total"
	if [[ -r /etc/os-release ]]; then
		local distro; distro=$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release | tr -d '"')
		kv "Distribution" "${distro:-unknown}"
	fi
	local out=""
	for id in "${MANAGERS[@]}"; do cap "$id" upgrade && out+="${id} "; done
	kv "Upgradable here" "${out:-none}"; echo
}

# Compact one-line summary used in the menu header
show_managers() {
	local id out=""
	for id in "${MANAGERS[@]}"; do out+="${GREEN}✔${RESET} ${LABEL[$id]}   "; done
	echo -e "  ${DIM}Detected:${RESET} ${out}\n"
}

# ──────────────────────────────────────────────────────────────────────────────
#  Manager: system packages (apt, dnf, yum, pacman, zypper, apk, xbps, emerge, eopkg)
# ──────────────────────────────────────────────────────────────────────────────
system_rows() {
	case "$PM" in
		apt)			dpkg-query -W -f='${db:Status-Abbrev} ${Package}\t${Version}\n' 2>/dev/null | awk -F'\t' '{ split($1, a, " "); if (a[1] == "ii") print a[2] "\t" $2 }' | sort ;;
		dnf|yum|zypper)	rpm -qa --qf '%{NAME}\t%{VERSION}\n' 2>/dev/null | sort ;;
		pacman)			pacman -Q 2>/dev/null | awk '{print $1 "\t" $2}' ;;
		apk)			apk info -v 2>/dev/null | sort | sed -E 's/^(.*)-([^-]+-r[0-9]+)$/\1\t\2/' ;;
		xbps)			xbps-query -l 2>/dev/null | awk '{ n=$2; sub(/-[^-]+$/, "", n); v=$2; sub(/.*-/, "", v); print n "\t" v }' ;;
		emerge)			local d; for d in /var/db/pkg/*/*; do [[ -d "$d" ]] && printf '%s\t\n' "${d#/var/db/pkg/}"; done ;;
		eopkg)			eopkg li 2>/dev/null | awk '{print $1 "\t"}' ;;
	esac
}

system_outdated() {
	case "$PM" in
		apt)			as_root apt-get update -qq >/dev/null 2>&1; apt list --upgradable 2>/dev/null | tail -n +2 ;;
		dnf|yum)		as_root "$PM" -q check-update ;;
		pacman)			if have checkupdates; then checkupdates; else pacman -Qu; fi ;;
		zypper)			as_root zypper -q refresh >/dev/null 2>&1; zypper -q list-updates ;;
		apk)			as_root apk update -q >/dev/null 2>&1; apk version -l '<' | tail -n +2 ;;
		xbps)			as_root xbps-install -S >/dev/null 2>&1; xbps-install -Sun ;;
		emerge)			emerge --pretend --update --deep --newuse @world 2>/dev/null | grep -E '^\[ebuild' ;;
		eopkg)			as_root eopkg -q update-repo >/dev/null 2>&1; eopkg list-upgrades ;;
	esac
}

# autoremove can drop packages without you noticing: never run it unattended
apt_autoremove() {
	if [[ "${AUTO_YES:-false}" == true ]]; then
		msg_dim "autoremove skipped in --yes mode (run 'sudo apt autoremove' yourself)."
	else
		as_root apt-get autoremove
	fi
	return 0
}

system_upgrade() {
	case "$PM" in
		apt)			as_root apt-get update && as_root apt-get -y full-upgrade && apt_autoremove ;;
		dnf)			as_root dnf -y upgrade --refresh ;;
		yum)			as_root yum -y update ;;
		pacman)			as_root pacman -Syu --noconfirm ;;
		zypper)			as_root zypper -n refresh && as_root zypper -n update ;;
		apk)			as_root apk update && as_root apk upgrade ;;
		xbps)			as_root xbps-install -Syu ;;
		emerge)			as_root emerge --sync && as_root emerge --ask=n --update --deep --newuse @world ;;
		eopkg)			as_root eopkg -y upgrade ;;
	esac
}

system_search() {
	case "$PM" in
		apt)			apt-cache search "$1" ;;
		dnf|yum)		"$PM" search "$1" ;;
		pacman)			pacman -Ss "$1" ;;
		zypper)			zypper search "$1" ;;
		apk)			apk search "$1" ;;
		xbps)			xbps-query -Rs "$1" ;;
		emerge)			emerge --search "$1" ;;
		eopkg)			eopkg search "$1" ;;
	esac 2>/dev/null
}

system_install() {
	case "$PM" in
		apt)			as_root apt-get install -y "$1" ;;
		dnf|yum)		as_root "$PM" install -y "$1" ;;
		pacman)			as_root pacman -S --noconfirm "$1" ;;
		zypper)			as_root zypper -n install "$1" ;;
		apk)			as_root apk add "$1" ;;
		xbps)			as_root xbps-install -y "$1" ;;
		emerge)			as_root emerge --ask=n "$1" ;;
		eopkg)			as_root eopkg -y install "$1" ;;
	esac
}

system_remove() {
	case "$PM" in
		apt)			as_root apt-get remove -y "$1" ;;
		dnf|yum)		as_root "$PM" remove -y "$1" ;;
		pacman)			as_root pacman -Rs --noconfirm "$1" ;;
		zypper)			as_root zypper -n remove "$1" ;;
		apk)			as_root apk del "$1" ;;
		xbps)			as_root xbps-remove -y "$1" ;;
		emerge)			as_root emerge --ask=n --unmerge "$1" ;;
		eopkg)			as_root eopkg -y remove "$1" ;;
	esac
}

# ──────────────────────────────────────────────────────────────────────────────
#  Manager: snap / flatpak / homebrew / nix / appimage
# ──────────────────────────────────────────────────────────────────────────────
snap_rows()			{ snap list 2>/dev/null | tail -n +2 | awk '{print $1 "\t" $2 "\t" $NF}'; }
snap_outdated()		{ LC_MESSAGES=C snap refresh --list 2>&1 | grep -vi 'all snaps up to date'; }
snap_upgrade()		{ as_root snap refresh; }
snap_search()		{ snap find "$1"; }
snap_install()		{ as_root snap install "$1"; }
snap_remove()		{ as_root snap remove "$1"; }

flatpak_rows()		{ flatpak list --columns=application,name,version 2>/dev/null; }
flatpak_outdated()	{ flatpak remote-ls --updates 2>/dev/null; }
flatpak_upgrade()	{ local rc; flatpak update -y; rc=$?; flatpak uninstall --unused -y; return $rc; }
flatpak_search()	{ flatpak search "$1"; }
flatpak_install()	{ flatpak install -y "$1"; }
flatpak_remove()	{ flatpak uninstall -y "$1"; }

brew_rows()			{ brew list --versions 2>/dev/null | awk '{print $1 "\t" $NF}'; }
brew_outdated()		{ brew update -q >/dev/null 2>&1; brew outdated; }
brew_upgrade()		{ brew update && brew upgrade && brew cleanup; }
brew_search()		{ brew search "$1"; }
brew_install()		{ brew install "$1"; }
brew_remove()		{ brew uninstall "$1"; }

nix_rows()			{ nix-env -q 2>/dev/null; }
nix_outdated()		{ nix-env -u --dry-run 2>&1 | grep -E '^\s*upgrading'; }
nix_upgrade()		{ { nix-channel --update 2>/dev/null; true; } && nix-env -u; }
nix_search()		{ nix-env -qaP ".*${1}.*" 2>/dev/null; }
nix_install()		{ nix-env -iA "nixpkgs.$1"; }
nix_remove()		{ nix-env -e "$1"; }

find_appimages() {
	local -a dirs=("$HOME" "$HOME/Applications" "$HOME/AppImages" /opt /usr/local/bin)
	find "${dirs[@]}" -maxdepth 3 -name '*.AppImage' 2>/dev/null | sort -u
}
appimage_rows() {
	local f
	while IFS= read -r f; do
		printf '%s\t%s\n' "$f" "$(du -sh "$f" 2>/dev/null | cut -f1)"
	done < <(find_appimages)
}

# ──────────────────────────────────────────────────────────────────────────────
#  Manager: language ecosystems
# ──────────────────────────────────────────────────────────────────────────────
# pip: system Python is locked by PEP 668 on recent distros; never fight it.
pip_external() {
	[[ -n "${VIRTUAL_ENV:-}" ]] && return 1
	python3 - <<'PY' 2>/dev/null
import os, sys, sysconfig
sys.exit(0 if os.path.exists(os.path.join(sysconfig.get_path("stdlib"), "EXTERNALLY-MANAGED")) else 1)
PY
}
pip_rows()			{ "$(pip_bin)" list --format=freeze 2>/dev/null | grep '==' | awk -F'==' '{print $1 "\t" $2}'; }
pip_outdated()		{ "$(pip_bin)" --timeout 10 --retries 0 list --outdated 2>/dev/null; }
pip_upgrade() {
	if pip_external; then
		echo -e "  ${DIM}System Python is externally managed (PEP 668): skipped. pipx, uv or a virtualenv are upgraded separately.${RESET}"
		return 2
	fi
	local pip; pip=$(pip_bin)
	local -a pkgs
	mapfile -t pkgs < <("$pip" --timeout 15 --retries 1 list --outdated --format=freeze 2>/dev/null | cut -d= -f1)
	if (( ${#pkgs[@]} == 0 )); then echo -e "  ${GREEN}Already up to date.${RESET}"; return 0; fi
	"$pip" install --upgrade "${pkgs[@]}"
}
pip_search()		{ "$(pip_bin)" index versions "$1"; }
pip_install() {
	pip_external && { echo -e "  ${YELLOW}PEP 668: system pip is locked. Use pipx/uv for apps or a virtualenv for libraries.${RESET}"; return 1; }
	"$(pip_bin)" install "$1"
}
pip_remove() {
	pip_external && { echo -e "  ${YELLOW}PEP 668: system pip is locked.${RESET}"; return 1; }
	"$(pip_bin)" uninstall -y "$1"
}

pipx_rows()			{ pipx list --short 2>/dev/null | awk '{print $1 "\t" $2}'; }
pipx_upgrade()		{ pipx upgrade-all; }
pipx_install()		{ pipx install "$1"; }
pipx_remove()		{ pipx uninstall "$1"; }

uv_rows()			{ uv tool list 2>/dev/null | awk '/^[^-[:space:]]/ {print $1 "\t" $2}'; }
uv_upgrade()		{ uv tool upgrade --all; }
uv_install()		{ uv tool install "$1"; }
uv_remove()			{ uv tool uninstall "$1"; }

conda_rows()		{ conda list 2>/dev/null | grep -v '^#' | awk '{print $1 "\t" $2}'; }
conda_outdated()	{ conda update --all --dry-run 2>&1 | sed -n '/package plan/,$p'; }
conda_upgrade()		{ conda update --all -y; }
conda_search()		{ conda search "*$1*"; }
conda_install()		{ conda install -y "$1"; }
conda_remove()		{ conda remove -y "$1"; }

# npm / gem: never escalate silently. When the install prefix is not writable, explain the safer
# user-level setup and use root only if the user explicitly agrees (tools are called by absolute path).
npm_run() {
	local root; root=$(npm root -g 2>/dev/null)
	if [[ -w "$root" ]]; then npm "$@"; return; fi
	confirm_root npm "npm config set prefix ~/.npm-global, then add ~/.npm-global/bin to PATH" || return 1
	as_root "$(command -v npm)" "$@"
}
npm_rows()			{ npm ls -g --depth=0 2>/dev/null | tail -n +2 | sed -E 's/^[^@[:alnum:]]*//; s/@([^@]*)$/\t\1/' | grep -P '\t' ; }
npm_outdated()		{ npm outdated -g 2>/dev/null; }
npm_upgrade()		{ npm_run update -g; }
npm_search()		{ npm search "$1"; }
npm_install()		{ npm_run install -g "$1"; }
npm_remove()		{ npm_run uninstall -g "$1"; }

yarn_rows()			{ yarn global list 2>/dev/null | sed -nE 's/^info "(.+)@([^@"]+)".*/\1\t\2/p'; }
yarn_upgrade()		{ yarn global upgrade; }
yarn_install()		{ yarn global add "$1"; }
yarn_remove()		{ yarn global remove "$1"; }

pnpm_rows()			{ pnpm ls -g --depth=0 2>/dev/null | awk 'NF == 2 && $1 !~ /^(Legend|dependencies:|devDependencies:)/ {print $1 "\t" $2}'; }
pnpm_outdated()		{ pnpm outdated -g 2>/dev/null; }
pnpm_upgrade()		{ pnpm update -g --latest; }
pnpm_search()		{ pnpm search "$1"; }
pnpm_install()		{ pnpm add -g "$1"; }
pnpm_remove()		{ pnpm remove -g "$1"; }

gem_run() {
	local dir; dir=$(gem env gemdir 2>/dev/null)
	if [[ -w "$dir" ]]; then gem "$@"; return; fi
	confirm_root gem "gem install --user-install, or set GEM_HOME=~/.gem and add ~/.gem/bin to PATH" || return 1
	as_root "$(command -v gem)" "$@"
}
gem_rows()			{ gem list --local 2>/dev/null | sed -E 's/^([^ ]+) \((default: )?([^,)]+).*/\1\t\3/'; }
gem_outdated()		{ gem outdated 2>/dev/null; }
gem_upgrade()		{ gem_run update; }
gem_search()		{ gem search "$1"; }
gem_install()		{ gem_run install "$1"; }
gem_remove()		{ gem_run uninstall "$1"; }

cargo_rows()		{ cargo install --list 2>/dev/null | sed -nE 's/^([^[:space:]]+) v([^ :]+).*/\1\t\2/p'; }
cargo_outdated()	{ if have cargo-install-update; then cargo install-update -l 2>/dev/null; else echo "  (install cargo-update for a precise check: cargo install cargo-update)"; fi; }
cargo_upgrade() {
	if have cargo-install-update; then
		cargo install-update -a
		return
	fi
	local -a crates; local c rc=0
	mapfile -t crates < <(cargo install --list 2>/dev/null | grep -E '^[^[:space:]]' | grep -vF '(' | awk '{print $1}')
	if (( ${#crates[@]} == 0 )); then echo -e "  ${DIM}No crates.io binaries installed.${RESET}"; return 0; fi
	echo -e "  ${DIM}cargo-update not found: reinstalling each crate (cargo install cargo-update makes this faster).${RESET}"
	for c in "${crates[@]}"; do cargo install "$c" || rc=1; done
	return $rc
}
cargo_search()		{ echo -e "  ${DIM}(cargo search relies on the crates.io API, results may be limited)${RESET}"; cargo search "$1"; }
cargo_install()		{ cargo install "$1"; }
cargo_remove()		{ cargo uninstall "$1"; }

rustup_rows()		{ rustup toolchain list 2>/dev/null | awk '{print $1}'; }
rustup_outdated()	{ rustup check 2>/dev/null; }
rustup_upgrade()	{ rustup update; }

composer_rows()		{ composer global show 2>/dev/null | awk 'NF >= 2 {print $1 "\t" $2}'; }
composer_outdated()	{ composer global outdated 2>/dev/null; }
composer_upgrade()	{ composer global update; }
composer_search()	{ composer search "$1"; }
composer_install()	{ composer global require "$1"; }
composer_remove()	{ composer global remove "$1"; }

# Table headers per manager
declare -A HEADER=(
	[system]=$'Package\tVersion'				[snap]=$'Name\tVersion\tNotes'
	[flatpak]=$'Application\tName\tVersion'		[brew]=$'Package\tVersion'
	[nix]=$'Package'							[appimage]=$'Path\tSize'
	[pip]=$'Package\tVersion'					[pipx]=$'Package\tVersion'
	[uv]=$'Tool\tVersion'						[conda]=$'Package\tVersion'
	[npm]=$'Package\tVersion'					[yarn]=$'Package\tVersion'
	[pnpm]=$'Package\tVersion'					[gem]=$'Gem\tVersion'
	[cargo]=$'Crate\tVersion'					[rustup]=$'Toolchain'
	[composer]=$'Package\tVersion'
)

# ──────────────────────────────────────────────────────────────────────────────
#  Manager selection
# ──────────────────────────────────────────────────────────────────────────────
# Resolve a name given on the command line into CHOSEN (optionally requiring capability $2)
resolve_manager() {
	local want="${1,,}" id
	CHOSEN=""
	case "$want" in
		pip3) want="pip" ;;
		homebrew) want="brew" ;;
		nix-env) want="nix" ;;
	esac
	[[ -n "$PM" && "$want" == "$PM" ]] && want="system"
	for id in "${MANAGERS[@]}"; do
		[[ "$id" == "$want" ]] || continue
		if [[ -z "${2:-}" ]] || cap "$id" "$2"; then CHOSEN="$id"; fi
		break
	done
	[[ -n "$CHOSEN" ]]
}

# Ask the user to pick one of the managers supporting capability $2
choose_manager() {
	local prompt="${1:-Choose the manager}" capab="${2:-}" id
	local -a ids=() labels=()
	CHOSEN=""
	for id in "${MANAGERS[@]}"; do
		if [[ -z "$capab" ]] || cap "$id" "$capab"; then ids+=("$id"); labels+=("${LABEL[$id]}"); fi
	done
	if (( ${#ids[@]} == 0 )); then msg_err "No manager available for this action."; return 1; fi
	select_menu "$prompt" "${labels[@]}" || return 1
	CHOSEN="${ids[$SELECTED]}"
}

# Use the manager named on the CLI if any, otherwise ask. $1=name $2=capability $3=prompt
pick_manager() {
	if [[ -n "$1" ]]; then
		resolve_manager "$1" "$2" || {
			msg_err "Manager '$1' is unknown, unavailable or doesn't support this action."
			return 1
		}
	else
		choose_manager "$3" "$2"
	fi
}

# ──────────────────────────────────────────────────────────────────────────────
#  Actions: list / count / check
# ──────────────────────────────────────────────────────────────────────────────
rows_of() { "${1}_rows" 2>/dev/null | awk 'NF'; }

# List one manager. If $FILTER is set, only matching rows (case-insensitive,
# whole line) are kept. With "quiet" as $2, managers without any match are hidden.
list_manager() {
	local id="$1" quiet="${2:-}"; local -a rows=()
	mapfile -t rows < <(rows_of "$id")
	if [[ -n "$FILTER" ]]; then
		local -a kept=(); local r
		for r in "${rows[@]}"; do
			[[ "${r,,}" == *"${FILTER,,}"* ]] && kept+=("$r")
		done
		rows=("${kept[@]}")
		[[ "$quiet" == quiet ]] && (( ${#rows[@]} == 0 )) && return 0
	fi
	section "${LABEL[$id]}${FILTER:+  (filter: $FILTER — ${#rows[@]} found)}"
	print_table "${HEADER[$id]}" rows
}

list_all() {
	local id
	{ for id in "${MANAGERS[@]}"; do list_manager "$id" quiet; done; } | pager
}

list_by_name() {
	local m="${1,,}"
	if [[ -z "$m" || "$m" == all ]]; then list_all; return; fi
	resolve_manager "$m" rows || { msg_err "Unknown or unavailable manager: $1"; return 1; }
	list_manager "$CHOSEN" | pager
}

choose_list_target() {
	local -a ids=(all) labels=("All") ; local id
	for id in "${MANAGERS[@]}"; do ids+=("$id"); labels+=("${LABEL[$id]}"); done
	select_menu "Which manager do you want to list?" "${labels[@]}" || return 1
	CHOSEN="${ids[$SELECTED]}"
}

count_totals() {
	if (( STALE )); then
		local id n
		spin_start "Counting installed packages..."
		COUNT_ROWS=()
		for id in "${MANAGERS[@]}"; do
			n=$(rows_of "$id" | wc -l); n=${n//[[:space:]]/}
			COUNT_ROWS+=("${LABEL[$id]}"$'\t'"$n")
		done
		spin_stop
		STALE=0
	fi
	print_table $'Manager\tInstalled' COUNT_ROWS
}

check_updates() {
	local id
	echo -e "${YELLOW}🔄 Checking for updates...${RESET}"
	for id in "${MANAGERS[@]}"; do
		cap "$id" upgrade || continue
		section "${LABEL[$id]}"
		if cap "$id" outdated; then
			"${id}_outdated" 2>/dev/null | indent_or_ok
		else
			echo -e "  ${DIM}(no dry-run check available; the upgrade step handles it)${RESET}"
		fi
	done
}

# ──────────────────────────────────────────────────────────────────────────────
#  Actions: upgrade
# ──────────────────────────────────────────────────────────────────────────────
# Run one manager's upgrade and record the result (0 = ok, 2 = skipped, other = failed)
upgrade_run() {
	local id="$1" rc
	section "${LABEL[$id]}"
	"${id}_upgrade"; rc=$?
	case $rc in
		0) RESULTS+=("${LABEL[$id]}"$'\t'"✔ Upgraded") ;;
		2) RESULTS+=("${LABEL[$id]}"$'\t'"○ Skipped") ;;
		*) RESULTS+=("${LABEL[$id]}"$'\t'"✗ Failed") ;;
	esac
	return $rc
}

reboot_notice() {
	if [[ -f /var/run/reboot-required ]]; then
		echo -e "  ${YELLOW}${BOLD}⚠ A reboot is required to finish applying the updates.${RESET}\n"
	fi
}

update_all() {
	local id; local -a targets=()
	for id in "${MANAGERS[@]}"; do cap "$id" upgrade && targets+=("$id"); done
	if (( ${#targets[@]} == 0 )); then msg_err "Nothing to update."; return 1; fi
	echo -e "${YELLOW}Full system update...${RESET}\n"
	echo -e "${RED}${BOLD}  sudo privileges may be required.${RESET}\n"
	echo "  Managers that will be updated:"
	for id in "${targets[@]}"; do echo -e "  ${CYAN}•${RESET} ${LABEL[$id]}"; done
	echo
	confirm "Confirm the global update?" || { echo "  Cancelled."; return 0; }
	prime_sudo
	RESULTS=()
	local failed=0
	for id in "${targets[@]}"; do
		upgrade_run "$id"
		(( $? == 1 )) && failed=1
	done
	STALE=1
	section "Summary"
	print_table $'Manager\tResult' RESULTS
	reboot_notice
	if (( failed )); then
		echo -e "  ${RED}${BOLD}Some updates failed, see the summary above.${RESET}"
		return 1
	fi
	echo -e "  ${GREEN}${BOLD}All updates are complete.${RESET}"
}

update_selective() {
	echo -e "${YELLOW}Selective update${RESET}\n"
	if [[ -n "${1:-}" ]]; then
		resolve_manager "$1" upgrade || { msg_err "Manager '$1' is unknown, unavailable or can't be upgraded."; return 1; }
	else
		choose_manager "Which manager do you want to update?" upgrade || return 1
	fi
	local id="$CHOSEN" rc
	if [[ "$id" == system ]]; then
		confirm "Update the system packages?" || { echo "  Cancelled."; return 0; }
	fi
	prime_sudo
	RESULTS=()
	upgrade_run "$id"; rc=$?
	STALE=1
	reboot_notice
	if (( rc == 0 || rc == 2 )); then echo -e "\n  ${GREEN}Done.${RESET}"; else echo -e "\n  ${RED}Update failed.${RESET}"; return 1; fi
}

# ──────────────────────────────────────────────────────────────────────────────
#  Actions: search / install / remove / export
# ──────────────────────────────────────────────────────────────────────────────
search_app() {
	local pkg="${1:-}"
	[[ -n "$pkg" ]] || read -rp "  Name to search for: " pkg
	[[ -n "$pkg" ]] || { msg_err "Empty name, search cancelled."; return 1; }
	valid_query "$pkg" || { msg_err "Invalid search text (it must not start with '-' or contain control characters)."; return 1; }
	pick_manager "${2:-}" search "In which manager?" || return 1
	"${CHOSEN}_search" "$pkg" | pager
}

install_app() {
	local pkg="${1:-}" rc
	[[ -n "$pkg" ]] || read -rp "  Name of the package to install: " pkg
	[[ -n "$pkg" ]] || { msg_err "Empty name, installation cancelled."; return 1; }
	valid_pkg "$pkg" || { bad_pkg; return 1; }
	pick_manager "${2:-}" install "Via which manager?" || return 1
	"${CHOSEN}_install" "$pkg"; rc=$?
	STALE=1
	return $rc
}

remove_app() {
	local pkg="${1:-}" rc
	[[ -n "$pkg" ]] || read -rp "  Name of the package to remove: " pkg
	[[ -n "$pkg" ]] || { msg_err "Empty name, removal cancelled."; return 1; }
	valid_pkg "$pkg" || { bad_pkg; return 1; }
	pick_manager "${2:-}" remove "Via which manager?" || return 1
	echo -e "  ${RED}Removing: ${BOLD}$pkg${RESET}"
	confirm "Confirm?" || { echo "  Cancelled."; return 0; }
	"${CHOSEN}_remove" "$pkg"; rc=$?
	STALE=1
	return $rc
}

export_list() {
	local dir file id
	dir="${XDG_STATE_HOME:-$HOME/.local/state}/app-manager"
	mkdir -p "$dir" && chmod 700 "$dir" || { msg_err "Cannot create $dir"; return 1; }
	file="$dir/apps_$(uname -n)_$(date +%Y%m%d_%H%M%S).txt"
	echo -e "${YELLOW}Exporting to ${BOLD}$file${RESET}...\n"
	(
		umask 077           # the list reveals every installed version: keep it private
		set -o noclobber    # never overwrite (or follow a symlink to) an existing file
		{
			echo "=========================================="
			echo "  Applications installed on $(uname -n)"
			echo "  Date: $(date)"
			echo "=========================================="
			for id in "${MANAGERS[@]}"; do
				printf '\n── %s ──────────────────────────\n' "${LABEL[$id]}"
				rows_of "$id" | awk -F'\t' '{ printf "%-45s %s\n", $1, $2 }'
			done
		} > "$file"
	)
	if [[ -s "$file" ]]; then
		echo -e "  ${GREEN}Exported: ${BOLD}$file${RESET}"
	else
		msg_err "Export failed (is $dir writable?)."
		return 1
	fi
}

# ──────────────────────────────────────────────────────────────────────────────
#  Interactive menu
# ──────────────────────────────────────────────────────────────────────────────
menu() {
	local -a main_options=(
		"List all applications"
		"Search for an application"
		"Check for updates"
		"Update EVERYTHING"
		"Update a specific manager"
		"Install an application"
		"Remove an application"
		"Export the full list to a text file"
		"Detect managers & tools"
		"Quit"
	)
	while true; do
		drop_sudo
		clear
		banner "MyApp Console v${VERSION} — Linux Application Manager" "Detect, list, search, install, remove & upgrade everything"
		root_warning
		show_managers
		count_totals
		select_menu "What would you like to do?" "${main_options[@]}" || exit 1
		echo
		case "$SELECTED" in
			0) if choose_list_target; then
				   read -rp "  Filter (Enter = show everything): " FILTER
				   list_by_name "$CHOSEN"
				   FILTER=""
			   fi;												pause ;;
			1) search_app;										pause ;;
			2) prime_sudo; check_updates | pager;				pause ;;
			3) update_all;										pause ;;
			4) update_selective;								pause ;;
			5) install_app;										pause ;;
			6) remove_app;										pause ;;
			7) export_list;										pause ;;
			8) show_detection;									pause ;;
			9) echo -e "  ${GREEN}See you soon!${RESET}\n";		exit 0 ;;
		esac
	done
}

# ──────────────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────────────
usage() {
	cat <<EOF
    Linux Application Manager v${VERSION} — CLI usage
    Without any option, the interactive menu is shown.
    Every action available in the menu can also be triggered directly:

        -d, --detect                Detect package managers and tools
        -l, --list [MANAGER]        List apps. MANAGER is optional:
                                    system|snap|flatpak|brew|nix|appimage|pip|pipx|uv|
                                    conda|npm|yarn|pnpm|gem|cargo|rustup|composer
                                    (default: all)
        -f, --filter TEXT           Only show entries containing TEXT when listing
                                    (case-insensitive, combine with -l MANAGER)
        -c, --check-updates         Check for available updates (refreshes package indexes, installs nothing)
        -U, --update-all            Update everything (asks to confirm unless -y)
        -m, --update-manager MGR    Update a single manager
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
        ./App-manager.sh --detect
        ./App-manager.sh --list snap
        ./App-manager.sh --list snap --filter code
        ./App-manager.sh -f python
        ./App-manager.sh --search vlc --manager flatpak
        ./App-manager.sh --install htop --manager system -y
        ./App-manager.sh --update-manager npm
        ./App-manager.sh --update-all --yes
EOF
}

need_arg() {
	if [[ $# -lt 2 || "$2" == -* ]]; then
		echo -e "${RED}Option $1 requires an argument.${RESET}"
		BAD_ARGS=true
		return 1
	fi
}

main() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
			-l|--list)
				DO_LIST=true
				if [[ -n "${2:-}" && "$2" != -* ]]; then LIST_MANAGER="$2"; shift; fi ;;
			-f|--filter)				need_arg "$@" || break; FILTER="$2"; DO_LIST=true; shift ;;
			-d|--detect)				DO_DETECT=true ;;
			-c|--check-updates)			DO_CHECK=true ;;
			-U|-u|--update-all)			DO_UPDATE_ALL=true ;;
			-m|-um|--update-manager)	need_arg "$@" || break; UPDATE_MANAGER="$2"; shift ;;
			-s|--search)				need_arg "$@" || break; SEARCH_PKG="$2"; shift ;;
			-i|--install)				need_arg "$@" || break; INSTALL_PKG="$2"; shift ;;
			-r|--remove)				need_arg "$@" || break; REMOVE_PKG="$2"; shift ;;
			--manager)					need_arg "$@" || break; ACTION_MANAGER="$2"; shift ;;
			-e|--export)				DO_EXPORT=true ;;
			-y|--yes)					AUTO_YES=true ;;
			-v|--version)				echo "App Manager v${VERSION}"; exit 0 ;;
			-h|--help)					SHOW_HELP=true ;;
			*) echo -e "${RED}Unknown option: $1${RESET}"; BAD_ARGS=true ;;
		esac
		shift
	done
	if $SHOW_HELP; then usage; exit 0; fi
	if $BAD_ARGS;  then usage; exit 1; fi

	# Run from a neutral directory: cargo, npm... read config files found in the current directory
	cd "${HOME:-/}" 2>/dev/null || cd /

	detect_managers
	root_warning

	# Any action flag switches the script to non-interactive mode
	if $DO_DETECT || $DO_LIST || $DO_CHECK || $DO_UPDATE_ALL || $DO_EXPORT \
		|| [[ -n "$UPDATE_MANAGER$SEARCH_PKG$INSTALL_PKG$REMOVE_PKG" ]]; then
		local status=0
		$DO_DETECT && show_detection
		$DO_LIST   && { list_by_name "$LIST_MANAGER" || status=1; }
		$DO_CHECK  && { prime_sudo; check_updates | pager; }
		$DO_UPDATE_ALL && { update_all || status=1; }
		[[ -n "$UPDATE_MANAGER" ]] && { update_selective "$UPDATE_MANAGER" || status=1; }
		[[ -n "$SEARCH_PKG"  ]] && { search_app  "$SEARCH_PKG"  "$ACTION_MANAGER" || status=1; }
		[[ -n "$INSTALL_PKG" ]] && { install_app "$INSTALL_PKG" "$ACTION_MANAGER" || status=1; }
		[[ -n "$REMOVE_PKG"  ]] && { remove_app  "$REMOVE_PKG"  "$ACTION_MANAGER" || status=1; }
		$DO_EXPORT && { export_list || status=1; }
		exit $status
	fi

	# No action flag: interactive menu (needs a terminal)
	if [[ ! -t 0 || ! -t 1 ]]; then usage; exit 1; fi
	menu
}

main "$@"
