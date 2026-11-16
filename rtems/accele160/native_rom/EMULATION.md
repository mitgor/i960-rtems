# AcceleRAID 160 emulation gate

## Revised BIOS-test strategy, 2026-11-14

The priority is now **measured stock-versus-candidate behavior at the card/host
boundary**, with QEMU used to replay and explain that behavior. The first
spare's external-programmer read is byte-identical to the intended native
image; the physical HP Z400 still hangs before the beep when that card is
installed and Slot 6 option-ROM download is disabled. Therefore a SeaBIOS
option-ROM hang is insufficient as the explanation. The prepared no-x86-ROM
image has not been physically tested. See the [first-spare record](../../../artifacts/current/accele160-spare-rom-20261025/README.md),
[Slot 6 result](../../../artifacts/current/accele160-second-spare-20261026/README.md),
and [SeaBIOS comparison](../../../artifacts/current/accele160-romless-post-20261025/README.md).

1. **Make the stock physical baseline observable.** If the planned
   [flash bridge](../../../docs/hardware/ACCELE160-FLASH-BRIDGE-PCB-BRIEF.md)
   is built, first prove ordinary stock-flash boot, then boot the *same card's*
   stock bytes from bridge SRAM. Capture card power-good, RP#, CE#/OE#/WE#,
   first flash accesses, all command writes, mode and image hash, and the
   observable POST outcome. Record any trace overflows. The current bridge
   proposal logs writes and the first read, not a full address-by-address read
   stream; add an optional bounded trigger/capture facility if finer reset
   localization is needed. These traces can identify flash-side divergence,
   but cannot by themselves reveal PCI configuration or host BIOS reads.
2. **Keep QEMU as a differential protocol test, not an HP BIOS oracle.** Run
   the same stock and candidate images against the two-function PCI model
   (`8086:2962` bridge and `1069:0050` RAID function), with identical event
   schedules. Report the first difference in i960 IP, internal register state,
   PCI configuration, BAR access, interrupt, DMA, and controller readiness.
   Require the stock model to complete the real Mylex option-ROM
   `GET_CTLR_INFO` request before using the model to judge a candidate that
   retains the option ROM. The current model reaches request submission but
   leaves it pending; its QLogic/80303 and concurrent-timing behavior remains
   incomplete. See [QEMU bridge](../emulator/qemu/README.md) and
   [current evidence](../emulator/EVIDENCE.md).
3. **Test the no-option-ROM path separately.** With option-ROM download off,
   the relevant question is whether ordinary PCI enumeration/configuration or
   card reset behavior stalls the physical host. Replay an x86 boot with the
   ROM disabled, but do not infer that SeaBIOS follows HP `786G3 v03.15`
   behavior. If physical instrumentation is available, correlate POST-stage
   information and PCI events with the flash trace; a flash trace alone cannot
   establish what the HP BIOS waited for.
4. **Use hardware-in-the-loop only after stock bridge acceptance.** The first
   candidate experiment should load the already-failed first-spare image into
   SRAM on that same recoverable spare, without another flash write. Capture
   stock/candidate traces under the same slot and BIOS settings, then return
   to physical STOCK mode and demonstrate cold-boot recovery. This can test
   the actual HP BIOS plus actual PCI/controller silicon. It does not replace
   the QEMU regression suite; it supplies the physical facts needed to make
   that suite predictive.

Do not prioritize running a dumped HP BIOS inside generic QEMU as the next
gate: without the Z400 chipset, firmware environment, and card timing, it
would be another approximation. The actionable emulator work is to remove
known unmodeled controller behavior and check it against physical captures.
The previous plan below is retained as the detailed software-model history;
its SeaBIOS and mailbox milestones are evidence, not physical acceptance.

The spare-specific native-ROM candidate passed structural checks, a native
unit test of the stage-two copy routine, STOREIMAGE, and a full staged
READIMAGE. Its first cold power-on then failed before the user's normal POST
beep. Those checks did not execute the stock i960 reset block, the 80303
hardware initialization, the x86 option ROM, or RTEMS on the complete image.

## What needs to be emulated

A useful model has two coupled sides. The controller side executes the actual
1 MiB flash bytes on an i960-compatible CPU with the 80303 reset mapping,
16 MiB of SDRAM, internal register blocks, flash/SRAM banks, PCI address
translation, interrupt state, and the minimum mailbox/host-visible state
needed by the reset block. The host side presents the card's PCI identity,
configuration space, 8 KiB BAR, and 32 KiB x86 option ROM to an x86 BIOS.
The host must see the consequences of the i960 side's initialization; an
isolated option-ROM run cannot explain why the identical BIOS bytes work with
stock firmware but fail with the candidate.

QEMU currently lists no i960 system target. A QEMU PCI device model alone
would therefore execute only the x86 half. MAME has an i960 instruction core,
but its declared CPU types are 80960KA/KB, not the 80303/Jx-compatible core.
The open-source `sim5` project implements more i960 instructions but has no
80303 board model, accepts ELF bootloaders rather than this flash image, and
currently hard-fails compilation outside x86-64. We should smoke-test CPU
semantics against small binaries before selecting or adapting either core.

## Incremental acceptance, before any further flash

The [first executable controller harness](../emulator/README.md) now loads both
real flash images and compares bounded CPU traces. Strict mode stops on the
first unmodeled peripheral read at `0xe0400000` in both images. Exploratory
mode with the measured post-boot board byte reaches the expected stage-two
divergence at cycle 1,354,523. Correcting the interpreter's `chkbit` and Jx
short/byte comparisons now lets stock build its Huffman tables, validate ZIP1's
CRC and reach the verified runtime entry at cycle 48,565,709. Candidate stage
two copies the RTEMS payload and enters RTEMS. Corrected Jx frame alignment
allows the saved context to return into RTEMS's thread handler, and corrected
`scanbit`/`spanbit` lets the simulated scheduler select Init. Its worker
completes 64 iterations, writes PASS and parks with code zero. The full card
gate remains inconclusive because the 80303 device and host PCI/BIOS models
are incomplete.
This is an **inconclusive gate**, not a successful emulation or a reason to
flash again.
The 80303 register model and post-entry stock runtime behavior remain to be
implemented and validated. A first [QEMU PCI probe](../emulator/qemu/README.md)
now provides the measured identity, an 8 KiB BAR and the actual x86 option
ROM, and can load a static i960 RAM snapshot. A later local socket bridge
provides host access to interpreter RAM and forwards one LP mailbox request
for tracing; it cannot complete the request. SeaBIOS does not access BAR0 in its
bounded ROM run, so it does not distinguish stock from candidate.
The shared x86 option ROM also passes a separate
[generic QEMU entry smoke test](../emulator/EVIDENCE.md); the later matching
PCI probe is the stronger host-side entry check, but still lacks controller
command behavior.

1. The user confirmed that the host boots normally after the programmed spare
   is removed. Keep the failed card and both saved stock-flash reads labelled.
   Do not use the remaining spare for another experimental flash yet.
2. Build a standalone controller harness that loads the actual stock 1 MiB
   image at its reset mapping. Trace every instruction, unmapped access,
   register write, and branch, with an instruction budget and deterministic
   register responses. Validate the CPU against i960 microprograms and the
   saved reset-block disassembly. Reject unsupported opcodes explicitly.
3. Extend the **stock** checkpoint now reached at runtime entry with modeled
   SDRAM, PCI configuration and mailbox behavior. Compare observations with
   saved stock captures; document unknown hardware responses rather than
   choosing values that make the candidate pass.
4. Both the original-card candidate and the exact image flashed to the spare
   now have a bounded controller-side result under
   the exploratory board byte: each copies the exact 15,840-byte RTEMS payload,
   reaches `0xc0010000`, writes the expected scheduling report, and parks with
   code zero. Both stock images reach their runtime entry. Keep the stock gate
   passing after every model change, and replace speculative peripheral
   responses with measured reset-time values when those become available.
5. The QEMU x86 PCI identity/ROM/BAR probe is built and tested for
   `1069:0050` / `1069:0054`. Its upper BAR page and PIATVR configuration
   register now connect to the i960 emulator's RAM after a bounded boot run.
   A qtest workload now submits the first Linux `myrs` LP hardware mailbox:
   QEMU fetches 64 bytes from guest RAM by PCI DMA and forwards the request
   to the interpreter trace. The command stays pending. Next implement the
   stock controller-side handler and status DMA, then compare its completion
   with the candidate using the same BIOS and
   controller responses. QEMU/SeaBIOS behavior will not by itself reproduce
   the HP Z400 firmware, so a pass is additional evidence rather than proof
   of physical POST compatibility.

The first valuable deliverable is the controller trace through reset and
handoff, not a complete RAID command simulator. SCSI disks, performance,
timing accuracy and the full stock runtime can follow only as needed to
reproduce the host-side boot interaction. Any new flash candidate must pass
stock/candidate differential runs and retain a practical hardware recovery
path, since no emulator can guarantee that a physical card remains
recoverable after a firmware failure.

Primary references: [Intel 80303 programming/initialization guide](https://www.bitsavers.org/components/intel/i960/80303/273395-005_80303_IO_Processor_Prog_Guide_and_Initialization_200104.pdf),
[Intel 80303 developer's manual](https://bitsavers.trailing-edge.com/components/intel/i960/273353-001_Intel_80303_IO_Processor_Developers_Manual_May2000.pdf),
[QEMU system targets](https://www.qemu.org/docs/master/system/targets.html),
[MAME i960 CPU](https://github.com/mamedev/mame/blob/master/src/devices/cpu/i960/i960.cpp),
and [sim5](https://github.com/DrItanium/sim5).
