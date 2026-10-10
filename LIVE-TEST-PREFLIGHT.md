# Next step toward live execution — 2026-10-10

Latest: [BOOT-RECOVERY.md](BOOT-RECOVERY.md) establishes an embedded recovery monitor (PCI 1069:0011) and partial vendor validation. Entry/restoration remain untested; continue over SSH without forcing a flash fault.

Latest programming audit: [PROGRAMMING-RECOVERY.md](PROGRAMMING-RECOVERY.md). The matching 512 KiB route uses 2B/1 and rewrites the lower 496 KiB; 22 returns an error on this route. An offline experimental MIMG package is archived, but vendor acceptance and recovery remain unverified.

**Read-only host preflight passed; custom loader execution remains untested.**
A second offline candidate closes two gaps in the first prototype: option-ROM
exposure and unchecked on-chip DMA. No image was flashed, no module was loaded,
and no reset, bind/unbind or PCI configuration write was performed in this step.

## Live result

Ran `sudo -n python3 .../postinit/preflight.py` on 192.168.2.75. It reads only
PCI sysfs metadata/configuration, not the memory aperture. The recorded result is
[the live preflight JSON](artifacts/postinit-preflight-20261010/live-preflight.json).

- Correct controller: 1069:0010 at 0000:37:09.1, driverless.
- BAR0: EE000000, 8192 bytes, memory access enabled; PCI command 0006.
- No dac960dump module loaded.
- ROM limit FFFF8000 and translation FEFA8000 remain the stock values. The
  currently disabled ROM BAR does not establish that the BIOS skipped it at boot.
- `host_preconditions_pass: true` means the host meets the inventory checks;
  `flash_ready` and `custom_loader_execution_verified` remain false.

This read cannot inspect local DMA/timer registers: the PG MU aperture must not
be confused with a general window onto those registers.

## Revision 2 candidate

Files: [artifacts/postinit-preflight-20261010/](artifacts/postinit-preflight-20261010/).
The first candidate remains archived in `postinit-prototype-20261010/`, with its
original entry assembly and image builder saved for provenance.

The RAM hook moves from **C004E844 to C004E834**, before the original code loads
1040 and clears PCI retry via EBCR. The new entry:

1. Disables core interrupts and data cache; invalidates instruction cache.
2. Disables the two core timers at **FF000308 and FF000318**. These full addresses
   come from the manual's Appendix C, not the abbreviated register labels.
3. Writes zero to ERLR at 1274, advertising no expansion-ROM space. BIOS payload
   bytes in flash remain unchanged. This aims to prevent the RAID option ROM
   issuing stock commands to a card now running our loader.
4. Masks MU outbound interrupt sources and inspects CSR0/1/2 at 1404/1444/1484.
   If any has channel-active bit 10 set, it publishes diagnostic status **60EF**
   in OMR0 and the combined CSR bits in OMR1, permits PCI configuration, and parks.
   It never publishes READY and does not pretend an active transfer was cancelled.
5. If all channels are idle, writes zero to CCR0/1/2 at 1400/1440/1480, rechecks
   active status, then applies the original EBCR value 8 and enters the loader.

The new loader is 832 bytes; the full candidate differs from stock in 666 bytes.
The reset vector, boot block, BIOS contents, descriptor, copied bootstrap and
compressed program remain unchanged. Hashes are in the candidate JSON manifest.

## Evidence and limits

The firmware's C004B750 routine (which the old hook skips) initializes DMA state
and descriptors. Therefore, we cannot rely on that routine to have quiesced DMA
when our loader starts. Stock code also polls CSR bit 10; the new guard covers
all three hardware channels, including channel 2.

Intel's [i960 Rx manual](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF)
provides the register semantics: §16.7.31 specifies ERLR zero as no ROM space;
§20.7 and Tables 20-2/20-4 describe the three DMA channels and active flag;
§19.1 and Appendix C identify the timers and their addresses.

The option-ROM change is a documented mechanism, **not yet a cold-boot result**.
If PCI configuration is accessible earlier due to straps or other firmware paths,
the host may race our setup. Cold-boot enumeration must still be tested.

The DMA guard concerns the i960's three channels. It does not prove downstream
SCSI bus-master inactivity, stop external watchdog hardware, validate stack space,
or establish that every indirect reference avoids the payload window. Timer disable
is not evidence that a board-level watchdog is disabled. These remain open.

## Validation and next gate

- Cross-build passed; target disassembly confirms the earlier hook, full timer
  addresses, ROM suppression, all three DMA checks and guarded paths.
- Native dispatcher test and ten Python tests passed. Tests cover image identity,
  unchanged stock regions, wrong donors/references, malformed sizes and read-only
  preflight behavior, including bound drivers and disabled/wrong-sized BARs.
- Current-source image generation reproduces the archived v2 image exactly.

The next substantive work is **the programming/recovery path**, alongside the
remaining downstream/watchdog audit. A raw 512 KiB candidate is not a vendor
update container. Component selection, accepted checksums and erase/write ranges
must be understood before sending a programming command. The existing requirement
for independent recovery is still unresolved; retaining stock boot-block bytes
alone does not prove recovery after an interrupted or incorrect flash.

Once those gates are satisfied, the first hardware acceptance sequence is:
PCI enumeration → ROM aperture absent → loader READY → ping → verified DRAM upload
of hello → GO → BEEF00EE execution marker. Status 60EF or any DMA uncertainty is
a stop condition, not an instruction to force reset/unload or proceed with GO.
