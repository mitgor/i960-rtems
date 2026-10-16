# Fresh-boot READIMAGE results — 2026-10-16

**Main stock firmware, boot block and BIOS recovered as matching pairs.**
This is not yet a complete 1 MiB physical flash backup.

Boot: `790e20a7-e84f-4f69-a137-937f71fd8eba`. AcceleRAID `0000:37:09.1`
was unbound at startup; old PG `0000:37:04.1` stayed unbound. Stock `myrs`
was prevented from binding by the previously documented temporary blacklist.

The first module load failed because `raid_class` was not loaded (no device
probe occurred). Loading that dependency resolved it. `probe_fresh.py` now
loads it explicitly. Fresh `myrsread` initialization succeeded. Two 1024-byte
descriptor reads both returned status 0 / residual 0 and identical bytes.

## Layout and successfully recovered images

| Selector | Image | Flash offset | Length | Result |
| --- | --- | --- | --- | --- |
| 1 | Boot block | 0xF0000 | 65,536 | matching pair |
| 2 | Main firmware | 0x40000 | 524,288 | matching pair; embedded ZIP CRC passes |
| 3 | BIOS | 0x30000 | 28,672 | matching pair; identical to earlier PCI ROM dump |
| 4 | EZAssist | 0x00000 | 164,575 | data returned, full residual; **not accepted** |
| 5 | Diagnostics | 0xC0000 | 64,512 | not yet verified locally |

The descriptor is a separate 1024-byte READIMAGE selector 14 result. Do not
assume a physical flash address for it from the selector alone. Unlisted flash
ranges have not been read; do not fill gaps with 0xFF and label that a full dump.

The cached controller reply confirms 100 MHz, one CPU, type code 7 (Linux's
`i960RM` enum), 16 MB memory, 8 MB cache, memory speed 66 MHz, flash size 1 MiB.
This is firmware-reported information, not an oscillator measurement or physical
CPU-marking identification. It supersedes earlier uncertainty from the `processor`
sysfs display; the raw reply and parser are retained.

`inspection.json` records all image hashes. Main firmware expands to 685,996
bytes with CRC32 `d93addd1`; reconstructed ZIP directory metadata is used only
for offline decompression, never added to the original dump. The boot block's
entry/PRCB/check word sum is zero. Its configuration words differ from the old
RP board; applying the old eight-word checksum formula would incorrectly flag it.

## Companion reader and failure boundary

The companion borrows the exact reviewed `myrsread` private ABI, pins the parent
module, shares the driver's direct-command mutex and queue lock, and uses normal
interrupt completion. It never binds, unbinds, resets, or programs a card.
Completed jobs explicitly release resources; pending jobs retain DMA memory and
module references. The driver itself remains initialized between reads.

Initial BIOS 1024-byte and full 28 KiB probes passed; the full image matches the
independent PCI capture. A 1024-byte main-firmware probe and full-size reads then
completed. The initial helper source is retained as `companion-attempt.c` and
`read-image-attempt.py`; requests record the attempted module SHA256. The module
binary remains on the remote host pending retrieval.

EZAssist's exact descriptor length is **not word-aligned**. The full read returned
status 0 but residual 164,575, despite filling the captured buffer with data.
The helper correctly rejected it. Subsequent queued attempts were a 1024-byte
EZAssist probe and a diagnostics read; SSH stopped responding before their
outcomes were obtained. The user confirmed the PC was frozen. We cannot identify
which operation caused the freeze from the evidence currently saved locally.

Potential explanations include a length/alignment handling bug or DMA outside the
requested region; neither is proved. The first companion allocated only the
requested DMA extent and did not scan guard space, so it cannot rule out an
overrun even for completed probes. Valid paired image contents do not establish
transport stability. No pending resources were forcibly unloaded after the loss
of SSH. A power cycle was requested; leaving the old card installed is appropriate
because no evidence implicates it in the failure.

## Prepared next revision — not yet hardware validated

The source companion now rejects non-word-aligned transfers and maps 64 KiB
sentinel guards on both sides of the destination, scanning them on completion.
The host permits only full descriptor-sized images rounded up to four bytes;
short image probes are disabled. Guard space is diagnostic, not an IOMMU safety
guarantee. The revised companion must be built and tested before reuse; it is
not the same build as the successful initial captures.

Next: retrieve remote failure logs and exact module after the power cycle,
reestablish fresh driver ownership, validate aligned full-image transfers with
guards (diagnostics before EZAssist), and investigate remaining flash gaps only
with verified addressing semantics. Keep the original PG untouched. Do not
program this board based on a partial chip backup.

Offline verification:

```sh
python3 host/accele160/readimage/inspect_dump.py artifacts/current/accele160-readimage-20261016/fresh
```

## Offline checks

Four tests pass: accepted component inspection; one-copy mutation rejection;
both-copy compressed-data mutation rejection via decompression/CRC; nonzero
residual rejection. The read-only inspector reproduces `inspection.json` exactly.
Python syntax checks passed. The new guarded companion has not yet been compiled
or run because the host is unavailable; its predecessor compiled and ran.

To build the guarded companion after recovery, copy `companion.c` and the
hash-pinned `myrs.h` into a fresh Linux build directory, create a Makefile with
`obj-m += companion.o`, and build against the running kernel headers. Preserve
and retrieve the first module before replacing it; captured requests record its
SHA256. Do not silently reuse the first unguarded module with the revised helper.
