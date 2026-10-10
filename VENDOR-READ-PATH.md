# Vendor read-path reconstruction and live result — 2026-10-10

**Current result:** [In-system recovery succeeded](SNAPSHOT-RECOVERY.md). A paired
512 KiB capture contains the exact 4.07-0-29 firmware and FWTCBBLK boot block,
plus the independently verified PCI BIOS. This supersedes older no-dump status
and the 256 KiB layout assumption below.

Latest: [FIRMWARE-HANDLERS.md](FIRMWARE-HANDLERS.md) documents verified firmware
unpacking, command dispatch, and a copy-on-first-use flash snapshot helper.
The reference is 4.07-0-39; the live 4.07-0-29 buffer remains unidentified.
The probe now limits the image window to 256 KiB. No valid dump exists yet.


**A card-to-host image-buffer read works. A physical-flash firmware backup is still
not obtained.** The controlled `0x20` tests returned repeatable data; offset zero
returned the exact `0x5A` pattern used in the earlier `0x21` experiment. This is
strong evidence of a shared staging buffer, rather than an immutable flash view.
Do not program this buffer or use these captures as recovery images.

## Correcting the symbol-record mistake

The prior analysis attached the address *after* each symbol name to that name.
This was wrong. Each public record is:

```
u16 offset; u16 segment; u16 flags; u8 name_length; char name[name_length];
file_offset = MZ_header_bytes + segment * 16 + offset
```

For decoded DAC960FL.EXE SHA-256
`1be1c11f5e030be80cd55b5c9215734f472daf4ee651abd1da57284e4888c552`,
the MZ header is `0x1800` bytes, and the contiguous 354-record public-symbol
block occupies `[0x5A29E, 0x5BBA7)`. The corrected mapping has coherent function
prologues and call/dataflow relationships. A version-specific extractor in
`host/dump/vendor_symbols.py` checks the binary hash and ten code anchors.
Its output is `artifacts/analysis/vendor-symbols.json`; vendor binary bytes are
not added to the repository. The tool does not execute the executable.

| Symbol | Correct file offset | Evidence/use |
| --- | --- | --- |
| `_GetImageHeader` | `0x1800` | Reads a file and checks MIMGMYLX magic |
| `_ReadFile` | `0x53EF` | Open, seek, read into supplied host buffer |
| `_load_image2` | `0x5232` | Builds opcode 0x20 with explicit buffer pointer |
| `_load_image` | `0x52D5` | Builds opcode 0x20 using global image-buffer offset |
| `_StoreRoadRunnerImage` | `0x552E` | Opcode 0x21 upload, descriptor updates |
| `_ProgramRoadRunnerImage` | `0x58F7` | Separate programming routine |
| `_StoreI2O` | `0x5AC4` | File read followed by opcode 0x21 |
| `_ReadFlashDescTbl` | `0x3C83` | Opcode 0x2B/subcommand 0x0D; fallback to subcommand 2 |
| `_xdcmd` | `0x8722` | Copies 13 mailbox bytes, dispatches by bus type |
| `_PCI_issue_cmd` | `0x992D` | Includes the PG register path |

The old claim that `_StoreRoadRunnerImage` or `_ReadFlashDescTbl` was a data
pointer/callback is withdrawn. They are functions. The file-to-0x21 flow previously
attributed to `_ProgramRoadRunnerImage` is actually `_StoreI2O`.

## Direction established from dataflow

`_load_image2` at `0x5232` accepts an image offset, length, and far host pointer.
It converts the host pointer through `_get_phy_addr`, then constructs:

| Mailbox bytes | Value |
| --- | --- |
| 0 | `0x20` |
| 1 | identifier (vendor uses 1; our transport uses fresh IDs) |
| 2–3 | byte count, little endian |
| 4–7 | image-buffer byte offset, little endian |
| 8–11 | host DMA address, little endian |

The related `_load_image` converts an offset into the global host `image` array
and submits the same mailbox. Callers at `0x32A5..0x3359` and
`0x5015..0x50C9` read preserved areas, including the last 16 bytes of an old image,
into corresponding positions of that host array. They then call `_store_image`
(`0x6C95`, opcode 0x21) to upload the assembled array. This establishes 0x20 as
card-to-host and 0x21 as host-to-card in this vendor image-buffer interface.

Independently, `_StoreI2O` calls `_ReadFile` before sending its buffer with 0x21.
`_StoreRoadRunnerImage` edits descriptor fields, uploads chunks with 0x21, then
sends a descriptor update. Its name is not a backup operation.

**Image offsets are not proven physical-flash offsets.** Direction and source
identity are separate questions. The new live observation below is the strongest
reason not to call these bytes a flash dump.

## Family submission and initialization boundaries

`_xdcmd` at `0x8722` copies 13 bytes without swapping 0x20/0x21, then dispatches
by a controller-record bus field: 0 → EISA, 1 → PCI, 4 → DACPVX, 2 → MC.
`_PCI_issue_cmd` checks the controller-record type at +0x0E. Its >=0x10 branch
at `0x9D35` uses IRQ mask +0x34, input doorbell +0x20, and output doorbell +0x2C;
it calls the mailbox writer at `0x9DDE` and status reader at `0xA1F6`.
This agrees with our already working PG transport. The old blanket description
of base+4/base+5 submission does not describe this branch.

The vendor also checks `_TsopPresent` (`0x713C`). `_load_image` skips its normal
mailbox path for a positive result, while `_store_image` takes a different path.
Thus the vendor itself does not treat every controller as having the same flash
interface. Complete initialization/type-table reconstruction and a firmware-side
handler mapping remain unfinished. The live test used the existing initialized
4.07 controller with no vendor initialization, reset, maintenance entry, or remap.

`_ReadFlashDescTbl` supplies additional offline leads: subcommand 0x0D receives
into `_ExtFlashDesc`, copies 0x160 bytes to a caller buffer, and falls back to
`_ReadOldFlashDescTbl`/subcommand 2 on failure. A caller checks `XLYM` at the
returned table start. This proves the vendor's intended reply use, but does not
establish compatibility or side effects for 0x2B on the running firmware. No 0x2B
command was sent in this work.

## Actual bounded reads

Host `mit@192.168.2.75`, controller `0000:37:09.1`, running version 4.07-0-29.
The module now permits only Enquiry2 (0x1C) and LoadImage (0x20); it no longer
permits 0x21. Each run used Enquiry2, two identical reads with A5/5A host sentinels,
and Enquiry2 again. All twelve completions had matching IDs, status zero, no
guard changes, and no pending transaction. All before/after enquiries returned
the same firmware-version bytes `04 07 1D 30`.

| Offset | Length | Result |
| --- | --- | --- |
| `0` | 512 | Both captures entirely `0x5A`; first read changed all A5 bytes |
| `0x200` | 512 | Both captures match, non-sentinel bytes |
| `0x200` | `0xF000` (61,440) | Both captures match; same first 512 bytes as previous run |

Offset-zero data exactly matches the pattern submitted by the earlier 0x21 run.
This strongly supports a staging-memory interpretation and means the earlier
statement “host buffers unchanged” must not be interpreted as “controller memory
unchanged.” The prior experiment likely overwrote the first 512 bytes of that
staging area. We did not attempt to restore unknown original bytes or commit it
to flash. The running firmware remained responsive.

The 60 KiB window starts `b7 12 77 80 dd f1 b8 07 0e 71 9a 68 0e 5c 17 1f`.
Its byte entropy is approximately 7.979 bits/byte. None of its 1,920 aligned
32-byte blocks occurs in either the available normalized 4.07-0-39 firmware
or boot-block image. That comparison does not exclude compressed/different-version
firmware, but provides no positive firmware identification. No offset sweep or
full-memory capture was performed.

Captures, exact transcripts, hashes, and classifier manifests are under
`artifacts/dump-load20-20261010/{offset0,offset200,window200}`. They are memory
captures, not verified firmware. The module was removed after each completed run;
final controller state is driverless, PCI command `0x0006`, BAR0 `0xEE000008`,
and the module is absent. No firmware-program opcode was sent.

## Reproduction and remaining work

```
python3 host/dump/vendor_symbols.py /path/to/decoded/DAC960FL.EXE
python3 -m unittest discover -s host/dump -p 'test_*.py'
python3 host/dump/validate_capture.py artifacts/dump-load20-20261010/window200
```

Kernel build with W=1 against the remote running kernel passed. Ten offline
regression tests pass, including the original captures, the new staging-pattern
case, real transfers that must not become backups, and symbol-record ordering.

The requested small controlled read is implemented and tested. What remains for
an actual firmware backup is establishing how this running firmware populates
or exposes its flash contents, rather than reading arbitrary staging offsets.
Use the corrected symbols to trace the controller type table, descriptor-read
preconditions, and (if unpacked) firmware command handlers. Do not use 0x21,
ProgramImage, reset, or a recovery-mode transition to populate this buffer.
