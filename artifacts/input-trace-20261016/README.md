# Default exact divide and bounded input trace — physical acceptance

The previously qualified exact FixedDiv is now the default for private playable
engine builds and the interactive builder. Use `--no-fast-fixed-div` for the
original divide; non-play compiler inventories keep their existing default.
`--fixed-div-profile` remains optional and now profiles the selected default
unless explicitly combined with `--no-fast-fixed-div`.

The next queue item adds opt-in `--input-trace`: a bounded per-frame ITR1 record
of card dequeue, pre-menu responder and post-menu responder, with display
frame, gametic, maketic, sequence, key/down and menu state. Host submission
records allow comparison with the exact point Doom consumes the event.
See [format](../../game/doom/input_trace/README.md) and [plan](PLAN.md).
The diagnostic does not change input scheduling, ownership or audit policy.

Native checks pass: default selection/override, exact arithmetic, deterministic
52-frame runs for both builds, interactive 40-frame runs, actual native Escape
menu transition, and recorder/decoder bounds and refusal tests. The trace's
read-only maketic accessor preserves the original variable's private linkage.
An initial linker failure and a native-test variable-shadowing failure are
saved under `setup-errors/` in the source/build archive; both were resolved
before hardware testing.

Physical acceptance completed with four accepted 520-frame runs. The earlier
failed logger attempt remains separately archived below. The exact divide is
now enabled by default; input tracing remains opt-in.

## Measured result

Fresh A/B/B/A, frames 100–499, 800 frames / 798 intervals per build; no outliers
removed. A = default exact divide, trace off. B = same arithmetic, trace on.

| Metric | Trace off | Trace on |
| --- | ---: | ---: |
| Host FPS | 6.43221 | 6.41250 |
| Renderer wall | 136.175 ms | 136.763 ms |
| Sampled renderer CPU | 133.600 ms | 134.063 ms |
| BSP/walls | 78.575 ms | 78.900 ms |
| Planes | 40.238 ms | 40.488 ms |
| Sprites | 17.363 ms | 17.375 ms |
| Screen copy | 10.513 ms | 10.462 ms |
| Release gate wait | 2.515 ms | 2.630 ms |
| Release ioctl | 7.674 ms | 7.745 ms |
| Completion observed → HTTP availability | 4.794 ms | 4.479 ms |

Tracing measured **0.31% lower FPS**, with renderer wall time 0.588 ms higher.
This small diagnostic comparison is not a new rendering speedup or proof of
zero overhead. Both builds retain frame/CPU/WAD counters and all full audits.
CPU attribution uses 10 ms sampling. DMA-start-to-HTTP bounds overlap:
17.60–48.42 versus 16.73–50.88 ms; no end-to-end or browser-paint latency claim.
Per-run/window data and pooled metrics are in `timing.json` and `comparison.json`.

All **2,080 corresponding images match**, including menus, and all **228 full
paired audits** pass (57 per run). Every run passes the roughly three-second
held-slot stall, held-frame STOP, heap drain, system/frame/WAD replay, 24 frame
mutations and four drain mutations. Maximum IRQ gap **10.832 ms**.
All **1,932 observed HTTP frame payloads** match their captures, without claiming
that the observer received every frame. The first 52 images retain only the
known native differences at 29260, 29261, 29580 and 29581. All 520 default-build
A1 images also match the previously accepted exact-divide B1 capture
(`default-images.json`). No flash writes or ownership/audit relaxations occurred.

## Input findings

Both traced runs reconcile **8 successful submissions → 24 phase records**,
with no overflow/loss. Their complete input records are identical. Six additional
trace-specific capture mutations are rejected in each run; host tests also cover
schema refusals and actual C recorder capacity/clearing. See `input-comparison.json`.

| Host observed frame before submission | Key pair | Consuming display frame | Game tic / make tic |
| --- | --- | ---: | ---: |
| 60 | Escape down/up | 62 | 61 / 61 |
| 62 | Enter down/up | 64 | 63 / 63 |
| 64 | Enter down/up | 66 | 65 / 65 |
| 66 | Enter down/up | 68 | 68 / 68 |

Escape changes menu-active 0→1; the final Enter changes it 1→0. Dequeue and
responder processing occur in the same recorded display generation for these
keys. Two generations after the host-observed frame is an observed pipeline
relationship, **not a measured two-frame input-to-paint latency**. Already
rendered/buffered frames must be accounted for. Game tics and display generations
are separate counters, as the final row demonstrates.

This completes the queued tracing capability and demonstrates why host enqueue
logs alone cannot identify the consuming frame. It does **not** retrospectively
prove the cause of the old one-frame menu mismatch: that capture lacked this
trace. Keep the original discrepancy recorded and use tracing on any recurrence.

## Build and evidence

`build-checks.json` confirms both builds use the accepted exact-divide object and
unchanged protected `R_PointOnSide` O0 object. Tracing grows the engine memory
from 819,168 to 820,208 bytes (+1,040); file/template grows 435,000→435,576 bytes.
No extra heap allocation is introduced. FixedDiv profiling symbols are absent.

Complete sources, generated builds, dependencies, native binaries/oracles and
logs are in `candidate.tar.gz.part-*`. The four accepted captures and failed
attempt have individual SHA-256 sums. All were saved/hash-checked locally before
reboot. `accepted-binaries.sha256` pins the loaded images. Raw disassembly is
preserved as `.raw.gz` alongside whitespace-normalized text.

```sh
python3 artifacts/input-trace-20261016/extract.py --verify-only
python3 artifacts/input-trace-20261016/extract.py /tmp/input-trace-evidence
```


## Reproduction

`build.sh build` builds trace-off/default-exact, `build.sh build-fast` builds
trace-on/default-exact (the second directory name follows the prior harness).
The A/B/B/A script runs 520 frames each, frames 100–499 for timing, without
outlier removal. Use `--input-trace` only on admitted pipeline builds; it shares
the reserved trailer with FixedDiv profiling and cannot run alongside it.

`game/doom/input_trace/verify.py CAPTURE` reconciles every successful scripted
submission with all three trace phases and validates all frame trailers.
Full frame/system/WAD replays, mutations, stalled slots, held STOP and heap drain
remain mandatory. `native_input.py` exercises the actual menu transition under
the native runtime. `check_frames.py` checks all corresponding pixels/palettes
and preserves the known four-pixel native/card difference.

## Preserved failed attempt

The first B1 attempt stopped at the first scripted input after frame 59: the
host-only diagnostic logger referenced `g` outside `serve()` scope. The card
accepted the key, then Python raised `NameError` before recording it. The run
is not an accepted lifecycle or FPS result. Its complete available capture is
`failed-b1-host-log.tar.gz`, with SHA-256 and HTTP observations in
`failed-b1-http/`. The host now passes the observed frame explicitly; a regression
test executes the real logger and checks every key call site. Card binaries
were unchanged. The failed evidence was saved/hash-checked locally before
reboot. A1 used the same trace-off path; B1 is repeated with the fixed logger.

## Service restoration

The public IPv6 relay is restored: HTTP 200, 2,890 response bytes,
SHA-256 `ef011879a65c6784a4827b03d91517679f073d8771f429eaba87e3de3f7fda09`. Boot ID
`df928288-d6ce-4cbd-aaa5-67fea627e0f3`. The relay owns the device and no Doom test session
remains active. See `restoration.json`, saved HTTP response and owner evidence.
