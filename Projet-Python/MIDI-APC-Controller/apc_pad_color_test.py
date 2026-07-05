import rtmidi
import time

midi_out = rtmidi.MidiOut()
ports = midi_out.get_ports()
idx = next((i for i, p in enumerate(ports) if "APC" in p and "Control" in p), None)
midi_out.open_port(idx)

NOTE = 33  # A1 = GIMP button

# Test all colors from 0 to 127
for color in range(128):
    midi_out.send_message([0x90, NOTE, color])
    print(f"Color: {color}")
    time.sleep(0.5)
