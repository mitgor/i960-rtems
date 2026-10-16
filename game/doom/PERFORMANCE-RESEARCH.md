# Doom on i960RP: performance research and ranked experiments

Research date: **2026-10-15**. Scope: our DAC960PG i960RP, existing RTEMS
runtime, pinned DoomGeneric/Freedoom engine. This is research and source/object
inspection, not a newly optimized build or hardware benchmark. Six upstream
repositories were checked out and inspected; exact commits, selected-file hashes,
permanent source URLs and arithmetic-object evidence are in
[`evidence.json`](../../artifacts/doom-research-20261015/evidence.json).

## Main findings

The largest practical opportunities are in rendering, geometry/math helpers and
generated code. Optional lower-resolution or flat-surface modes offer larger
potential gains at a visible quality cost. A full renderer redesign has a high
theoretical ceiling but much lower confidence and far more integration risk.
The sensible first experiments are smaller: exact FixedDiv, span kernels,
production qualification of our existing specialized C columns, and the hot
`R_PointOnSide` workaround/BSP traversal.

The engine already uses 16.16 integer arithmetic. Its pinned `FixedMul` uses a
64-bit product, and `FixedDiv` uses a shifted integer dividend. Converting the
engine wholesale from floating point to fixed point is therefore not an open
task. [Pinned arithmetic source](https://github.com/ozkl/doomgeneric/blob/e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric/m_fixed.c).

More concretely, the accepted archived i960 `m_fixed.o` contains **hardware
`emul` at text offset `18`**, while FixedDiv has a relocation to **`___divdi3`**.
FixedMul does not reference a general multiplication helper. This materially
changes priorities: audit signed correction/shift/call overhead in multiplication,
but investigate replacing general 64-bit division with a carefully bounded exact
operation first. The object is from the pinned accepted ping-pong build; this
does not establish its percentage of current frame time. The collection script
checks the archive identity, ELF symbols, relocation and opcode, not just strings.

## Use the latest local baseline

Several optimizations have already happened and must not be counted again:

| Existing local result | What it establishes |
|---|---|
| Screen copy `3.815 → 4.517 FPS`, copy `44 → 12 ms` | Fixed 320×200 presentation copy already accepted; do not propose replacing 200 bytewise row copies as new work. |
| Peer yield `4.517 → 5.273 FPS` | Service-worker scheduling already improved in an opt-in profile. |
| IRQ-drain fixed repeat `5.192 FPS`, maximum IRQ gap `10.731 ms` | Subsequent shutdown fix retained bounded IRQ service. Its FPS is not evidence of another rendering optimization. |
| Bulk capture `5.192 → 4.802 FPS`, capture ioctl `43.178 → 0.278 ms` | Dramatic host-call improvement did **not** establish an FPS gain. Release/audit/scheduling interactions need matched repeats. |
| Specialized columns: original `3.478`, C `3.857`, assembly `3.821 FPS` | Earlier bounded trial favored simple specialized C over assembly. Normal builds still select original columns unless the column-test build is enabled. Requalify a fixed C choice on the newer baseline. |
| WAD word copies: first frame `192.075 → 117.566 s`, gameplay about `3.8 FPS` | Loading improvement; do not turn it into a steady-rendering speedup claim. |

These are separate experiments and binary configurations. Their percentages
cannot be added or multiplied into a new combined result. See latest
[`CLAUDE.md`](CLAUDE.md), [screen-copy](../../artifacts/screen-copy-20261015/README.md),
[peer-yield](../../artifacts/peer-yield-20261015/README.md),
[IRQ-drain](../../artifacts/irq-drain-20261015/README.md),
[bulk-capture](../../artifacts/bulk-capture-20261015/README.md) and
[columns](../../artifacts/doom-columns-20261015/README.md).

## Ranked by potential steady FPS impact

The ordering is an engineering assessment of affected work, not measured
incremental gains. Confidence describes transferability to our implementation.
Items overlap: arithmetic and compiler improvements may speed the same renderer
time. The suggested implementation order appears later.

### Optional modes that change the image

| Rank | Idea | Potential | Main qualification |
|---|---|---|---|
| Q1 | Smaller 3D viewport; half-height rendering or 80-column “potato” mode; upscale on host | **Largest straightforward ceiling**, if pixel work dominates | Lower spatial detail; keep gameplay ticks unchanged. Existing low detail already halves horizontal samples, so that gain is spent. |
| Q2 | Flat-color floors/ceilings, then optional flat sky/walls | **High in surface-heavy scenes** | Removes texture sampling/lighting work and can remove plane machinery, but visibly changes the game. |
| Q3 | Simpler fuzz/transparency or reduced distant decoration | **Scene-specific**, often small in ordinary rooms | Changes effects or visibility. Never silently cull enemies or skip simulation. |

FastDoom explicitly offers quarter-width potato, half-height executables,
untextured surfaces and alternate invisibility effects. These are useful
user-selectable modes, not evidence that equivalent-quality code became that
much faster. [FastDoom options](https://github.com/viti95/FastDoom/blob/9a7b435a9b95db1ba38f89f1139050d748d32fde/README.txt).

The UI can continue producing 320×200 indexed frames while a smaller 3D view is
scaled by the host. This avoids spending card CPU to upscale the world. It needs
an explicit format/ownership contract; menus, automap, status bar, view tables,
aspect ratio and screenshots cannot be fixed by changing one resolution macro.

### Preserve the current image and gameplay as the acceptance target

| Rank | Candidate | Potential / confidence | Evidence and reason |
|---|---|---|---|
| F1 | Deferred/batched renderer that avoids hidden work and groups texture use | **Very high theoretical ceiling; low confidence** | RP2040 architecture shows a credible design, but our single CPU does not inherit its multicore or interpolator acceleration. Large rewrite; exact pixels are an acceptance goal, not a proven property. |
| F2 | Specialized span + column kernels; independent load scheduling; aligned packed stores | **High; medium-high confidence** | Pixel loops repeat thousands of times. Our columns already showed about 10% in an older trial; span loop remains a concrete target. |
| F3 | Exact fixed-point divide; remove hot arithmetic helper/call overhead | **Medium-high; medium confidence** | The accepted object actually references `___divdi3`; benefit depends on measured divide frequency and helper cost. |
| F4 | Fix/replace hot `R_PointOnSide` workaround; iterative BSP traversal and cheaper setup | **Medium-high in geometry-heavy views; medium confidence** | Current helper deliberately uses `-O0`; current BSP is recursive. FastDoom demonstrates an explicit-stack alternative. |
| F5 | Selective `-O2`/inlining/leaf calls for hot modules, keeping small cold code | **Medium; medium confidence** | Current engine/private libc use `-Os`. Requires target correctness checks because this compiler has known failures. |
| F6 | Private Newlib memcpy/memset, clipping-array copies, visplane fills | **Low-medium steady FPS; high confidence of relevant sites** | Still useful after the full-screen copy fix, but bulk presentation savings have already been captured. |
| F7 | Cache-aware layout, plane lookup hashing and flat-order batching | **Low-medium; scene-dependent** | Tiny direct-mapped D-cache and repeated plane searches/texture changes offer plausible opportunities. Sorting/hash overhead can lose on small scenes. |
| F8 | Bounded composite/pre-lit texture caches or prepared asset format | **Uncertain steady benefit; potentially strong for stalls** | More attractive if profiling finds repeated generation or expensive data access; existing caching may already cover it. |
| F9 | Remove the remaining screen copy through a qualified render-target redesign | **Small bounded ceiling after current copy fix; high risk** | Remaining copy was about 12 ms in its accepted comparison. Persistent row pointers/HUD state and DMA-pinned slots prevent naive pointer rotation. |
| F10 | More host buffers, host capture batching, DMA tuning | **Low current steady-FPS evidence** | Previous-publication wait had reached zero; latest capture batching reduced ioctl cost but regressed measured FPS. Treat jitter/latency separately. |

### Quantifying “potential” without inventing a benchmark

For a measured fraction `p` of total non-overlapped frame time sped up by `s`,
the ideal whole-frame multiplier is `1 / ((1-p) + p/s)`. These are **conditional
scenarios**, not predictions for any candidate above:

| Assumed current frame fraction | Local speedup | Ideal FPS gain |
|---:|---:|---:|
| 10% | 2× | 5.3% |
| 20% | 2× | 11.1% |
| 30% | 2× | 17.6% |
| 40% | 2× | 25.0% |
| 20% | 3× | 15.4% |
| 80% | 2× | 66.7% |

For example, 20% arithmetic time accelerated 3× yields 15.4%, not 3× FPS.
Using an illustrative 200 ms frame with 12 ms copying, eliminating that copy
completely gives at most `200/188 = 1.064×` under a serial model. Those timings
were not measured together in the latest build; use this only to understand
why a risky zero-copy rewrite now ranks below renderer work. Overlapping DMA,
audits and scheduling require critical-path measurements rather than blindly
adding all phase counters.

## What RealDOOM actually teaches us

RealDOOM targets 16-bit DOS and has extensively rewritten rendering and
arithmetic in assembly. Its release notes report a 35–40% gain for a renderer
rewrite versus an older release; that is an upstream claim, not an i960 estimate.
It also exposes fidelity options and acknowledges rendering inaccuracies.
Use its specialization and data-placement ideas while retaining our own oracle.
[RealDOOM project/history](https://github.com/sqpat/RealDOOM/blob/d5f6ce27a17d465691acef724d4b4d35207bcc74/README.md).

Inspecting its [column kernel](https://github.com/sqpat/RealDOOM/blob/d5f6ce27a17d465691acef724d4b4d35207bcc74/r_col24.asm),
[span kernel](https://github.com/sqpat/RealDOOM/blob/d5f6ce27a17d465691acef724d4b4d35207bcc74/r_span24.asm)
and [math](https://github.com/sqpat/RealDOOM/blob/d5f6ce27a17d465691acef724d4b4d35207bcc74/math.asm)
suggests keeping texture/lighting pointers and increments live, specializing
quality/wall/post cases outside loops, and avoiding general arithmetic machinery
where bounds allow a narrower exact operation. Its segment layouts, EMS mapping,
VGA ports and self-modifying arithmetic bytes are specific to that environment.
They should not be copied into our runtime. We can use fixed small kernels and
normal data parameters instead of patching executable instructions.

Our C-column trial is an important counterexample to “assembly is always faster”:
the assembly version did not beat specialized C. Measure generated instructions,
dependencies and working-set size, not the source language.

## Concrete equivalent-output experiments

### F2: spans first, then improve already qualified columns

The pinned `R_DrawSpan` already packs coordinates and increments into one
32-bit accumulator. An unused unrolled implementation is present under `#if 0`.
Do not claim packing itself as a new optimization, and do not simply enable
the disabled code: it includes an apparent typo and has not passed our tests.
[Pinned renderer](https://github.com/ozkl/doomgeneric/blob/e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric/r_draw.c).

Start with a private span-job kernel, local copies of source/colormap/step,
2- and 4-pixel variants and exact tails. Generate independent addresses early,
interleave independent samples, then pack four final indexed pixels into one
aligned word where worthwhile. For low-detail spans/columns, duplicate a
calculated pixel with an aligned short or repeated-pair word store rather than
independent byte stores where destinations are adjacent and alignment permits.
Keep sampling increments, wrap, endpoint counts and post bounds unchanged.

FastDoom retains processor-specific small and larger kernels, including
alternative span shift sequences. The portable lesson is to benchmark the code
size/latency tradeoff, not translate x86 shifts instruction-for-instruction.
[Example kernel](https://github.com/viti95/FastDoom/blob/9a7b435a9b95db1ba38f89f1139050d748d32fde/FASTDOOM/lineahKN.asm),
[maintainer changelog](https://github.com/viti95/FastDoom/wiki/Changelog).

For columns, first qualify a fixed specialized C selection on current play
builds: `doom_column_mode` presently rotates only in a bounded experiment.
Then try modest unrolling and independent lookup scheduling. Do not enlarge the
hot loop enough to displace other frequently executed code from instruction
cache. Existing post clamping and the four known native/card pixels remain
explicit correctness obligations.

### F3: exact FixedDiv before approximate reciprocal tricks

The i960 has unsigned extended multiply/divide instructions. An exact signed
fixed-point divide can potentially use bounded unsigned magnitudes, a 64-bit
shifted dividend, one extended divide and sign restoration, with the original
saturation contract handled explicitly. `ediv` is **not** signed and returns
remainder and quotient in a register pair; it is not a drop-in replacement for
the C expression. Validate zero, signs, INT_MIN, saturation and quotient bounds.
Do not create C signed-shift/negation undefined behavior while “optimizing” it.
[Intel Rx instruction reference, §6.2.25–26](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF).

Inspect the linked `___divdi3` body before estimating savings: a general helper
can itself use hardware divide. Its symbol alone does not prove bit-by-bit
software division or that a replacement will win.

FixedMul already emits `emul`; its remaining opportunities are sign correction,
shift sequence, exact leaf ABI and selective inlining. “Replace software multiply
with hardware multiply” is not supported by the inspected object. Preserve the
low 32 bits of the signed shifted product, including negative rounding behavior.

GBADoom's [integer divide path](https://github.com/doomhack/GBADoom/blob/89097b3ff31ac1e1b2cdce9854e49726cfa462bf/include/m_fixed.h)
and [reciprocal table](https://github.com/doomhack/GBADoom/blob/89097b3ff31ac1e1b2cdce9854e49726cfa462bf/source/m_recip.c)
are useful alternatives to study. The table has 65,537 32-bit entries—about
256 KiB—vastly larger than our data cache. It is not automatically faster than
hardware division on the i960. A smaller seed table plus refinement is a possible
render-only experiment; preserve exact gameplay arithmetic and validate errors
before replacing a quotient with an approximation.

The [nRF52840 helper source](https://github.com/next-hack/nRF52840Doom/blob/779cad0ba1fae35523139e9af1f64bb3b14a9aa1/NRF52840Doom/Doom/include/m_fixed.h)
explicitly uses floating-point reciprocal/division helpers. Importing those into
our soft-float build could make it slower. “Microcontroller port” does not imply
“no hardware floating point anywhere.”

### F4: BSP traversal and the known compiler workaround

Our `R_RenderBSPNode` is recursive and calls `R_PointOnSide`; our build extracts
the latter into a separate `-O0` translation unit to avoid a known compiler
miscompilation. Profile its call count and time before treating all “geometry”
as one opaque cost. An exact assembly/defined-integer helper or a separately
verified compiler configuration may remove this unusually expensive workaround.
[Current builder](build.py),
[pinned traversal](https://github.com/ozkl/doomgeneric/blob/e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric/r_bsp.c).

FastDoom implements [iterative front-to-back traversal](https://github.com/viti95/FastDoom/blob/9a7b435a9b95db1ba38f89f1139050d748d32fde/FASTDOOM/r_bsp.c)
with explicit node/side arrays. Preserve front-first order and the point at which
back-side bounding boxes are tested. Do not import its fixed maximum-depth
failure behavior or narrower geometry fields blindly. Bound/provision a stack
for accepted maps and fail safely if exhausted. Reduced function/window traffic
is plausible on i960, but its register cache means recursion is not necessarily
as expensive as on an 8088; benchmark both approaches.

### F5–F7: compiler, memory and planes

Sweep selected hot translation units through `-Os` and `-O2` before wider changes;
try inlining small arithmetic helpers only at measured hot sites. Keep code size,
stack/register spills, unresolved helpers and target pixel correctness in the
comparison. Intel's compiler guide discusses profile-guided decisions,
register pressure and scheduling, but its CTOOLS/global-optimizer switches are
not a recipe for our GCC 3.3.6 build. Do not pass unsupported historical flags
or enable blanket `-O3` around known backend failures.
[Intel compiler manual, chapter 12](https://datasheets.chipdb.org/Intel/80960/manuals/65123003.PDF).

Our [private library builder](runtime/platform/build.py) separately compiles and
namespaces Newlib; speeding RTEMS libc does not speed those engine symbols.
The [copy/fill backlog](BACKLOG.md#memory-copy-and-fill-optimization--added-2026-10-15)
already lists clipping arrays, visplane clears, automap and HUD work. Improve
exact byte edges/alignment, then compare word and quadword bulk kernels. calloc
and realloc in the platform adapter contain explicit loops and need separate
attention. Most level-array clears affect loading, not steady FPS.

For visplanes, test a small hash keyed by the **same** height/texture/light fields
used in the current linear lookup, preserving merge/split behavior. Then consider
rendering independent opaque planes in a texture-friendly order. d32xr contains
an explicit [plane sort to improve texture cache reuse](https://github.com/viciious/d32xr/blob/55bf94b43a039ae0a0d2f09ad9bc23bea5963714/r_phase7.c)
and a [bounded texture-cache implementation](https://github.com/viciious/d32xr/blob/55bf94b43a039ae0a0d2f09ad9bc23bea5963714/r_cache.c).
Its multicore synchronization and SH-2 cache operations do not transfer to i960.
Hashing/sorting may be slower on simple scenes; count probes, planes and texture
switches before implementing them.

An optional exact pre-lit cache could replace the dependent
`colormap[texture[index]]` pair with one lookup after preparation. Restrict it to
measured hot immutable texture/light combinations, with bounded eviction and
palette/colormap identity. Pre-lighting every texture at every light level
multiplies storage and can evict more useful data. This is speculative F8 work,
not a recommendation to allocate beyond the admitted arena.

## i960-specific coding rules worth applying

The RP uses a Jx-family core; optimization advice for superscalar Cx processors
does not automatically apply. Intel's assembler guide distinguishes the Rx
portable instruction subset from Jx-specific tuning on RP/RD. Match actual
assembler/compiler support rather than treating all 80960 variants alike.
[Intel assembler guide, chapter 2](https://datasheets.chipdb.org/Intel/80960/manuals/48527606.PDF).

For the RP, separate a load from its first dependent use with useful independent
work; keep data naturally aligned; benchmark aligned multiword transfers for
uncached bulk data. Avoid assuming fewer instructions means fewer cycles:
some register operations are microcoded. `test<cc>` can be costlier than select,
and RP has no Cx-style branch prediction. Do not use MDU destinations in the
first four local registers when avoidable. These are tuning opportunities,
not reasons to change fault policy or register preservation.
[Intel Rx §5.3](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF).

Use the documented ABI for inline assembly, register pairs and g14, and inspect
actual leaf-call generation. GCC's documented options include leaf procedures,
alignment and strict-alignment compatibility; some descriptions are generic
across older variants. `-mold-align` already participates in our private ABI:
changing it globally is not an isolated speed experiment.
[GCC 3.3.6 i960 options](https://gcc.gnu.org/onlinedocs/gcc-3.3.6/gcc/Intel-960-Options.html).

Our DRAM code and data already execute from external RAM. The 1 KiB internal
RAM is data-only; “put hot code in fast internal SRAM” from a GBA tutorial is
invalid here. Avoid packed/misaligned hot structures. With 2 KiB direct-mapped
D-cache, compare actual address mappings of hot tables and textures; a 320-byte
stride repeats cache-set selection after 32 rows for a fixed byte offset.
That arithmetic is not proof of a cache bottleneck: byte-store allocation,
source loads and competing accesses determine the actual effect.

## What to borrow, and what to leave behind

| Port | Transferable idea | Hardware/behavior that does not transfer directly |
|---|---|---|
| RealDOOM | Specialized kernels, carefully bounded integer math, small working sets | x86 segments/EMS/VGA/self-modifying instruction layout |
| FastDoom | Iterative BSP, CPU-specific kernels, explicit optional quality modes, timedemo measurements | x86 FPU/MMX copies, VGA register tricks, DOS extender improvements |
| GBADoom | Integer arithmetic helpers, hot-data placement, skip unchanged HUD work | GBA BIOS/DMA/VRAM/IWRAM assumptions and approximate math/demo differences |
| RP2040 Doom | Texture batching, avoid unnecessary work, strong deterministic demos | Second core, interpolators, PIO scanout and overclocked 270 MHz performance |
| nRF52840 Doom | Prepared assets, overlap display transfers and rendering | Hardware-FPU math helpers and its QSPI/display architecture |
| d32xr | Bounded caches, plane lookup/sorting, architecture-specific math | Dual SH-2 scheduling/divider registers/cache synchronization |

The GBADoom [HUD change detector](https://github.com/doomhack/GBADoom/blob/89097b3ff31ac1e1b2cdce9854e49726cfa462bf/source/st_stuff.c)
is a useful small-mode optimization: update relevant status-bar data when values
change. Correctly handle damage palettes, forced refresh, menus, wipes and
double-buffer history. It cannot avoid redrawing a changing 3D world.

RP2040's [rendering account](https://kilograham.github.io/rp2040-doom/rendering.html)
describes deferred texture-grouped columns and clipping that reduces work; its
[speed/RAM account](https://kilograham.github.io/rp2040-doom/speed_and_ram.html)
describes the tradeoff between storage size, decoding and cache churn. Its
reported 30–35+ FPS uses two cores and 270 MHz; it is not a target prediction
for a 33 MHz i960. Also, its alternative clipping has acknowledged subtle
sprite/wall differences, so the full rewrite does not automatically qualify as
pixel-equivalent to our renderer. [Author's introduction](https://kilograham.github.io/rp2040-doom/).

Preprocessing original assets into a versioned sidecar can preserve their pixels
while avoiding repeated runtime conversion. Keep the original WAD hash, tables
and conversion version; measure cold/warm data separately. Compression or tiny
packed representations trade RAM savings for decode cost. We have much more RAM
than a Pico, so their aggressive compression is not an automatic win here.
[next-hack's asset/transfer discussion](https://next-hack.com/index.php/2021/11/13/porting-doom-to-an-nrf52840-based-usb-bluetooth-le-dongle/).

## Measurement and implementation order

1. Freeze a current playable engine/kernel/module/WAD configuration and reproduce
   it across at least a simple room, a geometry/plane-heavy view and combat with
   sprites. Keep low detail, peer-yield and host-capture settings explicit.
2. Add bounded arithmetic counts and coarse cost categories: FixedDiv calls,
   BSP nodes/side tests, span/column pixels, visplane search probes, copies by
   site. Use minimal read-only hardware-time instrumentation; instrumentation
   overhead and IRQ time must be visible.
3. Build an exact FixedDiv candidate and separately qualify fixed specialized C
   columns. Then try span 1/2/4-pixel variants, followed by the PointOnSide fix
   and iterative traversal. Compare one change at a time.
4. Selectively tune compiler settings and private memcpy/memset. Try hashes,
   plane batching or prepared texture caches only if their measured work matters.
5. Offer smaller viewport/potato/flat-floor modes as explicitly selected options
   if maximum playability matters more than retaining the current picture.
6. Reserve a full deferred renderer for a separately budgeted rewrite after the
   smaller experiments establish the remaining bottleneck.

Use target A/B/B/A runs, time per frame plus delivered FPS and worst/p95 frame
time, fixed game-tic/input traces, and separate CPU render time from transport,
loading and browser display. Native host results prove correctness, not i960
speed. Preserve full audits, ownership, bounded IRQ/control latency, held-frame
STOP and drain. Demos can desynchronize from tiny arithmetic differences; the
RP2040 author reports this even for very small lookup-table changes. Keep exact
gameplay arithmetic and original tables until an independently validated change
is intended. Do not claim that uncapping FPS, dropping game tics, removing
checks or drawing on the host makes this i960 renderer faster.

No new claim of 10 FPS or a transferable 2× improvement is supported by this
research. It supplies ranked, testable work and the upstream/source evidence
needed for another chat to implement it.
