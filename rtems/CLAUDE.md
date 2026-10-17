# RTEMS working guidance

**2026-10-17 AcceleRAID 160 two-task resident lease:**
[Source](accele160/residentworkers/README.md) and
[accepted captures](../artifacts/current/accele160-residentworkers-20261017/README.md)
prove a separate worker runs after firmware operation 13 returns and suspends
before its supervisor shuts down RTEMS. Two HALT/expiry batches passed at
ticks 22/300, including wrong-token rejection, 2/280 worker timer IRQs,
six full flash reads, three stock inventories and full RAM/ISR/owner drain.
The worker disables RTEMS task preemption while it runs; timer interrupts
continue. A sleep-based predecessor hung ACTIVE and required a recovery
boot, so do not reintroduce an unqualified idle-thread handoff. No DMA is
owned, and masked interrupts or corrupt scheduling can defeat the deadline.
Next prove an explicit host-buffer/DMA owner, finite completion or timeout,
and complete STOP/expiry drain before reusing the grant.

**2026-10-17 AcceleRAID 160 post-return RTEMS task gate:**
[Source](accele160/residenttask/README.md) and [exact captures](../artifacts/current/accele160-residenttask-20261017/README.md)
prove one RTEMS task can run after operation-13 returns, using two separate
owned ISR continuations and a finite timer-1 lease. Two HALT/expiry batches
passed at ticks 22/300, with task progress and 2/280 task IRQs, stale STOP,
six full flash reads and three stock inventories. Whole-instance shutdown
returns to the retained firmware ISR for exact timer/vector/priority restore.
The RTEMS task context remains in the owned workspace after shutdown but is
never resumed; release only after the ISR and timer are quiet. This does not
yet own DMA or provide independent recovery for masked interrupts. Next
prove all task/ISR/DMA paths drained before network or Doom uses this card.


**2026-10-17 AcceleRAID 160 post-return RTEMS timer gate:**
[Exact source](accele160/residentclock/README.md) and
[live evidence](../artifacts/current/accele160-residentclock-20261017/README.md)
prove an RTEMS one-shot callback at hardware tick 20 after operation 13
returned and after host ENTER in a stock-firmware frame. HALT at tick 21 and
finite expiry at tick 300 restored timer/vector/priority, page, stage and all
owner records; four full flash reads and stock inventories matched. This is
**not a resident RTEMS task**. Do not schedule arbitrary work from the ISR
or release the grant while any task/ISR/DMA continuation could remain. Next
establish an owned post-return task context and exact quiescence boundary.


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
Evidence and reproduction: `artifacts/notes/render-20261015.md` and
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
`artifacts/notes/release-priority-20261015.md`.
<!-- /release-priority-current -->

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
Evidence, exact binaries, ABI and replay: `artifacts/notes/bulk-capture-20261015.md`.
Public IPv6 HTTP restored: 200 / 2890 bytes; boot
`27cc6b32-2d2f-4701-ba88-1c6d34484a42`, relay 1555 / supervisor 1552 owns
`dac960auto`. Doom 8087 closed. Historical PIDs below are stale; inspect actual
ownership before use.
<!-- /bulk-capture-current -->


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
59.9 ms-gap warning below. See `artifacts/notes/irq-drain-20261015.md` for exact
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
original scheduling. See `artifacts/notes/peer-yield-20261015.md` and
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
Evidence: `artifacts/notes/screen-copy-20261015.md`. One matched run, not a
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
rejections pass. See `artifacts/notes/wad-copy-20261015.md` for exact binaries,
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
Evidence/manual: `artifacts/notes/wad-profile-20261015.md`. Exact sources,
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


<!-- doom-pingpong-current -->
**2026-10-15 Doom ping-pong DMA bounded acceptance passed:** task-owned DMA1
handoff drains outstanding framebuffer DMA before publishing a WAD request.
Controlled low-detail Doom **3.503 → 3.887 FPS (+10.96%)**; host transfer/capture
**212.5 → 41.3 ms**, previous-publication wait **81 → 0 ms**. Renderer ~207.6 ms
plus retained screen copy ~44.1 ms now dominate. Estimated card start→host
observation **17–44 ms**, start→validated capture/release **64–92 ms**; these are
not pure DMA or input-to-display latency. Third host buffer estimated ~0–2%
steady benefit in this scene, possible jitter smoothing and +one frame of latency;
not implemented or benchmarked. Keep two buffers.
Controlled 100-frame run: **108 full audit pairs**, four exact DMA/mailbox pairs,
all 100 HTTP payloads exact, both-slot 3-second stall/resume, automatic level
restart with 55 additional WAD DMA reads, held frames 99/100 across STOP, global
drain. First 52 frames retain exactly four known native pixel differences and
matching palettes. Linux/Mac replay and 24 evidence mutations pass. Earlier
52-frame run has 104 audit pairs and browser input; its FPS is not a controlled
comparison. Both have zero active-frame full-snapshot counter: no new physical
overlap claim beyond the earlier v10 synthetic acceptance/native tests.
Kernel helper moved into existing protected engine code; 145 protected pages,
304-byte mutable reserve; no guard/RAM boundary or flash change. Doom is now
admitted only through explicit `--pingpong`; runner currently requires bounded
`--pipeline --pipeline-test --wad-dma`, optional `--wad-load-test` for 100 frames.
Keyboard input is disabled for bounded measurement; ordinary play defaults stay
unchanged. See `artifacts/doom-pingpong-20261015/README.md`, exact archives and
`game/doom/play/PLAY.md`. Tests ended, exact archives saved and replayed locally;
normal reboot released retained mappings. Public IPv6 HTTP is restored and
verified 200 from the Mac. Boot `a7e3490e-127d-4a0c-9f62-bb9466b03d05`, supervisor
4012 / relay 4014 owns `dac960auto`; see `restoration.json`. Inspect actual owner
before new hardware work; stop this relay normally. Never force-unload.
Older service/PID and Doom-excluded notes below are historical.
<!-- /doom-pingpong-current -->


<!-- dma-pingpong-current -->
**2026-10-15 card-initiated ping-pong DMA accepted (v10):** two persistent host
buffers, task-owned payload/completion chains, explicit generation release.
Synthetic producer **7.921 → 14.242 FPS (+79.80%)**, with 256 delivered + 2 held
frames, **20 full audit pairs**, five full mailbox comparisons, two 3-second host
stalls, resumed delivery, owned STOP and global drain. Linux/Mac full replay and
24 evidence mutations pass. Five full system snapshots validated active owned
DMA leases. Card start→host observation estimated mean **8–30 ms**; full validated
capture/release **62–83 ms**. These are not Doom/browser FPS or pure DMA latency.
The final host queries unrelated Upload completion once/second, immediately on
STOP. Ownership checks, full captures, guards and audits remain. Native tests
cover active-transfer STOP, hardware timeout quarantine and the stalled wait bound.
The protected table covers 145 pages; offline capacity check and per-page mutation
tests pass; kernel tail 304 bytes. The faster v9 attempt exposed a snapshot path
that did not recognize owned DMA. V10 validates the exact lease before changing
only its local report; foreign DMA and descriptor corruption remain errors.
All earlier failures are preserved, including v9 whose frame/STOP pass is not full
system acceptance. See `artifacts/notes/dma-pingpong-20261015.md` and
`rtems/dma/pingpong/README.md`. Doom remains excluded from admission: WAD and
frame traffic share DMA1 and need explicit coordination, followed by browser,
input/disconnect and pixel/palette acceptance. No flash change or RAM remap.
Final archives are local and replayed; normal reboot released the test module.
Public IPv6 HTTP is restored and verified 200 from the Mac. Current boot
`2225b1d9-c77e-4cb6-900e-9841154cd719`, supervisor 2569 / relay 2571 owns
`dac960auto`. See `restoration.json`; inspect actual owner before card work and
stop this relay normally. Never force-unload retained mappings.
Older ownership/service notes below are historical.
<!-- /dma-pingpong-current -->


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
`artifacts/notes/doom-detail-20261014.md`. Test closed and local replay passed;
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
passes. See `artifacts/notes/doom-present-20261014.md` and
`game/doom/play/PRESENTATION.md`. Test owner closed and evidence verified before normal reboot. SSH has not
returned; user power-cycle requested. Public HTTP restoration pending; see
`artifacts/doom-present-20261014/restoration.json` and `restore.sh`. Never
force-unload retained exclusive mappings.
<!-- /doom-present-current -->

<!-- wad-dma-current -->
**2026-10-14 bulk WAD DMA accepted:** `--pipeline --no-crc --wad-dma` uses
4096-byte host-to-card DMA without WAD/frame payload CRC, retaining ownership,
guards, hardware completion and all full audits. First level: **1642.751 →
318.183 s (5.163×)**; warm same-level restart: **10.291 → 3.068 s (3.354×)**.
52 frames match mailbox exactly; 14 full audit pairs, owned STOP and heap drain
pass. Full system/frame/WAD replay passes on Linux and Mac. Known native pixel
differences remain. Legacy CRC mailbox stays default; image admission is unchanged.
Evidence: `artifacts/notes/wad-dma-20261014.md`; manual: `game/doom/play/PLAY.md`.
The failed pre-WAD startup TCP attempt is preserved. Host now finishes network
proof before large game upload, retaining checks/deadlines/audits. Metadata queries
still cost 181.255 s. No arbitrary in-bounds corruption detection without CRC.
Remote workspace `/home/mit/i960-wad-dma-20261014`; interactive `play` on port 8087, supervisor 1469,
boot `5e6b2f6d-b685-486e-97cc-ca33dcc4e6b4`, live and browser keyboard verified. Do not force-unload retained resources or start another owner.
<!-- /wad-dma-current -->


<!-- doom-pipeline-current -->
**Two-buffer Doom/binary pipeline accepted (2026-10-14):** CRC-on **1.396095 FPS**,
CRC-off **2.070201 FPS (+48.285%)** in 52-frame on/off/off/on testing. All **29
full monitor/RAM pairs**, four exact mailbox/DMA pairs, owned STOP and global
heap drain pass. Linux/macOS replay rejects 35 frame/journal and 24 snapshot
mutations. All 52 binary HTTP packets match; native comparisons retain seven
pixel differences per frame with identical palettes/padding. This is delivery
FPS, not paint FPS or a 3–5× gain. Earlier single-buffer results used different
inputs, so do not attribute their difference solely to buffering or binary HTTP.
Build/run opt-in `--pipeline`; CRC remains on unless `--no-crc` is explicit.
Never remove ownership, generation, bounds, guards or hardware quiescence checks.
The initial run exposed WAD starvation during pending DMA; the host now services
WAD requests during polling. A separate TCP startup failure exposed executor
shutdown suspending audits; failures now request owned STOP while keeping the
control loop active. Both incomplete attempts are preserved, not accepted.
Evidence: `artifacts/notes/doom-pipeline-20261014.md`. Longer interactive and
disconnect acceptance remains future work. No firmware or RAM remap change.
All test ownership is released after archive verification/replay and reboot.
Public IPv6 HTTP returned 200. Current owner: relay supervisor **2796**, Python
**2798**, boot `d18b781d-a8e7-4604-b8fc-4a048e18506e`, bound `dac960auto`.
Stop that relay normally before new tests; never force-unload retained resources.
Ownership records below are historical, not current reservations.
<!-- /doom-pipeline-current -->

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
`artifacts/notes/doom-dma-cleanup-20261014.md`.
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
[Evidence and limits](../artifacts/notes/doom-dma-20261014.md).
<!-- /doom-dma-current -->

<!-- exclusive-dma-current -->
**Task-owned asynchronous DMA accepted (2026-10-14):** worker 1 now prepares,
launches and checks DMA1 with interrupts enabled; the MU handler only publishes
jobs and reads status. Host submit/poll calls release the session mutex between
commands. Two physical runs passed **48 exact transfers, 124 full monitor/RAM
pairs, 108 malformed/stale refusals and two canceled 64 KiB jobs**. Explicit
STOP acknowledged in **1.258 ms**; the independent 3,000-tick session deadline
also canceled before launch. Every canceled destination byte remained unchanged.
Maximum IRQ gaps are **10.710 / 10.990 ms**, versus **111.481 ms** synchronously
(90.1–90.4% smaller). All application allocations and shared handles retire.
Full system, DMA and cancellation replays pass on Linux and macOS; current
checks reject 24 DMA mutations, 42 cancellation mutations and 24 snapshot
mutations per applicable capture. The 73,728-byte coherent mapping stays pinned
until reboot. No forced unload, flash change, ATU remap or weakened audit.
This is still opt-in `--dma-proof`, **not Doom DMA/FPS acceptance**. Diagnostic
job wall time increases because source fill/check share CPU time; the measured
benefit is interrupt responsiveness. A physically stuck DMA engine/abort is not
claimed: native tests cover polling exhaustion/error/retention, while hardware
covers explicit STOP and RTEMS session timeout. Next: same-frame DMA/mailbox
comparison with a pinned Doom frame, then measured browser FPS and lifetime work.
Both archives are locally hash-verified and replayed; the public IPv6 page
returned HTTP 200 after reboot. Relay Python 2721 (supervisor 2717), boot
`33cafc40-6142-46dd-9c79-0156c77f2e4e`, owns the card. Test reservation released;
stop the relay normally before new hardware work. The archived physical modules
precede a native-tested logging-only diagnostic follow-up in the current host.
[Evidence, exact binaries and limits](../artifacts/notes/dma-async-20261014.md).
<!-- /exclusive-dma-current -->

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
[Exact results, sources, binaries and reproduction](../artifacts/notes/doom-bulk-20261014.md).
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
statements below are historical. See [current evidence and guide](../artifacts/notes/doom-play-20261013.md).
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
[Exact sources, binaries, captures, browser instructions and limits](../artifacts/notes/doom-visible-20261013.md).
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
[Exact sources, binaries, captures, failure reproductions and results](../artifacts/notes/doom-shutdown-20261013.md).

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
cleanly and coordinate before future exclusive work. [Evidence](../artifacts/notes/doom-height-20261013.md).


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
[Evidence and reproduction](../artifacts/notes/doom-checkpoints-20261013.md).


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
[Evidence and current status](../artifacts/notes/doom-startup-20261013.md).


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
[Evidence, reproduction and limits](../artifacts/notes/doom-batch-20261012.md). Next is N3: bind batching
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
[Accepted evidence and replay instructions](../artifacts/doom-progress-20261012/README.md).


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
[Runtime contract](../game/doom/runtime/platform/README.md) ·
[Physical evidence](../artifacts/notes/doom-platform-20261012.md).

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
[Contract](../game/doom/runtime/relocate/README.md) ·
[Evidence](../artifacts/notes/doom-relocate-20261012.md).

**New host-only cache/link checkpoint:** [../game/doom/runtime/cache/README.md](../game/doom/runtime/cache/README.md) and
[../game/doom/runtime/relocate/README.md](../game/doom/runtime/relocate/README.md). Opt-in `--wad-cache` requires `--arena-runtime`.
Only the separately allocated bounce base crosses runtime reads; zone interior
pointers stay in the owning application. Single IWAD, no rebind or reopen after
close; no general stdio/filesystem shim. Six host demos match 12,600 hashes with
1 MiB reserved image + at most 6,473,545 dynamic bytes in the 8 MiB arena.
44 engine imports remain. That REL checkpoint was host-only; the small proof is now accepted above.
Never bypass its closed card whitelist or infer relocation records from
pointer-looking words. Doom engine admission remains separate work.

**Runtime-entry/WAD bridge accepted:** [../game/doom/runtime/entry/README.md](../game/doom/runtime/entry/README.md).
`--doom-runtime` requires `--doom-shared`. Only the exact reviewed probe may
enter through the v1 table; this is not arbitrary Doom launch. WAD staging is
separate from UPL1, maximum 512 bytes, one immutable bound file. Copy in the
owning worker after claim/CRC; keep its allocation loan until completion or
cancellation. No cross-task destination pointer, ISR copy, or implicit unpin.
Keep the host WAD query/reply inside the reentrant audit gate, retain full
audits and the 500-tick timeout, and never retry uncertain writes. The live
normal/error/timeout/recovery batch passed; STOP-in-read is native-tested only.
No Doom engine has yet run on card. Next are imports/linking and a WAD cache.

**Shared arena follow-up accepted:** read [../game/doom/runtime/SHARED-ARENA.md](../game/doom/runtime/SHARED-ARENA.md).
Use one task mutex and private per-worker allocation records; retain pins during
unlocked bulk work and reclaim only after both task/IRQ drains. Wrong-task
calls must not write diagnostics. `--doom-shared` requires `--doom-heap`.
Both workers must not block at once: idle still deliberately faults and has no
registered IRQ owner. Keep a control worker runnable or explicitly admit/test
idle ownership. Preserve full audits, exclusive reboot-only release and the
cooperative public service. Earlier single-owner notes below are historical.


**Doom allocation adapter:** [../game/doom/runtime/README.md](../game/doom/runtime/README.md).
`--doom-heap` requires resident-upload, uses its single arena owner and protected
upper code section, and preserves system malloc. Physical 6 MiB calloc/resize
and retained-buffer STOP drain passed with six concurrent network rounds.
Do not generalize its worker-only gate to a multi-task lock.

**Resident integration accepted (2026-10-12):** [residentnet/UPLOAD.md](residentnet/UPLOAD.md).
Use the opt-in resident-upload profile for the new 8 MiB arena and PIO transport;
keep the baseline libc allocator and cooperative profiles. The initial upload
contains a separately linked upper code section which must remain outside BSS
and be verified before takeover. Decode manifest words explicitly: i960 C structs
have different padding. Preserve the whole-snapshot host gate during concurrent
uploads, sequence/epoch checks, pin retention, and reboot-only release. Exact
binaries, failed attempts and concurrent acceptance are linked in the contract.

**2026-10-12 allocator/segmented prototype:** [../loader/segmented/README.md](../loader/segmented/README.md) records native
6 MiB allocation tests and actual-card execution from a guarded 3,728-byte BIO
arena. This original small-arena rehearsal preceded the resident integration above.
Do not enlarge system malloc or
remove reserve patterns without the explicit RAM/placement/ownership gates.
Run `make -C loader test`; preserve generation/pin/quarantine semantics.

**12 MiB exclusive RAM checkpoint (2026-10-12):** `--owned-mib 12`
passed four startup patterns over `c0240000..c0e40000`, a 35-minute resident run,
48 dual-stack rounds and independent replay of 3,812 packets. RTEMS now initializes
after takeover, with a 256 KiB kernel workspace and three 64 KiB requested task
stacks (plus the idle slot). Both workers checked live 12 KiB stack objects;
a real 128 KiB workspace allocation survived the run, was fully checked and freed.
All 220,066 application allocations and 16,402 shared objects drained at tick
210,002, with both task IRQ contexts drained and two timer-counter carries.
The complete 11,993,024-byte reserve passed its final scan. Both workers now
service PIO; chunked shutdown scans keep control responsive. Observed word-ioctl
median/P95/max: 0.182/2.931/10.644 ms; draining maximum 1.845 ms versus the earlier
4.459-second blocked scan. These are workload observations, not latency bounds.
Maximum ISR gap was 11.038 ms: broader checks add cost, so this is not an IRQ-latency
improvement over the previous smaller profile. The application heap stays
171,824 bytes; the reserve is not yet a general allocator or executable grant.
The high protected-tail inventory and segmented loader remain gates before Doom.
Two incomplete 10 MiB sessions and their fixes are preserved. Cooperative profiles
remain available; no flash write. The post-run reboot returned; cooperative public IPv6 HTTP is restored and verified.
See [RAM contract](residentnet/LARGE-RAM.md), [captures](../artifacts/notes/rtems-large-ram-20261012.md), and [Doom OS plan](../game/doom/OS-PLAN.md).

**Fallback queue reclaimed; network work preemptible (2026-10-11):**
Opt-in `--queue-reclaim` requires the shared/general heap, validated extra RAM,
owned exceptions and secondary SCSI reset. After copying any startup packets
and irreversibly switching to the external queue, the old 102,000-byte object
becomes a guarded 101,872-byte second application arena. Total arena capacity
is 171,824 bytes; largest permitted request is 101,808 bytes, subject to free
contiguous space. Kernel workspace, task stacks, lwIP pools and upload size do
not grow. RX leases and unpublished TX buffers let lwIP/copy work run at priority
20, with only ownership transfers masked. Every 32nd shared cycle uses 80 KiB
in reclaimed storage. The forty-round, thirty-minute card run passed at tick
180,008: all 189,150 allocations and 14,138 shared objects drained, including both
IRQ contexts. Guard and metadata corruption each passed physical terminal
containment with live resources retained. Maximum observed ISR gap was 10.688 ms
(previous RNT7 endurance: 13.270 ms); 182 network-processing brackets spanned
interrupts. These are measured workloads, not worst-case guarantees. Full raw
packet replay, native regressions and offline tests passed. Failed host lookup
attempt and exact binaries are preserved. No flash write or new RAM range grant.
The post-test reboot returned; the cooperative public IPv6 RTEMS/Vader page
is restored and verified HTTP 200.
See [contract and evidence](residentnet/QUEUE-RECLAIM.md).

**Shared heap, latency and endurance (2026-10-11):** `--heap-shared` adds
explicit two-task references/pins and cancellation to the existing 69,952-byte
heap. Pinned or uncertain holders retain memory; no arbitrary task deletion or
automatic reclamation is authorized. Busy reservations let calloc/realloc copy
work restore the caller's interrupt priority. Measured protected maxima fell
from 14.804 ms to 0.261 ms for calloc and 11.064 ms to 1.985 ms for realloc; these
are observed sections, not whole-system bounds (maximum ISR gap: 13.270 ms).
The final card run passed forty dual-stack rounds, timer wrap and 180,008 ticks;
all 194,154 allocations and 14,764 shared objects drained, including both IRQ
contexts. Each large-memory path spanned interrupts in 180 calls. Native stress
passed 200,000 worker updates and a legitimate fragmentation refusal. A prior
HTTP endurance timeout exposed full packet-history rewrites on the host; an
append journal reduced recording from 188.43 to 0.200 ms in the matched benchmark
while preserving every byte and strict replay. Partial/failed attempts are kept.
No flash writes or new RAM grant. At this baseline the 102,000-byte internal
fallback queue remained reserved; the opt-in queue-reclamation follow-up reuses
it after external handoff. The baseline profile still reserves it.
Post-test reboot succeeded; cooperative public IPv6 HTTP is restored and verified.
That batch proposed fallback-queue reuse and less masked network work; the
queue-reclamation follow-up implements those. Broader task/resource ownership
and control-path latency remain future work. Read the
[contract, measurements and thirty-step evidence](residentnet/SHARED-HEAP.md).


**General application heap (2026-10-11):** `--general-heap` adds 69,952 bytes
at `c022ee80..c023ffc0` using RTEMS 4.6.6's real allocator. It requires
`--extra-ram --fault-owner --secondary-reset` and grants no additional RAM range.
The 128-slot packet queue remains intact; kernel workspace/task stacks stay in
the upload region. Allocation has a 64-live-block limit, exact-pointer checks,
redzones, bounded metadata validation and ISR refusal. Outer-guard, allocation
suffix, metadata-extent and saved-offset corruption each passed physical containment
tests with both live allocations retained; no forced unload or recovery resume.
The hardened non-injection image passed 36,000 ticks, ten spaced dual-stack
rounds, saturation/TCP loss recovery, and all 36,100 allocations freed before
both IRQ contexts drained. All six reboots returned normally; cooperative public
IPv6 HTTP is restored and checked. Do not enable `--heap-test` in production. See the
[heap contract and evidence](residentnet/GENERAL-HEAP.md).


**Exclusive exception/RAM follow-up (2026-10-11):** real constraint faults and
a real PCI doorbell NMI (vector 248) entered owned terminal handlers. The cached
NMI vector, all fault entries and interrupt stack are owned before SCSI reset.
A fixed 256 KiB range passed four patterns with protected-range checks; only
its guarded 192,000-byte packet queue is granted with `--extra-ram`. The
128-slot queue passed 24,000 ticks, six dual-stack rounds, saturation and TCP
loss recovery with IRQ contexts drained at the deadline. General
RAM reclamation remains disabled. The dedicated NMI ioctl exists only in a
module pinned to `--fault-test 3`; do not put it in production. All exclusive
resources remain retained until reboot. The final reboot succeeded and public
IPv6 HTTP is restored and checked. Preserve cooperative profiles and check
the live card owner before experimenting. [Contract and evidence](residentnet/FAULT-OWNERSHIP.md).


**SCSI stop boundary (2026-10-11):** the identified secondary Symbios 53C895
remained in bus reset for 36,000 ticks and ten spaced concurrent IPv4/IPv6
rounds, including saturation, TCP loss recovery and autonomous task shutdown.
This is forced stop/discard, not graceful SCSI drain or a disk flush. The opt-in
`--secondary-reset` build retains reset and resources until reboot; never force
unload it. Default/cooperative profiles remain available. Useful resident queue
storage is now 72 × 1,500 bytes inside the existing 512 KiB grant. **No broader
RAM grant:** stock cached NMI and fault paths remain; the NMI handler can
reinitialize the secondary interface. The candidate RAM-transfer policy is
offline only. The final reboot returned normally; public IPv6 HTTP is restored
and checked from the Mac. Follow the [contract and evidence](residentnet/SCSI-STOP.md) before further tests.


**Resident decode follow-up:** live board selector 6 and dispatch `c000d540`
qualify synchronous CPU XOR / internal DRAM, not the alternate external-cache
bit-0 completion path. Firmware reports 16 MiB. Resident networking now has
32 TX slots inside the original grant; three IPv4/IPv6 rounds and 12,000 ticks
passed. No outside RAM grant or all-engine drain is claimed. Preserve cooperative
profiles, never force-unload retained resident resources, and check the current
remote owner before testing. [Findings, thirty steps and remaining gates](residentnet/DECODE-BATCH.md).


**Exclusive RTEMS track (2026-10-11):** the user explicitly permits RAID/SCSI
shutdown during RTEMS and reboot/power-cycle to exit. `exclusive` now runs real
preemptible RTEMS after the ARM callback returns, with inactive i960 DMA disabled,
primary/secondary bus mastering denied and external secondary grants disabled.
Nine bounded sessions restored/unloaded; resident deadline/STOP runs parked at
1,200/581 ticks with all task IRQs drained and resources retained. The first
reboot needed user intervention; unattended recovery remains unproven.
This is tested CPU/bus isolation within the existing allocation, not proof of
cache-coprocessor drain or arbitrary RAM ownership. **Keep the cooperative
RTEMS + stock-firmware path and all its profiles/evidence as a future option.**
[Exclusive contract and remaining gates](exclusive/README.md),
[30-iteration ledger](exclusive/BATCH.md). Production remains `autonet`.


**Callback-free monitor milestone (2026-10-11):** `handoff` passed five final
sessions: 20 bounded entries from the timer ISR after the ARM firmware callback
returned, five omitted-RELEASE expiries and ten denied DMA/SCSI transfer
requests. Every final close restored RAM and unloaded. The initial token-repeat
failure required recovery; a second build exposed an i960 compiler condition-code
bug in the diagnostic policy. Both failures and corrections are preserved.
Stock firmware uses DMA0/1; idle registers do not grant ownership. This is a bare
monitor prerequisite, not callback-free RTEMS scheduling or permanent takeover.
Production IPv6 HTTP is restored. [Contract and next gates](handoff/README.md),
[16-step batch](handoff/BATCH.md).


**Continuous execution lease (2026-10-11):** `leaseirq` now keeps preemptible
RTEMS workers running continuously inside a parked firmware callback. Sideband
grant/renew/STOP, a 512-tick renewal deadline, a non-renewable 24,000-tick cap and
per-tick timer/vector/mask/MU checks make the execution lease explicit. Nine
sessions passed 23 callbacks and 13 leases, including 60 seconds of renewed
execution, 115 seconds to the cap, expiry and transitive quarantine. All 40,111
hardware checks reported no drift; all closes restored RAM and unloaded.
Native tests, 1,610 actual-report mutations and production IPv6 HTTP passed.
[Contract, ownership table and evidence](leaseirq/README.md). Firmware stays parked; DMA/SCSI
ownership and unrestricted coexistence are not established. Production remains
autonet. Earlier next-step descriptions below are historical.


**Persistent asynchronous epochs (2026-10-11):** `persistirq` preserves one
RTEMS instance across host calls and tracks a transitive two-mutex dependency
chain A/B/C. Five normal sessions passed 120 callbacks, 29 clean rollback/handoffs
and 46 follow epochs with the quarantined chain unchanged while Other ran.
An intentional six-callback early-close session retained resources despite a
completed QUIESCED handshake. Replay verified 126 reports and rejected 5,922
mutations; the full native suite passed. The retained-close reboot recovered;
a fresh 18-callback session passed and production IPv6 HTTP returned 200.
[Contract and evidence](persistirq/README.md). RTEMS interrupts run inside bounded epochs and are
restored between callbacks; this is not free-running firmware coexistence.
Keep production on autonet. Earlier next-step descriptions are historical.


**Asynchronous ownership integration (2026-10-11):** the separate `ownirq`
profile now combines a real shared mutex, blocked waiter and software lease with
task-owned IRQ stacks and concurrent host STOP. Nested critical sections defer
controller execution until outer release; clean cancellation drains the owner's
IRQ frame, waits for its lease, rolls back and hands the lock to the waiter.
Quarantine preserves owner/waiter dependencies while an unrelated preempted task
continues. A valid QUIESCED/completed callback with an outstanding lease returns
ENODATA and retains resources with pending=0. The first run exposed i960 struct
padding in report serialization; it was archived, corrected and retested.
Ten asynchronous sessions passed full RAM/MU restoration; both retained cases
recovered by reboot. The persistent serialization fix passed 48 more callbacks.
Native/replay checks passed, and production IPv6 HTTP returned 200.
[Contract, matrix and evidence](ownirq/README.md). These remain bounded one-shot experiments,
not unrestricted resident execution or physical DMA cancellation. Keep production
on autonet. Earlier next-step statements below are historical.


**Resident ownership batch (2026-10-11):** the separate persistent `ownership`
profile passed a 48-callback smoke run and three 371-callback sessions: real
priority-inheritance mutex, owner-only release, blocked waiter, cancellation
rollback, software-reference deferral, stale/duplicate completion rejection,
clean owner restart with new epochs, and owner/waiter quarantine while an
unrelated worker continues. These are bounded persistent callbacks, not the
asynchronous IRQ profile. A premature final close retained dirty state, DMA,
BAR and module with pending=0 and refused ordinary unload. After reboot, a
further 48-callback run passed full restoration; production IPv6 HTTP returned
200. Total: 1,209 normally completed callbacks, 62 rollback/handoffs and five
normal closes, plus the three-callback retained-close test. No flash writes.
[Contract, evidence and next integration gate](ownership/README.md). Earlier next-step
statements below are historical. Do not force-unlock a quarantined resource,
delete its tasks, reuse its stacks, or treat a software lease as a DMA drain.


**Automatic containment batch (2026-10-11):** six final critical-section
sessions passed (three per depth), following six initial passes. STOP at ticks
18/30 deferred controller execution until outer release at tick 40; external
suspension completed at tick 44. The final module removes a stack-frame warning.
Three separate failure tests retained resources: omitted STOP/final close,
omitted RELEASE/unbind, and invalid local report after real callback completion.
The last case returned ENODATA and retained dirty state with pending=0, proving
retention does not depend solely on an outstanding command. All refused unload;
evidence was saved before each reboot. All three reboots and final fresh
preflight passed; production IPv6 HTTP is restored. [Results and next gate](switch/CONTAINMENT-BATCH.md).
General resident task cancellation, permanent interrupt masks and DMA ownership
remain unproven; keep production on bounded autonet.

**STOP-ignoring worker containment (2026-10-11):** three live `contain`
sessions passed. Both workers continued four ticks after STOP, then the
controller externally suspended them, restored the timer and returned. Each
worker retained one live ISR continuation; task/ISR stacks were kept intact
until callback return, with 10,000 stable checks. The distinct QUIESCED token
and exact-image-pinned host gate prevent confusing suspension with draining.
Full RAM/MU restoration and unload passed each time; HTTP restored, no reboot
or flash. [Contract, results and limits](switch/CONTAINMENT.md).
This disposes of a bounded one-shot RTEMS instance; permanent interrupt masking,
scheduler corruption and resource-safe cancellation in a resident OS remain
unproven. Next: bounded critical-section containment and failure-path coverage.

**Failed-control teardown checkpoint (2026-10-11):** both live injection cases
passed: omitted STOP during final-user-fd close, and omitted RELEASE during
unbind. Both syscalls returned ETIMEDOUT; pending/dirty state, DMA/BAR and module
references remained retained. No post-failure firmware commands or cleanup/free
occurred; ordinary unload was refused. Completion became visible but was not
consumed after the control error. These are synthetic omissions on a responsive
card, not physical PCI faults. Evidence was saved before each recovery reboot.
Both reboots completed; fresh preflight passed and IPv6 HTTP returned 200.
[Contract, findings and reproduction](switch/FAILED-TEARDOWN.md).
Next: non-cooperative task containment; production stays on bounded autonet.

**Final-close / driver-unbind checkpoint (2026-10-11):** six final hardware
runs passed: three closes of the sole user descriptor and three sysfs unbinds
while callback/control syscalls were active. Release/removal waited for the
operations; restoration preceded BAR unmapping, and late calls were refused.
All target contexts and full RAM/MU cleanup passed; HTTP restored, no reboot/flash.
An initial truncated removal log was preserved and its publication fixed before
rerunning. [Contract and findings](switch/LIFECYCLE.md),
[evidence](../artifacts/notes/irq-lifecycle-20261011.md).
Logical unbind is tested; the later failed-control checkpoint above covers
synthetic omissions during teardown. Physical hot-unplug remains unproven. Task shutdown still cooperates with a stop flag.


**Concurrent host control (2026-10-11):** three card runs passed with STOP
issued by an ioctl on a second host thread while the firmware callback was
pending. A separate control mutex/window is joined before completion/cleanup;
wrong epochs, duplicate STOP and late requests were refused. Both ISR contexts
drained; full RAM/MU restoration and unload passed. IPv6 HTTP restored.
[API and lifetime contract](switch/CONCURRENT.md),
[evidence](../artifacts/notes/irq-concurrent-control-20261011.md).
Workers remain stop-aware. Live alias-close coverage is not final-close or
physical-removal fault injection; next are broader lifecycle failure tests and
non-cooperative task containment.


**Live web system information (2026-10-11):** the IPv6 Vader page now shows
card runtime uptime, RTEMS/lwIP and CPU details, memory capacities, HTTP counts
and RX/TX/drop counters. CPU utilization and temperature are explicitly
unavailable; measured timer-bus frequency is not labelled as CPU frequency.
24 live HTTP checks and full cleanup/restart passed. Production module is now
`autonet-module-system-info`, paired with the updated `autonet` image.
[Details](net/SYSTEM-INFO.md), [artifacts](../artifacts/notes/rtems-system-info-20261011.md).


**Nested STOP and timeout checkpoint (2026-10-11):** all twelve `stopcases`
card runs passed. STOP at critical depths 2/1 was recorded at ticks 18/30 but
controller dispatch/drain waited until outer release at tick 40. Missing STOP
reached the 128-tick event deadline; missing RELEASE exhausted its finite loop
and returned with only the expected `0x4000` flag. All contexts, guards, paired
RAM/MU restoration and unload checks passed; no reboot/flash. IPv6 HTTP restored.
[Implementation](switch/STOP-CASES.md),
[evidence](../artifacts/notes/irq-stop-cases-20261011.md).
Next: concurrent user-control/lifetime design and non-cooperative task containment.
These workers remain stop-aware; deliberate message omission is not a full host
crash or proof of recovery from permanently masked interrupts.


**Pending-callback MU STOP milestone (2026-10-11):** three `mustop` card runs
accepted a one-shot host STOP at ticks 34/41/52 while both owned ISR contexts
were live and firmware sequence 1 was still pending. Workers observed the stop
flag, both contexts drained, and the card acknowledged before host RELEASE
allowed the callback to return. Zero faults; full RAM/MU restoration and module
unload passed. IPv6 Vader HTTP restored. [Evidence](../artifacts/notes/irq-mu-stop-20261011.md).
This is a serialized host-driver experiment, not a concurrent control ioctl,
CTL1 framing, or forced termination of code that ignores the stop flag. Next:
exercise STOP during nested dispatch deferral and the missing-host deadline;
then generalize the control API and non-cooperative task containment.


**Nested dispatch-deferral milestone (2026-10-11):** three `defer` card runs
kept task A executing through four timer ticks at dispatch depth 2 and four at
depth 1. All eight IRQs observed a pending switch to a different heir; task B
started only after the outer enable. A resumed at tick 9, depth 0. Each run
finished at tick 32 with zero faults, 20/20 and 12/12 ISR entries/returns,
verified RAM restoration and module unload. IPv6 Vader HTTP returned 200 after
restart. [Evidence](../artifacts/notes/irq-deferral-20261011.md).
Next: integrate independent MU STOP with the two CPU-bound task contexts and
prove safe draining during an active callback. Resident operation and general
interrupt nesting remain unproven; production stays on `autonet`.


**Two-task interrupt-switch milestone (2026-10-11):** three bounded card runs
passed timer-driven switching between CPU-bound RTEMS tasks. Each run recorded
32 IRQ-path handoffs, 31 observations of both ISR continuations live, and 16
entries/returns per task. Separate task/ISR stacks, register sentinels, frame
ownership, draining and full restoration passed; web service restored without
reboot/flash. [Implementation](switch/README.md),
[evidence](../artifacts/notes/irq-switch-20261011.md). This is bounded preemption,
not a resident monitor; next are deferred-dispatch stress and MU STOP integration
while the CPU-bound task contexts are active.

**Owned ISR stack milestone (2026-10-11):** an owned, guarded C interrupt stack
and explicit GPR/TC preservation passed 126 isolated stress interrupts and 546
bounded RTEMS/control interrupts. Deep call chains, sentinels, PC/TC roundtrips,
frame/guard checks and independent STOP/HALT passed; full cleanup and web restart
passed without reboot/flash. The hardware entry frame stays in place: movable
per-task interrupt contexts and unrestricted preemption remain future work.
[Implementation](interrupt/README.md),
[evidence](../artifacts/notes/owned-interrupt-stack-20261011.md).

**Current development roadmap:** [loader memory extension, RTEMS and remaining gaps](../docs/rtems/DEVELOPMENT-PLAN.md). Next: M1, generalize the proven larger RAM profile; preserve scalar/BIO1 compatibility.


Read [README.md](README.md) and the dated artifact report before changing this
port. It already runs real RTEMS Classic tasks and lwIP on the i960RP, with
card-originated DNS/TCP/HTTP through the Linux host.

Preserve the cooperative contract: firmware owns its interrupt vectors/timers,
RTEMS stays at priority 31 during each bounded call, and the outer entry restores
firmware priority. The host supplies elapsed time. A standalone/preemptive BSP
or independent mailbox transport has not been validated.

Only the known staging allocation is borrowed. Keep RIO1 workspace limits,
immutable guards, paired readbacks, sequence/no-retry rules, failure pinning,
exclusive ownership and full close restoration. Do not alter Tetris's BIO1
layout to fit RTEMS. Do not force-unload a pending/uncertain module.

The old RTEMS BSP's interrupt/clock code contains board assumptions and defects;
never enable it just because it compiles. Current Newlib use is headers plus a
small freestanding runtime, and lwIP uses the raw API from one RTEMS task.

`make -C rtems test` is offline. `deploy.py` builds in a new remote directory and
does not touch hardware. `transport/relay.py` is an explicit live test which may
also change routing when `--internet` is provided; it saves a cleanup journal.
Use fresh output directories and retain exact target/module/source hashes.
Artifact source snapshots are historical evidence and must not be modernized.

## IPv6 milestone (2026-10-11)

The current net target is dual-stack. See [usage](README.md#ipv6-usage-and-scope)
and [evidence](../artifacts/rtems-ipv6-20261011/README.md). Installed launcher:
`/home/mit/i960-rtems-ipv6-20261011/serve.sh --ipv6`; `--internet6` enables NAT66
and IPv4 DNS routing. Raw IP input is operation 1; operation 5 selects AAAA/IPv6
HTTP, while operation 2 remains IPv4. Static ULA, MTU 1500, no fragmentation,
SLAAC or autonomous polling. Keep shared `lwip_patches.py` DNS packing and
mandatory IPv6 UDP checksum adaptation in native and target builds. Preserve
IPv6 forwarding/accept_ra journal rollback and verify both IP families.

## Web and hardware-interrupt checkpoint

See [current report](../artifacts/rtems-web-autonomous-20261011/README.md).
The `net` profile serves bounded HTTP on port 80. `--publish-http6 <host-global>`
with `--internet6` explicitly publishes it through DNAT (default port 8080).
Only four clients and 512-byte headers are supported.

The separate `irq` profile proved eight hardware interrupts/eight RTEMS task
wakeups and restored timer/vector/mask state. `auto` and `autonet` now pass
host-silent progression tests (20 and five seconds respectively). Use only the
exact image-pinned `dac960auto` transport from `autonomous/build_transport.py`
(`--network` for autonet: STOP operation 6; auto uses STOP 2). Kernel release
verifies STOP before RAM restoration, including SIGKILL and a completed
application error. Live cleanup passed for both signals and invalid operation.
Never load an autonomous image with the cooperative transport. Retain stock
interrupt sources, preserve timer 0, and keep IRQ work bounded. This does not
establish nested IRQ support, unrestricted preemption or independent transport.

The host relay also supports persistent HTTP visitor accounting via `--visitor-log`.
The deployed autonomous launcher enables it. See [visitor logging](transport/VISITORS.md)
for paths, counting semantics and tests. Keep real visitor databases/statistics
on the host, out of Git; no firmware rebuild is needed for this feature.

## Preemption and DMA roadmap (2026-10-11)

See the [staged preemption and DMA plan](../docs/rtems/RTEMS-PREEMPTION-DMA-PLAN.md). Order: independent control
and ownership prerequisites → arbitrary application-task preemption → host-RAM
DMA networking → gated direct peer experiments. Read-only direct-DMA research
has started; current NIC and Mylex occupy separate PCI branches. This is a plan
and initial inventory, not implemented preemption or verified peer DMA. Keep
the active web service on the existing bounded runtime.

## P0/P1 audit and prototype checkpoint (2026-10-11)

The [interrupt audit](control/INTERRUPT-AUDIT.md) is written. The
[control protocol prototype](control/README.md) passes native tests
and a two-process shared-memory demo, and cross-compiles for i960. Read-only
PCI configuration confirms PIATVR=C0000000 and the existing 8 KiB window.
No live independent control writes are enabled: the MU overlay/index interrupt
side effects and stock mailbox/stack ownership still require a proven reservation.
This completes the offline prototype, not P1 physical validation or preemption.

## Control ownership follow-up (2026-10-11)

The [matching-firmware ownership trace](control/OWNERSHIP.md) identifies active handler/fault
data and mailbox/interrupt-stack uses in the BAR window. No RAM slot is reserved.
Three read-only MU samples found IMR1/OMR1 zero with message interrupts masked.
These are selected for a separate, driver-serialized bounded echo experiment;
no live sideband writes have occurred. Use the pinned 4.07-0-29 evidence, not the
older 4.07-0-39 `remote-analysis` reference.

## RAM ownership follow-up (2026-10-11)

See [residentnet/RAM-OWNERSHIP.md](residentnet/RAM-OWNERSHIP.md). The resident queue is now 64 slots inside the
existing 512 KiB grant. Board/dispatch/staging identity is checked before network
initialization. Snapshot RNT2 words 57–59 are queue telemetry, not cache status.
The adjacent 240 KiB belongs to the stock cache data pool; never reclaim it from
size or zero software counters alone. Fixed page 15 observes SCSI bookkeeping;
hardware drain remains unproved. Cooperative net/autonet stays available.

## AcceleRAID 160 DMA inventory (2026-10-17)

**Corrected status:** The first [DMA inventory](accele160/dma_inventory/README.md)
read `0xff001400..14ff`, which is the wrong address range. Intel's 80303
peripheral map places the DMA registers at i960 local `0x00001400..14ff`.
The all-zero results cannot show channel idleness. The RTEMS lease, flash
and RAM audits remain valid, but do not use this image or select a DMA
channel from it. A transfer using the same wrong address timed out without
fetching its descriptor; the host kept the buffer and grant pinned pending
reboot. The next gate is a corrected read-only inventory, then one pinned
host buffer and aligned card descriptor with finite completion/error handling
and proven drain. Clearing CCR enable only suspends a running transfer; it
is not cancellation. Keep the old card unbound and preserve uncertain
resources. [Original captures](../artifacts/current/accele160-dma-inventory-20261017/README.md).

The [corrected inventory](accele160/dma_inventory_corrected/README.md) and
[channel-0 DMA transfer gate](accele160/dma_transfer/README.md) are now the
current checkpoint. Three 256-byte card-to-host transfers passed with fresh
pinned coherent windows, full payload/guard verification, inactive channel
and BCR/NDAR zero before release; HALT and no-host lease expiry both passed.
Channel 1 showed stock-owned descriptor state and was never borrowed. Eight
full flash reads and all owner/page/stage/worker/ISR audits passed. The
wrong-address artifact remains only as a failure record. Do not claim an
active-transfer abort or sustained network/Doom DMA path: a deliberately
stalled DMA transaction and exact drain remain to be tested. The 80303 CCR
enable bit suspends an active transfer rather than cancelling it.

## AcceleRAID 160 callback-free handoff (2026-10-17)

The [new-card handoff](accele160/handoff/README.md) passed a RAM-only finite
timer monitor after operation 13 returned. Host ENTER reached a stock-firmware
interrupt frame; expiry took 300 ticks / 3.048 s, and HALT took four ticks /
88.5 ms after a stale token remained pending. The image restored the original
firmware processor controls (`0x62002`), timer/vector/map/mask and SP. Four
same-boot complete flash reads, independent pre/post inventories, loader,
stage and every allocator record passed; [evidence and replay](../artifacts/current/accele160-handoff-20261017/README.md)
reject four tamper cases. Exact image SHA-256:
`1f448cdf017d3410e03a493f45f7ad37a8e4f4f3268c05270e5bc7fe10952f2a`.
The i960 `modpc` priority change needs mask `0x1f0000` and an initialized
replacement-value register; mask zero silently preserves the old priority.
The saved PC word in an interrupt frame is *process controls*, not an
instruction address. This bare monitor is not resident RTEMS or an
interrupt-independent watchdog. Do not run new-card networking/Doom until
RTEMS task quiescence, RAM/DMA ownership and a finite service exit pass.
The [AcceleRAID 160 finite-chain STOP gate](accele160/dma_chain_stop/README.md)
now passes twice with an unchanged image: STOP is observed during active
DMA at tick 21, the 26,624,000-byte chain completes at tick 48, and only
then do the host payload/guard, channel-inactive, owner and RTEMS audits
permit release. Six full flash reads and independent replay with ten tamper
rejections are archived. This proves deferral through **normal finite-chain
completion**, not cancellation of a genuinely stalled or erroring channel.
The shorter and cache-stale negative attempts are preserved; never unpin
after an uncertain completion.

The [active DMA suspend/resume gate](accele160/dma_suspend/README.md) passed
two unchanged-image card runs. After STOP at tick 21 with channel 0 active,
CCR=0 held the channel until tick 25, settled DAR/NDAR/BCR snapshots matched,
CCR=1 resumed it and the finite chain completed at tick 52. Full host,
channel, owner and RTEMS audits preceded release, four full flash reads
matched stock, and [replay](../artifacts/current/accele160-dma-suspend-20261017/README.md)
rejects twelve tampered captures. This is a controlled pause/resume proof,
not safe cancellation of a permanently stalled or erroring channel.

The [host-timeout retention gate](accele160/dma_timeout/README.md) then
passed twice: the card held channel 0 from tick 21 to 101, a 150 ms host
deadline expired, premature pin release returned `EBUSY`, and the owner
grant and pin remained live until the finite chain completed at tick 128.
Full card, host, flash and RTEMS audits preceded release; the
[captures and replay](../artifacts/current/accele160-dma-timeout-20261017/README.md)
reject sixteen mutations. This is an intentional software hold, not a real
PCI fault or process-death recovery proof. A timeout alone never grants
permission to unpin or release the stock RAM allocation.

The [host-process death gate](accele160/dma_process_death/README.md) reused
the accepted finite DMA image. Two host owners died by `SIGKILL` after
`DMA_HELD`; separate recovery processes saw their PIDs absent and retained
pin/grant/module state, refused early release, and only released after the
card resumed at tick 101 and finished at tick 128 with full audits. Six
flash reads matched stock and [replay](../artifacts/current/accele160-dma-process-death-20261017/README.md)
rejects fifteen changed captures. No recovery is proved for real PCI faults,
pre-checkpoint death or whole-host crash. Retain all DMA allocations until
the inactive channel, exact payload and all ownership records are proven.
