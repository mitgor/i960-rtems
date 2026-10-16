# Pinned Doom frame DMA/mailbox comparison

**Latest:** the [finite frame stress test](../../artifacts/notes/frame-dma-stress-20261014.md)
reproduced the timeout at frame 41: a scheduled peer's heap check rejected an
intentionally active, owned DMA transaction. The ownership-aware isolation check
passed 512 frames, 89 observed active-transaction checks, 20 full mailbox pairs,
30 full monitor/RAM audits, owned STOP and global drain. No timeout bounds or
completion checks were relaxed. DMA stays opt-in pending a fresh Doom comparison.

Earlier complete Doom comparisons measured 42.45–43.26% higher delivery FPS
(about 0.97→1.38); those predate this fix. The stress producer's 2.9759 FPS is
**not Doom FPS**. See the [previous diagnosis](../../artifacts/notes/doom-dma-cleanup-20261014.md)
and [original failure](../../artifacts/notes/doom-dma-20261014.md).

Opt-in bounded acceptance: build `game/doom/play/build.py --dma`, then run
`game/doom/play/run.py --dma-test` in a fresh isolated workspace on the qualified
exclusive DAC960PG. This is not the default play transport. The frame, engine
image, 12 MiB ownership profile and full monitor/RAM audits stay unchanged.

## Pin and task ownership

The existing renderer publishes exactly 65,536 immutable bytes and waits for an
ACK. The existing RTEMS worker performs DMA preparation, pre/post CRC32 and
bounded completion polling inside that wait. IRQ control only stages a kernel
DMA destination, submits the current generation or reads a frozen report.
ACK and job mutation are denied while phase 1 is pending. No third IRQ owner or
stack is introduced. On success, phase 2 is published after engine isolation,
source CRC equality and descriptor guard checks.

`play_clear()` masks interrupts across its pending check and pointer clear, then
restores the previous priority. It refuses pending DMA: STOP or the frame timeout can race with
submission after the worker's initial pending check. Any such release attempt
enters the existing nonreturning fault quarantine. The frame/image and coherent
mapping remain pinned. Error, polling exhaustion and uncertain transfers never
permit ACK, image reuse, unload or firmware return. A STOP after all benchmark
frames still follows the existing owned and global drain paths. Graceful
cancellation of a queued frame-DMA job is not claimed by this prototype.

A read-through source CRC is calculated both before and after DMA; the host
checks every payload byte through Linux CRC32 and checks every guard byte.
Four full DMA/mailbox comparisons establish bytewise equality independently of
the CRC. Every DMA frame captures all 73,728 coherent bytes for independent
replay, not only a checksum. Full paired system audits are mandatory throughout.

## ABI

The dedicated ioctl is `0xc4204d08`, with eight little-endian u32 header fields
and 1,024 payload bytes. Header: op, epoch, generation, offset, four zero words.
All request payload bytes must be zero. The kernel supplies the DMA address;
users cannot supply host/card pointers or transfer lengths.

- Op 1: submit fixed 64 KiB, offset zero, strictly increasing generation.
- Op 2: poll completion, offset zero; EAGAIN means pending. On completion, return
  the 16-word report followed by zero padding, only after CRC/guards/generation
  validation. Each command has the existing absolute ten-second transport bound.
- Op 3: read a validated full coherent buffer in 1 KiB windows, offsets 0..72704.
  Payload begins at 4096 and ends at 69632; both 4 KiB guards remain `a5`.

MU opcode 0x6b indices 3, 4 and 5 stage the DMA destination, submit a generation
and read a report word. Existing public upload ioctl index limits remain 0..2,
so these new indices are exposed only through the checked DMA ioctl. The report
is magic `0x314d4446`, phase, generation, destination, source, before CRC, after
CRC, CSR, DAR, NDAR, BCR, DCR, poll count, error, zero, descriptor address.
DMA1 uses DAR1 at **0x144c**, single descriptor/Memory Write 7, no IRQ/no DAC,
primary bus master only during the transfer. Success requires inactive/error-free
CSR, consumed NDAR, matching DAR, zero BCR, all-channel isolation and guards.
CCR disable is not an abort proof. Any uncertainty retains resources until reboot.

The kernel releases its mutex between poll calls. The Python benchmark holds
its reentrant audit gate only across one bounded DMA capture, preventing a full
monitor snapshot from sampling the intentional bus-master interval. Audit
requests are delayed rather than skipped, and all fields retain their checks.
The pinned generation is rechecked and the first payload window reread before ACK.

## Measurement and limitations

The first four frames are read through both DMA and paired mailbox transport.
Then frames 5–10 use mailbox, 11–16 DMA, 17–22 DMA, and 23–28 mailbox. Comparisons
are excluded from FPS blocks. Both methods retain first-window reread and live
generation checks; every DMA capture includes source CRC and complete guard
validation. Fixed forward/release input matches the accepted native 28-frame run.

Run `verify_play_dma.py` alongside `residentnet/verify.py`; neither replaces the
other. Native tests execute the actual target/header and kernel ioctl, exercise
all exchange failures and retain-before-release behavior, and run the actual
capture client against a model with independent replay. Report transfer latency,
server delivery FPS and HTTP observations separately; do not label HTTP receipt
as browser paint time. Compare against the unchanged admitted engine and preserve
known small native/card pixel differences instead of silently accepting new ones.

The proof supports one owned engine invocation per resident session. Reusable
mapping lifetime, generation restart, disconnect/recovery and production DMA
play remain separate acceptance work. Initial level load is unchanged.

## Failure-only terminal diagnostics

The current diagnostic candidate adds persistent phase markers and an iteration
counter. If the terminal fault owner runs, it freezes the DMA report and live
CSR/DAR/NDAR/BCR/CCR/PCI-command fields before other fault reporting. Terminal
read indices 64–95 expose that frozen extension. Existing normal completion and
full audit protocols are unchanged.

After a failed frame-DMA exchange poisons the driver, a separate diagnostic
helper can request the existing terminal read protocol. It has a two-second
total deadline and 2,000-poll per-word cap, checks masks/doorbell and exact
NMF1/epoch identity, and writes only read-request tokens. It cannot ACK, resume
RTEMS, disable DMA, clear poison or free retained resources. The captured
`frame-dma-fault.bin` is 100 little-endian words: FDF1 magic, epoch, received
word count, diagnostic error, then up to 96 frozen terminal words. Error values
are 1 deadline, 2 mask/doorbell, 3 poll exhaustion, 4 wrong terminal identity.

Use `python3 rtems/dma/decode_frame_fault.py PATH` for diagnosis. This is negative
evidence only, including when all 96 words arrive. A card that never reaches the
terminal monitor may produce no verified terminal identity. Destination arrival
and diagnostic visibility do not prove DMA retirement. See the
[diagnostic experiment](../../artifacts/notes/doom-dma-cleanup-20261014.md).

## Isolation during scheduled DMA

The strict idle postcheck remains mandatory outside the narrowly validated
DMA1 transaction. During stages 4–10, `frame_dma_isolation_snapshot()` validates
the current pin, sequence, addresses, complete descriptor and allowed engine
states before adjusting a local snapshot. Secondary reset/arbitration and other
engine checks still run unchanged. This permits a peer heap check while the DMA
worker is preempted; it does not mask interrupts or skip guards. Final completion
still requires idle hardware and bus mastering disabled.

Control `(5,16)` is a read-only count of recognized active-transaction checks.
Only DMA-enabled host builds expose it, and the builder emits the corresponding
feature macro. The stress runner checks initial zero and final positive values.

## Doom acceptance with the isolation fix

The [fixed repeat](../../artifacts/notes/doom-dma-fixed-20261014.md) passed all
28 scripted frames, four exact paired reads, sixteen guarded DMA captures,
29 full monitor/RAM pairs, owned STOP and global drain. Independent Linux/macOS
replays and 30 frame/journal plus 24 snapshot mutations passed. All 28 frame
buffers match the earlier physical run exactly; the known native/card rendering
difference remains unchanged.

Mailbox delivered 0.972816 FPS and DMA 1.376781 FPS, a 41.525% increase.
Mean transfer decreased from 503.489 to 228.797 ms (2.2006×). These are bounded
server delivery measurements; HTTP receipts are recorded separately and no
browser paint-rate claim is made. No timeout, validation or audit was relaxed.
The fixed runtime source is unchanged from the 512-frame stress acceptance.
DMA stays opt-in until longer interactive input and lifecycle tests pass.

## Optional CRC and two-buffer delivery

The [pipeline experiment](../../artifacts/notes/doom-pipeline-20261014.md)
adds explicit per-submit CRC selection: operation 1 offset word 0 means checked,
1 means unchecked, and other values are refused. Operations 2/3 retain their
existing offset contracts. Kernel-only control index 6 configures the target;
it is not exposed by the general upload control ioctl. Completion report word
14 echoes the selection. CRC-off requires both CRC words to be zero; checked
mode requires both source CRCs and the destination CRC to agree. All descriptor,
bounds, generation, guard, completion and quiescence checks still apply.
The driver pins its expected mode across pending polls and checks the report
against it. A mismatching mode is a protocol fault, not permission to skip CRC.

A separately admitted `ENGINE_PLAY_DOUBLE` image uses two alternating slots.
The engine task prepares at most one frame ahead, waits for the old ACK before
publishing the new slot, and services DMA only at task-level input/wait points.
The host copies and validates the complete destination before ACK; HTTP then
uses immutable host bytes. No browser operation owns a card buffer. CPU CRC and
rendering do not execute concurrently, and no new interrupt-context work or
unbounded queue is introduced. The finite runner compares CRC modes while
retaining full system audits. Physical results belong to the dated experiment;
old single-buffer captures keep their original strict verifier.

The accepted 52-frame repeat passes 29 full audit pairs and STOP/drain, with
1.396095 FPS CRC-on versus 2.070201 FPS CRC-off. Full local/remote replay rejects
35 frame/journal and 24 snapshot mutations. The original candidate exposed a
WAD/DMA wait dependency: pending DMA polling must service the WAD channel,
because the renderer can need WAD data before reaching a DMA service point.
This is now regression-tested; no deadline was extended. A separate startup
TCP failure is preserved, and the harness now requests owned STOP while keeping
audits active before propagating such network failures. See the dated ledger
for both incomplete attempts, accepted evidence and exact performance limits.
