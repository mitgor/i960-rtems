> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Bounded frame queue — 2026-10-11

## Result

The corrected two-slot cooperative RTEMS queue passed **four card sessions,
518 native-matching replies, 518 paired full-allocation audits, 202 paired targeted
slot checks and four complete restorations/unloads**. Every request reads the
entire 512 KiB allocation twice; queue reads are additional. No flash changes,
new RAM grant, autonomous rendering or reduced-audit mode were tested.

The first queue attempt exposed a host-driver allocation bug and required a
reboot. It is preserved separately and is not counted as a successful session.
The final four sessions all used boot `623293bc-618f-4c8b-bca4-58dba212e849`.

## Performance

Median of two session medians, milliseconds, 80 identical-input steady frames
per session. The baseline also audits the full allocation on **every** request;
its numbers are not directly comparable to earlier periodic-full-audit results.
For a queue frame, both its PUBLISH and separate ACK must be paid for.

| Measurement | Baseline frame | Queue PUBLISH | Queue ACK | PUBLISH + ACK |
| --- | ---: | ---: | ---: | ---: |
| Kernel transaction | 20.596 | 22.996 | 16.982 | 39.947 |
| Board.step wall time | 23.286 | 24.863 | 18.630 | 43.529 |
| Host process CPU during Board.step | 6.765 | 6.154 | 5.084 | 11.275 |
| Callback execution interval | 7.352 | 9.185 | 3.510 | 12.689 |
| Targeted read/validation | — | 0.591 | 0.250 | 0.836 |
| Full read/audit interval | 11.582 | 11.609 | 11.598 | 23.202 |

Combined columns are medians of actual frame/ACK pairs, so they need not equal
sums of independently calculated medians. Host timestamps include driver,
firmware, polling and validation costs; they are not target CPU cycle counts.
The additional archive compression and model replay after Board.step are outside
its timing window. These are transport timings, not measured browser FPS.

The queue currently costs **93.96% more kernel time per frame**. A successful
single-ready-slot targeted read transfers only 10,368 bytes in two descriptor and
two slot reads, but each request still transfers 1,048,576 bytes for its full
pair. PUBLISH also adds slot metadata, hashing and guard work. ACK validates the
occupied slot again and incurs its own callback and full audit. This prototype
establishes ownership/backpressure correctness; it is not a performance release.
Keep the previous optimized single-frame path as the default.

## Protocol and coverage

Two 5,120-byte slots at staging offset `0x60000` fit inside the existing mutable
allocation, below the transport block. A linker assertion prevents the target
image/BSS from overlapping them. Each slot has an epoch, monotonically increasing
generation, fixed length, READY-last marker, slot identity, complemented generation,
FNV corruption check, exact guards and the unchanged 4,864-byte RAY1 response.
The host reads after callback return and cache maintenance. It requires paired
bytes to match the full audited snapshot and the unchanged native renderer before
ACK. The READY store is not an asynchronous DMA/cache protocol.

Each queue session exercises full-queue refusal, occupied reset refusal, wrong
epoch/generation ACKs, duplicate ACK, stale publication, out-of-order slot ACK,
new-epoch reset, 80 steady frames, and CLOSE with a final unacknowledged frame.
Each baseline has 81 requests; each queue has 178. Complete archived command
sequences account for **16,720 commands** in the accepted batch.

Native ASan/UBSan tests also cover generation exhaustion, malformed requests,
insufficient output capacity, incomplete publication, 40,960 single-bit slot
corruptions, all six new read failure/timeout boundaries and 10,304 targeted/full
byte mismatches. The C queue matches the independent Python ownership model and
native renderer for all 178 requests. The generated-driver regression executes
its actual allocation, publication, copy, read_pair and cleanup fragments for all
60 captures and all 60 allocation-failure positions, including rejection before
DMA when capture storage is absent or undersized. Inherited quiet/session fault
tests pass, preserving the first-entry cache ordering and uncertain-DMA policy.

## Failure and correction

The v1 module expanded `capture[54]` to `capture[60]` but left allocation,
debugfs publication and cleanup loops bounded at 54. The earlier helper-level
mock supplied its own buffers and missed that integration error. The first
64-byte descriptor read reached `memcmp(NULL, NULL, 64)` in read_pair and faulted
the host kernel. No queue request completed its full audit. Its OPEN, kernel oops,
partial trace, exact module and target are preserved in `failed-v1.tar.gz` and
`builds.tar.gz`. An 81-request baseline immediately before it had passed.

The corrected builder derives all three loop bounds from ARRAY_SIZE and refuses
invalid capture storage before issuing paired reads. The new lifecycle regression
would reject the original generated driver. No force-unload was attempted. The
host was rebooted, returned with a new boot ID, and then passed the entire fresh
baseline/queue/queue/baseline batch. No clean CLOSE is claimed for the faulted run.

## Artifacts and replay

- `builds.tar.gz` and `binary-sha256.txt`: original exact queue target, accepted
  baseline target, baseline module and **failed v1 queue module**, generated
  sources, source hashes, ELF/map/disassembly and build logs.
- `corrected-build.tar.gz` and `corrected-binary-sha256.txt`: accepted v2 module,
  generated sources, corrected builder/test sources and Linux build/test logs.
- `failed-v1.tar.gz`: first baseline and failed queue attempt, kernel oops and
  partial logs; retained as failure evidence.
- `live.tar.gz`: all four accepted sessions, every full snapshot, replies,
  command logs, close captures, preceding production close and restored HTTP OPEN.
- `*-verified.json`, `*-quiet.json`, `comparison.json`: independently replayable
  acceptance counts, quiet-byte checks and timing calculations.
- Native logs record Mac/Linux sanitizer and inherited fault tests.
- HTTP headers/body and service state document the restored public service.
  The first service start encountered an occupied lock before opening the card;
  `http-first-start.log` preserves that refusal. A fresh output directory was used
  after the lock became available.

Remote workspace: `/home/mit/i960-framequeue-20261011-6UXJme`; accepted captures
are under `acceptance-v2`. Production remains the existing `autonet` target.

```
make -C game/raycaster test-queue
python3 game/raycaster/queue/verify_archive.py artifacts/framequeue-20261011
```

## Next step

Add an explicit combined ACK-and-PUBLISH request to amortize one callback and one
full audit, initially retaining the same complete audit on **every request**.
Define validation/commit ordering so a stale ACK or malformed publication changes
neither ownership nor renderer state. Test full queues, out-of-order ACKs, wrap,
reset, cancellation/close and uncertain completion against the independent model,
then repeat the same card A/B measurements. Profile slot hashing separately before
optimizing it. Autonomous producer/consumer overlap, browser integration and any
replacement for full immutable-memory auditing remain separate unproven steps.
