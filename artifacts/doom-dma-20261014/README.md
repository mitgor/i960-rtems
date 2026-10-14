# Pinned Doom frame DMA comparison — 2026-10-14

Status: **physical comparison partially passed; full acceptance failed** at
frame 12. Keep DMA opt-in. No accepted DMA FPS improvement or final heap drain.
The retained module was released by reboot after local archive verification.
Public IPv6 HTTP is restored and returned 200 from the Mac.

## Results and failure

| Measurement | Paired mailbox | DMA |
| --- | ---: | ---: |
| Mean transfer time for the same four pinned frames | 0.498802 s | 0.225233 s |
| Same-frame transfer speedup | | **2.2146×** |
| Completed timing block | 6 frames, 0.952700 FPS | only 1 frame |
| Accepted FPS improvement | | **not established** |

Four complete 65,536-byte comparisons are exact. Five DMA frames (1–4 and 11)
passed target completion/isolation, source CRC equality, complete host guards,
CRC, first-window reread, live generation and ACK. Eleven frames reached the
browser endpoint. All eleven named PNG hashes match the HTTP observations;
mean fetch time is 59.14 ms. The single mailbox block measured 0.9207 HTTP
receipts/s with 250 ms polling. No DMA block completed, and these are receipt
times, not browser paint times. `browser-benchmark.png` shows frame 7 during the
mailbox block. `browser-after-failure.png` shows the last retained image and fetch
failure after the harness closed; it is not a successful DMA-block screenshot.

Frame 12 submitted successfully, returned pending, then a completion poll timed
out with Linux errno 110 after 2.834 s. This is the existing 20,000-poll bound
inside the ten-second absolute command deadline; no timeout was enlarged.
The driver poisoned the session and retained the mapping/module/image. The
failure snapshot request was refused with EBUSY, as required by that state.

Read-only retained-buffer inspection found all expected frame-12 bytes and both
4 KiB guards intact; the payload exactly matches frame 12 from the previous
accepted physical mailbox run. Nevertheless, PCI command still showed bus
mastering enabled, and the MU request remained uncleared. **Arrival is not a
completion/retirement proof.** No ACK for frame 12, new request, forced unload,
manual bus-master clear or attempt to resume firmware followed. No terminal
snapshot or global/shared-heap drain is claimed. The root cause remains open;
the evidence narrows it to the interval after destination delivery and before
validated terminal publication, potentially including interrupted DMA cleanup.
It does not distinguish a CPU fault/park, lost interrupt context or another
control-path stall. No hardware erratum or compiler defect is claimed.

All **23 full monitor/RAM pairs** and 22 heap diagnostic pages were retained.
They precede the first frame; the failure prevented a post-DMA full audit.
The unchanged full verifier correctly rejects the incomplete run. Separate,
explicitly negative prefix inspectors validate the recorded wire responses,
image/module identities, paired RAM checks, all 11 frames, 650 mailbox reads,
five complete guarded captures, three refusals, planned input and ordered ACKs.
They require the failed frame-12 poll rather than pretending it completed.
Thirty frame/journal mutations and 24 snapshot mutations are rejected.

Two matching native 28-frame runs remain deterministic. The 11 delivered card
frames retain the known 7–8 differing pixels at x=139–141, y=90–92; palettes and
padding match exactly. All eleven buffers also exactly match the previous
physical mailbox run (`previous-card-comparison.json`). No new renderer
discrepancy was found in this prefix.

`failed-card-evidence.tar.gz` is the complete closed failed run, including
retained coherent bytes, read-only MU/PCI observations, kernel log and failure
cleanup. SHA-256:
`ba7cbc062c2c809be3780c69c51e535e9c7e830b6a56ed209952d63693b6fd6d`.
It was copied, hash-verified, extracted and prefix-replayed locally before reboot.
`measurements.json`, `failed-frame-replay.json`, `failed-system-replay.json`,
`failed-tamper-results.json`, `journal-costs.json` and `http-summary.json` preserve
the derived findings. `reference-mailbox-frame12.bin` comes from the previously
accepted mailbox capture, SHA-256
`6aef81ba5692ee7d2e6dc835c5e1331565f8faf77ab376563016387cd6aabf9e`.

## Next acceptance step

1. Add persistent phase markers around DMA launch, completion sampling,
   isolation and post-CRC, plus a bounded terminal diagnostic path that remains
   usable after normal transport is poisoned. Never re-enable mutation or reuse.
2. Reproduce repeated transfers with timer interrupts, recording fault/context
   information and the precise last completed phase. Fix only the demonstrated
   cause; retain the release lock, source/destination checks and full audits.
3. Repeat all four same-frame comparisons and the complete 28-frame A/B/B/A
   test, then prove owned STOP and global heap drain. Only that run can establish
   FPS improvement and support promoting DMA into ordinary browser play.


## Experiment

The admitted Doom engine is unchanged from the accepted mailbox run:
`9f2472c900bb724e7a69b2490e083c4c633520e1d525623398db2e36f2c1e173`.
Each immutable frame remains 65,536 bytes: 64,000 pixels, 768 palette bytes and
768 zero padding bytes. The renderer holds the frame until the checked ACK.

Read the first four frames completely through both DMA and paired mailbox,
requiring bytewise equality. Then use six-frame blocks in mailbox/DMA/DMA/mailbox
order, for 28 total frames. Each method has twelve measured transfers and ten
within-block delivery intervals; exclude the four dual-read frames from FPS.
Forward after frame 2 and release after frame 4 match two deterministic native
runs. Keep all full monitor/RAM audit pairs at the normal 60-second interval.

This is a bounded single-scene acceptance, not a general Doom benchmark or a
production DMA play mode. HTTP receipt timing is measured separately; it is not
browser paint timing. Startup remains unchanged.

## Ownership and validation

The existing RTEMS worker prepares the descriptor, computes source CRC32 before
and after, launches DMA1 and checks completion with interrupts enabled. The IRQ
handler only stages, submits or reads status. The host supplies no physical
address: the kernel allocates 73,728 coherent bytes against the actual PCI device
and stages its 32-bit DMA destination. The 64 KiB payload has a 4 KiB guard on
both sides. Every guard byte and the complete payload CRC are checked before
exposing results. Capture every byte, reread the first payload window, recheck
live generation and only then ACK. The renderer cannot release a pending frame.

DMA completion requires no active/error status, consumed NDAR, exact descriptor
address, zero remaining bytes, DCR 7, unchanged source CRC and descriptor guards.
Clear DMA enable and primary bus mastering, then recheck all-channel isolation.
Any uncertainty quarantines the frame/image/mapping until reboot. Clearing CCR
is not an abort proof. The Python audit gate spans one bounded DMA capture so a
full snapshot cannot sample intentional bus mastering; no audit check is removed.

See [FRAME-DMA.md](../../rtems/dma/FRAME-DMA.md) for the fixed ioctl/report ABI.
The prototype supports one owned engine invocation per resident session.
Graceful cancellation of pending frame DMA, reusable mappings, disconnect/restart
and ordinary interactive DMA play remain separate work. The accepted diagnostic
DMA STOP/deadline tests are not claimed as new frame-DMA hardware fault tests.

## Review-discovered release race

During the first startup, review found a submission window after the worker's
pending check: an interrupt could publish DMA just before STOP or frame timeout
released the frame. The test was stopped normally before any frame DMA command
was issued. Owned STOP, global drain and full system replay passed. The complete
closed evidence was copied and hash-verified locally before reboot.

The corrected `play_clear()` masks interrupts across the pending check and pointer clear,
restores the original priority, and refuses any release while DMA is pending. It enters
nonreturning quarantine, retaining the frame. A native test executes this exact
path, including submission immediately before lock acquisition and immediately
after priority restoration. A second startup was stopped before DMA when review
found that the initial check itself needed this atomic section. Both closed
captures pass full system replay. These were review findings, not observed DMA corruption. No performance
results are taken from the interrupted startup.

`preflight-stop-evidence.tar.gz` SHA-256:
`21bedacfaa727d9f6dee10edcfcc23fa1ed37cc3943d13ab7f0b649d20e7662c`.
`preflight-stop-replay.json` records its full independent replay.

## Exact candidate and reproduction

Final candidate workspace: `/home/mit/i960-doom-dma-20261014c`.
Boot `c44371f0-163e-41f0-8258-b54cc6982bad`, supervisor 2940.
`build.sh` preserves the transport-only build from the accepted engine.
`live.sh` preserves the finite physical test. The fresh-checkout wrappers are
`game/doom/play/build.py --work NEW --dma`, then, on the qualified exclusive host,
`sudo game/doom/play/run.py --work NEW --output NEW-CAPTURE --dma-test`.
Never force-unload retained resident resources or compete with another card owner.

Kernel SHA-256:
`d0f89f2dd509d1ed26d3b4e2213d6437f09e63d9127c6e0e462fce7ee3ad3ce4`.
Linux module SHA-256:
`2d8d94dfc19c01a83ba561ff689c11d87f0f70d4ecc5db42c799649063eec474`.
The layout audit passes; protected upload code is 28,304 bytes, engine gate code
11,904 bytes. No new RAM grant, ATU remap, flash write or engine change.

`pre-atomic-build-evidence.tar.gz` SHA-256:
`6b62092ceae1fd9e3990cf7129a1e365c968ee0c7d2b36c01a29f76323aecc87`.
This pre-atomic archive includes exact project/build inputs, generated target/module,
admission, disassembly, native wrapper/objects and both deterministic runs.
It is retained to explain the interrupted second startup, not for deployment. Source/newlib
and project artifact symlinks refer to the previously archived pinned inputs;
use the repository's existing source archives for fresh reproduction. Existing
RTEMS/lwIP patches remain supplied by the exact project builder.

## Host checks and independent replay

- Actual frame target under ASan/UBSan: exact DMA, independent CRC, stale and
  pending refusals, STOP, polling timeout, source/descriptor errors and quarantine.
- Actual kernel ioctl under ASan/UBSan: 21 exchange failure points, guards/CRC,
  pending status, stale generation/epoch, bounds, 32-bit mapping and copyout retention.
- Actual Python client with modeled ioctls: 28 frames, 16 full guarded captures,
  four exact pairs, A/B/B/A, all input/ACK events and 22 rejected mutations.
- Existing channel, STOP, scalar/paired request, MMIO polling and replay-duration
  regression checks pass. Two native Doom runs match exactly.

`verify_play_dma.py` reconstructs every payload from original ioctl responses,
checks complete guard captures, report metadata, CRC, raw/PNG/hash identity,
four mailbox/DMA pairs, all input/ACK events and owned STOP. Run it alongside
`residentnet/verify.py`, which checks the full system snapshots and RAM audits.
`tamper_play_dma.py` mutates copies, never original evidence. `analyze.py`,
`journal_costs.py`, `observe_http.py` and `http_summary.py` preserve measurements.

The second interrupted startup is preserved in `pre-atomic-stop-evidence.tar.gz`
(SHA-256 `f00c979c3d44a241e91de9f0cd5f15fa11e155d34b82bf035e208f38da964d4a`),
with `pre-atomic-stop-replay.json`. It pairs with the pre-atomic build archive,
not the final atomic-release candidate.

Final atomic-release `build-evidence.tar.gz` SHA-256:
`2c9f933987d5c1f5140c6be369547277fbec4dfb307c5b363e2c2089bc00a254`.
The disassembly confirms priority masking spans the phase check and all pointer
clears, followed by restoration. It uses the same established i960 priority-mask
sequence as the runtime locks.

## Replaying this failed capture

Extract `build-evidence.tar.gz` and `failed-card-evidence.tar.gz` into the same
new directory. From this Git checkout, run:

```sh
python3 artifacts/doom-dma-20261014/verify_failed_system.py EXTRACTED
python3 artifacts/doom-dma-20261014/verify_failed_frames.py EXTRACTED/live
python3 artifacts/doom-dma-20261014/tamper_failed_frames.py EXTRACTED/live
python3 artifacts/doom-dma-20261014/compare_prefix.py EXTRACTED
```

These dated tools deliberately validate only this failed prefix and require its
failure evidence. `verify_failed_system.py` executes the unchanged pre-terminal
checks of the full verifier, then explicitly requires that full acceptance
rejects the capture. The ordinary `verify_play_dma.py` and `verify.py` retain
all successful-run requirements. `close_capture.sh` is the planned successful
closure procedure; it refused this failed run as intended. No successful
`card-evidence.tar.gz`, A/B/B/A result or DMA FPS number was manufactured.

## Restoration

After all closed evidence was hash-verified and prefix-replayed locally, reboot
released the retained resources. Boot `91493f0a-3c46-4afa-a40c-6b62ad8304be` now
runs the existing public autonomous relay, supervisor 1604 / Python 1675.
IPv4/IPv6 ping, UDP and TCP startup tests passed. The Mac received HTTP 200 from
[the public page](http://[2a02:8106:40:9000:f662:19ee:dbad:1f1e]:8080/).
`restoration.json`, `restore-relay.log` and compressed raw HTTP headers/body
preserve those checks. Private visitor statistics remain on the host. The
public relay owns the card; coordinate and stop it normally before new tests.
The bounded Doom endpoint on port 8087 is closed.
