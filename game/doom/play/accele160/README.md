# Persistent Doom on AcceleRAID 160

See [doom_commands.md](../../../../doom_commands.md) for all installed launcher
variants, commands, options, browser controls and reset boundaries. The default
is the flat-enabled reusable wrapper, compatible with the old card removed.

From the repository on the Mac, run **`./doom`**, then open
**http://192.168.2.75:8088/**. The installed Linux command is
`/home/mit/.local/bin/i960-doom-flat`. It starts a systemd service, checks the exact
card/profile and pinned bundle, loads the exact BDF-gated reader driver on a
fresh unbound card, performs two guarded complete stock-flash
reads on this boot, admits the persistent engine and starts browser output.
SSH may disconnect after the command returns. No firmware write is issued.

Startup includes board/RAM audits, image upload and WAD loading. Refreshing
reconnects to the current game. Click the image for keyboard focus: W/S move,
A/D turn, Ctrl or Space fires, E opens/uses, Shift runs, Enter confirms and
Esc opens the menu. No sound is implemented. The accepted new-card low-detail
renderer, optimized columns/memory copy and private cache map are used;
each fresh game starts textured, and F6 toggles flat floors and ceilings.
Half-height stays disabled. The default kernel now uses the bounded sixteen-entry
card keyboard FIFO; `--keyboard-mode mailbox` is a fresh-session comparison
option. [Measured FIFO findings](../../../../artifacts/current/doom-key-fifo-20261018/README.md)
report queue-tail improvement separately from first-key latency and FPS.

`./doom status` reports the service. Use the page's **Stop Doom** button or
`./doom stop` to park the game with audited cleanup. Keys release after focus loss or a
three-second key-heartbeat timeout. Once a browser has attached, five minutes
without browser heartbeat requests STOP. Before the first attachment the game
can run unattended. The card separately stops if its host process heartbeat
disappears for 30 seconds; frame-slot ACK waits remain bounded to five seconds
and DMA completion to 50 ticks. These are different ownership/lifetime limits.

**One hardware owner per boot:** game Stop or menu Quit parks the reusable
engine; another `./doom` requests a fresh game with the same owner. After global
shutdown (`./doom shutdown`), failure or process death,
buffers and the exclusive grant remain pinned until PC reset. Starting again
then prints that a reset/power-cycle is required. Never force-unload retained
modules. Start a new session with `./doom` after Linux returns. The launcher
does not silently reboot the PC. The old DAC960PG is physically removed.

[A reusable-session investigation](reuse/README.md) now demonstrates native
fresh-image restarts with the same arena and pins. Its audited RTEMS idle/rearm
path now passes [physical STOP / reload / menu Quit / reload / STOP](../../../../artifacts/current/doom-rearm-20261018/README.md),
with 173 frames, 96 full PIO comparisons and unchanged pinned mappings.
Both final post-reset flash reads pass. A later real CLI idle restart also passed;
real browser idle restart now also passes.
The flat-enabled reusable bundle is now the Mac default by user request; its
final post-reset flash pair remains pending. Build with `--reusable`.
The reusable path makes browser Stop/menu Quit park the game, adds Start new
game, and makes a second `./doom` request restart from the same daemon.
`./doom shutdown` retains the reset-only global STOP behavior.

Live logs: `ssh mit@192.168.2.75 'sudo journalctl -fu i960-doom'`.
Default captures are under `/home/mit/i960-flat-accele160-20261018/sessions/`;
the sibling `latest-session.txt` points
to the current session. Every frame gets complete buffer guards, native host
FNV, completion-marker/source/generation/ACK checks. The first four also get
full independent PIO comparisons. Full card code/heap/owner/IRQ/system and
flash audits remain. For ordinary play, retain the first 32 frames, every
300th frame and latest frame, plus every receipt in a streaming JSONL journal.
In-memory histories are bounded. `--capture-all --max-frames 1024` retains
every frame for acceptance tests and requests normal STOP at the frame limit.
Per-frame card FNV is off; host hashing and ownership/system validation stay on.

## Persistent browser transport

The default flat wrapper also starts `i960-doom-stream.service` on port 8088.
It forwards ordered keyboard events over a persistent connection and pushes
only already-audited frames over a separate connection, with two display credits.
The original owner and polling page stay on port 8087; card DMA and all audits
are unchanged. Close other keyboard tabs before using the new page.

Matched Mac measurements improved F6-to-received-frame median from 142.13 to
106.18 ms (-25.3%), and received FPS from 16.63 to 20.40 (+22.7%). These are not
renderer speedups or browser paint measurements. Physical stalled-viewer, stale
input, disconnect release, sequence-gap and browser STOP/restart tests pass.
See the [installation and protocol guide](stream/README.md) and
[card evidence](../../../../artifacts/current/doom-stream-20261018/README.md).

## Rebuild and provision

`build.py` takes `--work NEW_DIRECTORY --archive PINNED_DOOMGENERIC_TAR
--newlib PATCHED_NEWLIB_DIRECTORY --rtems-build ACCEPTED_ACCELE160_RTEMS_DIR`
and optionally `--cross /path/to/i960-coff-`. It snapshots source, builds both
host32 and i960 engines, links private Newlib with `--persistent-play`, packs
and admits the relocated engine, generates its identity header and builds
the card kernel with `DOOM_PERSISTENT=1`. The kernel still records only the
first 32 diagnostic timestamps; persistent receipt journals supply timing
for the full run. Legacy 32-frame builders remain available.

Run `test_native.py --frames 256` against the host platform for repeated
determinism, keyboard, STOP and heap-drain checks. Run
`doom_dma/write_manifest.py SOURCE KERNEL ENGINE_MANIFEST DMA_MODULE` next;
it emits `persistent-manifest.json` and checks that the kernel build metadata
also declares persistent mode. `provision.py --help` lists the pinned
kernel, admission, reader/command/DMA modules, oracle and WAD inputs needed
to produce a self-contained bundle. A bundle's file hashes are verified
before startup; source edits require explicit reprovisioning.

The installed shell command executes `launch.py --bundle BUNDLE start`
through sudo. It may also pass `status`, `stop`, `--port`, `--max-frames`,
`--capture-all` or `--disconnect-seconds`. The Mac wrapper allows a different
SSH endpoint through `I960_HOST` and installed command path through
`I960_DOOM_LAUNCHER`. No card BDF is auto-discovered.

## Optional reusable session with the old card removed

The three-game STOP/Quit/rearm card proof and final flash audits pass.
The default flat-enabled bundle supports the single-card setup. To select
the older textured-only reusable bundle explicitly:

```sh
export I960_DOOM_LAUNCHER=/home/mit/.local/bin/i960-doom-reusable
./doom
```

This bundle records an absent old card explicitly and retains the exact
AcceleRAID target gate. Stop or menu Quit parks only Doom; Start new game
in the browser or another `./doom` requests a fresh image. `./doom stop`
parks the game; `./doom shutdown` is terminal/reset-only. Automatic physical
rearms and a real CLI idle restart are accepted. Browser idle restart also passed; idle host loss and
longer repeated play remain qualification work. The single-card policy was
unit-tested and used for final READIMAGE audits; no additional Doom execution
was performed after removing the old card.

## Optional flat floors and ceilings on AcceleRAID

Build with `--runtime-flat --reusable` for one engine that starts textured and
switches with **F6** or the browser **Toggle flat planes** button. Status is
confirmed from validated frame telemetry. The matched physical four-game
comparison measured **17.975 textured vs 22.129 flat card FPS (+23.1%)**, with
full audits and 128 paired PIO frames. See
[measurements and images](../../../../artifacts/current/accele160-flat-20261018/README.md).

The default installed wrapper is `i960-doom-flat`. After the acceptance reset:

```sh
./doom
```

Open `http://192.168.2.75:8088/`. F6 is debounced, and pressing it again returns
to textures without rebuilding, reloading the level or reallocating buffers.
Sky, walls, sprites, HUD and sector lighting remain; flat planes remove texture
detail and distance shading. Half-height is independent and remains on hold.
