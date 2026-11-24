#!/usr/bin/env bash
# Detect Manager - package managers, build tools, system and desktop environment.
# Reports which installation methods are available (with versions), then the operating
# system, the kernel and, on Linux, the desktop environment.
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
	local i lbl ind
	ind=$(rep " " $(( ${#SYM_SEL} + 3 )))		# same width as "  [»] "
	for i in "${!_MENU_OPTS[@]}"; do
		lbl=${_MENU_OPTS[i]}
		(( ${#lbl} > _MENU_W )) && lbl="${lbl:0:_MENU_W-${#SYM_DOT}}${SYM_DOT}"
		printf '\033[2K'
		if [[ "${_MENU_OPTS[i]}" == "$SEP" ]]; then
			printf '  %s%s%s\n' "$DIM" "$(rep "$BX_H" 28)" "$RESET"
		elif (( i == _MENU_IDX )); then
			printf '  %s%s%s %s%s\n' "$CYAN" "$BOLD" "$SYM_SEL" "$lbl" "$RESET"
		else
			printf '%s%s\n' "$ind" "$lbl"
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
	local i box lbl ind
	ind=$(rep " " $(( ${#SYM_SEL} + 3 )))
	for i in "${!_CB_OPTS[@]}"; do
		lbl=${_CB_OPTS[i]}
		(( ${#lbl} > _MENU_W )) && lbl="${lbl:0:_MENU_W-${#SYM_DOT}}${SYM_DOT}"
		printf '\033[2K'
		if (( _CB_ON[i] )); then box="${GREEN}${SYM_BOX_ON}${RESET}"; else box="$SYM_BOX_OFF"; fi
		if (( i == _CB_IDX )); then
			printf '  %s%s%s%s %s %s%s%s%s\n' "$CYAN" "$BOLD" "$SYM_SEL" "$RESET" "$box" "$CYAN" "$BOLD" "$lbl" "$RESET"
		else
			printf '%s%s %s\n' "$ind" "$box" "$lbl"
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

VERSION="2.1.0"
readonly VERSION

# ──────────────────────────────────────────────────────────────────────────────
#  Global state
# ──────────────────────────────────────────────────────────────────────────────
FOUND=0				# total number of tools detected
GROUP_HITS=0		# tools detected in the current group
SYS_HITS=0			# system package managers detected

ui_traps

# ──────────────────────────────────────────────────────────────────────────────
#  Detection helpers
# ──────────────────────────────────────────────────────────────────────────────
# First useful line of a tool's version output.
# stdin is closed and a timeout is applied (when the system has one) so nothing can block;
# the output is external text, so control characters are removed.
get_version() {		# $1 = command, $2 = version option(s)
	local out
	local -a pre=() opts=()
	read -ra opts <<< "${2:-}"
	if have timeout; then pre=(timeout 3)
	fi
	out=$("${pre[@]}" "$1" "${opts[@]}" </dev/null 2>&1 | head -n 1 | sanitize)
	out=${out#"${out%%[![:space:]]*}"}				# trim leading spaces
	printf '%s' "${out:0:80}"
}

group_begin() { section "$1"; GROUP_HITS=0; }
group_end() { (( GROUP_HITS )) || msg_dim "(none)"; }

# Print one detected tool and update the counters. Usage: report name path version
report() {
	local v="${3:-}"
	v=${v//[[:cntrl:]]/}
	item_ok "$1" "$2" "$v"
	(( ++FOUND )); (( ++GROUP_HITS ))
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
	local before

	group_begin "System package managers"
	before=$FOUND
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
	check pkg		pkg			--version
	SYS_HITS=$(( FOUND - before ))
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
	check clang		clang
	check git		git
	group_end

	group_begin "Download tools"
	check curl		curl
	check wget		wget
	group_end

	echo
	hr
	(( SYS_HITS )) || msg_warn "No system package manager detected."
	kv "Total detected" "$FOUND"
}

# Pretty name of the operating system. Parsed, never sourced: /etc/os-release defines VERSION,
# which would collide with this script's own read-only variable.
os_name() {
	local n=""
	if [[ -r /etc/os-release ]]; then
		n=$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release | head -n 1 | tr -d "\"'")
	fi
	printf '%s' "${n:-unknown}"
}

detect_system() {
	section "System"
	kv "Distribution" "$(os_name)"
	kv "Kernel" "$(uname -sr 2>/dev/null)"
	kv "Architecture" "$(uname -m 2>/dev/null)"
}

# Is a process with this exact name running?
running() { have pgrep && pgrep -x "$1" >/dev/null 2>&1; }

detect_desktop() {
	section "Desktop environment"

	# DE name: XDG_CURRENT_DESKTOP is the most reliable
	local de="${XDG_CURRENT_DESKTOP:-${DESKTOP_SESSION:-}}" p
	# Fallback: look at the running processes
	if [[ -z "$de" ]]; then
		for p in gnome-shell plasmashell xfce4-session cinnamon mate-session lxqt-session lxsession budgie-panel cosmic-session; do
			if running "$p"; then de="$p"; break; fi
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
		if running "$p"; then wm="$p"; break; fi
	done
	if [[ "$wm" == gnome-shell ]]; then
		kv "Window mgr" "mutter (via gnome-shell)"
	elif [[ -n "$wm" ]]; then
		kv "Window mgr" "$wm"
	fi

	# Display manager: read from systemd first
	local dm="" target=""
	if [[ -e /etc/systemd/system/display-manager.service ]]; then
		target=$(readlink /etc/systemd/system/display-manager.service 2>/dev/null)
		dm=$(basename "${target:-display-manager.service}" .service)
		[[ "$dm" == display-manager ]] && dm=""
	fi
	if [[ -z "$dm" ]]; then
		for p in gdm gdm3 sddm lightdm lxdm ly greetd; do
			if running "$p"; then dm="$p"; break; fi
		done
	fi
	[[ -n "$dm" ]] && kv "Display mgr" "$dm"
	echo
}

# ──────────────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────────────
usage() {
	cat <<USAGE
    Detect Manager v${VERSION} - CLI usage
    Detects package managers, build tools, system and desktop environment.

        -a, --ascii                 Force ASCII symbols (no Unicode)
        -v, --version               Show the program version and exit
        -h, --help                  Show this help

    Environment:
        UI_ASCII=1                  Same as --ascii
        NO_COLOR=1                  Disable colors

    Example:
        ./Detect-manager.sh
        NO_COLOR=1 ./Detect-manager.sh > report.txt
USAGE
}

main() {
	local bad=false
	while [[ $# -gt 0 ]]; do
		case "$1" in
			-a|--ascii)		ui_use_ascii ;;
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
