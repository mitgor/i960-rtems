# Official DAC960PG firmware package (found + archived on the box)

The complete official firmware/BIOS/flasher package for this exact card was located on
Fujitsu's still-live firmware server and downloaded to the box. It matches the card's
family (firmware v4.07, BIOS v4.10). **The card currently runs 4.07-0-29; this package is
4.07-0-39 — slightly newer, same line.**

## Source (public, stable)
- URL: `https://download.ts.fujitsu.com/globalflash/ScsiController/DAC960PG/V4.07-0-39_4.10-41/zip_dac960pg_v4.07-0-39_4.10-41.exe`
- self-extracting ZIP, 346,864 bytes
- sha256 `4e83c865240c577f9f005e631e5aec0802afc491ede8ed8772085194829885b2`

## Contents (extracted; kept on the box at `~/fwpkg/`, NOT committed here)
Vendor binaries are left on the user's machine rather than redistributed in this public
repo. Re-fetch from the URL above (it's the authoritative copy).

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
