# CHIP-8 streaming candidate — 2026-10-18

**Physical acceptance pending. No CHIP-8 card command or firmware write issued.**
The user selected AcceleRAID 160 and native simulation, and authorized a reboot
for testing after the candidate was ready. SSH did not return after that reboot;
a physical power-cycle request is pending. Do not label native timings as card
performance or treat the generated profile as accepted firmware.

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
`/home/mit/i960-chip8-upgrade-20261018/build-g6/bundle`.
The offline builder exited successfully and generated `build.json`, a full
`bundle.json` inventory, kernel/image, compact DMA module, native oracle
libraries, manifests and exact generated sources. Python compilation of the
host bridge passed. Earlier g1/g4 builds stopped at strict source-context
checks without any hardware operations; g2/g3/g5 are superseded experiments,
not alternate accepted binaries.

The build was staged before the PC reboot. Its exact binaries/inventory still
need copying into this artifact folder after SSH returns. Git currently holds
reproducible source and native evidence, not a completed hardware capture.
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
