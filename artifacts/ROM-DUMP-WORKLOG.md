# ROM dumping work log and findings

Current result, 2026-10-10: the card remained installed in the PC and yielded a
validated 512 KiB software snapshot. The main firmware is exactly 4.07-0-29.
All source packages, ROMs and capture sessions are now stored locally; start with
[ROM-INVENTORY.md](ROM-INVENTORY.md). Directory timestamps ending in `Z` are UTC;
for example `125336Z` is 14:53:36 in Europe/Berlin on this date.

## Investigation sequence

1. Reviewed the project and loader. Improved loader protocol bounds, fresh
   sequence handling, address policy, host checks and software validation, and
   documented outstanding hardware gates. Native tests do not prove hardware
   execution: the i960 internal RAM at 0x000–0x3FF is data-only, so the old
   hello-at-0x200 plan cannot work. See `loader/REVIEW.md`, `loader/PROTOCOL.md`,
   `loader/CLAUDE.md` and `PROJECT-REVIEW.md` in the project.
2. Explored the authorized SSH host, Ubuntu 6.8.0-138-generic, controller
   0000:37:09.1, PCI 1069:0010, with i960 bridge at .0. The card reports
   4.07-0-29. A PCI expansion-ROM read recovered the 28 KiB x86 BIOS, but did
   not expose the complete i960 program. BAR0 is an 8 KiB aperture; it is not
   a general mapping of flash or arbitrary local registers. Unbinding myrb had
   wedged previously; the subsequent experiments used an already driverless card.
3. Obtained Fujitsu's PG 4.07-0-39 package. Decoded the GlobalFlash transform:
   apply XOR 0xC3, then permute bit index i to i XOR 6 (see the archived decoder).
   Normalized firmware containers by removing their 512-byte header and ten-byte
   trailer. The executable and firmware then became available for static analysis.
4. Built a constrained coherent-DMA kernel experiment. Enquiry2 succeeded.
   The initial 0x21 experiment left host buffers unchanged. Later corrected
   symbol parsing and vendor dataflow showed why: 0x21 uploads host bytes to
   staging. Its final 0x5A fill contaminated staging; it was not a dump.
   No ProgramImage command was issued. Preserve this mistake as evidence;
   do not repeat it. See `DUMP-ATTEMPT.md` and `VENDOR-READ-PATH.md`.
5. Corrected DOS public-symbol parsing: address fields precede names. Verified
   0x20 card-to-host and 0x21 host-to-card directions. Restricted the harness to
   Enquiry2 and 0x20. Paired small reads confirmed working DMA, but returned
   staging fills or unidentified compressed-looking data, not a validated image.
6. Extracted the firmware's standard PKZIP method-6 ZIP1 program with Info-ZIP,
   validating output length, CRC and hashes. This is ZIP Implode, not DCL/blast.
   Recovered opcode dispatch, board callbacks, DMA descriptors and a helper that
   copies flash into staging once, then reuses the staging pointer. A previous
   upload therefore affects future reads until staging is renewed.
7. Analyzed memory initialization. Found static-bank register writes and board
   register profiles 0x257C203C / 0x231C201C. These are useful initialization
   evidence, not decoded DRAM timing values. Bit-field meanings, clock-dependent
   timings and their applicability to the installed boot block remain open.
   See `DRAM-ANALYSIS.md`; its older FWPJBBLK reference is not the recovered
   FWTCBBLK. No DRAM profile was programmed.
8. Downloaded the user's Fujitsu PRL 4.07-0-29 reference. Its bootstrap and
   relevant read/copy/DMA handlers match the 4.07-0-39 reference; decompressed
   programs differ by 555 bytes. This removed version mismatch as an explanation
   for the unexpected read offsets. See `FIRMWARE-40729.md`.
9. Read the entire initially allowed 256 KiB window. Found the first 64 KiB
   of the exact main firmware at offset 0x30000, with its ZIP at 0x37000.
   The previous expected offset 0x8000 had come from a different startup profile.
10. The host became briefly unreachable and returned with uptime below one minute.
    A reboot had been authorized, but this agent did not issue it. A fresh read
    now began with an intact EZAssist ZIP. Firmware at 0x30000 and BIOS at 0x28000
    supported the alternate 512 KiB profile, source FEF80000, descriptor FEFF9C00.
11. Extended the tested PG harness bound to 0x80000 and captured nine chunks,
    each twice with different host fills and Enquiry2 before/after. All 36
    completions had correct IDs, zero status, intact guards and pending=0.
    Both assembled 524,288-byte images are identical. Full-image SHA-256:
    `43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93`.
12. Validated main firmware against the vendor 4.07-0-29 payload, boot block
    against FWTCBBLK, and BIOS against the independently read PCI ROM. All are
    exact matches. ZIP1 extracts to 304,120 bytes with CRC 8a9d7f6c; EZAssist
    extracts to 545,516 bytes with CRC 9c5a2a90. No missing bytes were filled
    from vendor images. Removed the module after completion; controller remained
    driverless with PCI command 0006. Kernel build and 14 offline tests passed.
13. Copied both original Fujitsu packages, extracted package members and metadata,
    decoded references, all three snapshot sessions, disassemblies and collector
    to this Mac's `artifacts/` folder. Rechecked package hashes and ROM identities,
    and created a local file inventory and checksums.

## Findings that govern future work

- 0x20 reads firmware staging, not necessarily fresh physical flash on every call.
  0x21 uploads; 0x22 programs. Only 0x1C and 0x20 belong in this read harness.
- Success status and repeatable bytes alone are insufficient. Identity was
  established with full payload comparisons, archive CRCs and the independent BIOS.
- Firmware raw offsets and relocated runtime addresses differ. The copied
  bootstrap uses raw offset + C0009000; decompressed code begins at C0010000.
  Static disassembly labels using FEFC8000 do not establish the live image's base.
- The live image places firmware at 0x30000, BIOS at 0x28000, descriptor at 0x79C00,
  and boot block at 0x7C000. The prior 256 KiB limit was a mistaken generalization
  from the standalone startup path. See `SNAPSHOT-RECOVERY.md` for the full layout.
- PRL package main firmware and boot block exactly match this card. Its BIOS
  differs, and the PG package's FWPJBBLK also differs. Whole-package interchangeability
  has not been established.
- A command timeout is not DMA cancellation. The harness retains DMA memory and
  pins itself on uncertain completion; do not force unload or reuse that state.
- Paired reads came from one staging snapshot. Physical chip capacity, an
  independent programmer comparison and restoration have not been tested.
  The existing independent-backup gate before flashing remains applicable.

## Remaining work

The dumping objective is achieved for the installed main firmware and the 512 KiB
software image. Further work can proceed offline: trace the recovered FWTCBBLK
startup, decode descriptor/component records, and map DRAM profile bit fields
against the correct board hardware. Loader execution and reflashing are separate
unfinished goals; nothing in this dump validates the old internal-RAM execution plan.

Older reports retain the observations and hypotheses available at each stage.
For current status, this log and `SNAPSHOT-RECOVERY.md` take precedence over older
claims that dumping is impossible, that 0x21 reads, or that no valid image exists.

## Git preservation update

At the user's request, removed the exclusions for `artifacts/vendor-fujitsu/`
and `artifacts/private-dumps/`. Original packages, decoded firmware, hardware
captures and supporting analysis are intended to be committed with their provenance
and checksums. Existing directory names remain unchanged so links keep working.

## Remote completeness audit

Compared 295 remote project files with local content and archived 20 additional
items, including the Enquiry2 control log, historical analysis scripts, alternate
BIOS disassembly, old probe source and exact acquisition/target builds. See
[the audit report](remote-audit-20261010/README.md). No modified original files
were found in GCC 3.3.6 or binutils 2.27 sources compared with their upstream
tarballs. The important firmware and capture data were already local.
