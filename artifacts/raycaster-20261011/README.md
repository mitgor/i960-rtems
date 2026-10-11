# Raycaster hardware and profiling findings — 2026-10-11

The bounded fixed-point raycaster runs on Mylex/RTEMS and produces browser
output. **All 548 saved card replies match the native reference byte for byte.**
Both sessions restored the full saved RAM image and unloaded normally. Production
IPv6 HTTP returned 200 after restoration; no flash write or reboot was needed.

The parallel `leaseirq` hardware batch had completed and restored production
before these tests. The raycaster uses a separate bounded session, with no card
timer ownership changes. The profiling module only adds host timestamps; see
[instrumentation.diff](instrumentation.diff). The generated main driver, memory
policy and RIO validation header were byte-compared with the baseline.

| Session | Replies | Periodic full 512 KiB audits | Additional initial prefix snapshots |
| --- | ---: | ---: | ---: |
| Scripted rendering / OS benchmarks | 421 | 13 | 1 |
| Browser movement, turning and reset | 127 | 3 | 1 |

The scripted run includes 160 full renders, forty 10-column batches (five more
complete frames), forty snapshots and 180 benchmark requests, plus reset. The
browser trace includes initialization, 125 renders and another reset; thirty
requests contain held keys. These are reply counts, not 548 independent frames.
The two initial audit snapshots cover 471,136 bytes each, not a full allocation.
Both final close captures additionally prove full restoration.

## Measured frame path

Five host phases are measured with `ktime_get_ns()`. Values below are medians
in milliseconds; independently calculated medians need not sum exactly.

| Workload | Upload | Arm | Execution command | Verify | Paired readback / audit | Kernel total | Whole Board.step |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Full 80-column render, 4,864-byte reply | 10.74 | 22.05 | 14.19 | 0.78 | 12.60 | 60.38 | 65.15 |
| 10-column batch, 4,864-byte reply | 10.73 | 22.04 | 7.11 | 0.80 | 12.54 | 53.35 | 57.63 |
| Header-only snapshot, 64-byte reply | 10.75 | 22.06 | 5.05 | 0.82 | 14.53 | 53.21 | 58.55 |
| Full snapshot, 4,864-byte reply | 10.74 | 22.05 | 6.66 | 0.81 | 14.53 | 54.80 | 60.27 |

The full render's execution-command interval exceeds a full snapshot by about
**7.54 ms**. This includes ray traversal, filling the back buffer, publication
copy and frame hash. It is **not** an isolated measurement of ray arithmetic.
The command interval itself also contains host preparation, firmware dispatch,
completion polling and validation; no CPU cycle counter was used.

The image is only 4,800 bytes, but the ordinary paired staging reads total
942,272 bytes and every 32nd callback reads 1,048,576 bytes. That is roughly
196 times the image size for ordinary paired reads alone. Request upload and
arming together cost about **32.8 ms** per full frame. Therefore simply shrinking
the reply or optimizing the rasterizer cannot remove the dominant fixed cost.
No claim is made that the readback numbers measure raw PCI/DMA bandwidth.

Header-only versus full snapshots leave upload/arm/readback essentially the
same. The approximately **1.61 ms** execution difference closely agrees with the
measured cost of copying 4,800 bytes through the current byte-loop helper. It
saves card copy work, not the existing driver's fixed staging transaction.

The browser run delivered **10.18 host responses/s** over 12.28 seconds, with
65.31 ms median backend callback duration. This includes the browser's pacing,
SSH tunnel and request scheduling. It is a short observed response cadence,
not a sustained FPS promise or a browser compositor measurement. The lower-level
write/read trace had a 60.47 ms median and 79.37 ms maximum in that session.
The scripted suite's maximum was 312.64 ms during bounded repeated benchmarks;
that is not the normal frame latency.

## Existing runtime helpers on the i960

Each estimate fits four batch sizes (1, 16, 64, 128), five measurements per size,
after subtracting empty-benchmark medians. Setup/checksum costs stay in the fit
intercept. Every result/digest matched host libc/reference semantics.

| Routine / workload | Estimated time per operation | Effective payload rate |
| --- | ---: | ---: |
| memcpy, 4,096 bytes aligned | 1,358 µs | 2.88 MiB/s |
| memcpy, 4,096 bytes at offset 1 | 1,358 µs | 2.88 MiB/s |
| memset, 4,096 bytes | 861 µs | 4.54 MiB/s |
| memmove, 4,096 bytes overlapping by 1 | 2,007 µs | 1.95 MiB/s |
| memcmp, 4,096 equal bytes | 1,770 µs | 2.21 MiB/s |
| strlen, 4,095 nonzero bytes | 896 µs | 4.36 MiB/s |
| RTEMS semaphore request/reply roundtrip | 102.4 µs | Includes two task handoffs and semaphore operations |
| rtems_clock_tick, otherwise idle watchdog queues | 4.96 µs | Software tick call, not ISR entry/exit |

All fits have R² above 0.9994. The tick estimate is resolved by batching; its
single-call subtraction is slightly negative because of timing noise. Do not
interpret subtracted single samples as negative execution time. Memory helper
rates count logical payload bytes, not both read and write bus traffic.
Aligned and unaligned memcpy are equally slow because this profile uses the
same byte-at-a-time routine for both. Repeated buffers/code are reused within
a callback; these are not cold-cache, interrupt-loaded or DMA-contention tests.
Current CPU frequency and cycle counts are still not established by this work.

## What to optimize next

1. Prototype aligned word-copy/clear paths with byte prefixes/tails and proper
   overlap handling, in a separate test profile first. Cover offsets, zero/short
   lengths, tails, both overlap directions and guard boundaries before card
   benchmarking. Keep generic fallback routines. Frame publication/output copies
   are measurable beneficiaries; scheduler rewrites are not the first priority.
2. Investigate the 10.7 ms upload and 22.0 ms arming costs before changing audit
   cadence. Measure the constituent firmware commands. A small response alone
   cannot remove their fixed protocol work.
3. Design a validated frame queue/lease with generations, bounded backpressure
   and explicit host/card ownership, aligned with the parallel renewable-lease
   work. Batch frame metadata/data or use owned host buffers once completion and
   teardown are proven. Do not claim a software lease proves physical DMA drain.
4. Keep larger-RAM reservation and Doom runtime services as separate gates.
   This raycaster fits the current allocation; a multi-megabyte Doom heap does
   not. The renderer itself should be optimized only against another recorded
   workload/profile, with unchanged output or explicit visual tradeoffs.

This milestone profiles existing helpers; it does not replace them, change
firmware, relax validation or claim unrestricted resident execution.

## Reproduction and artifact contents

Source/commands: [game/raycaster/README.md](../../game/raycaster/README.md).
Isolated remote workspace: `/home/mit/i960-ray-20261011-AesT6N`.
Target: 23,792 text + 468 data + 71,040 BSS bytes, 202,596-byte flat extent.
Payload SHA256:
`47046f511b683911df78a329985efba067836e982c0f42ec1a5d863e8d8242a5`.

- `kernel.*`, `build.json`, `raycaster-build.json`, `target-source/`: exact target,
  source identities, code/section maps and disassembly. The manifest's
  `hardware_tested: false` records build-time status, before the subsequent runs.
- `dac960rtems.ko`, `module-source.tar.gz`, `module-build.log`: actual profiling
  module and generated source. Normal compiler-name/BTF-availability notices are
  preserved. `instrumentation.diff` records its complete session-code change.
- `raycaster-live.tar.gz`: full scripted and browser capture directories, paired
  reads, traces, audits, summaries, and browser timing samples. No visitor logs.
- `phases.json`, `profile.json`: per-call timings and reproducible analysis.
- `live1-verified.json`, `live-web-verified.json`, `browser-profile.json`: replay,
  audit/restoration results and observed host response cadence.
- `build-verified.json`, `native-mac.txt`, `native-linux.txt`: build identities and
  passing sanitizer plus six Python tests on both hosts.
- `card-browser.jpg`: real card output after movement/turning; reset was checked
  separately in the DOM and replay. `http-restored.*`: restored IPv6 HTTP 200.

Extract the live archive into a fresh directory. Run `verify_card.py CAPTURE
--payload artifacts/raycaster-20261011/kernel.bin --module
artifacts/raycaster-20261011/dac960rtems.ko`, adding `--browser` for `live-web`.
Run `profile.py artifacts/raycaster-20261011/phases.json` to recreate profile.json.
The verifiers check exact native replies, source/binary identities, proper audit
lengths, RIO immutable regions and full restoration; it also ties timing-row
headers to the replayed replies. No hardware is accessed during replay.
