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

[Physical acceptance and exact reproduction](../../artifacts/peer-yield-20261015/README.md)

Final card run: 4.517 → 5.273 FPS, all 58 paired audits and STOP/drain pass.
Keep opt-in: maximum IRQ gap was 59.855 ms versus baseline 10.546 ms. Long-gap
phase/PC attribution and repeat qualification remain pending; aggregate counters
cannot establish the cause. Yielding biases tick CPU samples; compare elapsed
wall time and delivered FPS instead of inferring CPU share.
