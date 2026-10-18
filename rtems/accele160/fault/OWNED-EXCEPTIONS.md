# P3b: Accele160 owned fault and NMI candidate

2026-10-18: implemented and native-tested; **hardware qualification pending**.
The first mode-3 revision cross-built and was archived before a reset. The PC
then refused SSH, before either new injection ran. Current source contains
additional ownership checks and the mode-4 doorbell path and must be rebuilt.
Neither candidate is promoted to the normal prompt profile.

## Ownership and entry

Only manifest-pinned `ACCELE_TERMINAL_TEST=3` or `4` installs hardware ownership.
Modes 0/1/2 retain their previous software-only semantics. No flash is written.
The first baseline is checked before changing any pointer: live PRCB `feffdd20`,
ROM fault-table pointer `c0000800`, cached NMI `c00521b0`, ISP `c0001000`, and all
64 table words (sixteen `c0053400,0` pairs, then sixteen zero pairs). A mismatch
enters the diagnostic park without returning to firmware.

Inside the existing 512 KiB grant, `c0779000..c077a000` now reserves a separate
4 KiB architectural interrupt-entry stack, guarded at both ends by 64 bytes.
ISP becomes `c0779040`. The existing per-task RTEMS ISR continuation stacks and
separate terminal C stack `c0778000..c0779000` remain in place. The cached NMI
entry is installed first, then ISP, then all 32 local-call fault entries with
zero second words. Readback failures are terminal, even before the application
RAM claim flag is set. Installation phase 1 means reset-required partial
ownership; phase 2 means the readback completed. Before either injection, the
card rechecks every table word, ISP, cached NMI and both IRQ-stack guards.

The two assembly entries retain four raw architecture words at FP-16..FP-4,
FP/SP, entry kind, and processor controls before switching to the terminal C
stack. Ordinary interrupts are masked and borrowed timer 1 is disabled. The
first-entry latch is checked before record writes; subsequent entries park
without calling C or replacing the first record. DONE is published last.
No handler returns, calls stock code, reports driver completion or frees pins.

This is terminal containment, not context recovery. A local-call fault still
needs a usable current stack for the processor's initial frame. A nested NMI
can interrupt an incomplete first capture; the non-atomic latch does not
promise a completed record under arbitrarily nested exceptions. Replacing ISP
also changes normal interrupt entry and needs normal-runtime qualification
before promotion. SCSI/cache engines and active-DMA containment are unqualified.

## Independent hardware tests

Mode 3 uses `cmpo 0,0; faulte`, not a direct call to the handler. Acceptance
requires actual fault kind 1, type/subtype `0x050001`, a kernel fault IP, owned
vectors/table, intact guards, stable terminal snapshots and retained resources
after a STOP request. A completed terminal record does not prove reset recovery.

Mode 4 arms only after a nonce/sequence/token match and owned-state revalidation.
It rejects a pending NMI source, saves IIMR and clears only its bit 3. The host
checks the documented host/local IDR/IISR/IIMR aliases before and after arming,
then writes `0x80000000` exactly once to existing BAR0 mapping offset `0x20`.
No second owner, mapping or generic MMIO command is introduced. Acceptance
requires interrupt procedure number 248, NISR MU bit 8, IISR bit 3, latched IDR
bit 31, and the unmasked source. The terminal handler snapshots first, remasks
only bit 3 and acknowledges only the injected doorbell bit. Other source
status is preserved. Software interrupts cannot request NMI vector 248.

The test is deliberately before Doom admission/DMA initialization. Zero safe
DMA register triples describe that test state, not an engine-stop proof.

## Record extension (schema 1, mode-gated)

| Words | Meaning |
|---|---|
| 144–145 | Stock cached NMI and ISP captured before writes |
| 146–147 | Install phase and architectural-stack guard validity |
| 148–149 | Owned fault and NMI entry addresses |
| 151–154 | NISR, IISR, IDR, IIMR; terminal NMI values precede acknowledgment |
| 155 | Authenticated NMI test armed |
| 160 | Entry kind: software 0, fault 1, NMI 2 |
| 161–164 | Raw FP-16, FP-12, FP-8, FP-4 hardware record |

Existing words and legacy mode-1/2 archives remain compatible. Host decoding
now reads 176 words; unused legacy record bytes are not treated as ownership.

## Source basis

Intel *80303 I/O Processor Developer's Manual*, 273353-001 (May 2000):
sections 8.1.5/8.2.3/8.2.5/8.2.9 describe records, cached NMI and interrupt
entry; 9.3 describes fault entries; 16.2 figure 16-1 maps MU registers into
the first 4 KiB of the primary inbound PCI window; 16.8.3–16.8.5 describe
IDR `1320`, IISR `1324`, IIMR `1328`. The host equivalents are offsets
`20`, `24`, `28`. See the [Intel manual scan](https://bitsavers.computerhistory.org/components/intel/i960/273353-001_Intel_80303_IO_Processor_Developers_Manual_May2000.pdf).
Do not copy the older PG's fixed `0x1f3/0x1fb` mask values: the 80303 definition
reserves bits above bit 6. Preserve read mask bits and change only bit 3.

## Resume and qualification

1. After physical recovery, record a changed Linux boot ID and inspect retained
   modules/owners. Do not force-unload or adopt a dead owner's buffers.
2. Overlay current source into `/home/mit/i960-exceptions-20261018/bundle`.
   Preserve the pinned engine identity/template and inputs. Build mode 3 using
   the commands in README, run `write_manifest.py`, regenerate `bundle.json`
   file hashes, inspect assembly/symbols and archive the exact candidate locally.
3. Launch that isolated bundle with `launch.py start --bundle PATH --port 8087
   --max-frames 64 --restart-cycles 0 --paired-frames 32 --capture-all`.
   The launcher performs both guarded full firmware reads before admission.
4. Replay terminal captures; additionally resolve the recorded handler pointers
   and fault IP against the exact kernel symbols/disassembly. Save the complete
   session and bundle locally before resetting.
5. Fresh reset and paired reads close mode 3 recovery. Rebuild as mode 4; repeat
   the isolated launch and capture/replay. Resolve vector 248 and source bits
   from raw data, never infer NMI delivery from a direct handler call.
6. Reset and paired reads close mode 4 recovery. Only then prepare a separate
   no-injection ownership profile and qualify ordinary task switching, Doom,
   console, STOP and reset. Current mode 0 intentionally does not install owned
   vectors; restoring it alone would not qualify the new ownership profile.

Native checks: `rtems/accele160/fault/test.sh`. They run actual C with mock MMIO,
all 2,048 stock-table corruptions, all 2,048 owned-table corruptions, a dropped
NMI-vector write, both guards, source arming/masking and host trigger rejection.
They do not execute i960 entry assembly or prove PCI/NMI delivery.
