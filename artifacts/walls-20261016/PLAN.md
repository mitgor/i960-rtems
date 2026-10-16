# Wall profiling and selective optimization acceptance

Predeclared: one unprofiled baseline P0 then profiled A/B/B/A, 520 frames each,
measuring frames 100–499 without exclusions. Both sides retain exact divide,
C columns/two-sample spans, protected O0 point-side, fixed low detail, full
paired audits and ownership checks. Only B compiles r_segs.c at O2, including its masked-segment routine;
report sprite/masked-stage changes too.

Optional wall profiling uses free-running elapsed ticks for BSP root, inclusive
subsectors, inclusive StoreWallRange and inclusive RenderSegLoop. Subtract nested
regions for traversal/culling, subsector other, wall setup and wall loop estimates.
Brackets include interrupts, preemption and instrumentation; do not call these
pure CPU times. Empty timer brackets are recorded; compare P0 to profiled A for
whole-instrumentation overhead (single P0 comparison has limited confidence).

Require native deterministic tests, target disassembly review, unchanged protected
helper hashes, full pixel/palette comparisons, system/frame/WAD replays and
mutations, stalled-host and held-frame STOP, heap drain and HTTP payload identity.
Archive/hash-check captures before reboot; restore public HTTP after testing.
No flash changes, no change to runtime defaults, no quality reduction.
