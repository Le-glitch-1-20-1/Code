# Projet-sh

Standalone Bash scripts with an interactive command-line interface (menus, colors,
automatic detection of available tools) and a complete CLI mode.
All scripts share the same console style, described in [`STYLE-GUIDE.md`](STYLE-GUIDE.md).

They run on Linux, macOS, BSD, WSL, Git Bash and Termux (`Midi-tester.sh` needs ALSA, so Linux only).

---

## Scripts

### `App-manager.sh` — Application manager

One interface to list, search, install, remove and update packages across several managers
(system/apt/dnf/pacman..., snap, flatpak, brew, nix, appimage, pip, pipx, uv, conda, npm, yarn,
pnpm, gem, cargo, rustup, composer). It detects the managers available on the machine.

```bash
./App-manager.sh                                     # interactive menu
./App-manager.sh --detect                            # detect managers and tools
./App-manager.sh --list snap                         # list snap packages
./App-manager.sh --list snap --filter code           # list, filtered by text
./App-manager.sh --search vlc --manager flatpak      # search for a package
./App-manager.sh --install htop --manager system -y  # install without confirmation
./App-manager.sh --remove htop --manager system --yes
./App-manager.sh --update-manager npm                # update a single manager
./App-manager.sh --update-all --yes                  # update everything
./App-manager.sh --check-updates                     # list available updates (refreshes indexes, installs nothing)
./App-manager.sh --export                            # export the list of installed apps
./App-manager.sh --version
./App-manager.sh --help
```

### `Detect-manager.sh` — Tool and environment detector

Shows the package managers and build/download tools present (with versions), then the
operating system, kernel and, on Linux, the desktop environment (version, Wayland/X11 session,
window manager, display manager).

```bash
./Detect-manager.sh                                  # full report
NO_COLOR=1 ./Detect-manager.sh > report.txt          # plain-text report in a file
./Detect-manager.sh --version
./Detect-manager.sh --help
```

### `Midi-tester.sh` — MIDI port tester

Listens to the detected ALSA MIDI ports and prints the received messages live.

```bash
./Midi-tester.sh                                     # interactive menu (all ports / choose ports / list)
./Midi-tester.sh --list                              # list ports/devices without listening
./Midi-tester.sh --port 20:0                         # listen to one port (repeatable)
./Midi-tester.sh -p 20:0 -p 24:0
./Midi-tester.sh --version
./Midi-tester.sh --help
```

## Common style

All three scripts embed the same style block (colors, `✔ ✗ ⚠` messages, banner, sections,
tables, spinner, arrow-key menus). It adapts to its environment: colors are disabled when the
output is not a terminal, when `TERM=dumb` or when `NO_COLOR` is set; ASCII symbols replace the
Unicode ones without a UTF-8 locale; menus become numbered lists on terminals that cannot
handle arrow keys.

- [`STYLE-GUIDE.md`](STYLE-GUIDE.md): full documentation of the style and how to apply it to other scripts.
- [`style-template.sh`](style-template.sh): ready-to-copy template for a new script.

## Security notes

- Text coming from outside (package names and descriptions, device names, user input) has its
  control characters removed before display, so it cannot rewrite the terminal.
- Messages are printed with `printf '%s'`, never `echo -e`: backslashes in data stay literal.
- Package names are validated: no leading or trailing `-`, no URLs (`git+https://...`), no
  wildcards, and no `/` where it could mean a local file or a GitHub repository.
- A manager name given on the command line is only compared with a fixed list, never executed.
- `PATH` is cleaned of relative entries at startup; `less` runs with `LESSSECURE=1`.
- `sudo` is only used when needed, its ticket is dropped after each action, and language
  managers (npm, gem) never escalate to root without an explicit, interactive "yes".
- Exported lists are written with mode 600 in a mode 700 directory, never overwriting a file.

## Structure

```
Projet-sh/
├── App-manager.sh
├── Detect-manager.sh
├── Midi-tester.sh
├── style-template.sh
├── STYLE-GUIDE.md
└── README.md
```

## Requirements

- Bash 4.0 or newer (macOS ships 3.2: `brew install bash`; the scripts switch to a newer
  bash automatically if they find one in the usual Homebrew/MacPorts locations)
- A UTF-8 terminal is recommended, but not required
- Depending on what you use: `apt`/`dnf`/`pacman`..., `snap`, `flatpak`, `brew`, `pip3`, `npm`,
  `cargo`... (`App-manager.sh` detects what is available; `sudo` is needed to install, remove
  or update system packages; `less` is used as a pager when present)
- `Detect-manager.sh`: nothing special (`pgrep` helps detect the desktop environment)
- `Midi-tester.sh`: Linux with ALSA (`aseqdump`/`aconnect`, package `alsa-utils`), user in the `audio` group

## Authors

Scripts written for personal projects.
