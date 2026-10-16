# Secondary SCSI stop and resident RAM boundary

Follow-up: [exclusive exception ownership and limited RAM grant](FAULT-OWNERSHIP.md)
now supplies real fault/NMI tests and a separately validated external packet queue.
The 72-slot build and remaining gates below describe this earlier batch.

The optional `rtems/build.py --profile residentnet --secondary-reset` build
adds a destructive, reboot-only stop of the private secondary PCI bus. Default
residentnet and all cooperative profiles keep their previous behavior. No flash
changes, SCSI commands or guessed chip-register writes are used.

## Identify before stopping

Fixed pages 16–28 read the firmware channel structures, not chip MMIO. This
board has one channel. Its firmware ID is vendor `1000`, device `000c`, revision
2; the primary/secondary flag is zero and the secondary-channel count is one.
The register mapping is `88000000`, PCI BAR `fff00000`, SCRIPT mapping `88002000`,
and configuration selector `10`. Firmware initialization at `c004f500` installs
these secondary-bus Symbios mappings. The alternative primary-bus and BusLogic
paths are preserved as evidence, not used as this board's recipe.

Page 29 corroborates the metadata through a single identified private PCI
device. It temporarily selects configuration offsets 0, 4, 8, 14 and 18 using
SOCCAR (`12a8`) and reads SOCCDP (`12b0`), then restores the selection. There are
no device configuration writes and no scan of absent devices. Observed values:
`000c1000`, `02000006`, `01000002`, `fff00000`, `fff02000`; SOCCAR restores to
`0001000c`. [Linux's PCI IDs](https://github.com/torvalds/linux/blob/master/include/linux/pci_ids.h)
identify `000c` as the Symbios 53C895. The earlier FlashPoint lead does not match
this live device.

## Stop contract

[Intel's Rx manual, table 15-35](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF)
describes BCR bit 6 as secondary reset: it resets bridge queues/buffers, halts
DMA2 and secondary ATU transactions, and resets secondary devices. The
[272918-019 specification update, item 7](https://datasheets.chipdb.org/Intel/80960/specupdt/27291819.PDF)
notes that firmware must arrange reset detection/reinitialization itself.
We hold reset asserted until host reboot. This forcibly stops/discards work;
it does not establish graceful completion or disk-data consistency.

The adapter rechecks the exact channel metadata and live PCI identity before
phase-2 isolation. It refuses any i960 DMA activity, missing internal-arbiter
ownership, an existing reset, or NMISR indication. It records irreversible
ownership before writing BCR. The write avoids acknowledging the W1C discard
status bit. It reapplies deny-all secondary grants, then requires three stable
readbacks within 4,096 attempts. Timeout retains reset/resources. No failure
path releases reset or returns to stock firmware.

The first physical run read primary command 2, secondary command 0, BCR `242`,
SACR `13ffc`, and zero DMA words. RTEMS timers, task interrupts, message-register
control and IPv4/IPv6 networking worked during held reset. Snapshot word 63 bit
1 revalidates this hardware state; bit 0 remains the existing memory check.
The host driver still disallows a second firmware callback and retains its
allocation/module at close. See the [capture ledger](../../artifacts/notes/rtems-scsi-stop-20261011.md).

## Why broader RAM is still gated

The stock NMI path at `c004e2e8` can reinitialize the secondary bus after detecting
reset. Priority 31 does not mask NMI. A successful quiet run is therefore not
permission to overwrite every cache buffer: asynchronous firmware fault/error
paths remain relevant. Pages 30–31 inspect the cached NMI vector, PRCB, fault
table and initial entries without changing them. The live PRCB was ROM
`feffd4d0`, so the RAM-only pointer guard skipped its dereference. Its fault
table is `c0000800` in the independently paired programmed-ROM captures;
the emitted sentinel words are not live fault entries. Cached NMI was
`c004e190`, directly matching the stock error-handler entry.

`ram_transfer.h` is an **offline policy prototype**, not a runtime grant. Its
fixed candidate is `c0200000..c0240000`, within the identified cache-data range,
with 64-byte end guards. It requires topology, held reset, disabled secondary
access, idle DMA, exclusive CPU ownership, dependency audit, capacity and pattern
proofs. No live code calls it; `ram_reclaim()` still rejects all external RAM.
Before enabling it, own or quarantine NMI/fault paths, audit the surviving
monitor dependencies, and perform a bounded non-aliasing/guard test on the card.
No destructive pattern test has been run outside the upload allocation.

## More useful storage inside the existing grant

The new resident queue has 72 slots of 1,500 bytes instead of 64 slots of 1,536
bytes. The raw-IP host and target transport already enforce an MTU of 1,500;
the extra per-slot padding was unnecessary. Packet storage rises from 98,304
to 108,000 bytes. The shared cooperative default remains eight 1,536-byte slots.
The linker and `ram_audit.py` verify the whole queue object remains inside the
existing guarded mutable range. RNT3 (`33544e52`) identifies this capacity;
RNT2 remains supported for historical captures. Native tests exercise actual
queue operations at both sizes and reject a 1,501-byte resident packet.

`--round-interval SECONDS` spaces dual-stack traffic throughout a run. A round
that overruns its slot starts the next round immediately, without dropping or
reordering rounds. Completion timestamps are recorded. The append-only control
journal avoids repeatedly serializing the growing snapshot history; final
replay requires every journal event to match the complete control capture.

Final physical acceptance: 36,000 ticks, ten concurrent IPv4/IPv6 rounds
30 seconds apart, 73 unique burst echoes / 23 counted drops, high-water 72,
TCP loss recovery and both IRQ continuations drained at the deadline. Independent
replay validates the pinned image/module, control journal, packets and guarded
held-reset snapshots. See [batch evidence](../../artifacts/notes/rtems-scsi-stop-20261011.md).
