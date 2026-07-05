#!/usr/bin/env python3
"""
midi_monitor.py

Listens to ALL available MIDI input ports on the machine
and displays each received message in real time.

Dependencies:
    pip install mido python-rtmidi

Usage:
    python midi_monitor.py

Ctrl+C to stop.
"""

import threading
import time
from datetime import datetime

import mido


def listen_port(port_name: str, stop_event: threading.Event):
    """Opens a MIDI port and displays each received message until stopped."""
    try:
        with mido.open_input(port_name) as inport:
            print(f"[+] Listening started on: {port_name}")
            while not stop_event.is_set():
                # non-blocking poll so we can stop cleanly
                for msg in inport.iter_pending():
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(f"[{timestamp}] {port_name:<25} -> {msg}")
                time.sleep(0.001)
    except Exception as e:
        print(f"[!] Error on port '{port_name}': {e}")


def main():
    ports = mido.get_input_names()

    if not ports:
        print("No MIDI input port detected.")
        print("Check that a MIDI device is properly connected / enabled.")
        return

    print("=== MIDI ports detected ===")
    for p in ports:
        print(f"  - {p}")
    print("============================\n")

    stop_event = threading.Event()
    threads = []

    for port in ports:
        t = threading.Thread(target=listen_port, args=(port, stop_event), daemon=True)
        t.start()
        threads.append(t)

    print("Listening on all ports. Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[!] Stop requested, closing ports...")
        stop_event.set()
        for t in threads:
            t.join(timeout=1)
        print("Done.")


if __name__ == "__main__":
    main()
