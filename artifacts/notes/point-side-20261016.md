> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Exact BSP point-side helper — physical acceptance

C columns remain **opt-in** (`--fast-columns`); recent accepted benchmark builds
explicitly use both `--fast-columns --fast-render`. Exact FixedDiv is already the
playable default. This batch keeps those settings fixed and tests only the next
queue item: opt-in `--fast-point-side` replacing the protected O0 helper.

The new implementation pairs signed compare/test instructions inside a single
inline-assembly statement, preventing the historical condition-code scheduling
bug. Unsigned deltas and explicitly defined sign conversion/shift arithmetic
preserve the pinned 32-bit Doom behavior. It keeps the original shortcut and tie
rule; it is not a higher-precision geometry approximation.

Predeployment results: 1,002,000 independent host-oracle cases, 12,000 UBSan
cases and builder option regressions; native deterministic
52-frame reference images; 1,024 candidate/original/oracle comparisons on the card
in 32 bounded transactions. All 3,520 firmware commands, 96 paired full staging
phases, restoration and clean module unloads pass independent local replay.
The scalar payload links the exact engine object; linked text is checked byte
for byte. The protected O0 object retains its accepted SHA256.

The predeclared [plan](PLAN.md) runs full-audit A/B/B/A, 520 frames/run, measuring
frames 100–499 without dropping outliers, matching images, held-frame STOP,
stalled-host behavior, final heap drain, native oracle and replay/tamper checks.
All four physical runs, full audits, image checks and lifecycle/replay/tamper
checks passed. The candidate remains opt-in.

Only point-side source changes. Unchanged assertion-bearing r_data.c and w_wad.c
also produce different object bytes because A/B embed different absolute source
paths; build checks verify their identical source and embedded paths. An initial
strict object-list assertion caught this distinction; it was corrected explicitly.
Initial probe preparation exceeded the 64KiB scalar limit using full node structs
and pulled unused divide dependencies. Compact vector records and a FixedMul-only
object (text-checked against the accepted engine) resolve both before card use.
A compare operand-order correction and explicit helper inlining were completed
before any scalar card execution. Setup failure logs remain archived.

The A1 coordinator initially reused the preceding experiment's temporary extraction
path. The capture archive itself was correct and hash-verified. Between runs,
the coordinator was stopped, its destination was corrected, A1 was freshly
extracted from that archive, and B1/B2/A2 resumed. All final comparisons use the
new experiment's captures. No card binary or test policy changed.

Build stdout used shared temporary filenames during preparation: the saved
`logs-fast/render-engine-host.log` contains the baseline path after being reused.
It is not a candidate build identity. Per-build compiler commands, source hashes,
objects, manifests, native captures and final binary hashes are retained in each
build directory and checked independently; the candidate binary hash list agrees
with the actual tested files. The original stdout is preserved as observed.

## Matched result

A/B/B/A, 520 frames per run, fixed low detail, exact divide and specialized C
columns/spans enabled on both sides. A is the original O0 point-side helper;
B is the defined exact replacement. Both retain frame/CPU/WAD counters. Timing
uses frames 100–499, 800 frames / 798 intervals per implementation, no exclusions.

| Metric | Original O0 | Exact candidate |
| --- | ---: | ---: |
| Host FPS | 6.42844 | 6.43066 |
| Renderer wall | 136.4625 ms | 136.1375 ms |
| Sampled renderer CPU | 133.8750 ms | 133.6000 ms |
| BSP/walls | 78.8000 ms | 78.3125 ms |
| Planes | 40.2125 ms | 40.3375 ms |
| Sprites | 17.4500 ms | 17.4875 ms |
| Completion observed to HTTP availability | 4.6322 ms | 4.8724 ms |

The observed pooled FPS difference is **+0.034%**, renderer
wall difference **-0.3250 ms**. This small difference
is within the variation between repeats; do not claim a meaningful FPS or latency
improvement. The exact helper is qualified as an optional implementation, not
promoted as a speed win. The emitted helper is 336 bytes versus 416 bytes, with
no calls and three adjacent signed compare/test pairs. Overall admitted image
sizes are 819,152 versus 819,104 bytes; distinct embedded source paths also affect
layout, so do not equate this overall difference with helper text size.

BSP/wall and CPU counters do not isolate exact helper cost; CPU sampling has
10ms resolution. This batch does not change traversal or prove a compiler-wide
fix. Broader map/interactive coverage and direct traversal profiling remain open.

## Acceptance and evidence

- All **2,080 corresponding pixel/palette images** match, including menus.
- Native first 52 frames retain exactly the four previously documented byte
  differences at 29260/29261/29580/29581; no new native divergence.
- **229 full paired system audits**, all ownership checks,
  held-slot stalls, held-frame STOP and heap drain pass.
- All four system/frame/WAD replays pass, with 24 frame and 4 drain evidence
  mutations rejected per run. Maximum IRQ gap: **10.832ms**.
- **1953 exact HTTP payload observations** match their captured card frames.
  This is delivery validation, not a browser-paint/input-to-photon measurement.
- Every capture was saved and hash-checked locally before reboot. No flash writes.

`candidate.tar.gz.part-*` reconstruct exact source/build/dependency/native archives;
`a1/b1/b2/a2` retain all raw card captures, replay reports and HTTP observations.
`probe-evidence.tar.gz` contains the exact scalar proof. Run
`python3 artifacts/point-side-20261016/extract.py --verify-only` to verify all
archives, or pass a destination to extract them. `build.sh`, `run.sh`, `accept.py`,
`verify.sh` and the measurement/image scripts reproduce this experiment in its
isolated workspace. Check hardware ownership before any live rerun.

Public IPv6 HTTP restored: **200**, 2,890 bytes, boot
`2b670864-d474-4926-9424-371f8b7f20b9`. The public relay owns the card; no Doom session remains.

## Next

Profile traversal path counts and costs separately from wall drawing before a
bounded iterative BSP experiment. Preserve front-to-back/culling order and exact
images; do not silently reduce rendering quality. Keep this candidate optional
and compare against the latest measured build. Specialized C columns remain
opt-in; exact FixedDiv remains default for playable builds.

Independent local system/frame/WAD replay also passes for all four captures.
The local Python version rounds two derived means differently at about 1e-14ms;
`replay_local.py` keeps integer/identity/shape comparisons exact and allows only
tight finite floating roundoff in the **summary comparison**. The underlying
full validators are unchanged. Both original and local reports and all differing
summary floats are saved, so this does not relax captured-byte or guard checks.
