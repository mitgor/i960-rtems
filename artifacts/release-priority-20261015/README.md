# Release priority and selective private-memory optimization

The experiment separates host audit-lock delay from ioctl duration, gives pending
frame releases priority, and publishes validated immutable host frames before
waiting for release. Full frozen-page, RAM/heap, code, guard, DMA-ownership and
STOP checks remain mandatory. No flash programming.

## Matched scheduling result

Two 520-frame card runs used identical kernel/engine/module/WAD binaries.
Measured blocks were frames 100–199, 200–299, 300–399 and 400–499; run order was
ABBA then BAAB, where A is baseline and B is priority. Each policy covers four
100-frame blocks, 396 frame intervals, balanced across the same frame positions.
All intervals stay in their blocks; no audit-induced pauses are removed.

| Pooled measurement | Baseline | Release priority |
| --- | ---: | ---: |
| Host-delivered FPS | 4.8374 | 4.8350 |
| Card DMA-publication FPS | 4.8387 | 4.8375 |
| Release audit-gate wait, mean | 13.402 ms | 2.659 ms |
| Release ioctl duration, mean | 6.966 ms | 7.276 ms |
| Completion observation → HTTP publication | 25.178 ms | 4.771 ms |
| Renderer elapsed, mean | 187.800 ms | 187.375 ms |

**Gate wait fell 80.16%; observation-to-publication latency fell 81.05%. FPS was
unchanged within this comparison (-0.049%).** Audit hold timestamps account for
nearly all baseline gate-wait time. This confirms the contention hypothesis from
the previous bulk-capture analysis. The ioctl component includes kernel mutex and
Linux scheduling time; it is not a pure card-execution measurement. HTTP
publication is availability to the HTTP handler, not receipt or browser paint.
Card-start-to-publication bounds in the JSON include 10 ms tick quantization and
clock calibration uncertainty; no cross-clock point estimate is claimed.

Both runs passed **520 frames and 62 full paired snapshots each**, initial
held-destination stall, final held-frame STOP and global heap/IRQ drain. Maximum
IRQ gaps were **10.828 ms** and **10.762 ms**. All 520 pixel/palette images match
between runs. First 52 retain exactly the four known native/card pixel differences
at 29260, 29261, 29580 and 29581. HTTP payloads are checked separately in
`scheduling-pixels-http.json`.

The new gate is reentrant and cannot preempt its current holder. In priority
mode, an audit unlocks after each word rather than each four-word group. It still
reads the same 64 frozen words; packet pumping and pacing remain once per four
words. Release remains synchronous, generation-checked and bounded by the
existing driver deadline. There is no new unbounded queue or early card-buffer
recycling. The browser gets a separate immutable host copy after validation.

## Evidence and reproduction

- `PLAN.md`: declared measurement windows, policy order and acceptance conditions.
- `run.sh abba` / `run.sh baab`: isolated 520-frame full-audit runs. Hardware must
  be unbound first; inspect its owner, and never force-unload retained mappings.
- `verify.sh NAME [BUILD] [full|replay]`: full system, every frame, WAD, profiling
  and drain replay. ABBA also ran all 24 frame mutations; BAAB reused those
  unchanged-verifier mutation cases, while replaying every byte of its own run.
- `measure.py CAPTURES...`: per-block and pooled host/card rates, separated gate/
  ioctl costs, audit-hold overlap and publication latency.
- `check_frames.py CAPTURES... --native PATH --http-root ARTIFACT_DIR`: every
  pixel/palette against the first run, first-52 native oracle and HTTP payloads.
- `candidate.tar.gz`: isolated sources, both baseline and memory-candidate
  binaries, native oracle and build logs. Each card archive has the full capture,
  run log and replay results. Adjacent `.sha256` files authenticate the archives.
  Extract only after checking hashes; omit workspace symlinks.

Baseline binaries are unchanged from bulk-capture acceptance:

- kernel `1dce227e130d144187cfd0577ca333da09d20d62baf6617db30bc29b137a2c08`
- module `e97e8bd9eeb7da15bfb19d62625bb928c2b393e4357cec1bc903abe0f48111d9`
- engine `e9e43e211d1abf31da7d6a29d9a2c7c42f09ada8e7255af4ec2a2a93d32813dd`

Both builds use the same Freedoom WAD:
`7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d`.
It and the pinned build dependencies are reused from the previous accepted
workspace; no download or source-version change is part of this comparison.

Unit tests: `test_io_gate.py` covers queued release priority, reentrancy and
exception cleanup; `test_release_replay.py` covers timing identities, complete
one-/four-word page coverage and eight rejected mutations. Replay verifies both
raw journals and publication ordering, in addition to all existing full audits.

## Private-memory result: correct, no material FPS gain established

The third 520-frame run used priority delivery throughout and selected `-O2
-fno-strict-aliasing` only for pinned private Newlib `memcpy.c` and `memset.c`.
These sources already contain aligned word paths, disabled by the usual `-Os`.
No other compilation unit changed flags or source content. The engine grew by
224 bytes, kept the same symbol namespacing, had no unresolved runtime functions,
and retained 146 protected pages and the same RAM layout. Generated i960 code
contains `ld`/`st` word transfers plus the unaligned byte fallback.

The actual pinned speed paths passed exhaustive host32 ASan/UBSan checks over
copy lengths 0–4096, source/destination alignments 0–7, every memset byte value,
fill lengths 0–1024, and guard-page ends. Native Doom passed input/STOP/heap-drain
checks and two deterministic 52-frame runs; all pixels/palettes matched the prior
native oracle before physical admission.

The card comparison uses the same frame-position blocks, with priority enabled
in both: each baseline block comes from the corresponding priority half of the
ABBA/BAAB pair. This is one memory-candidate run, not an engine ABBA repeat.

| Measurement | Original private memory | Speed paths |
| --- | ---: | ---: |
| Host FPS | 4.8350 | 4.8546 |
| Card publication FPS | 4.8375 | 4.8547 |
| Renderer elapsed mean | 187.375 ms | 187.050 ms |
| Timer-sampled renderer CPU | 184.025 ms | 183.675 ms |
| BSP elapsed mean | 108.325 ms | 107.450 ms |
| Planes elapsed mean | 57.500 ms | 57.875 ms |
| Sprites elapsed mean | 21.550 ms | 21.725 ms |
| Completion observation → HTTP publication | 4.771 ms | 4.676 ms |

The observed **+0.40% FPS / −0.17% renderer time** is too small to establish a
repeatable performance gain. Keep `--fast-memory` opt-in; do not recommend it as
a demonstrated fix for sustained 5.19 FPS. The experiment establishes correctness
and generated word paths, not hot-path call counts or a significant improvement.
It does not optimize explicit calloc/realloc loops, wall/plane rasterizers, or
fixed-point division. Those remain separate profiling candidates from the
parallel Doom research/backlog.

All 520 fast-build pixel/palette images match both prior card runs. The known
four native discrepancies remain unchanged. Full system/frame/WAD replay and
held-frame STOP pass. `memory-comparison.json` contains every block and renderer
component; `all-pixels-http.json` checks every frame and HTTP payload received.

Fast build hashes:

- kernel `b67c372f4579aca2b4dc16edec1595749d3fddc5814e0ad71e4c25a6cddc3073`
- module `70a82b9ed811b6167a536edac09480b21deb4c664e6a77597d767ea61db828aa`
- engine `2c29d719267b02d28ad2a035ff933e862f8593f83ef890dea556385684534b04`

Use `build-fast.sh` to reproduce from the copied accepted build, or add
`--fast-memory` to the top-level Doom build command. `run-fast.sh` runs the same
520-frame acceptance with constant priority. The final top-level CLI forwarding
was checked with `--help`; the tested binaries were produced by `build-fast.sh`.

## What remains

Release priority is a qualified latency improvement. The observed earlier
5.19 FPS was partly a short-window backlog effect; the matched sustained baseline
is about 4.84 FPS. These changes do **not** reach sustained 5.19 FPS. Reaching it
still needs roughly 13–14 ms less per frame from the fast candidate's measured
~206 ms publication interval. Profile the ~107 ms BSP and ~58 ms plane work,
then test exact arithmetic/rasterizer candidates. No benefit from a reciprocal
table, assembly rewrite, or broader compiler optimization is assumed here.

## Final acceptance totals

Three 520-frame runs delivered 1,560 frames and completed 186 full paired audits.
All corresponding card images agree; 1,524 received HTTP payloads match captures.
Stalled-host, held-slot STOP and heap/IRQ drain pass. Maximum IRQ gaps are
10.828 / 10.762 / 10.490 ms. Linux and Mac replay pass; frame mutations were
checked on ABBA and fast captures, drain mutations on all three, and eight
synthetic release-timing/audit-coverage mutations are rejected.

Final CLI defaults select priority only for Doom ping-pong; physical runs used
explicit schedules with the same behavior. The run-wrapper forwarding/default
test passes. Fast memory remains opt-in. Final archives were copied locally and
SHA256-verified before the retained module was released by reboot.

Public IPv6 HTTP was restored after reboot: HTTP 200 / 2,890 bytes checked from
the Mac, boot `d61f3b7c-a43c-4e19-8ce9-5800c8dfce09`, relay PID 1502 /
supervisor 1500, bound driver `dac960auto`. The public relay now owns the card;
Doom test ports are closed. See `restoration.json` and the captured HTTP response.
