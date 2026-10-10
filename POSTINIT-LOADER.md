# Firmware patch prototype — 2026-10-10

For the newer candidate that resumes stock firmware and adds a single PING
command, see [STOCK-PRESERVING-HOOK.md](STOCK-PRESERVING-HOOK.md). The prototype
below instead diverts startup into an exclusive loader and does not return to
stock firmware.

**Revision 2:** [LIVE-TEST-PREFLIGHT.md](LIVE-TEST-PREFLIGHT.md) records the live read-only host check and a newer candidate with an earlier hook, ROM suppression and three-channel DMA guard. The control-flow/size details below describe the preserved first prototype.

Built an **offline experimental 512 KiB image** that redirects stock firmware into
a host-controlled DRAM loader after early PCI initialization. No flashing,
controller reset, host reboot, or custom-code execution occurred in this work.
The prototype is not hardware validated and its manifest sets `flash_ready: false`.

Source and build instructions: [loader/postinit/README.md](loader/postinit/README.md).
Candidate and build evidence: [artifacts/postinit-prototype-20261010/](artifacts/postinit-prototype-20261010/).

## Actual boot path recovered

The live descriptor at full-image offset 0x79C60 describes firmware offset 0x30000,
length 0x38000. The installed FWTCBBLK reads a metadata record at component end
minus 0xA0: **full-image offset 0x67F60**, local address 0xFEFE7F60.

| Record offset | Stock value | Observed use |
| --- | --- | --- |
| +0x04 | C000C460 | Function called after copying bootstrap |
| +0x08 | C004A2E0 | Program entry returned to the boot block |
| +0x0C | 00006000 | Bootstrap copy length |
| +0x10 | 00001000 | Bootstrap source relative to firmware component |
| +0x14 | C000A000 | Bootstrap destination |
| +0x18 | F694B003 | Sum of copied bootstrap's 32-bit words |
| +0x1C | 00007000 | Compressed archive offset within component |
| +0x20 | C0010000 | Decompression destination |
| +0x7C | F6A09E48 | Sum of the preceding 31 little-endian words |

The boot block validates the metadata at FEFFCCCC–FEFFCCDC and the bootstrap
checksum at FEFFCD08–FEFFCD10. It copies the bootstrap at FEFFCD20, calls the
metadata function at FEFFCEE0, returns the entry at FEFFCEF0, and ultimately
branches to it at FEFFC614. Both checksums match the captured stock bytes.
C000C460 initializes globals, decompresses ZIP1, and finishes through C000C600,
the **512 KiB** profile. This resolves the earlier startup-route uncertainty.

The metadata entry is a useful hook: it avoids modifying the IBR, boot block,
compressed archive, or compressed-program checksum. The old `host/mkimage.py`
reset-vector assumptions do not apply to this full-ROM layout. Do not use its
old main-payload-at-top model for this patch.

## Prototype control flow

1. Builder places code in the verified zero-filled 4 KiB slot at image offset
   0x60000 (local FEFE0000), before metadata and after the compressed archive.
2. It changes metadata entry +8 to FEFE0000 and recomputes the +7C sum. Stock
   bootstrap copying, decompression and board-profile setup still occur.
3. The first stub patches **RAM** at C004E844 with `bx FEFE0034`, then branches
   to the original C004A2E0 entry. The original bytes at the patch site are
   checked against the hash-pinned unpacked firmware. Compressed flash bytes
   do not change.
4. Stock startup enters C004A9F0, which calls C004EE10 then C004E820. The latter
   runs C004D9A0 (ATU identity/aperture setup), C004DAE8, C004DC28, C004CB10 and
   C004DD10, then stores 8 to local EBCR at 1040. The hook is immediately after
   this store, before C004B750 and before the host command/bus-master wait loop.
5. The hook disables core interrupts and D-cache, invalidates I-cache, retains
   the external-memory call stack, and enters the polling loader. Stock RAID
   startup does not resume. Host transfers use MU registers, not new DMA commands.
6. The post-init profile accepts aligned payload access only in
   **C0120000–C012FFFF**, disables arbitrary register access, and invalidates
   I-cache before calling an uploaded entry. A leaf hello writes BEEF00EE to OMR1.

This is a static control-flow reconstruction, not a measured hardware handoff.
The two overwritten RAM words originally contain a call and the first word of an
LDA; there is no return to that instruction sequence. The original program remains
intact in flash. Disabling interrupts at the hook does not itself stop bus masters.

## New DRAM evidence from the installed boot block

The actual FWTCBBLK contains these direct startup writes (FEFFC4C8–FEFFC510):

| Register address | Value written |
| --- | --- |
| 151C | 00000B43 |
| 1520 | C0000000 |
| 1524 | 00000000 |
| 1528 | 00000000 |
| 152C | 000000CC |
| 1530 | 00000001 |

This supersedes the earlier statement that no direct DRAM-register setup had
been found; that analysis used a different boot-block reference. Values are
startup observations, not yet translated into timing specifications. Later
initialization may change them. Preserve stock initialization rather than
inventing settings.

C000D660 clears C0060000–C013FFFF before decompression. The candidate payload
window is in that initialized region, above the fixed globals seen through
C011E230 and below the allocator bookkeeping around C013FFC0. This supports
investigating the window; it does **not** prove freedom from indirect references,
DMA buffers or asynchronous activity. The earlier tentative C0080000 window was
rejected because the PCI startup path visibly writes state there.

Intel's [Rx manual](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF),
§6.2.23, identifies dcctl operation 0 as disabling D-cache; operation 1 enables it.
The prototype uses operation 0 at loader entry and icctl operation 2 before
executing uploaded instructions. Cache/alias behavior still needs target validation.

## Validation completed

- Cross-built 640-byte loader and 20-byte external-DRAM hello with GCC 3.3.6 /
  binutils 2.27; loader has no unresolved symbols.
- Inspected raw disassembly: flash entry, two RAM patch stores, original entry
  branch, hook, cache instructions, MU accesses and indirect payload call.
- Built a 524,288-byte candidate with a manifest of hashes and allowed changes.
  Only 538 bytes differ; boot block, IBR, BIOS, descriptor, bootstrap and compressed
  firmware are byte-identical to stock. Metadata sum revalidates.
- Five image tests cover the exact output, preserved regions, metadata/copy
  interpretation, wrong donors, truncated data, wrong runtime reference and invalid
  code sizes. Native tests exercise the actual post-init dispatcher, including
  internal-RAM GO rejection, DRAM bounds, readback and register-operation rejection.
- Existing loader native protocol/build tests and dump-tool tests were retained.

## Gates before installing

1. **Option-ROM boot behavior:** the preserved BIOS expects RAID firmware. Establish
   whether it can be disabled or will stall/overwrite our MU protocol while the PC
   boots. We have not demonstrated successful enumeration with the prototype.
2. **Ownership at the hook:** audit DMA channels, downstream devices, timers,
   watchdog and outstanding interrupt sources. Validate exclusive DRAM and stack
   use. intdis is not a complete device shutdown procedure.
3. **Programming format and checks:** a full raw snapshot is not a vendor MIMG update.
   Trace component selection, validation and erase/program boundaries before making
   a write tool or update container. The two verified boot metadata checks do not
   prove that every updater check is covered.
4. **Independent recovery:** no programmer comparison or restoration test exists.
   This work does not bypass the existing recovery gate or label the image safe
   to install merely because offline checks pass.

Next work should resolve gates 1–2 through offline startup/BIOS analysis, then
prepare the concrete programming/recovery procedure. Actual READY → upload → GO
→ execution-marker validation is still pending. No Mode 0 strap change is needed
for the proposed resident-loader behavior.
