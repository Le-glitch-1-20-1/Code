#!/bin/bash
# Exit code of a pipeline is the last command that failed, not just the last command
set -o pipefail

# Program version, mirrors the VERSION constant of the Python interface
VERSION="2.0.0"

# Color codes used for terminal output
RESET='\033[0m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
DIM='\033[2m'

# CLI flags and option variables, populated by argument parsing
SELECTED_PORTS=()
LIST_ONLY=false
NONINTERACTIVE=false
# Sentinel value used in menu option lists to render a divider line instead of a choice
readonly SEP="---sep---"
# Note names used to turn a MIDI note number into a readable name
NOTE_NAMES=("C" "C#" "D" "D#" "E" "F" "F#" "G" "G#" "A" "A#" "B")
MISSING=0
CLIENT_NUM=""
CLIENT_NAME=""
# Detected ports and their human-readable names, filled by detect_ports
declare -a ALL_PORTS
declare -A PORT_NAMES

# Stop cleanly on Ctrl+C, always restoring the terminal state first
trap 'stty sane 2>/dev/null; tput cnorm 2>/dev/null; echo -e "${RESET}\n  Stopping listening."; exit 0' INT

# Print CLI usage / help text
usage() {
	cat <<-EOF

	    MIDI Tester - Linux — CLI usage
	    Without any option, all detected MIDI ports are listened to
	    (same behaviour as before).

	        -p, --port CLIENT:PORT    Listen only on this port (repeatable)
	        -l, --list                Just list detected devices/ports, then exit
	        -v, --version              Show the program version and exit
	        -h, --help                Show this help

	    Examples:
	        ./midi_tester.sh
	        ./midi_tester.sh --list
	        ./midi_tester.sh --port 20:0
	        ./midi_tester.sh -p 20:0 -p 24:0
	EOF
}

# Turn a MIDI note number into a readable note name + octave
note_name() {
	local n=$1
	local idx=$((n % 12))
	local oct=$((n / 12 - 1))
	echo "${NOTE_NAMES[$idx]}$oct"
}

# Return the current terminal width, falling back to 80 columns
term_width() {
	tput cols 2>/dev/null || echo 80
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

# Draw a rounded panel with a bold title and a dim subtitle, like rich.Panel
draw_panel() {
	local title="$1"
	local subtitle="$2"
	local width
	width=$(term_width)
	local box_width=$((width - 8))
	[ "$box_width" -gt 64 ] && box_width=64
	local border
	border=$(printf -- '─%.0s' $(seq 1 "$box_width"))
	echo
	echo -e "  ${CYAN}╭${border}╮${RESET}"
	echo -e "  ${CYAN}│$(pad_center "" "$box_width")│${RESET}"
	echo -e "  ${CYAN}│${BOLD}$(pad_center "$title" "$box_width")${RESET}${CYAN}│${RESET}"
	echo -e "  ${CYAN}│${RESET}${DIM}$(pad_center "$subtitle" "$box_width")${RESET}${CYAN}│${RESET}"
	echo -e "  ${CYAN}│$(pad_center "" "$box_width")│${RESET}"
	echo -e "  ${CYAN}╰${border}╯${RESET}"
	echo
}

# Draw a horizontal rule with an embedded title, like rich.rule.Rule
draw_rule() {
	local title="$1"
	local width
	width=$(term_width)
	local left="── ${title} "
	local dash_count=$((width - ${#left} - 2))
	[ "$dash_count" -lt 0 ] && dash_count=0
	local dashes
	dashes=$(printf -- '─%.0s' $(seq 1 "$dash_count"))
	echo -e "${YELLOW}${BOLD}${left}${dashes}${RESET}"
}

# Clear the screen and draw the welcome panel
splash_screen() {
	clear
	draw_panel "MIDI Tester - Linux  v${VERSION}" "ALSA MIDI listener for Linux"
}

# Single-choice arrow-key menu, echoes the chosen index on stdout
# Pass "$SEP" as an option to render a non-selectable divider line
select_menu() {
	local prompt="$1"
	shift
	local options=("$@")
	local count=${#options[@]}
	local selected=0
	while [ "${options[$selected]}" = "$SEP" ]; do
		selected=$(( (selected + 1) % count ))
	done
	local first_draw=1
	local key esc i new
	tput civis >&2
	stty -echo -icanon min 1 time 0
	while true; do
		if [ "$first_draw" -eq 0 ]; then
			tput cuu "$((count + 1))" >&2
			tput ed >&2
		fi
		first_draw=0
		echo -e "  ${CYAN}?${RESET} ${BOLD}${prompt}${RESET} ${DIM}(Use arrow keys)${RESET}" >&2
		for ((i = 0; i < count; i++)); do
			if [ "${options[$i]}" = "$SEP" ]; then
				echo -e "  ${DIM}────────────────────────────${RESET}" >&2
			elif [ "$i" -eq "$selected" ]; then
				echo -e "  ${CYAN}» ${options[$i]}${RESET}" >&2
			else
				echo -e "    ${options[$i]}" >&2
			fi
		done
		IFS= read -rsn1 key
		if [[ "$key" == $'\x1b' ]]; then
			read -rsn2 -t 0.01 esc
			case "$esc" in
				'[A')
					new=$selected
					while true; do
						new=$(( (new - 1 + count) % count ))
						[ "${options[$new]}" != "$SEP" ] && break
					done
					selected=$new
					;;
				'[B')
					new=$selected
					while true; do
						new=$(( (new + 1) % count ))
						[ "${options[$new]}" != "$SEP" ] && break
					done
					selected=$new
					;;
			esac
		elif [[ -z "$key" ]]; then
			break
		fi
	done
	tput cuu "$((count + 1))" >&2
	tput ed >&2
	echo -e "  ${GREEN}✔${RESET} ${BOLD}${prompt}${RESET} ${CYAN}${options[$selected]}${RESET}" >&2
	stty sane
	tput cnorm >&2
	echo "$selected"
}

# Multi-choice arrow-key menu (space to toggle), echoes chosen indices on stdout
checkbox_menu() {
	local prompt="$1"
	shift
	local options=("$@")
	local count=${#options[@]}
	local cursor=0
	local first_draw=1
	local key esc i box
	local -a checked
	for ((i = 0; i < count; i++)); do
		checked[i]=0
	done
	tput civis >&2
	stty -echo -icanon min 1 time 0
	while true; do
		if [ "$first_draw" -eq 0 ]; then
			tput cuu "$((count + 1))" >&2
			tput ed >&2
		fi
		first_draw=0
		echo -e "  ${CYAN}?${RESET} ${BOLD}${prompt}${RESET} ${DIM}(space: toggle, enter: confirm)${RESET}" >&2
		for ((i = 0; i < count; i++)); do
			box="[ ]"
			[ "${checked[$i]}" -eq 1 ] && box="[${GREEN}x${RESET}]"
			if [ "$i" -eq "$cursor" ]; then
				echo -e "  ${CYAN}» ${box} ${options[$i]}${RESET}" >&2
			else
				echo -e "    ${box} ${options[$i]}" >&2
			fi
		done
		IFS= read -rsn1 key
		case "$key" in
			$'\x1b')
				read -rsn2 -t 0.01 esc
				case "$esc" in
					'[A') cursor=$(( (cursor - 1 + count) % count )) ;;
					'[B') cursor=$(( (cursor + 1) % count )) ;;
				esac
				;;
			' ')
				if [ "${checked[$cursor]}" -eq 1 ]; then
					checked[$cursor]=0
				else
					checked[$cursor]=1
				fi
				;;
			"")
				break
				;;
		esac
	done
	tput cuu "$((count + 1))" >&2
	tput ed >&2
	local result=()
	local names=()
	for ((i = 0; i < count; i++)); do
		if [ "${checked[$i]}" -eq 1 ]; then
			result+=("$i")
			names+=("${options[$i]}")
		fi
	done
	local summary
	summary=$(IFS=', '; echo "${names[*]}")
	if [ -n "$summary" ]; then
		echo -e "  ${GREEN}✔${RESET} ${BOLD}${prompt}${RESET} ${CYAN}${summary}${RESET}" >&2
	fi
	stty sane
	tput cnorm >&2
	echo "${result[@]}"
}

# Check required tools and shell features, exit early if something is missing
check_dependencies() {
	for cmd in aseqdump aconnect; do
		if ! command -v "$cmd" &>/dev/null; then
			echo -e "${RED}✗ '$cmd' is not installed.${RESET}"
			MISSING=1
		fi
	done
	if [ "$MISSING" -eq 1 ]; then
		echo -e "\n  Install the missing tools with:"
		echo -e "  ${CYAN}sudo apt install alsa-utils${RESET}\n"
		exit 1
	fi
	if ! echo "test123" | grep -qP "\d" 2>/dev/null; then
		echo -e "${RED}✗ Your version of 'grep' does not support Perl regex (-P).${RESET}"
		echo -e "  Install GNU grep: ${CYAN}sudo apt install grep${RESET}\n"
		exit 1
	fi
	if ! groups | grep -qw audio; then
		echo -e "${YELLOW}⚠ You are not in the 'audio' group. If no device is detected, run:${RESET}"
		echo -e "  ${CYAN}sudo usermod -aG audio \$USER${RESET}  then log out and back in."
		echo ""
	fi
}

# Parse "aconnect -l" output, fill ALL_PORTS / PORT_NAMES, print each port found
detect_ports() {
	draw_rule "Detected devices"
	echo ""
	while IFS= read -r line; do
		if echo "$line" | grep -qE "^client [0-9]+:"; then
			CLIENT_NUM=$(echo "$line" | grep -oP "^client \K[0-9]+")
			CLIENT_NAME=$(echo "$line" | grep -oP "'\K[^']+" | head -1)
			if [ "$CLIENT_NUM" -eq 0 ] || [ "$CLIENT_NUM" -eq 14 ] || [ "$CLIENT_NUM" -ge 128 ]; then
				CLIENT_NUM=""
			fi
		elif [ -n "$CLIENT_NUM" ] && echo "$line" | grep -qP "^\s+[0-9]+ '"; then
			PORT_NUM=$(echo "$line" | grep -oP "^\s+\K[0-9]+")
			PORT_NAME=$(echo "$line" | grep -oP "'\K[^']+" | head -1)
			KEY="${CLIENT_NUM}:${PORT_NUM}"
			ALL_PORTS+=("$KEY")
			PORT_NAMES["$KEY"]="$CLIENT_NAME / $PORT_NAME"
			echo -e "  ${CYAN}▸${RESET} ${BOLD}$KEY${RESET}  $CLIENT_NAME → $PORT_NAME"
		fi
	done < <(aconnect -l 2>/dev/null)
	echo ""
}

# Let the user pick one or more detected ports, filling SELECTED_PORTS
choose_ports_interactive() {
	local labels=()
	local key picked i
	for key in "${ALL_PORTS[@]}"; do
		labels+=("$key  ${PORT_NAMES[$key]}")
	done
	while true; do
		picked=$(checkbox_menu "Select port(s):" "${labels[@]}")
		echo >&2
		if [ -n "$picked" ]; then
			break
		fi
		echo -e "  ${YELLOW}⚠ No port selected (press space to check a box, then enter).${RESET}" >&2
		echo -e "  ${DIM}Press any key to try again...${RESET}" >&2
		read -rsn1 -s
	done
	SELECTED_PORTS=()
	for i in $picked; do
		SELECTED_PORTS+=("${ALL_PORTS[$i]}")
	done
}

# Interactive menu shown when the script is run without any CLI flag
show_menu() {
	local options=("Listen to all detected ports" "Choose specific port(s) to listen to" "Just list the ports, then exit" "$SEP" "Quit")
	local idx
	idx=$(select_menu "What would you like to do?" "${options[@]}")
	echo >&2
	case "$idx" in
		0) SELECTED_PORTS=() ;;
		1) choose_ports_interactive ;;
		2) LIST_ONLY=true ;;
		4) echo -e "  ${GREEN}See you soon!${RESET}\n" >&2; exit 0 ;;
	esac
}

# Format and print one parsed line coming from aseqdump
print_event() {
	local line="$1"
	local SRC; SRC=$(echo "$line" | grep -oP "[0-9]+:[0-9]+" | head -1)
	[ -z "$SRC" ] && return
	echo "$line" | grep -q "Waiting\|Source\|Connected" && return
	local PNAME="${PORT_NAMES[$SRC]:-$SRC}"
	local CH; CH=$(echo "$line" | grep -oP "[^0-9]\K[0-9]+(?=,)" | head -1)
	local CH_TXT=""
	[ -n "$CH" ] && CH_TXT=" (ch $CH)"
	if echo "$line" | grep -qi "Note on"; then
		local NOTE; NOTE=$(echo "$line" | grep -oP "note \K[0-9]+")
		local VEL; VEL=$(echo "$line" | grep -oP "velocity \K[0-9]+")
		[ -z "$NOTE" ] && return
		if [ "$VEL" = "0" ]; then
			local NAME; NAME=$(note_name "$NOTE")
			printf "  %-8s %-28s %-12s %-10s %s\n" "$SRC" "${PNAME:0:28}" "Note OFF" "" "$NAME$CH_TXT"
			return
		fi
		local NAME; NAME=$(note_name "$NOTE")
		printf "  ${GREEN}%-8s${RESET} %-28s ${BOLD}%-12s${RESET} %-10s %s\n" "$SRC" "${PNAME:0:28}" "Note ON" "vel=$VEL" "$NAME (MIDI $NOTE)$CH_TXT"
	elif echo "$line" | grep -qi "Note off"; then
		local NOTE; NOTE=$(echo "$line" | grep -oP "note \K[0-9]+")
		[ -z "$NOTE" ] && return
		local NAME; NAME=$(note_name "$NOTE")
		printf "  %-8s %-28s %-12s %-10s %s\n" "$SRC" "${PNAME:0:28}" "Note OFF" "" "$NAME$CH_TXT"
	elif echo "$line" | grep -qi "Control change"; then
		local CTRL; CTRL=$(echo "$line" | grep -oP "controller \K[0-9]+")
		local VAL; VAL=$(echo "$line" | grep -oP "value \K[0-9]+")
		[ -z "$CTRL" ] && return
		printf "  ${YELLOW}%-8s${RESET} %-28s ${YELLOW}%-12s${RESET} %-10s %s\n" "$SRC" "${PNAME:0:28}" "CC" "val=$VAL" "Controller #$CTRL$CH_TXT"
	elif echo "$line" | grep -qi "Program change"; then
		local PROG; PROG=$(echo "$line" | grep -oP "program \K[0-9]+")
		printf "  ${CYAN}%-8s${RESET} %-28s ${CYAN}%-12s${RESET} %s\n" "$SRC" "${PNAME:0:28}" "Prog CH" "#$PROG$CH_TXT"
	elif echo "$line" | grep -qi "Pitch bend"; then
		local VAL; VAL=$(echo "$line" | grep -oP "value \K-?[0-9]+")
		printf "  ${CYAN}%-8s${RESET} %-28s ${CYAN}%-12s${RESET} %s\n" "$SRC" "${PNAME:0:28}" "Pitch" "$VAL$CH_TXT"
	elif echo "$line" | grep -qi "Channel pressure\|Aftertouch"; then
		local VAL; VAL=$(echo "$line" | grep -oP "value \K[0-9]+")
		printf "  ${CYAN}%-8s${RESET} %-28s ${CYAN}%-12s${RESET} %s\n" "$SRC" "${PNAME:0:28}" "Aftertouch" "val=$VAL$CH_TXT"
	elif echo "$line" | grep -qi "Sysex"; then
		printf "  %-8s %-28s %-12s\n" "$SRC" "${PNAME:0:28}" "SysEx"
	fi
}

# Build the port list to listen on, print the header, then stream formatted events until Ctrl+C
listen_and_print() {
	local PORTS_ARG
	draw_rule "Listening"
	if [ ${#SELECTED_PORTS[@]} -gt 0 ]; then
		PORTS_ARG=$(IFS=,; echo "${SELECTED_PORTS[*]}")
		echo -e "  ${GREEN}✓ Listening on selected port(s): $PORTS_ARG${RESET}"
	else
		PORTS_ARG=$(IFS=,; echo "${ALL_PORTS[*]}")
		echo -e "  ${GREEN}✓ ${#ALL_PORTS[@]} port(s) found — listening...${RESET}"
	fi
	echo -e "  ${DIM}Press keys, pads, buttons — Ctrl+C to quit.${RESET}"
	echo ""
	printf "  %-8s %-28s %-12s %-10s %s\n" "PORT" "DEVICE / PORT" "TYPE" "VALUE" "DETAIL"
	echo "  ────────────────────────────────────────────────────────────────────"
	aseqdump -p "$PORTS_ARG" 2>/dev/null | while IFS= read -r line; do
		print_event "$line"
	done
}

# Entry point: parse CLI arguments, detect devices, then listen non-interactively or via the menu
main() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
			-p|--port)		SELECTED_PORTS+=("${2:-}"); shift ;;
			-l|--list)		LIST_ONLY=true ;;
			-v|--version)	echo "MIDI Tester v${VERSION}"; exit 0 ;;
			-h|--help)		usage; exit 0 ;;
			*)				echo "Unknown option: $1" >&2; usage; exit 1 ;;
		esac
		shift
	done
	# Validate any port given on the CLI
	for p in "${SELECTED_PORTS[@]:-}"; do
		[ -z "$p" ] && continue
		if [[ ! "$p" =~ ^[0-9]+:[0-9]+$ ]]; then
			echo -e "${RED}✗ Invalid port format: '$p' (expected CLIENT:PORT, e.g. 20:0)${RESET}" >&2
			exit 1
		fi
	done
	# Any CLI flag given switches the script to non-interactive mode (menu is skipped)
	if $LIST_ONLY || [ ${#SELECTED_PORTS[@]} -gt 0 ]; then
		NONINTERACTIVE=true
	fi
	splash_screen
	check_dependencies
	detect_ports
	if [ ${#ALL_PORTS[@]} -eq 0 ] && [ ${#SELECTED_PORTS[@]} -eq 0 ]; then
		echo -e "${RED}  No MIDI device found.${RESET}"
		echo ""
		echo -e "  Check that your device is plugged in, then try:"
		echo -e "  ${CYAN}aconnect -l${RESET}  — lists all MIDI clients"
		echo -e "  ${CYAN}amidi -l${RESET}	 — lists raw MIDI ports"
		echo ""
		echo -e "  If your device doesn't show up at all:"
		echo -e "  ${CYAN}lsusb${RESET}		— check that Linux recognizes it"
		echo -e "  ${CYAN}dmesg | tail -20${RESET} — look for errors when plugging it in"
		exit 1
	fi
	# No CLI flag given: show the interactive menu (list all / choose ports / list only / quit)
	$NONINTERACTIVE || show_menu
	if $LIST_ONLY; then
		exit 0
	fi
	listen_and_print
}

main "$@"
