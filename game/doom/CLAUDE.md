**N1 cache diagnostic (2026-10-17):** `runtime/cache_bench/` is an opt-in
fixed-work, eight-case Doom frame trailer at byte 65024. Build the same admitted
engine for both cards with `platform/build.py --cache-bench`. The old host decoder
must validate this trailer through `rtems/residentnet/presentation_profile.py`;
normal frames still require zero padding. Use four repeats per case, full frame
transport hashes, native checksum oracle, guards, owner/STOP and system audits.
It changes diagnostic frame time and must not be used as play FPS. The new-card
upper 8 MiB Doom arena is currently uncached despite global D-cache enabled;
see `artifacts/current/cache-scaling-20261017/AUDIT.md` before proposing more
compiler tuning. Keep host-written control and WAD-input pages coherent if a
private arena cache template is tested later. Half-height remains on hold.

**AcceleRAID direct Doom DMA physical run — 2026-10-17:**
The [exact bounded capture](../../artifacts/current/accele160-doom-dma-20261017/README.md)
passed 32 guarded channel-0 DMA frames and identical HTTP packets, four full
PIO comparisons, exact native WAD startup order, three-second held-host
buffer immutability, engine cleanup and quiescent STOP with all ownership
and system audits. Exact old optimized low-detail engine pixels/palette match
for all frames. Frames 12–31 give **7.819 card FPS / 7.878 HTTP-observer FPS**,
versus old optimized 6.35–6.40 and previous new high-detail 2.331. The latter
3.35× change combines renderer/quality/transport changes, not CPU speed.
Observed-to-HTTP availability is **2.03 ms**; renderer wall/sampled CPU is
91.5/90.5 ms. Full card transport FNV remains on and native host FNV is now
integrated. Both extra adapter copies disappear after the first four paired
qualification frames. Inclusive FPS with deliberate three-second stall is
4.480. **Two matching guarded full post-reset flash reads now close this run.** No firmware writes, old card unbound, buffers reboot-pinned; never
force-unload. This is a 32-frame gate, not persistent play. An optional card-hash-off run also passed 32 guarded DMA/HTTP frames and
STOP at **9.694 card / 9.643 observer FPS**, with identical pixels/palette and
full system checks and matching paired full post-reset flash reads. Both modes
retain native host hashing; card hashing defaults on. Scalar 4 KiB WAD
service, long interactive STOP and switchable quality remain ports. Half-height stays on hold. Older status below is history.

## AcceleRAID 160 first real Doom frame — 2026-10-17

[The third new-card run](../../artifacts/current/accele160-doom-first-frame-20261017/README.md)
served all 5,043 engine WAD reads in native order, rendered one real Doom
frame, read back its complete 65,536-byte frame/palette slot, and left the
engine through the owned boundary with all arena loans released. Its
framebuffer SHA-256 is
`f4d1c27a4ec8e8db4437d9e28012107370749765aa0e09c99758eeb54163b8ce`.
This took 123.54 seconds from entry to first frame. The post-reset paired complete flash audit passed. The next milestone is sustained frames with bounded input and host presentation; one frame establishes neither FPS nor browser play.

## Earlier AcceleRAID 160 startup stalls — 2026-10-17

[The new-card gate](../../rtems/accele160/doom_first_frame/README.md) now
binds the Doom runtime ABI to the accepted 8 MiB arena and full-WAD service.
At that stage no game frame had been produced. The second run served 3,801
WAD reads in the exact native order, then made no request or frame progress
for 120 seconds. It did not take cooperative STOP. The third run crossed
this point; keep the stall evidence, full ownership and post-reset flash
audits when building a playable port. The earlier diagnostic framebuffer
remains only a test pattern.

## AcceleRAID 160 full-WAD service — 2026-10-17

[The physical capture](../../artifacts/current/accele160-doom-wad-service-20261017/README.md)
accepted 38 card-requested reads across the exact 28,795,076-byte Freedoom
WAD, with full 4 KiB cache readback, four bounded refusal paths, STOP and
two matching guarded post-reset flash reads. The 867,792-byte Doom image
remains admitted but **not invoked**. The next gate is binding the service
to Doom's file/cache ABI, then an owned, bounded engine call and first real
frame. Do not describe the diagnostic frame as gameplay. Retain reboot-only
ownership, 2,048-page reversible bank audit, arena guards and old-card
isolation.

## AcceleRAID 160 Doom bridge — 2026-10-17

[The new-card physical capture](../../artifacts/current/accele160-doom-bridge-20261017/README.md)
accepts guarded image/6 MiB zone/64 KiB frame allocations, exact 867,792-byte
Doom image admission and relocation, a checked Freedoom header input and a
complete diagnostic framebuffer round trip. It does **not** execute Doom,
transfer the full WAD or prove gameplay FPS. RTEMS holds the operation-13
callback until reset. After reset, two full guarded flash reads match stock;
the old DAC960PG remains unbound. The next porting gate is the new card's
runtime ABI, full-WAD service and bounded real engine entry. Preserve the
exact bank preimage/alias checks and whole-card reset release boundary.

<!-- flat-planes-current -->

## Current two-card mapping — 2026-10-16

Old DAC960PG is now `37:04.1` (`1069:0010`, unbound). New AcceleRAID 160 is
`37:09.1` (`1069:0050`, subsystem `0054`, bound to `myrs`, firmware 6.00-05).
Do not reuse old hard-coded `37:09.1` launch/cleanup assumptions. New-card CPU
clock, firmware compatibility and execution support are not yet verified.
No custom runtime is active. [Inventory](../../docs/hardware/dual-card-20261016.md). Half-height stays on hold.


## User direction: half-height on hold — 2026-10-16

Pause further half-height optimization and testing until requested. Keep the
existing option off by default and retain its evidence. The user is replacing
the card with a similar board described as having a 100 MHz i960. Identify the
replacement hardware and firmware before reusing board-specific assumptions;
compatibility and performance have not yet been tested.



## Current half-height result (2026-10-16)

`--runtime-half-height` enables F7/browser control, independent of F6 flat planes,
full height initially. Keep off by default: same-session 920-frame card comparison
normal/half/flat/both = 6.3616/6.4042/7.7235/7.1115 FPS. Half alone +0.67% is not
an established practical gain; half + flat is 7.92% slower than flat alone.
Full audits, DMA ownership, held-slot STOP and stalled-host checks remain intact.
Record both wins and regressions; next investigate half-column/expansion costs.
[Exact results and reproduction](../../artifacts/current/half-height-20261016/README.md). The bounded ping-pong benchmark blocks
external keys; normal pipeline builds expose F7. Do not advertise the measured
bounded FPS as an interactive guarantee.

**2026-10-16 optional flat planes accepted:** playable `--runtime-flat` starts
textured and adds F6/browser toggling. Same-build low-detail ABBA: **6.454 →
7.877 FPS (+22.05%)**, renderer 135.51 → 107.31 ms, planes 40.96 → 13.46 ms.
520 frames / 56 full paired audits, STOP/stall/drain, remote/local replay and
mutation checks pass; native oracle retains exactly the four known differences.
Keep quality optional. The measured ping-pong session is bounded, not a newly
qualified interactive transport; normal pipeline builds expose the live button.
See `artifacts/current/flat-planes-20261016/README.md` and `game/doom/flat_planes/README.md`.
<!-- /flat-planes-current -->

# Doom milestone guidance

<!-- span-four-current -->
**2026-10-16 exact four-sample spans: correctness qualified, speedup not established.**
Opt-in `--span-four --fast-render` retains exact tails/wrap/alignment/duplication;
normal two-sample spans remain the default. Four 520-frame card runs passed:
**2,080 matching images, 228 full paired audits**, native oracle, STOP/stall/drain,
remote/local replay and tamper checks; 1,942 exact HTTP payload observations.
Host32 sanitizer primitives pass 123,264 cases per variant. Max IRQ gap 10.863 ms.

Predeclared A/B/B/A measured **6.617 → 6.449 FPS (−2.54%)** pooled, renderer
132.513 → 135.700 ms. Do not claim a causal regression or a speedup: unchanged
baseline A2 reached **6.814 FPS**, versus A1 **6.431**, exceeding the candidate's
small apparent initial gain. All images, baseline hashes/options/addresses and
nominal 10 ms IRQ period match. The repeat variation is unresolved; A2 must not
be discarded. HTTP availability improved observationally (5.074 → 4.393 ms),
but transport was unchanged and causation is unproven. No default promotion.

**Next:** investigate unchanged-baseline repeatability before further performance
claims. Then consider specializing span detail/alignment paths; unprofiled
fast-walls acceptance is still pending. Exact divide remains playable-default;
C columns/fast-render, fast-walls and the new span switch remain opt-in.
Public IPv6 HTTP service restored after saved evidence and reboot.
Evidence: [complete experiment](../../artifacts/span-four-20261016/README.md).

<!-- wall-profile-current -->
**2026-10-16 wall profiling and selective r_segs O2 qualified, opt-in.**
`--wall-profile` partitions root/subsector/wall-setup/wall-loop elapsed time;
`--fast-walls` independently selects O2 for r_segs.c, including masked drawing.
Both remain OFF by default. Exact divide stays playable-default; C columns and
spans/selective O2 remain explicitly enabled in benchmark builds.

Profiled A/B/B/A: **6.323 → 6.358 FPS (+0.555%)**, renderer **139.188 →
138.200 ms**. Small measured gain; no HTTP-delivery latency improvement. The
single plain control is 6.427 FPS / 136.475 ms; profiling adds about 2.71 ms versus
pooled A. Unprofiled fast-walls card FPS is unmeasured: qualify it before promotion.

Baseline partition: traversal/culling **4.97 ms**, other subsector **14.58 ms**,
wall setup **21.31 ms**, wall loop **40.02 ms**. These include profiler/interrupt/
preemption costs, not pure CPU cycles. The wall loop did not get faster. Do not
attribute the aggregate gain to pixel-loop speed or treat the old BSP bucket as
all traversal. Next promising trial: exact four-sample versus two-sample plane
spans, against the plain accepted baseline, keeping quality and all checks.

All **2,600 images**, **285 full paired audits**, ownership, stall/held-STOP/
heap drain and full system/frame/WAD replay/tamper tests pass; 2,444 exact HTTP
payload observations match. Region call counts agree on all 2,080 profiled frames.
Max IRQ gap 10.812 ms. Source/binary/capture evidence and reproduction:
`artifacts/walls-20261016/README.md`; flags/schema: `game/doom/wall_profile/README.md`.
No flash writes. Public IPv6 HTTP restored (200, 2,889 bytes), boot
`22b8d687-42db-477e-804b-8bb26eeac7da`; public relay owns the card.
<!-- /wall-profile-current -->

<!-- point-side-current -->
**2026-10-16 exact point-side candidate qualified, opt-in.** `--fast-point-side`
selects a defined 32-bit helper with adjacent i960 compare/test pairs; omitting it
retains the protected O0 function. C columns are still opt-in (`--fast-columns`),
explicitly enabled in these benchmarks with `--fast-render`. Exact FixedDiv stays
playable-default. No traversal/quality, audit or ownership policy changed.

Host oracle: 1,002,000 cases; UBSan: 12,000; physical scalar proof: 1,024 vectors,
32 transactions and 96 paired staging phases. Full A/B/B/A: **6.428 →
6.431 FPS (+0.034%)**, renderer 136.463 →
136.137 ms. This is within repeat variation, not a demonstrated FPS/
latency gain. All 2,080 images, 229 paired audits, stall/STOP/drain,
replay/tamper checks and 1953 HTTP observations pass; max IRQ 10.832ms.
Helper text shrinks 416→336 bytes and is call-free. Current counters measure BSP
plus walls, not isolated helper cost; direct traversal profiling is still next.
Evidence: `artifacts/point-side-20261016/README.md`; implementation/tests:
`game/doom/point_side/README.md`. No flash writes. Public IPv6 HTTP restored (200,
2,890 bytes), boot `2b670864-d474-4926-9424-371f8b7f20b9`; public relay owns card.
<!-- /point-side-current -->

<!-- input-trace-current -->
**2026-10-16 playable exact divide is now default.** `game/doom/play/build.py`
and private playable engine builds select the accepted exact FixedDiv unless
`--no-fast-fixed-div` is given. Non-play inventory builds keep their old default.
Divide profiling and the new `--input-trace` remain opt-in and cannot share the
same frame trailer. Earlier dated opt-in statements below are historical.

The queued input-consumption diagnostic is implemented and card-qualified:
8 scripted submissions reconcile with 24 dequeue/pre-menu/post-menu records in
each traced run. Both runs consume keys for display frames 62/64/66/68 at game
tics 61/63/65/68, two generations after host submission frames 60/62/64/66.
This is not an input-to-paint latency measurement or retrospective proof of the
historical menu mismatch; the old capture lacked these records.

Four accepted 520-frame runs: trace off **6.432 FPS**, on **6.412 FPS** (−0.31%).
All 2,080 images match, 228 full paired audits and all stall/STOP/drain/replay/
tamper checks pass; 1,932 observed HTTP payloads match. Maximum IRQ gap 10.832 ms.
One initial host logging scope failure is separately archived, fixed and tested;
it is excluded from accepted results. Ownership and full audits remain intact.
Evidence: `artifacts/input-trace-20261016/README.md`; format/tests:
`game/doom/input_trace/README.md`. Next: profile and qualify a defined exact
point-side helper/BSP change, preserving the current workaround until proven.
<!-- /input-trace-current -->

<!-- divplay-current -->
**2026-10-16 exact divide qualified without divide profiling:** `--fast-fixed-div`
now works independently of `--fixed-div-profile`; both remain opt-in. Fresh
520-frame A/B/B/A runs measure **6.224 → 6.412 FPS (+3.01%)**, renderer
**141.25 → 136.93 ms** (4.325 ms sooner), sampled CPU 138.66 → 134.35 ms.
Frame/CPU/WAD counters remain; only divide timers and per-frame arithmetic
self-tests are compiled out. Do not compare this directly with profiled FPS.

All **2,080 corresponding images agree**, **230 full paired audits** pass,
plus full replay/tamper, stalled-slot, held STOP and heap-drain tests. All 1,952
observed HTTP payloads match. Maximum IRQ gap 10.792 ms. No demonstrated HTTP
latency improvement (4.884 → 5.001 ms completion-observed to availability).
Ownership and full audits are unchanged; protected point-side object and exact
arithmetic objects retain their accepted hashes. No flash writes. Exact builds,
sources and captures: `artifacts/divplay-20261016/README.md`.

Next: trace frame/tic input consumption to explain the historical menu discrepancy,
then broader scenes/high detail and the next measured BSP/memory optimization.
Keep quality-reducing options explicit. This batch does not resolve the historical
menu discrepancy or establish performance for every map.
<!-- /divplay-current -->

<!-- fixeddiv-current -->
**2026-10-16 exact divide measured, opt-in:** add `--fixed-div-profile` and
`--fast-fixed-div` to the fixed-column/span build. Four matched 520-frame runs
measure **6.047 → 6.309 FPS (+4.34%)**, renderer **144.94 → 138.08 ms**,
and inclusive FixedDiv elapsed **9.588 → 3.669 ms/frame** at 480.67 calls/frame.
Both builds carry profiling and 32 differential checks per display; this is
not an uninstrumented FPS claim. Timer brackets include calls, clock reads,
interrupts and preemption, not pure CPU cycles. Exact sign/saturation/rounding
is preserved; INT_MIN retains the legacy path. No approximate reciprocals.

All **2,080 corresponding images and call-count traces agree**, 231 full paired
audits pass, 66,560 on-card arithmetic comparisons pass, plus STOP/stall/drain,
full replay and tamper tests. Maximum IRQ gap 10.810 ms. All 1,944 observed HTTP
payloads are exact. Ownership/release/audit policy is unchanged; HTTP latency
has no demonstrated improvement. Both admissions stay below 900,000 bytes;
point-side O0 object unchanged. No flash writes. Evidence and reproduction:
`artifacts/fixeddiv-20261016/README.md`, `game/doom/fixed_div/README.md`.

Next: qualify the fast path without profiler overhead, then broader scenes and
high detail. The earlier asynchronous menu discrepancy is still unexplained;
this batch's strict image pass does not replace input-consumption tracing.
<!-- /fixeddiv-current -->

<!-- columns-current -->
**2026-10-16 sequential backlog result:** `--fast-columns --fast-render` measures
5.330 → 6.204 FPS (+16.4%) on matched 520-frame A/B/B/A low-detail runs;
renderer 168.70 → 141.81 ms, BSP/walls 106.75 → 84.14 ms, sprites 21.73 → 17.44 ms.
Plane time is unchanged. No heap allocation added; image grows 480 bytes.
All 2,080 frames/234 full paired system audits, STOP/stall/drain and replay/tamper
checks pass. Both candidates match every reference image. **The last unchanged
baseline has one menu-transition mismatch at frame 64** (matches earlier menu
frames 62/63); every measured-window image agrees. The strict all-run image
oracle remains a failure, not an exception silently declared a pass. See
`artifacts/columns-20261015/README.md` for scope and exact evidence.

`--runtime-detail` permits high/low selection in one binary via F5/menu/browser;
`--low-detail` then selects only the starting preference. Fixed benchmark builds
remain fixed. Native and a separate 100-frame card run confirm low/high/low,
with 45 full audits and STOP/drain. Bounded ping-pong tests hide the button and
inject F5 themselves; interactive builds expose it. Keep future quality-reducing
modes independently switchable. Do not claim mixed-mode FPS as a matched result.

Retain the new relay pre-frame regression test and unconditional held-STOP
metadata check for 52/100-frame replays. Next: follow `game/doom/TESTING-QUEUE.md` and profile exact FixedDiv sites;
separately record input consumption frame/tic to resolve asynchronous menu timing.
Keep previous per-stage latency gains, all full audits and ownership checks.
<!-- /columns-current -->

<!-- renderer-current -->
**2026-10-15 fast renderer accepted in bounded low-detail card tests:** opt-in
`game/doom/play/build.py --fast-render` selects exact two-sample spans and `-O2`
only for r_bsp/r_plane/r_draw. The R_PointOnSide -O0 object is byte-identical;
no new renderer state/allocation. Release priority, full audits and all DMA
ownership checks remain. Keep baseline available by omitting the flag.

Four 520-frame A/B/B/A runs: matched **4.831 → 5.334 FPS (+10.40%)**,
renderer **187.64 → 168.18 ms**, planes **57.91 → 40.03 ms**, BSP/walls
**108.31 → 106.50 ms**. Most gain is in planes; this grouped experiment cannot
isolate span code from compiler flags or traversal from wall drawing.
Completion-to-HTTP availability remains low (**5.00 → 4.51 ms**); this is not
input-to-browser-paint latency. Retain validated per-stage latency improvements
even when overall FPS is unchanged.

**2,080 frames / 243 full paired audits** pass, with exact corresponding images,
2,032 exact HTTP payloads, all stall/held-STOP/heap-drain checks and maximum IRQ
gap 10.839 ms. Same four known native pixels differ. Image grows 272 bytes,
protected pages remain 146; mutable bounds unchanged. The flag remains opt-in
for broader scene/high-detail qualification. Next: profile exact arithmetic and
geometry inside the remaining 106.5 ms BSP/wall stage; preserve the point-side
workaround until independent target proof.
Evidence and reproduction: `artifacts/render-20261015/README.md` and
`game/doom/render/README.md`. Prior release-priority-only FPS limits below are
historical; this combined candidate exceeds 5.19 FPS in the tested workload.
<!-- /renderer-current -->

<!-- release-priority-current -->
**2026-10-15 release priority accepted:** release telemetry now separates shared
host-gate wait from ioctl execution (the latter still includes kernel scheduling).
Pending releases overtake ordinary waiters after the current holder finishes;
priority audits yield the gate between words while still reading every frozen
word and retaining all full paired audits. A validated immutable host frame is
published before its synchronous exact-generation release; ownership is unchanged.
Priority is now the default within opt-in Doom ping-pong; `--release-schedule
baseline` retains the comparison path. Other transports retain their defaults.

Two 520-frame, identical-binary ABBA/BAAB runs reduce mean release gate wait
**13.402 → 2.659 ms** and completion-observation-to-HTTP availability
**25.178 → 4.771 ms**. Sustained matched FPS is **4.837 → 4.835**, effectively
unchanged. HTTP availability is not browser paint latency. A third 520-frame run
with opt-in `--fast-memory` (private Newlib memcpy/memset word paths) reaches
**4.855 FPS**, only +0.40%; this does not establish a meaningful speedup.
Renderer wall time remains about 187 ms. Sustained 5.19 FPS is not achieved;
profile BSP/planes and exact arithmetic next, rather than assume more copy gains.

Across all three runs: **1,560 frames, 186 full paired audits**, stalled-host,
held-slot STOP and heap/IRQ drain pass. All 520 images agree across builds;
the same four known native pixel differences remain. 1,524 received HTTP payloads
match captured images. Maximum IRQ gap is 10.828 ms. Source, binaries, full replay,
mutation checks, timings and restoration evidence:
`artifacts/release-priority-20261015/README.md`.
<!-- /release-priority-current -->

Research handoff: [PERFORMANCE-RESEARCH.md](PERFORMANCE-RESEARCH.md) and the ranked
section of [BACKLOG.md](BACKLOG.md) cover Intel/RealDOOM/FastDoom/embedded-port
techniques. The accepted archived math object already uses `emul` for FixedMul
but references `___divdi3` for FixedDiv. These are source/object findings, not
new FPS results; do not replace exact arithmetic with approximate/FPU helpers
or count already accepted screen-copy/peer-yield work as a new improvement.

<!-- bulk-capture-current -->
**2026-10-15 bulk guarded framebuffer capture accepted:** steady ping-pong now
uses one 73,728-byte capture read instead of 72 small reads. Exact epoch/generation,
completion ordering, both guards, full raw journals and separate release remain.
Release credit is granted only after successful full copyout; partial-copy faults
also no longer grant credit in the legacy chunk path. The extended operation-8
buffer is 73,760 bytes despite the legacy ioctl number's size encoding; use the
matching new client/module. Card kernel and Doom engine are unchanged.

100 frames / 51 full paired audits, held-slot stall and STOP, heap drain, native
oracle and 45 evidence mutation checks pass. 95 HTTP payloads match captures.
Capture ioctl time fell **43.178 → 0.278 ms/frame**, completion-to-release
**61.398 → 26.405 ms**. Overall FPS was **5.192 → 4.802 (-7.52%)** in this
comparison; do not claim an FPS gain. Release ioctl waits rose 4.264 → 22.330 ms;
renderer time remains about 190 ms and audit/scheduling phases differ. Repeat
interleaved measurements before attributing the FPS difference to the new path.
Maximum IRQ gap: **10.488 ms**. First 52 card frames/palettes match the accepted
baseline; the same four known native pixel differences remain.

Initial 16 host-started comparison frames retain their old capture path. Bulk
capture is used by the existing opt-in ping-pong profile, not a new card protocol.
Evidence, exact binaries, ABI and replay: `artifacts/bulk-capture-20261015/README.md`.
Public IPv6 HTTP restored: 200 / 2890 bytes; boot
`27cc6b32-2d2f-4701-ba88-1c6d34484a42`, relay 1555 / supervisor 1552 owns
`dac960auto`. Doom 8087 closed. Historical PIDs below are stale; inspect actual
ownership before use.
<!-- /bulk-capture-current -->


Open performance handoff: [BACKLOG.md](BACKLOG.md) records the 2026-10-15
private memcpy/memset, renderer copy/fill and calloc/realloc candidates. These
are profiling/optimization tasks, not measured gains; use the latest accepted
baseline below before implementing them.

<!-- irq-drain-current -->
**2026-10-15 IRQ gap diagnosed and peer-yield shutdown fixed:** the original
59.855 ms spike occurred after STOP, not during rendering. The inherited outer
priority-31 region covered the remaining shared-buffer byte scan. A targeted
80 KiB shared-pin workload reproduced **55.997 ms drain with zero ticks** and
**60.237 ms maximum IRQ gap**. The fixed run retained all checks, took **60.753 ms
elapsed drain with six timer ticks**, and held maximum IRQ gap to **10.495 ms**.
The fix enables timer IRQs only after both workers cross the existing STOP
arrival barrier, then masks before done/suspend. Pins, allocator/reference locks,
controller ownership checks, IRQ-continuation drain and terminal quiescence remain.

Normal fixed Doom: **5.192 FPS**, **10.731 ms maximum IRQ gap**; instrumented
normal baseline 4.777 FPS / 10.785 ms. The shutdown-only change is not a claimed
FPS optimization; prior peer-yield achieved 5.273 FPS. Both normal repeats ended
with small buffers, so the separate stress pair establishes the long-scan fix.
Four bounded runs total **400 frames / 249 full paired audits**, with held-slot
STOP, global heap drain, Linux/Mac replay and capture-mutation checks. First 52
frames per run retain exact baseline pixels/palettes and only four known native
pixel differences. The stress workload changes input/restart timing; do not use
its fixed frame-66–68 interval as a normal loading/FPS comparison.

Frozen diagnostic page 3 (DRN1 schema 2; archived masked schema 1) is matched to
the raw control journal. New builds require it. Replay gates the fixed build at
**<20 ms full-session IRQ gap**, and checks drain tick progress against elapsed
time even when no subsequent IRQ could expose a final masked interval. This is
bounded acceptance, not a universal hard-real-time guarantee. 146 protected
pages remain; 16 mutable bytes remain in the existing layout. Current fix is in
the opt-in `--peer-yield` build; older images retain their original behavior.
Keep opt-in pending longer interactive qualification. This supersedes the open
59.9 ms-gap warning below. See `artifacts/irq-drain-20261015/README.md` for exact
sources, binaries, reproduction and restoration status. Historical ownership IDs
below are superseded; inspect actual hardware ownership before use.
Public IPv6 HTTP restored and verified 200 / 2,891 bytes; boot
`a32b6a8c-aedd-4f62-8537-0509ef285a26`, relay 1434 (supervisor 1416)
owns `dac960auto`. Bounded Doom port 8087 is closed.
<!-- /irq-drain-current -->

<!-- peer-yield-current -->
**2026-10-15 optional worker service yielding tested:** reviewed parallel chat
“Find i960MC board design guidance” and implemented `--peer-yield`. Worker 0
completes every network/control/shared-heap pass, then yields only while owned
application code runs. Both workers retain priority 2, controller priority 1,
10 ms ticks and original STOP/drain; ownership checks and full audits remain.
Matched Doom delivery improves **4.517 → 5.273 FPS (+16.73%)**; first-frame
execution **116.923 → 100.105 s**, upload **79.615 → 80.086 s**, warm restart
**2.780 → 2.830 s** (no restart improvement). 100 frames, 58 full paired audits,
held-buffer STOP, global heap drain, exact baseline pixels/palettes, Linux/Mac
replay and 35 capture mutation rejections pass. Four known native pixel
differences remain. Schema 4 adds peer telemetry; maximum completed-service gap
was 200 ms, sampled pass count 45,569, bounded by final worker progress 45,751.
**Keep opt-in:** final maximum IRQ gap was **59.855 ms**, versus baseline
10.546 ms and first candidate 10.623 ms. Aggregate capture cannot locate its
cause. Functional audit success does not qualify worst-case interrupt latency.
Next instrument long IRQ gaps with task/PC/phase attribution before default
promotion. Timer CPU attribution is phase-biased by yielding; use measured
wall/FPS, not a claimed CPU-share gain. First all-session-yield candidate remains
archived: 5.321 FPS but upload regressed to 106.514 s, so preparation now retains
original scheduling. See `artifacts/peer-yield-20261015/README.md` and
`rtems/exclusive/PEER-YIELD.md`. Historical ownership IDs below are superseded;
check actual remote ownership before hardware work.
Public IPv6 HTTP restored and independently verified: 200 / 2,891 bytes; boot
`74c0c2d0-c166-4185-9c75-8754a93ce11d`, relay 1658 (supervisor 1656)
owns `dac960auto`. Bounded Doom port 8087 is closed.
<!-- /peer-yield-current -->

<!-- screen-copy-current -->
**2026-10-15 remaining screen copy optimized and card-accepted:** fixed 320×200
indexed scale-one presentation uses one exact unrolled aligned word copy rather
than 200 bytewise Newlib row copies. **3.815 → 4.517 FPS (+18.39%)** in the matched
frames 21–50 window; screen copy **44 → 12 ms wall / 22 → 6 ms sampled task CPU**.
Renderer remains ~209 ms wall / ~105 ms sampled CPU. Persistent `I_VideoBuffer`
is retained: cached row pointers, incremental updates and zone ownership cannot
safely alias rotating/pinned DMA slots. Other geometry and unaligned-pointer
fallbacks remain. No libc-wide, DMA, scheduler, ownership or guard changes.
100 frames, **67 full paired audits** at unchanged cadence, held-buffer STOP,
heap drain, exact baseline pixels/palettes and full Linux/Mac replay pass;
33 mutated captures rejected. Four known native pixel differences remain.
Private platform builds use this automatically; WAD ring/ping-pong stay opt-in.
Evidence: `artifacts/screen-copy-20261015/README.md`. One matched run, not a
long soak; 10 ms telemetry is elapsed/sample-based, not cycle-accurate. Larger
remaining FPS headroom is renderer work/scheduling, not the remaining 12 ms copy.
Historical owner IDs below are superseded; inspect actual ownership before use.
Public IPv6 HTTP restored and verified 200 / 2,891 bytes; boot
`a9a9032f-68fa-4a83-8a6b-27032556f98b`, relay 2619 (supervisor 2617)
owns `dac960auto`. Bounded Doom server 8087 is closed.
<!-- /screen-copy-current -->

<!-- wad-copy-current -->
**2026-10-15 actual WAD-cache word copies accepted:** first-frame loading
**192.075 → 117.566 s (38.79% shorter)**; same-level warm restart
**4.506 → 2.890 s (35.86% shorter)**. All three cache copies total
**93.640 → 17.980 s**. Upload remains separate (~80 s); gameplay stays
**3.803 → 3.815 FPS**, not a demonstrated rendering gain. Equal alignment uses
exact byte prefix/tail plus aligned 32-bit copies; unequal alignment stays
bytewise. No DMA/cache-policy/guard/ownership changes. 100 frames, **68 full paired
audits** at unchanged 3 s cadence, held-buffer STOP and heap drain pass. First 52
frames match baseline and retain only four known native pixel differences.
ASan/UBSan edges, deterministic native runs, full Linux/Mac replay and 33 mutation
rejections pass. See `artifacts/wad-copy-20261015/README.md` for exact binaries,
sources, timings, reproducibility and service restoration. WAD ring/ping-pong
remain opt-in; next optimize retained staging/direct owned-cache DMA/read-ahead,
not remove audits. Historical profiling baseline and its owner IDs below are
superseded by this acceptance; inspect actual owner before hardware work.
Public IPv6 HTTP restored and verified 200 / 2,891 bytes after normal reboot;
boot `9bef2976-8b43-4c8d-bd4e-1e0b719249b7`, relay 2653 (supervisor 2651)
owns `dac960auto`. Bounded Doom server 8087 is closed.
<!-- /wad-copy-current -->

<!-- wad-profile-current -->
**2026-10-15 bounded WAD/DMA profiling accepted:** opt-in `--wad-profile` builds
retain every ownership/guard check and all full paired audits. A pinned-source
64 × 32 KiB host-to-card benchmark observes **20.605 MB/s** from DMA start to
completion and **6.793 MB/s** through the ordinary guarded transfer routine;
extra full-payload comparisons are timed separately. These are short elapsed
measurements including interrupts, not maximum PCI/RAID throughput or CPU cycles.
Across startup, 100 frames and warm restart, actual WAD-cache filling costs
**77.960 s**, cache/bounce → Doom copies **15.680 s**, target guard scans
**35.802 s**, staging copies **13.597 s**, initialization **8.767 s**,
allocation alone **3.138 s**, freeing alone **2.581 s**. Ordinary DMA completion
intervals total **2.843 s**. Categories have explicit nesting; do not add them
blindly. Cache timings use the existing 10 ms clock; kernel timings use read-only
timer 0 at nominal 4,166,700 Hz. Full-audit gate waits and host Python/ioctl time
are separately recorded and overlap card execution.
Final run: first frame **192.075 s** after preparation (80.113 s upload separate),
warm restart **4.506 s**, fixed-scene sample **3.803 FPS**. No speedup is claimed
for this instrumented build. Two completed runs pass **200 frames / 178 full
audit pairs**, held-buffer STOP, heap drain and local replay; final evidence
rejects 24 frame, three WAD and six timing mutations. First 52 controlled frames
retain exactly the four known native differences and exact palettes.
The initial completed candidate exposed the wrong, unused stdio cache; its zero
cache telemetry is explicitly invalid and preserved. The final build profiles
the actual backend, requires matching engine flags and cross-checks all cache
calls/bytes against runtime counters and WAD requests. Both actual native
52-frame runs prove nonzero backend telemetry before final hardware acceptance.
Next: optimize **actual WAD-cache byte copies**, then retained staging/direct
owned-cache DMA and adaptive read-ahead. Do not reduce guards or full audits.
146 protected pages; final mutable reserve **64 bytes**; no flash/map change.
Evidence/manual: `artifacts/wad-profile-20261015/README.md`. Exact sources,
binaries, captures, failed instrumentation evidence and replay tools are saved.
All captures were copied/hash-checked/replayed locally before normal reboot.
Public IPv6 HTTP is restored and verified 200 / 2,891 bytes. Current boot
`94855ff1-240c-45ce-a28f-bfd47d4195f1`, supervisor **3570**, relay **3572** owns
`dac960auto`. Doom test server is closed. Inspect current ownership before new
card work; stop the relay normally and never force-unload retained mappings.
<!-- /wad-profile-current -->


<!-- wad-ring-current -->
**2026-10-15 WAD ring bounded acceptance passed:** two guarded 32 KiB host slots,
shared request/response/completion records and 64 KiB read-ahead are opt-in via
`--wad-ring --pingpong --pipeline-test --wad-dma`. Same-build first frame:
**290.087 → 186.566 s (35.69% less, 1.555×)**, excluding ~80 s engine upload.
Warm restart **2.842 → 4.242 s (49.25% slower)**: do not promote the default.
Read-ahead raises total test payload from 20.89 to 59.15 MB. Baseline metadata
queries cost 180.606 s; new RAM-only ioctls plus pending polls cost 3.873 s,
excluding Python/card execution. The first byte-oriented ring passed safety but
regressed startup to 456.109 s; it is archived, not hidden.
All three runs pass: **300 frames, 358 full audit pairs**, exact source/completion
replay, four full frame comparisons per run, frame stall/resume, owned STOP and
heap drain. First 52 controlled frames are identical across card runs and retain
exactly four known native pixel differences; palettes match. Steady FPS is about
3.8–3.9; no sustained renderer speedup is claimed. Guards are fully scanned at
unchanged points using word operations; descriptor/ownership/quiescence checks
and all full audits remain. 146 protected pages, 288-byte mutable reserve;
no flash or memory-map change. Native tests cover publication reread, descriptor
bits, all guard bytes, host timeout and STOP while waiting. Physical mid-WAD
STOP/stall/timeout injection and longer interactive play remain unqualified.
Exact sources/binaries/captures and Linux/Mac replay are preserved in
`artifacts/wad-ring-20261015/`; protocol: `rtems/dma/wad_ring/README.md`.
Next optimize adaptive smaller read-ahead for warm/small reads; arbitrary
unaligned ring reads are not supported by the private cache-fill API.
All test ownership is released after local archive verification and normal
reboot. Public IPv6 HTTP is restored and verified 200 / 2,891 bytes from the Mac.
Boot `cf670f3e-d97f-4bf3-8649-04e1fc937e49`, supervisor **2721** / relay **2723**
owns `dac960auto`; see `restoration.json`. Inspect actual owner before further
card work; stop the relay normally and never force-unload retained mappings.
<!-- /wad-ring-current -->


<!-- doom-columns-current -->
**Column kernels accepted in bounded low-detail testing, 2026-10-15:** baseline
**3.478 FPS**, specialized C **3.857 (+10.89%)**, i960 assembly **3.821 (+9.86%)**.
Both reduce renderer wall **211.4 → 180 ms**, sampled CPU **105.9 → 90 ms**.
Assembly has no demonstrated extra advantage; prefer C for a future fixed play
build. `--pipeline --column-test` is a bounded baseline/C/assembly/baseline
experiment requiring `--pipeline-test`; it must not run interactively. Defaults
remain unchanged. 96 target oracle cases (real assembly), 52 guarded frames,
14 full audit pairs, exact first four DMA/mailbox pairs, STOP/drain, Linux/Mac
system/frame/WAD replay and 35 tamper cases pass. All optimized images match
prior card frames exactly; the four existing native/card pixels remain unresolved.
All 52 HTTP payloads match. No new timer policy, firmware or arena expansion.
Evidence: `artifacts/doom-columns-20261015/README.md`; code/manual:
`game/doom/columns/README.md`. Admission 872,376 bytes; kernel tail still 400.
The exclusive test has ended; archives are saved locally and replayed. Normal
reboot released the test module. Public IPv6 HTTP is restored and verified 200
from the Mac; boot `03e2a874-bffb-4c2e-b4f6-ec6d90e7a3db`, supervisor 1427 /
relay 1432 owns `dac960auto`. See `restoration.json`. Inspect actual owner before
card work; never force-unload retained mappings. Older service/PID notes below
are historical and superseded by this entry.
<!-- /doom-columns-current -->

<!-- doom-detail-current -->
**Low detail accepted, 2026-10-14:** high **2.481 → low 3.178 FPS (+28.09%)**;
low blocks vary 2.908–3.503, including the 884 ms frame-40 interval. All 52
frames, 14 full audit pairs, ownership/ACK, STOP/drain and 35 tamper cases pass.
Renderer wall **315.5 → 210.0 ms**, timer-sampled Doom CPU **158.2 → 105.0 ms**:
approximately half CPU share. This is 10 ms sampled attribution, not cycle-exact
or higher-resolution timing. Prior high-detail card images match exactly; low
has four unresolved native pixel differences in the existing small region.
Build `--pipeline --detail-test` for bounded high/low/low/high; fixed optional
`--low-detail --no-fnv --direct-frame` for a separate interactive candidate.
Do not claim 10 FPS or long interactive acceptance. Evidence and exact binaries:
`artifacts/doom-detail-20261014/README.md`. Test closed and local replay passed;
Public IPv6 HTTP restored (200), boot `1917f487-902d-4579-bbea-5b5b859db300`;
relay supervisor 1497 / Python 1521 owns `dac960auto`. Stop it normally before
new card work. Consult `restoration.json` there for service state.
Never force-unload retained resources or overlap hardware owners.
<!-- /doom-detail-current -->

<!-- doom-present-current -->
**2026-10-14 presentation accepted:** optional FNV and direct delivery-slot
presentation measured **1.965 → 2.474 FPS (+25.94%)** with full audits. All 52
frames, 14 audit pairs, exact ACK/ownership, STOP/drain and 35 tamper cases pass.
Pixels/palette match the prior card run; known seven native pixel differences
remain. Renderer ~317 ms, retained screen copy ~47 ms, DMA hardware quantized
mean ~3 ms. Profile query/host FNV validation affects measured FPS; do not claim
an uninstrumented or 10 FPS result. Default remains conservative; features opt-in.
The first selector attempt failed and is archived separately; table selection
passes. See `artifacts/doom-present-20261014/README.md` and
`game/doom/play/PRESENTATION.md`. Test owner closed and evidence verified before normal reboot. SSH has not
returned; user power-cycle requested. Public HTTP restoration pending; see
`artifacts/doom-present-20261014/restoration.json` and `restore.sh`. Never
force-unload retained exclusive mappings.
<!-- /doom-present-current -->

Bulk WAD DMA is physically accepted (2026-10-14). Use
`--pipeline --no-crc --wad-dma`; WAD and framebuffer CRC are separately optional,
while image admission, ownership, bounds, guards and full audits remain.
First level 1642.751 → 318.183 s; warm same-level restart 10.291 → 3.068 s.
All 52 frames match mailbox; 14 paired full audits, STOP and heap drain pass.
Evidence: `artifacts/wad-dma-20261014/README.md`; manual: `game/doom/play/PLAY.md`.
Network proof now completes before large game upload, with unchanged checks and
deadlines. Never force-unload retained resources; verify actual hardware owner.


<!-- doom-dma-cleanup-current -->
**Doom DMA diagnosis batch (2026-10-14):** two complete comparisons passed:
instrumented target 0.966→1.384 FPS (+43.26%), exact earlier target
0.969→1.380 FPS (+42.45%). Each kept 28 full monitor/RAM pairs, four exact
same-frame comparisons, 16 guarded DMA captures, 28 previous-card-exact images,
owned STOP and global drain. Full replay/tamper checks pass. **The earlier
intermittent timeout did not recur and is not diagnosed or fixed.** New phase
markers and bounded failure-only fault capture are diagnostic, not a proven
cure; the live fault path remains unexercised. Keep DMA opt-in and all audits.
Both closed runs were copied, hash-verified and replayed locally before reboot.
Public IPv6 HTTP restored and returned 200 from the Mac. Current card owner:
public relay supervisor 2619 / Python 2622, boot
`333a779d-bfd4-4a59-8562-1cce3176b5e6`, bound `dac960auto`.
Next: a fast repeated-frame stress harness covering timer interruption of
polling/cleanup, then fix a reproduced defect. Evidence:
`artifacts/doom-dma-cleanup-20261014/README.md`.
<!-- /doom-dma-cleanup-current -->

<!-- doom-dma-current -->
**Doom DMA comparison failed full acceptance (2026-10-14):** four pinned
frames matched mailbox/DMA exactly; same-frame transfer improved **0.498802 →
0.225233 s (2.2146×)**. Five DMA frames and eleven delivered frames passed, then
frame-12 completion polling timed out. Retained destination bytes match the old
physical frame and guards remain intact, but bus mastering remained enabled.
Do not confuse delivered bytes with quiescence. **No DMA FPS improvement or
final heap drain is accepted.** All 23 recorded full monitor/RAM pairs precede
the first frame; no post-DMA audit was obtained. The full verifier rejects the
run; explicit failed-prefix replay passes and rejects 30 frame/journal and 24
snapshot mutations. Two review-found release races were closed with an atomic
pending check/pointer clear; both earlier startups were stopped before DMA and
archived. Default play remains unchanged; `--dma` / `--dma-test` is experimental.
Next instrument completion/cleanup and terminal fault diagnostics, reproduce the
stall, then repeat full A/B/B/A and STOP/drain. Do not enlarge timeouts, remove
checks or recycle retained resources. The failed capture and exact build are
locally hash-verified. Reboot completed; public IPv6 HTTP returned 200 from the
Mac. Relay Python 1675 (supervisor 1604), boot
`91493f0a-3c46-4afa-a40c-6b62ad8304be`, owns the card. Test reservation released;
stop that relay normally before further exclusive tests.
[Evidence](../../artifacts/doom-dma-20261014/README.md).
<!-- /doom-dma-current -->

<!-- doom-bulk-current -->
**Doom mailbox bulk accepted (2026-10-14):** opt-in `--bulk` uses eight-byte
MU beats in fixed 1 KiB reads; no DMA or new RAM aperture. Same-run readback
improves **5.447 → 0.509 s** and delivered FPS **0.167 → 0.999 (5.97×)**.
Four complete same-frame comparisons, 28 frames, 30 full monitor/RAM pairs,
three refusals, exact input/ACK replay and owned/global STOP pass. All 95,622
allocations and 638 shared handles drain. Physical capture and snapshot
mutation tests each reject 24 corruptions. Preserve every audit, generation/
window check, reread, pin, STOP and uncertainty rule; scalar remains default.
The engine is unchanged. Native/card still differs by 6–8 pixels in the known
small region; palettes/padding and the first six previous card frames match.
Startup remains about 23 minutes. Replay timer-wrap coverage now depends on
actual audited elapsed ticks rather than the maximum configured budget.
The test workspace is `/home/mit/i960-doom-bulk-20261014`; port 8087 is stopped.
Both complete archives are saved and hash-verified locally. Reboot completed;
public IPv6 HTTP returned 200 from the Mac. Public relay Python 2127 now owns
the card in boot `cbeb9d86-ab62-4ac1-a830-1b30433e2e46`; the test reservation
is released. Stop the relay normally and coordinate before future card work.
Older ownership and next-step notes below are historical. Next: profile the remaining
render/service/ACK costs before any larger DMA transport.
[Exact results, sources, binaries and reproduction](../../artifacts/doom-bulk-20261014/README.md).
<!-- /doom-bulk-current -->

<!-- doom-play-current -->
**Interactive Doom work (2026-10-13; six-frame input/STOP passed):**
The user chose browser play now, with optimization/debugging driven by use.
The opt-in persistent engine, bounded input FIFO, immutable frame/ACK channel,
browser relay and fresh-workspace build/run wrappers are implemented. Sanitized
native 40-frame input runs are deterministic, differ from no-input, and pass
owned STOP/heap drain. Channel bounds, stale ACK, overflow, timeout and STOP
race tests pass. Keep `--point-side-o0`, identity/ownership/guard checks and full
paired audits (normal play interval 60 s; diagnostic interval 3 s).

The corrected card candidate is running in
`/home/mit/i960-doom-play-20261013b`, boot
`83ecfee3-b3a2-47bf-a415-2ce0b7d0602f`, supervisor 2999 / Python 3001. Use browser port **8088**: temporary corrected
keyboard bridge supervisor 118766 / Python 118767 duplicates the existing FD;
the original 8087 owner retains frame/ACK/STOP work. New builds use corrected
163/162 fire/use codes directly on 8087. Do not open competing input clients.
It owns the card exclusively; the public autonomous IPv6 HTTP relay is stopped.
Do not unload or reuse its resources. Six physical frames, forward/release and owned STOP passed; mean readback
5.473 s, delivery 0.169 frames/s. The first 26 full audit pairs passed. A host
comparison finds 7–8 differing pixels in a small region; palettes/padding match.
The fresh session is live: 130 frames and 57 full audit pairs are preserved;
browser turn/fire passed, with muzzle flash and ammo 50→48. The play budget
expires around 23:58 Europe/Berlin October 13. Global shutdown/final file release
is not claimed; both original and duplicated descriptors must close normally. Prior ownership and “next”
statements below are historical. See [current evidence and guide](../../artifacts/doom-play-20261013/README.md).
<!-- /doom-play-current -->

<!-- doom-visible-current -->
**Bounded visible Doom and browser delivery accepted (2026-10-13):**
The opt-in `--visible` build skips the opening wipe and returns two 320×200
indexed frames with palettes. Both full card captures match native byte for byte;
ticks 2/3 have identical pixels, so motion and interactive gameplay remain open.
The batch passes **604 full snapshot/RAM pairs, 75 dual-stack rounds, 441
checkpoints / 66 ACKs**, in-engine STOP, repeat and global parked-state drain.
All **322,731 allocations and 9,917 shared handles** retire. Default full native
replay accepts **8,152 replies**; 24 startup, 13 frame and 24 snapshot mutations
are rejected. No shutdown assertion or native replay abort recurred.

Normal result collection takes **1,541.382 / 1,537.299 s**; STOP **26.718 s**.
Two-slot readbacks take **15.340 / 18.087 s**, including full-audit contention;
Mac PNG HTTP delivery averages about **19 ms**. These are not rendering FPS.
The immutable 131,072-byte archive uses the existing 8 MiB arena after private
engine cleanup; next entry and global drain release it. No RAM grant changes.
Keep full paired audits, independent native bytes, checkpoint ACKs and
`--point-side-o0`; uncertain transfers retain the session until reboot.
Next: bounded visible motion, then persistent frame publication/backpressure and
input. Keep this mode opt-in. Both archives are locally hash-verified. Public
IPv6 HTTP and outbound IPv6 are restored in boot
`083c2956-4f85-49e6-abb9-3d485c4d7422`; relay supervisor **1745**, Python **1843**
owns the card. Static gallery PID **1746** serves http://192.168.2.75:8086/ and
never opens the card. Test reservation released; stop the relay cleanly before
future exclusive work, and never force-unload a retained module.
[Exact sources, binaries, captures, browser instructions and limits](../../artifacts/doom-visible-20261013/README.md).
<!-- /doom-visible-current -->

**Doom N3 first-frame and shutdown baseline accepted (2026-10-13):**
The bounded two-worker arrival barrier fixes shared cancellation racing a peer's
last acquire. A deterministic actual-allocator test reproduces the old SHCHECK 10
and passes with the barrier; the original card capture did not identify its exact
assertion line. Existing allocator stress and ownership/corruption tests pass.

The new card batch passes **626 full snapshot/RAM pairs**, **75 dual-stack network
rounds**, both normal Doom startups, in-engine STOP, and global STOP/final drain.
All **306,981 allocations** and **10,209 shared handles** retire; parked upload
query and full native replay of **7,832 replies** pass. Both 199-record normal
checkpoint streams match native, with **403 total records / 50 ACKs** across
normal/STOP/normal. Normal times: **1,522.551 / 1,514.546 s**; STOP: **25.922 s**.
Pixel FNV **4000963876**, palette FNV **1611003811**. The 24 startup-evidence
mutations and 24 snapshot corruptions are all rejected.

Native replay now models a 1 ms command transport delay outside target locks;
the target mutex deadline is unchanged. A stale remote checkpoint helper was
also synchronized. `--commands-only` remains explicitly diagnostic and cannot
accept physical drain; default full replay was used for this new capture.
Preserve full paired audits, native oracle, checkpoint ACKs and the narrow
`--point-side-o0` workaround. The engine and 8 MiB arena are unchanged.

This accepts the bounded initial wipe frame, STOP/repeat and system drain—not
visible gameplay, browser Doom or rendering FPS. Next: bounded visible-frame
progression, framebuffer readback and browser delivery, with the same full gates.
After local archive verification and reboot, public IPv6 HTTP returns 200 from
the Mac; outbound IPv6 fetch also passes. Production relay supervisor **4358** /
Python **4359** owns the card in boot `c76b2f32-a14d-4c03-952f-cbfa6b254cb9`.
Test reservation released; coordinate and stop the relay cleanly before reuse.
[Exact sources, binaries, captures, failure reproductions and results](../../artifacts/doom-shutdown-20261013/README.md).

**Height/branch diagnosis (2026-10-13; full Doom still unaccepted):**
The first 49 checkpoints match, including all decoded sector-height and side
texture-ID fingerprints. At request 4,670 the card spawns in subsector **1394** /
sector **82** (floor **−72**, ceiling **96**); host and independent WAD decode select
**226 / 0** (floor **0**, ceiling **192**). Both recorded height calls correctly
add viewheight **41** to the card's floor, producing **−31**. Do not patch the
camera height to mask the earlier wrong BSP selection.

A captured `cmpi` / `cmpib` / `testg` ordering loses the intended condition code.
An explicit model predicts the exact wrong sector. A bounded probe outside RTEMS
uses the same **160-byte optimized function body** before linking: optimized
code fails **2/9** vectors, scheduling disabled still fails **1/9**, and `-O0`
passes **9/9**. All **27 transactions / 2,970 commands / 81 paired staging phases**
pass full audit, RAM restoration and clean unload. This confirms a function
miscompilation, not a global compiler fix or full Doom success. Preserve accepted
kernel/toolchain binaries; disabling scheduling alone is not sufficient.

The long run preserved **279 full snapshot/RAM pairs**, 37 network rounds,
27,725 exact WAD fragments and 188 retrieved checkpoints. Last retrieved marker:
planes finished (43). No new post-render/wipe/copy marker was retrieved; this does
not narrow the exact hang beyond the previous masked-render marker or establish
a fault PC. First frame, startup STOP/repeat and final drain remain unaccepted.

Next: audit/fix backend condition-code dependencies (or a narrowly verified
implementation), broaden the small card proof, then rebuild and repeat every
native/ABI/placement and full N3 gate. Add bounded host-confirmed draining for
selected hang markers; current nonblocking logging can outrun host retrieval.

Exact binaries, sources, captures and replays are archived. Public HTTP returned
200 after reboot and the clean probes; reservation released. Production relay
PID **19965**, boot `e7e1bcd3-0421-4d31-8fa9-9d6748d7110e`, owns the card; stop it
cleanly and coordinate before future exclusive work. [Evidence](../../artifacts/doom-height-20261013/README.md).


**Startup checkpoints (2026-10-13; divergence localized, N3 still unaccepted):**
The first 50 scalar checkpoints match the native host. Record 51, stage 38,
first differs: player `viewz` is **−31 map units on i960 versus +41 on host**,
at WAD request 4,674, before the differing texture read. Position `(0, −160)`,
angle 90°, view sine/cosine, level counts and the side texture-ID fingerprint
match. Counts do not prove all geometry contents match. BSP, planes and masked
rendering finish; no `DG_DrawFrame` checkpoint or owned exit was captured.

The physical run preserved 170 checkpoint records, 274 full snapshot/RAM pairs,
one extra snapshot plus 40 final RAM words, and 37 network rounds. All 27,725
completed WAD fragments (14,194,884 bytes / 4,764 requests) match the pinned WAD.
An upload-query timeout retained the module. Final fault PC, first frame, STOP,
repeat and drain remain unknown/unaccepted; do not weaken their gates.

The opt-in 144-byte API and separate read-only channel use a non-overwriting
512-record, 16,400-byte registered log inside the existing 8 MiB arena. Native
normal/STOP/deadline/read-error/repeat and the accepted N2 replay pass. Runtime
code fits the existing guarded engine window. Exact card/build archives are local.
After hash verification and reboot, public IPv6 HTTP returned 200 from the Mac.
Exclusive reservation released; production relay PID 3737 in boot
`5e697ec6-a2e7-488d-95b3-4262e31f9b7f` owns the card. Coordinate and stop that relay
cleanly before future exclusive use.

Next: checkpoint player spawn and height calculation (`mo->z`, floor/ceiling,
viewheight, bob, sector/subsector selection), compare relevant field offsets and
signed fixed-point operations. Independently bracket the path from completed
masked rendering to `DG_DrawFrame`; the wrong height does not yet explain the hang.
[Evidence and reproduction](../../artifacts/doom-checkpoints-20261013/README.md).


**N3 actual startup (2026-10-13; implemented, not physically accepted):**
The real private-library Doom engine passes ten native first-frame / STOP /
deadline / read-error / repeat cases, with exact reference pixels and palette.
Both card attempts entered actual initialization but timed out before returning
an accepted frame. The first completed 4,769 WAD requests; the compatibility
retry completed 4,764. Both match the host through request 4,674 and then choose
the same different texture region. Every captured completed WAD fragment matches
the pinned file. Preserve both failures; do not substitute host/model success.

Startup-only `-mold-align` corrects an independently measured allocator/layout
mismatch: 55 Doom/zone/API constants match the 32-bit host and RTEMS callback
offsets stay unchanged. It did **not** remove the hardware failure. Candidate
span 744,608 bytes, 13,231 relocations, admission 797,532 bytes, zero unresolved
imports; no new RAM grant. Its kernel SHA256 is
`25dd26bc206cec40f77e55a9a7666adb6df1f85cf7c6d662d1c301fed1bec4a5`.

The retry preserved 275 full snapshot/RAM pairs plus one complete snapshot and
44 words of its final RAM page; captured fault markers are zero, but the fault
PC and final state are unknown. Packet pumping between four-word audit groups
allowed 36 complete dual-stack rounds, versus six previously. All full audits
remain required. The upload query timed out after 2,772.949 ms and the driver
retained resources until reboot. Startup-only aggregate budget is 90 minutes;
per-engine 30-minute and per-read five-second limits are unchanged.

Keep startup opt-in and N2 as the accepted baseline. Next: independently readable
startup checkpoints/fingerprints around level setup, texture precache, draw and
exit; locate the first state divergence before another full attempt. Then repeat
normal / partial-read STOP / normal with complete replay and drain. Neither this
first-wipe milestone nor visible/browser Doom is accepted yet. Both captures are
saved; reboot cleared retained resources and public IPv6 HTTP returned 200. The
Doom test reservation is released; coordinate with the public relay before reuse.
[Evidence and current status](../../artifacts/doom-startup-20261013/README.md).


**N2 WAD batching checkpoint (2026-10-12):** opt-in `--wad-batch`
uses owned, pinned 4 KiB requests assembled from ordered 512-byte fragments.
CRC, exact lengths, sequence/offset binding, STOP, timeout, full image/RAM audits
and final drain remain enforced. First-frame host trace: 27,648 → 4,747 logical
requests (82.83% fewer), identical delivered bytes. Small on-card cache probe:
24 → 7 requests, mean 3.588 → 1.655 s (2.17×; two runs per size, including report
queries, both using WAB1). No on-card Doom startup or FPS claim. Six host demos
retain all 12,600 frame hashes. Extra peak payload memory is 7,936 bytes plus
allocator overhead, within the unchanged 8 MiB arena.

Physical STOP/drain completed at tick 101,897. The live harness then failed an
obsolete expected-cancellation count (14 rather than 15); the raw failure is
preserved. A labelled derived view recovers the final raw reply and kernel
monitor log, separates and validates exception diagnostics, and passes unchanged
network audits plus full upload/native replay (7,949 commands). Keep this
qualification when citing acceptance; do not call the original live harness a
clean pass. The harness is corrected for future runs. Keep the feature opt-in.
[Evidence, reproduction and limits](../../artifacts/doom-batch-20261012/README.md). Next is N3: bind batching
into a newly authenticated engine image, perform bounded actual Doom
initialization, then verify the first frame. The accepted old diagnostic engine
still uses the 512-byte ABI; do not silently reuse its admission hashes for a
changed engine. Coordinate hardware ownership before testing.

**Accepted engine-preflight baseline (2026-10-12):** the engine-linked diagnostic
passed on-card normal / STOP / normal, changed-code/metadata refusal, executable
revalidation and full drain at tick 100,085. The bit-64 failure was a dispatcher
window: incoming task identity on the outgoing stack. Opt-in `--dispatch-atomic`
keeps interrupts masked through transfer and preserves the caller's saved level.
No IRQ guard or owner admission was relaxed. The 1 MiB initial reservation and
contiguous 6 MiB zone now have physical acceptance; candidate span 754,448 bytes,
13,175 relocations, admission storage 807,148 bytes, measured port peak 6,356,612
bytes plus separate cache/image/proof/stack costs. Both bootstrap windows remain
protected. Keep `--doom-engine`, `--dispatch-atomic` and `--wad-poll` opt-in.
Full native capture replay passes 7,853 commands; instant host replies had failed
the probe's clock-liveness check, fixed only in the replay transport model.
44 runtime/cache/relocation/owned/engine mutations and seven IRQ mutations reject.
Actual Doom initialization/rendering remains pending. The original next step was WAD batching; see the N2 checkpoint above.
Engine initialization and first-frame verification remain pending. Preserve all full audits.
The historical global ISR-level getter remains unfixed; this owner predicate uses
a read-only PC query. Coordinate card ownership before further hardware tests.
[Accepted evidence and replay instructions](../../artifacts/doom-progress-20261012/README.md).


**Private Doom runtime/cache checkpoint (2026-10-12):** the new private
Newlib/platform candidate has **zero unresolved imports**, a 752,804-byte
code/data/BSS span and 13,113 relocations matching three independent links.
The full private 32-bit library/port passes ASan/UBSan. It does not override
kernel libc and is not admitted for engine launch. The separate 1,760-byte
cache probe passed real i960 execution: both normal hashes matched, cached
repeats made no extra reads, and CRC/short/error/timeout/recovery passed.
Full audits, six network rounds/812 packets, 625-command replay, 48 evidence
mutations and STOP drain at tick 17,855 passed. The upper loader uses 25,312
bytes with unchanged boundaries. Explicit Doom object suffixes fix a linker
wildcard that depended on the workspace name. Public IPv6 HTTP is restored (200).
Next: owned engine entry/yield/STOP and i960 exit boundary, larger manifest
admission, WAD batching/initialization budget, then first frame. Keep the current
closed whitelist; **Doom itself has not run on card**.
[Runtime contract](runtime/platform/README.md) ·
[Physical evidence](../../artifacts/doom-platform-20261012/README.md).

**Relocated code/data/BSS proof accepted (2026-10-12):** the reviewed 184-byte
image executed twice at `0xc02d0050` inside the shared arena, returning
`1228486293` both times. Six trusted relocation sites, 128 zero-filled BSS bytes,
all 32 resulting counters and initialized code/data were checked. Eight admission
refusals, all paired audits, six network rounds and STOP drain at tick 14,903
passed. Native replay covers 593 requests / 1,511 upload ioctls; 24 snapshot,
eight WAD and seven relocation evidence mutations are rejected. TCP replay now
separates reused port tuples only after captured closure and a fresh SYN; gaps,
conflicting retransmissions and echo mismatches still fail. The exact card
build is archived. This is a closed returning proof, **not Doom execution**;
44 engine imports remain. Next: libc/platform imports and i960 cache/runtime
integration, then bounded initialization. Preserve both worker owners, pins,
full audits, and exclusive reboot-only release. The reboot completed and the
original public IPv6 HTTP service is restored (independent HTTP 200).
[Contract](runtime/relocate/README.md) ·
[Evidence](../../artifacts/doom-relocate-20261012/README.md).

**New host-only cache/link checkpoint:** [runtime/cache/README.md](runtime/cache/README.md) and
[runtime/relocate/README.md](runtime/relocate/README.md). Opt-in `--wad-cache` requires `--arena-runtime`.
Only the separately allocated bounce base crosses runtime reads; zone interior
pointers stay in the owning application. Single IWAD, no rebind or reopen after
close; no general stdio/filesystem shim. Six host demos match 12,600 hashes with
1 MiB reserved image + at most 6,473,545 dynamic bytes in the 8 MiB arena.
44 engine imports remain. That REL checkpoint was host-only; the small proof is now accepted above.
Never bypass its closed card whitelist or infer relocation records from
pointer-looking words. Doom engine admission remains separate work.

**Runtime-entry/WAD bridge accepted:** [runtime/entry/README.md](runtime/entry/README.md).
`--doom-runtime` requires `--doom-shared`. Only the exact reviewed probe may
enter through the v1 table; this is not arbitrary Doom launch. WAD staging is
separate from UPL1, maximum 512 bytes, one immutable bound file. Copy in the
owning worker after claim/CRC; keep its allocation loan until completion or
cancellation. No cross-task destination pointer, ISR copy, or implicit unpin.
Keep the host WAD query/reply inside the reentrant audit gate, retain full
audits and the 500-tick timeout, and never retry uncertain writes. The live
normal/error/timeout/recovery batch passed; STOP-in-read is native-tested only.
No Doom engine has yet run on card. Next are imports/linking and a WAD cache.

**Shared arena follow-up accepted:** read [runtime/SHARED-ARENA.md](runtime/SHARED-ARENA.md).
Use one task mutex and private per-worker allocation records; retain pins during
unlocked bulk work and reclaim only after both task/IRQ drains. Wrong-task
calls must not write diagnostics. `--doom-shared` requires `--doom-heap`.
Both workers must not block at once: idle still deliberately faults and has no
registered IRQ owner. Keep a control worker runnable or explicitly admit/test
idle ownership. Preserve full audits, exclusive reboot-only release and the
cooperative public service. Earlier single-owner notes below are historical.


Run runtime/test.py and runtime/verify_evidence.py for allocator evidence.
Read [runtime/README.md](runtime/README.md) for the allocation integration.
Opt-in --arena-runtime resolves the five allocation symbols: 631,112 static
bytes, 53 imports remain. The baseline inventory below remains historical.
The resident --doom-heap proof passed on-card; keep the single arena owner and
separate system libc. Do not expose it to another task without shared serialization.

Read [DETERMINISM.md](DETERMINISM.md), [OS-PLAN.md](OS-PLAN.md), README.md and
RAM-CONTRACT.md. The three variable frames were out-of-post sprite reads:
negative fixed-point indices wrapped to 127. Keep bounded_column.h and its
masked-dispatch bounds on both host and target; preserve wall wrapping.
Do not suppress frames, weaken comparisons or zero the heap to hide bad reads.

The current i960 relocatable engine is 627,096 bytes and has 58 unresolved
externals. It is NOT a loadable card image. Runtime code, WAD I/O and arbitrary
application task launch remain. The prior broad host allocation peak is
6,456,649 bytes, including the 6 MiB zone; never count zone contents twice.

The parallel resident-upload profile now has an accepted guarded 8 MiB arena
and an on-card contiguous 6 MiB proof. This does not automatically redirect
libc malloc or prove a final Doom memory manifest. Read residentnet/UPLOAD.md.

Keep the pinned DoomGeneric/Freedoom inputs and licenses. Host captures include
indexed pixels, RGB palettes and game-tic traces; instrumentation stays host-only.
The archived original milestone intentionally retains its old failed comparison.
Use verify_determinism.py for the new corpus, not a changed old verifier.
Finite host repeatability is not i960 correctness or all-WAD compatibility.

Do not touch the parallel RTEMS files, card owner or public service during host
work. Preserve all existing physical memory/ownership audits for target testing.

**New AcceleRAID 160 FPS work (2026-10-17):** the accepted first-frame engine
is now exercised by a separate bounded 32-frame RTEMS kernel in
`rtems/accele160/doom_first_frame`. It measures card presentation intervals,
not browser FPS. Three attempts stalled during WAD startup after 1,301,
4,809 and 79 native-oracle-matching requests and yielded no FPS. Do not report the 123.54 s
first-frame startup as FPS or transfer latency. See that subproject's README
and `artifacts/current/accele160-doom-fps-20261017/README.md` before another
card test. The first successful measurement is an unchanged-engine baseline;
`--fast-render --fast-columns`, direct frame and no play-mode FNV still need
a separate exact new-card build and matched test. Keep quality reductions off.

Later same-day correction: four fresh diagnostic runs localized the variable
startup stall to same-owner timer ISR reentry inside RTEMS dispatch. The
counted no-dispatch reentry path passed one 32-frame card run with 5,045 WAD
reads, exact 5,043-request native startup prefix, full pre-run paired flash
audits, bank/arena/STOP checks and **3.660 card-side FPS**. The owner fault
stayed zero; 10 reentries were counted over 14,899 ticks. Post-reset full
reads after the first run and a second unchanged-image 32-frame run passed:
both measured the same 847 ticks across 31 intervals, or 3.660 card-side FPS,
with identical pixel and palette hashes. The final post-second-run pair also
passed on a fresh boot, matching unchanged stock firmware. The new card has no browser
stream, keyboard bridge, or ping-pong DMA yet; old-card play binaries and
6+ FPS results are not directly interchangeable. See
`artifacts/current/accele160-doom-startup-20261017/README.md` and its replay.

The separate `rtems/accele160/doom_play` two-slot transport now has a physical
32-frame acceptance with paired full pre/post flash reads and offline replay:
`artifacts/current/accele160-doom-live-20261017/README.md`. PIATVR sees only
odd 4 KiB pages in 8 KiB pairs, so a direct host read of contiguous frame RAM
is invalid even if the first pixels appear plausible. Keep 16 odd-page chunks
per frame, full 64 KiB FNV before exact-generation ACK, bounded host-stall
timeout, full owner/bank/arena/STOP audits, and reboot-only release. That gate
measured 2.329 card-side FPS, not delivered or painted FPS. The HTTP/binary
frame and key endpoint now has a separate 32-frame physical run: all HTTP
payloads match card captures and W press/release reached stage 101 with
sequence/ACK two. Full runtime audits and paired pre/post flash reads passed
with stock SHA and zero residual/guard changes; `verify_browser.py` accepts
the bounded physical input/HTTP gate. Its 2.320 FPS is card-side presentation,
not delivered browser paint. DMA delivery, clean user STOP and a long
interactive owner are not yet accepted.

**Measured old/new delays (2026-10-17):** See
`artifacts/current/card-delay-comparison-20261017/README.md` and its replay
scripts before optimizing the new path. Its 429.03 ms frame interval contains
51.94 ms extra copy, 78.39 ms odd-page staging, 24.19 ms card FNV, and 274.52
ms combined engine work; that last field is not isolated renderer CPU.
Host PCI reads/FNV take 9.28/19.58 ms and observation-to-HTTP 29.38 ms.
Exact native host FNV microbenchmarked at 0.0874 ms, but is not integrated.
Fresh old low-detail/optimized/DMA windows give 6.35–6.40 FPS and 5.18 ms
HTTP latency; the inclusive scripted-reload interval gives 5.462 FPS.
Do not report the old/new FPS ratio as hardware speed: new is high detail
with older core routines. Both runs passed full replay/audits, all accepted
pixels/palettes, and final paired new-card stock-flash reads. No defaults or
firmware changed. Next preserve validation while making host FNV native,
then word copies and owned DMA/direct presentation. Full-quality matched
engine comparison remains open; half-height stays on hold.
