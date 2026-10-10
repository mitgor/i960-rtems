# T3: long hardware replay and latency — passed

2026-10-10. The primary run completed **1,000 consecutive hardware transactions**
using Tetris state returned by the preceding call. Every state and framebuffer
matched the native reference byte for byte. All 128,000 firmware commands had
matching IDs, expected status and intact DMA guards; each transaction restored
the full original staging image and unloaded cleanly. No flash write, reboot or
uncertain-command retry occurred. Boot ID remained
`a9429ca4-0144-452d-8a80-7189608ce99b`.

The primary run took 466.6 seconds including lossless archive creation/verification. Its calls comprised 974 updates, 19 initializations/restarts and 7 quits. There were 8 game-over responses followed by restart. The deterministic stress inputs did not clear a line (maximum score 0); the live two-line-clear test remains documented in T2.

A separate 64-call repeat run also passed (63 updates and one initialization).
Together the primary and repeat runs exercised **1,037 update calls** plus
initialization/quit calls, with 136,192 successful firmware commands. A preceding
three-call smoke test also passed. All evidence sets were independently validated
locally after extraction. The repeat overlapped host archive compression, so the
primary run is the basis for the latency table below. Final state is module
unloaded and card driverless; recovery remains untested.

## Measured latency

All values are milliseconds; p50 uses the sorted upper-middle sample, p95 the
nearest-rank 95th percentile. Timing includes the conservative full verification
path, not a resident session.

| Interval | Mean | p50 | p95 | Maximum |
| --- | ---: | ---: | ---: | ---: |
| Full CLI call | 306.40 | 306.27 | 315.25 | 373.32 |
| Kernel setup/upload/verification | 98.49 | 99.20 | 99.68 | 107.08 |
| Payload command round trip | 6.18 | 6.18 | 6.28 | 6.37 |
| Output readback/validation | 14.30 | 14.32 | 15.14 | 17.82 |
| Restore/verify/health | 67.29 | 67.33 | 68.77 | 70.67 |
| Lossless archive/round-trip check | 151.09 | 150.21 | 173.65 | 435.84 |

The full CLI path provides roughly **3.26 updates/second** when archive work is excluded, below the 20 Hz target. Setup, full-image verification and restoration dominate. The payload interval includes mailbox submission, polling and completion; it is not an isolated measurement of i960 execution time. Preflight before the timed run stage, module/process setup, capture copying, unload and Python verification account for additional CLI time.

The conservative one-shot path uploads, verifies, runs once, reads back and
restores the entire borrowed image on every request. It is intentionally not a
persistent session. This milestone changes only host-side timing instrumentation
and replay/evidence tooling; the T2 game binary, call gate and flash are unchanged.

Timings use Linux monotonic kernel timestamps around the run-stage phases:
setup includes initial paired full image/profile-dependent checks, payload upload
and verification and temporary callback installation; call is the firmware
payload command from submission through observed completion; output includes
self-disarm/result checks plus paired full output image reads and validation;
restoration includes original dispatch/code/result/image verification and the
final Enquiry. Pure i960 instruction execution time is not isolated. CLI latency
also includes process/module setup, earlier preflight, debugfs capture, module
unload and independent Python verification. Archiving is measured separately.

The archive tool stores every capture byte. Full 512 KiB blobs are XORed with a
pinned common baseline and ZIP-compressed; other files are stored directly with
ZIP compression. Every member records its original SHA256 and size. The packer
reconstructs and compares all bytes before removing its own transient raw folder.
This is lossless encoding, not substituting reference bytes for unread memory.
The independent validator reconstructs all captures, checks the full loader
transaction, replays the same seeded schedule through a freshly compiled native
oracle and compares exact response bytes. It checks request continuity, IDs,
statuses, DMA guards, one payload execution, restored hashes and clean unloads.

The schedule uses seeded initializations, varying 1..20-tick requests, movement,
rotation, drop, scheduled quit/restart and restart after game over. Expected
outputs are computed before each hardware call; the next request uses returned
card state. The runner stops on the first mismatch, error, unexpected command
count or retained module. It never retries an uncertain execution. This is a
stress/latency run, not a human playing or a 30-minute interactive acceptance test.

## Evidence and reproduction

[artifacts/tetris-t3-20261010](artifacts/tetris-t3-20261010/) contains the timed
module/source, tests, timing rows, summary, final frame and complete replay
archives. The game binary and native oracle sources remain the T2 versions.
`replay.tar.xz` contains `replay/archives/0000.zip` through `0999.zip`, the pinned
baseline and every run record. The ZIP members named `data/...` may be XOR encoded;
use the provided tool to reconstruct raw captures. Each archive was round-trip
checked before deleting its temporary raw directory. Local independent validation
reconstructed all 1,000 runs and recomputed the native outputs and continuity.

```sh
# Offline: extract into a new directory, then independently validate all runs.
mkdir /tmp/tetris-t3-evidence
tar -xJf artifacts/tetris-t3-20261010/replay.tar.xz -C /tmp/tetris-t3-evidence
cc -O2 -DTETRIS_CORE_ONLY game/tetris.c game/oracle.c -o /tmp/tetris-oracle
python3 host/loadrun/validate_replay.py /tmp/tetris-t3-evidence/replay \
  --oracle /tmp/tetris-oracle
python3 host/loadrun/capture_archive.py \
  /tmp/tetris-t3-evidence/replay/archives/0000.zip \
  --baseline /tmp/tetris-t3-evidence/replay/baseline.bin --output /tmp/tetris-step-0
```

`host/loadrun/tetris_replay.py` is explicit hardware work: it requires payload,
module, oracle, baseline and a new output directory. The deployed copies are
under `/home/mit/i960-tetris-t3/`; it defaults to 1,000 calls and never retries a
failed execution. Native tests retain 194 scalar and 230 BIO1 failure boundaries,
plus capture archive and deterministic-schedule tests. The timed module built
with W=1. Kernel timing uses monotonic `ktime_get_ns()` and changes no target code.

## Next step

T3 is complete. T4's terminal client can use this path at its measured cadence,
but reaching 20 updates/second calls for T5's persistent session optimization:
verify/save once, perform bounded per-frame requests, then restore/verify at
close. This needs its own ownership/disconnect/failure tests. Do not remove
checks from the one-shot path or keep a callback armed just to improve a benchmark.
The long replay is not a 30-minute interactive-play or disconnect acceptance test.
