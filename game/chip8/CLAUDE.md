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
