# N1 cache audit

## Execution paths checked

The accepted new-card `doom_dma/app.c` upper-bank probe reads global D-cache
status, temporarily disables caching for the full save/pattern/restore audit,
invalidates, and re-enables only when the incoming enable bit was set. It checks
restoration. This is not a policy that enables caching for the Doom arena.

The normal new-card invalidation wrapper is called in WAD reply polling,
input/key polling (checkpoint 101), frame ACK waiting, and the outer Init
command loop. The outer loop does not keep running while its synchronous Doom
entry is executing. The timer ISR does not call this wrapper. Normal renderer
phase callbacks and CPU-sample reads do not invalidate. `engine_stopping()`
checks ownership/control/deadline without invalidation; do not remove the
transport boundary invalidations, which protect against stale PCI writes.
Instruction-cache invalidation occurs during image admission, not each frame.

The old-card engine similarly invalidates data/instruction caches at admitted
image synchronization. Its key/frame service code has no explicit `dcctl`;
host control arrives through the existing owned MU/RTEMS service path. Its RAM
probes temporarily disable/restore D-cache. A historical `loader/postinit`
experiment disables cache, but is not evidence that the accepted running
firmware or current Doom image uses that experimental path.

These are a source/control-flow audit, not measured per-frame invalidation
counts. Global status alone cannot establish arena cacheability. Version 2 of
the shared benchmark captures the five logical memory configuration registers
read-only, using the Intel Jx/Rx documented register addresses. Decode both
board captures before proposing any change to logical templates. Never make
host-written control pages cacheable merely to accelerate private engine data.

## Initial new-card exploratory run

Record version 1 passed 32 whole DMA frames, first four full PIO pairs, 32 HTTP
frames, native WAD prefix, full system audits, three-second stalled-host test,
engine cleanup and STOP. Independent replay passed 18 transport tamper tests.
All pixels/palette matched the earlier optimized engine. Global D-cache status
was 0x8221 before/after all workloads (enabled, 4 KiB geometry).

This first version used different loop shapes for small warm reads and forced
invalidations. Those timings must not be subtracted to estimate invalidation
cost. Version 2 corrects that experimental comparison and adds logical cache
attributes. The initial evidence is retained as an exploratory result, not a
matched old/new result. Its post-reset firmware audit passed in the first
reboot, but it is superseded by the matched version 2 run.

## New-card logical attributes observed (version 2)

All 32 frames report D-cache `0x8221`, DLMCON `0`, LMADR0 `0xc0000002`,
LMMR0 `0xffc00001`, LMADR1 `0xc0400002`, LMMR1 `0xffe00001`.
The enabled templates cache `c0000000–c03fffff` and `c0400000–c05fffff`.
The benchmark allocation `c0f7b850` matches neither and uses uncached DLMCON.
The owned upper-bank Doom arena and `c0710000` kernel grant are also outside
these templates. This is a measured configuration mismatch, not a hypothesis
about the nominal CPU frequency. Warm 1 KiB reads (360 ms median) and the same
loop with 4,096 invalidations (365 ms) are consistent with uncached memory;
they do not measure the benefit of enabling it. No cache-map register was
written. A cache-enabled Doom FPS claim still requires a separate physical run.

## Follow-up boundary: owned-arena caching, not global caching

A candidate can replace a logical template only after reboot-only ownership and
full 8 MiB admission succeed. Its cacheable extent must be restricted to the
owned upper bank; keep DLMCON uncached and leave host control/WAD-input pages
outside it. Capture all five original registers, use the documented ordered
cache/template transition, and prove exact restored or reboot-only state.
CPU-to-host frame DMA reads write-through data, but host-to-card writes require
explicit synchronization before CPU use. Keep the existing invalidations until
a separate coherency proof supports narrowing them. Never reuse this policy in
stock-firmware coexistence mode. No flash patch is required for this experiment.

The current run does not measure a cache-enabled FPS gain. Even with the map
fixed, larger working sets, memory latency, scheduling and renderer instructions
can prevent ideal clock scaling. Use unchanged renderer quality and identical
engine bytes for a cached/uncached comparison before tuning compiler flags.

## Old-card matched run

The failed old-card run reached and captured one real frame before the host
rejected the unexpected benchmark trailer. On that frame, D-cache status is
`0x7221` (enabled, 2 KiB); LMADR0/LMMR0 are `c0000002/ff000001`, matching
the allocation at `c0a1db20` and allowing data caching across the 16 MiB card
RAM range. LMMR1 has enable bit clear and does not participate. The exact
xorshift result matched the native oracle. The host decoder was extended to
validate the entire declared trailer, and 11 trailer mutations plus four
undeclared/conflicting-mode cases were rejected on the captured frame. This
one frame is diagnostic evidence, not a completed old-card benchmark. The
subsequent corrected host decoder admitted the exact manifest's trailer,
rejected 11 actual-frame mutations and four undeclared/conflicting modes,
then captured all 120 frames and clean STOP on the old card. Its native WAD
oracle, 120 full frame audits, 70 system snapshots, owner and drain checks
passed. All eight benchmark cases have four matching repetitions in frames
1–32 on both cards. The integer and clear workloads scale by more than 5×,
while warm reads and repeated copies scale by less than 2×. Read the medians
and all raw samples in `comparison.json`; every workload checksum matches.
The old 1 KiB read rose from 700 to 935 ms with 4,096 invalidations, versus
360 to 365 ms on the uncached new arena. With the 10 ms timer, the new 5 ms
difference is below reliable single-run resolution.

Both physical tests left logical cache registers unchanged, used exact BDFs,
and kept the other card free. The new-card 32-frame run also passed first-four
full PIO pairs, 32 identical HTTP frames, native WAD order, three-second
host stall, STOP and all system audits. The new-card pre-reset guarded flash
pair matched stock. After releasing the retained sessions, the PC returned on boot `29dd7853-2614-40e9-8666-2b49b6764324`; both final guarded full 1 MiB reads matched SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`. Both returned done=1, status=0, residual=0, released=0 and guard_changes=0. The old card stayed unbound; the new card has only the read-only `myrsread` driver bound. Combined offline replay passed all full audits and 32 matched benchmark records per card.
