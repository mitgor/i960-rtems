# Accele160 exclusive SCSI stop and isolation contract

This is a staged contract, not a claim that SCSI/DMA isolation is established.
The primary host ATU/MU, BIU and RTEMS host-DMA path must remain operational.
The existing stock-firmware coexistence approach stays a separate future option;
an uncertain exclusive transition never returns to stock firmware or frees RAM.

## What the mechanisms actually establish

| Mechanism | Evidence / meaning | What it does not establish |
| --- | --- | --- |
| Owned i960 interrupt/fault/NMI tables and paused stock callback | Existing runtime prevents the captured stock callback and old ISR dispatch from running during the probe | Exhaustive audit of every stock timer/watchdog/callback or private bus master |
| Equal request/response indices | Profile 17 observed chip consumer 37 versus cached 0, producer 37; response 22/22 | DMA completion, empty FIFO, no SCSI command still executing |
| HCCR `2000`, read PAUSE bit `0020` | QLogic RISC pause acknowledgement; profile 18 qualifies this transition | Halt/drain of independent command/data DMA or SXP |
| HCCR `3000`, PAUSE clear | Release of the paused RISC, qualified by profile 18 | Restoration of SCSI service or proof that no external work was disturbed |
| BIU_ICR soft reset `0001` | Stock reset routine and FreeBSD initialization reset the chip | Graceful completion or preservation of queued work |
| DMA clear-channel/reset-interrupt commands | FreeBSD reset path explicitly treats command/data DMA separately | Any completion proof if evidence is cleared first |
| PCI bus-master disable or bridge arbitration disable | Potential prevention of future master grants, after device/slot proof | Outstanding transaction/FIFO drain or safe RAM reuse |
| 80303 secondary-bus reset | A broad reset affecting bridge queues and DMA2/secondary ATU | A targeted SCSI-only transition that preserves all host transport |

## Pinned stock-firmware evidence

Expanded runtime SHA-256:
`09e84895223627edeff8f1a6902d2a9a573c2c3e7769a5ea16caaa32cf07e3db`.

At `c006b18c..c006b254`, the routine uses context `+28` as the chip mapping.
It writes ICR soft reset, HCCR reset `1000`, release `3000`, then pause `2000`;
reads RISC state; selects bank `0300` through CONF1; reads `+80`; restores CONF1
to zero and releases again. This is a reset/initialization routine with delays,
not a graceful-stop API. Its complete sequence is not invoked by profile 18.

The pinned queue/mailbox audit remains relevant: request publish `c0070a98`,
response callback `c006ef80`, consumer `c006f8f0`, pending enqueue `c0070ad0`, and
mailbox transaction `c006bc30`. A stock callback can consume responses and
publish pending requests; mailbox operations share the index registers. The
probe issues no stock mailbox command and does not resume the pending callback.
DMA1 still references stock descriptors; keep it and all firmware ranges reserved.
No exhaustive caller or descriptor-lifetime audit has been completed.

## Register-bank hazard

FreeBSD's ISP1080-family accessor selects the DMA bank using CONF1 bits `0300`.
Its DMA register offset is `60` plus the logical register offset, so DDMA_CONF
at logical `40` aliases physical `c0`, the normal HCCR address. Writing HCCR
without checking the bank can therefore address the wrong register.

Profile 18 reads CONF1 and ICR first, refuses nonzero bank bits or soft reset,
and never writes CONF1. A future paused bank snapshot must save CONF1, select
only the documented bank, read only qualified registers, and restore CONF1
**even if its saved value was zero** before any HCCR access. A bus fault makes
restoration uncertain; retain everything and reset. Do not use 1040 direct DMA
offsets or 2300 queue registers on this 10160.

## Qualified boundary and remaining implementation

1. Preserve a checked identity/config/RAM/queue snapshot and the owned i960
   environment. Refuse pending lists, active exchanges, unsettled indices,
   mailbox lock, unexpected control state or mismatched metadata.
2. Qualify pause/release with two halfword writes and bounded polling. Profile
   18 is one-shot, ready-phase only; it preserves its result through frame32,
   idle and STOP. Native tests cover timeouts and retry refusal. Physical success
   covers only the observed quiet workload, not a busy or stalled SCSI workload.
3. Next: while paused, qualify a minimal banked **read-only** command/data-DMA
   snapshot with unconditional bank restoration and native fault-path tests.
   Establish exact active/FIFO/error semantics before using it as a drain gate.
   SXP status reads need their own access/side-effect audit. Pause is not drain.
4. Then choose and test an exclusive stop policy: prove drain if possible; if
   uncertainty remains, retain buffers/descriptors and require reset. Establish
   how to keep all relevant producers stopped and prevent re-enabling masters
   before any held-reset or master-disable experiment. Do not clear evidence
   or report completion because a channel was disabled.
5. Qualify sustained RTEMS host DMA, guards, STOP and reboot recovery after the
   eventual isolation transaction. Only then combine hardware exclusion with
   allocator, firmware-dependency and alias proofs for additional RAM ownership.

## Primary source basis

- FreeBSD releng/12.4 `sys/dev/isp/ispreg.h`: bank selections, HCCR commands and
  status bits; `isp_pci.c`: ISP1080 bank access and paused diagnostic snapshot;
  `isp.c`: RISC pause plus separate chip/DMA reset operations.
- Linux v6.1 `drivers/scsi/qla1280.h` / `qla1280.c`: QLogic-authored 16-bit
  register interface, pause/release commands and diagnostic usage. Its direct
  cdma/ddma struct fields are explicitly marked 1040-only.
- Intel 80303 manual 273353-001 sections 14.15, 17.6 and 20.11 constrain bridge
  reset, arbitration and AAU; see the preceding engine audit.

Exact source snapshots, URLs, SHA-256 values and stock-firmware disassembly are
preserved in the [profile-18 artifacts](../../../artifacts/current/accele160-qlogic-pause-20261019/README.md).


## Profile 19: DMA-window inspection completed

The [paused-bank transaction](PROFILE19.md) now verifies selection and exact,
unconditional restoration of CONF1 before any HCCR release. Both six-register
passes agree; command/data status `0008` has the reference terminal-count bit
set, channel/pipeline masks zero and FIFO status zero. These are observations,
not a hardware exclusion guarantee. All stock DMA/SCSI RAM remains reserved.
The separate application-loader work uses only the already validated upper
arena and does not depend on widening this ownership claim.
