# Plan: RTEMS on i960, TCP/IP through the Linux host

Original plan: 2026-10-10. Updated status: 2026-10-11.

**A cooperative RTEMS port and card TCP/IP now work:** see [implementation](rtems/README.md) and [hardware evidence](artifacts/rtems-20261011/README.md). R1 produced RTEMS 4.6.6 with the existing i960 ELF tools. Classic tasks, context switches, semaphores, message queues and software ticks passed live tests. Persistent task state and lwIP 2.1.3 now carry ICMP, UDP, TCP, DNS and HTTP through host TUN/NAT.

The architecture below describes the still-unimplemented **autonomous takeover** path. It is no longer a prerequisite for using RTEMS: the implemented alternative deliberately returns to firmware on every host callback, keeps interrupts masked within RTEMS, and advances time from host polling. It does not satisfy the original exclusive-ownership/preemptive-clock gates. Networking uses TUN/raw IPv4 instead of TAP/Ethernet. Recovery remains untested.
Build on [TETRIS-ON-CARD-PLAN.md](TETRIS-ON-CARD-PLAN.md), especially proven console
transport, memory bounds and reproducible target builds.

## Architectural decision

RTEMS will own the card CPU, its scheduling and interrupts during a session.
It cannot simply run forever inside the current returning firmware callback:
the host would time out, and stock firmware commands would stop being serviced.
The current 64 KiB loader is a bootstrap mechanism, not an RTEMS memory budget.
The reported 16 MiB DRAM is not automatically all free while firmware is running.

Aim for RAM-only boot after normal PC startup. Preserve vendor DRAM/PCI startup,
then deliberately quiesce the RAID firmware and transfer ownership to a resident
RAM monitor/RTEMS image. Assume reboot or power cycle is needed to regain stock
firmware until a return path is separately proven. Recovery testing remains
excluded as previously requested; this plan does not claim remote recovery.

For networking, run TCP/IP **on the card**. The Linux host relays complete packets
and routes/NATs them through its physical network interface. A host socket proxy
would not prove an RTEMS TCP/IP stack.

```text
RTEMS application -> card TCP/IP -> virtual Ethernet driver
                                        |
                              framed PCI transport
                                        |
Linux relay <-> TAP interface <-> Linux routing/NAT <-> LAN/Internet
```

TAP carries Ethernet frames; TUN carries IP packets. Prefer TAP for compatibility
with ordinary Ethernet network drivers, with a private routed subnet rather than
bridging the card onto the LAN. A point-to-point TUN transport is an alternative
if the selected stack's driver interface makes it materially simpler.
[Linux TUN/TAP documentation](https://docs.kernel.org/networking/tuntap.html).

## R1 — Pin a buildable RTEMS/CPU/toolchain combination

The official historical architecture table lists i960 support in RTEMS 4.6 and
its absence in 4.7 and later releases shown there. Start archaeology with the
4.6 release line; choose the exact patch release only after checking its sources.
[RTEMS development roadmap](https://www.rtems.com/sites/default/files/EWiLi-RTEMS-JoelSherrill-2013.pdf).
The archived tool instructions explicitly mention `i960-rtems`.
[RTEMS 4.6.1 tool documentation](https://docs.rtems.org/docs/4.6.1/html/started/started00050.html).

Obtain and hash official kernel, historical i960 CPU port/BSPs, Newlib and tool
sources. Inspect support for the RP's interrupt model, register windows, fault
handling and little-endian ABI; an i960-family port is not proof of RP support.
Check calling convention, context assembly, libgcc helpers and object format
against our actual GCC 3.3.6/binutils 2.27 ELF pipeline. The existing `i960-coff-`
naming workaround does not supply an RTEMS C library or target configuration.
Build a minimal kernel/application offline in a reproducible environment.

**Exit:** a linked, inspected RTEMS hello image and map, a documented compiler/
Newlib combination, image/RAM-size budget and explicit CPU-port gaps. No live
handoff before this gate. If historical support cannot be adapted, document the
scope of restoring i960 in a maintained RTEMS release as a separate porting
project; do not pretend that a BSP alone adds a missing CPU architecture.

## R2 — Independent host/card transport and RAM monitor

Before stopping firmware, establish communication that does not depend on its
opcodes 20/21/6F. Start with polled message registers/doorbells and bounded chunks.
Audit exact host/local register offsets and ownership; the 8 KiB BAR is not a
mapping of arbitrary DRAM. Any new ATU translation/window requires explicit
register analysis and a test that PCI enumeration and host access survive.

Design a versioned framed protocol with channels for control, console and
packets; lengths, sequences, ownership, credit/backpressure and checksums.
Start with tiny synchronous messages and no host-memory DMA. Add bulk windows or
DMA later only if measured throughput requires them, with proper Linux DMA
mapping/IOMMU lifetime and cache rules. Multiplexing must keep control traffic
available when console/network queues fill.

A small monitor must fit within the proven upload allocation, use an explicit
stack and preserve its own code/transport buffers. Audit DMA engines, SCSI
activity, interrupt sources and watchdogs; stop activity before claiming RAM.
Design launch as an acknowledged ownership transition with a new ready marker,
not a normal firmware command left pending. This needs a dedicated host module
state machine, not disabling the existing timeout check.

**Exit:** monitor heartbeat, bidirectional console/loopback and disconnect
behavior after firmware handoff; no unexplained DMA or interrupt activity. Keep
all host resources mapped until the device is known quiescent or reset. Capture
each boundary. Stock firmware restoration after takeover is not assumed.

## R3 — RAM image loading and DAC960PG BSP

After ownership transfer, the monitor can receive the larger RTEMS image into a
surveyed region outside itself. Define code/data/BSS, heap, stacks, vectors,
monitor and transport reservations; test RAM without overwriting still-live
boot/monitor state. Reject overlapping or out-of-range ELF segments and verify
the complete load before entry. Do not grow the current 64 KiB allowlist into
unowned firmware memory to make an image fit.

Create a DAC960PG BSP preserving established DRAM setup and necessary PCI state.
Provide startup, BSS clearing, ABI/g14 initialization, interrupt/fault tables,
console, idle and fatal-error paths. Implement a real timer/clock driver and
verify its rate rather than assuming a clock frequency. Check register-window
save/restore and separate interrupt stack behavior under nesting/context switches.

**Exit, in order:** polled RTEMS boot banner; one task; two tasks switching and
preserving registers; measured periodic tick; timed sleeps; semaphore/message
queue tests; bounded heap/stack tests; at least 30 minutes of scheduler stress.
Record fatal reasons over console. A hello banner alone does not prove a port.

## R4 — Select and integrate the network stack

For the initial historical kernel, evaluate its matching legacy BSD stack first
for API/toolchain compatibility. In parallel on paper/source, assess a small lwIP
port with an RTEMS OS adaptation (`sys_arch`: threads, semaphores, mailboxes,
timeouts and protection). Select based on a successful compile, RAM footprint
and driver integration, not the existence of a modern package name.

Current RTEMS documentation offers lwIP and LibBSD integrations, but neither is
evidence of drop-in support for a 4.6 i960 kernel. Prefer lwIP for a later
maintainable small-stack route if its C/compiler and OS adaptation are feasible;
keep LibBSD outside the first milestone due to its modern kernel/toolchain
integration requirements. Pin the chosen source and record required patches.
[RTEMS packages](https://docs.rtems.org/docs/main/user/package/index.html),
[lwIP integration](https://docs.rtems.org/docs/main/user/package/lwip/index.html),
[LibBSD integration](https://docs.rtems.org/docs/main/user/package/libbsd/index.html).

Implement a virtual NIC over R2, with bounded MTU, packet queues, explicit drops,
link up/down and error counters. Start with software checksums and polled/batched
transport servicing from a task; do not allocate or block in an ISR. Validate
short/oversized frames, queue exhaustion, packet ordering, checksums and link
restart. Measure transport bandwidth before choosing TCP buffer sizes.

**Exit:** ARP plus ICMP between host and card, then UDP and a card-side TCP echo
or client test. Verify payload hashes, multi-packet transfer, retransmission and
backpressure. Task/console responsiveness must survive network load.

## R5 — Linux gateway and Internet access

Build a host relay that moves frames between the PCI transport and a dedicated
TAP interface. Configure a collision-free private /30 subnet after inspecting
host routes (example only: host 192.168.240.1, card .2). Set the card's default
route to the host. Use a locally administered MAC and static addressing first.

Use IPv4 forwarding, interface/subnet-scoped firewall rules and source NAT on
the actual uplink when the LAN has no route back to the card. Discover existing
firewall management first; preserve SSH connectivity and existing rules. Provide
idempotent setup and teardown that removes only project-owned changes and
restores settings it changed where safe. No routing/firewall changes are made
by this planning task.

Keep unsolicited inbound connections blocked initially, particularly if using
a historical network stack. Test through a local host service before enabling
outbound Internet traffic. Configure a reachable DNS resolver explicitly; DNS
and routing are separate milestones. HTTPS additionally requires a suitable TLS
library, entropy, clock/certificate policy and RAM budget; it is not implied by
working TCP. Begin with a controlled HTTP/TCP endpoint and known content.

**Exit:** card-to-host TCP; routed access by IP; DNS lookup; outbound TCP/HTTP
fetch with verified content hash; simultaneous console activity; link loss,
reconnect and cleanup tests. Packet captures must show the card originates the
IP/TCP exchange, while the host routes/NATs it. Record performance rather than
promise Ethernet-class throughput from a mailbox transport.

## Dependencies and deliverables

Tetris T1–T4 yields useful game and console infrastructure, but its firmware RPC
transport does not automatically survive RTEMS takeover. R1 can be researched
while Tetris progresses. For hardware: R2 precedes R3, R3 precedes stack execution,
and local R4 networking precedes Internet routing in R5. Keep the existing
working returning loader as an independent baseline throughout.

Proposed new areas: `rtems/` for pinned source/build manifests and BSP patches,
`loader/monitor/` for takeover/loading, `host/cardlink/` for transport and console,
and `host/cardnet/` for relay/gateway tooling. These names are proposed, not
claims that code exists. Store target images, maps, source hashes, logs, captures
and acceptance reports under dated artifact directories; update Claude guidance
and the story as each stage passes.

The first useful RTEMS deliverable is the R1 buildability report. The first useful
Tetris deliverable is T1: a returning payload that sends a bounded text/buffer
response to the host. Neither requires a new flash image.
