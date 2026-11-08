#!/usr/bin/env bash
# MIDI Tester - listens to ALSA MIDI ports and prints the received messages live (Linux only).
# The exit code of a pipeline is the last command that failed, not just the last one
set -o pipefail

VERSION="3.0.0"
readonly VERSION

# >>> STYLE BEGIN v2.0 - shared console style, keep this block identical in every script >>>
# Reference: STYLE-GUIDE.md. Portable: bash >= 4.0 on Linux, macOS, BSD, WSL, Git Bash, Termux.
# Degrades gracefully: ASCII symbols without UTF-8, plain text without colors, numbered
# menus without a capable terminal. No external dependency except coreutils-like basics.

# ── Shell version guard (must stay first: nothing below may use bash 4+ syntax before it) ──
if (( BASH_VERSINFO[0] < 4 )); then
	if [[ -z "${_STYLE_REEXEC:-}" ]]; then
		# macOS ships bash 3.2: use a newer bash from a well-known location if there is one
		for _b in /opt/homebrew/bin/bash /usr/local/bin/bash /opt/local/bin/bash /usr/pkg/bin/bash; do
			[[ -x "$_b" ]] && _STYLE_REEXEC=1 exec "$_b" "$0" "$@"
		done
	fi
	printf 'This script needs bash 4.0 or newer (found %s).\n' "$BASH_VERSION" >&2
	printf 'macOS: run "brew install bash". Other systems: install a recent bash package.\n' >&2
	exit 1
fi
unset _b _STYLE_REEXEC

# ── Safe environment ─────────────────────────────────────────────────────────
IFS=$' \t\n'

# Drop empty and relative entries from PATH (a "." or "::" would run programs from the
# current directory), and unset CDPATH (it silently changes what "cd" does).
harden_env() {
	local -a parts=()
	local p out=""
	IFS=: read -ra parts <<< "$PATH"
	for p in "${parts[@]}"; do
		[[ "$p" == /* ]] && out+="${out:+:}$p"
	done
	PATH="${out:-/usr/local/bin:/usr/bin:/bin}"
	unset CDPATH
}
harden_env

# ── Capabilities: UTF-8, terminal, colors ────────────────────────────────────
# Without a UTF-8 locale ${#var} counts bytes and boxes/tables break: try to switch to one,
# otherwise fall back to ASCII symbols.
_utf8_locale() {
	local cm
	if command -v locale >/dev/null 2>&1; then
		cm=$(locale charmap 2>/dev/null)
	else
		cm="${LC_ALL:-${LC_CTYPE:-${LANG:-}}}"
	fi
	case "$cm" in *[Uu][Tt][Ff]-8*|*[Uu][Tt][Ff]8*) return 0 ;; esac
	return 1
}

UI_UTF8=false
if _utf8_locale; then
	UI_UTF8=true
elif command -v locale >/dev/null 2>&1; then
	_avail=$'\n'"$(locale -a 2>/dev/null)"$'\n'
	for _c in C.UTF-8 C.utf8 en_US.UTF-8 en_US.utf8; do
		if [[ "$_avail" == *$'\n'"$_c"$'\n'* ]]; then
			export LC_ALL="$_c"
			_utf8_locale && UI_UTF8=true
			break
		fi
	done
	unset _avail _c
fi

# Terminal control sequences are only used when TERM is set and not "dumb"
UI_TERM=false
[[ -n "${TERM:-}" && "$TERM" != dumb ]] && UI_TERM=true

# Colors: off when the stream is not a terminal, TERM is dumb or NO_COLOR is set.
# stdout and stderr are checked separately so redirecting one never leaks escape codes.
_color_ok() { [[ -z "${NO_COLOR:-}" ]] && $UI_TERM; }
if [[ -t 1 ]] && _color_ok; then
	RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; CYAN=$'\033[0;36m'
	MAGENTA=$'\033[0;35m'; BOLD=$'\033[1m'; DIM=$'\033[2m'; RESET=$'\033[0m'
else
	RED=''; GREEN=''; YELLOW=''; CYAN=''; MAGENTA=''; BOLD=''; DIM=''; RESET=''
fi
if [[ -t 2 ]] && _color_ok; then
	E_RED=$'\033[0;31m'; E_RESET=$'\033[0m'
else
	E_RED=''; E_RESET=''
fi
if [[ -t 1 ]] && $UI_TERM; then
	HIDE_CURSOR=$'\033[?25l'; SHOW_CURSOR=$'\033[?25h'
else
	HIDE_CURSOR=''; SHOW_CURSOR=''
fi

# Symbols (Unicode when possible, ASCII otherwise)
if $UI_UTF8; then
	SYM_OK='✔'; SYM_ERR='✗'; SYM_WARN='⚠'; SYM_INFO='•'; SYM_ASK='?'; SYM_SEL='»'
	SYM_SKIP='○'; SYM_ARROW='→'; SYM_DOT='…'
	BX_TL='╭'; BX_TR='╮'; BX_BL='╰'; BX_BR='╯'; BX_V='│'; BX_H='─'
	TB_TL='┌'; TB_TM='┬'; TB_TR='┐'; TB_ML='├'; TB_MM='┼'; TB_MR='┤'
	TB_BL='└'; TB_BM='┴'; TB_BR='┘'; TB_V='│'; TB_H='─'
	SPIN_FRAMES='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
else
	SYM_OK='+'; SYM_ERR='x'; SYM_WARN='!'; SYM_INFO='*'; SYM_ASK='?'; SYM_SEL='>'
	SYM_SKIP='-'; SYM_ARROW='->'; SYM_DOT='...'
	BX_TL='+'; BX_TR='+'; BX_BL='+'; BX_BR='+'; BX_V='|'; BX_H='-'
	TB_TL='+'; TB_TM='+'; TB_TR='+'; TB_ML='+'; TB_MM='+'; TB_MR='+'
	TB_BL='+'; TB_BM='+'; TB_BR='+'; TB_V='|'; TB_H='-'
	SPIN_FRAMES='|/-\'
fi
readonly RED GREEN YELLOW CYAN MAGENTA BOLD DIM RESET E_RED E_RESET HIDE_CURSOR SHOW_CURSOR
readonly SYM_OK SYM_ERR SYM_WARN SYM_INFO SYM_ASK SYM_SEL SYM_SKIP SYM_ARROW SYM_DOT
readonly BX_TL BX_TR BX_BL BX_BR BX_V BX_H TB_TL TB_TM TB_TR TB_ML TB_MM TB_MR TB_BL TB_BM TB_BR TB_V TB_H
readonly SPIN_FRAMES

# Pass "$SEP" as an option of select_menu to draw a non-selectable divider line
readonly SEP="---sep---"

# ── Small helpers ────────────────────────────────────────────────────────────
have() { command -v "$1" >/dev/null 2>&1; }

# True when both stdin and stdout are terminals (prompts can be answered)
ui_interactive() { [[ -t 0 && -t 1 ]]; }
# True when arrow-key menus, spinners and cursor control can be used
ui_fancy() { $UI_TERM && [[ -t 0 && -t 1 ]]; }

# Untrusted text (device names, package descriptions, user input) must never reach the
# terminal with its control characters: an ESC sequence could rewrite the screen.
# clean "text"  -> result in $REPLY (strips ESC, CR, BEL, TAB... no subshell)
clean() { REPLY=${1//[[:cntrl:]]/}; }
# sanitize      -> filter for external command output: drops control characters except TAB / newline
sanitize() { LC_ALL=C tr -d '\000-\010\013-\037\177'; }

# Repeat string $1 $2 times, without forking
rep() {
	local s
	(( $2 > 0 )) || return 0
	printf -v s '%*s' "$2" ''
	printf '%s' "${s// /$1}"
}

# Terminal size into TERM_ROWS / TERM_COLS (24x80 when unknown)
term_size() {
	local out="" r c
	TERM_ROWS=24; TERM_COLS=80
	if have stty; then out=$(stty size 2>/dev/null </dev/tty) || out=""; fi
	r=${out%% *}; c=${out##* }
	if [[ "$r" =~ ^[0-9]+$ && "$c" =~ ^[0-9]+$ ]] && (( r > 0 && c > 0 )); then
		TERM_ROWS=$r; TERM_COLS=$c
	elif [[ "${COLUMNS:-}" =~ ^[0-9]+$ ]] && (( COLUMNS > 0 )); then
		TERM_COLS=$COLUMNS
		[[ "${LINES:-}" =~ ^[0-9]+$ ]] && (( LINES > 0 )) && TERM_ROWS=$LINES
	elif have tput; then
		c=$(tput cols 2>/dev/null)
		[[ "$c" =~ ^[0-9]+$ ]] && (( c > 0 )) && TERM_COLS=$c
	fi
	return 0
}

term_width() {
	term_size
	printf '%s' "$(( TERM_COLS < 40 ? 40 : TERM_COLS ))"
}

# Pad plain text on the right to a width counted in characters (printf counts bytes in some
# locales). Usage: pad "text" width  -> result in $REPLY
pad() {
	local s="$1"; local -i n=$2-${#1}
	(( n < 0 )) && n=0
	printf -v REPLY '%s%*s' "$s" "$n" ''
}

# Center plain text (no ANSI codes) inside a field of the given width
pad_center() {
	local text="$1"; local -i width="$2" len=${#1}
	local -i left=$(( (width - len) / 2 )) right
	(( left < 0 )) && left=0
	right=$(( width - len - left )); (( right < 0 )) && right=0
	printf '%*s%s%*s' "$left" "" "$text" "$right" ""
}

# Clear the screen on terminals only
clear_screen() {
	ui_fancy || return 0
	tput clear 2>/dev/null || printf '\033[H\033[2J'
}

# ── Messages (printf only: text is never interpreted as escape sequences) ────
msg_ok()   { local m="$*"; printf '  %s%s%s %s\n' "$GREEN" "$SYM_OK" "$RESET" "${m//[[:cntrl:]]/}"; }
msg_err()  { local m="$*"; printf '  %s%s %s%s\n' "$E_RED" "$SYM_ERR" "${m//[[:cntrl:]]/}" "$E_RESET" >&2; }
msg_warn() { local m="$*"; printf '  %s%s %s%s\n' "$YELLOW" "$SYM_WARN" "${m//[[:cntrl:]]/}" "$RESET"; }
msg_info() { local m="$*"; printf '  %s%s%s %s\n' "$CYAN" "$SYM_INFO" "$RESET" "${m//[[:cntrl:]]/}"; }
msg_dim()  { local m="$*"; printf '  %s%s%s\n' "$DIM" "${m//[[:cntrl:]]/}" "$RESET"; }
die()      { msg_err "$*"; exit 1; }

# ── Layout: banner, rules, key/value, list items ─────────────────────────────
# Rounded panel shown once at startup. Usage: banner "Title" ["Subtitle"]
banner() {
	local title="$1" subtitle="${2:-}" border blank
	local -i width min_box box
	width=$(term_width)
	min_box=${#title}
	(( ${#subtitle} > min_box )) && min_box=${#subtitle}
	min_box+=4; (( min_box < 44 )) && min_box=44
	box=$(( width > 70 ? 60 : width - 10 ))
	(( box < min_box )) && box=$min_box
	border=$(rep "$BX_H" "$box")
	blank=$(pad_center "" "$box")
	printf '\n  %s%s%s%s%s\n' "$CYAN" "$BX_TL" "$border" "$BX_TR" "$RESET"
	printf '  %s%s%s%s\n' "$CYAN" "$BX_V$blank$BX_V" "$RESET" ""
	printf '  %s%s%s%s%s%s%s%s\n' "$CYAN" "$BX_V" "$BOLD" "$(pad_center "$title" "$box")" "$RESET" "$CYAN" "$BX_V" "$RESET"
	printf '  %s%s%s%s%s%s%s%s\n' "$CYAN" "$BX_V" "$RESET$DIM" "$(pad_center "$subtitle" "$box")" "$RESET" "$CYAN" "$BX_V" "$RESET"
	printf '  %s%s%s%s\n' "$CYAN" "$BX_V$blank$BX_V" "$RESET" ""
	printf '  %s%s%s%s%s\n\n' "$CYAN" "$BX_BL" "$border" "$BX_BR" "$RESET"
}

# Horizontal rule, with an optional embedded title. Usage: hr ["Title"]
hr() {
	local label="${1:-}" head
	local -i width=$(( $(term_width) - 2 )) padn
	if [[ -n "$label" ]]; then
		label=${label//[[:cntrl:]]/}
		head="${BX_H}${BX_H} ${label} "
		padn=$(( width - ${#head} )); (( padn < 0 )) && padn=0
		printf '  %s%s%s%s%s\n' "$MAGENTA" "$BOLD" "$head" "$(rep "$BX_H" "$padn")" "$RESET"
	else
		printf '  %s%s%s\n' "$MAGENTA" "$(rep "$BX_H" "$width")" "$RESET"
	fi
}

# Titled block: blank line, rule with title, blank line
section() { echo; hr "$1"; echo; }

# "Label         : value" line. Usage: kv "Label" "value"
kv() {
	local k="${1//[[:cntrl:]]/}" v="${2//[[:cntrl:]]/}"
	pad "$k" 14
	printf '  %s: %s%s%s\n' "$REPLY" "$BOLD" "$v" "$RESET"
}

# "✔ name  detail  extra" line for detected / found things. Usage: item_ok name [detail] [extra]
# name and detail are cleaned; extra is trusted markup (e.g. a colored tag), never external text.
item_ok() {
	local n="${1//[[:cntrl:]]/}" d="${2:-}" x="${3:-}" nn
	d=${d//[[:cntrl:]]/}
	pad "$n" 12; nn=$REPLY
	pad "$d" 30
	printf '  %s%s%s %s %s%s%s%s\n' "$GREEN" "$SYM_OK" "$RESET" "$nn" "$DIM" "$REPLY" "$RESET" "${x:+  $x}"
}

# ── Tables ───────────────────────────────────────────────────────────────────
# Split a TAB-separated row into the global array _COLS (keeps empty fields: TAB alone
# would collapse them, so tabs are first turned into a non-whitespace separator).
_COLS=()
split_row() {
	IFS=$'\x1f' read -ra _COLS <<< "${1//$'\t'/$'\x1f'}"
}

# Bordered table. Usage: print_table $'Col1\tCol2' < rows
# Rows come on stdin, one TAB-separated line each. Empty lines are ignored; cells are cleaned
# and cut at TABLE_MAX_CELL characters (default 60) so a long value never wraps the table.
print_table() {
	local header="$1" line cell top mid bot seg
	local -a headers=() cells=() widths=()
	local -i ncol i r nrows=0 max=${TABLE_MAX_CELL:-60} keep
	keep=max-${#SYM_DOT}
	split_row "$header"; headers=("${_COLS[@]}"); ncol=${#headers[@]}
	for ((i = 0; i < ncol; i++)); do widths[i]=${#headers[i]}; done
	while IFS= read -r line || [[ -n "$line" ]]; do
		[[ -n "${line//[[:space:]]/}" ]] || continue
		split_row "$line"
		for ((i = 0; i < ncol; i++)); do
			cell=${_COLS[i]:-}; cell=${cell//[[:cntrl:]]/}
			(( ${#cell} > max )) && cell="${cell:0:keep}${SYM_DOT}"
			cells+=("$cell")
			(( ${#cell} > widths[i] )) && widths[i]=${#cell}
		done
		(( ++nrows ))
	done
	if (( nrows == 0 )); then
		printf '  %s(no entries found)%s\n\n' "$DIM" "$RESET"
		return 0
	fi
	top="$TB_TL"; mid="$TB_ML"; bot="$TB_BL"
	for ((i = 0; i < ncol; i++)); do
		seg=$(rep "$TB_H" $(( widths[i] + 2 )))
		top+="$seg"; mid+="$seg"; bot+="$seg"
		if (( i < ncol - 1 )); then top+="$TB_TM"; mid+="$TB_MM"; bot+="$TB_BM"
		else top+="$TB_TR"; mid+="$TB_MR"; bot+="$TB_BR"; fi
	done
	printf '  %s%s%s\n' "$DIM" "$top" "$RESET"
	line="  $TB_V"
	for ((i = 0; i < ncol; i++)); do
		pad "${headers[i]}" "${widths[i]}"
		line+=" ${BOLD}${CYAN}${REPLY}${RESET} $TB_V"
	done
	printf '%s\n' "$line"
	printf '  %s%s%s\n' "$DIM" "$mid" "$RESET"
	for ((r = 0; r < nrows; r++)); do
		line="  $TB_V"
		for ((i = 0; i < ncol; i++)); do
			pad "${cells[r * ncol + i]}" "${widths[i]}"
			line+=" ${REPLY} $TB_V"
		done
		printf '%s\n' "$line"
	done
	printf '  %s%s%s\n\n' "$DIM" "$bot" "$RESET"
}

# ── Spinner ──────────────────────────────────────────────────────────────────
SPIN_PID=""
SPIN_DELAY=0.08

spin_start() {
	ui_fancy || return 0
	[[ -z "$SPIN_PID" ]] || return 0
	local msg="${1//[[:cntrl:]]/}" parent=$$
	sleep 0.01 2>/dev/null || SPIN_DELAY=1		# some systems cannot sleep for a fraction of a second
	(
		local i=0 n=${#SPIN_FRAMES}
		printf '%s' "$HIDE_CURSOR"
		# Stops by itself if the parent dies without cleaning up
		while kill -0 "$parent" 2>/dev/null; do
			printf '\r  %s%s%s %s' "$CYAN" "${SPIN_FRAMES:i++%n:1}" "$RESET" "$msg"
			sleep "$SPIN_DELAY"
		done
	) &
	SPIN_PID=$!
	disown "$SPIN_PID" 2>/dev/null
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
	"$@" >/dev/null 2>&1 </dev/null; rc=$?
	spin_stop
	if (( rc == 0 )); then msg_ok "$msg"; else msg_err "$msg"; fi
	return $rc
}

# Restore the terminal (spinner, cursor, echo). Call it from the EXIT trap.
ui_restore() {
	spin_stop 2>/dev/null
	printf '%s' "$SHOW_CURSOR"
	[[ -t 0 ]] && stty echo 2>/dev/null
	return 0
}

# Standard traps: restore the terminal on exit, clean messages and exit codes on signals.
# A script may replace the INT trap afterwards (e.g. a listener that stops with code 0).
ui_traps() {
	trap ui_restore EXIT
	trap 'printf "%s\n  %s%s%s\n" "$RESET" "$YELLOW" "Interrupted." "$RESET"; exit 130' INT
	trap 'exit 143' TERM
	trap 'exit 129' HUP
}

# ── Single-choice menu ───────────────────────────────────────────────────────
# Usage: select_menu "Prompt" "Option 1" "Option 2" "$SEP" "Quit" || return 1
# Sets $SELECTED to the chosen 0-based index (separators count). Arrows or j/k + Enter on a
# capable terminal; a numbered list otherwise (dumb terminal, screen too short).
SELECTED=0
_MENU_OPTS=(); _MENU_IDX=0; _MENU_W=40

_menu_fits() { term_size; (( $1 + 3 <= TERM_ROWS )); }

_menu_step() {		# move to the next selectable entry (+1 / -1), skipping dividers
	local -i n=${#_MENU_OPTS[@]} guard=0
	while :; do
		(( _MENU_IDX = (_MENU_IDX + $1 + n) % n ))
		[[ "${_MENU_OPTS[_MENU_IDX]}" != "$SEP" ]] && break
		(( ++guard > n )) && break
	done
}

_menu_draw() {
	local i lbl
	for i in "${!_MENU_OPTS[@]}"; do
		lbl=${_MENU_OPTS[i]}
		(( ${#lbl} > _MENU_W )) && lbl="${lbl:0:_MENU_W-${#SYM_DOT}}${SYM_DOT}"
		printf '\033[2K'
		if [[ "${_MENU_OPTS[i]}" == "$SEP" ]]; then
			printf '  %s%s%s\n' "$DIM" "$(rep "$BX_H" 28)" "$RESET"
		elif (( i == _MENU_IDX )); then
			printf '  %s%s%s %s%s\n' "$CYAN" "$BOLD" "$SYM_SEL" "$lbl" "$RESET"
		else
			printf '    %s\n' "$lbl"
		fi
	done
}

_select_plain() {
	local prompt="$1"; shift
	local -a opts=("${@//[[:cntrl:]]/}") map=()
	local -i i n=0
	local ans
	printf '  %s%s%s %s%s%s\n' "$CYAN" "$SYM_ASK" "$RESET" "$BOLD" "$prompt" "$RESET"
	for i in "${!opts[@]}"; do
		[[ "${opts[i]}" == "$SEP" ]] && continue
		(( ++n )); map[n]=$i
		printf '    %2d) %s\n' "$n" "${opts[i]}"
	done
	while true; do
		read -rp "  Choice [1-$n]: " ans || return 1
		if [[ "$ans" =~ ^[0-9]{1,6}$ ]] && (( 10#$ans >= 1 && 10#$ans <= n )); then
			SELECTED=${map[10#$ans]}
			return 0
		fi
		msg_warn "Enter a number between 1 and $n."
	done
}

select_menu() {
	if [[ ! -t 0 || ! -t 1 ]]; then
		msg_err "An interactive terminal is required."
		return 1
	fi
	local prompt="$1"; shift
	if ! ui_fancy || ! _menu_fits $#; then _select_plain "$prompt" "$@"; return; fi
	_MENU_OPTS=("${@//[[:cntrl:]]/}"); _MENU_IDX=0
	_MENU_W=$(( TERM_COLS - 8 ))
	local -i count=${#_MENU_OPTS[@]}
	local key
	[[ "${_MENU_OPTS[0]}" == "$SEP" ]] && _menu_step 1
	printf '%s' "$HIDE_CURSOR"
	printf '  %s%s%s %s%s%s %s(Use arrow keys)%s\n' "$CYAN" "$SYM_ASK" "$RESET" "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
	_menu_draw
	while true; do
		IFS= read -rsn1 key || { printf '%s' "$SHOW_CURSOR"; return 1; }
		if [[ "$key" == $'\033' ]]; then
			IFS= read -rsn2 -t 0.05 key || key=""
			case "$key" in
				'[A'|'OA') _menu_step -1 ;;
				'[B'|'OB') _menu_step 1 ;;
			esac
		elif [[ "$key" == k ]]; then _menu_step -1
		elif [[ "$key" == j ]]; then _menu_step 1
		elif [[ -z "$key" ]]; then break
		fi
		printf '\033[%dA' "$count"
		_menu_draw
	done
	printf '\033[%dA\033[J' $(( count + 1 ))
	printf '  %s%s%s %s%s%s %s%s%s\n' "$GREEN" "$SYM_OK" "$RESET" "$BOLD" "$prompt" "$RESET" "$CYAN" "${_MENU_OPTS[_MENU_IDX]}" "$RESET"
	printf '%s' "$SHOW_CURSOR"
	SELECTED=$_MENU_IDX
}

# ── Multi-choice menu ────────────────────────────────────────────────────────
# Usage: checkbox_menu "Prompt" "Option 1" "Option 2" ... || return 1
# Sets the array $SELECTED_IDX to the checked 0-based indices (possibly empty).
# Arrows or j/k to move, Space to toggle, Enter to validate (numbered prompt as fallback).
SELECTED_IDX=()
_CB_OPTS=(); _CB_ON=(); _CB_IDX=0

_cb_draw() {
	local i box lbl
	for i in "${!_CB_OPTS[@]}"; do
		lbl=${_CB_OPTS[i]}
		(( ${#lbl} > _MENU_W )) && lbl="${lbl:0:_MENU_W-${#SYM_DOT}}${SYM_DOT}"
		printf '\033[2K'
		if (( _CB_ON[i] )); then box="[${GREEN}${SYM_OK}${RESET}]"; else box="[ ]"; fi
		if (( i == _CB_IDX )); then
			printf '  %s%s%s%s %s %s%s%s%s\n' "$CYAN" "$BOLD" "$SYM_SEL" "$RESET" "$box" "$CYAN" "$BOLD" "$lbl" "$RESET"
		else
			printf '    %s %s\n' "$box" "$lbl"
		fi
	done
}

_checkbox_plain() {
	local prompt="$1"; shift
	local -a opts=("${@//[[:cntrl:]]/}") picked toks
	local -i i n=${#opts[@]} ok
	local ans tok
	printf '  %s%s%s %s%s%s\n' "$CYAN" "$SYM_ASK" "$RESET" "$BOLD" "$prompt" "$RESET"
	for i in "${!opts[@]}"; do printf '    %2d) %s\n' $(( i + 1 )) "${opts[i]}"; done
	while true; do
		read -rp "  Numbers separated by spaces (empty = none): " ans || return 1
		picked=(); ok=1
		read -ra toks <<< "${ans//,/ }"		# split without globbing
		for tok in "${toks[@]}"; do
			if [[ "$tok" =~ ^[0-9]{1,6}$ ]] && (( 10#$tok >= 1 && 10#$tok <= n )); then
				picked+=( $(( 10#$tok - 1 )) )
			else
				ok=0; break
			fi
		done
		(( ok )) && break
		msg_warn "Enter numbers between 1 and $n."
	done
	SELECTED_IDX=("${picked[@]}")
}

checkbox_menu() {
	if [[ ! -t 0 || ! -t 1 ]]; then
		msg_err "An interactive terminal is required."
		return 1
	fi
	local prompt="$1"; shift
	if ! ui_fancy || ! _menu_fits $#; then _checkbox_plain "$prompt" "$@"; return; fi
	_CB_OPTS=("${@//[[:cntrl:]]/}"); _CB_ON=(); _CB_IDX=0
	_MENU_W=$(( TERM_COLS - 12 ))
	local -i count=${#_CB_OPTS[@]} i
	local key joined=""
	for ((i = 0; i < count; i++)); do _CB_ON[i]=0; done
	printf '%s' "$HIDE_CURSOR"
	printf '  %s%s%s %s%s%s %s(space: toggle, enter: confirm)%s\n' "$CYAN" "$SYM_ASK" "$RESET" "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
	_cb_draw
	while true; do
		IFS= read -rsn1 key || { printf '%s' "$SHOW_CURSOR"; return 1; }
		case "$key" in
			$'\033')
				IFS= read -rsn2 -t 0.05 key || key=""
				case "$key" in
					'[A'|'OA') (( _CB_IDX = (_CB_IDX - 1 + count) % count )) ;;
					'[B'|'OB') (( _CB_IDX = (_CB_IDX + 1) % count )) ;;
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
	for ((i = 0; i < count; i++)); do
		(( _CB_ON[i] )) || continue
		SELECTED_IDX+=("$i")
		joined+="${joined:+, }${_CB_OPTS[i]}"
	done
	[[ -n "$joined" ]] && printf '  %s%s%s %s%s%s %s%s%s\n' "$GREEN" "$SYM_OK" "$RESET" "$BOLD" "$prompt" "$RESET" "$CYAN" "$joined" "$RESET"
	printf '%s' "$SHOW_CURSOR"
}

# ── Prompts ──────────────────────────────────────────────────────────────────
# Yes/no prompt, auto-accepted when AUTO_YES=true (--yes). Without a terminal the answer is "no".
confirm() {
	[[ "${AUTO_YES:-false}" == true ]] && return 0
	[[ -t 0 ]] || return 1
	local answer
	read -rp "  $1 [y/N]: " answer || return 1
	[[ "$answer" =~ ^[Yy]([Ee][Ss])?$ ]]
}

# Free-text prompt. Usage: ask "Label: " || return 1   -> cleaned answer in $REPLY
ask() {
	[[ -t 0 ]] || return 1
	local answer
	read -rp "  $1" answer || return 1
	REPLY=${answer//[[:cntrl:]]/}
}

pause() {
	[[ -t 0 ]] || return 0
	echo
	read -rp "  Press [Enter] to continue..." _
}

# Pipe through a pager when attached to a terminal ("less" with shell escapes disabled)
pager() {
	if [[ -t 1 ]] && have less; then
		LESSSECURE=1 LESSOPEN= LESSCLOSE= less -RFX
	else
		cat
	fi
}
# <<< STYLE END <<<

# ──────────────────────────────────────────────────────────────────────────────
#  Global state
# ──────────────────────────────────────────────────────────────────────────────
SELECTED_PORTS=()			# ports given on the CLI or picked in the menu
LIST_ONLY=false
NONINTERACTIVE=false
BAD_ARGS=false
MISSING=0
# Note names used to turn a MIDI note number into a readable name
NOTE_NAMES=("C" "C#" "D" "D#" "E" "F" "F#" "G" "G#" "A" "A#" "B")
# Detected ports and their human-readable names, filled by detect_ports
declare -a ALL_PORTS=()
declare -A PORT_NAMES=()

ui_traps
# A listener is stopped with Ctrl+C on purpose: that is a normal end, not an error
trap 'printf "%s\n  %s%s%s\n" "$RESET" "$YELLOW" "Stopping listening." "$RESET"; exit 0' INT

# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────
# Turn a MIDI note number into a readable note name + octave (result in $REPLY, no subshell)
note_name() {
	local n=$((10#$1))
	REPLY="${NOTE_NAMES[n % 12]}$((n / 12 - 1))"
}

# Suggest the install command of package $1 for the package manager found on this machine
install_hint() {
	local cmd=""
	if   have apt-get;      then cmd="sudo apt install $1"
	elif have dnf;          then cmd="sudo dnf install $1"
	elif have pacman;       then cmd="sudo pacman -S $1"
	elif have zypper;       then cmd="sudo zypper install $1"
	elif have apk;          then cmd="sudo apk add $1"
	elif have xbps-install; then cmd="sudo xbps-install $1"
	elif have emerge;       then cmd="sudo emerge media-sound/$1"
	fi
	echo
	if [[ -n "$cmd" ]]; then
		printf '  Install the missing tools with:\n  %s%s%s\n\n' "$CYAN" "$cmd" "$RESET"
	else
		printf "  Install the '%s' package with your system's package manager.\n\n" "$1"
	fi
}

# Check the platform and the required tools, exit early if something is missing
check_dependencies() {
	local cmd
	if [[ "$(uname -s 2>/dev/null)" != Linux ]]; then
		die "ALSA is only available on Linux: this tool cannot run on $(uname -s 2>/dev/null)."
	fi
	for cmd in aseqdump aconnect; do
		if ! have "$cmd"; then
			msg_err "'$cmd' is not installed."
			MISSING=1
		fi
	done
	if (( MISSING )); then
		install_hint alsa-utils
		exit 1
	fi
	if [[ " $(id -nG 2>/dev/null) " != *" audio "* ]]; then
		msg_warn "You are not in the 'audio' group. If no device is detected, run:"
		printf '  %s%s%s  then log out and back in.\n\n' "$CYAN" 'sudo usermod -aG audio $USER' "$RESET"
	fi
}

# ──────────────────────────────────────────────────────────────────────────────
#  Detection
# ──────────────────────────────────────────────────────────────────────────────
# Parse "aconnect -l" output with bash only (no grep -P, which BSD/busybox lack),
# fill ALL_PORTS / PORT_NAMES and print each port found.
detect_ports() {
	local line key cnum="" cname="" pnum pname
	local re_client="^client[[:space:]]+([0-9]+):[[:space:]]+'(.*)'"
	local re_port="^[[:space:]]+([0-9]+)[[:space:]]+'(.*)'"
	section "Detected devices"
	while IFS= read -r line; do
		if [[ "$line" =~ $re_client ]]; then
			cnum="${BASH_REMATCH[1]}"
			cname="${BASH_REMATCH[2]}"
			# Skip the ALSA system clients (0 = System, 14 = Midi Through, >=128 = software)
			if (( 10#$cnum == 0 || 10#$cnum == 14 || 10#$cnum >= 128 )); then cnum=""; fi
		elif [[ -n "$cnum" && "$line" =~ $re_port ]]; then
			pnum="${BASH_REMATCH[1]}"
			pname="${BASH_REMATCH[2]}"
			# Names come from the hardware: strip control characters and trailing blanks
			clean "$cname"; cname="${REPLY%"${REPLY##*[![:space:]]}"}"
			clean "$pname"; pname="${REPLY%"${REPLY##*[![:space:]]}"}"
			key="${cnum}:${pnum}"
			ALL_PORTS+=("$key")
			PORT_NAMES["$key"]="$cname / $pname"
			item_ok "$key" "$cname $SYM_ARROW $pname"
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
		4) printf '  %sSee you soon!%s\n\n' "$GREEN" "$RESET"; exit 0 ;;
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
	pad "$pname" 28; pname="$REPLY"
	[[ "$rest" =~ $re_ch ]] && ch_txt=" (ch ${BASH_REMATCH[1]})"
	case "$lc" in
		*"note on"*)
			[[ "$lc" =~ $re_note ]] || return
			note="${BASH_REMATCH[1]}"
			[[ "$lc" =~ $re_vel ]] && vel="${BASH_REMATCH[1]}"
			note_name "$note"
			if [[ "$vel" == 0 ]]; then
				printf '  %-8s %s %-12s %-10s %s\n' "$src" "$pname" "Note OFF" "" "$REPLY$ch_txt"
				return
			fi
			printf '  %s%-8s%s %s %s%-12s%s %-10s %s\n' "$GREEN" "$src" "$RESET" "$pname" "$BOLD" "Note ON" "$RESET" "vel=$vel" "$REPLY (MIDI $note)$ch_txt" ;;
		*"note off"*)
			[[ "$lc" =~ $re_note ]] || return
			note_name "${BASH_REMATCH[1]}"
			printf '  %-8s %s %-12s %-10s %s\n' "$src" "$pname" "Note OFF" "" "$REPLY$ch_txt" ;;
		*"control change"*)
			[[ "$lc" =~ $re_ctrl ]] || return
			ctrl="${BASH_REMATCH[1]}"
			[[ "$lc" =~ $re_val ]] && val="${BASH_REMATCH[1]}"
			printf '  %s%-8s%s %s %s%-12s%s %-10s %s\n' "$YELLOW" "$src" "$RESET" "$pname" "$YELLOW" "CC" "$RESET" "val=$val" "Controller #$ctrl$ch_txt" ;;
		*"program change"*)
			[[ "$lc" =~ $re_prog ]] && prog="${BASH_REMATCH[1]}"
			printf '  %s%-8s%s %s %s%-12s%s %s\n' "$CYAN" "$src" "$RESET" "$pname" "$CYAN" "Prog CH" "$RESET" "#$prog$ch_txt" ;;
		*"pitch bend"*)
			[[ "$lc" =~ $re_val ]] && val="${BASH_REMATCH[1]}"
			printf '  %s%-8s%s %s %s%-12s%s %s\n' "$CYAN" "$src" "$RESET" "$pname" "$CYAN" "Pitch" "$RESET" "$val$ch_txt" ;;
		*"channel pressure"*|*aftertouch*)
			[[ "$lc" =~ $re_val ]] && val="${BASH_REMATCH[1]}"
			printf '  %s%-8s%s %s %s%-12s%s %s\n' "$CYAN" "$src" "$RESET" "$pname" "$CYAN" "Aftertouch" "$RESET" "val=$val$ch_txt" ;;
		*sysex*|*"system exclusive"*)
			printf '  %-8s %s %-12s\n' "$src" "$pname" "SysEx" ;;
	esac
}

# Build the port list to listen on, print the header, then stream formatted events until Ctrl+C
listen_and_print() {
	local ports_arg rc line
	section "Listening"
	if (( ${#SELECTED_PORTS[@]} > 0 )); then
		ports_arg=$(IFS=,; echo "${SELECTED_PORTS[*]}")
		msg_ok "Listening on selected port(s): $ports_arg"
	else
		ports_arg=$(IFS=,; echo "${ALL_PORTS[*]}")
		msg_ok "${#ALL_PORTS[@]} port(s) found - listening..."
	fi
	msg_dim "Press keys, pads, buttons - Ctrl+C to quit."
	echo
	printf '  %s%s%-8s %-28s %-12s %-10s %s%s\n' "$BOLD" "$CYAN" "PORT" "DEVICE / PORT" "TYPE" "VALUE" "DETAIL" "$RESET"
	printf '  %s%s%s\n' "$DIM" "$(rep "$BX_H" 68)" "$RESET"
	aseqdump -p "$ports_arg" | while IFS= read -r line; do
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
	cat <<USAGE
    MIDI Tester v${VERSION} - CLI usage
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
USAGE
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
	if $LIST_ONLY || (( ${#SELECTED_PORTS[@]} > 0 )); then
		NONINTERACTIVE=true
	fi
	# No flag and no terminal: the menu cannot work
	if ! $NONINTERACTIVE && [[ ! -t 0 || ! -t 1 ]]; then usage; exit 1; fi

	clear_screen
	banner "MIDI Tester v${VERSION}" "Live ALSA MIDI message viewer"
	check_dependencies
	detect_ports

	# A port given on the CLI must exist in the detected list (virtual ports are still allowed)
	for p in "${SELECTED_PORTS[@]}"; do
		[[ -n "${PORT_NAMES[$p]+x}" ]] || msg_warn "Port $p is not in the detected list (listening anyway)."
	done

	if (( ${#ALL_PORTS[@]} == 0 && ${#SELECTED_PORTS[@]} == 0 )); then
		msg_err "No MIDI device found."
		echo
		echo "  Check that your device is plugged in, then try:"
		printf '  %saconnect -l%s        - lists all MIDI clients\n' "$CYAN" "$RESET"
		printf '  %samidi -l%s           - lists raw MIDI ports\n' "$CYAN" "$RESET"
		echo
		echo "  If your device doesn't show up at all:"
		printf '  %slsusb%s              - check that Linux recognizes it\n' "$CYAN" "$RESET"
		printf '  %sdmesg | tail -20%s   - look for errors when plugging it in\n' "$CYAN" "$RESET"
		exit 1
	fi

	# No CLI flag given: interactive menu (list all / choose ports / list only / quit)
	$NONINTERACTIVE || show_menu
	$LIST_ONLY && exit 0
	listen_and_print
}

main "$@"
