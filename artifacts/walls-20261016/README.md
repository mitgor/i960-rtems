# Wall-region profiling and selective r_segs optimization

Implemented independent opt-in `--wall-profile` and `--fast-walls` switches.
The latter compiles only r_segs.c at O2, including masked-segment drawing. Both
remain **off by default**. Exact FixedDiv remains the playable default; these
benchmarks explicitly enable C columns, two-sample spans and fixed low detail.
No renderer approximation, firmware write, ownership change or audit reduction.

## Matched result

One plain control P0, then profiled A/B/B/A, 520 frames each. Timing uses every
frame 100–499, with no exclusions: 800 frames/798 intervals per profiled variant.
A uses the current size optimization for r_segs.c; B uses O2. See [plan](PLAN.md),
[comparison](comparison.json), [all timing windows](timing.json) and
[partitioned regions](regions-pooled.json).

| Metric | Profiled A | Profiled B |
| --- | ---: | ---: |
| Host FPS | 6.32306 | 6.35817 |
| Renderer wall | 139.1875 ms | 138.2000 ms |
| Sampled renderer CPU | 136.5625 ms | 135.5750 ms |
| Coarse BSP/walls | 81.5125 ms | 80.5625 ms |
| Planes | 40.2000 ms | 40.3250 ms |
| Sprites/masked | 17.4750 ms | 17.3125 ms |
| Completion observed → HTTP availability | 4.8246 ms | 4.9727 ms |

Observed gain: **+0.555% FPS**, renderer **0.9875 ms sooner**. Per-run FPS:
A1 6.32708, B1 6.36137, B2 6.35498, A2 6.31904. This is a small measured gain
in this workload, not a general performance guarantee. No transport-latency
improvement is demonstrated; HTTP availability is not browser paint latency.
Keep the optional candidate, but qualify it without profiling before promotion.

The single plain control measured **6.42698 FPS**, renderer **136.475 ms**.
Compared with pooled A, profiling costs about 2.71 ms of renderer time and 1.62%
of FPS. This is a single plain run against two profiled runs, not a matched
uninstrumented optimization comparison. Normal play keeps profiling disabled;
**uninstrumented fast-walls FPS has not been measured on the card**.

## Where the combined BSP time goes

Four inclusive, nonrecursive elapsed brackets use the existing 4,166,700 Hz
free-running downcounter: BSP root, subsectors, StoreWallRange and RenderSegLoop.
Subtract nested brackets to partition the work; recursive BSP calls are untouched.
The original coarse BSP counter also includes work outside the root call.

| Partition | Profiled A | Profiled B |
| --- | ---: | ---: |
| Traversal/culling outside subsectors | 4.972 ms | 4.899 ms |
| Other subsector work: line processing, clipping, plane lookup, sprite collection | 14.584 ms | 13.846 ms |
| Wall setup outside RenderSegLoop | 21.311 ms | 20.939 ms |
| Wall loop, including column drawing and texture lookup | 40.021 ms | 40.368 ms |

These are **instrumented elapsed times**, including interrupts, preemption and
wrapper/clock overhead, not isolated CPU cycles. The empty read bracket is about
0.8 microseconds; it does not measure all instrumentation overhead. Region call
counts agree for all 2,080 profiled frames. Measured-window averages are one root,
87 subsectors and 110.4575 wall ranges/loops per frame.

The wall loop did not improve. Much of the small aggregate difference appears
outside wall setup; this experiment does not establish whether layout/cache or
scheduling effects explain that partition. Do not attribute all gains to a faster
pixel loop. Traversal is a small fraction of the frame; prioritize exact plane
span kernels before an iterative BSP rewrite in this workload.

## Checks and artifacts

- All **2,600 corresponding pixel/palette images** match across five runs.
- Native first 52 frames retain only the four established differences at
  29260/29261/29580/29581; no new divergence.
- **285 full paired system audits**, all ownership checks, 3-second held-slot
  stalls, held-frame STOP and heap drain pass. Maximum IRQ gap **10.812 ms**.
- Five full system/frame/WAD replays pass remotely and independently locally;
  24 frame and 4 drain evidence mutations are refused per run. Local summary
  comparison allows only the previously established floating roundoff tolerance;
  the underlying full validators are unchanged.
- **2,444 exact HTTP payload observations** match captured card frames.
- Both profiled variants pass deterministic native 52-frame repeats and match
  accepted native images. Existing Linux ASan/UBSan presentation tests pass;
  the new trailer validator refuses 21 malformed/conflicting cases. Native
  telemetry is also decoded: real call counts and zero hardware-clock ticks.
- Protected point-side O0 and exact-divide objects retain accepted hashes.
  Admission sizes: plain 819,168 bytes, profiled A 819,680, B 819,728; all below
  900,000. A/B changed engine objects are r_segs plus the aggregate and unchanged
  r_data/w_wad objects containing distinct absolute assertion source paths.
  All three target final links have no undefined symbols.

A missing stock runner dependency was corrected before card execution; the setup
failure log is retained. One Linux 32-bit adapter-test invocation could not link
on macOS; rerunning on its intended Linux host passed. An early remote invocation
of the local region-analysis script had an incorrect import root; the script now
supports both layouts and all final results are recomputed locally. Shared root
build stdout filenames retain the last preparation output; exact per-build
commands, source/object hashes and native captures identify each tested binary.

`candidate.tar.gz.part-*` contain exact source, dependencies, three builds and
native evidence; `p0/a1/b1/b2/a2` contain all raw card captures and reports.
`binaries/early-builds.tar.gz` separately preserves the images/modules/admissions
saved locally before later reboots. Every capture and the source/build archive
was hash-verified locally before the final reboot. Reassemble/verify with
`python3 artifacts/walls-20261016/extract.py --verify-only`, or pass an extraction
destination. Build/run/replay/measurement scripts are retained beside the evidence.
The executed coordinator invocation was `accept.py --runs p0 a1 b1 b2 a2`;
its inherited final stdout label says “four” despite recording all five completed
runs. The current script defaults to all five. Inspect actual hardware ownership
before any rerun.

Public IPv6 HTTP restored: **200**, 2,889 bytes, boot
`22b8d687-42db-477e-804b-8bb26eeac7da`. The public relay owns the card; no Doom session remains.
See `restoration.json` and captured HTTP response.
