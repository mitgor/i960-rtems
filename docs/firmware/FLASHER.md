# DAC960FL.EXE — the DOS flash utility (decoded) + the MIMG image format

Latest programming audit: [PROGRAMMING-RECOVERY.md](PROGRAMMING-RECOVERY.md). The matching 512 KiB route uses 2B/1 and rewrites the lower 496 KiB; 22 returns an error on this route. An offline experimental MIMG package is archived, but vendor acceptance and recovery remain unverified.

The older image-building and live-flash recipes below are historical, superseded by POSTINIT-LOADER.md and this audit. Do not treat their legacy payload/IBR assumptions or safety claims as a procedure for the recovered full ROM.

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

Findings from the **decoded** `DAC960FL.EXE` ("DAC960 Firmware Upgrade Utility", (c) 1997
Mylex, build Jul 28 2000). Decode it from the Fujitsu package with
[`host/globalflash_decode.py`](../../host/globalflash_decode.py).

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

## Building a custom i960 image (DONE — tooling + verified)

Tools: [`host/mkimage.py`](../../host/mkimage.py) (image builder) and
[`host/i960stub.py`](../../host/i960stub.py) (proof-of-life payload).

### The stock IBR, located and decoded
The firmware payload is linked so its **end maps to `0xFF000000`**, so base =
`0xFF000000 − len(payload)` (stock: payload `0x38000` ⇒ base **`0xFEFC8000`**), and the IBR
sits at payload offset `len − 0xD0` = `0x37F30` ⇒ address **`0xFEFFFF30`** — exactly the
architectural IBR address. Stock IBR:

| word | value | meaning |
|---|---|---|
| 0–3 | `0x00000000` | PMCON14_15 bytes — **all zero in stock** (nothing to derive) |
| 4 | `0xFEFC8000` | first instruction = image byte 0 |
| 5 | `0xFEFC8B10` | PRCB pointer |
| 6 | `0x0206F4F0` | checksum word |
| 7 | `0x00000000` | — |

**Boot checksum rule (corrected by measurement): `sum(IBR words 0..7) == 0 (mod 2^32)`**, so
`word6 = −(word4 + word5)`. Verified: `0xFEFC8000 + 0xFEFC8B10 + 0x0206F4F0 ≡ 0`. (The
manual's "checksum ... with the constant FFFFFFFF ... passes when sum = 0" reads as ≡1; the
real images are ≡0. Trust the measurement.)

Stock PRCB (`0xFEFC8B10`): fault table `0xC0000800`, control table `0xFEFC8690`, AC image
`0x00009000`, fault cfg `0x40000000`, interrupt table `0xFEFC8700`, system procedure table
`0xFEFE0000`, interrupt stack `0xC0001000`.

### Strategy: redirect, don't rebuild
`mkimage.py` starts from the **decoded stock image** and changes only the IBR's `firstIP`
(plus the checksum word), keeping Mylex's known-good PRCB and system tables. The i960 then
initialises exactly as stock and jumps into our code. Custom code goes in a filler region —
default payload offset `0x4D44` (8,892 bytes of `0xFF`, addr `0xFEFCCD44`, word-aligned); a
32 KB zero region near `0x2FF00` is available for something larger. The builder refuses to
overwrite the control/interrupt/PRCB/system-procedure tables or run into the IBR.

### Verification achieved
- `--selftest` round-trips the stock image **byte-for-byte**, and the solver independently
  reproduces the stock checksum word `0x0206F4F0`.
- A built custom image: size **identical** to stock (229,898 B — matters, the flasher checks
  "File size expected"), magic `MIMGMYLX`, type `0x02`, length field `0x38200` = size−10,
  trailer intact, `firstIP` → `0xFEFCCD44`, recomputed checksum, `sum8 = 0`.
- Diff vs stock: **24 bytes** (20 code + 4 checksum). Minimal, auditable.

### Proof-of-life payload and how the host observes it
`i960stub.py` emits 20 bytes: `lda 0xC0FFEE01,g0 ; st g0,0x1318 ; b .` — it writes the magic
to the Messaging Unit **Outbound Message Register 0 (OMR0, i960 local `0x00001318`)** then
spins. The host reads the same register at **BAR0 + 0x18** (`0xee000018`).

Why that mapping is trustworthy: the card's PG window maps i960 local `0x1300+X → BAR0+X`,
corroborated by three independent agreements with the Linux PG register map — IDR
`0x1320→+0x20`, ODR `0x132C→+0x2C`, OIMR `0x1334→+0x34` (and we measured `0xfb` there, the
driver's "interrupts enabled" value). MU registers are internal MMRs, so the stub needs **no
memory-controller or DRAM init** — safe as the first instruction after reset. `BAR0+0x18`
currently reads `0x00000000`, so the magic will be unmistakable.

Build and check:
```
python3 host/i960stub.py i960stub.bin
python3 host/mkimage.py --stock <decoded-stock-fw>.bin --code i960stub.bin --out custom-fw.img
# flash (DOS):  DAC960FL -c 0=custom-fw.img
# verify (Linux, read-only):  sudo ./myflash probe 0xee000000   -> BAR0+0x18 == 0xC0FFEE01
```
**Still gated on an external-programmer backup first** — the flasher cannot dump, so flashing
is irreversible without one.
