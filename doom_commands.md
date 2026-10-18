# Doom launcher commands

Run these commands from the repository root on the Mac. They use SSH key
authentication to `mit@192.168.2.75`; the installed Linux wrappers supply the
pinned bundle and run the privileged launcher. Launching does not flash firmware.

## Choose the installed version

| Installed launcher | Behavior | Current qualification |
| --- | --- | --- |
| `/home/mit/.local/bin/i960-doom-flat` | Reusable session with persistent input/pushed frames on port 8088; starts textured; F6 toggles planes | FIFO/pushed-frame transport, STOP/restarts, matched latency and both batches’ closing flash reads passed |
| `/home/mit/.local/bin/i960-doom-private-wq` | Experimental core launcher, port8087, private admission queue |218 audited frames/32 PIO and graphics shutdown passed; final power-off/post-reset reads deferred; not default |
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

Automatic card rearms, CLI idle restart and real browser STOP/restart passed.
Extended idle and host-loss qualification remain open. The flat-enabled reusable wrapper is
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

With the default flat launcher, open
[http://192.168.2.75:8088/](http://192.168.2.75:8088/) for persistent keyboard input
and pushed frames. Close other Doom keyboard tabs first. Port 8087 remains the
original polling page and is still used by the textured-only/legacy wrappers.
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
| `--port N` | `8087` | Original owning daemon HTTP port, 1024–65535 |
| `--stream-port N` | `8088` | Pushed-frame gateway port; flat wrapper only, must differ from owner port |
| `--max-frames N` | `0` | Normal game STOP at N frames; zero means unlimited |
| `--capture-all` | Off | Retain every frame instead of the bounded capture sample |
| `--paired-frames N` | `4` | Full independent PIO comparisons; choose 4 or 32 |
| `--disconnect-seconds N` | `300` | Browser absence timeout, minimum 5 seconds |
| `--restart-cycles N` | `0` | Automatic reusable-game acceptance batch; requires at least 40 frames per game |
| `--quit-game N` | `0` | Use menu Quit in game N of an automatic restart batch |
| `--flat-benchmark` | Off | Four-game textured/flat/flat/textured comparison; requires flat engine, four cycles and at least 128 frames |
| `--keyboard-mode MODE` | `fifo` | Fresh-session input transport: `fifo` or `mailbox`; active daemon keeps its mode |
| `--bundle PATH` | Set by wrapper | Pinned Linux bundle; normally leave wrapper selection in charge |

Examples, after selecting a reusable wrapper and on a fresh hardware session:

```sh
./doom --port 8089 --stream-port 8090 --disconnect-seconds 600
./doom --max-frames 256 --capture-all --paired-frames 32
```

The second example is an alternative launch, not a way to reconfigure the first.
Use port 8090 in the browser for the first example. Changing the port of an
already running gateway requires stopping only `i960-doom-stream.service` first. Capturing all frames consumes
more disk. Ownership checks and full system audits remain enabled with all these
options; no audit-disable flag is provided.

## Automated card acceptance commands

The ordinary `./doom` now selects the accepted sixteen-entry **card keyboard
FIFO** and pushed-frame gateway. Eight-game physical acceptance, full-ring STOP,
restarts and paired post-reset firmware reads passed. Textured remains default;
F6 switches flat planes. See the [FIFO findings](artifacts/current/doom-key-fifo-20261018/README.md).

For a matched comparison on a **fresh hardware session**:

```sh
./doom --keyboard-mode mailbox
# Or the default: ./doom --keyboard-mode fifo
```

These flags do not change a retained running daemon. The dedicated
`i960-doom-key-fifo` core launcher also accepts `--keyboard-selftest` for the
bounded pending-input STOP probe; leave it off during ordinary play. The test
runner selects modes at idle, admits a fresh engine per game, and owns input:

```sh
/tmp/i960-doom-stream-venv/bin/python \
  game/doom/play/accele160/stream/benchmark_fifo.py \
  --host 192.168.2.75 --out NEW_RESULTS_DIRECTORY
```

The full-ring probe requires a fresh acceptance owner started explicitly with
`--keyboard-selftest --paired-frames 32`, plus the updated gateway. Do not run
this input-injecting comparison while another person is playing.

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
ssh mit@192.168.2.75 'sudo journalctl -fu i960-doom-stream'
ssh mit@192.168.2.75 'sudo journalctl -b -u i960-doom --no-pager'
ssh mit@192.168.2.75 'cat /home/mit/i960-key-fifo-20261018/latest-session.txt'
```

Session roots by wrapper:

| Wrapper | Session directory and pointer |
| --- | --- |
| Default flat + FIFO | `/home/mit/i960-key-fifo-20261018/sessions/`, sibling `latest-session.txt` |
| Original flat baseline | `/home/mit/i960-flat-accele160-20261018/sessions/`, sibling `latest-session.txt` |
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

The gateway journal is `/home/mit/i960-doom-stream-20261018/transport.jsonl`.
The installed flat wrapper starts it automatically, checks source/dependency
identities and preserves the original owner wrapper. `stop` parks only Doom;
`shutdown` stops both services and terminally shuts down RTEMS. See the
[stream gateway guide](game/doom/play/accele160/stream/README.md) for installation,
rollback and gateway-only restart commands. No hardware modules are unloaded.

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


## Pending host power-off qualification

The private-queue candidate removes the observed retained-card/NVIDIA global
workqueue interaction. See the [shutdown findings](artifacts/current/host-shutdown-20261018/README.md).
The PC is intentionally left on after terminal global RTEMS shutdown; a fresh
Doom instance requires a PC reset. The next physical test is normal
`sudo systemctl poweroff` with graphics and the fixed retained module present,
then power on and finish guarded firmware reads before default promotion.
Do not force-unload or adopt its pinned resources to start another game.
