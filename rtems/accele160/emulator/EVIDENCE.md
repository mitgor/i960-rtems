# Controller emulator run record, 2026-10-25

All runs used the x86-64 Linux host at `192.168.2.80`, g++ 11.4 with
`-std=gnu++20`, and the locally vendored sim5 adaptation. Only saved local
images were read; no PCI or flash operation was performed.

| Input | SHA-256 |
| --- | --- |
| Original stock flash | `0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a` |
| Spare stock flash (`rawflash-0/data.bin`) | `fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816` |
| Original-card native-ROM candidate | `3f97745c76bd2d5e71a5ee143c9c9fec86bdb6a9d4a4b1202093eb944767909c` |
| Failed spare native-ROM candidate | `6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd` |

Default strict comparison: stock and candidate stop at cycle 56 on the first
unmodeled read, `0xe0400000`. The preceding writes to the documented 80303
core and flash-bank configuration registers are recognized at their observed
reset values. The register side effects and SDRAM controller are not complete.

Historical exploratory comparisons before the Jx instruction corrections,
with unmodeled registers backed by zero-filled storage:

| Board selector override | First stage-two divergence | Stock terminal | Candidate terminal |
| --- | --- | --- | --- |
| unset, response zero | cycle 232,069 | self-loop `0xc000a858`, cycle 1,318,217 | CPU fault at `ret` `0xc0010d50`, cycle 481,019 |
| 6 | cycle 232,069 | self-loop `0xc000a858`, cycle 1,318,201 | same return fault, cycle 481,019 |
| 8 | cycle 232,073 | self-loop `0xc000a858`, cycle 1,318,195 | same return fault, cycle 481,023 |

These historical runs exposed an emulator error. The ZIP1 archive's literal
tree flag is clear; [Intel's Jx instruction reference](https://www.bitsavers.org/components/intel/i960/272483-001_Intel_i960_Jx_Microprocessor_Users_Manual_Sep94.pdf) specifies that `chkbit`
sets condition code `000` when its bit is clear. The vendored interpreter did
the opposite, so stock incorrectly tried to build a 256-entry literal tree
from a valid 64-entry tree. It then skipped decompression and failed its CRC.
The interpreter now implements the documented `chkbit` condition and the
missing signed/unsigned short comparisons, and masks byte comparisons to
their low eight bits.

The whole-card comparison gate remains **INCONCLUSIVE**. The stock loader now
reaches its runtime entry; a coupled x86/PCI/i960 model must still exercise
firmware-dependent host behavior before another flash experiment can be considered.

## Measured post-boot byte on the original card

On the later boot `d6818bde-e292-44ca-979d-612fb48154c4`, two bounded
operation-13 RAM calls on the original card read `0x0b` from `0xe0400000`.
Both calls returned cleanly; full flash, loader page and allocator audits are
in [the capture](../../../artifacts/current/accele160-board-id-20261025/README.md).
This is a post-boot byte, not a measured reset-time value or a measurement on
the failed spare. The reset-block disassembly uses an `ldob` at the same
address for the cycle-56 read.

With `--explore --board-id 11` and the original card's saved stock/candidate
pair, the first trace divergence is at cycle 1,354,523. After the ISA fixes,
stock builds two 64-entry Huffman tables, expands ZIP1 with computed and stored
CRC `d93addd1`, and reaches `c004cf70` at cycle 48,565,709. It has no CPU
fault through the 100,000,000-instruction budget. The standalone Jx
microprogram passes `chkbit`, `cmpis`, `cmpos`, `cmpib`, `cmpob`, `scanbit` and
`spanbit`; the pinned
stock loader gate passes. The [run transcripts](../../../artifacts/current/accele160-emulator-isa-20261025/README.md)
record the images, executable and checkpoints. The exploratory model lets
later writes to the board byte replace the initial override, but still records
unmodeled register accesses.

Both candidates reach their RTEMS payload and report `SGT2`, stage-two result
`0x2000`, 15,840 copied bytes, and `RTEM` (entered RTEMS). Correcting the
interpreter's call/return frame ownership and Jx 16-byte frame alignment
restores the saved context and resumes at `__Thread_Handler` (`c0013bf0`).
The interpreter's `scanbit`/`spanbit` originally returned the least significant
matching bit instead of the most significant one. Correcting both allowed
RTEMS to select Init. The pinned [candidate scheduler gate](candidate_scheduler_gate.py)
passes: task create/start return zero, the worker runs 64 iterations, `done`
is 1, the marker is `PASS` (`50415353`), and the image parks with code zero at
`c0010030` after 1,608,278 instructions. The exact image programmed to the
spare produces the same controller-side result. Both stock images also reach
the same CRC and runtime entry. This is an offline simulated CPU
path, not proof that physical hardware would take the same path. A matching
x86 PCI identity/BAR probe exists, but the controller's host-facing mailbox
is not coupled to it. The physical POST
failure remains unexplained and the flash gate is inconclusive.

The stock and candidate x86 option-ROM bytes at flash offsets
`0x30000..0x36fff` are identical (SHA-256
`96d5d8996099ad587533f50caebe18c0211eb4a555f17027a75763f4e633b47a`).
They pass the 55AA size/checksum and `PCIR` `1069:0050` checks. An isolated
QEMU 6-second TCG run using `-option-rom` executed the ROM entry at `0xc0003`.
This is a generic host-side smoke test only. A later
[matching PCI probe](../../../artifacts/current/accele160-qemu-pci-probe-20261025/README.md)
ran the same ROM on a `1069:0050` QEMU device. SeaBIOS reached its entry but
made no BAR0 or extended-configuration access in the bounded run; the stock
and candidate ROM traces were identical. A subsequent
[live RAM bridge](../../../artifacts/current/accele160-qemu-live-bridge-20261025/README.md)
connects QEMU's upper BAR page to the i960 interpreter and verifies PIATVR
remapping against both saved spare images. That stage did not complete a host
mailbox command, model DMA/IRQ, or reproduce physical POST. The flash gate
remains inconclusive.

The next [LP mailbox transport gate](../../../artifacts/current/accele160-qemu-mailbox-20261025/README.md)
replays Linux `myrs`'s first 64-byte `SET_MEM_MBOX` submission through guest
RAM and PCI DMA. QEMU and the interpreter trace receive the exact request
for stock and the failed-spare candidate. Both remain pending because the
interpreter has no controller-side mailbox handler or host status DMA. This
transport result does not change the inconclusive flash gate.

The follow-up [stock mailbox diagnosis](../../../artifacts/current/accele160-stock-mailbox-diagnosis-20261025/README.md)
identifies a separate initial hardware-mailbox path. The saved stock runtime
dispatches inbound-doorbell bit 0 at `c004e870`, which calls the receive
routine at `c004e660`; that routine reads the two MU message words at
`0x1310/0x1314`. In a 100-million-instruction exploratory stock run, neither
path executed, and the later memory-ring pointer remained zero. The QEMU
bridge currently traces the 64-byte request without latching these MU
registers; the interpreter treats MU status registers as plain storage and
its `Core::serviceInterrupt` remains unimplemented. A synchronized host
event, MU register side effects, i960 interrupt entry, and DMA/status
handling are required before a stock command-completion comparison is valid.

The next [inbound MU latch gate](../../../artifacts/current/accele160-mu-latch-20261025/README.md)
adds a minimal message-register, doorbell, and status-bit model. QEMU's
hardware-mailbox bridge event now latches the guest DMA pointer; bounded
test-only CPU stepping and register inspection verify that the event remains
pending and that firmware-side clear writes affect the modeled bits. Both
saved spare images pass this register gate, the QEMU submission gate still
passes, and stock/candidate boot regressions pass. The 80303 Jx/Rx PRCB
interrupt-table and interrupt-stack offsets were corrected in the vendored
core. Stock's bounded state still points at the ROM PRCB/table and has
priority 30 with core interrupts enabled, but its MU inbound mask remains
`0xffffffff`. No interrupt handler, guest DMA read, or
command completion was observed or fabricated. The flash gate remains
inconclusive.

The [host-readiness probe](../../../artifacts/current/accele160-host-ready-20261025/README.md)
traced why stock never unmasked that MU interrupt: it waits for both local
PCI command words (`0x1204` bits 1+2, `0x1004` bit 2). Test-only staging of
both words passes the first gate, while either alone leaves stock waiting.
Stock next waits for inbound doorbell bit 1 at `0x1320`; the LP mailbox event
modeled above asserts bit 0. A separate exploratory bit-1 event advances the
firmware into later initialization, revealing an interpreter gap for
`dcctl 0`. Modeling that documented cache-disable operation removes the
fault. In a further 80-million-instruction bounded step, this synthetic path
has no CPU fault but has not reached the observed MU unmask or a completed
mailbox command. These staged inputs do not constitute a validated host boot.

The later [two-function QEMU gate](../../../artifacts/current/accele160-qemu-multifunction-20261025/README.md)
models the measured Intel bridge function 0 and Mylex RAID function 1, then
mirrors their host PCI command writes into the respective i960 local words.
Those QEMU writes alone release stock's first readiness wait. Stock still
awaits inbound doorbell bit 1, for which this model has no observed host
source. The gate does not explain the physical POST failure or establish
mailbox completion. In a coupled two-second SeaBIOS/stock option-ROM run,
both local PCI command words were `0x00000103` and inbound doorbell was zero.
Stock continued waiting at the first gate after another million instructions.
This shows that the bounded BIOS phase itself did not provide the required
bus-master command bits; the qtest host explicitly provided them.

The [LP initialization replay](../../../artifacts/current/accele160-lp-init-20261025/README.md)
adds the opening `myrs` ACK-status write at BAR0+`0x20`, provisionally mapped
to local doorbell bit 1. Through QEMU MMIO, this write releases stock's next
wait without a direct test-socket doorbell injection. The first 64-byte
`SET_MEM_MBOX` request also reaches the controller model. After 450 million
additional instructions, stock has crossed its boot marker and a calibrated
delay into the event loop, with no CPU fault, but MU remains masked
(`0xffffffff`) and the request remains pending. The LP bit mapping, driver
timing, interrupt entry, DMA read, and completion still need hardware-grounded
validation. The flash gate remains inconclusive.

The [MU mask gate](../../../artifacts/current/accele160-mu-mask-20261025/README.md)
adds a read-only bridge diagnostic for inbound `IISR & ~IIMR`. The MU latch
test confirms that a pending doorbell is blocked at reset, appears when mask
bit 2 is cleared, and disappears after a doorbell clear. A coupled stock
replay reports status `7`, mask `0xffffffff`, and zero unmasked sources after
20 million post-submission instructions. It still has no 80303 interrupt
routing, CPU interrupt entry, guest DMA read, or completion.

The [priority and timer diagnosis](../../../artifacts/current/accele160-timer-priority-20261025/README.md)
found that the vendored interpreter used the `modpc` dummy operand as its
replacement PC value. Correcting this and fetching ICON/IMAP0-2 from the
PRCB control table changes stock's event-loop CPU priority from 30 to 12 and
exposes the ROM's timer-0 map (`IMAP2=0x00080000`). Stock programs timer 0
with reload/count `0x0004c4b4` and mode `0x36`, but the emulator has no timer
countdown or interrupt entry. In the 450-million-instruction replay all
software event queues remain empty and the startup dispatcher, MU setup,
unmask, and receive paths remain unvisited. This narrows the next emulator
work to the timer and interrupt path without treating the pending mailbox as
a completed command.

The [timer-0 pending gate](../../../artifacts/current/accele160-timer-pending-20261025/README.md)
adds an opt-in one-bus-clock-per-instruction approximation. A synthetic
timer test passes divide-by-eight, reload, and TINT0 latching in IPND bit 12.
In the 450-million-instruction coupled stock replay, the timer expires 179
times and IPND remains `0x00001000`; stock eventually sets IMSK bit 12 while
running at CPU priority 12. The ROM maps TINT0 to vector `0x82` (priority 16),
whose table entry points to `0xc0000418`. No CPU interrupt entry is implemented
yet, so event queues stay empty and the mailbox remains pending.

The [interrupt-entry gate](../../../artifacts/current/accele160-timer-interrupt-20261025/README.md)
adds opt-in TINT0 delivery with an i960 interrupt frame and return path. A
synthetic ROM enters vector `0x82`, updates a RAM marker once, and returns to
the interrupted IP. An initial coupled stock run faulted after timer entry.
That diagnosis was **corrected** after dumping the installed stock runtime:
the older updater disassembly at `c001c5fc` showed an indirect call, while
the running stock image has `ret` there. Nested ISR calls overwrote sim5's
frame RIP with the handler's own return address. Interrupt return now uses
its separately saved interrupted IP. In the 450-million-instruction coupled
replay, timer 0 expires 179 times, 55 entries reach the handler at
`0xc0000418`, and there is no CPU fault. The timer-related word at
`c00c3690` advances to `0x23d`; MU setup/unmask/receive still have zero
visits, the inbound mask remains `0xffffffff`, and the Linux mailbox is
pending. The exact runtime page is saved in the linked gate artifact; static
addresses from the older updater image must be checked against it before use.
An additional exact-runtime dump shows the event loop at `c004d438` waiting
on four zero work sources (`c00c3700`, `c00c0300`, `c04016a0`, and the callback
object's `+0x118` word); its second queue count at `c03e1e20` is zero too.

The same offline coupled replay was extended to 900 million observed i960
instructions. Bounded installed-runtime dumps in the linked timer artifact
show the actual startup chain: `c004d640` initializes the board,
`c0054580` returns after programming timer registers, `c009fb60` creates a
startup monitor, and its `c009fcc0` callback allocates a workspace and calls
the scan scheduler at `c002f680`. The scan callback `c002f840` begins state 0.
At the replay limit the startup monitor is in state 14; it and the scan
callback have each run once. Timer 0 has 359 expirations and 235 delivered
interrupts, but MU unmask/dispatch/receive remain unvisited, with a pending
Linux mailbox. The scan state was subsequently revisited with a secondary
PCI device model.

The later secondary PCI gate changed the zero-channel diagnosis: the opt-in
model returns the five physically captured ISP10160 configuration dwords at
slot 16, and stock discovers one channel. An opt-in ISP mailbox experiment
models register, word RAM, DMA load/dump, and checksum commands with a
64K-word RISC RAM backing. Its direct test passes. In a coupled stock/QEMU
replay it completes 61,448 commands without an i960 fault, including the
32-word DMA self-test and firmware upload, then stops at `0x0002` (execute
firmware). The uploaded `0x3379`-word image has SHA-256
`4470b91079573f60249998eb1b8f9e9fe33b5abac44938cb97eea85c56e90d13`
and a zero 16-bit sum. The host SET_MEM_MBOX request remains pending. See
the linked artifact for the captured image and exact runtime trace; ISP
instruction execution is the next offline gate.

The [bounded ISP configuration probes](../../../artifacts/current/accele160-isp-config-20261025/README.md)
then accept exact observed `0x0032`, `0x003a`, and `0x0035` requests, each
opt-in and ordered after the earlier queue/image checks. Stock next waits at
`0x004a` (firmware features). This is protocol tracing only; the QLogic RISC
code is not executed. The actual Mylex x86 ROM, rather than a synthetic Linux
request, submits DAC960 V2 `GET_CTLR_INFO` (`0x20`/`0x01`) with a 512-byte
destination at guest DMA `0x0009f3e0`. In the 900-million-instruction coupled
run with timer interrupts, 145 timer entries occur but MU setup/receive
remain unvisited and the ROM request has no completion.

The [feature/status replay](../../../artifacts/current/accele160-isp-feature-status-20261025/README.md)
advances the exact `0x004a` request to `0x001f` GET FIRMWARE STATUS.
Disassembly confirms that stock stores the returned MB2 in per-channel state;
therefore the response cannot be reduced to a completion code. An explicitly
fabricated zero-status experiment reaches `0x0030` SET INIT SCSI ID (`7`), and
an exact ACK reaches `0x0018` BUS RESET (`1`). No ISP RISC firmware, SCSI bus,
or 80303 MU completion is modeled, so this replay neither explains the spare's
pre-beep POST failure nor changes the flash gate.

The [offline no-option-ROM POST probe](../../../artifacts/current/accele160-romless-post-20261025/README.md)
tests a one-byte change to the failed spare image at flash offset `0x30000`.
In experimental SeaBIOS/QEMU, the valid x86 ROM enters a BAR-poll loop and
does not reach a test boot sector in eight seconds; the invalid-signature ROM
performs zero BAR accesses and boots that sector. The i960 interpreter still
reaches its RTEMS `PASS` report. This supports the option-ROM wait as a
plausible host-side cause, but physical BIOS behavior remains unmeasured.
