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
