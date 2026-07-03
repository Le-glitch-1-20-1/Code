#!/usr/bin/env python3
"""
midi_monitor.py

Écoute TOUS les ports MIDI d'entrée disponibles sur la machine
et affiche en temps réel chaque message reçu.

Dépendances :
    pip install mido python-rtmidi

Utilisation :
    python midi_monitor.py

Ctrl+C pour arrêter.
"""

import threading
import time
from datetime import datetime

import mido


def listen_port(port_name: str, stop_event: threading.Event):
    """Ouvre un port MIDI et affiche chaque message reçu jusqu'à l'arrêt."""
    try:
        with mido.open_input(port_name) as inport:
            print(f"[+] Écoute démarrée sur : {port_name}")
            while not stop_event.is_set():
                # poll non-bloquant pour pouvoir s'arrêter proprement
                for msg in inport.iter_pending():
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(f"[{timestamp}] {port_name:<25} -> {msg}")
                time.sleep(0.001)
    except Exception as e:
        print(f"[!] Erreur sur le port '{port_name}': {e}")


def main():
    ports = mido.get_input_names()

    if not ports:
        print("Aucun port MIDI d'entrée détecté.")
        print("Vérifie qu'un périphérique MIDI est bien connecté / activé.")
        return

    print("=== Ports MIDI détectés ===")
    for p in ports:
        print(f"  - {p}")
    print("============================\n")

    stop_event = threading.Event()
    threads = []

    for port in ports:
        t = threading.Thread(target=listen_port, args=(port, stop_event), daemon=True)
        t.start()
        threads.append(t)

    print("Écoute en cours sur tous les ports. Ctrl+C pour arrêter.\n")

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[!] Arrêt demandé, fermeture des ports...")
        stop_event.set()
        for t in threads:
            t.join(timeout=1)
        print("Terminé.")


if __name__ == "__main__":
    main()
	