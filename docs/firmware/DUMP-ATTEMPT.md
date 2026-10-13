# In-system firmware dump attempt — 2026-10-10

> **Latest follow-up:** [VENDOR-READ-PATH.md](VENDOR-READ-PATH.md) corrects the
> vendor symbol addresses and verifies opcode 0x20 card-to-host transfers.
> Returned bytes appear to be staging memory; no physical-flash backup exists.
> Opcode 0x21 uploads host bytes and must not be used as a dump command.


**Result: no i960 firmware dump obtained.** The host/card command and DMA path
worked, but two 512-byte opcode-0x21 transactions produced no changes in their host buffers.
The controlled attempt narrows the earlier transport uncertainty; it does not
prove that all in-system read paths are impossible.

## What ran on the actual card

SSH target: `mit@192.168.2.75`. Controller: `0000:37:09.1`, `1069:0010`, initially
and finally driverless. No disks or RAID-driver operations were performed.
Built a separate `dac960dump` module in
`/home/mit/i960-analysis.7jVBmy/dump`, using Linux 6.8.0-138-generic headers.
The old `dac960probe` module was not used.

The new transport requests PCI regions, uses the kernel coherent DMA API with a
32-bit mask, checks status command IDs, refuses stale/busy input, uses 32-bit
PG doorbell/mask accesses, and preserves DMA allocations on uncertain completion.
No timeout or mismatched completion occurred in this attempt.

First ran an Enquiry2-only control. It returned status 0, ID 1, changed 128 bytes,
no guard changes, and firmware version bytes `04 07 1d 30` (4.07-0-29).
Then unloaded that completed control module and ran this sequence:

| Command | ID | Length argument | Offset | Sentinel | Status | Changed bytes | Guard changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Enquiry2 `0x1c` | 1 | 0 (implicit reply size) | 0 | `0xa5` | 0 | 128 | 0 |
| Historical image command `0x21` | 2 | 512 | 0 | `0xa5` | 0 | 0 | 0 |
| Historical image command `0x21` | 3 | 512 | 0 | `0x5a` | 0 | 0 | 0 |
| Enquiry2 `0x1c` | 4 | 0 (implicit reply size) | 0 | `0x5a` | 0 | 128 | 0 |

Every completion matched the submitted identifier. The actual DMA bus address
for the four-command run was `0xfffc0000`. Full mailbox words and head bytes are
recorded in artifacts/dump-attempt-20261010/result.txt.

The first image capture is entirely 0xa5 and the second entirely 0x5a. Because the
output follows the host's initial pattern rather than the card's contents, they
are **untouched host buffers**, not erased flash and not a firmware image.
This rules out useful card-to-host output in these buffers. It does not establish
that no DMA occurred: a controller reading host memory would leave it unchanged. No larger
0x21 read or alternative offset sweep was attempted after this result.

## Important correction: the 0x21 direction is not established

Offline analysis of the decoded vendor `DAC960FL.EXE` showed that the code around
file offsets `0x5B67..0x5B8E` calls a helper that seeks/reads a file into a host
buffer. Later code at `0x5C18..0x5C4C` constructs opcode 0x21, length at bytes 2–3,
offset at bytes 4–7, and that buffer address at bytes 8–11. The initial offset
in this path is 0x80000, not zero; the length is capped at 0xF000.

This is associated with the code address assigned to `_ProgramRoadRunnerImage`
under the current MZ/symbol reconstruction. It strongly suggests staging bytes
**from host to controller**, rather than a general card-to-host firmware read.
The symbol `_StoreRoadRunnerImage` resolves into a data segment under that same
reconstruction, so finding its name was never sufficient to identify a callable
dump routine. Segment/callback reconstruction still needs verification.

Separate routines construct opcode 0x20, but their direction, arguments and
controller-state preconditions are not yet verified. They were **not** run on the
card. Neither was 0x2B (background-initialization control in the field-firmware
header), 0x22 (ProgramImage), diagnostic mode, explicit flash erase/program sequences,
controller reset, ROM-window remapping, or board-register writes.

The earlier project statements “StoreImage is definitely a safe card-to-host read”
are therefore superseded by this uncertainty. Do not use the historical opcode
names or a status-zero response as evidence of DMA direction or absence of effects.
In this actual run, the DMA buffers did not change and Enquiry2 remained healthy;
that is the measured observation. Firmware version consistency alone does not
prove bit-for-bit flash contents are unchanged.

## Captures, cleanup, and tests

Local artifacts: `artifacts/dump-attempt-20261010/` contains the transcript, both
sentinel captures, before/after Enquiry2 data, and a JSON manifest with hashes.
No file is named fwdump or represented as a valid firmware image.

Collected the captures, then removed the module with all transactions completed.
Final state: no bound controller driver; PCI command `0x0006`, BAR0
`0xee000008`, matching the pre-attempt state. Saved IRQ mask was `0x000000ff`
and was restored on removal. No pending DMA or retained allocation remained.

- Module build against the running kernel: PASS.
- Live Enquiry2 control and fresh completion-ID checks: PASS.
- Live opcode-0x21 transfer: FAIL to produce data, status-zero completion.
- Five capture-classification regression tests: PASS.
- Captures classify as `no_host_buffer_update`, with backup verification explicitly false.

## Next actionable work

Recover the vendor's actual card-to-host read operation and family-specific
controller initialization/callbacks. Confirm direction from memory/file dataflow
and, where available, the firmware handler. Only then add that verified operation
to the constrained transport and attempt a small controlled read. Do not substitute
another opcode or force recovery mode merely because this experiment returned no data.

The card stays installed in the PC. A complete physical-flash backup without an
external programmer remains unachieved.
