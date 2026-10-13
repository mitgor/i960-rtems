# Confirmed BSP comparison miscompilation — no deployed Doom fix

The exact `engine-cross/i960/r_main.o` is in `build-evidence.tar.gz`; its full
relocated-symbol disassembly is `r-main-disassembly.txt`. In `R_PointOnSide`, the
vertical-line path contains:

```asm
0x0fc: cmpi   g4,0             # g4 = node->dy
0x100: cmpibl g5,g0,0x178      # g5 = node->x; g0 = x
0x104: b      0x128
0x128: testg  g6
```

The source requires `node->dy > 0` when `x <= node->x`. For the root node of E1M6,
x is 0, node x is 1792, and dy is −128 (coordinates scaled by 65,536). The first
comparison is less-than. The compare-and-branch is not taken, but its comparison
is greater-than. `testg` then consumes that newer result, returning 1 where the
source requires 0.

Intel's *i960 Processor Assembler User's Guide*, section “Compare and Branch”,
printed page 7-29, specifies that these instructions update the condition code.
[Primary Intel guide, mirrored PDF](https://datasheets.chipdb.org/Intel/80960/manuals/48527607.pdf).
The corresponding horizontal-line path has another `cmpi` / `cmpibge` / `testg`
ordering. The upstream [GCC 3.3.6 i960 backend](https://raw.githubusercontent.com/gcc-mirror/gcc/releases/gcc-3.3.6/gcc/config/i960/i960.md)
is a starting point for checking condition-code dependencies; it is not proof
of every patch/configuration in our installed compiler.

`inspect_spawn_map.py` has two explicitly labelled offline modes:

- Source semantics: subsector **226**, sector **0**, floor **0**, ceiling **192**,
  stationary view height **41**. This matches the native trace.
- `--compiled-axis-cc`: follows the two captured axis-aligned instruction paths,
  with compare-and-branch updating flags. It reaches subsector **1394**, sector
  **82**, floor **−72**, ceiling **96**, view height **−31**. These all match the
  physical trace. The first wrong decision is at root node **1396**.

Both modes use the same pinned WAD and otherwise the same explicit signed
32-bit/fixed-point calculations. The model does not execute the i960 binary or
prove the entire compiler correct/incorrect. Nevertheless, the captured sequence
has a concrete condition-code dependency problem under the documented ISA, and
predicts the observed wrong spawn exactly. Correct scalar layout, correct WAD
bytes and matching decoded sector-height fingerprints do not cure that problem.

## Focused hardware proof

After the retained Doom session was archived and rebooted, `branch_probe.py`
compiled the same `R_PointOnSide` source into three small scalar payloads. It
asserted that the optimized function's **160 object-text bytes** exactly equal
those in the real Doom object. Normal linking resolves its two `FixedMul` calls;
the tested body is not a handwritten approximation. The payload entry is first,
rejects indexes outside nine vectors, has no BSS and returns without a loop.

Each variant ran all nine vectors through the established stock-firmware RAM
loader, outside RTEMS and without WAD traffic. Results:

| Variant | Wrong cases | Correct / tested |
| --- | --- | --- |
| Original optimized flags | 0 and 5 | 7 / 9 |
| Both scheduling passes disabled | 0 | 8 / 9 |
| Same source at `-O0` | None | 9 / 9 |

Case 0 is the actual E1M6 root-node decision: source expects 0, optimized code
returns 1. Case 5 is a horizontal-line decision requiring 1 but returning 0.
The other cases include equality, both direction signs and a fixed-multiply path.
All **27 transactions / 2,970 firmware commands** passed complete paired staging,
code/result, restoration and health checks and unloaded cleanly. Independent local
replay rechecks all 81 paired 512 KiB staging phases, request/module identities,
results and command sequences (`branch-probe-replay.json`). See
`branch-probe-evidence.tar.xz` for exact source, three binaries, disassembly,
generated module and all raw captures.

This confirms an optimized function miscompilation on the real card, independently
of RTEMS preemption, WAD transport, allocation, and Doom's height update. Turning
off scheduling alone is **not a fix**. `-O0` passing these nine vectors is not
full-engine acceptance, a global compiler guarantee, or a performance result.

## Next correction

Audit the installed backend's condition-code definitions/effects for compare/branch
and bit-branch instructions. Prototype a compiler dependency fix or a narrowly
verified implementation, then expand the bounded hardware vectors before rebuilding
Doom. Preserve accepted kernel/toolchain binaries; do not silently change global
compiler flags. Repeat native determinism, all ABI/link/placement gates and complete
N3 normal/STOP/normal/drain acceptance after any correction. The full Doom image
and RTEMS kernel have not been rebuilt or deployed with a proposed fix here.

The render-to-frame hang is **not** proven to share this cause. The latest run
retrieved stage 43 (planes complete), but not stage 44 or any new stage 81–98.
The previous run retrieved stage 44. A recorded callback can be newer than the
last record copied to the host, so absence is not a fault-PC measurement. A next
hang probe needs bounded host-confirmed checkpoint draining at selected boundaries
or an independently readable fault/log capture, with STOP/deadline tests and all
existing audits retained. It must not silently turn the current nonblocking
checkpoint callback into an unlimited wait.
