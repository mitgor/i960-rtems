# Memory initialization findings from remote firmware analysis

Update: the actual installed FWTCBBLK directly writes registers 151C–1530; see [POSTINIT-LOADER.md](POSTINIT-LOADER.md). Earlier no-direct-DRAM-setup findings below concern the different FWPJBBLK reference.

Date: 2026-10-10. SSH access to `mit@192.168.2.75` works with the Mac's installed
key. Work is isolated in `/home/mit/i960-analysis.7jVBmy`. No firmware commands,
BAR writes, resets, module loads, or driver changes were performed.

## Environment and target build

- Host: `mit-HP-Z400-Workstation`, Linux `6.8.0-138-generic`.
- Target tools: GCC 3.3.6 and GNU binutils 2.27 in `~/i960/tools/bin`.
- Copied current loader sources into the isolated directory. `make all check test`
  passed, including actual i960 compilation/linking and Linux native regression tests.
- Loader binary: 652 bytes, entry `0xFEFCCD44`; hello binary: 48 bytes, entry `0x200`.
  The hello entry remains **invalid for instruction fetch on hardware**. Compilation
  does not resolve the architecture blocker in PROJECT-REVIEW.md.
- `check_build.py` passed against the actual decoded stock container
  `~/fwpkg/decoded/407t39b0.img.full`.
- Target disassembly showed GCC using g14 to store C zero initializers. The reset
  stub did not initialize it. Added `mov 0,g14` before calling C, then rebuilt and
  repeated target layout/symbol checks successfully. GCC's own i960.h documents
  g14 as an argument-block/leaf-return pointer, otherwise zero.
- GCC did **not** inline the dispatcher: `_loader_main` calls `_dispatch`. Keep
  the generated frames in the stack budget; source `inline` is not a guarantee.
- Saved the current target disassembly in
  `artifacts/analysis/loader-target.dis` and the vendor-profile fingerprints in
  `artifacts/analysis/dram-profile-manifest.json`.

## Normalize images before analysis

The vendor containers include a 512-byte header and ten-byte trailer. Extracted
both boundaries in the remote work directory, leaving the original files intact:

| Image | Raw length | Placement inferred from IBR position |
| --- | --- | --- |
| Firmware 4.07-0-39 | `0x38000` | `0xFEFC8000` |
| FWPJBBLK boot block | `0x4000` | `0xFEFFC000` |

Boot-block IBR gives firstIP `0xFEFFC400` and PRCB `0xFEFFD480`. Disassemble from
that entry, not the x86 option-ROM header at the beginning of the payload.
The raw images and full vendor disassemblies remain on the remote machine.

## Confirmed startup writes: static-memory banks

Both reset paths write the same constants below. Firmware instructions begin at
`0xFEFC802C`; boot-block equivalents begin at `0xFEFFC428`.

| Local register | Value | Intel register name |
| --- | --- | --- |
| `0x1500` | `0x007100F1` | MBCR |
| `0x1504` | `0xFE000000` | MBBAR0 |
| `0x1508` | `0x00040600` | MBRWS0 |
| `0x150C` | `0x00040600` | MBWWS0 |
| `0x1510` | `0xE0000000` | MBBAR1 |
| `0x1514` | `0x00060600` | MBRWS1 |
| `0x1518` | `0x00060600` | MBWWS1 |

These are **ROM/SRAM/flash-bank settings, not recovered DRAM timings**. Intel's
DRAM block is separate (`DBCR` at 0x151C through `DPER` at 0x1530). No standalone
32-bit literals for those DRAM register addresses were found in either image.
That does not prove absence of writes: indirect addressing, other code, or another
controller may be involved. See Intel i960 Rx manual chapter 14.

## Confirmed board-register profiles: strong DRAM initialization lead

Firmware routine `0xFEFC8330` and boot-block routine `0xFEFFC718` perform related
board initialization followed by accesses/tests in the `0xC0000000` memory range.
Both contain the following sequence:

1. Read the board register at `0x40800000`.
2. Select `0x257C203C` if original bit 5 is set; otherwise select `0x231C201C`.
3. Write a byte to board register `0xE0100000` and write the selected word to
   `0x40800000`.
4. Read-modify-write that word with bit 31 set and read it back.
5. Execute a 64-iteration flash-read delay, followed by additional delay/probing.
6. Clear bit 20, perform memory probes around `0xC3C00000`, and conditionally
   modify bits 15 and 13 and the board byte register.
7. Set bit 20 and perform bulk read/write accesses from `0xC0000000`.

The two profile literals occur at raw firmware offsets `0x3C8`/`0x3D8`, and
boot-block offsets `0x7B0`/`0x7C0`. A script checked the literal values in both
normalized images; their hashes and offsets are in the saved manifest.

The identical profiles and their placement before memory probes make this a
strong candidate for board memory configuration. **We have not identified the
board component, decoded the bit fields, or established nanosecond timing values.**
Do not name bit 31 or bit 20 as a refresh/enable bit without further evidence.
Nor should the profile be replayed without its surrounding initialization,
clock/board selection, and memory-size handling.

The same board block also participates in serial/manufacturing-mode handling.
Its presence is not proof that every field controls DRAM.

## Current card state, read-only snapshot

Both PCI functions have no bound driver. Controller BAR0 remains
`0xEE000000..0xEE001FFF`; PIALR `0xFFFFE000`, PIATVR `0xC0000000`, ERTVR
`0xFEFA8000`. Bridge EBCR low word is `0x0018`. This host aperture does not give
an established direct read path to the board register at `0x40800000`.

## Follow-up status (2026-10-11)

The exact 4.07-0-29 reference is now preserved and external-RAM execution has
passed repeated hardware tests; see [CURRENT-FINDINGS.md](CURRENT-FINDINGS.md).
Board identity and timing-field decoding remain unresolved. The list below
records the investigation plan at the time of this report.

## Historical next steps

- Identify the board register block and the meaning of bit 5 (board/clock/memory
  selection is a hypothesis, not a measured fact).
- Fully annotate both initialization routines and their conditional probe paths.
- Compare an exact 4.07-0-29 reference and its boot block if available.
- Recover the complete register sequence and delays; decode cycle counts only
  after identifying the controller and clock.
- Validate external executable RAM with a correct startup and bounded memory test
  before moving hello or other payloads there.

No DRAM timing profile has been programmed into the card. No flash image was
created or installed during this environment exploration.
