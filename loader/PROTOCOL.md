# Loader protocol contract

Updated 2026-10-10. The C sources and `mu.h` are authoritative. Host and card use
four 32-bit registers; no doorbell interrupts are required.

| Local address | BAR0 offset | Register | Meaning |
| --- | --- | --- | --- |
| `0x1310` | `0x10` | IMR0 | Host argument |
| `0x1314` | `0x14` | IMR1 | Host commit: `(seq << 16) | opcode` |
| `0x1318` | `0x18` | OMR0 | Card acknowledgment: `(seq << 16) | status` |
| `0x131c` | `0x1c` | OMR1 | READ result; hello execution marker after GO |

## Startup and synchronization

At startup, the card snapshots IMR1's sequence, clears its destination/mode and
OMR1, and publishes READY with that sequence. It discards an old committed input
rather than replaying it after reset. Hosts must wait for READY before first use;
sending commands during startup is outside the protocol contract.

Each CLI process acquires the device lock before accessing the channel. It reads
OMR0 and IMR1 and waits for their high halves to agree. This lets an already
committed command finish before choosing a fresh sequence. Unknown statuses and
HANDOFF reject further commands. A stuck pending command times out without being
overwritten; inspect/reset the card before retrying. The loader cannot infer a
host's intent or roll back a partially executed transaction.

Once synchronized, the host increments the acknowledged 16-bit sequence modulo
65536, writes IMR0, then commits IMR1. It waits for OMR0 with that exact sequence
and checks the status. The card consumes a command only when its sequence differs
from its last consumed sequence. Zero is a valid sequence after wraparound.

Never restart a counter at zero without synchronization. Never retry an
unacknowledged WRITE automatically: it may already have advanced the card's
pointer. After a failure, synchronize and reupload the entire payload from a fresh
SET_ADDR, verifying it again. A late GO remains a hand-off; reset is required.

Timeouts use a two-second monotonic deadline and 50-microsecond polling sleeps.
The host's volatile accesses and write fence preserve its commit order in the
implementation; actual PCI/MMIO ordering remains a hardware bring-up check.

## Commands and validation

| Opcode | Command | Argument and result |
| --- | --- | --- |
| 1 | PING | Ignored argument; OK |
| 2 | SET_ADDR | Aligned payload word address; selects payload write mode |
| 3 | WRITE | Data at selected payload address; pointer advances by 4 |
| 4 | READ | Aligned payload word address; returns value in OMR1 |
| 5 | GO | Aligned payload entry; HANDOFF then calls entry |
| 6 | SET_REG_ADDR | Aligned allowed register address; selects register write mode |
| 7 | REG_WRITE | Data at selected register address; pointer does not advance |
| 8 | REG_READ | Aligned allowed register address; returns value in OMR1 |

Payload word addresses are `0x200..0x3fc`. A WRITE at `0x3fc` succeeds and advances
to `0x400`; another WRITE is rejected before accessing memory. Null, unaligned,
stack-region, flash, DRAM, and wrapping addresses are rejected.

Register addresses are aligned words in `[0x1000, 0x2000)`, excluding
`0x1310..0x131c`. This is a conservative explicit-access policy; addresses inside
it are not all guaranteed to be implemented hardware registers. Normal
SET_ADDR/WRITE/READ cannot access them. Invalid SET_ADDR or SET_REG_ADDR clears the
previous write mode and pointer. WRITE/REG_WRITE require their matching mode.

| Status | Meaning |
| --- | --- |
| `0x600d` READY | Booted and idle; not a command-success result |
| `0x0002` OK | Command completed |
| `0x00ee` BADOP | Unknown opcode |
| `0x00ef` BADADDR | Invalid/unaligned address or exhausted payload range |
| `0x00f0` BADSTATE | Missing or incorrect write mode |
| `0x600e` HANDOFF | GO accepted; loader no longer serves commands |

## Hand-off and verification

The loader clears OMR1 and publishes HANDOFF **before** calling the entry. If the
payload returns, the loader parks permanently. Payloads must preserve OMR0 if the
host is to observe the hand-off acknowledgment reliably. The hello payload writes
`0xBEEF00EE` to OMR1 and spins. A status read can distinguish acknowledged GO from
confirmed hello execution, even if the payload writes its marker immediately.

The sender's upload verification compares every padded word with the original
in-memory upload buffer. GO validates its address, but does not track whether an
entry was uploaded/verified or authenticate executable contents. A caller can
explicitly GO to another allowed word; successful upload verification and the
chosen entry remain caller responsibilities.

## Compatibility and extension

The original hello overwrote OMR0, and the original sender restarted at sequence
1 and ignored error statuses. Do not mix those binaries with this revision.
There is no version-negotiation opcode; matching source builds are required.

DRAM support requires verified base/end and initialization first. Extend both
host/card range policy, linker layout, transfer-size handling, tests, and these
documents together. Do not merely disable validation or allow arbitrary memory.
