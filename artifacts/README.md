# Artifacts

Latest RAM/OS milestone: [12 MiB exclusive RAM and RTEMS workspace](rtems-large-ram-20261012/README.md):
256 KiB workspace, larger stacks, 35-minute / 48-round networking acceptance,
responsive final scans, preserved failures, exact binaries and the Doom OS plan.


**Current index (2026-10-12): [findings, evidence and unresolved questions](../CURRENT-FINDINGS.md).** Earlier milestone notes below retain their historical context.

Latest: [T4 SSH Tetris](tetris-t4-20261010/README.md): a 30-minute terminal run, 35,846 native-matching frames, plus disconnect/reconnect and resize evidence. Exact playable frontend, module and target binaries are preserved.

Latest: [T5 persistent sessions](tetris-t5-20261010/README.md) sustain 20 Hz on the card, with a 1,000-frame verified replay and process-death cleanup evidence. Exact module, target binaries, sources and captures are preserved.

**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](../FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


Latest: [one-shot programming harness](../ONE-SHOT-PROGRAMMING.md) is implemented in `host/program/`
(repository-root relative). Native transport/failure tests and a 105-command live
RAM-only rehearsal passed. Wrong activation token rejected before driver
registration; no programming doorbell issued. Full stock RAM restored and probe
unloaded. Exact binaries/captures are in `artifacts/one-shot-harness-20261010/`.
At this rehearsal milestone programming was still pending. Programming, full
readback and patched boot subsequently passed; see FIRMWARE-PROGRAMMED.md.
Recovery testing remains excluded.


Latest (2026-10-10): [programming preflight and live CPU verification](../PROGRAMMING-PREFLIGHT.md)
passed. The CPU read all 512 KiB of the candidate through programmer alias
C1F2C000 with explicit cache invalidation and matched CRC32 2012D01F. All 105
commands completed cleanly; original staging/table/code restored, probe unloaded.
The descriptor policy and bytewise post-program flash-readback route are now
documented. Next implement the one-shot programming state machine and its
failure tests. No flash programming or recovery test occurred. Exact evidence
is in `artifacts/programming-preflight-20261010/` from the repository root.


## Live staging rehearsal

[Live staging rehearsal](../STAGING-REHEARSAL.md) passed: six full 512 KiB captures verify the original
stock image, the patched candidate in RAM, and complete stock restoration.
All 74 commands completed cleanly; probe unloaded. Exact binaries, source,
logs and validation are in `artifacts/staging-rehearsal-20261010/` (relative
to the repository root). No flash programming or recovery test occurred.


**Live RAM dispatch and flash fetch:** `romfetch-live-20261010/` preserves five
hardware attempts and three read-only flash-map captures. A changed table
word executed RAM callbacks; the final callback called a stock flash `RET`
after startup and restored all RAM. See
[ROM-FETCH-LIVE.md](../ROM-FETCH-LIVE.md). No flash was written.

`romhook-20261010/stage-plan/` holds the exact offline three-write staging
plan: 56 upload bytes that reconstruct the 512 KiB candidate from the pinned
stock image. It has not been applied on hardware.

**Step-4 preflight:** `romhook-20261010/experimental-firmware.img` is the
offline Fujitsu MIMG wrapper; `romhook-step4-20261010/` holds the fixed
read-only live opcode-`0x6F` table capture. See
[ROM-HANDLER-STEP4.md](../ROM-HANDLER-STEP4.md). Those step-4 artifacts alone
did not prove post-startup flash instruction fetch and do not make the image
flash-ready; the later live result is documented above.

**Step-3 ROM handler:** `romhook-20261010/` holds a target-built PING handler
at FEFE001C and its offline 512 KiB candidate. See
[ROM-HANDLER-STEP3.md](../ROM-HANDLER-STEP3.md). It avoids the unowned DRAM
window but has not been flashed or run.

**Handler DRAM audit:** `dram-hook-audit-20261010/` archives the fixed,
read-only live C0120000 capture. See [DRAM-HOOK-AUDIT.md](../DRAM-HOOK-AUDIT.md):
the bytes were zero, but the stock-preserving hook still lacks a lifetime
storage reservation.

**Local archive:** [ROM-INVENTORY.md](ROM-INVENTORY.md) links the original Fujitsu packages, normalized ROMs, complete hardware dumps and supporting captures. [ROM-DUMP-WORKLOG.md](ROM-DUMP-WORKLOG.md) records the investigation, corrections and findings. All binaries are now on this Mac under `artifacts/`.

**Current result:** [In-system recovery succeeded](../SNAPSHOT-RECOVERY.md). A paired
512 KiB capture contains the exact 4.07-0-29 firmware and FWTCBBLK boot block,
plus the independently verified PCI BIOS. This supersedes older no-dump status
and the 256 KiB layout assumption below.

**Execution boundary:** [LIVE-EXECUTION-HANDOFF.md](../LIVE-EXECUTION-HANDOFF.md)
records why the stock mailbox interface can upload staging data but cannot call
it. `live-handoff-20261010/` preserves a target-built return-status callback for
the future patched-boot route; it was not uploaded or executed.

**Offline stock-preserving candidate:** `stockhook-20261010/` holds the new
opcode-0x6F PING boot hook, exact source/target build, 512 KiB candidate and
manifest. See [STOCK-PRESERVING-HOOK.md](../STOCK-PRESERVING-HOOK.md).

## dac960pg-x86-bios.rom
The **PCI expansion ROM (x86 option ROM)** of this Mylex DAC960PG — the card's PC-side
BIOS that the host runs at boot (the `Alt-R` configuration utility, drive detection, etc.).

- 28672 bytes, valid x86 option ROM (`55AA` signature, PCIR header, Mylex `1069:0010`,
  code type 0 = x86).
- A `4.10-x` version token appears in the image (consistent with the DAC960PG BIOS 4.10 line).
- sha256: `f292ced6f809fedf5446f048495fcb983021d620923daba2b8690242c612e624`

**Dumped in-system** (no external programmer), read-only, via the PCI expansion-ROM aperture:
```bash
D=/sys/bus/pci/devices/0000:37:09.1
echo 1 | sudo tee $D/rom >/dev/null
sudo dd if=$D/rom of=card.rom
echo 0 | sudo tee $D/rom >/dev/null
```

### This is NOT the i960 firmware
This is only the x86 BIOS extension. The i960's own firmware lives in a separate flash
region that the expansion-ROM aperture does not expose, and it cannot be reliably dumped
in-system on this card (see `../REFLASH.md` §3 — the full-firmware backup needs an external
programmer). One of this BIOS's own strings, *"DAC960 firmware checksum error - reload
firmware"*, reflects that the i960 firmware is a distinct image.

## dac960pg-x86-bios.asm
Full disassembly of `dac960pg-x86-bios.rom` (16-bit real-mode x86):
`objdump -D -b binary -mi386 -Maddr16,data16 dac960pg-x86-bios.rom`. Reproducible from the
ROM; committed for convenience. See `../BIOS-ANALYSIS.md` for the annotated findings.

(Not committed: `/tmp/fwdump.bin` on the box was a failed StoreImage attempt — 524,288 bytes
of a single sentinel byte `0xA5`, i.e. no data transferred — so it is not a real firmware
dump and is omitted. A valid in-system dump is still pending the exact StoreImage sequence.)

## analysis/ (2026-10-10)

- `loader-target.dis`: actual target disassembly of this repository's loader,
  built with GCC 3.3.6/binutils 2.27, including the g14 initialization fix.
- `dram-profile-manifest.json`: hashes and checked offsets of two candidate
  board-memory initialization profiles in the vendor firmware and boot block.

See ../DRAM-ANALYSIS.md for findings and limits. Vendor raw images and their full
disassemblies remain in the isolated remote work directory, not in this repo.

## dump-attempt-20261010/

Controlled live Enquiry2/opcode-0x21 experiment: transcript, before/after Enquiry2
responses, two untouched sentinel buffers, and a classification manifest. These
are experiment captures, **not firmware dumps**. See ../DUMP-ATTEMPT.md for
results and the newly disputed opcode direction.

## LoadImage follow-up

`dump-load20-20261010/` contains three paired 0x20 captures with transcripts and
hash manifests. Offset zero contains the previous staging sentinel; offset 0x200
contains unidentified repeatable bytes. These are not firmware backups.
`analysis/vendor-symbols.json` is the corrected 354-symbol map, generated by
`host/dump/vendor_symbols.py` from the hash-checked decoded vendor EXE.
See `VENDOR-READ-PATH.md` for interpretation.

`firmware-handler-20261010/` preserves the two later live reads. The 0x48000 read
preceded the discovery of a 256 KiB image window and is outside that window;
it is not evidence of flash contents. `analysis/firmware-unpacked-manifest.json`
records the verified offline reference extraction, not a live firmware dump.

`analysis/firmware-40729-manifest.json` and `firmware-40729-comparison.json`
record the matching-version vendor reference and the identical read/copy handler
regions. They are offline evidence, not a live dump; see `FIRMWARE-40729.md`.

## Preservation audit — 2026-10-11

[Final audit](preservation-audit-20261011/README.md) reconciles 7,859 remote
project files and preserves 41 missing historical files. The exact compiler
installation and original upstream sources are in [toolchain-20261011](toolchain-20261011/README.md).
A separately observed terminal session completed during collection: all 2,224
frames independently matched, full RAM restoration and unload passed. No card
commands, reboot or programming were performed by the audit. See
[the current findings index](../CURRENT-FINDINGS.md) for remaining unknowns.
