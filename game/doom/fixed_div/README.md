# Exact FixedDiv experiment

`--fixed-div-profile` instruments each pinned-source call site and runs 32
bounded differential comparisons per display. `--fast-fixed-div` selects the
candidate; it currently requires the profiling flag. Both are opt-in. Keep
fixed quality, full audits and ownership checks for comparisons.

The original signed 64-bit helper is preserved as `doom_div_legacy`. The new
path uses unsigned magnitudes, the same `(abs(a) >> 14) >= abs(b)` saturation
rule, and one unsigned i960 `ediv`. The guard proves a nonzero denominator and
quotient below 2^30; restoring the sign truncates toward zero. No reciprocal
approximation, floating point, division table or extra DMA ownership is used.
`INT_MIN` inputs fall back to the original compiled implementation rather than
silently redefining its toolchain-dependent `abs(INT_MIN)` behavior.
`INT_MIN / 0` is undefined in the original and excluded from differential tests.

The Intel Rx manual specifies a 64-bit unsigned dividend, remainder in the
first destination register and quotient in the next:
[Rx developer manual](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF).
The assembly helper uses local register pairs r4/r5 and r6/r7.

Per-frame FDV1 telemetry starts at byte 65024 of the existing owned frame.
Eight header words contain magic, version, site count, implementation, nominal
counter frequency, cumulative differential checks, cumulative back-to-back
clock-read ticks and zero. They are followed by count/elapsed-tick pairs for
sites in the generated `fixed-sites.json`; the unused tail must remain zero.
Counts and elapsed ticks reset after each publication. Reads use the existing
exclusive owner's timer-0 downcounter; they do not configure it or mask IRQs.
Elapsed costs include calls, the clock read, interrupts and preemption. They
are **not CPU cycles**. The 10 ms CPU attribution remains separate. Profiling
and differential-test overhead must be stated when reporting FPS.

Run `python3 game/doom/fixed_div/test.py` for randomized and saturation-boundary
comparisons plus strict schema/mode/padding refusals. Native tests do not execute
i960 instructions; on-card differential checks are required before acceptance.
See [experiment](../../../artifacts/fixeddiv-20261016/PLAN.md) for the matched-run
plan. The evidence report records the physical acceptance scope and measured costs.
