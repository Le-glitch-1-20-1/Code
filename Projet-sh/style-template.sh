#!/usr/bin/env bash
# NAME — one-line description of what the script does.
# Copy this file, rename it, then edit everything OUTSIDE the STYLE block.
set -o pipefail

VERSION="1.0.0"
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
AUTO_YES=false
DO_DEMO=false
BAD_ARGS=false

trap ui_restore EXIT
trap 'echo -e "${RESET}\n  ${YELLOW}Interrupted.${RESET}"; exit 130' INT

# ──────────────────────────────────────────────────────────────────────────────
#  Actions (replace with your own)
# ──────────────────────────────────────────────────────────────────────────────
demo_messages() {
	section "Messages"
	msg_ok   "Success message"
	msg_info "Information message"
	msg_warn "Warning message"
	msg_dim  "Secondary / hint message"
	msg_err  "Error message (stderr)"
	kv "Key" "value"
	item_ok "tool" "/usr/bin/tool" "1.2.3"
}

demo_table() {
	local -a rows=($'alpha\t1.0' $'beta\t2.3')
	section "Table"
	print_table $'Name\tVersion' rows
}

demo_task() {
	section "Task"
	run_task "Doing something slow" sleep 2
}

demo_confirm() {
	section "Confirmation"
	if confirm "Do you want to continue?"; then msg_ok "Confirmed"; else msg_warn "Cancelled"; fi
}

demo_checkbox() {
	section "Multi-choice"
	checkbox_menu "Pick some items:" "Item A" "Item B" "Item C" || return 1
	echo "  Indices: ${SELECTED_IDX[*]:-none}"
}

# ──────────────────────────────────────────────────────────────────────────────
#  Interactive menu
# ──────────────────────────────────────────────────────────────────────────────
menu() {
	while true; do
		[[ -t 1 ]] && clear
		banner "NAME v${VERSION}" "One-line description"
		select_menu "What would you like to do?" \
			"Show messages" \
			"Show a table" \
			"Run a task" \
			"Ask for confirmation" \
			"Pick several items" \
			"$SEP" \
			"Quit" || exit 1
		echo
		case "$SELECTED" in
			0) demo_messages;  pause ;;
			1) demo_table;     pause ;;
			2) demo_task;      pause ;;
			3) demo_confirm;   pause ;;
			4) demo_checkbox;  pause ;;
			6) echo -e "  ${GREEN}See you soon!${RESET}\n"; exit 0 ;;
		esac
	done
}

# ──────────────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────────────
usage() {
	cat <<EOF
    NAME v${VERSION} — CLI usage
    Without any option, the interactive menu is shown.

        -d, --demo                  Run every demo without the menu
        -y, --yes                   Auto-confirm any prompt (non-interactive)
        -v, --version               Show the program version and exit
        -h, --help                  Show this help

    Examples:
        ./name.sh
        ./name.sh --demo --yes
EOF
}

# Usage inside the parser: need_arg "$@" || break   (option that takes a value)
need_arg() {
	if [[ $# -lt 2 || "$2" == -* ]]; then
		msg_err "Option $1 requires an argument."
		BAD_ARGS=true
		return 1
	fi
}

main() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
			-d|--demo)		DO_DEMO=true ;;
			-y|--yes)		AUTO_YES=true ;;
			-v|--version)	echo "NAME v${VERSION}"; exit 0 ;;
			-h|--help)		usage; exit 0 ;;
			*)				msg_err "Unknown option: $1"; BAD_ARGS=true ;;
		esac
		shift
	done
	if $BAD_ARGS; then usage; exit 1; fi

	# Any action flag switches the script to non-interactive mode
	if $DO_DEMO; then
		demo_messages; demo_table; demo_task; demo_confirm
		exit 0
	fi

	# No action flag: interactive menu (needs a terminal)
	if [[ ! -t 0 || ! -t 1 ]]; then usage; exit 1; fi
	menu
}

main "$@"
