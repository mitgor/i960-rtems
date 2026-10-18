# Doom launcher commands

Run these commands from the repository root on the Mac. They use SSH key
authentication to `mit@192.168.2.75`; the installed Linux wrappers supply the
pinned bundle and run the privileged launcher. Launching does not flash firmware.

## Choose the installed version

| Installed launcher | Behavior | Current qualification |
| --- | --- | --- |
| `/home/mit/.local/bin/i960-doom-flat` | Reusable session; starts textured; F6 toggles flat floors/ceilings | 512-frame card comparison passed; final post-reset flash read pair pending |
| `/home/mit/.local/bin/i960-doom-reusable` | Reusable session, textured planes | Automatic STOP/Quit/reload passed; final flash audits passed |
| `/home/mit/.local/bin/i960-doom` | Legacy, one game per hardware session | Requires the old card present and unbound; unsuitable while it is physically removed |

`./doom` defaults to the **flat-enabled reusable** wrapper. Each fresh game
starts textured; press **F6** to toggle flat floors and ceilings. No environment
override is needed for the current single-card setup:

```sh
./doom
```

To explicitly select the older textured-only reusable version:

```sh
export I960_DOOM_LAUNCHER=/home/mit/.local/bin/i960-doom-reusable
./doom
```

For a one-command selection without changing the shell environment:

```sh
I960_DOOM_LAUNCHER=/home/mit/.local/bin/i960-doom-flat ./doom
```

An existing `I960_DOOM_LAUNCHER` environment override still takes precedence.
Use `unset I960_DOOM_LAUNCHER` to return to the new default.

All variants share `i960-doom.service` and one exclusive card lock. Choose the
bundle before starting a fresh hardware session. Calling another wrapper while
the service owns the card does **not** replace its running engine or kernel.

## Start, stop and restart

These commands work with the default flat-enabled reusable wrapper:

```sh
./doom                  # Start service, or restart the game from live idle
./doom start            # Same as ./doom
./doom status           # Show systemd service status
./doom stop             # Park Doom while keeping the reusable RTEMS owner alive
./doom                  # Request a fresh game after Stop or menu Quit
./doom shutdown         # Terminal RTEMS shutdown; PC reset required afterward
./doom --help           # Show the selected installed launcher's options
```

There is no `restart` action: use `start` again. If Doom is already playing,
`start` reports the current service/URL. Browser **Stop Doom** or menu Quit
parks a reusable game; **Start new game** requests a fresh image and BSS reload.
WAD loading repeats, so restarting is not instantaneous. SSH can disconnect
after `start` returns.

Automatic card rearms passed. Positive browser/CLI idle restart, extended idle
and host-loss qualification remain open. The flat-enabled reusable wrapper is
now the Mac default by user request; those qualification gaps remain unchanged.
The legacy launcher has no reusable idle path: its `stop` ends the hardware
session and its installed parser does not support `shutdown` or newer benchmark
options.

**Reset boundary:** global shutdown, process death, failed cleanup or a terminal
QUIE state retains resources until PC reset. Do not force-unload the driver,
unbind it or start a replacement owner. A full power cycle is the reliable reset
on this PC; warm reboots have repeatedly stalled. The launchers never reboot
automatically. `stop` falls back to stopping the service if no valid reusable
control record exists, so use it only with a live reusable owner for soft STOP.

The latest flat-plane acceptance batch ended in planned global shutdown; a
power cycle and final paired flash reads are still required to close that batch.

## Browser connection and controls

Open [http://192.168.2.75:8087/](http://192.168.2.75:8087/) from the same LAN.
Click the game image to focus it. Refresh reconnects to the existing game.

| Key or button | Action |
| --- | --- |
| W / Up, S / Down | Move forward / backward |
| A / Left, D / Right | Turn |
| Ctrl / Space | Fire |
| E | Use / open |
| Shift | Run |
| 1–7 | Select weapon |
| Enter / Esc | Confirm / menu |
| F10, then Y or N | Quit prompt, confirm or cancel |
| Tab | Automap |
| F6 / Toggle flat planes | Toggle floors and ceilings; flat-enabled bundle only |
| Stop Doom / Start new game | Park / restart a reusable game |

F6 again restores textures. Half-height rendering remains disabled. No sound
is implemented. Keys release on focus loss or a three-second keyboard heartbeat
timeout. After the first browser attachment, five minutes without browser
heartbeat requests STOP by default; before attachment the game can run unattended.

## Launch options

Options apply when creating a service, not to an already running service.
These are the current reusable/flat launcher options:

| Option | Default | Meaning |
| --- | --- | --- |
| `--port N` | `8087` | HTTP port, 1024–65535 |
| `--max-frames N` | `0` | Normal game STOP at N frames; zero means unlimited |
| `--capture-all` | Off | Retain every frame instead of the bounded capture sample |
| `--paired-frames N` | `4` | Full independent PIO comparisons; choose 4 or 32 |
| `--disconnect-seconds N` | `300` | Browser absence timeout, minimum 5 seconds |
| `--restart-cycles N` | `0` | Automatic reusable-game acceptance batch; requires at least 40 frames per game |
| `--quit-game N` | `0` | Use menu Quit in game N of an automatic restart batch |
| `--flat-benchmark` | Off | Four-game textured/flat/flat/textured comparison; requires flat engine, four cycles and at least 128 frames |
| `--bundle PATH` | Set by wrapper | Pinned Linux bundle; normally leave wrapper selection in charge |

Examples, after selecting a reusable wrapper and on a fresh hardware session:

```sh
./doom --port 8088 --disconnect-seconds 600
./doom --max-frames 256 --capture-all --paired-frames 32
```

The second example is an alternative launch, not a way to reconfigure the first.
Use port 8088 in the browser for the first example. Capturing all frames consumes
more disk. Ownership checks and full system audits remain enabled with all these
options; no audit-disable flag is provided.

## Automated card acceptance commands

Run only when intending a bounded test followed by **terminal global shutdown**.
These batches need a reset afterward, unlike ordinary reusable game STOP.

Three-game STOP / menu Quit / STOP:

```sh
I960_DOOM_LAUNCHER=/home/mit/.local/bin/i960-doom-reusable \
  ./doom --max-frames 65 --restart-cycles 3 --quit-game 2 \
  --paired-frames 32 --capture-all
```

Four-game quality/performance comparison in the same flat-capable binary:

```sh
I960_DOOM_LAUNCHER=/home/mit/.local/bin/i960-doom-flat \
  ./doom --max-frames 128 --restart-cycles 4 --flat-benchmark \
  --paired-frames 32 --capture-all
```

The latter injects controlled F6 transitions, excludes ordinary browser keys
during the benchmark and keeps STOP available. It measures matched windows;
it is not an interactive-play FPS guarantee. The accepted comparison measured
17.975 textured versus 22.129 flat card FPS (+23.1%). See the
[evidence and qualification limits](artifacts/current/accele160-flat-20261018/README.md).

## Logs, captures and direct SSH

```sh
ssh mit@192.168.2.75 'sudo journalctl -fu i960-doom'
ssh mit@192.168.2.75 'sudo journalctl -b -u i960-doom --no-pager'
ssh mit@192.168.2.75 'cat /home/mit/i960-flat-accele160-20261018/latest-session.txt'
```

Session roots by wrapper:

| Wrapper | Session directory and pointer |
| --- | --- |
| Flat | `/home/mit/i960-flat-accele160-20261018/sessions/`, sibling `latest-session.txt` |
| Reusable | `/home/mit/i960-doom-rearm-20261018/sessions/`, sibling `latest-session.txt` |
| Legacy | `/home/mit/i960-doom/sessions/`, sibling `latest-session.txt` |

Each session contains results, receipts and retained framebuffer evidence.
An inactive service may make `status` return a nonzero exit code.

Equivalent commands without the Mac wrapper:

```sh
ssh mit@192.168.2.75 '/home/mit/.local/bin/i960-doom-flat start'
ssh mit@192.168.2.75 '/home/mit/.local/bin/i960-doom-flat status'
ssh mit@192.168.2.75 '/home/mit/.local/bin/i960-doom-flat stop'
ssh mit@192.168.2.75 '/home/mit/.local/bin/i960-doom-flat shutdown'
```

For foreground diagnostics, `./doom run` runs the owning launcher attached to
SSH. It is not an attach command and requires the same fresh-session ownership
conditions. Interrupting the owner ends the session; use normal `start` for play.

`I960_HOST` overrides the SSH destination, for example:

```sh
I960_HOST=mit@192.168.2.75 \
I960_DOOM_LAUNCHER=/home/mit/.local/bin/i960-doom-flat ./doom status
```

Changing the SSH destination does not change the pinned card profile or PCI
address. The current bundles target AcceleRAID 160 at `0000:37:09.1`; they do
not auto-discover arbitrary cards. For building/provisioning rather than
launching, see [the AcceleRAID play README](game/doom/play/accele160/README.md).
