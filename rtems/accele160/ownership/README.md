# Accele160 engine-ownership audit (P3i)

The 2026-10-19 observational audit finds **no established permanent SCSI or AAU
exclusion**. It preserves normal profile 5 and the prompt. It grants no RAM and
performs no PCI configuration writes, BAR mappings, new firmware callbacks,
private-bus scans, module unloads or resets.

## Physical evidence

Three captures on boot `bbefd6d3-016a-4c9e-8388-36a164e78fd4` identify bridge
`0000:37:09.0` as `8086:2962` and endpoint `0000:37:09.1` as `1069:0050`.
Bridge BCR is `0x202`: secondary reset is **not asserted**. SACR is `0x1554`:
each external slot's two-bit priority is 1, not the disabled encoding 3.
Bus numbers are primary 0x37, secondary/subordinate 0x38. The endpoint's PCI
bus-master bit remains enabled, as required for current host DMA. This does
not identify which physical slot contains a SCSI device; an arbitration slot
is not evidence of a populated device. Linux's visible topology is insufficient
to identify a firmware-private SCSI device.

The existing service answered `apps`, `mem` and `uptime` between samples;
both services stayed active, frames remained 64, idle stayed 1, and the zone
loan stayed zero. These are new live host/config/console observations, not new
core-engine snapshots. Previously archived profile-5 samples show CCR/NDAR/BCR
zero on all three DMA channels. They omit DAR, CSR and AAU state. Earlier fuller
inventories found a stock DMA1 descriptor `0xc0611320` with DCR `0x3f`; the three
zero fields cannot erase that dependency. Keep DMA1 reserved.

[Raw evidence, replay and provenance](../../../artifacts/current/accele160-engine-audit-20261019/README.md).

## Ownership matrix

| Component | Established | Still required |
| --- | --- | --- |
| CPU fault/NMI and ISP | Profile 5 owned tables/stacks; controlled fault/NMI exception tests | Unknown-source policy and wider interrupt/watchdog audit |
| DMA0 | Finite transfer, drain, suspension, one-shot resume/refusal, retained terminal resources | Permanent exclusion of every stock writer; generic task cancellation is not implied |
| DMA1 | Stock descriptor found in prior full inventory | Stock caller/descriptor lifetime audit; no commandeering |
| DMA2 | Quiet samples | Secondary-master and reset policy, outstanding transaction accounting |
| Secondary SCSI masters | Bridge identity and enabled arbitration observed | Board-specific identity/BAR/topology; stop or held-reset contract |
| Application accelerator (AAU) | 80303 has a separate accelerator | Live register inventory, stock callers/descriptors and completion policy |
| ATU/MU | Existing mappings and prompt transport operate | Preserve host path during isolation; do not disable primary ATU/MU |
| Firmware cache RAM | Explicit allocator grant supports current runtime | Engine exclusion plus dependency/alias/guard proofs before reclamation |

“Cache” has three different meanings here: CPU D-cache coherence, firmware cache
buffer ownership, and the AAU used for memory/XOR operations. Cache invalidation
is not an engine stop or a transfer of allocator ownership.

## Manual constraints and next implementation

Use **Intel 80303 Developer's Manual 273353-001**, not the DAC960PG's 80960Rx
register recipe. Sections 14.15 (BCR table 14-45), 17.6.1–2 (SACR/IACR), and
20.11.1–3 (AAU) establish these boundaries:

- SACR is core `0x104c`, bridge PCI config `0x4c`. IACR is core `0x1600`;
  its independent fields include AAU, BIU, DMA0/1/2, secondary ATU and primary
  ATU/MU. Disabling grants alone does not prove queues drained.
- BCR bit 6 asserts secondary reset. It resets bridge queues, stops secondary
  PCI activity for DMA2, affects secondary ATU configuration, and causes the
  primary bridge interface to retry most transactions. This is not a graceful
  drain and must not be applied by copying the PG sequence blindly.
- AAU ACR is core `0x1800`, ASR `0x1804`, ADAR `0x1808`. Clearing ACR Enable
  suspends transactions with queued data retained; it does not prove completion
  or authorize freeing descriptors. Treat ASR as an owned status source; do not
  add it to a generic observational dump that might consume event evidence.

Next implementation, in order:

1. Add a new opt-in kernel inventory profile, keeping profile 5 unchanged.
   Capture documented non-status DMA registers, IACR, AAU ACR/ADAR/next/count
   after verifying each address/access attribute. Identify firmware SCSI channel
   metadata offline before any private configuration access. Bound the record
   and validate identities before any future writes.
2. Audit stock firmware users of DMA1/AAU and the private SCSI path. Record
   descriptor pools, monitor/interrupt/watchdog dependencies and transactions
   that may outlive CPU takeover. Unknown ownership fails closed.
3. Design a board-specific exclusive isolation transaction: stop new producers,
   prove drain or retain, then isolate known secondary masters. Preserve the
   primary ATU/MU, DMA0 host transport and BIU. Any irreversible transition or
   uncertainty retains allocations and requires reboot; no stock return.
4. Qualify that profile on a fresh boot, then verify host transport, guards,
   bounded failure handling and firmware/reset recovery before restoring prompt.
5. Only then consider more RAM or P4 general resource cancellation. Retain the
   stock-firmware coexistence path and DAC960PG implementation as separate options.

## Reproduction

Run `collect.py` with privilege on the identified host while the existing
service owns the card. It reads only standard 64-byte config headers and the
identified bridge SACR, then calls the existing console. It never creates a
second card owner. Redirect its JSON to a new evidence file, then:

```sh
python3 rtems/accele160/ownership/audit.py CAPTURE.json
python3 rtems/accele160/ownership/test_audit.py
```

The decoder always reports broader ownership as unproved, even for a synthetic
capture with reset asserted and grants disabled. Tests reject changed identity,
boot/order, short reads, inactive services and non-idle/loaned runtime state.
