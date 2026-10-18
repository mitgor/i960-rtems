# CHIP-8 application guidance

Read README.md and ../../GAME-PROGRESSION.md. This is a bounded application
track alongside the parallel RTEMS ownership/interrupt work. Native tests, i960 cross-build and 705 byte-exact card replies pass, including
browser movement/restart, 21 periodic full-allocation audits and two clean restorations/unloads.
Production IPv6 HTTP was restored. See artifacts/chip8-20261011 from root.

Do not overwrite the parallel `persistirq` work or use the card while another
hardware batch owns it. That batch finished before the CHIP-8 acceptance runs. Build with build_target.py in a fresh directory; it reuses a
snapshot of the bounded RTEMS session profile without editing rtems/build.py.
Keep RIO1 guards, paired reads, audit cadence, exclusive lock and final restoration.
Use explicit LE serialization: i960 structure padding previously broke reports.

Core is freestanding and capped at 1,000 instructions/call. Test with
`make -C game/chip8 test` from root. Browser default is native simulation;
card selection must be explicit. Future tests must not relabel native or
cross-build results as card results. DoomGeneric is the chosen future base;
FastDoom supplies optimization ideas. Multi-megabyte RAM ownership remains a
separate prerequisite. Do not add WADs or third-party ROMs implicitly.

## AcceleRAID/native streaming candidate (2026-10-18)

User selected AcceleRAID 160 plus native simulation. See `accele160/README.md`
and root `chip8_commands.md`. Do not confuse the old DAC960 acceptance above
with physical acceptance of the new resident path: it is still pending.
Keep `chip8.c/h` and original C8G1 replies unchanged. `stream/player.c` wraps
elapsed scheduling and bounded key latches; `stream/oracle.py` replays all
captured frames against the original native core, with bounded input history.
The generated profile transfers 512-byte DMA packets through two guarded 12 KiB
allocations, keeps full 64 KiB paired source audits and all system audits, and
rejects any WAD/file request. Never adopt Doom's retained resources. The private
admission worker is mandatory. No firmware write belongs to this upgrade.
Builder workspaces are isolated; inventory sources and artifacts before use.

First AcceleRAID physical batch: 96 frames replayed, 32 paired PIO checks,
full audits, guest STOP and idle ownership passed. Second-game host adapter
mistakenly repeated Doom WAD admission; status 5 correctly rejected it and
failure STOP reached terminal QUIE. Build-g7 fixes that and explicit global
STOP; run `accele160/test_generate.py` to prevent recurrence. Full repeated
restart/input/browser acceptance is still pending a physical PC reset. See
`artifacts/current/chip8-stream-20261018` for preserved evidence.

Second physical batch (g7): 338+202 captured frames, 64 paired comparisons,
30 consumed keys, all replay/guards pass. First STOP/idle/rearm passed; second
STOP exposed frame counting before the DMA slot ownership wait. Build-g8 moves
the commit after that wait, preserving strict captured-count equality. Actual
generated wait/commit code passes ASan STOP/timeout/normal fixtures. Latest
launcher target is g8; it is NOT yet fully accepted. Exact candidate binaries
and both failed-batch captures are locally archived. Never adopt old pinned
resources when the user's “back online” reply has not changed the boot ID.

## Current accepted reusable build: g8

Physical acceptance passed: boot 6b1199a3-8fe8-4aad-abe7-e0fa1649c01f, four
games/three rearm transitions, 7,123 frames replayed, 128 full PIO comparisons,
98 cumulative consumed key edges, FIFO depth 16 and three-second host pause
with both 12 KiB destinations unchanged. Four guest STOP/idle audits passed.
The owner is left idle and `./chip8` reuses it. Measured LAN delivery 47–48 FPS;
browser about 52 FPS; key-state-to-frame median 30–39 ms. This supersedes the
pending status in earlier chronological entries above.

The stalled-host pause intentionally exceeds the gateway's two-second HTTP
timeout. It fails closed; an explicit `./chip8` restarts only that gateway and
the page must refresh. Never silently adopt a changed owner. Global SIGTERM
and an expired card-side timeout were NOT tested in the accepted reusable
batch. Do not claim that acceptance, nor that global shutdown can rearm.
Exact sources/binaries and complete evidence are in the current artifact folder.
