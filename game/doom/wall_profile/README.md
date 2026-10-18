# Wall-region timing and compiler experiment

`--wall-profile` is optional diagnostic instrumentation; `--fast-walls` separately
selects `-O2` for r_segs.c only (including its masked-segment routine,
so changes can also appear in the sprite/masked stage). Both are off by default. The profiled card comparison measured +0.555% FPS and 0.9875 ms less renderer
time; unprofiled fast-walls performance remains unmeasured. Keep the point-side O0 workaround, exact arithmetic,
quality, ownership and full system audits unchanged.

Four nonrecursive inclusive regions use the existing 4,166,700 Hz downcounter:
BSP root, subsectors, StoreWallRange and RenderSegLoop. Nested subtraction gives
traversal/culling, subsector other work, wall setup, and inner wall rendering.
The latter includes column calls; it is not solely setup or pixel arithmetic.
Intervals include preemption, interrupts, timer reads and wrapper overhead.
Native builds report zero ticks and real call counts. A plain-build comparison
is required to assess instrumentation overhead; never call elapsed ticks CPU cycles.

The existing 512-byte trailer at offset 65024 holds magic WAL1, version,
generation, four sites, timer Hz, empty read bracket, two zero words, four
(count,ticks) pairs and zero padding. It conflicts with input/divide profiling.
Records reset after each publication; the decoder validates identity, padding,
nested timing, bounded counts and explicit admission. No allocation, MMIO write,
new DMA access or change to the 65536-byte framebuffer is introduced.

Run `python3 game/doom/wall_profile/test.py` for malformed-evidence checks.

On the AcceleRAID 160, add `--wall-profile-accele160` with `--wall-profile`.
The old DAC960PG helper reads timer 0 as a continuously decreasing 4.1667 MHz
counter. That assumption is false in the AcceleRAID Doom lease: timer 0 wraps
at its reload and timer 1 is owned by RTEMS at 100 Hz. The new helper combines
the owned timer-1 count with the RTEMS tick, checks both sides of the count
read, and reports a monotonic timestamp on the WAL1 scale. It records clock
fallback/nonmonotonic faults in the reserved WAL1 word; the decoder requires
zero. This path is diagnostic and is not part of the playable default.

The first new-card run on 2026-10-18 accidentally used the old helper. Doom,
DMA, HTTP, STOP, ownership and stock-flash audits passed, but its WAL1 timing
contains wrapped values. Independent trailer replay rejects the capture. See
`artifacts/current/renderer-tune-20261018/` for the rejected evidence and the
corrected candidate test.
Physical acceptance plan/evidence: `artifacts/walls-20261016/PLAN.md`.

Acceptance: 2,600 matching images, 285 full paired audits, STOP/stall/drain and
full replay/tamper checks pass. See `artifacts/notes/walls-20261016.md`.
