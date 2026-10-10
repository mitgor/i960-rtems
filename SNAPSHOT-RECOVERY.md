# In-system firmware recovery — 2026-10-10

**Archive update:** All vendor originals and dump sessions are now local. See [artifact inventory](artifacts/ROM-INVENTORY.md), [work log](artifacts/ROM-DUMP-WORKLOG.md), and [checksums](artifacts/SHA256SUMS).

**Success: recovered a repeatable 512 KiB controller image through opcode 0x20,
with the card installed in the PC.** The entire 224 KiB main firmware region
matches Fujitsu's 4.07-0-29 reference byte for byte. The 16 KiB boot block also
matches that package's FWTCBBLK image, and the BIOS matches our earlier independent
PCI expansion-ROM read. No flash programmer was used.

## Saved files

Local archive directory (included in Git):
`artifacts/private-dumps/snapshot-fresh-20261010T125336Z/`

- `image-window-0.bin` and `image-window-1.bin`: two identical 524,288-byte captures.
- `firmware-40729.bin`: extracted 229,376-byte main firmware.
- `bootblock.bin`, `pci-bios.bin`, `ezassist-archive.bin`: extracted regions.
- Nine offset directories retain every transaction log and both host-buffer fills.

Remote copy: `/home/mit/i960-analysis.7jVBmy/snapshot-fresh-20261010T125336Z/`.
Full-image SHA-256:
`43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93`.
Public evidence, hashes and per-chunk validation:
[manifest](artifacts/analysis/snapshot-20261010/manifest.json).
Firmware binaries and original vendor packages are intended for Git preservation.
The historical directory name `private-dumps` is retained to preserve existing links;
it no longer indicates a Git exclusion.

## Recovered layout

Offsets are relative to the captured image. The 512 KiB firmware board profile
maps these to local addresses starting at 0xFEF80000.

| Offset | Length | Content and validation |
| --- | --- | --- |
| 0x00000 | 0x1B943 | ZIP containing EZASSIST.ROM; decompresses to 545,516 bytes, CRC32 9c5a2a90 |
| 0x28000 | 0x7000 | BIOS; identical to artifacts/dac960pg-x86-bios.rom |
| 0x30000 | 0x38000 | Main firmware; identical to normalized Fgj40729.img |
| 0x37000 | within firmware | ZIP1; decompresses to 304,120 bytes, CRC32 8a9d7f6c |
| 0x79C00 | descriptor region | XLYM signature and component records, including firmware version bytes 04 07 1d 30 |
| 0x7C000 | 0x4000 | Boot block; identical to normalized FWTCBBLK.IMG from the 4.07-0-29 package |

The boot block differs from the previously examined PG package's FWPJBBLK. Do
not substitute that reference when analyzing this installed card. Main firmware
and boot-block identity do not establish that every component of the Fujitsu
update package is interchangeable: the installed BIOS differs from BGJ41041.
Unlisted image regions remain preserved, without assigning unsupported meanings.

## What changed in the investigation

The earlier first-512-byte upload via 0x21 had overwritten staging, not flash.
A full 256 KiB read before the fresh boot nevertheless contained the first
64 KiB of the matching firmware at 0x30000. Tiny probes at 0x8000 had missed it.

SSH briefly became unavailable; on reconnect the host reported uptime under one
minute and boot ID `13f4bfa6-76a4-4c20-88d5-6fdd337e5aeb`. This agent did not issue
the reboot command. The user had authorized reboot if needed. The fresh read at
image offset zero then returned a valid EZAssist ZIP instead of the staging fill.

The previous 256 KiB bound was based on the raw firmware's standalone startup
path through C000C4E0/C000C9A0. The same bootstrap also contains an alternate
wrapper C000C460 that finishes through C000C600, which configures a 512 KiB
window at FEF80000 and descriptor FEFF9C00. The live BIOS at offset 0x28000 agrees
with the previously observed expansion-ROM translation FEFA8000. The observed
firmware position, and subsequently the descriptor and exact boot-block match,
support this 512 KiB profile. The standalone entry is not proof of the installed
boot block's startup route. Earlier documentation generalized it incorrectly.

The kernel harness bound is now 0x80000 for this tested PG setup. Do not extrapolate
this layout to another model or firmware merely because opcode 0x20 succeeds.

## Acquisition and checks

The controller was already driverless. The collector used the existing kernel
harness with `attempt=1`, offsets 0, F000, 1E000, 2D000, 3C000, 4B000, 5A000,
69000, 78000, lengths F000 except the final 8000. Every chunk issues Enquiry2,
two 0x20 reads with different initial host fills, then Enquiry2. It saves debugfs
captures and removes the module only after successful completed transactions.
The exact executed collector is saved remotely as
`/home/mit/i960-analysis.7jVBmy/capture-window.py`.

All 36 completions had the expected IDs, status zero, unchanged DMA guards,
and pending=0. Every paired payload matched; all before/after Enquiry2 responses
reported 4.07-0-29. Offline capture validation passed for all nine chunks.
Both embedded archives extracted successfully with Info-ZIP and their stored
CRCs matched the output. The firmware and boot block were compared against
independently decoded vendor reference files, not used to fill missing bytes.

The module built against the running kernel with W=1 (only compiler-name/BTF
environment notices). All 14 existing dump-tool tests passed. The module was
removed after capture, leaving the controller driverless. No opcode 0x21, 0x22,
descriptor command, flash programming, or controller-reset command was sent in
this recovery attempt.

## Meaning and remaining limits

This achieves in-system recovery of the installed main firmware and a validated
512 KiB software image containing its surrounding components. The paired reads
come from the same firmware staging snapshot; they are not two independent
flash acquisitions. No external-programmer comparison, physical-chip-capacity
measurement, or restoration test was performed. Keep the existing independent
backup gate before any flashing experiments.

The next useful work is offline analysis of the recovered boot block and its
DRAM initialization, using these exact installed bytes. Another live dumping
experiment is not required to obtain the 4.07-0-29 main program.
