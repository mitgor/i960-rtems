# Local ROM archive

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
artifact file at collection time, except itself and the JSON inventory.
[artifact-inventory.json](artifact-inventory.json) additionally records lengths.
Run from the project root: `shasum -a 256 -c artifacts/SHA256SUMS`.

Original source packages:

- [Fujitsu DAC960PRL 4.07-0-29](https://support.ts.fujitsu.com/globalflash/ScsiController/DAC960PRL/V4.07-0-29_4.10-41/zip_dac960prl_v4.07-0-29_4.10-41.exe)
- [Fujitsu DAC960PG 4.07-0-39](https://download.ts.fujitsu.com/globalflash/ScsiController/DAC960PG/V4.07-0-39_4.10-41/zip_dac960pg_v4.07-0-39_4.10-41.exe)

Both package hashes were checked against the earlier recorded manifests. After
copying, the two complete dumps were compared, and extracted firmware, boot block
and BIOS were compared against their local references. Every comparison passed.
See [the work log](ROM-DUMP-WORKLOG.md) and [recovery report](../SNAPSHOT-RECOVERY.md).

## Remote completeness audit

[Remote audit](remote-audit-20261010/README.md) checked 295 project files by hash
and preserved 20 additional historical scripts, control/build artifacts and the
exact acquisition module. No unique GCC/binutils source patches were found.
