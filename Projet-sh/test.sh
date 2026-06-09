#!/bin/bash

# ─────────────────────────────────────────
#  Testeur MIDI en temps réel
#  Compatible Ubuntu/Debian (ALSA)
#  Usage : bash test_midi.sh
# ─────────────────────────────────────────

RESET='\033[0m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'

NOTE_NAMES=("Do" "Do#" "Ré" "Ré#" "Mi" "Fa" "Fa#" "Sol" "Sol#" "La" "La#" "Si")

note_name() {
    local n=$1
    local idx=$((n % 12))
    local oct=$((n / 12 - 1))
    echo "${NOTE_NAMES[$idx]}$oct"
}

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}        Testeur MIDI − Linux             ${RESET}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

# ── Vérification des dépendances ──────────────────────────────────────────────
MISSING=0
for cmd in aseqdump aconnect; do
    if ! command -v "$cmd" &>/dev/null; then
        echo -e "${RED}✗ '$cmd' n'est pas installé.${RESET}"
        MISSING=1
    fi
done

if [ "$MISSING" -eq 1 ]; then
    echo -e "\n  Installe les outils manquants avec :"
    echo -e "  ${CYAN}sudo apt install alsa-utils${RESET}\n"
    exit 1
fi

# ── Vérification du groupe audio ──────────────────────────────────────────────
if ! groups | grep -qw audio; then
    echo -e "${YELLOW}⚠ Tu n'es pas dans le groupe 'audio'. Si aucun appareil n'est détecté, lance :${RESET}"
    echo -e "  ${CYAN}sudo usermod -aG audio \$USER${RESET}  puis reconnecte-toi."
    echo ""
fi

# ── Détection des ports MIDI ──────────────────────────────────────────────────
echo -e "${BOLD}Appareils et ports MIDI détectés :${RESET}"
echo ""

declare -a ALL_PORTS
declare -A PORT_NAMES

# Lit la sortie de aconnect -l ligne par ligne
CLIENT_NUM=""
CLIENT_NAME=""

while IFS= read -r line; do
    # Ligne de client (appareil) — supporte les variantes de format ALSA
    if echo "$line" | grep -qE "^client [0-9]+:"; then
        CLIENT_NUM=$(echo "$line" | grep -oP "^client \K[0-9]+")
        CLIENT_NAME=$(echo "$line" | grep -oP "'\K[^']+" | head -1)
        # Exclure : System (0), Midi Through (14), PipeWire (>= 128)
        if [ "$CLIENT_NUM" -eq 0 ] || [ "$CLIENT_NUM" -eq 14 ] || [ "$CLIENT_NUM" -ge 128 ]; then
            CLIENT_NUM=""
        fi
    # Ligne de port (indentée, commence par des espaces puis un numéro)
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

if [ ${#ALL_PORTS[@]} -eq 0 ]; then
    echo -e "${RED}  Aucun appareil MIDI trouvé.${RESET}"
    echo ""
    echo -e "  Vérifie que ton appareil est bien branché, puis :"
    echo -e "  ${CYAN}aconnect -l${RESET}  — liste tous les clients MIDI"
    echo -e "  ${CYAN}amidi -l${RESET}     — liste les ports MIDI bruts"
    echo ""
    echo -e "  Si ton appareil n'apparaît pas du tout :"
    echo -e "  ${CYAN}lsusb${RESET}        — vérifie qu'il est reconnu par Linux"
    echo -e "  ${CYAN}dmesg | tail -20${RESET} — cherche des erreurs au branchement"
    exit 1
fi

# ── Écoute MIDI ───────────────────────────────────────────────────────────────
echo -e "${GREEN}✓ ${#ALL_PORTS[@]} port(s) trouvé(s) — écoute en cours...${RESET}"
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  Appuie sur des touches, pads, boutons..."
echo -e "  Ctrl+C pour quitter."
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
printf "  %-8s %-28s %-12s %-10s %s\n" "PORT" "APPAREIL / PORT" "TYPE" "VALEUR" "DÉTAIL"
echo "  ────────────────────────────────────────────────────────────────────"

PORTS_ARG=$(IFS=,; echo "${ALL_PORTS[*]}")

aseqdump -p "$PORTS_ARG" 2>/dev/null | while IFS= read -r line; do

    # Extrait la source (format "  24:0   ..." ou "Source  24:0   ...")
    SRC=$(echo "$line" | grep -oP "[0-9]+:[0-9]+" | head -1)
    [ -z "$SRC" ] && continue

    # Ignore les lignes d'en-tête d'aseqdump
    echo "$line" | grep -q "Waiting\|Source\|Connected" && continue

    PNAME="${PORT_NAMES[$SRC]:-$SRC}"

    if echo "$line" | grep -qi "Note on"; then
        NOTE=$(echo "$line" | grep -oP "note \K[0-9]+")
        VEL=$(echo "$line" | grep -oP "velocity \K[0-9]+")
        [ -z "$NOTE" ] && continue
        # Note on avec velocity 0 = Note off déguisé
        if [ "$VEL" = "0" ]; then
            NAME=$(note_name "$NOTE")
            printf "  %-8s %-28s %-12s %-10s %s\n" \
                "$SRC" "${PNAME:0:28}" "Note OFF" "" "$NAME"
            continue
        fi
        NAME=$(note_name "$NOTE")
        printf "  ${GREEN}%-8s${RESET} %-28s ${BOLD}%-12s${RESET} %-10s %s\n" \
            "$SRC" "${PNAME:0:28}" "Note ON" "vel=$VEL" "$NAME (MIDI $NOTE)"

    elif echo "$line" | grep -qi "Note off"; then
        NOTE=$(echo "$line" | grep -oP "note \K[0-9]+")
        [ -z "$NOTE" ] && continue
        NAME=$(note_name "$NOTE")
        printf "  %-8s %-28s %-12s %-10s %s\n" \
            "$SRC" "${PNAME:0:28}" "Note OFF" "" "$NAME"

    elif echo "$line" | grep -qi "Control change"; then
        CTRL=$(echo "$line" | grep -oP "controller \K[0-9]+")
        VAL=$(echo "$line" | grep -oP "value \K[0-9]+")
        [ -z "$CTRL" ] && continue
        printf "  ${YELLOW}%-8s${RESET} %-28s ${YELLOW}%-12s${RESET} %-10s %s\n" \
            "$SRC" "${PNAME:0:28}" "CC" "val=$VAL" "Contrôleur #$CTRL"

    elif echo "$line" | grep -qi "Program change"; then
        PROG=$(echo "$line" | grep -oP "program \K[0-9]+")
        printf "  ${CYAN}%-8s${RESET} %-28s ${CYAN}%-12s${RESET} %s\n" \
            "$SRC" "${PNAME:0:28}" "Prog CH" "#$PROG"

    elif echo "$line" | grep -qi "Pitch bend"; then
        VAL=$(echo "$line" | grep -oP "value \K-?[0-9]+")
        printf "  ${CYAN}%-8s${RESET} %-28s ${CYAN}%-12s${RESET} %s\n" \
            "$SRC" "${PNAME:0:28}" "Pitch" "$VAL"

    elif echo "$line" | grep -qi "Channel pressure\|Aftertouch"; then
        VAL=$(echo "$line" | grep -oP "value \K[0-9]+")
        printf "  ${CYAN}%-8s${RESET} %-28s ${CYAN}%-12s${RESET} %s\n" \
            "$SRC" "${PNAME:0:28}" "Aftertouch" "val=$VAL"

    elif echo "$line" | grep -qi "Sysex"; then
        printf "  %-8s %-28s %-12s\n" \
            "$SRC" "${PNAME:0:28}" "SysEx"
    fi

done
