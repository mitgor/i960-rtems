# WAD-cache word copies — 2026-10-15

## Scope and acceptance plan

Replace only the actual engine cache's three copy loops: bounce to cache,
miss to caller, and hit to caller. Equal alignment uses an exact byte prefix,
aligned 32-bit words, then an exact byte tail. Unequal alignment stays bytewise.
There are no overreads, unaligned word accesses, or changes to cache geometry,
DMA, guard scans, ownership, allocation lifetime, read-ahead, or full audits.

Baseline: `../wad-profile-20261015/card-v2.tar.gz` (`live-profile3`), final
corrected cache instrumentation. Candidate uses the same profiling, low-detail,
no-FNV, direct-frame, WAD ring and ping-pong settings. Compare first-frame time
excluding upload, same-level warm restart frames 66–68, and frames 21–50 FPS.
The bounded 100-frame run includes held buffers, STOP, heap drain and full paired
audits. Compare the first 52 controlled frames with baseline and native oracle.
The four existing native pixel differences are not being fixed here.

Host tests cover all 16 source/destination alignments and lengths 0–1024 at
ASan allocation boundaries (16,400 cases), with profiling off and on, and
30,000 cache reads across 512/4096/65536-byte modes. Native engine runs must
repeat deterministically before physical acceptance.

## Measured results

| Measurement | Accepted byte-copy baseline | Word-copy candidate |
| --- | ---: | ---: |
| First frame after preparation (upload excluded) | 192.075 s | 117.566 s |
| Engine upload, separate | 80.113 s | 80.250 s |
| Same-level warm restart, frames 66–68 | 4.506 s | 2.890 s |
| Fixed-scene delivered FPS, frames 21–50 | 3.803 | 3.815 |
| Cache fill, complete run | 77.960 s | 14.480 s |
| Miss → Doom copy | 6.920 s | 1.940 s |
| Hit → Doom copy | 8.760 s | 1.560 s |
| Runtime WAD read, cache clock | 78.540 s | 78.100 s |
| Full paired audits | 89 | 68 |

First-frame loading is **38.79% shorter (1.63×)**, warm restart **35.86% shorter
(1.56×)**. Total cache copies fall **93.640 → 17.980 s**, an **80.80% reduction
(5.21×)**. FPS differs by only +0.31%; this is a loading improvement, not evidence
of a rendering speedup. Startup excludes preflight and engine upload. This is one
matched candidate versus the prior accepted baseline, not repeated statistical
qualification. Warm restart is the same controlled level, not every map/mod.

Same workload: 1,755 requests before first frame, 1,805 total, 38 on restart;
903 fills, 59,138,244 useful wire bytes, 14,753,444 bytes delivered to Doom.
The full-audit interval remains 3 seconds; fewer audit pairs reflect shorter
execution, not reduced checking. Timings include scheduling/interrupts, and cache
telemetry is quantized to 10 ms. Nested/overlapping timing categories must not be
summed as independent CPU costs. Warm-restart cache fill falls 1.660 → 0.300 s.

## Acceptance

100 physical frames, **68 full paired audits**, four full DMA/mailbox comparisons,
three-second held slots 17/18, held frames 99/100 across owned STOP, global heap
drain, and all 146 protected pages pass. First 52 controlled frames have identical
pixels/palettes to the accepted baseline and retain exactly the four known native
pixel differences (29260, 29261, 29580, 29581); palettes match native exactly.
Two native 52-frame runs are deterministic. ASan/UBSan and transport/ping-pong
checks pass. Linux and local Mac replay pass; tamper replay rejects 24 frame,
three WAD and six profile mutations. No checks were removed.

The HTTP observer received 97 frames; every payload matches the corresponding
capture. Mean fetch time is 28.33 ms, which is HTTP receipt time, not browser
paint latency. The bounded server closes at STOP; this is not an interactive
soak test. WAD ring/ping-pong remain opt-in.

`comparison.json` and `profile.json` provide exact timings; `system.json`,
`frames.json`, `wad.json`, `*-tamper.json`, `local-replay.log` and
`http-verification.json` provide acceptance results. `cache-disassembly.txt`
confirms aligned i960 `ld`/`st` in the copy loop. `source-check.json` verifies
791 archived source files against the working tree.

## Reproduction and artifacts

`build.sh` builds matching native/i960 engines, admission, resident kernel and
transport with profiling enabled. `native-frames.py` makes the independent
52-frame oracle. `run.sh` requires a released card and runs the bounded full-audit
loading test; inspect the actual owner before executing it. Do not force-unload
retained DMA mappings. `verify-remote.sh` runs physical replay and mutation tests.
Extract `candidate.tar.gz` and `card.tar.gz` together, then use `replay.sh` with
the extracted directory and pinned Freedoom WAD. `compare.py` additionally takes
the extracted prior `live-profile3`, new `live-copy`, and `--native native-frames2`.

The copied build dependencies are the accepted profiling baseline's `build2`;
the supplied scripts rebuild the engine/platform/admission/kernel/module, not
reuse the old admitted image. New authenticated artifacts:

- Kernel: `5d120cd478280848f73342a40bcced9ba633f7a8d22fac972b1702c0e6014697`
- Module: `61faf31c605e2aa7dfdf1905b63b780a969728f4cde84dd7e65cd2343d08cecf`
- Engine template: `8bbeef6ce3f4064b3b1cbfda5ebcfed203e10ab6ea9e1fb776ece80b4bd49dba`

RAM audit remains at 146 protected pages and 64 bytes of mutable reserve; the
upload helper is 28,576 bytes and the engine helper 22,080 bytes. The shared
cache probe also incorporates the new helper and passes the normal admission
and full-system replay.

Both archives have adjacent SHA-256 files. Candidate contains exact sources and
binaries; card contains complete captures and native oracle. Captures are closed,
copied, hash-checked and replayed locally before the normal reboot. No flash or
memory-map change. Public service restoration is recorded separately.

## Remaining bottlenecks

Target WAD reads remain about 78.89 s: full guard scans total 35.57 s, staging
copies 13.74 s, initialization 8.30 s, allocation/loans 6.26 s and release/returns
5.74 s (nested metrics, not an additive total). Normal DMA start-to-completion
intervals total 3.07 s. These are essentially the previous bottlenecks after
removing most cache copying. Next, qualify retained owned staging to amortize
allocation/initialization/loan costs, then direct guarded cache DMA and selective
read-ahead. Preserve STOP, ownership and full audits throughout.

## Public service restored

Normal reboot returned as `9bef2976-8b43-4c8d-bd4e-1e0b719249b7`.
Supervisor 2651 / relay 2653 now own `dac960auto`; the unchanged public IPv6
service returned HTTP 200, 2,891 bytes and RTEMS content from the Mac. See
`restoration.json`. The bounded Doom server on 8087 is closed. Recheck actual
ownership before another card run; these IDs describe completion of this batch.
