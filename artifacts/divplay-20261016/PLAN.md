# Exact FixedDiv without divide profiling — declared acceptance plan

Compare original FixedDiv (A) against the previously qualified exact implementation
(B), both without FixedDiv timers or per-frame differential self-tests. Keep the
existing renderer CPU, frame and WAD counters, fixed low detail, exact fast columns
and spans, no FNV, direct frame slots, ping-pong DMA and release priority identical.
The optimization remains opt-in through `--fast-fixed-div`.

Run A1/B1/B2/A2, 520 frames each. Use frames 100–499 and every interval between
them, without removing outliers. Report individual and pooled FPS, renderer wall
and sampled CPU time, stages, release wait/execution and delivery latency. Retain
all full paired audits, ownership checks, slot stall, held STOP and heap drain.
Replay system/frame/WAD captures and run all frame/drain tamper tests. Require all
corresponding 520 pixel/palette images to agree. Compare first 52 images to the
native oracle, preserving the documented four-pixel target/native difference.
Verify the unprofiled linked image contains no divide profiling/self-test symbols,
all frame reserved tails remain zero, and the protected point-side object is unchanged.
Save and hash-check each capture locally before reboot. Restore public IPv6 HTTP.
Do not attribute differences from prior instrumented runs solely to arithmetic.
