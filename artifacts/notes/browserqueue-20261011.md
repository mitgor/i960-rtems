> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Browser queue integration — 2026-10-11

The accepted combined queue now drives the browser with complete audits retained.
This batch changes only host/browser software: no card image/module changes,
flash writes, reboots, new RAM claims or asynchronous producer assumptions.
Contract and reproduction: [bridge README](../../game/raycaster/browserqueue/README.md).

## Accepted evidence

Seven sessions pass **663 replies and full paired allocation audits**, **640
paired targeted slot reads**, **22,608 commands**, and seven complete RAM/code/
table/UART restorations, module unloads and unbound-device checks. Chromium drew
640 frames across two four-run ABBA comparisons, checking movement, turn, reset,
blur, opaque pixels and exactly one request in flight. Reset draw replies are
synthetic deterministic reset images after audited ACK/INIT; rendered frames
come from paired card slot bytes and match the independent native renderer.

| Capture | Requests / full audits | Outcome |
| --- | ---: | --- |
| Baseline browser, gzip 9 | 325 | 320 draws, graceful SIGTERM close |
| Idle expiry | 1 | No rendered frames; close after one second idle |
| Frame limit | 3 | Two rendered frames, automatic close |
| SIGTERM during combined request | 3 | Second response completed, then close |
| TCP reset during combined request | 3 | ConnectionResetError, no retry, verified close |
| Fast archive browser, gzip 1 | 325 | 320 draws, graceful SIGTERM close |
| Fast archive TCP reset | 3 | ConnectionResetError, no retry, verified close |

The expected nonzero exits on TCP reset are HTTP failures, not failed card
restorations. Every completed card request in those sessions passed replay.
No device fault or recovery reboot occurred in this batch. The earlier parallel
heap/network test finished before this batch acquired the card; all seven runs
use boot `23b38c34-f329-496a-9f41-c462f825e766`.

## Performance

Both compression variants use the exact same accepted payload and kernel module.
Each variant runs 80 draws in each of four ABBA pacing trials. Summaries exclude
the first five draws per trial and reset draws; raw samples remain included.

| Metric | Original host path | Accepted host path |
| --- | ---: | ---: |
| Full audit compression/write, ms | 21.606 (gzip 9) | 5.940 (gzip 1) |
| Kernel request, ms | 24.422 | 24.469 |
| Card execute phase, ms | 10.017 | 10.018 |
| Full paired audit phase, ms | 11.912 | 11.923 |
| Canvas interval, ms | 102.175 (16-ms delay) | 76.336 (animation-frame pacing) |
| Observed delivered frames/s | 9.787 | 13.100 |

Compression/write cost falls **72.51%**, while total observed delivery rises
**33.85%**. With compression held at level 1, pacing alone reduces draw interval
86.307 → 76.336 ms. With animation-frame pacing held fixed, compression reduces
92.673 → 76.336 ms. These are host/browser measurements, not i960 CPU cycles or
physical display scanout. The controls use the same script but input transitions
can differ by a few frames; timings vary and are not cycle-identical workloads.
The unchanged kernel/execute/audit times support the host-side explanation.

Every request retains a full 512-KiB snapshot after both physical reads matched,
plus targeted bytes and raw command logs. Across seven runs that is 331.5 MiB of
uncompressed full snapshots. Lower gzip compression changes stored size and CPU
cost, not read coverage or replay requirements. The online and offline checks
still compare exact bytes; checksums do not replace them.

## Files and reproduction

- `browser-builds.tar.gz` / `browser-live.tar.gz`: exact baseline executed sources,
  accepted binaries, Linux native results, five captures and production close.
- `browser-fast-builds.tar.gz` / `browser-fast-live.tar.gz`: accepted gzip-1 sources,
  unchanged binaries, Linux tests, two captures and preceding production close.
- `source-manifest.json`, `fast-source-manifest.json`: source/reference hashes.
  Archives include original Fujitsu inputs needed by the independent UART check.
- `binary-sha256.txt`: unchanged payload `3c6f40e4…` and module `3796b5cb…`.
  Full target build provenance remains in `artifacts/slotopt-20261011/`.
- `card-browser/`, `fast-card-browser/`: all draw samples and full-page screenshots.
  `profile.json`, `fast-profile.json`, `comparison.json` join update IDs to host
  timings and retain kernel/oracle/readback/archive/slot/log timing breakdowns.
- `*-verified.json`, `*-quiet.json`, `archive-replay.json`: independent replay.
  `tamper-tests.json`, `fast-tamper-tests.json` reject eight altered capture classes.
- Native tests cover all control masks, consecutive resets, audit corruption,
  uncertain timeout/no-retry, HTTP disconnect, idle/frame limits and in-flight
  SIGTERM. `command-reference-check.json` compares the adapter schedule to all
  114 accepted physical requests from the preceding slot optimization batch.
- `http-headers.txt`, `http.html`, `service-state.txt`: final public IPv6 HTTP 200,
  Vader/system information and active production service. The raycaster bridge
  was loopback-only through SSH and is now closed.

```sh
python3 game/raycaster/browserqueue/verify_archive.py artifacts/browserqueue-20261011
```

Replay compiles the unchanged native oracle from each archived source tree,
checks pinned binaries and manifests, replays every snapshot/command/transition,
verifies exact restoration, checks UART preimages and recreates timing reports.
A malformed immutable-memory capture correctly raises the existing ValueError;
the tamper harness recognizes that alongside assertion failures.

## Remaining work

Measure metadata serialization and repeated request/phase-history rewrites next.
They are outside the five explicit host stage intervals; residual request time
is not yet uniquely attributed. An append-only journal could reduce that work,
but must retain every intent/result and reject incomplete or truncated captures.
The larger Doom framebuffer/heap plan, asynchronous ownership, multi-client
sessions and long-duration browser service are separate work. Native simulation
remains the default backend; this opt-in queue still uses bounded callbacks.
