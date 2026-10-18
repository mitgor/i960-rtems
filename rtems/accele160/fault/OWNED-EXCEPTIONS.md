# P3b: Accele160 owned fault and NMI candidate

Follow-up: the [no-injection owned-runtime profile](OWNED-RUNTIME.md) now passed
two-game normal execution, rearm, live ownership sampling and global STOP on
Accele160. See that document and its evidence batch for current restoration
status; the mode-0 service described below is the earlier checkpoint.

2026-10-18: **mode 3 passed on Accele160** on fresh boot
`b748d05a-16d1-40bf-b96d-973127ab6856`. Kernel
`08690ea79e991169c713c8dc6cd910da550e13115f02afe98c4b62f11a33acf7`
recorded a real `faulte` at tick 18: raw words `2002,9002,50001,c0716230`.
The IP resolves exactly to `_accele_raise_fault+4`; fault entry `c0716150`,
cached NMI entry `c0716160`, ISP `c0779040`, all table words and guards passed.
Stale request, stable record, STOP retention, pending admission and unchanged
DMA pin guards all passed. Local archive replay independently verifies this.

Mode 4 also **passed on Accele160**, on boot
`5caaf490-19ac-4b1b-ab1c-c01cacc9c924`, kernel
`dbb43a389db7d6cd101284c8759e9ce2e6a37046ff83388171aed32fadad9ed4`.
At tick 18 its raw architecture record was `2002,9002,f8,0` (NMI vector 248),
with NISR `100`, IISR `f`, IDR `80000010`, IIMR `73`. The other IDR bit `10`
was already present; the handler writes only bit 31 when acknowledging the
injected NMI. The capture records pre-acknowledgment state, not an independent
post-clear readback. Owned entries, ISP, both guards, stable snapshots and
STOP resource retention passed. Exact archive replay passes.

Both guarded full firmware reads on this newer boot match, closing mode 3's
reset recovery. The previous normal runtime's recovery was closed by mode 3's
prechecks. Mode 4's post-test reset recovery is now verified on fresh boot
`aea81f51-24ce-493b-a7d2-114195611d5b`: both guarded full firmware reads
match. The accepted mode-0 normal prompt is restored, with a 64-frame game,
audited idle, and 577 successful external console exchanges. The service is
left live for the user. Mode 0 does not install the new exception ownership;
normal owned-ISP/runtime qualification remains a separate next step.

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

## Current service and next qualification

The completed recovery run uses `/home/mit/i960-fault-20261018/bundle`, session
`sessions/20261018T204122Z`, accepted normal kernel
`4a9c0278ff23815ea94d546a7fc43bfc3566c8ff916b70d0c2b0e7e42582ad3e`.
It remains live in verified idle. Linux `~/rtems-console` calls the updated
`/home/mit/rtems-console-client.py`; the Mac wrapper uses that shortcut.
Do not stop/reset the service merely to finish evidence collection. The live
snapshot does not claim global STOP or subsequent reset of this new session.

Next: prepare a separate no-injection ownership profile and qualify normal
task switching, Doom, console, STOP and reset with owned vectors/ISP. Keep
active-DMA and engine exclusion tests separate. The restored mode 0 is the
previously qualified software-terminal-only profile and is not that new test.

Do not repeat modes 3/4 simply to restore the prompt; their completed immutable
bundles are `mode3-tested.tar.xz` and `mode4-tested.tar.xz` in the evidence batch.
`verify_archive.py ARCHIVE` independently replays raw records, firmware pairs,
source/kernel hashes and exact symbols. The remote exceptions working bundle
still contains mode 4 and deliberately enters a terminal park; it must not be
used as the normal prompt image.

Native checks: `rtems/accele160/fault/test.sh`. They run actual C with mock MMIO,
all 2,048 stock-table corruptions, all 2,048 owned-table corruptions, a dropped
NMI-vector write, both guards, source arming/masking and host trigger rejection.
They do not execute i960 entry assembly or prove PCI/NMI delivery.
