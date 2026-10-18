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
