# Slot validation and hashing — fifteen-step batch, 2026-10-11

**All fifteen steps completed.** Ten card sessions passed **1,691 native-matching
replies, 1,691 paired full-allocation audits, 2,506 paired targeted slot checks and
ten complete restorations/unloads**. All six release runs produced the same 80
steady frames byte-for-byte. Public IPv6 HTTP is restored and checked from the Mac.
All measurements used boot `39332cc7-b410-4d68-927c-d0398d95316a`.
This batch required no card-test retry, forced unload, flash change or reboot.

## Measured result

Target-only word hashing plus metadata/guard validation reduces kernel frame time
**25.165 → 24.158 ms (4.00%)**, callback time **11.219 → 10.081 ms (10.14%)**, and
Board.step wall time **27.257 → 26.224 ms (3.79%)**. Full paired audit cost remains
about 11.8 ms per request, using the exact same kernel module and byte coverage.

| Release candidate | Callback ms | Kernel ms | Board.step wall ms |
| --- | ---: | ---: | ---: |
| Accepted byte baseline | 11.219 | 25.165 | 27.257 |
| Word-loaded hash only | 10.188 | 24.174 | 26.328 |
| Hash + word metadata/guards | **10.081** | **24.158** | **26.224** |

Values are medians of two session medians, 80 identical-input frames per session.
Sequence: base / hash / words / words / hash / base. Individual kernel medians
were base 25.253/25.076, hash 24.080/24.268, words 24.252/24.064 ms. Host audit and
CPU variation are visible; **the 0.016 ms aggregate kernel difference between
hash-only and words is not a reliable incremental end-to-end improvement**.
Words is selected because it also has consistently lower callback time in both
runs and lower independently measured validation cost. Both candidates beat the
byte baseline, and both remain selectable opt-ins. No unvalidated candidate was
silently promoted, and no audit reduction was tested.

| Diagnostic slope, ms per repetition | Byte | Hash only | Hash + words |
| --- | ---: | ---: | ---: |
| 4,864-byte FNV | 1.755 | 1.317 | 1.317 |
| Full slot validation | 2.021 | 1.434 | 1.341 |
| Validation minus hash, estimate | 0.266 | 0.117 | 0.024 |

Word hashing is **24.97% cheaper**; full validation is **33.63% cheaper**. Fits use
five observations at each of 0, 1, 4, 8, 16 and 32 repeats, with interleaved count
order. Maximum median-point residual is under 0.024 ms. Subtracting slopes includes
compiler/loop differences and is not a pure guard-cost measurement. The two hash
passes predict about 1.118 ms saved, close to the observed 1.137 ms callback saving.
Timings include loop/check overhead and warmed data; they are not CPU cycle counts.

The post-Board.step oracle/archive work is outside its timing interval; these are
not browser FPS measurements. Full audit timing variation is not credited to this
target-only change. This queue is still opt-in and has not been shown faster than
the earlier non-queue renderer.

## Starting evidence

The accepted combined queue costs 25.078 ms/kernel frame: callback 11.218 ms,
full read/audit 11.606 ms, targeted read/validation 0.599 ms. Those measurements
come from `artifacts/ackpublish-20261011`, not a new unaudited measurement. Each
replacement checks its occupied slot, renders, and hashes the new 4,864-byte reply.
The next question is how much the two target-side hash passes cost.

The pinned baseline target is
`cd46d47e7e4fc02b68c12ee2a7046da4db7f861e90c71310ad29c61735d61c19`.
Every experiment reuses the exact accepted full-audit kernel module
`3796b5cbeacb853d31c966defa0788fcd568886160725674f7d7011c77aef0fa`.
No timeout, read coverage, equality, guard, ownership or restoration rule changes.

## Candidates and bounded measurement

- `byte`: the accepted reference slot code.
- `hash`: aligned word loads with the same serial FNV byte order, prefix and tail.
- `words`: adds exact word equality for guards and aligned metadata loads with
  an unaligned byte fallback. All original fields/bytes are checked.

Three separately built diagnostic targets support opcode 5: repeat hashing or
full slot validation 0–32 times, checking every result. Compiler memory barriers
prevent invariant hoisting; no timer/IRQ is borrowed. The complete queue and
renderer state stay unchanged. Repeated measurements at six counts estimate
cost slopes including loop/check overhead and warmed data. Release targets have
no diagnostic opcode. They are compared using the original combined-request
sequence, with identical keys and full audits after every callback.

Native tests cover reference equality over all 5,121 lengths at four alignments,
163,840 single-bit slot corruptions per candidate, metadata offsets, protected-page
tails, accepted combined request/rejection state preservation, 512 diagnostic
request mutations, the 67-request benchmark sequence and 806-request two-slot
stress sequence. Both release and diagnostic variants receive combined tests.
The stress sequence has eight epochs, 512 successful replacements, both slots
occupied, duplicate/stale requests, backpressure, and unacknowledged close.

## Artifacts and progress

`builds.tar.gz` contains all five target binaries, ELF/map/disassembly, generated
sources/source hashes, baseline binary, unchanged module and sources, and original
Linux build/test logs. `binary-sha256.txt` pins all seven binaries. The separate
`native-linux-final.log` and `native-mac.log` include the expanded final tests.
`build-replay.json` reproduces candidate source transforms and the unchanged module.
`diagnostic-request.dis` preserves the actual compiled bounded function.

Workspace: `/home/mit/i960-slotopt-20261011-V52780`. An initial Linux native/build
job was interrupted before any target build by a parallel-task reboot; its partial
log is retained. All five targets subsequently completed and their manifests pass.
A second parallel reboot delayed copying artifacts; it did not interrupt a card
test from this batch. Card access remained subject to the existing shared lock. We waited through the
parallel fault/NMI/RAM tests and their recovery, verified the clean production
close, then ran every card test on the first attempt in one boot.

`bench-live.tar.gz`, `release-live.tar.gz` and `stress-live.tar.gz` preserve all ten
sessions, every full audited snapshot, raw command logs, responses and closes.
The stress archive also includes executed suite/core host scripts, preceding
production close and restored production OPEN. Replay reconciles **59,284 commands**,
all quiet-byte checks, full snapshots and exact model responses. The final stress
snapshot has both slots READY; CLOSE still restores the entire original allocation.
`comparison.json`, `*-verified.json`, `*-quiet.json`, `selected.json` and
`archive-replay.json` hold reproducible results. `prior-combined-replay.json` confirms
compatibility with the earlier accepted evidence. HTTP headers/body and service
state document restoration into `http-after-slotopt`.

Build manifests still say `hardware_tested: false`, because they describe builds;
this ledger and hash-matched live captures supply hardware acceptance.

```
make -C game/raycaster test-slotopt
python3 game/raycaster/slotopt/verify_archive.py artifacts/slotopt-20261011
```

## Accepted scope and next step

Use `--queue-slots words` with the existing `--request-words --render-fast
--frame-queue --queue-combined` flags. Preserve byte/hash alternatives and the
single-frame default. Opcode 5 exists only with `--queue-diagnostic`; release
images do not contain it. The kernel module is unchanged. The queue stays inside
its original allocation and inherits none of the parallel task's broader RAM or
exception-ownership claims.

The next useful application step is connecting the accepted combined queue to the
browser bridge: acknowledge only fully verified frames, retain every full audit,
exercise keys/disconnect/close, and measure actual displayed frame delivery.
Further target micro-optimizations should be judged against the roughly 11.8 ms
full-audit cost that now dominates; do not remove checks to improve the graph.

See [the fifteen-step ledger](../../game/raycaster/slotopt/BATCH.md) and
[protocol/tests](../../game/raycaster/slotopt/README.md). All outcomes are backed by the preserved hardware evidence and complete local replay.
