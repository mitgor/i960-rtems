# Plan: Tetris on the card, terminal on the host

Date: 2026-10-10. T1 is now [implemented and hardware validated](../loader/BUFFER-IO.md).
T2 is also [implemented and hardware validated](TETRIS-STEP.md). T3 is [completed](TETRIS-REPLAY.md), T5 [persistent sessions](../loader/PERSISTENT-SESSION.md) are validated, and T4 [SSH terminal play](TETRIS-TERMINAL.md) has passed its 30-minute acceptance test. No additional flash programming was needed.
Follow with [RTEMS-HOST-NETWORK-PLAN.md](../rtems/RTEMS-HOST-NETWORK-PLAN.md).

## Starting point and architecture

The [runtime loader](../loader/SOFTWARE-LOADER.md) has executed two different C programs
in three successful runs without reboot. It supports 64 KiB returning functions,
one argument and one result. It restores borrowed RAM after each execution.

`game/tetris.c` currently blocks in `io_sync()` until the host clears a doorbell,
uses static BSS, and loops until game over. `game/io.h` places its framebuffer at
`0x00090000`, an emulator address, not a validated live-card buffer. Uploading
this executable unchanged would not implement console I/O and could hang the
firmware callback. The existing linker deliberately rejects BSS.

Use cooperative steps first. The i960 performs game logic and draws all 1,920
ASCII cells; Linux supplies input/timing and renders those bytes over its SSH
terminal. State initially travels back to the host after every step, then returns
with the next request. This works with restoration after every call and avoids
assuming that arbitrary card RAM can hold persistent state.

```text
SSH terminal -> Linux input/frame client -> bounded loader request
                                            |
                                  i960: advance game, draw
                                            |
SSH terminal <- ANSI screen renderer <- state + 24x80 framebuffer
```

## T1 — Bounded input/output for returning payloads (complete)

Extend `host/loadrun` and `loader/runtime` with a versioned request/response block
inside the validated payload window. Pass its card address as the argument.
Specify fixed-width little-endian fields, magic/version, capacities, sequence,
status and actual lengths. No arbitrary address read/write API.

Keep immutable code and mutable request/state/output areas disjoint. Define
bounds in the linker/build manifest and validate them on both sides. Preserve
all original staging bytes before writing, and read output after the returning
call but **before** restoring staging. Output can be modified legitimately;
pre-execution upload verification and final restoration verification stay intact.
Retain the existing one-shot execution and runner self-disarm semantics.

Start with a payload that emits a string and transforms a short input buffer.
Read through the established firmware path; explicitly test CPU-store/DMA-read
visibility and define cache handling. Add guard words and reject stale sequences,
oversized responses, malformed requests and partial completion. Never replay a
request whose execution is uncertain.

**Exit:** host prints card-generated text and exact transformed bytes; malformed
requests fail cleanly; original RAM/hash and PING are restored. Save captures.
Completed; see BUFFER-IO.md and its archived live evidence. T2 and T3 are also complete; see TETRIS-REPLAY.md for latency and the T4/T5 decision.

## T2 — Extract a deterministic game step (complete)

Refactor the current game into initialization and one bounded update/render call.
Put board, piece, score, RNG, tick and game-over state in an explicit serialized
state structure. Pass a framebuffer pointer; remove the hardware path's fixed
`IO_BASE`, blocking doorbell loop and game-over waiting loop. Preserve an adapter
for emulator/native tests rather than silently changing their I/O semantics.

Initialize every state field explicitly. The host supplies a seed, ordered input
and elapsed ticks; cap work per call so a delayed host does not cause an unbounded
catch-up loop. Define restart, quit and game-over as returned states. Check frame
bounds, game-state validity and stack usage. Compile through the known i960RP
pipeline and verify size, symbols, relocation assumptions and absence of BSS.

**Exit:** native and interpreted i960 runs agree on state/frame hashes for seeded
input traces covering rotation, wall collision, hard drop, line clear, game over,
restart and quit. These tests establish software equivalence, not live execution.

## T3 — First complete frame and repeated live frames (complete)

Upload the step payload with an initial state, run it once, and capture its state
and framebuffer. Compare them with the native reference for exactly that input.
Feed the returned state into subsequent transactions. Use the full existing
verification/restoration transaction initially, even if slow. Record actual
end-to-end latency and time spent copying/verifying versus executing.

**Exit:** an automated sequence of at least 1,000 steps matches reference hashes,
with no guard corruption or uncertain completions, and final firmware health and
RAM restoration pass. A screenshot is useful, but state/frame agreement is the
stronger evidence that the card is running the game.

## T4 — Play over SSH (complete)

Implemented and validated in [TETRIS-TERMINAL.md](TETRIS-TERMINAL.md): 35,846 frames over 30 minutes at 19.91 Hz, all native-matching, with 68 restarts. Real SSH hangup/reconnect, Ctrl-C, resize and final full RAM restoration passed. Requirements below are retained as the acceptance record.

Add a host terminal client using raw input and ANSI rendering. Support existing
`a/d/w/s/q` controls, optional arrow-key translation, timed gravity and a bounded
input queue. Restore terminal settings on normal exit, error and interruption.
Treat framebuffer content as fixed ASCII cells, not arbitrary terminal escapes.

Target 20 updates/second if measurements permit; cap catch-up and render only
changed rows when useful. A full screen is 1,920 bytes, about 38.4 KB/s at 20 Hz;
the initial multi-megabyte validation transaction will dominate that cost.
Do not assume the one-shot loader is already a real-time transport.

**Exit:** a playable session through `ssh -t`, correct gravity and controls,
repeatable restart, clean quit, and recorded latency/drop statistics. Run for
at least 30 minutes, including disconnect/reconnect or safe session termination.

## T5 — Optimize only where measurements require it (complete)

Implemented and hardware validated; see [PERSISTENT-SESSION.md](../loader/PERSISTENT-SESSION.md). The 1,000-frame session replay passed, and a paced 400-frame run sustained 20 Hz. T4 interactive frontend and long-duration acceptance are now complete. The design requirements below are retained for context.

If T3/T4 is too slow, add a kernel-owned session: OPEN saves and verifies the
borrowed region once; STEP updates bounded request data, executes once and reads
results; CLOSE restores and verifies the complete original image. Keep code/state
inside the known allocation and prohibit commands that free or repurpose it.
The card still returns to stock firmware between steps. Do not keep the user
callback armed between steps.

Define exclusive ownership, worker lifetime on process death, serialized close,
and cleanup only after a known completed command. Test close/disconnect during
each phase, stale requests and failed restoration. Do not free DMA or code merely
because the terminal exited. This session path is new work and needs its own
failure tests; existing 194-case one-shot coverage is not sufficient.

**Exit:** playable measured cadence, clean normal/disconnect cleanup, unchanged
firmware image and archived evidence. If the conservative path already meets the
target, defer this optimization.

## Completion and scope

Done means the actual i960 computes gameplay and framebuffer while Linux only
transports input and displays output. No new flash is planned. Recovery testing
remains outside the previously agreed scope; it is not a hidden prerequisite.
Archive payloads, host/module sources, manifests, traces and test results; update
SOFTWARE-LOADER.md, STORY.md and Claude guidance only with achieved milestones.
