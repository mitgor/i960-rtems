# Matching-version reference found — 2026-10-10

**Current result:** [In-system recovery succeeded](SNAPSHOT-RECOVERY.md). A paired
512 KiB capture contains the exact 4.07-0-29 firmware and FWTCBBLK boot block,
plus the independently verified PCI BIOS. This supersedes older no-dump status
and the 256 KiB layout assumption below.

The user located Fujitsu's [DAC960PRL package directory](https://support.ts.fujitsu.com/globalflash/ScsiController/DAC960PRL/V4.07-0-29_4.10-41/).
The package contains **Fgj40729.img**, whose decoded MIMGMYLX header identifies
4.07-0-29, released April 9, 1999. This matches the version reported by the card;
it does not prove that every byte equals the installed firmware.

The package was downloaded, decoded and unpacked offline on the SSH host in
`/home/mit/i960-analysis.7jVBmy/prl29/`. No controller commands or flashing ran
in this follow-up. Vendor files are now archived locally under `artifacts/vendor-fujitsu/4.07-0-29/` (included in the Git archive); see `artifacts/ROM-INVENTORY.md`.

## Verified comparison

- Firmware payload: 229,376 bytes after removing the 512-byte container header
  and ten-byte trailer.
- First 28,672 bytes (bootstrap and relocated helper code): **identical** to the
  4.07-0-39 reference.
- Embedded ZIP: method 6, ZIP1, 167,565 compressed bytes → 304,120 bytes;
  CRC32 `8a9d7f6c`, verified on extraction.
- Decompressed versions differ in only **555 bytes**.
- Opcode dispatch, configuration dispatch, DMA helpers, flash snapshot helper,
  image reads/uploads, and the programming-handler region compared in the
  manifest are **byte-for-byte identical**. Addresses in FIRMWARE-HANDLERS.md
  remain valid for these regions.
- Decoded DAC960FL.EXE is identical to the previously analyzed flasher.

This removes differences between these two reference versions' read/copy code
as an explanation for our unidentified captures. Next analysis should focus on
actual board initialization, staging state and memory-address aliases. It should
not keep postponing that work for lack of a 4.07-0-29 reference.

The main decompressed differences are near runtime 0xC001064C/0xC0010660,
0xC001A4AC, 0xC0033C19–0xC0033E4F, and 0xC004F4D6. No semantic explanation for
all those differences is claimed here.

## Hardware/package distinction

The package metadata explicitly identifies **DAC960PRL (TomCat)** and includes
`FWTCBBLK.IMG` version 4.06-59. The earlier PG package contains `FWPJBBLK.IMG`.
The two boot-block payload hashes differ. A matching main firmware version is
therefore not approval to install the PRL package or its boot block on this card.
The common main-image bootstrap and command handlers make it a useful analysis
reference independently of whole-package compatibility.

## Reproduction and evidence

`host/dump/unpack_firmware.py` now recognizes both exact input hashes and verifies
version-specific compressed length, CRC and output hash. Both real reference
images pass extraction and all 14 existing dump-tool tests pass.

- `artifacts/analysis/firmware-40729-manifest.json`: version-specific extraction
  metadata, hashes and command table.
- `artifacts/analysis/firmware-40729-comparison.json`: source URL, package hash,
  exact compared address ranges and their hashes.

The package SHA-256 is
`5ba2adb79dbd3b536ee042fb11242f1b87aa42df4f95dd1224adf66f14d935f9`.
The normalized main firmware SHA-256 is
`8afaebf954bbbf31bba42f1156c76237c3e632b071f6b400d3f17fbcd9d8baa5`.
The unpacked program SHA-256 is
`21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195`.

**Subsequent result:** the complete main firmware and FWTCBBLK boot block now
match the live capture exactly. See `SNAPSHOT-RECOVERY.md`; the package itself
is still a vendor reference, distinct from the saved hardware snapshot.
