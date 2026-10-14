# DoomGeneric milestone 1: i960 compile and host memory profile

For the current playable RTEMS profile, use the [browser play guide](play/README.md).
The [October 14 bulk-transfer batch](../../artifacts/doom-bulk-20261014/README.md)
measured 0.999 FPS with full audits. Later DMA comparisons measured about
1.38 FPS. The [frame stress test](../../artifacts/frame-dma-stress-20261014/README.md)
now fixes a reproduced isolation-check halt during owned DMA, with 512-frame
physical acceptance. Re-run the Doom comparison before making DMA the default.
The original milestone below is historical.

**Completed 2026-10-11. No Doom code was loaded on the card.** All 80 selected
engine translation units compile with GCC 3.3.6 for i960RP and combine into a
relocatable ELF32 i960 object. Final linking intentionally fails on 58 missing
external symbols. `doom-engine.o` is an inventory artifact, **not firmware**.
The next target is a real runtime/platform link and application launch, followed
by headless i960 correctness testing.

**2026-10-12 follow-up:** [sprite sampling and deterministic output](DETERMINISM.md)
resolve the three differing frames. Current i960 static size is 627,096 bytes;
the tables below preserve the original milestone measurements. RTEMS now has an
accepted 8 MiB guarded application arena and resident segmented uploads.

**Allocation follow-up:** [runtime integration](runtime/README.md) passes 12,600
host frames and an actual-card 6 MiB allocation/resize/drain proof. The opt-in
combined object is 631,112 bytes and has 53 unresolved imports. Other runtime
services and arbitrary application launch remain.

## OS implementation path

The [RTEMS-to-Doom plan](OS-PLAN.md) orders the large-RAM allocator, segmented
loader, runtime link, host-backed WAD service, task/control integration and
correctness gates. The exclusive workspace/RAM experiments are separate from
this engine milestone. The later resident-upload profile now grants the requested
8 MiB arena; libc/task integration remains, and no Doom image has run on the card.

## Inputs and build changes

Engine: [DoomGeneric e257a095](https://github.com/ozkl/doomgeneric/tree/e257a09527062bfb986b6e5e0780839b6cbd5b71),
including its GPL-2.0-or-later source/license. Data: [Freedoom 0.13.0](https://github.com/freedoom/freedoom/releases/tag/v0.13.0),
both IWADs, with license and credits in the original release archive. No commercial
WAD is needed for these measurements. Inputs are preserved and SHA-256 pinned in
`build.py`, `run_profiles.py` and the artifact manifest.

The target uses `-mrp -Os -std=gnu99 -ffreestanding -fno-builtin
-fno-strict-aliasing -fcommon`, the existing patched newlib 1.11 headers, and small
`stdint.h`, `inttypes.h`, `strings.h` compatibility headers. ABI probes require
32-bit int/pointers/size_t and 64-bit int64_t. Target int64 field offset and sample
structure size are 8 and 16 bytes. The only remaining compiler warning is an
upstream unsigned-key `>= 0` check that is always true.

Both target and host use `CMAP256`, 320×200, sound disabled, and the original two source fixes (plus the subsequent bounded sprite sampling
fix documented in DETERMINISM.md):

- Allocate `DG_ScreenBuffer` using `sizeof(pixel_t)`: upstream reserves four bytes
  per pixel even in indexed mode. This saves 192,000 bytes of ordinary heap.
- Clear the initial internal video buffer so the startup wipe does not consume
  uninitialized pixels. The engine buffer is inside the zone; the output buffer
  is a separate ordinary allocation.

Host-only instrumentation tracks direct malloc/calloc/realloc/free/strdup requested
bytes, zone occupancy after every allocation, cache-pressure purges, read calls,
frame hashes and function-entry stack span. It does not belong in the target
image. Accounting unit tests cover allocation, zeroing, resizing/preservation,
free, strdup and failed overflowing calloc. The host binary is **32-bit Linux**,
using four-byte pointers; gcc-multilib was installed on the Linux host. Profiling
never acquired the card lock or changed its firmware/service. Parallel RTEMS
reboots interrupted builds; all accepted outputs were rebuilt/completed afterward.

## Measured memory

| Item | Bytes | Meaning |
| --- | ---: | --- |
| i960 text | 306,720 | Includes compiled engine code/constants in this section |
| i960 data | 69,888 | Initialized data |
| i960 BSS | 250,248 | Includes resolved COMMON storage (`ld -r -d`) |
| **Engine static total** | **626,856** | Excludes RTEMS, platform runtime, helpers, stacks and heap |
| Zone reserved | 6,291,456 | Source default, one contiguous ordinary allocation |
| Maximum direct allocation peak | 6,456,649 | Includes zone and output buffer; requested bytes only |
| Maximum outside-zone allocation | 165,193 | Already included in preceding row |
| Maximum non-purgeable zone occupancy | 2,211,560 | Includes block headers, not an additional allocation |
| Maximum total zone occupancy | 6,284,784 | Cache can consume almost all reserved space |
| Maximum host engine stack span | 5,856 | Instrumented x86 function entries; not an i960 stack bound |
| Largest observed WAD read request | 224,280 | Must be split across bounded transport windows |

The existing 128 KiB code window and 512 KiB total staging grant are both too
small. Even static engine storage alone exceeds 512 KiB by **102,568 bytes**.
WADs are about 28.8 MB each and must remain host-backed; no full-WAD RAM residency
is proposed. No claim is made that all 16 MiB of physical card DRAM is available.

The final baseline matrix comprises **20 workloads × 2,100 draws = 42,000 frames**:
Phase 1/2 DEMO1–3, Phase 1 E1M1/E2M8/E3M8/E4M1 and Phase 2 MAP01/MAP15/MAP30 at
6 MiB, DEMO1 at 2/3/4 MiB for each phase, and a repeated Phase 1 DEMO1 at 6 MiB.
These are capped prefixes, not complete demos or full-level traversal. Warp runs
have no player input. A synthetic clock makes these memory workloads fast; their
wall time is not a card speed estimate. `Z_CheckHeap()` runs at the draw cap.

Separate low-memory tests terminate with `Z_Malloc` errors: both first demos at
1 MiB and Phase 1 DEMO3 / Phase 2 MAP15 at 2 MiB. Thus first-demo success at 2 MiB
is not a suitable minimum-RAM guarantee. The stock timedemo fatal cleanup also
reports recursive `I_Error`/zero-tic timing; target fatal handling needs replacement.

### Repeatability follow-up

The original milestone retained three differing frames (497, 1426, 1817).
[The follow-up investigation](DETERMINISM.md) traces all three to negative
fixed-point sprite sample indices wrapping to 127, beyond their finite posts.
The current builder bounds masked sampling. Original evidence remains intact;
use the new corpus for host reference output. Target equality remains untested.

## Missing runtime functions

Exact symbol lists and calling objects are in the build archive's
`cross/i960/undefined.txt` and `runtime-callers.json`. ABI symbols have one extra
leading underscore; the JSON summary removes that decoration.

| Category | Count | Work required |
| --- | ---: | --- |
| `DG_*` platform hooks | 6 | Frame publication, keyboard, time, sleep, initialization, title |
| Compiler helpers | 9 | Signed 64-bit division plus eight soft-float conversions/operations |
| Newlib state/glue | 4 | errno, stream/reentrancy state, ctype table; or replace dependent libc paths |
| Allocation | 5 | malloc/calloc/realloc/free/strdup against an owned arena |
| Files/process | 12 | Read-only WAD service; explicit config/savegame policy; clean fatal/exit path |
| Formatting, strings, math | 22 | Implement/test required subset; reuse accepted copy/clear where applicable |

`__divdi3` comes from `m_fixed.c`. Soft-float callers include `g_game.c`,
`v_video.c` and `m_config.c`; a fixed-point renderer does not remove all floating
point. `system()` comes from desktop error-dialog code and should be removed from
the target error path. Existing RTEMS tiny libc supplies only a subset (such as
memcpy/memset/strlen/strcmp), not these 58 symbols as a complete linked runtime.
No fake platform implementations were used to conceal unresolved symbols.

## RTEMS handoff and reproduction

Read [RAM-CONTRACT.md](RAM-CONTRACT.md): request an **8 MiB owned arena** as a
provisional budget, including a 6 MiB zone, 256 KiB non-zone heap, 64 KiB game stack,
two frame slots, a 64 KiB WAD window and explicit runtime/guard allowances. The
original computed budget was 8,029,480 bytes; the sprite fix increases it to
8,029,720 bytes, leaving 358,888 bytes in an 8 MiB reservation.
Runtime/helper allowances are estimates; reject an oversized final link rather
than treating this proposal as permission to write card memory.

The isolated Linux workspace is `/home/mit/i960-doom-m1-eziNKY`. Reproduce in a
fresh directory with the pinned archives and the tools in this folder:

```sh
python3 tools/build.py --work cross --archive doomgeneric-source.tar.gz --target i960
python3 tools/build.py --work native --archive doomgeneric-source.tar.gz --target host32
python3 tools/run_profiles.py .
python3 tools/low_memory.py .
python3 tools/audit_runtime.py .
python3 tools/summarize.py . > summary.json
```

`--newlib` can point to another copy of the preserved patched newlib headers.
The cross prefix currently names the repository's established Linux toolchain.
The profile runner requires fresh run directories and a Linux multilib compiler.
This is not a Mac executable; verification below does not execute either binary.

[Artifacts and checks](../../artifacts/doom-m1-20261011/README.md):

```sh
python3 game/doom/verify_evidence.py artifacts/doom-m1-20261011
```
