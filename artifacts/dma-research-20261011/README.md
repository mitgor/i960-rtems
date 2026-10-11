# DMA networking: initial read-only research

2026-10-11. No MMIO reads/writes, DMA submission, driver unbind, NIC reset or
firmware change was performed. PCI configuration/sysfs inventory and source
inspection only; `i960-http6` remained active. `topology.txt` preserves the
inventory. Full execution roadmap: [preemption/DMA plan](../../RTEMS-PREEMPTION-DMA-PLAN.md).

## Observed hardware

| Item | Finding |
|---|---|
| Host kernel | Ubuntu 6.8.0-138-generic |
| Host bridge | Intel 8086:3405, 5520/5500/X58 |
| Mylex | 37:09.1, DAC960PG 1069:0010, behind conventional PCI bridge 00:1e.0 |
| Mylex BAR0 | 0xee000000, 8 KiB, prefetchable; this does not prove arbitrary card RAM is exposed |
| Current NIC | 01:00.0, Broadcom BCM5764M 14e4:1684; driver tg3; PCIe branch 00:1c.5 |
| NIC BAR0 | 0xec000000, 64 KiB, non-prefetchable MMIO |
| IOMMU groups | NIC 12, Mylex 14; group numbers alone prove neither peer routing nor usable shared DMA addresses |
| Other device on bus 37 | 37:05.0 LSI FireWire controller, not a second NIC |

The NIC carries host network access. No spare isolated NIC/queue was established.
The topology is not the simple same-bridge peer case. This is a reason to require
routing evidence, not proof that the chipset physically cannot route requests.

## Source findings

Linux's P2PDMA documentation explains the hierarchy/host-bridge restrictions and
provider/client/orchestrator responsibilities. Generic DMA-capable endpoints do
not automatically form a supported peer path. See [P2PDMA documentation](https://www.kernel.org/doc/html/latest/driver-api/pci/p2pdma.html).

In [upstream Linux v6.8 p2pdma.c](https://github.com/torvalds/linux/blob/v6.8/drivers/pci/p2pdma.c#L425),
this host's Intel 3405 ID is absent from the explicit host-bridge whitelist.
This is an upstream-source observation; the Ubuntu build's exact patched source
and runtime compatibility result have not yet been checked. Do not infer that
changing a whitelist creates hardware support. D1 remains open.

The [upstream v6.8 tg3 driver](https://github.com/torvalds/linux/blob/v6.8/drivers/net/ethernet/broadcom/tg3.c)
contains the 5764 device entry. It uses NIC-device DMA mappings for packet buffers
and coherent allocations for descriptor/status rings. Source inspection found no
`p2pdma` reference in this file. This does not establish a supported P2P networking
API or prove every generic networking path excludes P2P pages. The existing NIC
rings remain Linux-owned. Relevant functions include `tg3_start_xmit`, and RX/TX
ring allocation around lines 8581–8847. `source-hashes.txt` records the retrieved
v6.8 files; the links pin a release rather than moving master.

The [Linux DMA guide](https://www.kernel.org/doc/html/latest/core-api/dma-api-howto.html)
distinguishes CPU, physical/bus and device DMA addresses. Allocation/mapping,
mask limits, cache synchronization and memory ordering must be specified in the
host-RAM design. No cross-device address identity is assumed.

Intel's [i960 Rx Developer's Manual, 272736-002](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF),
chapter 20, describes three DMA channels: two for the primary PCI bus and one for
the secondary bus. It distinguishes PCI address/upper address and local address
registers. This supports investigating card↔host RAM transfers through the
primary channels. It does not establish a spare channel under stock firmware,
that all addresses are reachable in the current configuration, or that peer
NIC MMIO is an appropriate transfer destination. Earlier idle DMA snapshots
are observational evidence only.

## Conclusions and unresolved work

- Best first implementation remains host-memory queues, retaining Linux NIC
  ownership and allowing a copied network path before optimizing shared buffers.
- Direct P2P needs independent proofs of route, memory aperture, NIC ownership,
  address translation/cache ordering and teardown. None is currently complete.
- NIC doorbell writes alone do not bypass host packet memory. Direct NIC DMA into
  Mylex-owned memory requires a suitable exposed aperture; the current BAR size
  is not such proof.
- Next research: exact chipset peer-routing documentation, distribution P2PDMA
  source/configuration, RP ATU/MU ownership, supported NIC queue isolation or a
  dedicated same-bus NIC. Do not probe unknown device register space to fill a
  documentation gap.
