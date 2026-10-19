# Profile 19 — paused DMA-bank inspection

On Accele160 `0000:37:09.1`, the physical ISP10160 at core base `8bf00000`
passed one pause/select/read/restore/release transaction. Profile 18's exact
PCI identity, queue context, idle observation and initial-control gates remain
mandatory. Profile 19 adds twelve 16-bit loads: two passes over command DMA
configuration/status/FIFO status at physical `80/84/86`, then data DMA at
`c0/c4/c6`. These are the ISP1080/12160 DMA-window offsets, not ISP1040 offsets.

The FreeBSD 12.4 ISP1080 accessor selects CONF1 bits `0300`, and the driver's
paused diagnostic reads these six registers. References are preserved with the
profile-18 source archive, copied into this batch. No DMA control/count/address,
FIFO data, SXP, or mailbox command register is written by this new helper.

## Captured result

- CONF1: `0074 → 0374 → 0074`; exact selection and restoration read back.
- HCCR: `0000 → 0020`; still `0020` after bank restoration; release to `0000`.
- Pause/release each acknowledged on the first poll.
- Both DMA passes: command `{config:1,status:8,FIFO:0}`;
  data `{config:8,status:8,FIFO:0}`.
- ISR stayed zero, semaphore 2, chip request/response indices 37/22.
- 64 frames, 5,045 WAD reads, 709 external console exchanges, zero errors.
- Ready/frame32/idle/final STOP retain the same one-shot record.
- Final STOP acknowledged QUIE; pending callback/pins retained, guards unchanged.

The reference PCI status definitions label bit `0008` as terminal count /
transfer completed. Their channel and pipeline masks, and the FIFO count mask,
are zero in these samples. These are observations under those definitions;
status `8` is recorded without declaring the controller stopped or drained. A paused
RISC does not prevent an already launched engine from bus mastering. This
experiment grants **no new RAM** and does not disable SCSI.

An initial run completed this same register transaction but rejected the Doom
upload because an older generated engine-identity header had been copied into
the candidate bundle. Its archive/log remain alongside the successful repeat.
The correct bundle-generated header was restored before rebuilding and resetting.

## Failure policy and report

The existing pause latch prevents retries after success or failure. Selection
mismatch skips all DMA reads, then attempts unconditional restoration of the
saved CONF1. Restoration is attempted even when saved CONF1 is zero. A failed
restoration comparison forbids HCCR access; a changed paused HCCR or failed
selection forbids release. A bus fault may prevent the restoration instruction
itself: the owned containment path retains resources for reset, not rollback.

Words 464..511 in the existing 4 KiB report:

| Words | Meaning |
|---|---|
| 464..468 | QDB1, version 1, nonce, origin sequence 1, result |
| 469..473 | saved/selected-request/selected-read/restored CONF1; paused HCCR |
| 474..475 | CONF1 writes (2), DMA reads (12) |
| 476..479 | zero |
| 480..491 | two six-register passes in the order above |
| 492..511 | zero |

Result 0 means the transaction completed; 1 is selection/read in progress,
2 restoration mismatch, 3 changed paused state, 4 failed selection/read count.
The parent pause report also fails on any nonzero helper result. Poll loops
remain limited to 10,000 accesses; a stalled bus access has no wall-clock bound.
Native tests cover failed selection, failed restoration, lost pause, zero saved
CONF1, pause timeout, exact access order, duplicate suppression and report bounds.

Evidence: [artifact batch](../../../artifacts/current/accele160-qlogic-dma-bank-20261019/README.md).
Next hardware ownership work: establish precise ISP10160 DMA/SXP status and
stop/drain semantics before any disable or RAM-reclamation experiment.
