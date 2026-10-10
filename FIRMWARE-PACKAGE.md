# Official DAC960PG firmware package (found + archived on the box)

**Current result:** [In-system recovery succeeded](SNAPSHOT-RECOVERY.md). A paired
512 KiB capture contains the exact 4.07-0-29 firmware and FWTCBBLK boot block,
plus the independently verified PCI BIOS. This supersedes older no-dump status
and the 256 KiB layout assumption below.

> **Latest follow-up:** [VENDOR-READ-PATH.md](VENDOR-READ-PATH.md) corrects the
> vendor symbol addresses and verifies opcode 0x20 card-to-host transfers.
> Returned bytes appear to be staging memory; no physical-flash backup exists.
> Opcode 0x21 uploads host bytes and must not be used as a dump command.


> **2026-10-10 live-attempt update:** See [DUMP-ATTEMPT.md](DUMP-ATTEMPT.md).
> Fresh, matched-ID 0x21 transactions left host buffers untouched; Enquiry2 worked.
> Vendor-code dataflow also puts the claimed card-to-host direction of 0x21 in
> doubt. Historical “safe StoreImage dump” statements below are superseded;
> no verified firmware-read procedure exists yet.

The complete official firmware/BIOS/flasher package for this exact card was located on
Fujitsu's still-live firmware server and downloaded to the box. It matches the card's
family (firmware v4.07, BIOS v4.10). **The card currently runs 4.07-0-29; this package is
4.07-0-39 — slightly newer, same line.**

## Source (public, stable)
- URL: `https://download.ts.fujitsu.com/globalflash/ScsiController/DAC960PG/V4.07-0-39_4.10-41/zip_dac960pg_v4.07-0-39_4.10-41.exe`
- self-extracting ZIP, 346,864 bytes
- sha256 `4e83c865240c577f9f005e631e5aec0802afc491ede8ed8772085194829885b2`

## Contents
Original packages and decoded vendor binaries are now archived locally for Git
preservation under `artifacts/vendor-fujitsu/`. See `artifacts/ROM-INVENTORY.md`.
The URL above records the original source.

| File | Size | What it is |
|------|------|-----------|
| `DAC960FL.EXE` | 377,472 | **DOS flash utility (DACFL)** — the tool that issues LoadImage/StoreImage/ProgramImage |
| `407t39b0.img` | 229,898 | i960 **firmware** image, rev 4.07-0-39 (rel_note name `fgj40729.img`) |
| `BGJ41041.IMG` | 29,194  | **BIOS** (x86 option ROM) rev 4.10-41 |
| `FWPJBBLK.IMG` | 16,906  | firmware **boot block** |
| `gf.par`, `rel_note.txt`, `versionLeaf.txt` | — | GlobalFlash metadata (plain text) |

`rel_note.txt`: "Firmware, Bootblock und BIOS flash for DAC960G/J — Firmware fgj40729.img
Rev. 4.07-0-39, Bootblock fwpjbblk.img, BIOS bgj41041.img Rev. 4.10-41".

## Encoding finding (important)
The `.img` and `.EXE` payloads inside the package are stored in Fujitsu's **GlobalFlash
container encoding**, not as plain files:
- All payloads share an identical 8-byte header; none begins with `MZ` (DOS) or `55 AA`
  (option ROM).
- It is **not** plain, not whole-file bit-reversal, not a trivial XOR; the firmware portion
  is high-entropy (76% gzip) suggesting compression/encryption inside the container.
- The sidecar metadata (`gf.par`, `rel_note.txt`, `versionLeaf.txt`) is plain text.

### What this means
- **To reflash STOCK firmware (recover/update):** boot DOS and run the vendor flow (the
  Fujitsu GlobalFlash updater, or `DAC960FL.EXE` once GlobalFlash has written it out). This
  is the official, working path and does not require decoding anything by hand.
- **To enable in-system CUSTOM flashing** (the `FIRMWARE-PROTOCOL.md` goal — recover the
  exact StoreImage/ProgramImage mailbox params): one must first decode the GlobalFlash
  container to get a runnable/analyzable `DAC960FL.EXE`, then disassemble its mailbox code.
  That decode is an open RE task; simple transforms did not crack it.

## Net
The DOS flasher and the firmware image the user asked for are **found and archived on the
box**. Flashing stock via DOS is unblocked. Driving custom code in-system still needs the
GlobalFlash decode + flasher disassembly, or the external-programmer route in `REFLASH.md`
(for which `407t39b0.img`, once decoded, is a useful reference image).

## GlobalFlash container decode — attempted, partially mapped, not fully cracked

A real decode pass (brute-forcing per-byte transforms + structural analysis):
- **Padding transform is XOR 0xc3**: the dominant stored byte `0x3c` (10,140× in the BIOS
  img) = `0xFF ^ 0xc3` (flash erase state); `0xc3` = `0x00 ^ 0xc3`.
- **Container header is ~512 bytes**: the BIOS and firmware imgs share a 9-byte prefix
  (`b2 a2 b2 12 b2 a6 f2 e6 c3`); after XOR 0xc3 an option-ROM-style header (`55 aa 2c 6b
  af f8 …`) appears at offset 512.
- **But the code/string body does NOT decode** under XOR 0xc3 or any per-byte transform
  tried (xor 0..255, bit-reverse, rotations, nibble-swap, NOT): no `DAC960`/`Mylex`/`BIOS`/
  `Version`/`(c)`/`PCIR` strings emerge. The scattered zlib/gzip 2-byte "signatures" are
  coincidental (no valid streams at them).

**Conclusion:** the `.img` is a **packed vendor update format**, not a raw flash image — the
flasher decompresses it before writing (confirmed by the fact that the card's *actual* flash,
dumped via the expansion-ROM aperture, is plain `55AA`+strings, unlike this packed `.img`).
Fully unpacking it requires reversing the GlobalFlash / `DAC960FL.EXE` decompressor — a large
RE effort, deferred.

### Practical impact (unchanged bottom line)
- **Stock reflash / recovery:** use the vendor DOS GlobalFlash flow — it unpacks internally.
  Works today; no decode needed.
- **Custom in-system flash:** still blocked (needs the unpack + flasher mailbox disassembly).
- **External programmer:** remains the guaranteed route; it reads/writes the *raw* flash
  directly, bypassing this packed format entirely.

## UPDATE — GlobalFlash encoding CRACKED + StoreImage dump protocol recovered

The container encoding is solved (decoder: `host/globalflash_decode.py`, verified):
```
decoded = PERM(stored XOR 0xC3)        # PERM swaps bit i <-> bit i^6, self-inverse
```
Not compression — a fixed bit-permutation after XOR 0xC3. It equals plain XOR 0xC3 only on
permutation-invariant bytes, which is why whole-file XOR 0xC3 never revealed strings. Cracked
by crib-dragging the card's plaintext BIOS dump against the encoded `BGJ41041.IMG`.

`.IMG` files have a 512-byte header (`MIMGMYLX` + `"Ver 4.10-41 Released on Feb 02 1999"`),
raw image at offset 512; `DAC960FL.EXE` has no header. Verified decoded outputs (on the box,
`~/fwpkg/decoded/`; now also archived under `artifacts/vendor-fujitsu/4.07-0-39/decoded/`):
- `DAC960FL.EXE` -> `MZ` DOS exe; strings "DAC960 Firmware Upgrade Utility", "StoreImage".
- `BGJ41041.IMG[512:]` -> `55 AA 38 E9` option ROM; "DAC960 BIOS Version", "Mylex", "PCIR".
- `407t39b0.img[512:]` -> i960 firmware; the firmware itself is Huffman-packed internally
  ("Out of Huffman table space!", "Bad CRC %x").

### StoreImage (0x21) — the safe in-system firmware DUMP (from DAC960FL.EXE disassembly)
`DAC960FL.EXE` carries a symbol table; `_StoreRoadRunnerImage` builds a Type-3D mailbox and
loops in <=0xF000-byte chunks, card->host (a READ — the safe dump):
```
byte 0      opcode       = 0x21
byte 1      id/unit      = 0x01
bytes 2-3   WORD         transfer length in bytes (host clamps to <= 0xF000)
bytes 4-7   DWORD        flash/image byte offset of this chunk
bytes 8-11  DWORD        32-bit PCI DMA bus address of host buffer
byte 12     status       (card-filled)
```
- `0x2B` = config / Flash-Descriptor-Table DMA (subcommand@byte2, fixed buffer).
- **Flash WRITE is memory-mapped, not a mailbox opcode**: the flasher maps the flash into a
  PCI window and does erase-block / write-word directly (strings "Erasing Flash BlockNo %xH",
  "Writing FlashAddr %lxH with %lxH"). So there is no single destructive "ProgramImage"
  command — writing means map+erase+write.
- The flasher's own submission path uses a doorbell write `0xD0`@base+4 / poll base+5 (an older
  interface variant); our card responds on the **PG** map we already proved works (mailbox
  @0x1000, doorbell @0x20, status @0x101A), so the dump uses that with the Type-3D layout above.

**Impact:** an in-system firmware DUMP is now fully specified and safe (StoreImage is a
card->host read). It can be added to `host/kmod/dac960probe.c` using the proven mailbox path.
