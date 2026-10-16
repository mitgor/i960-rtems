# Resident networking and RAM ownership

For the optional Doom engine in the existing 8 MiB application arena, see the
[bounded visible-frame milestone](../../artifacts/notes/doom-visible-20261013.md).
Its new UPL1 operation 9 uses mailbox selectors `0x6c..0x6e` to read a published,
immutable post-return frame archive. Epoch, session, pending-command and
uncertainty checks remain mandatory; it exposes no arbitrary address reads.
The static browser gallery runs on the host and never opens the card.

Shared allocation cancellation and exclusive timer-based heap measurements are
available with `--heap-shared`; see [the contract and replay instructions](SHARED-HEAP.md).

Latest follow-up: [general application heap and containment](GENERAL-HEAP.md).
The opt-in heap uses 69,952 bytes within the validated 256 KiB range, alongside
the 128-slot external queue. [Fault/NMI and RAM ownership](FAULT-OWNERSHIP.md)
and [SCSI stop](SCSI-STOP.md) describe its prerequisites. The measurements below
are historical and do not describe the latest optional layouts.

This experimental profile runs RTEMS and lwIP after the single ARM firmware
callback returns. The original firmware IRQ continuation remains parked. It
inherits exclusive phase-2 isolation: inactive i960 DMA, primary and secondary
PCI bus mastering disabled, external secondary master grants denied. It exits
only by host reboot or power cycle. **Never force-unload the retained module.**

The cooperative `net`/`autonet` profiles remain the production/future coexistence
option. This profile makes no flash change and performs no disk operation.

## Tested implementation

`runtime.c` includes the exclusive RTEMS scheduler with optional networking hooks.
Worker 0 services lwIP in bounded masked sections; worker 1 remains preemptible
CPU work. The real timer IRQ supplies elapsed ticks. lwIP is NO_SYS and is never
called from the interrupt handler; its packet queues are static and single-owner.
The independent control channel is polled both by the timer and worker 0, with
worker polling masked against the ISR. STOP drains both task IRQ continuations,
parks RTEMS, rejects further packet work and retains all memory until reboot.
Pending TCP state or queued packets are not a promise of graceful peer shutdown.

`network.c` reuses the existing IPv4/IPv6 lwIP stack. The proof endpoint serves
plain text on TCP 80; TCP 9600 and UDP 9601 echo data. The production Darth Vader
page stays in `autonet`. The current resident harness is bounded to 6,000 ticks
(about 60 seconds), not a permanent public service.

No host-memory DMA is used for resident packets. The host writes IMR0 data and
IMR1 requests, and reads OMR0 data and OMR1 replies. The existing loader still uses
its normal upload/audit mechanism before resident entry.

## Host ABI

`0xc6204d05`: eight little-endian u32 header words plus 1,536 payload bytes.
Input words are operation (1 send, 2 receive), epoch, input length, then five zeros.
Send accepts one raw IP packet of 20–1,500 bytes; receive requires input length 0.
Output words include returned length, firmware sequence (always 1), outbound
completion register, pending flag and uncertainty flag. Receive data is a sequence
of length-prefixed raw IP packets. Readbacks are copied before TX ownership is
released. No implicit retransmission is made on an uncertain device operation.

MU request high nibbles A/B/C are RX begin/word/commit, D/E/F are TX length/word/
release. Bits 16–27 encode word index; bits 0–15 hold the session epoch. Reply sets
bit 27 and requires IMR1 to have been consumed. Data words are little-endian.
The target requires ordered RX words and complete commit, bounds TX reads and
rejects networking outside running state. The host mutex serializes packets and
STOP/snapshot operations. A packet transaction has a five-second deadline;
timeout or inconsistent hardware state poisons the session and retains resources.
The v2 first capture predates the whole-transaction deadline; its per-word bound
and retained-close behavior are preserved in the artifact source.

## RAM contract

The linker and `ram_audit.py` enforce code below `c0f4c000`, mutable state within
`c0f4c010..c0f9bff0`, and both existing guards. All task/IRQ stacks, RTEMS workspace,
lwIP heap/pools and packet buffers stay in that grant. `ram_owned()` rejects empty,
overflowing and out-of-range requests. `ram_reclaim()` always denies new regions.
This is intentional: observed idle DMA and a cache completion flag cannot grant
ownership of firmware queues, outstanding SCSI transactions or arbitrary DRAM.

The first resident image used 229,056 bytes of BSS and left 98,160 bytes before
the upper guard. More application state can fit in the existing allocation;
expansion beyond it is still gated on cache/engine and firmware-range ownership.

## Cache investigation

`audit.py` checks 73,608 disassembly rows against the exact matching dumped and
Fujitsu firmware bytes. In routine `c004e940`, it identifies eight descriptor/result
words at `40800020..4080003c`, command submission at `4080001c`, a 16-bit bit-0
completion wait at `40800008`, then acknowledgement with 1. The DMA-assisted path
at `c004ea80` first waits for DMA0 status bit 10 to clear, saves the mask at
`4080000a`, installs mask 1, coordinates firmware event bit 6 and restores the
mask. This is a per-operation sequence, not a global idle/drain API.

A separate bit-5 wait belongs to the board timer sequence. Do not confuse it
with the bit-0 operation completion. Error handling also reads status and mask;
zero status is ambiguous after acknowledgement.

The first resident snapshots read status `0008`, mask `4080`, configuration
`40800000`. These resemble address/bus data and **are not accepted as valid cache
engine status**. `cache_probe.h` performs register-indirect reads after two distinct
RAM seed loads. A second probe temporarily disables the CPU D-cache and restores
its prior enabled state (status `0x7221`). Observe, DMA-disable and bus-isolate
sessions all returned the same address-like values even with CPU caching off.
These probes run in the ARM report and the final STATUS report after controls
are restored, not inside the isolated interval; the resident snapshots separately
record the normal-cache reads while isolation is active.
NMISR stayed zero and ATUCR was `0x26` (direct-address mode clear). This rules out
CPU D-cache state alone as the explanation, but does not establish an idle cache
engine. The probe never writes a board-cache command, mask or ACK.
Board decode, actual register identity, completion liveness and whole-engine drain
must be established before reclaiming RAM. No claimed MYL-86138 disable sequence
is implemented.

Primary context: [Mylex DAC960PG installation guide, cache subsystem](https://mylex.manymanuals.com/disk-arrays/dac960pg/installation-guide-36627/26)
identifies the MYL-86138 as its cache controller. The
[Intel Rx manual](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF)
§16.3.6 says bus-master disable prevents outbound ATU claiming, and §16.3.6.2
makes low-address decode depend on ATUCR direct-address mode. Neither document
establishes the board-specific completion contract. Historical captured ATUCR was
`0x26`; fresh probe records it rather than assuming that value.

## Reproduce

```sh
python3 rtems/residentnet/test_native.py
python3 rtems/residentnet/test_host.py
python3 rtems/residentnet/audit.py --out /tmp/cache-audit
# Remote work root, with the existing hash-pinned sources and cross compiler:
python3 project/rtems/build.py --work . --profile residentnet
python3 project/rtems/residentnet/build_transport.py --out residentnet-module --payload residentnet/kernel.bin
make -C /lib/modules/$(uname -r)/build M=$PWD/residentnet-module CC=gcc-12
sudo python3 project/rtems/exclusive/live.py --payload residentnet/kernel.bin --module residentnet-module/dac960auto.ko --output fresh-bounded --phase 2 --ticks 100
sudo python3 project/rtems/residentnet/live.py --payload residentnet/kernel.bin --module residentnet-module/dac960auto.ko --output fresh-resident
# After collecting evidence, reboot. A power cycle may still be necessary.
```

Do not run while another experiment or production service owns the card. Every
output directory must be new. Preserve captures before reboot. Offline replay:
`verify.py --root EXTRACTED EXTRACTED/residentnet-live1`; `ram_audit.py EXTRACTED/residentnet`.

See [batch ledger](BATCH.md) and [artifacts](../../artifacts/notes/rtems-residentnet-20261011.md)
for exact completed and pending tests.

Final build: three uncached-probe phases restored/unloaded, and a third resident
network run passed STOP at 846 ticks. The production IPv6 Darth Vader page was
restored after the final reboot and verified from the Mac. Final mutable tail
space is 98,144 bytes. Artifact recovery verification is in `verify_production.py`.

## Allocation follow-up

The [RAM ownership batch](RAM-OWNERSHIP.md) supersedes the 32-slot queue limit
with 64 slots inside the same grant, adds board admission and RNT2 queue telemetry,
and documents fixed allocation/SCSI diagnostic pages. Physical RAM outside the
upload remains unavailable.

See [SCSI stop and RAM boundary](SCSI-STOP.md) for the opt-in held-reset build,
72-slot queue, card evidence and outstanding NMI/fault ownership gate.

The newer [exclusive exception/RAM contract](FAULT-OWNERSHIP.md) covers real
fault/NMI containment and the opt-in fixed external packet-buffer grant.
