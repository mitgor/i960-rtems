# N2: bounded WAD batching — 2026-10-12

The cache batching implementation has physical normal/fault/STOP/recovery evidence,
full audit replay and two matching native command replays. Keep it opt-in. The
original live harness failed **after** successful physical STOP/drain because it
expected 14 image cancellations instead of the correct 15; see the evidence
qualification below. It is not an unqualified clean live-harness pass. The original
engine preflight image is unchanged and uses its old 512-byte ABI; the batch proof
has its own negotiated cache API. Actual Doom initialization is still N3.

See [protocol and lifetime contract](../../game/doom/runtime/batch/README.md).
The batch test runs after all earlier runtime/cache/relocation/owned/engine
proofs, with full paired audits and six parallel IPv4/IPv6 rounds. It compares
512 / 4096 / 4096 / 512 normal workloads around late-fragment CRC, short reply,
host error, partial timeout and partial STOP injection, including stale STOP
refusal and fresh-entry recovery. No real Doom initialization is attempted.

## Native and host evidence

- `native-runtime.log`: actual allocator, loans, runtime, wire assembly and cache
  under ASan/UBSan. 48 full/fault/STOP cases over all eight fragment positions,
  no destination changes on failure, exhaustion recovery, 10,000 cache reads,
  EOF/bounds/owner/sequence/fragment-order rejection and final drain.
- `native-host.log`: actual host response server, exact ordered fragment bytes,
  late injected faults, no duplicate replies, stale STOP and EOF.
- `offline-final.log`: complete offline RTEMS regression suite, exit 0.
- `trace-comparison.json`: real cache + assembly code replaying every first-frame
  logical read against the pinned WAD. 27,648 → 4,747 requests (82.83% fewer),
  unchanged 27,648 fragments / 14,155,460 wire data bytes. All 13,804,084 delivered
  bytes match. This is a request-count result, not card timing.
- `host-results.json`: six real 32-bit host Doom demos, all 12,600 frame hashes
  match the accepted corpus, with the new batched cache and complete arena drain.
  The host adapter uses trusted immutable host memory; the separate native wire
  tests exercise CRC/assembly/loans. This is the earlier host libc/arena profile,
  not the private Newlib engine running on the card.
- `ram-audit.json`: final link passes unchanged memory/code/guard boundaries.
- `build-layout-rejected.log`: rejected initial static staging layout, never
  loaded onto the card. Final staging uses pinned application arena allocation;
  validation code uses spare space inside the existing protected engine window.

At a pending 4096-byte read, extra payload memory versus the original cache is
3584 bytes of bounce plus 4352 bytes of staging = 7936 bytes, plus allocation
metadata/alignment. No kernel BSS region or code protection boundary was enlarged.

The actual 512-byte comparison uses the same WAB1 assembly, owner and loan path
with a smaller negotiated limit. This isolates batching, but it is not identical
to the old WAD1 implementation. Report its timing accordingly; neither fewer
requests nor host timing alone proves a Doom frame-rate gain.

## Card measurements and acceptance

Exact payload SHA256: `4c9197c50da698d9710fa93d1cc287fbe9c776cf9592d8620888af1a448925e3`.
Test boot: `dbedeae4-8006-49c4-be48-fd51aaf37c59`; PCI `0000:37:09.1`.
Cache probe template: 2,144 bytes, 12 relocations; SHA256
`c11edadb4fef02c2c1c8dfc1bd8608dbfb7a531544e990b7d6851c5b075d0081`.
Pinned Freedoom1: 28,795,076 bytes; SHA256
`7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d`.

| Normal WAB1 limit | Requests | Fragments | Run seconds | Mean seconds |
|---|---:|---:|---|---:|
| 512 | 24 | 24 | 2.995, 4.182 | 3.588 |
| 4096 | 7 | 24 | 2.051, 1.259 | 1.655 |

Same byte oracle `1465048495` on every normal run, including recovery after faults.
Mean ratio 2.168×, elapsed reduction 53.88%. These are two observations per size,
including eight report commands per run, not a statistical benchmark. Late CRC,
short, host-error, partial timeout and partial STOP all return the expected failure;
next fresh entry works. Partial STOP rejects the stale generation before accepting
13. All 82 logical requests and 156 fragments have independent byte/protocol checks.
The five-second timeout measured 6.243 s including reports and host overhead.
All report states/loans return to zero; final cancellation count is 15.

`card-performance.json` records individual command ioctl costs. Across all cases,
212 WAD metadata polls total 1,694.232 ms (7.992 ms mean), and 156 fragment writes
total 6,199.149 ms (39.738 ms mean). Batching amortizes metadata/handshakes; it does
not remove fragment payload transfers or validation. No claim of bus bandwidth,
old WAD1 wall-clock speedup, actual Doom startup duration or Doom FPS follows.

`card-network-replay.json` verifies image identity, full paired initial audit,
all retained diagnostic words and final STOP snapshots, 8 MiB ownership, packet
checksums/reassembly and parallel network traffic. `recovery-provenance.json` confirms
all captured IRQ rejection records are zero. `card-upload-replay*.json` match all **7,949 commands**
twice with actual native C runtime/cache/assembly and ASan/UBSan. As before, native
replay models the i960-only engine diagnostic's call from independently checked
physical reports; it is not an i960 emulator. 18 new batch evidence mutations and
44 earlier runtime/cache/relocation/owned/engine mutations are rejected.

One earlier native replay invocation aborted at `exclusive_abort` without a useful
call site. No card code or expected result was changed to make it pass. Diagnostic
backtraces were added to the native harness; the subsequent two complete runs
matched. The initial cause is unresolved (do not label it a proven hardware fault
or a proven host scheduling fault). Retain this caveat if it recurs; do not retry
hardware faults away. The physical card run itself has no such abort.

## Original harness failure and derived replay view

`card-evidence-initial.tar.gz` is the unmodified remote capture: original `live/`,
`live.log`, post-run kernel log, exact source snapshot, generated binaries,
three-link cache admission, engine metadata and final module. It preserves the
obsolete harness assertion and exception diagnostic page. It does not contain
visitor logs or another copy of the WAD.

At tick 101,897 global STOP reached state 2, both parked snapshots matched, network
operations refused correctly, and the final raw upload query showed no pending
command/image/handle and 15 cancelled images. The host assertion still expected
14 and prevented two convenience files from being written. `recover_view.py`
creates a **separate derived view**, never edits the original:

- Decodes `upload-parked.json` from the final raw ioctl response.
- Uses retained `dmesg-after-live.txt` as `last-control.txt`, clearly labelled in
  provenance as kernel ring-buffer text, not an original debugfs capture. It has
  monitor entries and no later firmware submission, satisfying the existing
  verifier's no-submit-after-monitor check. It is a tail, not a full boot log.
- Separates the final exception-only 65 control records into
  `exception-controls.json`, checking every tag and all state words against the
  raw failure snapshot and final parked snapshot. The ordinary full audits are
  retained unchanged; the exception page had no associated RAM audit page.

`recovery-provenance.json` binds the raw sources by hash. All verifier assertions
remain enabled. The source harness now records the final reply and monitor text
before asserting, and expects 15 when batch results exist. The corrected harness is syntax-checked; it has not had a second complete
physical run.

## Reproduce offline

From the repository root, with the pinned WAD available:

```sh
mkdir -p /tmp/i960-batch-card
tar -xzf artifacts/doom-batch-20261012/card-evidence-initial.tar.gz -C /tmp/i960-batch-card
python3 artifacts/doom-batch-20261012/recover_view.py /tmp/i960-batch-card
python3 rtems/residentnet/verify.py --root /tmp/i960-batch-card /tmp/i960-batch-card/replay-view
python3 rtems/residentnet/verify_upload.py /tmp/i960-batch-card/replay-view --output /tmp/batch-replay.json --doom-heap --doom-shared --doom-runtime --wad /path/to/freedoom1.wad --wad-poll
python3 rtems/residentnet/test_batch_evidence.py /tmp/i960-batch-card/replay-view --build /tmp/i960-batch-card/residentnet/entry/cache --wad /path/to/freedoom1.wad --output /tmp/batch-mutations.json
python3 artifacts/doom-batch-20261012/measure_capture.py /tmp/i960-batch-card/live --output /tmp/batch-performance.json
```

The remote isolated workspace is `/home/mit/i960-doom-batch-20261012`.
`residentnet/build.json`, `live/request.json`, `live/test-options.json` and original
source snapshot retain build/run settings. Build adds `--wad-batch --wad-poll`
to the accepted engine/dispatch-atomic/8 MiB profile. New image/source changes
require rebuilding and fresh admission; never reuse old hashes implicitly.

## Restored service and next step

After evidence was saved, reboot plus a user-assisted power cycle released the
retained exclusive test module. Production boot is
`900d54e8-90bb-456d-97aa-e98e044e66b2`; relay PID 3361 owns `dac960auto` using the
unchanged `/home/mit/i960-rtems-web-20261011` build. Output is
`http-after-doom-batch-20261012`, existing visitor statistics retained. External
IPv6 HTTP 8080 returned 200; `service-restored.json` records the check. Never
force-unload its retained resources. Hardware handoff was sent to the parallel
RTEMS chat after restoration.

N3: explicitly bind the batch API into a newly authenticated engine candidate,
keep owned entry, bounded STOP/deadline, executable revalidation and the 8 MiB
contract, then attempt actual Doom initialization and a deterministic first
frame. Keep rendering/browser-loop work separate until that succeeds.
