# Combined networking, console and bounded applications

The combined module keeps the existing raw lwIP IPv4/IPv6/HTTP service and adds
two bundled applications: a progress counter and an ASCII-uppercase text service.
Both can run while HTTP, UDP and the independent diagnostic worker are active.
Stopping/restarting either application does not unload networking. No additional
RTEMS task, interrupt context or heap allocation is introduced.

This is the first bounded P8 integration, not completion of general concurrent
segmented loading or Doom alongside networking. The hardware owner still holds
the qualified Doom-idle lease. Starting an incompatible module upload while the
combined module is active returns the existing refusal. Arbitrary applications
still require separate segmented allocations/imports and owned task contexts.

## User interface

The installed `~/rtems-console` wrapper uses `service.py`; the prior diagnostic
wrapper is retained as `~/rtems-console.before-combined-20261019`. Commands:

```text
help
net
app list
app start counter
app start echo
app echo hello from the host
app stop counter
app start counter
mem
tasks
quit
```

`quit` disconnects only the client. All MMIO remains with the existing PCI owner;
the wrapper uses the two root-only local sockets over SSH. Network clients cannot
start/stop applications: the private application envelope begins with invalid
IP version 15, whereas packets received from the TUN are IP datagrams.

## Execution and wire contract

The two applications are bounded callbacks inside the existing single-owner
module. Each timer/packet invocation updates at most two records; a text command
handles at most 256 bytes. Networking timers still advance during application
control calls. Control replies do not consume queued network packets; the next
relay poll drains them. lwIP is never entered concurrently by multiple tasks.
This bounds individual work, but does not establish strict scheduler fairness
or worst-case IRQ latency under arbitrary client load.

Runtime op 5 carries a private little-endian envelope: magic `505041f1`, version
1, command, application ID and expected generation, followed by optional text.
Commands are start (1), stop (2), status (3), text (4). IDs 1/2 are counter/echo.
A start increments generation and clears its per-run progress/request counters.
Mutation requires the current generation; status is read-only. Application
generations are scoped to one loaded module instance: clients must discard them
when the outer runtime epoch changes on unload/reload. No automatic mutation
retry or cross-module token adoption is supported. Duplicate STOP
is harmless; stale-generation STOP cannot stop a replacement. Generations never
wrap into reuse. These are bounded callback lifetimes, not forced cancellation
of non-cooperative RTEMS tasks.

The reply has twelve LE words: magic `525041f1`, version, status, application ID,
generation, running, update count, elapsed milliseconds, requests, completed
stops, cumulative protocol errors, payload length; then at most 256 text bytes.
Expected negative tests increment protocol errors, not networking packet drops.
No native C structure is copied onto the wire.

## Bounded host arbitration

`broker.py` exposes `/run/i960-combined.sock`, root-only, and passes operations
through the original `/run/i960-rtems-runtime.sock`. It has no PCI mapping and
never retries an uncertain operation. The relay and combined prompt select it
with `I960_RUNTIME_SOCKET`; the diagnostic console retains its independent socket.

At most sixteen front-end clients are live. Partial requests expire after two
seconds; queued requests expire before dispatch after five seconds. Requests are
limited to one JSON operation and 4096 bytes per connection. Already-arrived
requests are classified before dispatch. When both classes are queued, at most
three network operations precede an application operation; applications cannot
starve indefinitely behind a continuous network queue. This ratio describes
classified queues, not a hard bound on OS scheduling or backend latency.

The owner is still the authority after dispatch; a dead peer merely loses its
reply. Broker journals rotate at 2 MiB with one backup. The underlying hardware
owner's application journal remains unbounded and is a separate long-run gap.
`start_broker.py` refuses an existing process/listener and removes only a proven
dead, correctly owned Unix socket before restarting the broker. It never adopts
or resets the PCI owner or its grant.

The first direct-client mixed run failed on an HTTP timeout after roughly eight
minutes, although the server later responded and card packet drops were zero.
That run is preserved. The scheduler removes avoidable contention; the precise
cause of the original timeout is not proved. The first scheduler prototype was
stopped early after finding accept-one/dispatch-one could bypass classification;
the final scheduler classifies all already-arrived requests before choosing.

## Qualification stages and limits

`test_apps.c` checks state transitions, independent progress, stale generations,
repeated STOP and bounds under ASan/UBSan. `test_combined.py` runs actual lwIP
IPv4/IPv6 TCP/UDP/HTTP, starts both apps, restarts one and verifies IP still works.

`endurance.py` runs three independent host clients for the first 600-second
stage: dual-stack HTTP/UDP, console polling, and application output/restarts.
Predetermined limits are 5 seconds per HTTP/console operation, 3 seconds per UDP
receive and combined echo query/action. Failed operations are recorded without
silently retrying or widening limits. A separate full-zone loan test runs during
this workload, including two-pin cancellation retention and refused module close.
One-hour and eight-hour endurance, bounded production journal rotation, actual
IRQ-gap instrumentation and arbitrary hostile-load fairness remain open.

`recovery.py` tests an abandoned application client, occupied-module upload
refusal, relay SIGSTOP/SIGCONT, relay SIGKILL with TUN destruction, idle broker SIGKILL/restart, cleanup without
a TUN, and recovery on the same boot/PCI owner. It also closes the bounded module,
writes only the first upload chunk, rejects execution of that partial image,
aborts it, reloads pristine BSS and restores both applications and networking.
It never kills the PCI owner or treats its death as a reusable grant.

## DMA qualification boundary

The running kernel's preceding baseline has 64 guarded channel-0 DMA frames and
32 live paired PIO comparisons. Existing hardware captures for profiles 6–13
are independently replayed by `qualify_dma_evidence.py`: active DMA fault/NMI,
stall/timeout retention, exact-evidence CE resume and refusal after evidence
mutation. Native production-header tests exercise chain order, peer isolation,
reuse and error/timeout retention. These captures used their recorded kernels;
replaying them is not a new injection into the combined runtime.

The packet path remains PIO. The existing DMA primitive copies 64 KiB into a
retained coherent frame target and publishes a second-descriptor marker. Packet
replies are at most 2 KiB, and current response polling still reads a 4 KiB page.
Substituting the frame primitive without changing publication/completion would
not by itself establish an acceleration benefit. No measured packet speedup,
input DMA direction, simultaneous frame/packet arbitration or direct NIC DMA is
claimed.

The next P9 experiment needs a kernel-owned packet DMA descriptor/target lease,
generation completion without redundant full-page PIO polling, byte-exact PIO
comparison, and matched packet sizes/CPU/IRQ measurements. Keep channels 1/2 and
stock SCSI resources excluded. Exercise stale completions, backpressure, STOP,
owner death and finite timeout before enabling it by default. A failed or
uncertain transfer retains its buffers until proved drain/reset.

The current owner also has an explicit **100 ms idle-loop sleep** in
`doom_dma/run_bridge.py`, after heartbeat, ownership audit and status snapshot.
The broker does not alter that live process. Its observed roughly 100–300 ms
backend calls are consistent with this polling cadence, rather than proving a
PCI bandwidth limit. Before a packet-DMA A/B run, split fast service polling
(e.g. a separately qualified 5 ms budget) from the existing 100 ms ownership
checks and 500 ms heartbeat. That requires a new owner session/reset and fresh
hardware baseline; do not patch or replace the running owner in place. Verify
fault detection and STOP bounds, then measure fixed-size PIO and DMA transactions
under identical service scheduling. A frame-DMA FPS result is not evidence of a
network-DMA speedup.
