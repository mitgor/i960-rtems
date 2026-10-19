See [PACKET-DMA.md](PACKET-DMA.md) for the next owner-polling and opt-in
reply-DMA qualification. Its dated artifact record distinguishes measurements
from pending endurance stages.

## Combined service

Networking, the independent diagnostic console and two bounded applications now
share the running card service. See [COMBINED-SERVICE.md](COMBINED-SERVICE.md) for
commands, ownership boundaries, arbitration, recovery and qualification limits.
The packet transport remains PIO; general concurrent segmented applications and
unrestricted task cancellation remain separate work.

# Accele160 resident applications and network module

This opt-in extension (`ACCELE_RUNTIME=1`, with `ACCELE_SERVICE=1`) integrates
`loader/segmented` with the existing exclusive RTEMS kernel. The normal profile
remains the default. The fixed Doom image and the new module use separate
allocations; the loader accepts requests only after Doom is idle. The host creates the application socket only after its final Doom rearm/guard
and console selftests pass, not merely when the card first reports idle. The
opt-in application service owns that idle lease until global shutdown; browser
restarts are refused and automatic restart cycles are disabled. Use the normal
profile for repeated Doom games. This prevents allocation during final host
rearm checks and preserves their original strict zero-dynamic-allocation gate.

## Memory and ownership

| Consumer | Budget / placement |
|---|---|
| RTEMS workspace | existing `c0730000..c075ffff`, 192 KiB |
| Init stack | existing 64 KiB allocation inside that workspace |
| Worker stacks | existing two 8 KiB allocations inside that workspace |
| Owned IRQ/terminal stacks | existing separate linker reservations |
| Application transport | grant page `c077b000..c077bfff` |
| Runtime reservation | 512 KiB guarded parent allocation in the validated upper arena |
| Module partition | first 384 KiB of that reservation |
| General heap | last 128 KiB, separate guarded arena metadata in the kernel |
| lwIP heap | 48 KiB static heap inside the module, not an extra board allocation |

The seven existing Doom reservations leave `0x9f380` bytes before additional
allocation guards. With their current sizes, the new parent payload starts at
`c0f50c90`, and its first module payload at **`c0f50ca0`**. The loader checks the
actual allocated address against the manifest; this is not permission to write
to an arbitrary host-supplied address. Every newly used byte is inside the
already validated exclusive upper-bank arena. No stock range is reclaimed, and
the reboot-only stock-firmware return rule remains.

The general heap exposes bounded 16-byte aligned allocations and generation
handles, explicit pins, cancellation and release. Cancellation forbids new pins
but cannot free an existing consumer's storage. A failed guard or uncertain
module execution retains the parent. Child generations restart only with a new
service epoch; callers must not carry handles across epochs. The wire currently
exposes a bounded heap proof, not arbitrary pointer access. General malloc/
realloc APIs, arbitrary task creation, shared reference graphs, stack resizing
and larger RTEMS workspace are still separate work.

## Loader and execution ABI

Board ID `01601077`, application ABI 1, segmented format ABI 1. The manifest
uses an explicit 184-byte little-endian wire record (five words per segment,
independent of compiler struct padding), and contains at most eight non-overlapping RX/RW segments, an RX entry, exact linked
base, lengths and per-segment CRC32. The host additionally verifies the module
SHA256. CRC is corruption detection, not authentication: all loaded code is
trusted in a single address space. Absolute i960 binaries have no runtime ELF
relocations or unresolved imports. Text/data/BSS are represented separately.

Begin, ordered chunks (at most 1016 bytes), incremental verify/zero (at most
1024 bytes per operation), initialize, packet/call, close, query and heap-proof
operations are serialized by the existing Init task. Instruction-cache sync
uses the existing kernel's `syncf; icctl 2` admission pattern. Code cannot execute
before all segments verify. BSS is cleared on every fresh load. Timers advance
from RTEMS ticks independently of host packet polling, with catch-up capped at
one second per module invocation. No allocator or lwIP call runs from an ISR.

The entry signature is:

```c
unsigned entry(unsigned op, unsigned elapsed_ms,
               const unsigned char *input, unsigned length,
               unsigned char *output, unsigned capacity);
```

Module operations: 0 initialize, 1 timers, 2 one input packet / bounded output,
3 counters. Output is at most 2048 bytes. Networking uses length-prefixed IP
packets, each at most 1500 bytes. One module owns lwIP (`NO_SYS=1`, raw API).
A module must return: non-cooperative application containment is not established
by this ABI. A fatal lwIP assertion parks the module and requires retained
storage/reset; it must never be treated as successful close.

The single root-only socket `/run/i960-rtems-runtime.sock` delegates all MMIO to
the existing owner thread. It never opens another PCI mapping or submits stock
commands. Epoch/sequence/CRC and bounded request/reply lengths protect the wire.
Timeout after publication quarantines the channel; it sends no subsequent close
or release command. The independent diagnostic console remains separate.

## Build and use

`build_net.py --out DIR --tools CROSS_BIN --newlib NEWLIB_INCLUDE` builds the
IPv4/IPv6/HTTP module and manifest. Add `--hello` for the small text application.
Without `--tools`, it builds a native test library only. The pinned lwIP 2.1.3
archive and existing checksum/alignment patches are reused.

On an accepted runtime bundle, after Doom is idle:

```sh
sudo python3 runtime/client.py upload MODULE_DIR
sudo python3 runtime/client.py query
sudo python3 runtime/client.py stop
```

`runtime/relay.py` creates a bounded TUN relay. Configure its private link with
host `10.196.0.1/30`, `fd96:196:960::1/64`, and MTU 1500. Card addresses are
`10.196.0.2` and `fd96:196:960::2`; HTTP is port 80, UDP echo 9601, TCP echo 9600.
With `--seconds 0` the relay runs until stopped or its owner connection fails;
each RPC remains bounded. Stop it with `systemctl stop i960-rtems-ip`.
The relay does not install NAT, public routes or firewall rules. Its ULA IPv6
address is not globally reachable. HTTP content and TCP state are on the card;
Linux supplies IP transport. Public IPv6 and outbound Internet/DNS are additional
routing/qualification steps.

Native tests: `test.py`, `test_host.py`, and `test_net.py network.so`. The network
harness checks real UDP and TCP HTTP for both families, checksums, card identity
and FIN; the shared stack's existing sanitizer suite adds malformed inputs,
10,000 packet cases and queue backpressure. `test_net.py --rpc` repeats the packet
exchange through the owner channel on the physical card.

See the [evidence batch](../../../artifacts/current/accele160-runtime-port-20261019/README.md)
for the hardware qualification state. Do not infer card success from a native
run or a successful cross-compile.

## Further reclamation and public IPv6

See [loan/cancellation contract](RECLAMATION-CANCELLATION.md) for the idle 6 MiB
zone heap and wire operation 9. Forced non-cooperative task termination remains
unqualified; cancellation revokes access and retains outstanding references.

`build_net.py --ipv6 GLOBAL_ADDRESS` adds a third, global IPv6 address while
keeping both private addresses. Rebuild/reload the module when the ISP prefix
changes. `public_ipv6.py apply --address GLOBAL_ADDRESS` checks the current LAN
prefix, performs duplicate-address detection, installs a host /128 route through
`accele0`, proxy NDP on `enp1s0`, RA-preserving forwarding and a dedicated nftables
table. Forwarded ingress permits card HTTP/80, ICMPv6 and established/related
traffic; echo-test TCP/9600 and UDP/9601 are not public. Local host-to-card tests
remain available. This is routing to card-side lwIP, not a host HTTP proxy.

Run `public_ipv6.py remove` **before stopping the TUN relay** to restore saved
sysctls, route, proxy and table. State is `/run/i960-public-ipv6.json`; setup is
explicit and not persistent across reboot. The script does not alter the router.
An upstream IPv6 firewall may still need an inbound HTTP rule for the dedicated
card address. LAN access alone does not establish Internet reachability.
