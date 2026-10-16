# Optional peer-service yielding

`--peer-yield` opts the profiled Doom/WAD-ring build into one service pass per
worker-0 dispatch while owned application code is executing, followed by `rtems_task_wake_after(RTEMS_YIELD_PROCESSOR)`.
It does not change priorities, the 10 ms tick, interrupt ownership, or the
one-tick RTEMS timeslice. Both workers remain ready unless an existing operation
blocks them. In RTEMS 4.6.6 the zero-delay branch only yields; it does not enter
`STATES_DELAYING`. Thus this does not introduce the unsupported idle-task IRQ
context when Doom blocks. Controller priority/STOP arrival/drain remain intact.

The yield is after network, general heap, stack proof and shared Doom peer work,
with interrupts enabled and no service lock held. STOP bypasses it. Worker 0
can continue immediately if it is the only ready worker. This preserves peer
service while giving unused slice time to the CPU-bound engine.

The three counters in `peer_yield.h` live in owned mutable memory; their code
is linked through `doom_runtime.c` into the existing protected engine window.
WAD profile version 4 exposes maximum completed-service gap (10 ms ticks) and
pass count in words 6/7. Other builds retain version 2 and zeros there. The archived first experiment
used version 3 and yielded during upload too; version 4 leaves upload/preparation
scheduling unchanged. Counts
are independently sampled after engine STOP, not an atomic scheduler snapshot.
The existing volatile `owned_running` state gates the yield; no new application
lifetime or STOP flag is introduced. Counters still cover every completed peer
pass across the session. Replay cross-checks the build flag and original command/reply bytes; the measured
maximum gap must be nonzero and at most one second for this acceptance. This
ceiling is not a newly guaranteed scheduling deadline. Existing IRQ-gap evidence
and full system/network/STOP checks remain required.

Build through `game/doom/play/build.py` with the existing profiled low-detail
WAD-ring/ping-pong options plus `--peer-yield`. It is experimental and opt-in.
Run `rtems/exclusive/test_peer_yield.py` for wrap/maximum counter behavior and
`rtems/dma/wad_ring/test_target.py` for both report schemas and guarded DMA paths.

[Physical acceptance and exact reproduction](../../artifacts/notes/peer-yield-20261015.md)

The initial card run reached 5.273 FPS but recorded a 59.855 ms final IRQ gap.
Subsequent investigation isolated an inherited priority-31 shutdown scan and
reproduced a 55.997 ms masked drain / 60.237 ms IRQ gap with the existing 80 KiB
shared payload. Current peer-yield builds enable timer interrupts across that
post-barrier drain, restoring priority 31 before done/suspend. No byte check,
internal allocator lock, shared pin, arrival barrier or controller drain changes.
Read-only frozen control page 3 records both workers' elapsed downcounter counts,
RTEMS tick progress and completion counts; schema 1 archives the masked baseline,
schema 2 the interruptible fix. Replay requires all original audit pages and
matches this page to the raw control journal. Schema 2 additionally requires a
full-session IRQ gap below 20 ms and tick progress consistent with drain elapsed
time, including when there is no later IRQ to expose a final masked gap.
The normal fixed run delivered 5.192 FPS with 10.731 ms maximum IRQ gap. This is
a shutdown latency fix, not a demonstrated FPS optimization. Stress qualification
and full evidence are recorded in `artifacts/notes/irq-drain-20261015.md`.
Keep opt-in pending longer interactive qualification. Yielding biases tick CPU
samples; compare wall time and delivered FPS instead of inferring CPU share.
