# Preemptive RTEMS and DMA networking plan

2026-10-11. Requested order: unrestricted task preemption, Mylex ↔ host RAM ↔
NIC, then direct Mylex ↔ NIC experiments. Direct-path documentation research
starts now. This plan refines A1–A3 in DEVELOPMENT-PLAN.md; it does not claim
those implementation gates have passed.

## Starting point and the central dependency

Timer 1 already drives bounded RTEMS work between host requests. This is not
arbitrary-instruction task preemption: the network tasks use interrupt level
31, and the timer handler resumes an RTEMS context that must yield back. The
current `_CPU_Context_switch` is a call-boundary context switch, not by itself
an asynchronous full-machine-state save. The build rewrites historical CPU
interrupt macros to level 31. Simply removing that rewrite is insufficient.

Stock firmware still services the commands used to load, poll and stop RTEMS.
Letting a task run indefinitely inside that callback or IRQ can prevent the
very STOP needed to recover it. Therefore the preemption phase must first prove
an independent control path and RAM ownership, even though bulk DMA networking
comes later. These prerequisites are part of the preemption phase, not a reason
to prematurely take over the NIC.

“Unrestricted” here means ordinary application loops need not yield to the host.
It does not mean protection against privileged code that masks every interrupt,
corrupts the kernel or writes arbitrary hardware registers. There is no new
memory isolation or protection boundary in this plan.

## P — Preemption and autonomous ownership

| Step | Implementation / investigation | Acceptance gate |
|---|---|---|
| P0: interrupt/ABI audit | Trace hardware interrupt entry/return, PC/AC/TC state, all globals, local register windows, PFP/SP, `flushreg`, stack alignment, dispatch-disable and ISR nesting. Audit `context.S`, timer ISR, build-time CPU patches and fatal exits. Produce an explicit saved-frame layout and ownership/state diagram. | Reviewed frame/return model with every preserved field accounted for; no reliance on the historical shared ISR save area. |
| P1: independent control | Identify a documented host-visible MU/ATU/mailbox path without modifying live mappings. Build a bounded polled control prototype, separate from stock 20/21/6F command completion. Define epoch, sequence, heartbeat, STOP, status and timeout semantics. | Bidirectional control survives RTEMS activity; STOP does not require an application task to yield or a firmware callback to finish. |
| P2: ownership/handoff | Establish an owned RAM region via the existing memory-extension gates; inventory firmware DMA, SCSI, interrupt and watchdog users. Transfer ownership to a resident monitor through an acknowledged state change. Reserve control/interrupt stacks and buffers. | No guessed “free RAM”; explicit takeover acknowledgement, valid resource lifetime and an agreed stop/reset route. Stock return must be proven separately. |
| P3: actual preemption | Build a separate resident profile. Application threads run below timer priority; ISR only accounts time and requests dispatch, with scheduling at a defined exit boundary. Preserve original interrupt frames across task switches. Implement correct interrupt-mask primitives and bounded critical sections. | A never-yielding arithmetic task is interrupted by a timed higher-priority task; two equal-priority loops time-slice; register/condition-code sentinels and deep call chains remain correct. |
| P4: concurrency | Validate nested IRQ entry where enabled, pending interrupts during critical sections, semaphore handoff, priority inversion behavior, guarded stacks and fault records. Keep lwIP in one network task: current `NO_SYS=1` raw API is not made reentrant by preemption. ISR queues work; it does not call arbitrary application/network code. | No duplicated/lost dispatch or corrupted windows/stacks under timer/control load; measured tick drift and worst-case wake latency. |
| P5: sustained operation | Exercise HTTP/IPv6 and console while a CPU-bound task runs. Stop/disconnect/reconnect under load, then a one-hour soak. | Control remains responsive; no unexplained clock loss or buffer corruption; clean shutdown or explicit retained ownership after uncertainty. Save binaries, traces and checksums. |

Start with offline P0 and a bounded P1 proof. Recovery testing remains deferred
under the existing user direction. Do not turn that into a blanket ban on offline
work, but do not represent a spare card as proof that exclusive takeover can be
undone. Before live P2/P3, resolve the existing takeover/recovery-risk gate in
DEVELOPMENT-PLAN.md with concrete results. No flash change is planned.

## H — Mylex ↔ host RAM ↔ NIC

First version:

    RTEMS/lwIP ↔ Mylex DMA ↔ pinned host queues ↔ Linux netdev/IP routing ↔ tg3 ↔ NIC

This replaces per-packet firmware command exchange. It does not initially promise
zero CPU copies or direct sharing of the NIC's descriptor rings. Linux keeps the
existing NIC, SSH and routing. The current TUN relay remains the reference path.

| Step | Work | Acceptance gate |
|---|---|---|
| H0: DMA ownership | Audit RP primary-bus DMA channels 0/1 and stock users; select a channel only with an ownership protocol. An idle snapshot is insufficient. Establish PCI address width, translation and cache requirements from the manual and live configuration. | Written address map and channel owner; no changing active ATU windows or commandeering firmware DMA. |
| H1: bounded memory transfer | Linux allocates/maps a small guarded DMA buffer for the Mylex, initially constrained to a verified addressable range. Exchange returned DMA address through P1. Copy patterns host→card and card→host with bounded descriptors, completion and timeout. | Exact bytes/guards for both directions, alignment/boundary cases and stale descriptors; demonstrate quiescence before unmapping. |
| H2: packet queues | Two single-producer/single-consumer rings, initially 16 slots × 2 KiB each direction, plus descriptors/control. This is proposed host allocation, not extra unowned card RAM. Use bounded card staging slots. Little-endian ABI, length ≤1500, slot IDs rather than arbitrary guest pointers, monotonic producer/consumer counters, epoch and credits. Reserve control capacity. | Queue wrap, full/empty, duplicate/stale epochs, backpressure and partial completion tests pass. Publish descriptor only after payload visibility; completion only after DMA ends. |
| H3: Linux network integration | First adapt the TUN pump to ring batches for comparison, then expose a dedicated point-to-point netdev with NAPI/completion batching. Route IPv4/IPv6 through the existing NIC driver; preserve HTTP publication and visitor accounting or replace its observation hook explicitly. | Ping, UDP/TCP echoes, HTTP, IPv6 Internet fetch, loss/reordering tests and multi-client traffic match baseline; no dependency on per-packet 20/21/6F calls. |
| H4: lifetime/failure handling | Stop production, acknowledge card quiescence, drain/abort DMA, then revoke mappings. Handle process death, service restart, link loss and epoch changes. Kernel owns mapping lifetime; a userspace exit cannot free memory still reachable by DMA. | SIGTERM/SIGKILL and simulated timeout tests; retain mappings on uncertain hardware state. No force-unpin after timeout. |
| H5: optimization | Measure packets/s, throughput, host CPU, latency percentiles, interrupt rate, copies/packet and i960 load against current relay. Optimize batching first; investigate shared pages only after evidence identifies copy cost. | One-hour soak and recorded comparison; no invented speed target or claimed zero-copy without measurement. |

DMA addresses belong to a device mapping. Never give the NIC a Mylex DMA address
and assume it means the same memory. H3 can use separate buffers and the normal
Linux network stack. A later shared-page design needs supported mappings for both
devices, cache/ownership transitions and NIC completion tracking before reuse.
Even coherent memory requires ordering barriers. Start with completion polling;
add interrupts only after the notification ownership and ISR paths are proven.

## D — Direct Mylex ↔ NIC research

Research status: started, not a supported transfer path. See
[hardware/source findings](artifacts/dma-research-20261011/README.md).

Two separate mechanisms must be evaluated:

1. Mylex writes NIC MMIO/doorbells and maintains NIC rings. Packet DMA may still
   go through host RAM: this alone is not a direct packet-data path.
2. NIC DMA reads/writes a PCI aperture backed by owned Mylex RAM (or another
   documented peer-memory window). This could avoid host packet RAM, but requires
   routing, aperture and both-driver support. The current 8 KiB Mylex BAR does not
   establish such an aperture; NIC BAR registers are not a generic packet FIFO.

| Step | Research / experiment | Gate |
|---|---|---|
| D0: topology/source audit | Record bridge paths, BAR types/sizes, driver, IOMMU groups; inspect pinned Linux P2PDMA and tg3 source and Intel RP manual. | Completed initial inventory below; distinguish observations from hypotheses. |
| D1: routing proof on paper | Identify chipset rules for conventional PCI↔PCIe peer requests, ACS/bridge windows and IOMMU behavior for both directions. Audit exact distribution kernel support, not only upstream. | Positive documented routing support or a bounded sacrificial-device experiment design; no inference from successful host-memory DMA. |
| D2: peer memory / NIC ownership | Determine whether an owned card RAM window can be exposed without breaking firmware. Obtain usable NIC programming documentation; establish a dedicated NIC or supported isolated queue with separate management access. | No competing Linux/i960 writers to the same rings; no use of live SSH NIC as a scratch register target. |
| D3: bounded P2P proof | On a dedicated test device/window, one small transfer each way with guard/checksum and error capture, then descriptor/doorbell ordering tests. | No master abort, timeout, corruption or topology workaround assumed safe. |
| D4: driver prototype | RTEMS Ethernet driver, MAC/PHY setup, RX/TX rings, interrupts, link changes and lwIP Ethernet/ND integration. Host-assisted bootstrap is acceptable if described. | ARP/IPv6 ND and LAN ping before routed Internet tests; sustained traffic and teardown before public service. |

A dedicated conventional PCI NIC behind the same bridge as the Mylex is the
preferred topology to investigate if another NIC is available; this is a design
preference, not a verified compatible model recommendation. The current same-bus
37:05.0 device is FireWire, not a spare Ethernet controller. Do not use it as an
unowned DMA target.

## Immediate next implementation

P0 audit and the transport-neutral P1 prototype are now recorded below. Next,
trace ownership of the translated C0000000–C0001FFF window and MU interrupt
status/masks before choosing a live control slot. Keep the running Vader web
service on the proven bounded profile until the physical control gate passes.
H0 and D1 documentation can progress in parallel in the schedule; this does not
authorize simultaneous hardware ownership experiments.

## P0/P1 audit and prototype checkpoint (2026-10-11)

The [interrupt audit](rtems/control/INTERRUPT-AUDIT.md) is written. The
[control protocol prototype](rtems/control/README.md) passes native tests
and a two-process shared-memory demo, and cross-compiles for i960. Read-only
PCI configuration confirms PIATVR=C0000000 and the existing 8 KiB window.
No live independent control writes are enabled: the MU overlay/index interrupt
side effects and stock mailbox/stack ownership still require a proven reservation.
This completes the offline prototype, not P1 physical validation or preemption.

## Control ownership follow-up (2026-10-11)

The [matching-firmware ownership trace](rtems/control/OWNERSHIP.md) identifies active handler/fault
data and mailbox/interrupt-stack uses in the BAR window. No RAM slot is reserved.
Three read-only MU samples found IMR1/OMR1 zero with message interrupts masked.
These are selected for a separate, driver-serialized bounded echo experiment;
no live sideband writes have occurred. Use the pinned 4.07-0-29 evidence, not the
older 4.07-0-39 `remote-analysis` reference.
