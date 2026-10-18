# Persistent Doom on AcceleRAID 160

From the repository on the Mac, run **`./doom`**, then open
**http://192.168.2.75:8087/**. The installed Linux command is
`/home/mit/.local/bin/i960-doom`. It starts a systemd service, checks the exact
card/profile and pinned bundle, loads the exact BDF-gated reader driver on a
fresh unbound card, performs two guarded complete stock-flash
reads on this boot, admits the persistent engine and starts browser output.
SSH may disconnect after the command returns. No firmware write is issued.

Startup includes board/RAM audits, image upload and WAD loading. Refreshing
reconnects to the current game. Click the image for keyboard focus: W/S move,
A/D turn, Ctrl or Space fires, E opens/uses, Shift runs, Enter confirms and
Esc opens the menu. No sound is implemented. The accepted new-card low-detail
renderer, optimized columns/memory copy and private cache map are used;
flat planes and half-height remain disabled.

`./doom status` reports the service. Use the page's **Stop Doom** button or
`./doom stop` for audited shutdown. Keys release after focus loss or a
three-second key-heartbeat timeout. Once a browser has attached, five minutes
without browser heartbeat requests STOP. Before the first attachment the game
can run unattended. The card separately stops if its host process heartbeat
disappears for 30 seconds; frame-slot ACK waits remain bounded to five seconds
and DMA completion to 50 ticks. These are different ownership/lifetime limits.

**One hardware session per boot:** after STOP, failure or process death,
buffers and the exclusive grant remain pinned until PC reset. Starting again
then prints that a reset/power-cycle is required. Never force-unload retained
modules. Start a new session with `./doom` after Linux returns. The launcher
does not silently reboot the PC. The old DAC960PG remains unbound and untouched.

Live logs: `ssh mit@192.168.2.75 'sudo journalctl -fu i960-doom'`.
Captures are under `/home/mit/i960-doom/sessions/`; `latest-session.txt` points
to the current session. Every frame gets complete buffer guards, native host
FNV, completion-marker/source/generation/ACK checks. The first four also get
full independent PIO comparisons. Full card code/heap/owner/IRQ/system and
flash audits remain. For ordinary play, retain the first 32 frames, every
300th frame and latest frame, plus every receipt in a streaming JSONL journal.
In-memory histories are bounded. `--capture-all --max-frames 1024` retains
every frame for acceptance tests and requests normal STOP at the frame limit.
Per-frame card FNV is off; host hashing and ownership/system validation stay on.

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
