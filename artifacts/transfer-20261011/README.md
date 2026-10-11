# Upload/arming profiles and faster validated framebuffer readback — 2026-10-11

**Complete:** five card sessions passed **2,105 native-matching replies**, 65
periodic full-allocation audits, five initial prefix snapshots and five full RAM
restorations/unloads. No flash changes or reboot occurred in this batch. The
production IPv6 page was restored and returned HTTP 200.

Detailed timing covers **43,904 STEP commands** across four controlled sessions.
The optimized host processing reduces full-frame kernel time by **3.61%** and
its readback/audit phase by **13.15%**, with identical requests, returned frames,
DMA read volume and validation coverage. This accelerates framebuffer readback
processing; it does not compress frames or reduce bytes transferred.

[Implementation, contract, tests and reproduction](../../game/raycaster/transfer/README.md)

## Where upload and arming time goes

Each ordinary frame makes 26 stock commands: three uploads, one callback and
22 reads. Every 32nd frame makes 28 commands for the full allocation. The first
request retains four additional cache-handshake commands. The profiler verifies
this exact opcode/count/offset sequence, not just command totals.

Median full-render command groups, combining the two baseline session medians:

| Group | Calls/frame | Bytes per call | Completion wait ms | Total ms |
|---|---:|---:|---:|---:|
| Request upload, opcode 21 | 1 | 12,384 | 10.604 | 10.730 |
| Result sentinel upload, opcode 21 | 1 | 16 | 10.079 | 10.209 |
| Dispatch-table upload, opcode 21 | 1 | 4 | 11.330 | 11.447 |
| Dispatch-table reads, opcode 20 | 4 | 4 | 0.364 | 0.809 |
| Result reads, opcode 20 | 2 | 16 | 0.156 | 0.368 |
| Callback, opcode 6f | 1 | — | 11.860 | 11.978 |
| Paired staging reads, opcode 20 | normally 16 | up to 61,440 | 9.369 | 10.845 |

Grouped columns sum work per frame before taking medians; they are not medians
of an individual read. Periodic full audits have two extra staging reads. First
entry is excluded from steady-state timing. Group medians need not sum exactly
to the median full transaction.

The three upload completion waits alone account for about **32.0 ms**. DMA-buffer
preparation and logging are measured separately and are much smaller (roughly
5–13 µs per upload stage/log in the baseline). Therefore shrinking a 12 KiB
request, removing logs or optimizing CPU copies cannot eliminate the dominant
cost of three separately completed uploads. The polling interval/timeout was
not changed. Wait includes firmware work, Linux polling and host scheduling;
it is not an isolated firmware timer or raw PCI bandwidth measurement.

The saved `firmware-dispatch.txt` independently maps vendor opcode 20 to
`c001fdb8 → c004ccb0` and opcode 21 to `c001fdc8 → c004cd00`, with controller
methods at offsets +e0/+e4. This is an offline lookup in the matching firmware,
not proof of the internal source of the measured delay. No fixed-delay bypass
or new firmware patch follows from these observations.

The sentinel, arming write and paired table/result reads remain necessary parts
of the current fresh-result/self-disarm contract. They were not omitted to make
a timing number smaller.

## Optimization and unchanged validation

Two host computations changed; the i960 payload is unchanged:

- An eight-byte arithmetic counter replaces the scalar DMA byte scan. It returns
  the exact number of bytes different from the fill pattern, including a byte
  tail. Both payload diagnostic counts and guard-corruption counts are preserved.
  Compiled Linux code uses ordinary 64-bit loads and integer arithmetic, with
  no per-word memcpy call or SIMD state requirement.
- Four `memcmp` ranges replace byte-at-a-time immutable-region classification.
  They cover exactly the original immutable bytes. An explicit maximum-output
  check also prevents invalid metadata from entering range arithmetic.

The full two snapshots still compare byte for byte, including mutable private
RAM. Code, both workspace guards, header/input, output tail/guards and periodic
full-allocation suffix remain checked. All request/sequence, opcode/address/size,
status/ID, DMA barrier, pending/uncertain-state and restoration gates are unchanged.
Ordinary paired staging reads still total **942,272 bytes**; every 32nd callback
reads **1,048,576 bytes**. The reply still contains 4,800 indexed pixels plus its
64-byte header. Audits were neither sampled less often nor replaced with hashes.

Detailed source comparison proves the two generated variants differ only in
these computations (plus the corresponding build-mode metadata). The final
coarse-profile module's generated source reproduces exactly. Compiler-generated
`.mod.c` symbol/version stubs are archived but are not policy-source comparisons.

## Repeated card results

All sessions use target SHA256
`8a19e5a357d3443721ee835d5fbdfd52ffd61710b339b8be9d74554d947da5e3`, the already
validated word-memory raycaster. Its ELF/map/source are preserved in
`../word-memory-20261011/word/`. No new target code was built for this milestone.

The controlled order was **baseline, optimized, optimized, baseline**, then a
final optimized run without extra command profiling. Each ran the same 421
requests: 160 full frames, forty partial batches, twenty each full/header-only
snapshots and 180 bounded memory/OS benchmark requests, plus reset.

| Full-render phase | Baseline ms | Optimized ms | Reduction |
|---|---:|---:|---:|
| Upload | 10.754 | 10.695 | 0.55% |
| Arming | 22.074 | 21.960 | 0.52% |
| Execute | 11.988 | 11.929 | 0.49% |
| Table/result verification | 0.829 | 0.606 | 26.82% |
| Paired readback/audit | **12.217** | **10.610** | **13.15%** |
| Kernel transaction | **57.830** | **55.742** | **3.61%** |
| Complete Board.step | 61.718 | 59.936 | 2.89% |

These are medians of the two independent session medians. Full-frame kernel
medians were 57.976/57.683 ms for baseline and 55.674/55.809 ms for optimized.
The final coarse build measured **55.642 ms kernel**, **10.507 ms audit** and
60.214 ms Board.step. Its single-run wall timing is not a separate controlled
speedup claim. No browser/compositor FPS measurement was made in this batch;
all returned frames were compared byte for byte with the native renderer.

The DMA scans for ordinary staging reads fell from about 1.119 to 0.438 ms per
full-frame group. A typical single small-command scan fell from about 82 to
28 µs. The kernel remainder outside `issue()` fell from 1.445 to 0.506 ms; it
includes immutable validation, copying and profiling logs, so it is not isolated
validator CPU time. Completion waits dominate the remaining cost. Changes well
below a millisecond should not be attributed to target OS speed or hardware
frequency; the target and its scheduling/benchmarks are unchanged.

## Tests, replay and service

ASan/UBSan passed on macOS and Linux:

- Every immutable byte of a 512 KiB response, all 8,193 output boundaries,
  metadata corruptions and randomized prefix/full differential comparisons.
- 528,384 pattern/offset/length counter cases and 65,536 adjacent-byte cases,
  compared with an independent scalar loop; inaccessible native guard pages.
- Three generated variants each passed 348 command-failure/timeout injections,
  stale/malformed requests and six output-corruption cases. This includes
  periodic full audits and final restoration/retention behavior.
- Existing raycaster and word-memory native tests passed on Linux.

All five live sessions restored the known complete staging image and temporary
runner/table/result regions, unloaded normally, and left the PCI function
unbound. Offline replay verified all 2,105 replies, the 65 periodic full audits,
the five initial prefix snapshots and the original production service close.
It also verified every profiled command sequence and recreated all timing
reports/comparison. Derived floating calculations permit 1e-12 relative/absolute
rounding differences across Python versions; raw replies remain byte-exact.

We waited until the parallel exclusive-RTEMS tests had recovered and verified
HTTP, then stopped `http-after-exclusive` normally. Its verified close is in the
live archive. After our last run, autonet restarted into `http-after-transfer`;
the Mac received HTTP 200. The boot ID throughout our five sessions was
`926ae76c-6a22-45fb-bd0c-e2cf93556afc`. Visitor logs were not collected.

Remote workspace: `/home/mit/i960-transfer-20261011-gvR3xq`.

## Preserved artifacts

- `kernel.bin`: exact unchanged payload; see the word-memory artifact for ELF,
  map and target source.
- `module-base/`, `module-fast-v2/`, `module-release/`: exact loaded modules,
  build-mode metadata, complete generated C/header/Makefile archives and Linux
  disassembly. `module-*.log` includes build output. The preliminary
  `module-fast.log` is a range-only development build that was never card-tested;
  it was superseded by the combined counter/range variant before optimized testing.
- `live.tar.gz`: all five complete captures and verified prior production close.
  Four contain complete command logs/rows in `commands.jsonl.gz`; release retains
  ordinary logs in its periodic audit/open/close captures, plus per-step phase
  timing, without extra CMDPROFILE rows.
- `*-verified.json`, `*-profile.json`, `*-commands.json`, `comparison.json`,
  `archive-replay.json`: byte-exact replay, command reconciliation and analysis.
- `native-mac.txt`, `native-linux.txt`, `native-ray.txt`, `live-*.log`: tests/results.
- `http-restored.*`, `service-state.txt`: restored service and actual HTTP response.
- `firmware-dispatch.txt`: limited offline dispatch findings and their scope.

## Next useful work

The next substantial reduction requires a protocol that amortizes the three
completed uploads, with explicit generations, request acceptance, result
freshness, self-disarm/stop and full validation retained. Design it separately
against the parallel ownership work; do not leave the current callback table
armed, remove sentinel writes, or infer DMA drain from a completed software call.
An owned batch/frame queue may help once those contracts are established. The
current optimized coarse module is suitable for this bounded raycaster path;
production networking and exclusive RTEMS need their own regression acceptance
before adopting it.
