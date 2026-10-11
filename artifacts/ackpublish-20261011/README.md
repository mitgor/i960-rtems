# Combined ACK-and-PUBLISH — 2026-10-11

**Card acceptance passed on the first attempt:** four sessions, **586 native-matching
replies, 586 paired full-allocation audits, 452 paired targeted slot checks and
four clean RAM restorations/unloads**. The same 80 steady frames match byte-for-byte
across all four sessions. The public IPv6 web service is restored and returns 200.
All runs used boot `1e938df7-c454-479f-8e64-8ec7f754831e`. This task made no flash
changes and required no reboot; the parallel networking task rebooted before the
comparison began.

## Performance

Median of two session medians, milliseconds per rendered frame. Separate timing
adds the actual ACK(previous)+PUBLISH(next) pair before taking the median. Combined
timing covers its single callback. Both start from identical reset/seed state and
use the same 80 input frames; extra error tests are excluded.

| Interval | Separate ACK + PUBLISH | Combined | Reduction |
| --- | ---: | ---: | ---: |
| Kernel transaction | 39.958 | 25.078 | **37.24%** |
| Board.step wall time | 43.364 | 26.908 | 37.95% |
| Host process CPU during Board.step | 11.367 | 6.503 | 42.79% |
| Callback execution | 12.689 | 11.218 | 11.59% |
| Full read/audit | 23.203 | 11.606 | 49.98% |
| Targeted read/validation | 0.862 | 0.599 | 30.46% |

Individual kernel medians are 39.990/39.927 ms separate and 25.013/25.144 ms
combined. The dominant saving is avoiding a second full audit and transaction.
Full audit cost **per request** stays about 11.6 ms; occupied-slot integrity is
still checked before rendering, and publication retains its hash and guards.
Each request transfers 1,048,576 full-audit bytes plus its paired targeted reads.

These timings include host driver, firmware and polling costs, not target CPU
cycles. Post-Board.step oracle/archive compression work is outside the timed
window, and browser FPS was not measured. Component medians need not add exactly.
The combined queue remains opt-in: the earlier single-frame baseline was about
20.6 ms in a different batch, so this result does not establish that queueing is
faster than the non-queue renderer.

## Implementation

The opt-in `--queue-combined` target adds operation 4 to the accepted bounded
queue. It names an occupied slot, its acknowledged generation, and the next global
publication generation. All request fields, epoch/generation constraints and
occupied-slot integrity are checked before replacing the acknowledged slot. The
other slot stays unchanged. Rejected inputs mutate neither the queue nor renderer.
The renderer, hash, READY-last metadata and cache-return sequence are preserved.
No rollback or retry of an uncertain execution is introduced.

Both old and new targets use the **exact accepted v2 queue kernel module**,
SHA256 `3796b5cbeacb853d31c966defa0788fcd568886160725674f7d7011c77aef0fa`.
Every request retains all paired targeted checks and the complete paired 512 KiB
allocation audit, including application errors. A combined frame performs one
callback and one audit pair; the separate pair performs two. This changes the
number of transactions per frame, not the audit policy within a transaction.
The previous separate-operation queue and single-frame defaults remain available.

## Native tests and provenance

Mac and Linux tests pass 293 differential requests, identical 80-frame trajectories,
all 512 request-bit mutations (508 rejected without queue/renderer mutation), bad
lengths/capacity, generation exhaustion and 5,120 corrupt publication bytes.
Existing queue, targeted-read failure and generated-driver lifecycle tests pass.
The previous queue artifact set replays unchanged through the updated host scripts.

`builds.tar.gz` contains the exact combined target, ELF/map/disassembly, generated
profile, source-hash manifest, unchanged baseline target, unchanged kernel module
and generated source, and Linux build/native logs. `binary-sha256.txt` pins all
three binaries. Baseline target SHA256 is
`38f9969b2177b6cfd7e471eac939f6febd9bd0498292a7544c8122b199212776`.
The combined target is built from an isolated Git snapshot plus this task's files,
not the unrelated in-progress resident-network changes in the shared working tree.
Remote workspace: `/home/mit/i960-ackpublish-20261011-1acuXg`.

## Acceptance and saved evidence

Ran separate / combined / combined / separate with full audits, comparing
ACK(previous)+PUBLISH(next) against combined replacement. Both variants reset,
seed and then render 80 identical-input frames. Combined error cases exercise
empty-slot replacement, bad ACK/generation/epoch, malformed render/reserved fields,
full-queue replacement in both slots, duplicate replacement and stale old ACK.
Both variants closed with an unacknowledged publication. All full snapshots and
raw command sequences are archived. Independent replay reconciles **19,720
commands**, all model responses, all targeted slots and full audits, and verifies
identical actual frame bytes across the four sessions. Each separate session has
179 requests; each combined session has 114. Quiet-byte restoration also passes.

- `live.tar.gz`: four complete sessions, every full snapshot, raw command logs,
  replies, close captures, executed host scripts, preceding production close and
  restored production OPEN.
- `*-verified.json`, `*-quiet.json`, `comparison.json`, `archive-replay.json`:
  replayed counts, format-byte restoration and timing calculations.
- `native-*.log`, `build-replay.json`, `previous-archive-replay.json`: Mac/Linux
  tests, source/binary verification and prior-evidence compatibility.
- HTTP headers/body and service state: production `autonet` restored into
  `/home/mit/i960-rtems-web-20261011/http-after-ackpublish`.

Build metadata describes a build and remains `hardware_tested: false`; this ledger
and the exact matching live evidence supply acceptance.

```
make -C game/raycaster test-combined
python3 game/raycaster/combined/verify_archive.py artifacts/ackpublish-20261011
```

## Working progress and next step

1. Added an explicitly selected target transformation and independent host model;
   preserved the original queue source, module and default behavior.
2. Passed Mac/Linux sanitizer and differential tests, built in a fresh snapshot,
   archived exact binaries, and reproduced generated sources before hardware use.
3. Waited for the parallel networking run/reboot and its public HTTP restoration.
   Stopped the service cleanly and verified its original RAM restoration.
4. Completed all four sessions without retries, force-unload, flash changes or
   reboot. All closes restored even with unacknowledged frames.
5. Restored HTTP, archived every audit and replayed both current and prior evidence.

Next, profile occupied-slot verification and publication hashing separately, then
consider equivalent word-at-a-time validation while keeping every byte, guard and
hash check. Full paired audits remain required. Browser integration and autonomous
producer/consumer overlap are separate work; no relaxed audit policy or larger
RAM grant is established here.

The [protocol and reproduction instructions](../../game/raycaster/combined/README.md)
explain the accepted boundaries and reproduction steps.
