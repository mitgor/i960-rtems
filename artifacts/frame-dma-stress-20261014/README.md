# Reproducing the frame DMA timeout — 2026-10-14

The small admitted producer reproduced a completion timeout at frame 41. The
frozen diagnostic record identifies a software isolation halt during an owned
DMA transaction, rather than exhausted DMA polling. The final fixed build passed 512 frames, 89 active-transaction isolation checks,
owned STOP, global drain and 30 full monitor/RAM audit pairs.

## Reproduction

Baseline kernel `3c7bc27fcc41ce718d8508b1da1eee147537190a0865ebe42a4473ee13a5e34d`,
module `ba57ed74b8b8c9860ef3b15d5c2817b54f92ad55a17412915a7121240d0de03f`.
Boot `333a779d-bfd4-4a59-8562-1cce3176b5e6`, Python owner 29678. The public relay
was stopped normally with SIGTERM and released the module before this run.

A 372-byte admitted executable replaces Doom and WAD startup with a deterministic
65,536-byte frame. Its total code/data/BSS span is 131,504 bytes. It uses the same
segmented admission, relocation, arena pin, owned invocation, actual DMA worker,
host coherent buffer, mailbox comparison and ACK paths. It binds WAD identity
metadata but makes **zero WAD reads**. The separate result version and manifest
prevent it being mistaken for Doom. See [the harness](../../rtems/dma/stress/README.md).

Forty frames passed exact byte checks. Frame 41's DMA poll ioctl timed out
(`ETIMEDOUT=110`); the next full audit refused the poisoned transport. The retained
frame 41 bytes and both guards were exact, but the transfer was **not accepted**.
There were five complete monitor/RAM audit pairs and two heap diagnostic pages
before failure, without final STOP or drain. Independent prefix replay rejects
24 snapshot mutations; the full acceptance verifier correctly rejects this run.

The failure-only terminal reader captured all 96 words with the correct epoch:

- Software abort, trap kind 4, not a hardware fault.
- Heap error 1: `general_heap.c:enter_op()` rejected `exclusive_extra_valid()`.
- SCSI isolation verification false; exception ownership and guards remained valid.
- DMA generation 41, phase 1, stage 7, poll iteration 49 of the unchanged 200,000 bound.
- CSR=0, NDAR=0, BCR=0, DAR points at the descriptor: DMA had completed.
- CCR=1 and PCI command=6: cleanup had not executed when the peer task halted it.

The call chain explains the timing dependence. RTEMS preempts the DMA worker;
a peer's heap check follows `exclusive_extra_valid()` into
`scsi_target_verified()`. The old `scsi_stop_postcheck()` required **every** DMA
engine idle and PCI command=2, including the intentionally active, exclusively
owned DMA1 transaction. That valid transient state therefore poisoned the heap
and entered the terminal handler. The host subsequently saw a completion timeout.
This reproduces the earlier symptom; the original frame-12 capture had no frozen
heap/phase record, so its precise cause cannot be proved retrospectively.

## Fix and unchanged checks

The strict idle check remains the first path. Only DMA-enabled images can use
the new task-owned transaction check. It verifies the pending phase, stages 4–10,
pinned source and generation, no ACK, exact source/destination/descriptor bounds,
all eight descriptor words, allowable channel-1 transitions, no DMA error bits,
and no unrelated active engines. It normalizes only DMA1 CCR/CSR and the primary
PCI command in a **local snapshot**, then reruns the existing strict secondary
reset/arbitration/isolation check. It never changes hardware for a check.

The worker still enables interrupts, retains its 200,000-iteration bound,
verifies completion registers, disables the channel and bus mastering, checks
source CRC before/after, and checks descriptor guards. Host and offline verifiers
retain all guards, full raw captures, CRC, generation checks and paired reads.
Full monitor/RAM audits remain unchanged. DMA remains opt-in.

Read-only frame control `(index=5,value=16)` exposes the count of checks that
recognized the owned active transaction. The finite stress run requires this
count to be positive as well as complete owned STOP and global drain. Native
ASan/UBSan tests exercise every published transition, all descriptor bit flips,
invalid engine states, wrong generation and the existing STOP/error paths.

## Reproduction and evidence

Use `build.sh` and `live.sh` in a fresh isolated workspace with the pinned source
and toolchain dependencies available. Remote workspace:
`/home/mit/i960-frame-stress-20261014`. `live.sh` requests 512 frames and full audits
every five seconds. Every frame captures 73,728 bytes; frames 1–4, each multiple
of 32 and the final frame also receive full mailbox readback. These are synthetic
producer timings, not Doom FPS.

`failed-build-evidence.tar.gz` and `failed-card-evidence.tar.gz` contain the exact
pre-fix sources/binaries and all negative evidence. They were copied and
SHA-256 verified locally before reboot. Extract both into one temporary folder,
then run `verify_failed_frames.py` and `verify_failed_system.py` against it.
Neither script promotes the failed run to acceptance.

`close_capture.sh` requires successful owner exit, runs both full verifiers and
capture tamper tests, then archives the fixed build and capture. Never force
unload a retained module; archive and replay before reboot. `restore.sh` restores
the separate public IPv6 service after the reboot.

## Intermediate diagnostic-query rejection

The first fixed target completed all 512 exact DMA frames, with no DMA timeout,
but the new read-only isolation counter request was missing from the host ioctl
allowlist. Linux returned `EINVAL` before sending it to the card, so owned STOP
and global drain were not reached. This is an incomplete run, not acceptance.
`counter-build-evidence.tar.gz` and `counter-card-evidence.tar.gz` preserve it.
All 512 captured payloads and guards were independently checked locally before
reboot; their archive hashes were verified too.

The host now permits only the specific read-only `(5,16)` query when compiled
with `I960_DOOM_DMA`; DMA destination and submit controls remain inaccessible
through that ioctl. Native tests compile the actual validator both with and
without DMA and check its allowlist and nonzero-tail rejection. The stress client
also checks a zero counter before entering the producer, catching missing support
early, and requires a positive count before STOP. The RTEMS target binary is
unchanged between this incomplete run and the final repeat.

The added early check then caught a second integration omission: the transport
builder used the DMA build flag to insert its ioctl, but did not emit the
`I960_DOOM_DMA` C macro used by the new allowlist branch. That attempt submitted
no frames; `counter-preflight-evidence.tar.gz` preserves its driver and capture.
The builder now emits the macro, and `test_counter.py --generated <driver.c>`
checks the actual generated source before hardware admission. This capture too
was copied and hash-verified before reboot. Neither integration failure changed
the RTEMS target binary or demonstrated another DMA timeout.

## Final physical acceptance

Boot `01d9ea46-6579-4be4-9f6f-f4213288de2d`, supervisor 2872. Kernel
`405754153149481ea2ca2fde0b03b2b38d59125d83e998e411c781e6fc513e35`, module
`957ad52c1d70916a9a7d659c57c058dc065dfd1be8d80580ae8c7b6e37c3787b`.

- **512 exact frames**, including 20 complete mailbox/DMA comparisons.
- **89 active-transaction isolation checks**, observed on the actual card.
- **30 full monitor/RAM audit pairs**, including final STOP/drain acceptance.
- 37,748,736 coherent bytes captured; all payloads, both guards and rereads passed.
- 23,963 bounded pending polls; no completion timeout or DMA error.
- Owned STOP and global STOP completed; final tick 19,574, reason 1.
- Zero WAD reads; 174.051 seconds for the finite engine operation.
- 2.9759 synthetic frames/s from first to last delivery, including full audits
  and the selected mailbox comparisons. DMA capture averaged **225.58 ms**
  (median 226.33 ms, range 214.40–233.25 ms).

This fixes the reproduced software isolation halt under the tested schedule.
It does not establish indefinite stability or a new Doom FPS improvement. The
next application acceptance is the same pinned Doom frame A/B/B/A comparison
with this fixed worker, followed by longer interactive testing. Keep DMA opt-in.

Both full verifiers pass remotely and again on the locally extracted closed
archives. Capture tamper testing rejects **34** corruptions, including ACK,
owned STOP, isolation counter and paired-read evidence; the system verifier
rejects **24** snapshot corruptions. Native modeled replay separately rejects
22 corruptions. See the JSON and native logs alongside this README.

Closed accepted archive SHA-256:

- Build: `f5d318bf75169a041a36a94ffd2dd82f74fd0ca46a0c16a1617ffc7fd82247c4`
- Card: `fb50e284c76bedc7783d9026f3ace7e2dcf479e1410d228529c924236712a522`

Extract both into one temporary directory, run
`rtems/residentnet/verify.py --root <directory> <directory>/live`, then
`rtems/dma/stress/verify.py <directory>/live`. `tamper.py` tests temporary copies;
it never changes original evidence. Exact binaries are included in the build
archive; `build.sh` provides the source reproduction commands.

## Restoration

After local archive hashes and both full replays passed, reboot released the
retained module. The public relay is restored: supervisor **2430**, Python
**2432**, boot `5ae888c7-143b-400b-80ea-5e2a24392de6`, card `0000:37:09.1` bound
to `dac960auto`. The Mac received HTTP **200** with the RTEMS page from the public
IPv6 endpoint. `restoration.json` and compressed headers/body record this check.
The stress reservation is released; the public relay now owns the card.
