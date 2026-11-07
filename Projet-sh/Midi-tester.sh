#!/usr/bin/env bash
# MIDI Tester — Linux
# Listens to ALSA MIDI ports and prints the received messages live.
# The exit code of a pipeline is the last command that failed, not just the last one
set -o pipefail

VERSION="2.1.0"
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
SELECTED_PORTS=()			# ports given on the CLI or picked in the menu
LIST_ONLY=false
NONINTERACTIVE=false
BAD_ARGS=false
MISSING=0
CLIENT_NUM=""
CLIENT_NAME=""
# Note names used to turn a MIDI note number into a readable name
NOTE_NAMES=("C" "C#" "D" "D#" "E" "F" "F#" "G" "G#" "A" "A#" "B")
# Detected ports and their human-readable names, filled by detect_ports
declare -a ALL_PORTS=()
declare -A PORT_NAMES=()

trap ui_restore EXIT
trap 'echo -e "${RESET}\n  ${YELLOW}Stopping listening.${RESET}"; exit 0' INT

# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────
# Turn a MIDI note number into a readable note name + octave (result in $REPLY, no subshell)
note_name() {
	local n=$((10#$1))
	REPLY="${NOTE_NAMES[n % 12]}$((n / 12 - 1))"
}

# Device names come from the hardware and are printed later with echo -e:
# strip control characters and backslashes (result in $REPLY)
clean_name() {
	local s="${1//[^[:print:]]/}"
	REPLY="${s//\\/}"
}

# Check required tools and shell features, exit early if something is missing
check_dependencies() {
	local cmd
	for cmd in aseqdump aconnect; do
		if ! have "$cmd"; then
			msg_err "'$cmd' is not installed."
			MISSING=1
		fi
	done
	if (( MISSING )); then
		echo -e "\n  Install the missing tools with:"
		echo -e "  ${CYAN}sudo apt install alsa-utils${RESET}\n"
		exit 1
	fi
	if ! echo "test123" | grep -qP "\d" 2>/dev/null; then
		msg_err "Your version of 'grep' does not support Perl regex (-P)."
		echo -e "  Install GNU grep: ${CYAN}sudo apt install grep${RESET}\n"
		exit 1
	fi
	if ! groups | grep -qw audio; then
		msg_warn "You are not in the 'audio' group. If no device is detected, run:"
		echo -e "  ${CYAN}sudo usermod -aG audio \$USER${RESET}  then log out and back in.\n"
	fi
}

# ──────────────────────────────────────────────────────────────────────────────
#  Detection
# ──────────────────────────────────────────────────────────────────────────────
# Parse "aconnect -l" output, fill ALL_PORTS / PORT_NAMES, print each port found
detect_ports() {
	local line KEY PORT_NUM PORT_NAME
	section "Detected devices"
	while IFS= read -r line; do
		if echo "$line" | grep -qE "^client [0-9]+:"; then
			CLIENT_NUM=$(echo "$line" | grep -oP "^client \K[0-9]+")
			CLIENT_NAME=$(echo "$line" | grep -oP "'\K[^']+" | head -1)
			# Skip the ALSA system clients (0 = System, 14 = Midi Through, >=128 = software)
			if [ "$CLIENT_NUM" -eq 0 ] || [ "$CLIENT_NUM" -eq 14 ] || [ "$CLIENT_NUM" -ge 128 ]; then
				CLIENT_NUM=""
			fi
		elif [ -n "$CLIENT_NUM" ] && echo "$line" | grep -qP "^\s+[0-9]+ '"; then
			PORT_NUM=$(echo "$line" | grep -oP "^\s+\K[0-9]+")
			PORT_NAME=$(echo "$line" | grep -oP "'\K[^']+" | head -1)
			clean_name "$CLIENT_NAME"; CLIENT_NAME="$REPLY"
			clean_name "$PORT_NAME"; PORT_NAME="$REPLY"
			KEY="${CLIENT_NUM}:${PORT_NUM}"
			ALL_PORTS+=("$KEY")
			PORT_NAMES["$KEY"]="$CLIENT_NAME / $PORT_NAME"
			item_ok "$KEY" "$CLIENT_NAME → $PORT_NAME"
		fi
	done < <(aconnect -l 2>/dev/null)
	(( ${#ALL_PORTS[@]} )) || msg_dim "(none)"
	echo
}

# ──────────────────────────────────────────────────────────────────────────────
#  Interactive menus
# ──────────────────────────────────────────────────────────────────────────────
# Let the user pick one or more detected ports, filling SELECTED_PORTS
choose_ports_interactive() {
	local -a labels=()
	local key i
	for key in "${ALL_PORTS[@]}"; do
		labels+=("$key  ${PORT_NAMES[$key]}")
	done
	while true; do
		checkbox_menu "Select port(s):" "${labels[@]}" || exit 1
		echo
		(( ${#SELECTED_IDX[@]} )) && break
		msg_warn "No port selected (press space to check a box, then enter)."
		msg_dim "Press any key to try again..."
		read -rsn1
	done
	SELECTED_PORTS=()
	for i in "${SELECTED_IDX[@]}"; do
		SELECTED_PORTS+=("${ALL_PORTS[$i]}")
	done
}

# Menu shown when the script is run without any CLI flag
show_menu() {
	select_menu "What would you like to do?" \
		"Listen to all detected ports" \
		"Choose specific port(s) to listen to" \
		"Just list the ports, then exit" \
		"$SEP" \
		"Quit" || exit 1
	echo
	case "$SELECTED" in
		0) SELECTED_PORTS=() ;;
		1) choose_ports_interactive ;;
		2) LIST_ONLY=true ;;
		4) echo -e "  ${GREEN}See you soon!${RESET}\n"; exit 0 ;;
	esac
}

# ──────────────────────────────────────────────────────────────────────────────
#  Listening
# ──────────────────────────────────────────────────────────────────────────────
# Format and print one line coming from aseqdump.
# Pure bash (regex + printf): no subprocess per event, so fast MIDI streams do not lag.
print_event() {
	local line="$1" lc src rest pname ch_txt="" note="" vel="" ctrl="" val="" prog=""
	local re_src='^[[:space:]]*([0-9]+:[0-9]+)[[:space:]]+(.*)$'
	local re_ch='[^0-9]([0-9]+),'
	local re_note='note ([0-9]+)' re_vel='velocity ([0-9]+)' re_ctrl='controller ([0-9]+)'
	local re_val='value (-?[0-9]+)' re_prog='program ([0-9]+)'
	[[ "$line" =~ $re_src ]] || return
	src="${BASH_REMATCH[1]}"; rest="${BASH_REMATCH[2]}"
	lc="${rest,,}"
	pname="${PORT_NAMES[$src]:-$src}"; pname="${pname:0:28}"
	[[ "$rest" =~ $re_ch ]] && ch_txt=" (ch ${BASH_REMATCH[1]})"
	case "$lc" in
		*"note on"*)
			[[ "$lc" =~ $re_note ]] || return
			note="${BASH_REMATCH[1]}"
			[[ "$lc" =~ $re_vel ]] && vel="${BASH_REMATCH[1]}"
			note_name "$note"
			if [[ "$vel" == 0 ]]; then
				printf "  %-8s %-28s %-12s %-10s %s\n" "$src" "$pname" "Note OFF" "" "$REPLY$ch_txt"
				return
			fi
			printf "  ${GREEN}%-8s${RESET} %-28s ${BOLD}%-12s${RESET} %-10s %s\n" "$src" "$pname" "Note ON" "vel=$vel" "$REPLY (MIDI $note)$ch_txt" ;;
		*"note off"*)
			[[ "$lc" =~ $re_note ]] || return
			note_name "${BASH_REMATCH[1]}"
			printf "  %-8s %-28s %-12s %-10s %s\n" "$src" "$pname" "Note OFF" "" "$REPLY$ch_txt" ;;
		*"control change"*)
			[[ "$lc" =~ $re_ctrl ]] || return
			ctrl="${BASH_REMATCH[1]}"
			[[ "$lc" =~ $re_val ]] && val="${BASH_REMATCH[1]}"
			printf "  ${YELLOW}%-8s${RESET} %-28s ${YELLOW}%-12s${RESET} %-10s %s\n" "$src" "$pname" "CC" "val=$val" "Controller #$ctrl$ch_txt" ;;
		*"program change"*)
			[[ "$lc" =~ $re_prog ]] && prog="${BASH_REMATCH[1]}"
			printf "  ${CYAN}%-8s${RESET} %-28s ${CYAN}%-12s${RESET} %s\n" "$src" "$pname" "Prog CH" "#$prog$ch_txt" ;;
		*"pitch bend"*)
			[[ "$lc" =~ $re_val ]] && val="${BASH_REMATCH[1]}"
			printf "  ${CYAN}%-8s${RESET} %-28s ${CYAN}%-12s${RESET} %s\n" "$src" "$pname" "Pitch" "$val$ch_txt" ;;
		*"channel pressure"*|*aftertouch*)
			[[ "$lc" =~ $re_val ]] && val="${BASH_REMATCH[1]}"
			printf "  ${CYAN}%-8s${RESET} %-28s ${CYAN}%-12s${RESET} %s\n" "$src" "$pname" "Aftertouch" "val=$val$ch_txt" ;;
		*sysex*|*"system exclusive"*)
			printf "  %-8s %-28s %-12s\n" "$src" "$pname" "SysEx" ;;
	esac
}

# Build the port list to listen on, print the header, then stream formatted events until Ctrl+C
listen_and_print() {
	local PORTS_ARG rc line
	section "Listening"
	if [ ${#SELECTED_PORTS[@]} -gt 0 ]; then
		PORTS_ARG=$(IFS=,; echo "${SELECTED_PORTS[*]}")
		msg_ok "Listening on selected port(s): $PORTS_ARG"
	else
		PORTS_ARG=$(IFS=,; echo "${ALL_PORTS[*]}")
		msg_ok "${#ALL_PORTS[@]} port(s) found — listening..."
	fi
	msg_dim "Press keys, pads, buttons — Ctrl+C to quit."
	echo
	printf "  ${BOLD}${CYAN}%-8s %-28s %-12s %-10s %s${RESET}\n" "PORT" "DEVICE / PORT" "TYPE" "VALUE" "DETAIL"
	echo -e "  ${DIM}$(rep '─' 68)${RESET}"
	aseqdump -p "$PORTS_ARG" | while IFS= read -r line; do
		print_event "$line"
	done
	rc=${PIPESTATUS[0]}
	if (( rc != 0 )); then
		msg_err "aseqdump stopped with an error (invalid port or missing permission?)."
		return 1
	fi
}

# ──────────────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────────────
usage() {
	cat <<EOF
    MIDI Tester v${VERSION} — CLI usage
    Without any option, the interactive menu is shown.

        -p, --port CLIENT:PORT      Listen only on this port (repeatable)
        -l, --list                  Just list detected devices/ports, then exit
        -v, --version               Show the program version and exit
        -h, --help                  Show this help

    Examples:
        ./Midi-tester.sh
        ./Midi-tester.sh --list
        ./Midi-tester.sh --port 20:0
        ./Midi-tester.sh -p 20:0 -p 24:0
EOF
}

need_arg() {
	if [[ $# -lt 2 || "$2" == -* ]]; then
		msg_err "Option $1 requires an argument."
		BAD_ARGS=true
		return 1
	fi
}

# Entry point: parse CLI arguments, detect devices, then listen non-interactively or via the menu
main() {
	local p
	while [[ $# -gt 0 ]]; do
		case "$1" in
			-p|--port)		need_arg "$@" || break; SELECTED_PORTS+=("$2"); shift ;;
			-l|--list)		LIST_ONLY=true ;;
			-v|--version)	echo "MIDI Tester v${VERSION}"; exit 0 ;;
			-h|--help)		usage; exit 0 ;;
			*)				msg_err "Unknown option: $1"; BAD_ARGS=true ;;
		esac
		shift
	done
	if $BAD_ARGS; then usage; exit 1; fi

	# Validate any port given on the CLI
	for p in "${SELECTED_PORTS[@]}"; do
		[[ "$p" =~ ^[0-9]+:[0-9]+$ ]] || die "Invalid port format: '$p' (expected CLIENT:PORT, e.g. 20:0)"
	done

	# Any CLI flag switches the script to non-interactive mode (menu is skipped)
	if $LIST_ONLY || [ ${#SELECTED_PORTS[@]} -gt 0 ]; then
		NONINTERACTIVE=true
	fi
	# No flag and no terminal: the menu cannot work
	if ! $NONINTERACTIVE && [[ ! -t 0 || ! -t 1 ]]; then usage; exit 1; fi

	[[ -t 1 ]] && clear
	banner "MIDI Tester - Linux  v${VERSION}" "ALSA MIDI listener for Linux"
	check_dependencies
	detect_ports

	# A port given on the CLI must exist in the detected list (virtual ports are still allowed)
	for p in "${SELECTED_PORTS[@]}"; do
		[[ -n "${PORT_NAMES[$p]+x}" ]] || msg_warn "Port $p is not in the detected list (listening anyway)."
	done

	if [ ${#ALL_PORTS[@]} -eq 0 ] && [ ${#SELECTED_PORTS[@]} -eq 0 ]; then
		msg_err "No MIDI device found."
		echo
		echo -e "  Check that your device is plugged in, then try:"
		echo -e "  ${CYAN}aconnect -l${RESET}        — lists all MIDI clients"
		echo -e "  ${CYAN}amidi -l${RESET}           — lists raw MIDI ports"
		echo
		echo -e "  If your device doesn't show up at all:"
		echo -e "  ${CYAN}lsusb${RESET}              — check that Linux recognizes it"
		echo -e "  ${CYAN}dmesg | tail -20${RESET}   — look for errors when plugging it in"
		exit 1
	fi

	# No CLI flag given: interactive menu (list all / choose ports / list only / quit)
	$NONINTERACTIVE || show_menu
	$LIST_ONLY && exit 0
	listen_and_print
}

main "$@"
