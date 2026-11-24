#!/usr/bin/env bash
# App Manager - application manager for Linux.
# Detects every package manager / install method on the system, then lets you
# list, search, install, remove and (above all) upgrade everything from one place.
# >>> STYLE BEGIN v2.4 - shared console style, keep this block identical in every script >>>
# Reference: STYLE-GUIDE.md. Portable: bash >= 3.2 on any Linux (WSL and Termux included).
# Started from sh / dash / zsh, it relaunches itself under bash.
# Degrades gracefully: ASCII symbols without UTF-8, plain text without colors, numbered
# menus without a capable terminal. No external dependency except coreutils-like basics.
# UI_ASCII=1 (environment) or --ascii forces the ASCII symbols.

# ── Bootstrap (plain POSIX sh syntax only: sh, dash or zsh read these lines before bash does) ──
# Started with "sh script" or "zsh script": hand over to bash instead of dying on bash-only syntax.
if [ -z "${BASH_VERSION:-}" ]; then
	if command -v bash >/dev/null 2>&1; then exec bash "$0" "$@"; fi
	printf 'This script needs bash, which was not found.\n' >&2
	printf 'Install it (apt install bash, apk add bash, pkg install bash...).\n' >&2
	exit 1
fi

# ── Shell version guard (nothing below may use syntax newer than bash 3.2) ──
if (( BASH_VERSINFO[0] < 3 || (BASH_VERSINFO[0] == 3 && BASH_VERSINFO[1] < 2) )); then
	printf 'This script needs bash 3.2 or newer (found %s).\n' "$BASH_VERSION" >&2
	printf 'Install a recent bash package (apt, dnf, pacman or apk: install bash).\n' >&2
	exit 1
fi

# bash < 4 only accepts whole seconds as read timeout (used to tell a lone ESC from arrow keys)
if (( BASH_VERSINFO[0] >= 4 )); then _KEY_TIMEOUT=0.05; else _KEY_TIMEOUT=1; fi

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

# Pass "$SEP" as an option of select_menu to draw a non-selectable divider line
readonly SEP="---sep---"

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
UI_UTF8_OK=false		# can the terminal display UTF-8? (used by the menu toggle)
if _utf8_locale; then
	UI_UTF8_OK=true
elif command -v locale >/dev/null 2>&1; then
	_avail=$'\n'"$(locale -a 2>/dev/null)"$'\n'
	for _c in C.UTF-8 C.utf8 en_US.UTF-8 en_US.utf8; do
		if [[ "$_avail" == *$'\n'"$_c"$'\n'* ]]; then
			export LC_ALL="$_c"
			_utf8_locale && UI_UTF8_OK=true
			break
		fi
	done
	unset _avail _c
fi
# String operations must count characters, not bytes (old bash, odd locales): otherwise the
# boxes and tables would be misaligned, so stay in ASCII.
if $UI_UTF8_OK; then
	_t='é✓'
	[[ ${#_t} -eq 2 && "${_t:1:1}" == '✓' ]] || UI_UTF8_OK=false
	unset _t
fi
[[ "${UI_ASCII:-0}" != 1 ]] && $UI_UTF8_OK && UI_UTF8=true

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

# Symbols (Unicode when possible, ASCII otherwise). Can be called again to switch mode.
ui_set_symbols() {
	if $UI_UTF8; then
		SYM_OK='[✓]'; SYM_ERR='[x]'; SYM_WARN='[!]'; SYM_INFO='[*]'; SYM_ASK='[?]'; SYM_SEL='[»]'
		SYM_SKIP='[-]'; SYM_ARROW='[→]'; SYM_DOT='…'
		SYM_BOX_ON='[✓]'; SYM_BOX_OFF='[ ]'
		BX_TL='╭'; BX_TR='╮'; BX_BL='╰'; BX_BR='╯'; BX_V='│'; BX_H='─'
		TB_TL='┌'; TB_TM='┬'; TB_TR='┐'; TB_ML='├'; TB_MM='┼'; TB_MR='┤'
		TB_BL='└'; TB_BM='┴'; TB_BR='┘'; TB_V='│'; TB_H='─'
		SPIN_FRAMES='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
	else
		SYM_OK='[OK]'; SYM_ERR='[x]'; SYM_WARN='[!]'; SYM_INFO='[*]'; SYM_ASK='[?]'; SYM_SEL='[>]'
		SYM_SKIP='[-]'; SYM_ARROW='->'; SYM_DOT='...'
		SYM_BOX_ON='[x]'; SYM_BOX_OFF='[ ]'
		BX_TL='+'; BX_TR='+'; BX_BL='+'; BX_BR='+'; BX_V='|'; BX_H='-'
		TB_TL='+'; TB_TM='+'; TB_TR='+'; TB_ML='+'; TB_MM='+'; TB_MR='+'
		TB_BL='+'; TB_BM='+'; TB_BR='+'; TB_V='|'; TB_H='-'
		SPIN_FRAMES='|/-\'
	fi
}
ui_set_symbols

# Switch to ASCII symbols (--ascii)
ui_use_ascii() { UI_UTF8=false; ui_set_symbols; }

# Toggle Unicode <-> ASCII (menu). Unicode only if the terminal supports it.
ui_toggle_mode() {
	if $UI_UTF8; then
		UI_UTF8=false; ui_set_symbols
		msg_info "ASCII mode enabled"
	elif $UI_UTF8_OK; then
		UI_UTF8=true; ui_set_symbols
		msg_info "Unicode mode enabled"
	else
		msg_warn "This terminal has no UTF-8 locale: staying in ASCII mode."
	fi
}

readonly RED GREEN YELLOW CYAN MAGENTA BOLD DIM RESET E_RED E_RESET HIDE_CURSOR SHOW_CURSOR

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
msg_ok()     { local m="$*"; printf '  %s%s%s %s\n' "$GREEN" "$SYM_OK" "$RESET" "${m//[[:cntrl:]]/}"; }
msg_err()    { local m="$*"; printf '  %s%s %s%s\n' "$E_RED" "$SYM_ERR" "${m//[[:cntrl:]]/}" "$E_RESET" >&2; }
msg_warn()   { local m="$*"; printf '  %s%s %s%s\n' "$YELLOW" "$SYM_WARN" "${m//[[:cntrl:]]/}" "$RESET"; }
msg_info()   { local m="$*"; printf '  %s%s%s %s\n' "$CYAN" "$SYM_INFO" "$RESET" "${m//[[:cntrl:]]/}"; }
msg_dim()    { local m="$*"; printf '  %s%s%s\n' "$DIM" "${m//[[:cntrl:]]/}" "$RESET"; }
die()        { msg_err "$*"; exit 1; }

# Skipped / cancelled / not applicable
msg_skip()   { local m="$*"; printf '  %s%s %s%s\n' "$DIM" "$SYM_SKIP" "${m//[[:cntrl:]]/}" "$RESET"; }
# Step in progress
msg_step()   { local m="$*"; printf '  %s%s%s %s\n' "$CYAN" "$SYM_ARROW" "$RESET" "${m//[[:cntrl:]]/}"; }
# msg_change "old" "new"  ->  old → new
msg_change() {
	local a="${1//[[:cntrl:]]/}" b="${2//[[:cntrl:]]/}"
	printf '  %s%s%s %s %s%s%s %s%s%s\n' "$CYAN" "$SYM_INFO" "$RESET" "$a" "$CYAN" "$SYM_ARROW" "$RESET" "$BOLD" "$b" "$RESET"
}

# ── Layout: banner, rules, key/value, list items ─────────────────────────────
# Rounded panel shown once at startup. Usage: banner "Title" ["Subtitle"]
banner() {
	local title="$1" subtitle="${2:-}" border blank indent
	local -i width min_box box margin
	width=$(term_width)
	min_box=${#title}
	(( ${#subtitle} > min_box )) && min_box=${#subtitle}
	min_box+=4; (( min_box < 44 )) && min_box=44
	box=$(( width > 70 ? 60 : width - 10 ))
	(( box < min_box )) && box=$min_box

	# Margin used to center the box
	margin=$(( (width - box) / 2 ))
	(( margin < 0 )) && margin=0
	indent=$(rep " " "$margin")

	border=$(rep "$BX_H" "$box")
	blank=$(pad_center "" "$box")

	printf '\n%s%s%s%s%s%s\n' "$indent" "$CYAN" "$BX_TL" "$border" "$BX_TR" "$RESET"
	printf '%s%s%s%s\n' "$indent" "$CYAN" "$BX_V$blank$BX_V" "$RESET"
	printf '%s%s%s%s%s%s%s%s%s\n' "$indent" "$CYAN" "$BX_V" "$BOLD" "$(pad_center "$title" "$box")" "$RESET" "$CYAN" "$BX_V" "$RESET"
	printf '%s%s%s%s%s%s%s%s%s\n' "$indent" "$CYAN" "$BX_V" "$RESET$DIM" "$(pad_center "$subtitle" "$box")" "$RESET" "$CYAN" "$BX_V" "$RESET"
	printf '%s%s%s%s\n' "$indent" "$CYAN" "$BX_V$blank$BX_V" "$RESET"
	printf '%s%s%s%s%s%s\n\n' "$indent" "$CYAN" "$BX_BL" "$border" "$BX_BR" "$RESET"
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

# "[✓] name  detail  extra" line for detected / found things. Usage: item_ok name [detail] [extra]
# name and detail are cleaned; extra is trusted markup (e.g. a colored tag), never external text.
item_ok() {
	local n="${1//[[:cntrl:]]/}" d="${2:-}" x="${3:-}" nn
	d=${d//[[:cntrl:]]/}
	pad "$n" 14; nn=$REPLY
	pad "$d" 30
	printf '  %s%s%s %s %s%s%s%s\n' "$GREEN" "$SYM_OK" "$RESET" "$nn" "$DIM" "$REPLY" "$RESET" "${x:+  $x}"
}

# ── Tables ───────────────────────────────────────────────────────────────────
# Split a TAB-separated row into the global array _COLS (keeps empty fields: TAB alone
# would collapse them, so tabs are first turned into a non-whitespace separator).
_COLS=()
_TAB=$'\t'; _US=$'\x1f'
split_row() {
	local row="${1//$_TAB/$_US}"
	IFS=$_US read -ra _COLS <<< "$row"
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
	# Borders (horizontal and vertical) all use DIM so the frame has one single tone
	printf '  %s%s%s\n' "$DIM" "$top" "$RESET"
	line="  ${DIM}${TB_V}${RESET}"
	for ((i = 0; i < ncol; i++)); do
		pad "${headers[i]}" "${widths[i]}"
		line+=" ${BOLD}${CYAN}${REPLY}${RESET} ${DIM}${TB_V}${RESET}"
	done
	printf '%s\n' "$line"
	printf '  %s%s%s\n' "$DIM" "$mid" "$RESET"
	for ((r = 0; r < nrows; r++)); do
		line="  ${DIM}${TB_V}${RESET}"
		for ((i = 0; i < ncol; i++)); do
			pad "${cells[r * ncol + i]}" "${widths[i]}"
			line+=" ${REPLY} ${DIM}${TB_V}${RESET}"
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
			printf '\r  %s%s%s %s%s' "$CYAN" "${SPIN_FRAMES:i++%n:1}" "$RESET" "$msg" "$SYM_DOT"
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

# Run a command behind a spinner, then show [✓] / [x]. Usage: run_task "Message" cmd args...
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
			IFS= read -rsn2 -t "$_KEY_TIMEOUT" key || key=""
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
		if (( _CB_ON[i] )); then box="${GREEN}${SYM_BOX_ON}${RESET}"; else box="$SYM_BOX_OFF"; fi
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
				IFS= read -rsn2 -t "$_KEY_TIMEOUT" key || key=""
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

set -o pipefail

VERSION="3.1.0"
readonly VERSION

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
MANAGERS=()					# ordered ids of the managers available on this system
M_LABEL=()					# display labels, same order as MANAGERS (no associative arrays: bash 3.2)
RESULTS=()					# per-manager upgrade results
COUNT_ROWS=()				# cached package counts

cleanup() {
	drop_sudo
	ui_restore
}
ui_traps
trap cleanup EXIT

# Does manager $1 implement capability $2 (rows, outdated, upgrade, search, install, remove)?
cap() { declare -F "${1}_${2}" >/dev/null; }

# Lower-case text (bash 3.2 has no ${var,,}). Result in $REPLY.
lower() { REPLY=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]'); }

# Label of manager $1 (printed), and "is manager $1 registered?"
lbl() {
	local i
	for i in "${!MANAGERS[@]}"; do
		if [[ "${MANAGERS[i]}" == "$1" ]]; then printf '%s' "${M_LABEL[i]}"; return 0; fi
	done
	return 1
}
has_manager() { local i; for i in "${!MANAGERS[@]}"; do [[ "${MANAGERS[i]}" == "$1" ]] && return 0; done; return 1; }

# Run a command as root (directly if already root, through sudo otherwise)
as_root() {
	if (( EUID == 0 )); then
		"$@"
	elif have sudo; then
		sudo "$@"
	else
		msg_err "Root privileges are required but sudo was not found."
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
	disown "$SUDO_KEEPALIVE_PID" 2>/dev/null
}

# Stop the sudo keep-alive and drop the cached ticket, so a sudo credential never outlives the action
drop_sudo() {
	[[ -n "$SUDO_KEEPALIVE_PID" ]] || return 0
	have pkill && pkill -P "$SUDO_KEEPALIVE_PID" 2>/dev/null
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
	ui_interactive || return 1
	read -rp "  Continue as root anyway? [y/N]: " answer || return 1
	[[ "$answer" =~ ^[Yy]([Ee][Ss])?$ ]]
}

# Warn when the whole script runs as root (user-level managers would act on root's files)
root_warning() {
	if (( EUID == 0 )); then
		msg_warn "Running as root: pip, npm, cargo... will act on root's files. Prefer your normal user (sudo is asked when needed)."
	fi
	return 0
}

# ── Input validation ─────────────────────────────────────────────────────────
# Refuse anything that could be read as an option, a URL, a local path or a pattern.
# Package names: letters, digits and . _ + : = @ / ~ -   never starting with "-", no wildcards.
valid_pkg() {
	local re_scheme='^(git|file|http|https|ssh|ftp|github|gitlab|bitbucket|link|workspace|portal|npm|jsr|patch)[:+]'
	[[ "$1" =~ ^[[:alnum:]@][[:alnum:]._+:=@/~-]*$ ]] || return 1
	[[ "$1" == *- ]] && return 1			# "name-" means "remove name" for apt
	[[ "$1" == *://* ]] && return 1			# any URL
	[[ "$1" =~ $re_scheme ]] && return 1	# git+https:..., github:user/repo, file:...
	return 0
}
bad_pkg() { msg_err "Invalid package name (allowed: letters, digits and . _ + : = @ / ~ - ; no leading or trailing '-', no URLs, no wildcards)."; }

# A "/" means a tap, a remote or a scope for some managers, but a GitHub repo or a local file
# for others (npm "user/repo", pip "dir/file.whl"): accept it only where it is a plain name.
# $1 = manager id, $2 = package name
pkg_allowed_for() {
	local mgr="$1" pkg="$2" re_file='\.(deb|rpm|apk|xbps|zst|xz|gz)$'
	[[ "$pkg" == */* ]] || return 0
	case "$mgr" in
		brew|flatpak|nix|composer) return 0 ;;
		npm|yarn|pnpm) [[ "$pkg" =~ ^@[^/]+/[^/]+$ ]] && return 0 ;;
		system) [[ "$pkg" =~ $re_file ]] || return 0 ;;
	esac
	msg_err "A name containing '/' is not accepted for this manager (it could point to a local file or a repository)."
	return 1
}

# Search text: free text, but not an option and without control characters.
valid_query() { [[ -n "$1" && "$1" != -* && "$1" != *[[:cntrl:]]* ]]; }

# Prefix each line with two spaces, or say that there is nothing to show.
# Input comes from external commands: control characters are removed first.
indent_or_ok() {
	local out; out=$(sanitize)
	if [[ -z "${out//[[:space:]]/}" ]]; then
		printf '  %sAlready up to date.%s\n' "$GREEN" "$RESET"
	else
		sed 's/^/  /' <<< "$out"
	fi
}

# Pretty name of the operating system
os_name() {
	local n=""
	if [[ -r /etc/os-release ]]; then
		n=$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release | head -n 1 | tr -d "\"'")
	fi
	printf '%s' "${n:-$(uname -s 2>/dev/null)}"
}

# ──────────────────────────────────────────────────────────────────────────────
#  Detection
# ──────────────────────────────────────────────────────────────────────────────
register() { MANAGERS+=("$1"); M_LABEL+=("$2"); }

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
		has_manager "$id" && continue		# already registered (e.g. pip / pip3)
		case "$id" in
			yarn) [[ "$(yarn --version 2>/dev/null)" == 1.* ]] || continue ;;
			pip)  [[ -n "$(pip_bin)" ]] || continue; cmd=$(pip_bin) ;;
		esac
		register "$id" "$label" "$cmd"
	done
	return 0
}

show_detection() {
	local entry group name cmd id label path g any total=0 tag
	local -a groups=(); local seen="|"
	for entry in "${DETECT_TABLE[@]}"; do
		group="${entry%%|*}"
		[[ "$seen" == *"|$group|"* ]] || { seen+="$group|"; groups+=("$group"); }
	done
	for g in "${groups[@]}"; do
		section "$g"; any=false
		for entry in "${DETECT_TABLE[@]}"; do
			IFS='|' read -r group name cmd id label <<< "$entry"
			[[ "$group" == "$g" ]] || continue
			path=$(command -v "$cmd" 2>/dev/null) || continue
			tag=""
			[[ -n "$id" ]] && has_manager "$id" && tag="${GREEN}managed${RESET}"
			item_ok "$name" "$path" "$tag"
			(( ++total )); any=true
		done
		$any || msg_dim "(none)"
	done
	echo
	hr
	kv "Total detected" "$total"
	kv "Distribution" "$(os_name)"
	local out=""
	for id in "${MANAGERS[@]}"; do cap "$id" upgrade && out+="${id} "; done
	kv "Upgradable here" "${out:-none}"; echo
}

# Compact one-line summary used in the menu header
show_managers() {
	local id out=""
	for id in "${MANAGERS[@]}"; do out+="${GREEN}${SYM_OK}${RESET} $(lbl "$id")   "; done
	printf '  %sDetected:%s %s\n\n' "$DIM" "$RESET" "$out"
}

# ──────────────────────────────────────────────────────────────────────────────
#  Manager: system packages (apt, dnf, yum, pacman, zypper, apk, xbps, emerge, eopkg)
# ──────────────────────────────────────────────────────────────────────────────
system_rows() {
	case "$PM" in
		apt)			dpkg-query -W -f='${db:Status-Abbrev} ${Package}\t${Version}\n' 2>/dev/null | awk -F'\t' '{ split($1, a, " "); if (a[1] == "ii") print a[2] "\t" $2 }' | sort ;;
		dnf|yum|zypper)	rpm -qa --qf '%{NAME}\t%{VERSION}\n' 2>/dev/null | sort ;;
		pacman)			pacman -Q 2>/dev/null | awk '{print $1 "\t" $2}' ;;
		apk)			apk info -v 2>/dev/null | sort | awk '{ if (match($0, /-[^-]+-r[0-9]+$/)) print substr($0, 1, RSTART - 1) "\t" substr($0, RSTART + 1); else print $0 "\t" }' ;;
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
		apt) as_root apt-get update && as_root apt-get -y full-upgrade && apt_autoremove ;;
		dnf) as_root dnf -y upgrade --refresh ;;
		yum) as_root yum -y update ;;
		pacman) as_root pacman -Syu --noconfirm ;;
		zypper) as_root zypper -n refresh && as_root zypper -n update ;;
		apk) as_root apk update && as_root apk upgrade ;;
		xbps) as_root xbps-install -Syu ;;
		emerge) as_root emerge --sync && as_root emerge --ask=n --update --deep --newuse @world ;;
		eopkg) as_root eopkg -y upgrade ;;
	esac
}

system_search() {
	case "$PM" in
		apt) apt-cache search "$1" ;;
		dnf|yum) "$PM" search "$1" ;;
		pacman) pacman -Ss "$1" ;;
		zypper) zypper search "$1" ;;
		apk) apk search "$1" ;;
		xbps) xbps-query -Rs "$1" ;;
		emerge) emerge --search "$1" ;;
		eopkg) eopkg search "$1" ;;
	esac 2>/dev/null
}

system_install() {
	case "$PM" in
		apt) as_root apt-get install -y "$1" ;;
		dnf|yum) as_root "$PM" install -y "$1" ;;
		pacman) as_root pacman -S --noconfirm "$1" ;;
		zypper) as_root zypper -n install "$1" ;;
		apk) as_root apk add "$1" ;;
		xbps) as_root xbps-install -y "$1" ;;
		emerge) as_root emerge --ask=n "$1" ;;
		eopkg) as_root eopkg -y install "$1" ;;
	esac
}

system_remove() {
	case "$PM" in
		apt) as_root apt-get remove -y "$1" ;;
		dnf|yum) as_root "$PM" remove -y "$1" ;;
		pacman) as_root pacman -Rs --noconfirm "$1" ;;
		zypper) as_root zypper -n remove "$1" ;;
		apk) as_root apk del "$1" ;;
		xbps) as_root xbps-remove -y "$1" ;;
		emerge) as_root emerge --ask=n --unmerge "$1" ;;
		eopkg) as_root eopkg -y remove "$1" ;;
	esac
}

# ──────────────────────────────────────────────────────────────────────────────
#  Manager: snap / flatpak / homebrew / nix / appimage
# ──────────────────────────────────────────────────────────────────────────────
snap_rows() { snap list 2>/dev/null | tail -n +2 | awk '{print $1 "\t" $2 "\t" $NF}'; }
snap_outdated() { LC_MESSAGES=C snap refresh --list 2>&1 | grep -vi 'all snaps up to date'; }
snap_upgrade() { as_root snap refresh; }
snap_search() { snap find "$1"; }
snap_install() { as_root snap install "$1"; }
snap_remove() { as_root snap remove "$1"; }

flatpak_rows() { flatpak list --columns=application,name,version 2>/dev/null; }
flatpak_outdated() { flatpak remote-ls --updates 2>/dev/null; }
flatpak_upgrade() { local rc; flatpak update -y; rc=$?; flatpak uninstall --unused -y; return $rc; }
flatpak_search() { flatpak search "$1"; }
flatpak_install() { flatpak install -y "$1"; }
flatpak_remove() { flatpak uninstall -y "$1"; }

brew_rows() { brew list --versions 2>/dev/null | awk '{print $1 "\t" $NF}'; }
brew_outdated() { brew update -q >/dev/null 2>&1; brew outdated; }
brew_upgrade() { brew update && brew upgrade && brew cleanup; }
brew_search() { brew search "$1"; }
brew_install() { brew install "$1"; }
brew_remove() { brew uninstall "$1"; }

nix_rows() { nix-env -q 2>/dev/null; }
nix_outdated() { nix-env -u --dry-run 2>&1 | grep -E '^[[:space:]]*upgrading'; }
nix_upgrade() { { nix-channel --update 2>/dev/null; true; } && nix-env -u; }
nix_search() { nix-env -qaP 2>/dev/null | grep -iF -- "$1"; }		# literal match: the text is never a regex
nix_install() { nix-env -iA "nixpkgs.$1"; }
nix_remove() { nix-env -e "$1"; }

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
pip_rows() { "$(pip_bin)" list --format=freeze 2>/dev/null | grep '==' | awk -F'==' '{print $1 "\t" $2}'; }
pip_outdated() { "$(pip_bin)" --timeout 10 --retries 0 list --outdated 2>/dev/null; }
pip_upgrade() {
	if pip_external; then
		msg_dim "System Python is externally managed (PEP 668): skipped. pipx, uv or a virtualenv are upgraded separately."
		return 2
	fi
	local pip; pip=$(pip_bin)
	local -a pkgs=(); local p
	while IFS= read -r p; do [[ -n "$p" ]] && pkgs+=("$p"); done < <("$pip" --timeout 15 --retries 1 list --outdated --format=freeze 2>/dev/null | cut -d= -f1)
	if (( ${#pkgs[@]} == 0 )); then printf '  %sAlready up to date.%s\n' "$GREEN" "$RESET"; return 0; fi
	"$pip" install --upgrade "${pkgs[@]}"
}
pip_search() { "$(pip_bin)" index versions "$1"; }
pip_install() {
	pip_external && { msg_warn "PEP 668: system pip is locked. Use pipx/uv for apps or a virtualenv for libraries."; return 1; }
	"$(pip_bin)" install "$1"
}
pip_remove() {
	pip_external && { msg_warn "PEP 668: system pip is locked."; return 1; }
	"$(pip_bin)" uninstall -y "$1"
}

pipx_rows() { pipx list --short 2>/dev/null | awk '{print $1 "\t" $2}'; }
pipx_upgrade() { pipx upgrade-all; }
pipx_install() { pipx install "$1"; }
pipx_remove() { pipx uninstall "$1"; }

uv_rows() { uv tool list 2>/dev/null | awk '/^[^- \t]/ {print $1 "\t" $2}'; }
uv_upgrade() { uv tool upgrade --all; }
uv_install() { uv tool install "$1"; }
uv_remove() { uv tool uninstall "$1"; }

conda_rows() { conda list 2>/dev/null | grep -v '^#' | awk '{print $1 "\t" $2}'; }
conda_outdated() { conda update --all --dry-run 2>&1 | sed -n '/package plan/,$p'; }
conda_upgrade() { conda update --all -y; }
conda_search() { conda search "*$1*"; }
conda_install() { conda install -y "$1"; }
conda_remove() { conda remove -y "$1"; }

# npm / gem: never escalate silently. When the install prefix is not writable, explain the safer
# user-level setup and use root only if the user explicitly agrees (tools are called by absolute path).
npm_run() {
	local root; root=$(npm root -g 2>/dev/null)
	if [[ -w "$root" ]]; then npm "$@"; return; fi
	confirm_root npm "npm config set prefix ~/.npm-global, then add ~/.npm-global/bin to PATH" || return 1
	as_root "$(command -v npm)" "$@"
}
npm_rows() {
	npm ls -g --depth=0 2>/dev/null | awk 'NR > 1 {
		s = $0; sub(/^[^@A-Za-z0-9]*/, "", s)
		i = match(s, /@[^@]*$/)
		if (i > 1) print substr(s, 1, i - 1) "\t" substr(s, i + 1)
	}'
}
npm_outdated() { npm outdated -g 2>/dev/null; }
npm_upgrade() { npm_run update -g; }
npm_search() { npm search "$1"; }
npm_install() { npm_run install -g "$1"; }
npm_remove() { npm_run uninstall -g "$1"; }

yarn_rows() {
	yarn global list 2>/dev/null | awk '/^info "/ {
		s = $0; sub(/^info "/, "", s); sub(/".*/, "", s)
		i = match(s, /@[^@]*$/)
		if (i > 1) print substr(s, 1, i - 1) "\t" substr(s, i + 1)
	}'
}
yarn_upgrade() { yarn global upgrade; }
yarn_install() { yarn global add "$1"; }
yarn_remove() { yarn global remove "$1"; }

pnpm_rows() { pnpm ls -g --depth=0 2>/dev/null | awk 'NF == 2 && $1 !~ /^(Legend|dependencies:|devDependencies:)/ {print $1 "\t" $2}'; }
pnpm_outdated() { pnpm outdated -g 2>/dev/null; }
pnpm_upgrade() { pnpm update -g --latest; }
pnpm_search() { pnpm search "$1"; }
pnpm_install() { pnpm add -g "$1"; }
pnpm_remove() { pnpm remove -g "$1"; }

gem_run() {
	local dir; dir=$(gem env gemdir 2>/dev/null)
	if [[ -w "$dir" ]]; then gem "$@"; return; fi
	confirm_root gem "gem install --user-install, or set GEM_HOME=~/.gem and add ~/.gem/bin to PATH" || return 1
	as_root "$(command -v gem)" "$@"
}
gem_rows() {
	gem list --local 2>/dev/null | awk 'NF >= 2 && $2 ~ /^\(/ {
		v = $2; if (v == "(default:") v = $3
		gsub(/[(),]/, "", v)
		print $1 "\t" v
	}'
}
gem_outdated() { gem outdated 2>/dev/null; }
gem_upgrade() { gem_run update; }
gem_search() { gem search "$1"; }
gem_install() { gem_run install "$1"; }
gem_remove() { gem_run uninstall "$1"; }

cargo_rows() {
	cargo install --list 2>/dev/null | awk '/^[^ \t]/ {
		v = $2; sub(/^v/, "", v); sub(/:$/, "", v)
		print $1 "\t" v
	}'
}
cargo_outdated() { if have cargo-install-update; then cargo install-update -l 2>/dev/null; else echo "  (install cargo-update for a precise check: cargo install cargo-update)"; fi; }
cargo_upgrade() {
	if have cargo-install-update; then
		cargo install-update -a
		return
	fi
	local -a crates=(); local c rc=0
	while IFS= read -r c; do [[ -n "$c" ]] && crates+=("$c"); done < <(cargo install --list 2>/dev/null | grep -E '^[^[:space:]]' | grep -vF '(' | awk '{print $1}')
	if (( ${#crates[@]} == 0 )); then msg_dim "No crates.io binaries installed."; return 0; fi
	msg_dim "cargo-update not found: reinstalling each crate (cargo install cargo-update makes this faster)."
	for c in "${crates[@]}"; do cargo install "$c" || rc=1; done
	return $rc
}
cargo_search() { msg_dim "(cargo search relies on the crates.io API, results may be limited)"; cargo search "$1"; }
cargo_install() { cargo install "$1"; }
cargo_remove() { cargo uninstall "$1"; }

rustup_rows() { rustup toolchain list 2>/dev/null | awk '{print $1}'; }
rustup_outdated() { rustup check 2>/dev/null; }
rustup_upgrade() { rustup update; }

composer_rows() { composer global show 2>/dev/null | awk 'NF >= 2 {print $1 "\t" $2}'; }
composer_outdated() { composer global outdated 2>/dev/null; }
composer_upgrade() { composer global update; }
composer_search() { composer search "$1"; }
composer_install() { composer global require "$1"; }
composer_remove() { composer global remove "$1"; }

# Table header (TAB-separated column titles) of manager $1
table_header() {
	case "$1" in
		snap)			printf 'Name\tVersion\tNotes' ;;
		flatpak)		printf 'Application\tName\tVersion' ;;
		nix)			printf 'Package' ;;
		appimage)		printf 'Path\tSize' ;;
		uv)				printf 'Tool\tVersion' ;;
		gem)			printf 'Gem\tVersion' ;;
		cargo)			printf 'Crate\tVersion' ;;
		rustup)			printf 'Toolchain' ;;
		*)				printf 'Package\tVersion' ;;
	esac
}

# ──────────────────────────────────────────────────────────────────────────────
#  Manager selection
# ──────────────────────────────────────────────────────────────────────────────
# Resolve a name given on the command line into CHOSEN (optionally requiring capability $2).
# The name is only ever compared with known ids, never executed.
resolve_manager() {
	local want id
	lower "$1"; want=$REPLY
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
		if [[ -z "$capab" ]] || cap "$id" "$capab"; then ids+=("$id"); labels+=("$(lbl "$id")"); fi
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
# Rows of one manager: TAB-separated, empty lines dropped, control characters removed
rows_of() { cap "$1" rows || return 0; "${1}_rows" 2>/dev/null | awk 'NF' | sanitize; }

# Keep only the lines containing $FILTER (case-insensitive, literal text, never a pattern)
filter_rows() {
	if [[ -z "$FILTER" ]]; then cat; return; fi
	FILTER_TEXT="$FILTER" awk 'BEGIN { f = tolower(ENVIRON["FILTER_TEXT"]) } index(tolower($0), f) > 0'
}

# List one manager. If $FILTER is set, only matching rows are kept. With "quiet" as $2,
# managers without any match are hidden.
list_manager() {
	local id="$1" quiet="${2:-}" data n=0
	data=$(rows_of "$id" | filter_rows)
	if [[ -n "$data" ]]; then n=$(printf '%s\n' "$data" | wc -l); n=${n//[[:space:]]/}; fi
	if [[ -n "$FILTER" && "$quiet" == quiet && "$n" == 0 ]]; then return 0; fi
	section "$(lbl "$id")${FILTER:+  (filter: $FILTER - $n found)}"
	printf '%s\n' "$data" | print_table "$(table_header "$id")"
}

list_all() {
	local id
	{ for id in "${MANAGERS[@]}"; do cap "$id" rows && list_manager "$id" quiet; done; } | pager
}

list_by_name() {
	local m
	lower "${1:-}"; m=$REPLY
	if [[ -z "$m" || "$m" == all ]]; then list_all; return; fi
	resolve_manager "$m" rows || { msg_err "Unknown or unavailable manager: $1"; return 1; }
	list_manager "$CHOSEN" | pager
}

choose_list_target() {
	local -a ids=(all) labels=("All"); local id
	for id in "${MANAGERS[@]}"; do cap "$id" rows && { ids+=("$id"); labels+=("$(lbl "$id")"); }; done
	select_menu "Which manager do you want to list?" "${labels[@]}" || return 1
	CHOSEN="${ids[$SELECTED]}"
}

count_totals() {
	if (( STALE )); then
		local id n
		spin_start "Counting installed packages..."
		COUNT_ROWS=()
		for id in "${MANAGERS[@]}"; do
			cap "$id" rows || continue
			n=$(rows_of "$id" | wc -l); n=${n//[[:space:]]/}
			COUNT_ROWS+=("$(lbl "$id")"$'\t'"$n")
		done
		spin_stop
		STALE=0
	fi
	printf '%s\n' "${COUNT_ROWS[@]}" | print_table $'Manager\tInstalled'
}

check_updates() {
	local id
	msg_info "Checking for updates (package indexes are refreshed, nothing is installed)..."
	for id in "${MANAGERS[@]}"; do
		cap "$id" upgrade || continue
		section "$(lbl "$id")"
		if cap "$id" outdated; then
			"${id}_outdated" 2>/dev/null | indent_or_ok
		else
			msg_dim "(no dry-run check available; the upgrade step handles it)"
		fi
	done
}

# ──────────────────────────────────────────────────────────────────────────────
#  Actions: upgrade
# ──────────────────────────────────────────────────────────────────────────────
# Run one manager's upgrade and record the result (0 = ok, 2 = skipped, other = failed)
upgrade_run() {
	local id="$1" rc
	section "$(lbl "$id")"
	"${id}_upgrade"; rc=$?
	case $rc in
		0) RESULTS+=("$(lbl "$id")"$'\t'"$SYM_OK Upgraded") ;;
		2) RESULTS+=("$(lbl "$id")"$'\t'"$SYM_SKIP Skipped") ;;
		*) RESULTS+=("$(lbl "$id")"$'\t'"$SYM_ERR Failed") ;;
	esac
	return $rc
}

reboot_notice() {
	if [[ -f /var/run/reboot-required ]]; then
		printf '  %s%s%s A reboot is required to finish applying the updates.%s\n\n' "$YELLOW" "$BOLD" "$SYM_WARN" "$RESET"
	fi
}

update_all() {
	local id; local -a targets=()
	for id in "${MANAGERS[@]}"; do cap "$id" upgrade && targets+=("$id"); done
	if (( ${#targets[@]} == 0 )); then msg_err "Nothing to update."; return 1; fi
	msg_step "Full system update..."; echo
	printf '  %s%sAdministrator (sudo) privileges may be required.%s\n\n' "$RED" "$BOLD" "$RESET"
	echo "  Managers that will be updated:"
	for id in "${targets[@]}"; do msg_info "$(lbl "$id")"; done
	echo
	confirm "Confirm the global update?" || { msg_skip "Cancelled."; return 0; }
	prime_sudo
	RESULTS=()
	local failed=0
	for id in "${targets[@]}"; do
		upgrade_run "$id"
		(( $? == 1 )) && failed=1
	done
	STALE=1
	section "Summary"
	printf '%s\n' "${RESULTS[@]}" | print_table $'Manager\tResult'
	reboot_notice
	if (( failed )); then
		printf '  %s%sSome updates failed, see the summary above.%s\n' "$RED" "$BOLD" "$RESET"
		return 1
	fi
	printf '  %s%sAll updates are complete.%s\n' "$GREEN" "$BOLD" "$RESET"
}

update_selective() {
	msg_step "Selective update"; echo
	if [[ -n "${1:-}" ]]; then
		resolve_manager "$1" upgrade || { msg_err "Manager '$1' is unknown, unavailable or can't be upgraded."; return 1; }
	else
		choose_manager "Which manager do you want to update?" upgrade || return 1
	fi
	local id="$CHOSEN" rc
	if [[ "$id" == system ]]; then
		confirm "Update the system packages?" || { msg_skip "Cancelled."; return 0; }
	fi
	prime_sudo
	RESULTS=()
	upgrade_run "$id"; rc=$?
	STALE=1
	reboot_notice
	if (( rc == 0 || rc == 2 )); then
		printf '\n  %sDone.%s\n' "$GREEN" "$RESET"
	else
		printf '\n  %sUpdate failed.%s\n' "$RED" "$RESET"
		return 1
	fi
}

# ──────────────────────────────────────────────────────────────────────────────
#  Actions: search / install / remove / export
# ──────────────────────────────────────────────────────────────────────────────
search_app() {
	local pkg="${1:-}"
	if [[ -z "$pkg" ]]; then ask "Name to search for: " || return 1; pkg=$REPLY; fi
	[[ -n "$pkg" ]] || { msg_err "Empty name, search cancelled."; return 1; }
	valid_query "$pkg" || { msg_err "Invalid search text (it must not start with '-' or contain control characters)."; return 1; }
	pick_manager "${2:-}" search "In which manager?" || return 1
	"${CHOSEN}_search" "$pkg" | sanitize | pager
}

install_app() {
	local pkg="${1:-}" rc
	if [[ -z "$pkg" ]]; then ask "Name of the package to install: " || return 1; pkg=$REPLY; fi
	[[ -n "$pkg" ]] || { msg_err "Empty name, installation cancelled."; return 1; }
	valid_pkg "$pkg" || { bad_pkg; return 1; }
	pick_manager "${2:-}" install "Install with which manager?" || return 1
	pkg_allowed_for "$CHOSEN" "$pkg" || return 1
	"${CHOSEN}_install" "$pkg"; rc=$?
	STALE=1
	return $rc
}

remove_app() {
	local pkg="${1:-}" rc
	if [[ -z "$pkg" ]]; then ask "Name of the package to remove: " || return 1; pkg=$REPLY; fi
	[[ -n "$pkg" ]] || { msg_err "Empty name, removal cancelled."; return 1; }
	valid_pkg "$pkg" || { bad_pkg; return 1; }
	pick_manager "${2:-}" remove "Remove with which manager?" || return 1
	pkg_allowed_for "$CHOSEN" "$pkg" || return 1
	printf '  %sRemoving: %s%s%s\n' "$RED" "$BOLD" "$pkg" "$RESET"
	confirm "Confirm?" || { msg_skip "Cancelled."; return 0; }
	"${CHOSEN}_remove" "$pkg"; rc=$?
	STALE=1
	return $rc
}

export_list() {
	local base dir file id host
	base="${XDG_STATE_HOME:-}"
	[[ "$base" == /* ]] || base="${HOME:-}/.local/state"
	[[ "$base" == /* ]] || { msg_err "Cannot find a place to write (HOME is not set)."; return 1; }
	dir="$base/app-manager"
	( umask 077; mkdir -p "$dir" ) && chmod 700 "$dir" || { msg_err "Cannot create $dir"; return 1; }
	host=$(uname -n 2>/dev/null); host=${host//[^[:alnum:]._-]/_}
	file="$dir/apps_${host:-host}_$(date +%Y%m%d_%H%M%S).txt"
	msg_step "Exporting to $file..."; echo
	(
		umask 077           # the list reveals every installed version: keep it private
		set -o noclobber    # never overwrite (or follow a symlink to) an existing file
		{
			echo "=========================================="
			echo "  Applications installed on ${host:-this machine}"
			echo "  Date: $(date)"
			echo "=========================================="
			for id in "${MANAGERS[@]}"; do
				cap "$id" rows || continue
				printf '\n-- %s --------------------------\n' "$(lbl "$id")"
				rows_of "$id" | awk -F'\t' '{ printf "%-45s %s\n", $1, $2 }'
			done
		} > "$file"
	)
	if [[ -s "$file" ]]; then
		printf '  %sExported: %s%s%s\n' "$GREEN" "$BOLD" "$file" "$RESET"
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
		"Toggle ASCII / Unicode mode"
		"$SEP" \
		"Quit"
	)
	while true; do
		drop_sudo
		clear_screen
		banner "App Manager v${VERSION}" "Detect, list, search, install, remove & upgrade everything"
		root_warning
		show_managers
		count_totals
		select_menu "What would you like to do?" "${main_options[@]}" || exit 1
		echo
		case "$SELECTED" in
			0) if choose_list_target; then
				   if ask "Filter (Enter = show everything): "; then FILTER=$REPLY; else FILTER=""; fi
				   list_by_name "$CHOSEN"
				   FILTER=""
			   fi;											pause ;;
			1) search_app;									pause ;;
			2) prime_sudo; check_updates | pager;			pause ;;
			3) update_all;									pause ;;
			4) update_selective;							pause ;;
			5) install_app;									pause ;;
			6) remove_app;									pause ;;
			7) export_list;									pause ;;
			8) show_detection;								pause ;;
			9) ui_toggle_mode;								pause ;;
			10) printf '  %sSee you soon!%s\n\n' "$GREEN" "$RESET";	exit 0 ;;
		esac
	done
}

# ──────────────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────────────
usage() {
	cat <<USAGE
    App Manager v${VERSION} - CLI usage
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
        -u, --update-all            Update everything (asks to confirm unless -y)
        -m, --update-manager MGR    Update a single manager
        -s, --search NAME           Search for a package
        -i, --install NAME          Install a package
        -r, --remove NAME           Remove a package (asks to confirm unless -y)
            --manager MGR           Manager to use with -s/-i/-r
                                    (if omitted, you'll be prompted)
        -e, --export                Export the full installed-app list to a file
        -y, --yes                   Auto-confirm any prompt (non-interactive)
        -a, --ascii                 Force ASCII symbols (no Unicode)
        -v, --version               Show the program version and exit
        -h, --help                  Show this help

    Environment:
        UI_ASCII=1                  Same as --ascii
        NO_COLOR=1                  Disable colors

    Examples:
        ./App-manager.sh --detect
        ./App-manager.sh --list snap
        ./App-manager.sh --list snap --filter code
        ./App-manager.sh -f python
        ./App-manager.sh --search vlc --manager flatpak
        ./App-manager.sh --install htop --manager system -y
        ./App-manager.sh --update-manager npm
        ./App-manager.sh --update-all --yes
USAGE
}

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
			-l|--list)
				DO_LIST=true
				if [[ -n "${2:-}" && "$2" != -* ]]; then LIST_MANAGER="$2"; shift; fi ;;
			-f|--filter) need_arg "$@" || break; FILTER="$2"; DO_LIST=true; shift ;;
			-d|--detect) DO_DETECT=true ;;
			-c|--check-updates) DO_CHECK=true ;;
			-u|-U|--update-all) DO_UPDATE_ALL=true ;;
			-m|--update-manager) need_arg "$@" || break; UPDATE_MANAGER="$2"; shift ;;
			-s|--search) need_arg "$@" || break; SEARCH_PKG="$2"; shift ;;
			-i|--install) need_arg "$@" || break; INSTALL_PKG="$2"; shift ;;
			-r|--remove) need_arg "$@" || break; REMOVE_PKG="$2"; shift ;;
			--manager) need_arg "$@" || break; ACTION_MANAGER="$2"; shift ;;
			-e|--export) DO_EXPORT=true ;;
			-y|--yes) AUTO_YES=true ;;
			-a|--ascii) ui_use_ascii ;;
			-v|--version) echo "App Manager v${VERSION}"; exit 0 ;;
			-h|--help) SHOW_HELP=true ;;
			*) msg_err "Unknown option: $1"; BAD_ARGS=true ;;
		esac
		shift
	done
	if $SHOW_HELP; then usage; exit 0; fi
	if $BAD_ARGS;  then usage; exit 1; fi

	# The filter is shown on screen: never let it carry control characters
	clean "$FILTER"; FILTER=$REPLY

	# Run from a neutral directory: cargo, npm... read config files found in the current directory
	cd "${HOME:-/}" 2>/dev/null || cd /

	detect_managers

	# Any action flag switches the script to non-interactive mode
	if $DO_DETECT || $DO_LIST || $DO_CHECK || $DO_UPDATE_ALL || $DO_EXPORT \
		|| [[ -n "$UPDATE_MANAGER$SEARCH_PKG$INSTALL_PKG$REMOVE_PKG" ]]; then
		local status=0
		root_warning
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
