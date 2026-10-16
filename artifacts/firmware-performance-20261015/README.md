# Installed i960 firmware performance audit — 2026-10-15

All five requested areas were inspected offline against the installed DAC960PG
4.07-0-29 firmware, current RTEMS sources, archived target code and existing
physical measurements. This concerns our **i960RP RAID board**, not the PRO/100
adapter photographed in the earlier conversation. The latter is not attached
or dumped here.

The useful optimization leads are application copying and RTEMS worker CPU
allocation. No evidence supports reducing DRAM wait fields or enabling an
apparently disabled cache as a quick fix. There is **no newly measured speedup**
from this audit. No hardware, SSH, flash, service owner, DMA mapping, scheduler
or production runtime was changed. The pre-existing `game/doom/build.py` edits
and screen-copy experiment were left untouched.

## Reproducible evidence

Run from the repository root:

```sh
python3 host/audit/firmware_performance.py --out artifacts/firmware-performance-20261015/evidence
python3 host/audit/test_firmware_performance.py
```

The auditor pins firmware and disassembly hashes, matches the unpacked vendor
image to the installed dump, checks decoded four-byte rows against binary bytes,
and saves selected excerpts. It also checks the accepted ping-pong kernel
against its recorded archive hash and binary bytes. Counts: **73,608 runtime,
48,750 bootstrap, 3,701 boot-block and 42,444 accepted-kernel rows**. A byte check
does not make a linear disassembly a control-flow/reachability proof: strings,
compressed data, jump tables and x86 ROM content can decode as i960 opcodes.
Interpretations below are restricted to reviewed code paths.

Machine-readable findings and full input identities: [audit.json](evidence/audit.json).
The historical register pages are extracted as data without unpacking arbitrary
archive paths. They are from **October 11**, not a fresh measurement during Doom.
Sources may evolve; their audit-time hashes are also recorded.

Primary architecture reference: Intel *i960 Rx I/O Microprocessor Developer's
Manual*, 272736-002, [original PDF](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF),
§4.4, §6.2.23, chapter 12, §14.6–14.7 and chapter 20. The PDF was retrieved and
text-extracted during this audit. Applicable register tables take precedence
over the inconsistent bit-number sentence in §12.5.3: Table 12-4 defines
LMADR data-cache enable as **bit 1**.

## 1. Memory controller: already minimal programmed wait fields

The exact installed FWTCBBLK writes these values at `FEFFC4C8–FEFFC510`:

| Register | Boot value | Archived live value, October 11 |
|---|---:|---:|
| DBCR, `151C` | `00000B43` | `00000B4F` |
| DBAR, `1520` | `C0000000` | `C0000000` |
| DRWS, `1524` | `00000000` | `00000000` |
| DWWS, `1528` | `00000000` | `00000000` |
| DRIR, `152C` | `000000CC` | `000000CC` |
| DPER, `1530` | `00000001` | `00000001` |

All programmable read/write RAS-to-CAS, CAS-width and extra-recovery fields
are zero. These are minimum **field encodings**, not zero-latency DRAM. EDO
still has mandatory timing. Refresh is enabled with a 204-S_CLK interval;
at an assumed 33 MHz this is about 6.18 µs. That frequency conversion is an
example, not a newly calibrated clock. Parity is enabled with even polarity.
No refresh reduction or parity removal is warranted by this evidence.

DBCR changes during firmware sizing at `C004FC40`: `B4F` is installed at
`C004FCA0`; one branch installs `F5F` at `C004FD34`. `B4F` encodes two EDO
banks with 64 MiB-per-bank geometry, **not 128 MiB of fitted RAM**. Firmware
probes aliases and reports 16 MiB. The live capture's `B4F` is consistent
with this path. Do not replay destructive startup probing in occupied memory.

The earlier `257C203C/231C201C` board profiles concern an external-controller
path in the same firmware family. Board selector 6 and matching dispatch
pointers qualify this card's internal RP controller/CPU-XOR path. Applying
external-cache timing interpretations to this board would be a category error.

Evidence: [boot writes](evidence/boot-memory-cache.txt),
[sizing path](evidence/runtime-dram-sizing.txt),
[historical live registers](evidence/archived-register-pages.json),
[prior board qualification](../../rtems/residentnet/DECODE-BATCH.md).

**Decision:** preserve the working timing. Before any future memory experiment,
capture current DRWS/DWWS/DBCR during the exact Doom image and identify fitted
DRAM timing requirements. Zero wait encodings leave no simple field to decrement.

## 2. Cache and placement: enabled historically; templates matter

The archived positive-control page reports `dcctl 4` status **`00007221`**:
data cache enabled, consistent with the RP's 2 KiB direct-mapped data cache.
This disproves a blanket claim that the known runtime always leaves it disabled;
it does not establish current cacheability for every Doom address.

The main bootstrap writes `DLMCON=0`, `LMADR0=C0000002`,
`LMMR0=F8000001` at `FEFC810C–FEFC8124`, then enables D-cache. That template
makes `C0000000–C7FFFFFF` cacheable under the documented mask comparison,
while unmatched regions default to uncached. The boot block initially uses
the narrower `FF000001` mask. A runtime sizing branch can restore the wider
mask. **Do not infer that the C1000000 alias is uncached**: it lies inside the
wider template. These are observed writes, not a complete current two-template
snapshot; LMADR1/LMMR1 and later indirect writes must also be checked.

Data-cache enable bits do not control instruction caching. The existing upload
path invalidates data and instruction caches before entering new code. Keep
that lifecycle behavior; repeated invalidation inside a renderer hot loop would
be a separate cost to measure, not an optimization.

The RP uses write-through data caching and lacks snooping of other bus masters.
Therefore CPU writes being visible in RAM do not prove that CPU reads see DMA
updates. Keep completion, ownership and invalidation sequencing. Source bytes
and DMA-written destinations have different coherency requirements.

Evidence: [bootstrap cache setup](evidence/bootstrap-cache-clear-copy.txt),
`rtems/residentnet/upload.c`, `rtems/residentnet/cache_probe.h` and manual §4.4.
Previously observed PMCON words cannot establish bus width by themselves:
the archived BCON has the PMCON-valid bit clear. The old decoder already records
this limitation.

**Decision:** no global cache switch or alias remap. A future bounded experiment
should first record cache status, both logical templates and BCON at Doom entry
and during steady play. Then compare owned-buffer copies at fixed alignments
and sizes. A 16-byte bulk loop is worth measuring, but the manual alone cannot
prove it faster than the accepted word loop on this board.

## 3. Interrupts and DMA: retain asynchronous task ownership

Vendor `C004C8B8–C004C9A4` constructs DMA state, polls a hardware status bit,
calls a service routine while waiting, and conditionally invalidates D-cache.
That is evidence of vendor completion/coherency handling, not a recommendation
to reintroduce synchronous polling or call its routines from RTEMS.

Our later accepted task-owned asynchronous DMA improved maximum observed IRQ
gaps from roughly **111 ms to 11 ms**. Card-triggered ping-pong then improved
controlled delivered Doom FPS **3.503 → 3.887**, with host transfer/capture
**212.5 → 41.3 ms** and previous-publication wait **81 → 0 ms**. Those are
existing physical results, not results of this audit. WAD and framebuffer
traffic share DMA1; their explicit handoff is necessary. A second descriptor
queue cannot make that engine transfer both directions simultaneously.

In current `rtems/exclusive/runtime.c`, the real IRQ increments the tick,
polls control, advances RTEMS and dispatches only when dispatch-disable state
permits. The IRQ leave path scans per-owner stack guards. Existing CPU samples
are 10 ms attribution; they do not separate IRQ entry/exit, dispatch and task
cost exactly. No measurement here justifies removing those checks.

Evidence: [vendor DMA excerpt](evidence/vendor-dma-poll.txt),
[asynchronous acceptance](../dma-async-20261014/README.md),
[controlled ping-pong measurements](../doom-pingpong-20261015/README.md),
`rtems/exclusive/runtime.c` and `rtems/dma/pingpong/README.md`.

**Decision:** preserve task-owned DMA and short IRQ work. Next IRQ optimization
needs elapsed-time accounting around entry/body/dispatch/exit, with control
latency, worst IRQ gap, stack preservation and STOP tested alongside FPS.
The existing read-only timer-0 approach is preferable to reprogramming a timer.

## 4. Copy/clear routines: real remaining byte-oriented work

The accepted ping-pong kernel SHA-256
`13dc18948520e463f7312f77eacc1a51b52e23e7b46eb1f2b9b668f5f4d68261`
has actual byte loops in `_memset` at `C0F32AE0` and `_memcpy` at `C0F32B20`.
The implementation comes through `residentnet/libc.c → exclusive/libc.c →
switch/libc.c → irq/libc.c`. This is target-disassembly evidence, not merely
an assumption that GCC preserves a byte-oriented C source loop.

Vendor code uses several different strategies:

- Bootstrap clears its known aligned range with `stq` at `FEFC8160`.
- The selected CPU-XOR backend at flash `FEFCC540` / runtime `C000D540`
  uses `ldq`, word XORs and `stq` for aligned bulk work.
- `C004CA68` is a quadword fill loop. Its inputs/count/alignment contract must
  be recovered before treating it as a general memset.
- `C004CA7C` reads and writes the **same pointer**. It is not memcpy between
  separate buffers; do not transplant it as one.
- `C004CAC0` itself copies bytes. The vendor did not universally replace byte
  loops. The auditor lists 11 linear direct-call candidates to it; these are
  neither an exhaustive call graph nor a hotness measurement.

Evidence: [accepted compiled libc](evidence/accepted-kernel-memory-routines.txt),
[vendor routines](evidence/vendor-fill-refresh-byte-copy.txt),
[selected CPU XOR](evidence/vendor-cpu-xor.txt).

The already accepted WAD word-copy change reduced first-frame loading
**192.075 → 117.566 s**, warm restart **4.506 → 2.890 s**, and its three copy
categories **93.640 → 17.980 s**. Gameplay stayed about 3.8 FPS. This is strong
board-specific evidence for widening the right copies, not for expecting the
same percentage improvement in rendering.

**Decision:** finish the separate fixed-screen-copy qualification already in
progress, then profile remaining libc call sites before changing shared libc.
Any general replacement must handle zero length, all source/destination
alignments, exact prefix/tail bounds, byte truncation for memset, and memmove
overlap. Restrict wide accesses to normal owned RAM; do not change MMIO or
volatile hardware access widths. Native sanitizers establish bounds/correctness;
target disassembly and controlled on-card timing establish generated code/speed.

## 5. Background activity: RTEMS peer share, not stock RAID CPU work

The exclusive resident path installs its owned timer ISR, enables only mask
`2000`, switches to RTEMS, and never returns to normal firmware execution while
resident. Its failure path parks in control polling. Other PCI engines still
require explicit isolation/drain evidence; parked CPU code alone is not that
proof. The later DMA acceptance has the corresponding channel and secondary-
bus ownership checks.

Two workers are deliberately created at equal RTEMS priority **2**, both with
time slicing. Worker 0 handles peer/network/control work; worker 1 executes
uploads/Doom. The worker loops remain runnable. The existing low-detail report
attributes about half of renderer elapsed time to the Doom task, consistent
with this scheduling policy. This is not an exact measurement of peer busy
work or IRQ overhead, and does not promise a 2× FPS gain.

Removing vendor background routines is therefore not the first experiment.
An unbounded priority boost can starve worker 0, and naively blocking both
workers reaches an idle path which this runtime intentionally rejects because
it has no owned idle-task IRQ context. Keep both continuation owners and shared
heap service/drain behavior intact.

Evidence: `rtems/exclusive/runtime.c` (`Worker`, `Init`, `exclusive_resident`),
[sampled task attribution](../doom-detail-20261014/README.md),
[exclusive DMA contract](../../rtems/dma/README.md).

## Ranked bounded experiments

| Order | Experiment | Main evidence required |
|---|---|---|
| 1 | Finish existing fixed-screen copy comparison | Same engine/settings, deterministic pixels/palette, phase timings, full audits, held-frame STOP/drain |
| 2 | Measure task/IRQ/service time, then try a bounded peer-service budget | Doom FPS plus peer maximum service gap, network/control progress, IRQ gap and STOP; no unsupported idle transition |
| 3 | Selective libc copy/clear widening on measured call sites | Alignment/edge/overlap sanitizer corpus, target code inspection, exact output and controlled target timing |
| 4 | Read-only current logical cache/template snapshot; aligned word vs quadword microbenchmark | Same owned buffers, both cache state and templates, current image hashes, no DMA overlap or policy change |
| 5 | Retained WAD staging/direct owned-cache DMA/adaptive read-ahead | Separate cold load, warm restart and steady FPS; DMA1 handoff and unchanged full ownership/audit coverage |

Use matched scene, resolution/detail, checksum settings, audit cadence, WAD and
binary identities, ideally A/B/B/A. Report renderer CPU/wall, copy CPU/wall,
delivered frame intervals, cold load/upload separately, warm restart and worst
control delay. Existing independent improvements must not be multiplied together
as if measured in one combined build. Preserve the four known native/card pixel
differences as unresolved defects rather than suppressing them.

This audit completes inspection and identifies what is supported, rejected or
still unmeasured. It does not implement the ranked hardware experiments or
qualify a new scheduler/cache/memory policy. No current service state is claimed
from historical PID or restoration records.
