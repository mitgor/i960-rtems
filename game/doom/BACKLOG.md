# Doom backlog

## Latest: optional flat floors/ceilings accepted — 2026-10-16

`--runtime-flat` adds F6/browser switching in one engine, textured initially.
Same-session textured/flat/flat/textured low-detail windows measured **6.454 →
7.877 FPS (+22.05%)**; renderer **135.51 → 107.31 ms**, planes **40.96 → 13.46 ms**.
520 frames, 56 full paired audits, STOP/stall/drain, native oracle and mutation
checks pass. One scene/session: broader maps and interactive transport remain
separate qualification. Sky, walls, sprites and HUD retain normal rendering.
[Evidence](../../artifacts/current/flat-planes-20261016/README.md).

Next quality experiment: independently switchable half-height rendering with
browser scaling; keep normal and flat-plane controls independent. Do not claim
linear pixel/FPS scaling or extrapolate this test to 10 FPS. Baseline repeat
variance from earlier exact-span runs remains unresolved, although the two
textured windows here agree within about 0.7%. The priorities below preserve
the earlier experiments' context; flat planes are no longer just a proposal.

## Sequential execution and quality policy

Test one change at a time against the latest accepted build. Keep image-preserving
optimizations separate from quality reductions, and retain measured stage-latency
improvements even if total FPS does not change. Every card experiment retains full
system audits, ownership checks, STOP/drain, exact artifact hashes and matched runs.

- **Accepted:** selective renderer O2 + exact two-sample spans; 4.831 → 5.334 FPS
  (+10.4%), all corresponding pixels/palettes identical. See
  [renderer acceptance](../../artifacts/notes/render-20261015.md).
- **Measured, opt-in:** fixed specialized C columns on the span baseline:
  5.330 → 6.204 FPS (+16.4%), renderer 168.70 → 141.81 ms. Both candidates match
  all 520 reference images; final baseline repeats a menu image at frame 64 only.
  All measured-window images match. Full audits/replays pass; the strict all-run
  image oracle retains that failure. See [evidence](../../artifacts/notes/columns-20261015.md).
- **Done, default for playable builds:** exact bounded FixedDiv. Instrumented
  testing measured 6.047 → 6.309 FPS; independent unprofiled testing measured
  **6.224 → 6.412 FPS (+3.01%)**, renderer 141.25 → 136.93 ms, with 2,080
  matching images and 230 full paired audits. Keep `--no-fast-fixed-div` for
  the legacy reference. See [unprofiled acceptance](../../artifacts/notes/divplay-20261016.md)
  and [47-site profiling](../../artifacts/notes/fixeddiv-20261016.md).
- **Done, diagnostic opt-in:** `--input-trace` records frame/tic consumption and
  menu responder state. All 2,080 images and 228 full audits passed; trace-off
  6.432 versus trace-on 6.412 FPS. The historical menu mismatch is still
  unexplained; use the trace if it recurs, rather than retroactively declaring
  it fixed. See [acceptance](../../artifacts/notes/input-trace-20261016.md).
- **Qualified, opt-in, no meaningful speedup:** `--fast-point-side` replaces the
  protected O0 helper with defined exact arithmetic. 1,024 card vectors,
  2,080 matching images and 229 paired audits passed. **6.428 → 6.431 FPS
  (+0.034%)**, renderer 136.46 → 136.14 ms, is within repeat variation.
  Keep O0 as the default. See [acceptance](../../artifacts/notes/point-side-20261016.md).
- **Defaults:** C columns (`--fast-columns`) and spans/selective O2
  (`--fast-render`) remain opt-in; these benchmark builds explicitly enable both.
  Do not confuse the measured combined baseline with launcher defaults.
- **Done, opt-in:** wall profiling and r_segs O2; small profiled gain, full
  acceptance, defaults unchanged. See the updated execution priorities below.
- **Correctness qualified, opt-in, no established speedup:** four-sample spans.
  Pooled 6.617 → 6.449 FPS (−2.54%), but unchanged baselines differ 6.431 vs
  6.814 FPS. All 2,080 images and 228 full audits pass. Preserve the complete
  batch; investigate repeatability before interpreting the small kernel effect.
  [Evidence](../../artifacts/notes/span-four-20261016.md).
- **Quality settings:** normal rendering must remain available. Prefer runtime
  selection in one build, with explicit UI controls; separate binaries are a fallback.
  `--runtime-detail` adds high/low selection via F5 or the browser button; combine
  with `--low-detail` only to choose the initial setting. Fixed-detail builds remain
  useful for reproducible benchmarks. Do not silently enable flat floors, reduced
  viewport, alternative fuzz or missing decorations. Each needs its own switch and
  separate image-quality/FPS acceptance.

## Current execution priorities — reconciled after span acceptance, 2026-10-16

**Completed:** optional wall-region profiling and selective r_segs O2
(`--wall-profile`, `--fast-walls`). Profiled A/B/B/A measured **6.323 → 6.358 FPS
(+0.555%)**, renderer **139.188 → 138.200 ms**. Five runs including one plain
control pass: **2,600 matching images, 285 full paired audits**, ownership,
stall/STOP/drain and full replay/tamper checks. See
[wall acceptance](../../artifacts/notes/walls-20261016.md).

The plain control is **6.427 FPS / 136.475 ms renderer**. Profiling adds about
2.71 ms versus pooled A; that overhead comparison has only one plain run. Both
new switches remain off by default, and unprofiled fast-walls card FPS is still
unmeasured. Keep this small profiled improvement without claiming a normal-play
speedup or delivery-latency gain. Do not add gains from dated baselines together.

The instrumented baseline partitions BSP work into **4.972 ms traversal/culling**,
**14.584 ms other subsector work**, **21.311 ms wall setup**, **40.021 ms wall
loop**. These include preemption/interrupts/profiler overhead. The wall loop did
not improve with O2; the mechanism behind improvements elsewhere is not isolated.
Planes still cost about **40.2 ms** independently of this combined BSP bucket.

1. **Next: baseline repeatability.** The four-sample span experiment completed
   exact-output/lifecycle acceptance, but A1/A2 with identical baseline binaries
   measured 6.431/6.814 FPS. Pooled A/B/B/A is 6.617/6.449 FPS, renderer
   132.513/135.700 ms. Keep the candidate `--span-four` opt-in, two-sample default,
   and retain all four runs. Full options, framebuffer addresses, images and IRQ
   period match; cache/scheduling causes remain hypotheses. Reproduce unchanged
   plain baselines across sessions before another performance claim. See
   [all evidence](../../artifacts/notes/span-four-20261016.md).
   After repeatability is understood, consider separate high/low span paths and
   hoisting invariant alignment decisions; generated code still tests these
   inside the loop. Do not assume this unmeasured idea will improve FPS.
2. **Before promoting fast-walls:** fresh unprofiled matched A/B/B/A, full image
   and lifecycle acceptance. No default change based only on the profiled batch.
3. **Lower-priority BSP rewrite:** bounded iterative front-to-back traversal only
   where scene-specific profiling supports it. Preserve visibility order/depth
   bounds. This workload does not support treating the whole 80 ms bucket as
   traversal; broader maps can differ.
4. **Then measured memory/lookup hot spots:** profile clip copies, plane fills
   and visplane probes. Private Newlib fast-memory is already tested (see below).
   Reciprocal tables must beat the accepted exact hardware divide.

Continue one change at a time: matched A/B/B/A, every frame/palette comparison,
full paired audits, ownership, stalled-host/held-frame STOP, heap drain and
replay/tamper checks. Keep measured stage-latency gains even if total FPS is flat.

## Ranked research follow-up — added 2026-10-15

Full [performance research and source references](PERFORMANCE-RESEARCH.md), based
on Intel manuals, RealDOOM, FastDoom, GBADoom, RP2040 Doom, nRF52840 Doom and
d32xr. Source commits/hashes and accepted-object arithmetic checks are saved in
[`evidence.json`](../../artifacts/doom-research-20261015/evidence.json).
The research ranks potential separately from effort/confidence; it contains no
new target speedup. Earlier screen-copy/peer-yield improvements are already spent.

### Requested priorities 1–6: preserve graphics and gameplay

These correspond to items 1–6 in the research chat's final ranking, ordered by
potential steady FPS impact. See the execution priorities above and `TESTING-QUEUE.md` for measured results;
remaining experiments are unmeasured. This historical ranking is not the current execution order.
They are implementation handoffs, not authorization to discard existing checks.

1. [ ] **Specialized span and column kernels (F2): partially complete.** Exact
   two-sample spans and specialized C columns have measured gains recorded above.
   Further private 1/4-pixel span variants remain open. Coordinates are already
   packed: evaluate independent sample scheduling, modest unrolling and aligned
   packed stores, including safe low-detail duplication. Preserve endpoints,
   wrap and post bounds; do not repeat the completed column qualification.
2. [ ] **Exact fixed-point arithmetic (F3): FixedDiv complete; further work open.**
   The 47-site profile, bounded exact `ediv` implementation and independent
   unprofiled acceptance are complete; exact divide is now the playable default.
   Preserve target saturation, signs, rounding and legacy INT_MIN fallback.
   FixedMul already uses hardware `emul`; target call/sign/shift overhead only
   if measured. Reciprocal candidates must beat the new exact baseline, not the
   old general-purpose helper. See the experiment matrix below.
3. [ ] **Geometry/BSP (F4): exact point-side qualification complete; traversal open.**
   The opt-in exact helper passed full acceptance but gave no meaningful speedup.
   The split wall profile is now complete: traversal/culling averages about
   4.97 ms in this workload. Iterative traversal is lower priority here; retain
   safe depth bounds, visibility order and exact output in any future trial.
4. [ ] **Selective compiler optimization (F5): partially complete.** The r_segs
   Os/O2 profiled comparison is accepted (+0.555% FPS); unprofiled qualification
   remains open. Compare other measured hot modules; inspect size, spills, calls and
   target correctness. Keep the private ABI and known compiler workarounds
   explicit. Do not promote blanket flags from another i960/compiler variant.
5. [ ] **Private memcpy/memset and repeated fills (F6): low–medium steady
   potential.** Follow the detailed memory backlog below: private namespaced
   Newlib, clipping arrays, plane fills and explicit calloc/realloc loops.
   Level-loading gains and automap/UI improvements are separate from steady FPS.
   The opt-in `--fast-memory` path has since passed a full 520-frame comparison
   in [release-priority acceptance](../../artifacts/notes/release-priority-20261015.md):
   4.835 → 4.855 FPS (+0.40%), insufficient to establish a meaningful gain.
   Do not repeat implementation of that switch; per-site profiling remains open.
6. [ ] **Cache/layout and plane lookup/order (F7): low–medium, scene-dependent.**
   Count visplane search probes, texture switches and hot-table access. Compare
   small exact-key hashes and cache-aware ordering against simple linear paths;
   include sorting/hash overhead and memory pressure in timing.

Additional longer-term research, outside the requested six priorities:

- [ ] **F8: bounded composite/pre-lit caches or prepared assets**, only after
  measuring generation/reuse/misses and staying inside the admitted arena.
- [ ] **F1: assess deferred texture-grouped rendering as a separate rewrite.**
  Large theoretical ceiling, low confidence; RP2040 multicore/interpolators do
  not transfer, and equivalent pixels require independent proof.

Optional quality modes, ranked by potential FPS impact:

- [ ] **Q1: smaller viewport / half-height / potato**, preferably host upscaling,
  with explicit UI/HUD/aspect/protocol support; keep gameplay tick rate intact.
- [ ] **Q2: flat-color floors/ceilings**, followed by optional flat sky/walls.
- [ ] **Q3: alternate fuzz/transparency and optional distant decoration limits**;
  do not silently remove enemies or simulation.

Use the report's Amdahl scenarios only as conditional calculations, not FPS
forecasts. Measure current frame fractions, compare A/B/B/A on several scenes,
and keep audits, IRQ/control latency, ownership, pixel/palette and STOP/drain
acceptance. Remaining screen-copy removal, more host buffers, and WAD/loading
work have lower current evidence for additional steady FPS.

### Best practices to carry over from other ports

| Source | Practice to apply here | Concrete backlog action / limit |
|---|---|---|
| [RealDOOM](https://github.com/sqpat/RealDOOM) | Specialize wall/post, detail and lighting paths outside pixel loops; keep pointers and increments in registers; use bounded integer math. | Apply to priorities 1–2; test small kernels and data alignment. Do not import x86 segmentation, EMS, VGA I/O or self-modifying code. Keep our pixel oracle: upstream fidelity choices are not automatic equivalents. |
| [FastDoom](https://github.com/viti95/FastDoom) | Iterative front-to-back BSP, CPU-specific small/large kernel choices, controlled timedemos and explicit quality settings. | Apply to priorities 1, 3 and 4. Preserve traversal/culling order, handle stack depth safely, compare compact vs unrolled code, and expose quality reductions only as optional modes. x86 FPU/MMX/VGA techniques do not apply. |
| [RP2040 Doom rendering](https://kilograham.github.io/rp2040-doom/rendering.html) | Reduce hidden/repeated work, batch by texture where ordering permits, separate rendering from display ownership. | Use priority 6 measurements before batching; reserve deferred display lists for the separate rewrite task. The second core/interpolators do not exist on our RP, and its clipping differences need independent validation. |
| [RP2040 speed/RAM analysis](https://kilograham.github.io/rp2040-doom/speed_and_ram.html) | Place small hot data deliberately; balance code/data size against cache churn and decoding overhead. | Measure working sets and code growth in priorities 1, 4 and 6. Our engine already runs from DRAM, and internal i960 RAM is data-only: do not copy the GBA/Pico advice to execute hot code there. |

- [ ] Use exact recorded demo/input traces and compare full pixels/palettes,
  game tics and state, not only a single screenshot or average FPS.
- [ ] Keep simulation math and original lookup tables exact. Tiny arithmetic
  differences can desynchronize demos; rendering-only approximations require a
  separately selected and tested fidelity mode.
- [ ] Measure render, copy, data stalls and transport separately. Preserve audits,
  control/IRQ latency, generation ownership, held-frame STOP and heap/IRQ drain.
- [ ] Prefer measured C specialization to an assembly rewrite by default; our
  previous C-column trial was slightly faster than its assembly alternative.

### Reciprocal table: memory feasibility and likely benefit

**Assessment, 2026-10-15:** a full table is small enough relative to physical
DRAM to investigate, but is not currently a proven allocation or FPS win.
Native exact division has since passed acceptance and is the playable default.
Any small/full-table experiment must now improve on that baseline. This analysis does not allocate RAM or change the port.

**Size and placement:** GBADoom's
[`reciprocalTable[65537]`](https://github.com/doomhack/GBADoom/blob/89097b3ff31ac1e1b2cdce9854e49726cfa462bf/source/m_recip.c)
contains 32-bit entries: **262,148 bytes (256 KiB + 4 bytes)**. That is about
1.56% of the board's 16 MiB and 3.13% of the **owned 8 MiB Doom arena**. Physical
capacity alone does not grant allocation rights; the arena also holds the engine,
6 MiB zone, caches, frame buffers, metadata and guards. Do not count unused zone
contents as free outer-arena memory or shrink the zone without compatibility tests.

Embedding the full array in engine `.data`/`.rodata`/`.bss` is not a drop-in
option: [`runtime/engine/admit.py`](runtime/engine/admit.py) currently caps playable
admission at **900,000 bytes**. The latest plain wall-batch image is 819,168
bytes; adding the array alone gives **1,081,316 bytes**, before extra code/metadata.
The very small kernel mutable-tail reserve is also not storage for this table.

A possible trial is a **normal owned arena allocation outside the admitted image**,
filled/generated or uploaded with existing bounded ownership mechanisms. Count
initialization, guards, descriptors and alignment; bind the pointer through a
reviewed private runtime interface and retain it until task/IRQ/DMA users drain.
First inspect the latest exact memory manifest and largest contiguous free block
at the intended allocation phase. Old estimates leave different headroom and are
not proof that this current build can allocate the table. Reserving it before the
6 MiB zone can fragment/fail that allocation; reserving after startup can fail or
increase later level/cache pressure. Do not silently raise admission or arena caps.

**Why it might help:** repeated denominators, high arithmetic cost and good table
locality can replace expensive divisions with a load, multiply and shifts. Measure
FixedDiv/reciprocal call counts, denominator range/reuse and helper elapsed time.
The table is not relevant to ordinary pixel loops already using incremental adds;
do not introduce division or table access per pixel where none exists.

**Why it might not:** the i960RP D-cache is **2 KiB**; the full table is about
**128×** that size, so dispersed denominators can cause DRAM loads and displace
texture/colormap data. A normalized lookup also costs sign handling, normalization,
shifts, multiplication and any correction. The accepted bounded `ediv` path already avoids the legacy general-purpose
`___divdi3` handling; measure any table against that current path.
Table storage/access, initialization and cache pressure must be included, not just
instruction count on a warm lookup microbenchmark.

**Accuracy:** the GBADoom
[`FixedReciprocal`](https://github.com/doomhack/GBADoom/blob/89097b3ff31ac1e1b2cdce9854e49726cfa462bf/include/m_fixed.h)
is an approximation. It normalizes larger divisors by shifting; this can discard
bits, and its finite-width reciprocal is rounded/truncated. A 65,537-entry table
does not supply an exact result for every signed 32-bit divisor/numerator.
Multiplying by that reciprocal is not automatically bit-identical to FixedDiv.
Keep gameplay, physics, BSP side tests and deterministic-demo math exact. For an
exact replacement, validate an estimate plus quotient correction under proved
bounds, or retain exact division as a fallback. Handle zero, INT_MIN, saturation,
negative rounding and overflow explicitly; do not import the nRF FPU helpers.

| Candidate to compare | Table payload | Reason to test |
|---|---:|---|
| Legacy `___divdi3` | 0 | Reference retained through `--no-fast-fixed-div`; comparison completed. |
| Exact bounded i960 divide | 0 | Current playable default; unprofiled gain accepted. Baseline for new candidates. |
| 256/512-entry normalized seed table plus refinement/correction | 1/2 KiB | Much smaller footprint; still competes with other hot data. Correctness/refinement overhead must be measured. |
| Small bounded cache for measured repeated denominators | Depends on key/value/precision/metadata | Avoid a global table when a few denominators dominate. Do not mistake a cached reciprocal for an exact cached quotient. |
| Full 65,537-entry table | 262,148 bytes | Benchmark actual denominator locality and arena/cache effects; rendering-only approximate mode unless exactness is proved. |

- [ ] Freeze the current build and record exact admission bytes, arena high-water,
  largest free block and allocation phase; decide whether a full-table trial fits
  without moving guards, reducing validation or breaking the contiguous zone.
- [ ] Capture denominator distributions and time/call counts by site on several
  scenes. Test clustered/repeated and dispersed denominators, with normal texture
  traffic; report exact/approximate paths separately.
- [x] Compare legacy division against exact bounded divide, including signed
  extremes, zero, saturation and recorded/random oracle inputs; see accepted evidence above.
- [ ] Compare small seed tables, denominator caches and any full-table candidate
  against the accepted exact divide. Repeat independent edge/random/recorded
  arithmetic tests; the old division result does not qualify table arithmetic.
- [ ] If approximate rendering is tried, quantify quotient/pixel differences and
  gate it explicitly; never let a rendering-only experiment replace game math.
- [ ] Accept only after full matched card FPS/frametime, memory-pressure and
  level-change tests, unchanged ownership/audits and STOP/drain. No speedup is
  established by table size or successful allocation alone.

## Memory copy and fill optimization — added 2026-10-15

**Status: partially complete.** The private Newlib `--fast-memory` switch has
physical acceptance in the release-priority batch (4.835 → 4.855 FPS, no
meaningful gain established). Per-site target profiling and further gains remain
unmeasured. User requested this handoff for work from another chat. Read the
latest entries in `CLAUDE.md` and dated acceptance artifacts before choosing a
baseline: screen copying, peer scheduling and IRQ draining have separate ongoing
or accepted changes. Do not reuse an older FPS figure as the current baseline.

### First target: Doom's private memory routines

Doom links a namespaced private Newlib, built by
[`runtime/platform/build.py`](runtime/platform/build.py). Changing RTEMS's
`rtems/irq/libc.c` does **not** automatically change engine memory calls.
The private library is built with size optimization; pinned Newlib 1.11.0
`libc/string/memcpy.c` and `memset.c` select byte-oriented source implementations
under `__OPTIMIZE_SIZE__`. Inspect the actual private target routines and compiler
inlining before claiming that all callers execute byte loops.

- [ ] Measure private memcpy/memset call counts, byte totals and size/alignment
  distributions in a controlled scene; distinguish loading from gameplay.
- [ ] Compare selective speed compilation of these routines or private aligned
  word/bulk implementations, keeping the rest of the engine's build fixed.
- [ ] Inspect generated i960 code and benchmark on the card; native timings
  cannot establish i960 performance.

### Candidate engine sites

These locations were inspected in pinned DoomGeneric commit
`e257a09527062bfb986b6e5e0780839b6cbd5b71`, archived in
`artifacts/doom-m1-20261011/doomgeneric-source.tar.gz`. Line numbers refer to that
unpatched source and may move in generated builds.

| Priority / phase | File and function | Candidate work |
|---|---|---|
| High: gameplay | `r_segs.c`, `R_StoreWallRange`, lines 718/726 | Variable-length ceiling/floor clipping copies into `lastopening`; repeated per eligible wall segment. Short arrays can be only 2-byte aligned: handle unequal modulo-4 alignments correctly. |
| High: gameplay | `r_plane.c`, `R_ClearPlanes`, line 194 | Clear the 800-byte `cachedheight` array each rendered frame. |
| High: gameplay | `r_plane.c`, `R_FindPlane` / `R_CheckPlane`, lines 249/314 | Fill each new/split visplane's `top` array with `0xFF`; scene-dependent frequency. |
| Mode-specific: automap | `am_map.c`, `AM_clearFB`, line 836 | Large framebuffer fill on automap redraws. |
| HUD / smaller views | `v_video.c`, `V_CopyRect` / `V_DrawBlock`, lines 113/523; `r_draw.c`, `R_VideoErase`, line 931 | Rectangular row copies and background restoration; status-bar refresh calls `V_CopyRect`. Profile actual redraw frequency rather than assuming a full HUD copy every frame. |
| Loading / warm restart | `p_setup.c`, level-loading functions | Zero seg/subsector/sector/line/side/blocklink arrays; improves level preparation rather than steady FPS. |
| Texture first use | `r_data.c`, `R_DrawColumnInCache`, line 212 | Copy texture posts into composite textures; potential loading/first-use stalls, not necessarily repeated steady work. |
| Transitions | `f_wipe.c`, lines 70/141; `i_video.c`, `I_ReadScreen`, line 377 | Full-screen transition copies/captures. |
| Lower priority / conditional | `v_video.c`, `V_DrawRawScreen`; `r_draw.c`, `R_FillBackScreen`; `f_finale.c` | Raw-screen/background/finale copies; qualify which modes actually execute them. |

- [ ] Profile wall-clipping copies and visplane fills first after the private
  routine baseline; record counts/bytes/time before specializing individual sites.
- [ ] Keep automap, HUD, transitions and loading measurements separate from
  steady renderer FPS.

### Explicit byte loops outside memcpy/memset

[`runtime/platform/port.c`](runtime/platform/port.c) implements `calloc` clearing
and `realloc` copying with explicit byte loops. Optimizing private Newlib alone
will not change these loops.

- [ ] Profile calloc/realloc use, then route suitable work through tested private
  bulk routines or specialize it without changing allocation ownership/lifetimes.

The already optimized WAD-cache copies and fixed screen-presentation path are
separate work; check their latest acceptance before duplicating changes.
Additional context: [firmware performance audit](../../artifacts/firmware-performance-20261015/README.md).

### Acceptance for any implementation

- [ ] Test zero length, every pointer alignment, exact allocation edges, prefix
  and tail handling, and all memset byte values; no overreads or unaligned wide
  accesses. Preserve memmove overlap behavior wherever it delegates to memcpy.
- [ ] Preserve Newlib symbol namespacing, ABI, allocation ownership and normal
  RAM-only access widths. Do not widen MMIO/volatile operations.
- [ ] Run sanitizer correctness tests and native deterministic pixel/palette
  comparisons, then inspect the actual target code.
- [ ] Use a bounded matched target comparison, preferably A/B/B/A. Keep scene,
  detail level, renderer variant, scheduling, WAD, checksum modes and audit
  cadence fixed. Report cold load, warm restart, renderer/copy timings, steady
  delivered FPS and IRQ/control latency separately.
- [ ] Retain full audits, frame/DMA ownership checks, held-frame STOP and heap/
  IRQ drain. Keep the known native/card pixel discrepancies visible unless this
  work independently fixes and validates them. Do not claim a speedup from
  source inspection or extrapolate loading gains to gameplay.
