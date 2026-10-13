# DAC960PG x86 BIOS (option ROM) analysis

Disassembly/analysis of the card's PC-side BIOS — the plaintext 28 KB option ROM we dumped
in-system (`artifacts/dac960pg-x86-bios.rom`). Unlike the GlobalFlash-packed update images,
this is the real runtime ROM, so it disassembles directly (`objdump -b binary -mi386
-Maddr16,data16`).

## Structure
- PCI option ROM: signature `55 AA`, size byte `0x38` = 56×512 = 28,672 bytes.
- Entry: `e9 fa 2f` at offset 3 → **init at 0x3000** (`jmp`).
- PCI Data Structure ("PCIR") at offset 0x28: vendor `0x1069` (Mylex), device `0x0010`,
  code type 0 (x86). Single image.
- Banner: "DAC960 BIOS Version " (label at ROM offset 0x464d; version filled at runtime),
  "[c] MYLEX Corporation". Family BIOS v4.10.

## Boot flow (from code + strings)
1. Locate the controller and read its BARs via **PCI BIOS `INT 1A`** (AH=B1h services) —
   many `int 0x1a` calls in the 0x3000+ init.
2. **Enter unreal mode** to reach the memory-mapped register window: `lgdtl`/`sgdtl` +
   `mov %cr0,%eax` / `mov %eax,%cr0` PE-bit toggle (at 0x128d–0x12b6), loading 4 GB-limit
   segments, then returning to real mode. Thereafter it uses 32-bit segment-override moves
   (`66 26 … %es:…`) to read/write the controller's BAR0 registers at `0xee000000` directly.
3. Run controller self-tests: "DAC960 fatal error - memory test failed!", "command
   interface test failed!" — i.e. it exercises the same command mailbox we drive from Linux.
4. Verify integrity: "firmware checksum error - reload firmware", "configuration checksum
   error", "Mismatch between NVRAM & Flash EEPROM configurations". It also monitors flash
   wear: "WARNING: The Firmware Flash EEPROM is reaching the end of its life".
5. **Load the RAID configuration software** (the Alt-R utility) from the controller:
   "Checking… / Loading… / Starting RAID Configuration software" (or "…not found").
6. Spin up drives, enumerate system drives, hook **INT 13h** to present RAID volumes as BIOS
   disks. Falls back to low memory **segment 0x7000** as a work/transfer buffer when no other
   free RAM ("No free RAM found for DAC960 operation- using 7000:0000").

## Card-access mechanism (the useful bit)
- Discovery: `INT 1A` PCI BIOS.
- Register access: **unreal-mode flat 32-bit** reads/writes to BAR0 (`0xee000000`) — the same
  PG mailbox/doorbell window our kernel module (`host/kmod/dac960probe.c`) drives via
  `pci_iomap`. Independent confirmation that BAR0 is the command interface.
- Data buffers: low real-mode memory at `0x70000` (seg 0x7000), which the controller
  bus-master DMAs to/from — the "memory mailbox" style, analogous to our
  `dma_alloc_coherent` buffer.

## What the BIOS does NOT do
It does **not** flash firmware — it only *checks* the firmware checksum and tells the user to
"reload firmware". The actual LoadImage/StoreImage/ProgramImage flashing lives in the DOS
`DAC960FL.EXE`, which is GlobalFlash-packed (being reverse-engineered separately).

## Takeaways
- Confirms the whole command path we built on: BAR0 = PG register window, low-RAM DMA buffer,
  same self-tests. Our in-system `Enquiry` success is exactly what this BIOS does at POST.
- The firmware-flash protocol is not in the BIOS; it's in the flasher. So cracking the
  GlobalFlash container + disassembling `DAC960FL.EXE` remains the route to in-system custom
  flashing.
