# Doom milestone guidance

Read README.md and RAM-CONTRACT.md before changing this prototype. Milestone 1
compiles 80 engine units for i960 but leaves 58 explicit unresolved externals.
The relocatable object is NOT a loadable card image. No new RAM grant exists.

Use the pinned DoomGeneric/Freedoom archives and preserve their licenses. Keep
instrumentation host-only. Engine text/data/BSS total 626,856 bytes; the ordinary
allocation peak is 6,456,649 bytes including a 6 MiB zone. Do not double count
zone contents. The proposed 8 MiB arena is a planning request with unmeasured
runtime/stack headroom, not a verified memory layout.

Twenty capped 32-bit host workloads pass 42,000 frames; four small-zone tests
fail explicitly. Video initialization fixes the startup wipe, but frames 497,
1426 and 1817 still differ in repeated 2,100-frame traces. Resolve this before
claiming a deterministic oracle or first-card Doom correctness.

Do not touch the parallel RTEMS files or card owner. Next: runtime/platform
implementation, proven RAM/loader manifest, then headless target acceptance.
Keep all paired/full audit contracts until a larger-range contract is proven.
