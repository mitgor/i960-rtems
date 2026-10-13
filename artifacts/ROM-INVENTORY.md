# Local ROM archive

**Current index (2026-10-11): [findings, evidence and unresolved questions](../CURRENT-FINDINGS.md).** Earlier milestone notes below retain their historical context.

**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](../docs/firmware/FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


Latest: [one-shot programming harness](../docs/firmware/ONE-SHOT-PROGRAMMING.md) is implemented in `host/program/`
(repository-root relative). Native transport/failure tests and a 105-command live
RAM-only rehearsal passed. Wrong activation token rejected before driver
registration; no programming doorbell issued. Full stock RAM restored and probe
unloaded. Exact binaries/captures are in `artifacts/one-shot-harness-20261010/`.
At this rehearsal milestone programming was still pending. Programming, full
readback and patched boot subsequently passed; see FIRMWARE-PROGRAMMED.md.
Recovery testing remains excluded.


Latest (2026-10-10): [programming preflight and live CPU verification](../docs/firmware/PROGRAMMING-PREFLIGHT.md)
passed. The CPU read all 512 KiB of the candidate through programmer alias
C1F2C000 with explicit cache invalidation and matched CRC32 2012D01F. All 105
commands completed cleanly; original staging/table/code restored, probe unloaded.
The descriptor policy and bytewise post-program flash-readback route are now
documented. Next implement the one-shot programming state machine and its
failure tests. No flash programming or recovery test occurred. Exact evidence
is in `artifacts/programming-preflight-20261010/` from the repository root.


## Live staging rehearsal

[Live staging rehearsal](../docs/loader/STAGING-REHEARSAL.md) passed: six full 512 KiB captures verify the original
stock image, the patched candidate in RAM, and complete stock restoration.
All 74 commands completed cleanly; probe unloaded. Exact binaries, source,
logs and validation are in `artifacts/staging-rehearsal-20261010/` (relative
to the repository root). No flash programming or recovery test occurred.


All files below are present on this Mac under the project's `artifacts/` directory.
This archive was collected on 2026-10-10 from `mit@192.168.2.75`; it does not depend
on continued SSH access. Binary archives, this index, checksums, validation results and work log are all
intended for Git preservation at the user's request. The historical `private-dumps`
directory name is retained for link stability; its files are not Git-ignored.

## Primary files

| File | Meaning |
| --- | --- |
| [Dumped 512 KiB ROM](private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin) | Complete recovered software image; 524,288 bytes |
| [Second capture](private-dumps/snapshot-fresh-20261010T125336Z/image-window-1.bin) | Byte-identical paired read |
| [Dumped main firmware](private-dumps/snapshot-fresh-20261010T125336Z/firmware-40729.bin) | 224 KiB region extracted at offset 0x30000 |
| [Dumped boot block](private-dumps/snapshot-fresh-20261010T125336Z/bootblock.bin) | 16 KiB at offset 0x7C000 |
| [Dumped BIOS](private-dumps/snapshot-fresh-20261010T125336Z/pci-bios.bin) | 28 KiB at offset 0x28000 |
| [Unpacked dumped firmware](private-dumps/snapshot-fresh-20261010T125336Z/firmware-unpacked.bin) | Verified 304,120-byte i960 program |
| [Original Fujitsu 4.07-0-29 package](vendor-fujitsu/4.07-0-29/package.exe) | Unmodified self-extracting archive from the DAC960PRL directory |
| [Fujitsu 4.07-0-29 ROM](vendor-fujitsu/4.07-0-29/Fgj40729.img.raw) | Decoded main payload; exactly matches the dumped main firmware |
| [Fujitsu 4.07-0-29 container](vendor-fujitsu/4.07-0-29/Fgj40729.img.decoded) | Decoded image including 512-byte header and ten-byte trailer |
| [Fujitsu boot block](vendor-fujitsu/4.07-0-29/FWTCBBLK.IMG.raw) | Exactly matches the dumped boot block |
| [Original Fujitsu 4.07-0-39 package](vendor-fujitsu/4.07-0-39/package.exe) | Unmodified DAC960PG archive used in earlier analysis |
| [Fujitsu 4.07-0-39 ROM](vendor-fujitsu/4.07-0-39/407t39b0.img.raw) | Normalized 224 KiB reference; not the installed revision |

A vendor main-firmware payload is not a full 512 KiB card image. Keep the originals,
decoded containers, normalized payloads and hardware captures distinct.

## Supporting artifacts

- `romfetch-live-20261010/`: five live RAM-dispatch attempts, exact builds,
  three flash-map captures, command transcripts and validator report. The
  final run proved post-startup stock flash instruction fetch and restored
  the table/RAM. See [ROM-FETCH-LIVE.md](../docs/loader/ROM-FETCH-LIVE.md). Attempt 2's raw
  tar contains zero-sized dynamic debugfs files; use its dmesg transcript.
- [ROM-hook staging plan](romhook-20261010/stage-plan/stage-plan.json): exact
  offline three-write plan (56 upload bytes) that reconstructs the unflashed
  candidate from the pinned stock image. A live staging rehearsal remains.

- `romhook-20261010/`: exact ROM-resident hook build, full candidate and
  offline Fujitsu MIMG wrapper; `romhook-step4-20261010/`: read-only live
  dispatch-word capture and exact Linux probe. See
  [ROM-HANDLER-STEP4.md](../docs/loader/ROM-HANDLER-STEP4.md). Neither file is a stock backup
  or a flash-ready update.
- `vendor-fujitsu/<version>/original-package-contents/`: all original encoded
  members and package metadata extracted without executing either EXE.
- `vendor-fujitsu/4.07-0-29/`: decoded BIOS, boot block and DOS flasher, embedded
  ZIP, bootstrap/program disassemblies and unpacked reference binaries.
- `vendor-fujitsu/4.07-0-39/decoded/`: original decode outputs and
  `globalflash_decode.py`. Historical `.bin`/`.rom` outputs here retain the
  ten-byte container trailer; use the normalized `.raw` files for comparisons.
- `private-dumps/remote-analysis/`: earlier firmware/boot-block disassemblies,
  DOS-flasher disassembly, extraction outputs, analysis manifest and the exact
  `capture-window.py` used remotely. That script has historical absolute remote
  paths; archive evidence, not a portable turnkey command.
- `private-dumps/snapshot-20261010T124921Z/`: pre-fresh-boot 256 KiB capture;
  staging was contaminated at its beginning, but firmware was found at 0x30000.
- `private-dumps/snapshot-fresh-20261010T125216Z/`: clean-start 256 KiB capture
  identifying EZAssist, BIOS and the firmware prefix.
- `private-dumps/snapshot-fresh-20261010T125336Z/`: successful 512 KiB session,
  including all per-chunk transaction logs and A5/5A captures, extracted ZIPs,
  and boot-block disassembly.
- `dump-attempt-20261010/`, `dump-load20-20261010/`,
  `firmware-handler-20261010/`: previous transport tests, including failed and
  contaminated reads. These are historical evidence, not alternative good ROMs.
- `analysis/snapshot-20261010/`: successful acquisition's shareable logs and
  validation manifest. Other `analysis/` files record reference comparison,
  vendor symbols, DRAM initialization leads and target-build evidence.

## Integrity and provenance

[SHA256SUMS](SHA256SUMS) records the size-independent SHA-256 digest of every local
artifact file at collection time, except itself; it includes the JSON inventory.
[artifact-inventory.json](artifact-inventory.json) additionally records lengths.
Run from the project root: `shasum -a 256 -c artifacts/SHA256SUMS`.

Original source packages:

- [Fujitsu DAC960PRL 4.07-0-29](https://support.ts.fujitsu.com/globalflash/ScsiController/DAC960PRL/V4.07-0-29_4.10-41/zip_dac960prl_v4.07-0-29_4.10-41.exe)
- [Fujitsu DAC960PG 4.07-0-39](https://download.ts.fujitsu.com/globalflash/ScsiController/DAC960PG/V4.07-0-39_4.10-41/zip_dac960pg_v4.07-0-39_4.10-41.exe)

Both package hashes were checked against the earlier recorded manifests. After
copying, the two complete dumps were compared, and extracted firmware, boot block
and BIOS were compared against their local references. Every comparison passed.
See [the work log](ROM-DUMP-WORKLOG.md) and [recovery report](../docs/firmware/SNAPSHOT-RECOVERY.md).

## Remote completeness audit

[Remote audit](remote-audit-20261010/README.md) checked 295 project files by hash
and preserved 20 additional historical scripts, control/build artifacts and the
exact acquisition module. No unique GCC/binutils source patches were found.

## Experimental patch (not a stock backup)

`postinit-prototype-20261010/` contains the separately labelled loader candidate,
its full-ROM output, manifest, binaries, disassemblies and Linux host tool. See
[POSTINIT-LOADER.md](../docs/loader/POSTINIT-LOADER.md). It has not been flashed or executed.

## Live-test preparation, revision 2

Read-only PCI preflight passed on the remote host. Archived the v2 candidate,
preflight JSON and build evidence in `postinit-preflight-20261010/`; the first
prototype remains preserved. See [LIVE-TEST-PREFLIGHT.md](../docs/loader/LIVE-TEST-PREFLIGHT.md)
for the earlier hook, ROM suppression, DMA guard and unresolved installation gates.
No custom code has executed on the card.

## Programming audit and offline MIMG — 2026-10-10

Archived `postinit-update-20261010/`: experimental firmware component, manifest, programming map and evidence excerpts. The candidate reconstructs exactly; 14 Python tests and the native dispatcher test passed. The matching programming route rewrites lower 496 KiB, with boot block conditional. No remote or flash operation occurred. See [PROGRAMMING-RECOVERY.md](../docs/firmware/PROGRAMMING-RECOVERY.md).

## Boot-block recovery analysis — 2026-10-10

`boot-recovery-20261010/` contains the extracted 0x2A00-byte recovery monitor, relocated disassembly, evidence excerpts and offline audit. Descriptor/bootstrap-checksum failures reach this monitor; it sets PCI ID 1069:0011 and supports 20/21/2B commands. No hardware entry or programming was attempted. Native test plus 18 Python tests passed. See [BOOT-RECOVERY.md](../docs/firmware/BOOT-RECOVERY.md).

## SSH recovery-entry investigation — 2026-10-10

Archived `ssh-recovery-investigation-20261010/` with read-only live preflight and static evidence. Device remains normal-mode 1069:0010. Traced an unchecked staging-relative address-add lead; staging address and safe handoff remain unknown. No hardware writes or flash. Serial setup instructions and investigation status are in [SSH-RECOVERY-ENTRY.md](../docs/firmware/SSH-RECOVERY-ENTRY.md).

## Staging allocator and live control — 2026-10-10

`staging-allocation-20261010/` archives fresh Enquiry2 and paired offset-zero reads, allocator evidence and the checked geometry report. Predicted staging base C0F2C000 remains unobserved directly. Three bounded control runs completed cleanly; the first two exports failed locally, as documented in [STAGING-ALLOCATION.md](../docs/loader/STAGING-ALLOCATION.md). Native test and 21 Python tests passed. No out-of-window read, upload or flash.

## Live staging pointer confirmed — 2026-10-10

`staging-pointer-20261010/` archives the six-command transcript, all captures, exact source/header, compiled module and verification report. Two four-byte reads returned C0F2C000 at the derived C0112A70 address; all statuses and guards clean, pending=0. Module removed, card driverless. No upload/execution/flash. See [STAGING-POINTER-VERIFIED.md](../docs/loader/STAGING-POINTER-VERIFIED.md).

## Runtime code and board callbacks verified — 2026-10-10

`runtime-read-20261010/` preserves initial and hardened captures, exact executed sources and modules. The paired reads verified C004A2E0 entry bytes, board C0110780, alias C1000000 and the active callbacks. Both 13-command runs completed cleanly; module removed, card driverless. Native guard and 17 Python tests passed. No upload, execution, recovery or flash. See [RUNTIME-READ-VERIFIED.md](../docs/loader/RUNTIME-READ-VERIFIED.md).

## Offline returning-callback build — 2026-10-10

`live-handoff-20261010/` contains `return-status.bin` (20 bytes), its ELF/map/
disassembly, source and byte-contract verifier. The binary is linked for the
extra staging allocation at C0FAC100 and tail-branches to verified stock
completion `C004BAD0` after recording status `0x017e`. It is an offline build;
the stock mailbox protocol has no discovered handoff primitive, so no bytes were
uploaded or executed. See [LIVE-EXECUTION-HANDOFF.md](../docs/loader/LIVE-EXECUTION-HANDOFF.md).

## Offline stock-preserving command hook — 2026-10-10

`stockhook-20261010/` contains the 84-byte i960 hook, ELF/map/disassembly,
exact source, pinned image builder, 512 KiB candidate and manifest. The hook
maps previously unsupported opcode 0x6F to a returning PING and continues the
original stock entry. The candidate differs from stock in 76 bytes and has
not been flashed or executed. See [STOCK-PRESERVING-HOOK.md](../docs/loader/STOCK-PRESERVING-HOOK.md).

## Handler memory audit and ROM successor — 2026-10-10

`dram-hook-audit-20261010/` holds the exact fixed read-only probe build and
paired 64-byte live captures from C0120000. Both were zero; that does not
establish lifetime ownership. `romhook-20261010/` holds the step-3 successor:
a 48-byte target-built metadata hook with its PING handler at FEFE001C in
verified firmware flash padding, plus the full raw offline image and manifest.
Reachable stock paths can free the staging allocation, so it was not used as
handler storage. The new image has not been flashed or run. See
[DRAM-HOOK-AUDIT.md](../docs/loader/DRAM-HOOK-AUDIT.md) and
[ROM-HANDLER-STEP3.md](../docs/loader/ROM-HANDLER-STEP3.md).

## Reversible RAM upload verified — 2026-10-10

`ram-scratch-20261010/` archives exact executed source/headers/module, 20 capture blobs, 22-command transcript and verification. Sixteen bytes at C0FAC010 were uploaded, read back and restored; paired surrounding 64-byte reads verified no neighboring changes. Status/guards clean; pending=0, scratch-dirty=0. Module removed; card driverless. Two native guard tests and 20 Python tests passed. No execution/recovery/flash. See [RAM-WRITE-VERIFIED.md](../docs/loader/RAM-WRITE-VERIFIED.md).

Runtime loader milestone: [software-loader-20261010/README.md](software-loader-20261010/README.md)
contains exact target binaries, generated Linux module, three live run capture
sets, source snapshot and test reports. These are RAM execution captures, not a
new firmware revision or independent physical-flash backup.

T1 buffer I/O: [buffer-io-20261010/README.md](buffer-io-20261010/README.md)
archives the target/module sources and binaries, four buffer runs, scalar
regression, exact outputs and offline validation. Captures are transient RAM;
no new firmware image was programmed.

T2 Tetris: [tetris-t2-20261010/README.md](tetris-t2-20261010/README.md) contains the
returning game payload, source snapshots, native/interpreted tests and nine live
state/frame captures with independent byte-exact validation.

T3 replay: [tetris-t3-20261010/README.md](tetris-t3-20261010/README.md) contains
complete lossless archives for the 1,000-call main run, 64-call repeat and
three-call smoke test, timing data, exact timed module and independent validation.

## T5 persistent runtime session (2026-10-10)

`artifacts/tetris-t5-20261010/` contains the exact final Linux module, generated
sources, unchanged T2 payload/native oracle, prepared BIO image, development
module sources, full replay/lifecycle/cadence captures in `evidence.tar.xz`,
independent validations and final host status. Main replay: 1,000 native-matching
frames, median 41.12 ms. Separate paced test: 400 frames at 20.007 Hz. Both lifecycle
sweeps and all full final RAM restorations passed. No new ROM image or flash
operation; installed-ROM identity remains unchanged. See PERSISTENT-SESSION.md
for the per-frame versus periodic full audit coverage.

## T4 SSH Tetris (2026-10-10)

`artifacts/tetris-t4-20261010/` preserves the terminal frontend/launcher and
sources, exact unchanged T5 module/T2 payload, native comparison library,
remote captures in `evidence.tar.xz`, Mac ANSI/key transcripts, five independent
trace/restoration validations, test results and final host status. Main run:
35,846 frames over 30 minutes, 68 restarts, 19.91 Hz, all native-matching.
Short runs cover normal quit, real SSH loss/reconnect, Ctrl-C and resize.
Full RAM restored, module unloaded; no new flash image or reboot.

## Preservation audit — 2026-10-11

[Final audit](preservation-audit-20261011/README.md) reconciles 7,859 remote
project files and preserves 41 missing historical files. The exact compiler
installation and original upstream sources are in [toolchain-20261011](toolchain-20261011/README.md).
A separately observed terminal session completed during collection: all 2,224
frames independently matched, full RAM restoration and unload passed. No card
commands, reboot or programming were performed by the audit. See
[the current findings index](../CURRENT-FINDINGS.md) for remaining unknowns.
