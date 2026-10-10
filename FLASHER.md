# DAC960FL.EXE — the DOS flash utility (decoded) + the MIMG image format

Findings from the **decoded** `DAC960FL.EXE` ("DAC960 Firmware Upgrade Utility", (c) 1997
Mylex, build Jul 28 2000). Decode it from the Fujitsu package with
[`host/globalflash_decode.py`](host/globalflash_decode.py).

## Authoritative usage (reconstructed from the binary's help screen)
```
FL <file> <file> ...        ; upgrades DACs sequentially with the files specified
FL -c ctrl=img1,img2, ...   ; ctrl is DAC number (0 based), or allctl to flash all DACs.
                            ; img1,img2... = Boot Block, Firmware, Bios, Diagnostics
                            ; binaries for DAC960PJ and similar controllers
FL -d                       ; displays the details of Boot Block, Bios, Firmware, BCU,
                            ; and Diagnostics flashed on the controller
FL -i<ctrl>=<on|off|show>   ; I2O bit control
```
Option handlers in the binary: `_CtrlOption`, `_DisplayOption`, `_BinaryVerOption`,
`_I2OBitOption`. Note `-b` prints **"-b option not working yet..."** — unimplemented.

### IMPORTANT: there is no dump/save-to-file option
`-d` only **displays** versions/dates; nothing writes the flash contents to a file. So this
utility **cannot** be used to back up the existing firmware — a real backup needs an
**external programmer** (`REFLASH.md` §3). `-d` is, however, completely safe and read-only.

### Image validation (fails safe — a refusal does not write)
`"Invalid firmware file! Program terminated."`, `"Wrong type of image"`,
`"This Image CANNOT be flashed to the controller"`, `"File size expected=%ld"`,
`"Signature Mismatch in the Flash Desc Area"`, `"BootBlock record not found in the Image."`

## The MIMG container format (reverse-engineered)
Every `.img` payload, once GlobalFlash-decoded, is `[512-byte header][image][10-byte trailer]`:

| offset | size | field |
|---|---|---|
| +000 | 8 | magic `"MIMGMYLX"` |
| +008 | 4 | LE dword = **total file size − 10** (verified on 5 images) |
| +00C | 1 | constant `0x02` |
| +00D | 1 | **image type**: `01`=Boot Block, `02`=Firmware, `03`=BIOS |
| +00E | 2 | constant `0x0030` |
| +010 | 4 | version bytes (major, minor, turn/build) |
| +014 | 4 | day, month (**0-based**), year (LE word) |
| +018 | ~64 | ASCII `"Ver 4.07-0-39 Released on Dec 20 1999"` (NUL-padded) |
| +058 | 4 | constant `0x00000010` |
| +05C | .. | zero to +1FF |
| end  | 10 | constant trailer `03 93 c2 e3 52 2e 4f be 97 d3` (identical in all images) |

Observed samples: firmware 4.07-0-39 / 4.07-0-29 (229,898 B), BIOS 4.10-41 (29,194 B),
boot blocks 4.06-01 / 4.06-59 (16,906 B).

**No per-image CRC lives in the container** — the header beyond the fields above is all zero
and the trailer is constant. The `"Bad CRC %x"` / `"Out of Huffman table space!"` strings are
inside the **firmware payload** (the i960's own internal decompressor), not the container
check. So the container appears forgeable; the integrity that *does* matter for a custom
image is the **i960 IBR boot checksum** (see `REFLASH.md` §1).

## FreeDOS boot USB kit
A bootable image is built from FreeDOS 1.3 LiteUSB plus the decoded kit in `\DAC960`
(`DAC960FL.EXE`, `407T39B0.IMG` fw 4.07-0-39, `BGJ41041.IMG` BIOS 4.10-41,
`FWPJBBLK.IMG` boot block 4.06-01, and a `README.TXT` with a safe-first procedure).
The image itself is not committed (32 MB binary); rebuild:
1. Fetch `FD13-LiteUSB.zip` from
   `https://www.ibiblio.org/pub/micro/pc-stuff/freedos/files/distributions/1.3/official/`
2. Decode the Fujitsu payloads with `host/globalflash_decode.py` (keep the 512-byte header —
   the flasher expects whole MIMG files, and it checks the expected file size).
3. Copy them into `\DAC960` on the image's FAT16 partition.

**Why bare metal, not a VM/DOSBox:** DOSBox has no PCI bus, no PCI BIOS (`INT 1A`), and no
passthrough — structurally unable to reach the card. QEMU+VFIO passthrough is the only
virtual route, and this card shares a non-isolated IOMMU group (with a FireWire controller
and a chipset bridge), so it would require binding those to vfio too. Bare-metal FreeDOS is
the vendor-intended, reliable environment.
