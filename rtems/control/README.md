# Independent control protocol prototype — P1

**Subsequent live result:** [bounded MU echo and restoration passed](MU-ECHO.md).
The read-only investigation/prototype statements below describe the earlier checkpoint.
Independent STOP and permanent coexistence remain unproven.

Status: native shared-memory host/target demonstration and cross-compiled i960
protocol core; **no live independent MMIO channel is enabled**. Existing stock
firmware commands are not used by the prototype. Hardware binding awaits an
owned RAM/register reservation and visibility/interrupt proof.

The [interrupt audit](INTERRUPT-AUDIT.md) covers P0. This directory is separate
from the working network/IRQ profiles and does not change their entry/exit code.

## Hardware discovery and why there is no write backend yet

Read-only PCI configuration on the live DAC960PG returned:

| Register | Value | Implication |
|---|---|---|
| PIABAR (config 10h) | EE000008 | BAR base EE000000, prefetchable flag set |
| PIALR (40h) | FFFFE000 | Existing 8 KiB aperture; no enlargement performed |
| PIATVR (44h) | C0000000 | Inbound RAM translation base |
| ATUCR (88h) | 00000026 | Recorded without changing translation/control |

MU overlay occupies BAR offsets 0000–004F. Offsets 0050–0FFF are index locations
backed by translated local RAM; writes also set the MU index interrupt status
and latch the index address. This is not a side-effect-free scratch page.
BAR offset 1000 is the existing stock command mailbox; status is at 1018/101A.
The earlier PRCB observation also points the interrupt stack at C0001000.
These uses rule out selecting an address based only on an idle-looking snapshot.

Candidate paths, in order of required proof:

- An explicitly reserved translated RAM slot: preferred for a 128-byte polled
  protocol, but needs a firmware ownership/lifetime audit and correct treatment
  of index-write interrupt effects if it is inside 0050–0FFF.
- Inbound/outbound message registers: only two words each and writes trigger
  interrupt status. Need a fragmented handshake plus proven register/status/mask
  ownership. They are not treated as spare because their last values look idle.
- MU hardware queues: reading queue ports dequeues; enabling/reconfiguring them
  requires owned local memory and firmware coordination. Not a read-only probe.
- APIC registers: interlocks can retry/deadlock bus accesses; excluded entirely.
- Doorbells: existing firmware transport owns them, including special NMI
  behavior. No exploratory bit writes.

`inspect_config.py` reads only four documented configuration dwords, validates
DAC960PG IDs and offers no write option. It does not read BARs, queue ports,
APIC registers, timers or reserved registers. See Intel manual chapters 16–17.
A live adapter must use driver-mediated readl/writel or equivalent defined-width
access and locking, not Python mmap writes into the running driver's resource.

## Protocol and implementation

`control.c/.h` is the target-independent C core. `protocol.py` is host framing.
The native demo runs a separate target process over a 128-byte shared mapping;
its barrier shim is a native C11 implementation, **not a PCI/i960 cache barrier**.

Two single-writer 64-byte slots; little-endian 32-bit words:

| Word | Host request | Target response |
|---|---|---|
| 0 | Commit sequence (zero while unpublished) | Acknowledged sequence, published last |
| 1–3 | Magic CTL1, version 1, nonzero epoch | Same, with target's current epoch |
| 4 | STATUS=0, PING=1, STOP=2 | Status code |
| 5 | PING argument | PING echo |
| 6 | FNV-1a checksum of words 0–5 | Stopped flag |
| 7 | Reserved zero | Heartbeat counter |
| 8 | Reserved zero | Checksum of words 0–7 |
| Remaining | Reserved zero | Reserved zero |

Host initializes request/response storage under exclusive ownership before
starting the target. It publishes one request and waits for its response before
changing the request again. Each side clears its commit word, orders body writes,
then publishes the nonzero sequence. Readers order and sample commit around their
snapshot; checksums detect corruption, not malicious forgery. A hardware adapter
must implement cache maintenance, release/acquire and posted-write completion as
needed. `volatile` alone does not supply those guarantees.

The target owns a nonzero session epoch and increments no host sequence itself.
A new session requires a new epoch and an ownership handshake; deterministic 123
in the demo is only a fixture. Sequence wrap is refused until a new session.
Duplicates do not execute twice. Bad framing/epoch/sequence do not consume the
expected sequence. Valid requests with unsupported/failed operations do consume
it. Do not automatically retry uncertain mutating requests; query acknowledged
state first. Tick/poll are serialized by the monitor, not called concurrently.

STOP calls a required bounded quiesce hook. Only its success sets `stopped` and
permits a successful acknowledgement. A failed hook returns NOT_QUIESCENT and
keeps ownership. Repeated STOP is harmless; PING is rejected after STOP; STATUS
remains readable. The prototype hook stops only simulated work. A hardware hook
must stop scheduling and DMA, prove the monitor's handler/stack lifetime, and
coordinate timer/interrupt teardown before allowing the host to release RAM.
No generic checksum or STOP flag proves those hardware conditions.

## Reproduce

```sh
python3 rtems/control/test_control.py
python3 rtems/control/demo.py
# Explicit read-only inventory on the Linux host:
sudo python3 rtems/control/inspect_config.py
# Cross-compile only; this does not create/install a runnable board payload:
i960-coff-gcc -mrp -O2 -ffreestanding -fno-builtin -c rtems/control/control.c -o control.o
```

Tests cover PING/heartbeat, STOP success/failure/idempotence, stale epochs,
out-of-order/wrapped sequences, corrupted and torn publication, unsupported
operations, host response validation and 10,000 deterministic malformed frames.
The separate-process demo proves host/target exchanges without firmware calls
in simulation. Artifacts preserve i960 object/disassembly, config inventory and
native results. It is not a live proof that STOP reaches a CPU-bound card task.

Next: determine an owned host-visible slot from firmware references/lifetime,
or an explicit takeover reservation; specify its interrupt mask/status protocol.
Then implement a bounded driver/target visibility experiment that saves/restores
exactly the borrowed state. Until this is proven, P1's physical control gate and
live unrestricted preemption remain open. The existing Vader service stays active.

## Control ownership follow-up (2026-10-11)

The [matching-firmware ownership trace](OWNERSHIP.md) identifies active handler/fault
data and mailbox/interrupt-stack uses in the BAR window. No RAM slot is reserved.
Three read-only MU samples found IMR1/OMR1 zero with message interrupts masked.
These are selected for a separate, driver-serialized bounded echo experiment;
no live sideband writes have occurred. Use the pinned 4.07-0-29 evidence, not the
older 4.07-0-39 `remote-analysis` reference.
