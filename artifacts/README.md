# Artifacts

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
