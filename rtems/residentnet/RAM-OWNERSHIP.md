# Firmware allocations, SCSI bookkeeping and resident capacity

This batch keeps exclusive RTEMS inside the established 512 KiB staging
allocation. It doubles the resident packet queue from 32 to 64 slots (98,304
payload bytes), leaving 12,000 bytes of unused mutable space in the tested link
map. Cooperative `net`/`autonet` still use eight slots. `ram_reclaim()` still
rejects every external interval. No flash, SCSI command or SCSI reset is added.

## Allocation map from the matching firmware

`allocation_audit.py` checks the disassembly against the SHA256-pinned vendor
program, then checks the captured metadata against the recovered arithmetic.

| Region / property | Evidence |
|---|---|
| Detected RAM | Firmware global `c00a8718` reports 16 MiB. |
| Cache data starts | `c0140000`. |
| Cache line | `c009c3f8 = 16` sectors, or 8,192 bytes. |
| Line count | Table + `120` = 1,876; `(RAM - 140040)/(8192+52)`. |
| Descriptor base | `c00600ec = c0fe8000`; data start + line count × line size. |
| Descriptor extent | 1,876 × 52 bytes, ending at `c0fffd10`. |
| Upload staging | `c0112a70 = c0f2c000`, image size table + 8 = `80000`. |
| Apparent adjacent space | `c0fac000..c0fe8000`, 240 KiB, still cache data. |

The helper at `c004d230` returns the existing staging pointer. If absent, it
clears a warm marker, reserves cache lines through `c001ea70`, records the
pointer and copies the ROM. This is not a general-purpose RAM allocator.
For this image the reservation arithmetic uses `80000/2000 + 1 = 65` lines;
`(table124 - 65 - 2) * 2000 + c0140000` gives `c0f2c000` exactly. The extra
line and nearby descriptors do not become ours through that arithmetic.
Do not call the helper again or overwrite allocator lists to obtain more RAM.

The warm marker near the end of RAM, cache descriptors, stock continuation,
firmware globals and channel structures remain reserved. A linker change alone
cannot enlarge the grant. A future destructive exclusive layout needs a proved
engine-stop contract, an inventory of all monitor/IRQ dependencies, and a cold
restart path. Cooperative operation must continue using the original allocation.

## SCSI ownership evidence and remaining gate

The firmware debug format at `c0010ab0` names four counters. Its call site at
`c0010dc0` supplies `c006011c` (DrvQcnt), `c0060120` (IodQcnt), `c0060124`
(SkedQcnt), and `c0060128` (ScsiIoCount). The last is incremented at `c0051688`
and decremented at `c004bb28`; a busy predicate at `c004a260` tests it for zero
while setting another global. We only read these variables: invoking that
predicate would change firmware state. Fixed diagnostic page 15 reads them
without introducing a host-selectable address.

After the recovery reboot, page 15 read `DrvQcnt=0`, `IodQcnt=0`,
`SkedQcnt=4`, `ScsiIoCount=0`. These were observed after a bounded 100-tick
phase-2 run returned to stock firmware, not an atomic shutdown certificate.
The scheduler still had entries.

Zero counters would not certify an empty hardware FIFO or drained posted bus
transactions. Existing exclusive isolation disables i960 DMA and PCI mastering,
and denies external secondary-bus grants. That blocks new grants; it does not
prove all earlier SCSI activity has finished. The firmware includes Symbios
SCRIPT parameter names and command construction; this does not establish which
physical SCSI chip is installed. The older FlashPoint reset lead is not an
approved reset recipe. Constants `a0000000/a1000000` in command construction
must not be assumed to be MMIO bases.

## Implementation contract

Resident admission now checks board selector 6, dispatch table `c0110780`, CPU
XOR pointer `c000d540`, sizing pointer `c004fc40`, 16 MiB report, staging
`c0f2c000`, and 512 KiB image size. It checks the table address before reading
its fields. Native tests flip each of 224 identity bits and require rejection.
This is a board/profile check, not a claim to external memory.

Snapshot words 57..59 use version marker `RNT2` (`32544e52`), enqueue-drop
count, and queue high-water mark. Words 60..63 retain accepted RX, released TX
blobs, rejected requests and memory/guard validity. Old captures retain their
old cache observations. The verifier supports both formats.

`live.py --burst` sends 96 UDP requests while withholding TX consumption,
requires a full 64-slot queue and counted drops, then drains and verifies exact,
unique echoes. `--parallel` runs IPv4 and IPv6 clients concurrently per round.
Explicit RX EAGAIN keeps the same pending packet; uncertain failures are not
retried. Saved raw ioctls are replayed independently for checksums, UDP burst
contents, TCP stream bytes, queue bounds and final snapshot invariants.

See the [batch evidence](../../artifacts/notes/rtems-ram-ownership-20261011.md)
for measured results, pinned binaries, recovery and the 30-step ledger.
