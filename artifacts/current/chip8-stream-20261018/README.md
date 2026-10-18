# CHIP-8 streaming candidate — 2026-10-18

**Partial physical acceptance: first 96 frames and guest STOP passed.**
Both pre-run guarded 1 MiB firmware reads passed. The first game produced 96
packets with native replay, full audits and 32 paired PIO comparisons. Its
steady card-timer cadence was 60 Hz; this is not a browser paint measurement.
Guest STOP and the idle ownership audit passed. There were no keyboard events
in this run, so no physical input-latency result is claimed.

The second-game harness still issued a Doom-only WAD admission command. CHIP-8
correctly rejected it with status 5; the failure handler reached terminal QUIE
without releasing pinned resources. This is a host adapter bug, not evidence of
a failed DMA or native replay. Build-g7 removes that command and replaces the
Doom-specific shutdown query with the existing explicit global STOP. A source
generation regression test prevents both leftovers from returning.

`g6-card-evidence.tar.gz` preserves the complete failed-batch captures and
firmware reads. `g6-card-replay.json` records offline revalidation of all 96
packets, compact guards and hashes; a modified captured pixel was independently
rejected. `g6-card-summary.json` distinguishes accepted first-game results from
the second-game failure and verified terminal STOP.

The user authorized reset for card acceptance. A second warm reboot, after
stopping graphics cleanly, again did not return. A physical power cycle is
pending before build-g7's repeated games, browser/input and timeout tests.
No firmware write has occurred.

Implemented sources: `game/chip8/stream`, `game/chip8/accele160`, root `chip8`.
Only the shared Doom gateway API was generalized with backward-compatible
constructor defaults; installed Doom binaries/launcher were not changed.

## Measured native results

`native-timing.json`: 180 frames, 60.07 delivered frames/s, median
20.12 ms/max 20.76 ms key submission to observed frame, 18 input samples.
This is an in-process native owner with real separate WebSocket connections;
it excludes PCI, physical card execution, network and browser paint latency.
No matched old-card/new-card FPS improvement is claimed.

`native-core.txt`: original core sanitizer tests, exhaustive opcode coverage,
1000 random programs, 6001 bounded player slices/3601 reference frames,
guards, brief keys, wrap and catch-up limits.

`native-replay.txt`: 3601 frames independently replayed using unchanged C8G1
native code; 300 brief key edges; bounded input history; clock clamp/wrap;
11 tampered state/input/budget/trace cases rejected.

`native-stream.txt`: real gateway/player, input/down/up, disconnect release,
two-credit stalled video, independent STOP, restart/stale isolation, malformed
frame rejection. Existing Doom gateway regression passed separately.

`rearm-policy.txt`: Linux32 actual resident FIFO/rearm code with hostile
fixtures. This mocks MMIO/scheduling and does not prove physical rearm.
Linux32 ASan/UBSan additionally passed the actual CHIP-8 adapter (eight alternating
source frames, brief key, ROM immutability and STOP) and compact DMA descriptor
state-machine fixture (reuse, markers, peer isolation, admission and failures).

## Remote build

Latest candidate:
`/home/mit/i960-chip8-upgrade-20261018/build-g8/bundle`.
The offline builder exited successfully and generated `build.json`, a full
`bundle.json` inventory, kernel/image, compact DMA module, native oracle
libraries, manifests and exact generated sources. Python compilation of the
host bridge passed. Earlier g1/g4 builds stopped at strict source-context
checks without any hardware operations; g2/g3/g5 are superseded experiments,
not alternate accepted binaries.

The corrected build was staged before the second PC reboot. Its exact binaries and generated sources have now been copied into
`g8-build.tar.gz`; hardware acceptance remains open. Git holds source, exact candidate binaries and both partial card captures;
none establishes completed repeated-restart acceptance.
Do not claim the remote-only binaries have been archived locally.

Compared with Doom: DMA payload 65536 → 512 bytes (128× smaller); full capture
77824 → 12288 bytes (6.33× smaller), with paired full-source PIO checks retained.
These are byte counts, not measured FPS gains. Two internal 64 KiB source slots
and the inherited exclusive arena remain reserved to avoid mixing a new memory
ownership experiment into this transport port.

## Remaining acceptance

Fresh boot inventory and exact card ownership; two guarded 1 MiB firmware reads;
32 paired full PIO/DMA frames, replay all captured packets, input edges and FIFO
bounds, repeated Stop/Start, stale run rejection, stalled host and timeout/STOP
handling; measure physical frame and keyboard latency; archive exact build and
captures and restore/check the desired public service. Never force-unload the
retained Doom or failed CHIP-8 session.

## Second card batch and STOP accounting fix

Build-g7 completed a full first-game STOP, idle audit and rearm. It captured
338 frames in game 1 and 202 in game 2, with 32 paired PIO comparisons per
game and 30 consumed input edges total. Offline replay of all 540 frames,
full eight-word DMA markers, hashes and allocation guards passed. Two guarded
firmware reads match the accepted SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

The real gateway sent 152 frames per observed game: 53.44 and 48.48 FPS across
those intervals. These include LAN client acknowledgements and full audits,
and exclude browser painting. This batch did not complete, so these are
partial measurements, not accepted final performance or input-latency results.

Second-game STOP exposed a resident accounting race: `first_frame_seen` was
advanced before the slot ACK/ownership wait. STOP inside that wait reported
one frame which never acquired a DMA destination. Build-g8 moves the committed
frame counter/timestamp past the ownership wait. The original strict equality
between captured frames and the kernel's committed count is retained. An
ASan/UBSan fixture compiles the actual generated wait/commit code and verifies
normal commit, STOP and timeout. No counter allowance or relaxed audit was
added. This change is isolated to the CHIP-8 generated profile; ordinary Doom
has not been silently changed.

`g7-card-evidence.tar.gz`, `g7-card-summary.json` and `g7-card-replay.json`
preserve the failed batch. `g8-build.tar.gz` now archives exact new kernel,
image, modules, manifests, ROM/data image, generated resident/host code and
CHIP-8 sources locally. The remaining base project is identified by its bundle
inventory and repository source. It is a candidate build, not accepted output.

The immediate retry saw the same boot ID and pinned command as the failed run;
the launcher refused to adopt them. A genuine host power cycle is pending.
Next: build-g8 three-game input/video/Stop/rearm acceptance, native replay,
stalled-host checks and final lifecycle audit. The external acceptance client
also passed three games/two restarts, 16-edge batches and stalled-video STOP
against the native backend (`client-native-regression.json`).
