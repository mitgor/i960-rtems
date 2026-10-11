# RTEMS on the DAC960PG

**Exclusive RTEMS track (2026-10-11):** the user explicitly permits RAID/SCSI
shutdown during RTEMS and reboot/power-cycle to exit. `exclusive` now runs real
preemptible RTEMS after the ARM callback returns, with inactive i960 DMA disabled,
primary/secondary bus mastering denied and external secondary grants disabled.
Nine bounded sessions restored/unloaded; resident deadline/STOP runs parked at
1,200/581 ticks with all task IRQs drained and resources retained. The first
reboot needed user intervention; unattended recovery remains unproven.
This is tested CPU/bus isolation within the existing allocation, not proof of
cache-coprocessor drain or arbitrary RAM ownership. **Keep the cooperative
RTEMS + stock-firmware path and all its profiles/evidence as a future option.**
[Exclusive contract and remaining gates](exclusive/README.md),
[30-iteration ledger](exclusive/BATCH.md). Production remains `autonet`.


**Callback-free monitor milestone (2026-10-11):** `handoff` passed five final
sessions: 20 bounded entries from the timer ISR after the ARM firmware callback
returned, five omitted-RELEASE expiries and ten denied DMA/SCSI transfer
requests. Every final close restored RAM and unloaded. The initial token-repeat
failure required recovery; a second build exposed an i960 compiler condition-code
bug in the diagnostic policy. Both failures and corrections are preserved.
Stock firmware uses DMA0/1; idle registers do not grant ownership. This is a bare
monitor prerequisite, not callback-free RTEMS scheduling or permanent takeover.
Production IPv6 HTTP is restored. [Contract and next gates](handoff/README.md),
[16-step batch](handoff/BATCH.md).


**Continuous execution lease (2026-10-11):** `leaseirq` now keeps preemptible
RTEMS workers running continuously inside a parked firmware callback. Sideband
grant/renew/STOP, a 512-tick renewal deadline, a non-renewable 24,000-tick cap and
per-tick timer/vector/mask/MU checks make the execution lease explicit. Nine
sessions passed 23 callbacks and 13 leases, including 60 seconds of renewed
execution, 115 seconds to the cap, expiry and transitive quarantine. All 40,111
hardware checks reported no drift; all closes restored RAM and unloaded.
Native tests, 1,610 actual-report mutations and production IPv6 HTTP passed.
[Contract, ownership table and evidence](leaseirq/README.md). Firmware stays parked; DMA/SCSI
ownership and unrestricted coexistence are not established. Production remains
autonet. Earlier next-step descriptions below are historical.


**Persistent asynchronous epochs (2026-10-11):** `persistirq` preserves one
RTEMS instance across host calls and tracks a transitive two-mutex dependency
chain A/B/C. Five normal sessions passed 120 callbacks, 29 clean rollback/handoffs
and 46 follow epochs with the quarantined chain unchanged while Other ran.
An intentional six-callback early-close session retained resources despite a
completed QUIESCED handshake. Replay verified 126 reports and rejected 5,922
mutations; the full native suite passed. The retained-close reboot recovered;
a fresh 18-callback session passed and production IPv6 HTTP returned 200.
[Contract and evidence](persistirq/README.md). RTEMS interrupts run inside bounded epochs and are
restored between callbacks; this is not free-running firmware coexistence.
Keep production on autonet. Earlier next-step descriptions are historical.


**Asynchronous ownership integration (2026-10-11):** the separate `ownirq`
profile now combines a real shared mutex, blocked waiter and software lease with
task-owned IRQ stacks and concurrent host STOP. Nested critical sections defer
controller execution until outer release; clean cancellation drains the owner's
IRQ frame, waits for its lease, rolls back and hands the lock to the waiter.
Quarantine preserves owner/waiter dependencies while an unrelated preempted task
continues. A valid QUIESCED/completed callback with an outstanding lease returns
ENODATA and retains resources with pending=0. The first run exposed i960 struct
padding in report serialization; it was archived, corrected and retested.
Ten asynchronous sessions passed full RAM/MU restoration; both retained cases
recovered by reboot. The persistent serialization fix passed 48 more callbacks.
Native/replay checks passed, and production IPv6 HTTP returned 200.
[Contract, matrix and evidence](ownirq/README.md). These remain bounded one-shot experiments,
not unrestricted resident execution or physical DMA cancellation. Keep production
on autonet. Earlier next-step statements below are historical.


**Resident ownership batch (2026-10-11):** the separate persistent `ownership`
profile passed a 48-callback smoke run and three 371-callback sessions: real
priority-inheritance mutex, owner-only release, blocked waiter, cancellation
rollback, software-reference deferral, stale/duplicate completion rejection,
clean owner restart with new epochs, and owner/waiter quarantine while an
unrelated worker continues. These are bounded persistent callbacks, not the
asynchronous IRQ profile. A premature final close retained dirty state, DMA,
BAR and module with pending=0 and refused ordinary unload. After reboot, a
further 48-callback run passed full restoration; production IPv6 HTTP returned
200. Total: 1,209 normally completed callbacks, 62 rollback/handoffs and five
normal closes, plus the three-callback retained-close test. No flash writes.
[Contract, evidence and next integration gate](ownership/README.md). Earlier next-step
statements below are historical. Do not force-unlock a quarantined resource,
delete its tasks, reuse its stacks, or treat a software lease as a DMA drain.


**Automatic containment batch (2026-10-11):** six final critical-section
sessions passed (three per depth), following six initial passes. STOP at ticks
18/30 deferred controller execution until outer release at tick 40; external
suspension completed at tick 44. The final module removes a stack-frame warning.
Three separate failure tests retained resources: omitted STOP/final close,
omitted RELEASE/unbind, and invalid local report after real callback completion.
The last case returned ENODATA and retained dirty state with pending=0, proving
retention does not depend solely on an outstanding command. All refused unload;
evidence was saved before each reboot. All three reboots and final fresh
preflight passed; production IPv6 HTTP is restored. [Results and next gate](switch/CONTAINMENT-BATCH.md).
General resident task cancellation, permanent interrupt masks and DMA ownership
remain unproven; keep production on bounded autonet.

**STOP-ignoring worker containment (2026-10-11):** three live `contain`
sessions passed. Both workers continued four ticks after STOP, then the
controller externally suspended them, restored the timer and returned. Each
worker retained one live ISR continuation; task/ISR stacks were kept intact
until callback return, with 10,000 stable checks. The distinct QUIESCED token
and exact-image-pinned host gate prevent confusing suspension with draining.
Full RAM/MU restoration and unload passed each time; HTTP restored, no reboot
or flash. [Contract, results and limits](switch/CONTAINMENT.md).
This disposes of a bounded one-shot RTEMS instance; permanent interrupt masking,
scheduler corruption and resource-safe cancellation in a resident OS remain
unproven. Next: bounded critical-section containment and failure-path coverage.

**Failed-control teardown checkpoint (2026-10-11):** both live injection cases
passed: omitted STOP during final-user-fd close, and omitted RELEASE during
unbind. Both syscalls returned ETIMEDOUT; pending/dirty state, DMA/BAR and module
references remained retained. No post-failure firmware commands or cleanup/free
occurred; ordinary unload was refused. Completion became visible but was not
consumed after the control error. These are synthetic omissions on a responsive
card, not physical PCI faults. Evidence was saved before each recovery reboot.
Both reboots completed; fresh preflight passed and IPv6 HTTP returned 200.
[Contract, findings and reproduction](switch/FAILED-TEARDOWN.md).
Next: non-cooperative task containment; production stays on bounded autonet.

**Final-close / driver-unbind checkpoint (2026-10-11):** six final hardware
runs passed: three closes of the sole user descriptor and three sysfs unbinds
while callback/control syscalls were active. Release/removal waited for the
operations; restoration preceded BAR unmapping, and late calls were refused.
All target contexts and full RAM/MU cleanup passed; HTTP restored, no reboot/flash.
An initial truncated removal log was preserved and its publication fixed before
rerunning. [Contract and findings](switch/LIFECYCLE.md),
[evidence](../artifacts/irq-lifecycle-20261011/README.md).
Logical unbind is tested; the later failed-control checkpoint above covers
synthetic omissions during teardown. Physical hot-unplug remains unproven. Task shutdown still cooperates with a stop flag.


**Concurrent host control (2026-10-11):** three card runs passed with STOP
issued by an ioctl on a second host thread while the firmware callback was
pending. A separate control mutex/window is joined before completion/cleanup;
wrong epochs, duplicate STOP and late requests were refused. Both ISR contexts
drained; full RAM/MU restoration and unload passed. IPv6 HTTP restored.
[API and lifetime contract](switch/CONCURRENT.md),
[evidence](../artifacts/irq-concurrent-control-20261011/README.md).
Workers remain stop-aware. Live alias-close coverage is not final-close or
physical-removal fault injection; next are broader lifecycle failure tests and
non-cooperative task containment.


**Live web system information (2026-10-11):** the IPv6 Vader page now shows
card runtime uptime, RTEMS/lwIP and CPU details, memory capacities, HTTP counts
and RX/TX/drop counters. CPU utilization and temperature are explicitly
unavailable; measured timer-bus frequency is not labelled as CPU frequency.
24 live HTTP checks and full cleanup/restart passed. Production module is now
`autonet-module-system-info`, paired with the updated `autonet` image.
[Details](net/SYSTEM-INFO.md), [artifacts](../artifacts/rtems-system-info-20261011/README.md).


**Nested STOP and timeout checkpoint (2026-10-11):** all twelve `stopcases`
card runs passed. STOP at critical depths 2/1 was recorded at ticks 18/30 but
controller dispatch/drain waited until outer release at tick 40. Missing STOP
reached the 128-tick event deadline; missing RELEASE exhausted its finite loop
and returned with only the expected `0x4000` flag. All contexts, guards, paired
RAM/MU restoration and unload checks passed; no reboot/flash. IPv6 HTTP restored.
[Implementation](switch/STOP-CASES.md),
[evidence](../artifacts/irq-stop-cases-20261011/README.md).
Next: concurrent user-control/lifetime design and non-cooperative task containment.
These workers remain stop-aware; deliberate message omission is not a full host
crash or proof of recovery from permanently masked interrupts.


**Pending-callback MU STOP milestone (2026-10-11):** three `mustop` card runs
accepted a one-shot host STOP at ticks 34/41/52 while both owned ISR contexts
were live and firmware sequence 1 was still pending. Workers observed the stop
flag, both contexts drained, and the card acknowledged before host RELEASE
allowed the callback to return. Zero faults; full RAM/MU restoration and module
unload passed. IPv6 Vader HTTP restored. [Evidence](../artifacts/irq-mu-stop-20261011/README.md).
This is a serialized host-driver experiment, not a concurrent control ioctl,
CTL1 framing, or forced termination of code that ignores the stop flag. Next:
exercise STOP during nested dispatch deferral and the missing-host deadline;
then generalize the control API and non-cooperative task containment.


**Nested dispatch-deferral milestone (2026-10-11):** three `defer` card runs
kept task A executing through four timer ticks at dispatch depth 2 and four at
depth 1. All eight IRQs observed a pending switch to a different heir; task B
started only after the outer enable. A resumed at tick 9, depth 0. Each run
finished at tick 32 with zero faults, 20/20 and 12/12 ISR entries/returns,
verified RAM restoration and module unload. IPv6 Vader HTTP returned 200 after
restart. [Evidence](../artifacts/irq-deferral-20261011/README.md).
Next: integrate independent MU STOP with the two CPU-bound task contexts and
prove safe draining during an active callback. Resident operation and general
interrupt nesting remain unproven; production stays on `autonet`.


## Hardware clock and IPv6 web server (2026-10-11)

`net` remains the cooperative baseline. `autonet` runs bounded RTEMS/lwIP work
from timer-1 interrupts at approximately 100 Hz, including between host calls.
It serves HTTP on card port 80 with four connections and 512-byte request headers.
Packet delivery still uses the Linux TUN relay. See [implementation and limits](autonomous/README.md)
and [live evidence](../artifacts/rtems-web-autonomous-20261011/README.md).

Build with `build.py --profile autonet` and the usual work directory/toolchain
arguments. Generate the **matching** module with
`autonomous/build_transport.py --network --payload <autonet/kernel.bin> --out <module-dir>`;
compile it against the running host kernel. Never pair a background image with
the cooperative module. Run `transport/relay.py --autonomous --payload <kernel.bin>
--module <dac960auto.ko> --output <new-directory> --serve --internet6
--publish-http6 <host-global-IPv6> --http-port 8080` with root privileges.
The host address must be assigned to its uplink. Gateway changes are journaled;
normal close stops the timer, restores RAM and removes routing rules. After a
killed relay, `transport/cleanup.py --help` describes explicit journal cleanup;
the kernel release itself performs the timer stop before restoring memory.

The current remote launcher is `rtems/serve-autonomous.sh`, installed alongside
the build directories. Stop its transient service with `sudo systemctl stop
 i960-http6`. This service is intentionally left running for the user's test;
it is not configured to restart after reboot.


RTEMS 4.6.6 Classic tasks and lwIP 2.1.3 now execute on the physical i960RP.
The card answers ICMP, provides UDP/TCP echo services, resolves DNS and fetches
HTTP through the Linux host. A 30-minute run passed 29,352 callbacks and echoed
18,896,608 TCP bytes exactly; shutdown, forced-client-exit and full restoration
checks also passed. Exact images, source packages, captures and results
are under [artifacts/rtems-20261011](../artifacts/rtems-20261011/README.md).

IPv4 and IPv6 now work together on the card. Static IPv6 ping, UDP/TCP echo,
AAAA lookup and IPv6 Internet HTTP passed live tests. See the
[IPv6 evidence and limitations](../artifacts/rtems-ipv6-20261011/README.md).

## Execution model

This is a **cooperative, RAM-only RTEMS port** using the existing programmed
stock-firmware extension. Each host request resumes RTEMS; a service task
processes bounded work, exchanges a semaphore signal with another task, and
switches back to the saved firmware-call context. Task stacks, queues and lwIP
state persist across calls. The firmware regains control between calls.

The card runs RTEMS scheduling and the TCP/IP implementation. Linux transports
complete IP packets through a TUN interface, then routes/NATs outbound traffic.
Clock ticks come from elapsed host monotonic time, in 10 ms units. Task sleeps
and timeouts advance when requests arrive. Interrupt priority stays at 31
inside RTEMS and returns to its saved value when the callback finishes. Stock
interrupt vectors and timers retain their ownership.

This makes practical progress without the original plan's exclusive firmware
handoff. An autonomous hardware-clock/preemptive BSP, independent mailbox
transport, CPU takeover, recovery, POSIX sockets, TLS and general libc support
remain future work. RTEMS pauses when the host stops polling. A callback that
never returns still cannot be preempted by the host.

## Build from the preserved sources

The tested host is Ubuntu 22.04.5 x86-64, kernel `6.8.0-138-generic`, with the
existing GCC 3.3.6 / binutils 2.27 tools at `/home/mit/i960/tools/bin`.
The [exact compiler archive](../artifacts/toolchain-20261011/README.md) is in Git.
Source URLs and SHA256 identities are pinned in [sources.json](sources.json).

From the repository root on the Mac, choose a new remote build directory:

```sh
python3 rtems/deploy.py --destination /home/mit/i960-rtems-new-build
```

This copies the relevant sources/packages, builds the target and generates a
separate `dac960rtems.ko`. It does not touch the card or host routing. Kernel
module hashes vary with build paths/debug metadata; compare generated source
and retain the exact module used in each run. The target image was reproduced
byte-for-byte in a separate build directory.

`build.py --work <directory> --profile bounded|session|net` can also be used
on Linux. `bounded` is the one-shot Classic API test, `session` retains two
tasks and echoes bytes across callbacks, and `net` adds lwIP and guarded task
stacks. The build uses RTEMS core source files and headers directly, with the
explicit adaptations below, rather than the old board's BSP startup.

Newlib 1.11.0 plus its matching RTEMS patch supplies compatible headers. The
application links the small freestanding routines in `libc.c`; it does not
claim a complete Newlib runtime. Tested applications are integer-only C for
i960RP; no floating-point library or task FP-state support is provided.
The compiler's `i960-coff-` command names drive ELF assembler/linker tools.

## Run on the existing PC

The installed working directory is `/home/mit/i960-rtems-ipv6-20261011`.
Use a **new** output directory for each invocation. The card must be idle and
unbound; the runner shares Tetris's exclusive `/run/lock/i960-loadrun.lock`.
It refuses an already-owned card. Finish Tetris before starting RTEMS.

To keep RTEMS services running in the foreground, use the installed launcher:

```sh
ssh -t mit@192.168.2.75 /home/mit/i960-rtems-ipv6-20261011/serve.sh
```

It creates a timestamped capture directory. Ctrl-C restores RAM and releases
the module/interface. Add `--ipv6` for dual-stack local services, `--internet`
for IPv4 routing, or `--internet6` for IPv6 Internet routing and tests.

For a finite local host/card ICMP, UDP and TCP test:

```sh
ssh -t mit@192.168.2.75 'sudo -n python3 /home/mit/i960-rtems-ipv6-20261011/project/rtems/transport/relay.py --payload /home/mit/i960-rtems-ipv6-20261011/net/kernel.bin --module /home/mit/i960-rtems-ipv6-20261011/module/dac960rtems.ko --output /home/mit/i960-rtems-ipv6-20261011/my-local-test'
```

Add `--internet` to resolve and fetch `example.com` over HTTP, `--faults` to
inject one dropped TCP data packet and a slow reader, or `--duration 1800`
for a half-hour local TCP stress test. `--fetch <hostname>` chooses the HTTP
host when Internet testing is enabled. Add `--serve` to keep services running
after the tests until Ctrl-C, or `--serve 60` for a bounded service interval.
From another SSH terminal, try `ping 10.196.0.2` or `nc 10.196.0.2 9600`; TCP
returns the bytes you send. Results and packet captures go into
the chosen output folder. The client automatically closes/restores the card,
unloads its module and removes its routing changes after the test.

The current fixed network profile uses host `10.196.0.1/30`, card
`10.196.0.2/30`, interface `i960rt0`, DNS `192.168.2.3`, TCP echo port 9600 and
UDP echo port 9601. The relay checks for overlapping host routes and an existing
interface/rules before use. To use another network, change the target and host
configuration together and rebuild. It does not bridge the card onto the LAN.

IPv4 Internet mode discovers the single default uplink, temporarily enables IPv4
forwarding and adds address/interface-scoped NAT and forwarding rules. It
allows replies toward the card and drops unsolicited forwarded input. Cleanup
removes only its exact rules and restores the saved forwarding value. Loading
iptables may leave empty default-policy tables/chains initialized; no project
rules remain after normal cleanup. Snapshots record the actual before/after
configuration.

### IPv6 usage and scope

```sh
ssh -t mit@192.168.2.75 "/home/mit/i960-rtems-ipv6-20261011/serve.sh --ipv6"
# From another terminal on that PC:
ping -6 fd96:196:960::2
nc -6 fd96:196:960::2 9600
```

Host/card IPv6 addresses are `fd96:196:960::1/64` and `fd96:196:960::2/64`.
The card also configures `fe80::960:2`. The TUN link carries raw IP packets;
Ethernet neighbor resolution is unnecessary. Addresses are static: SLAAC,
router solicitation, DAD and MLD are disabled. IPv6 fragmentation/reassembly
is disabled; MTU is 1500 and TCP MSS is 1200. This is a tested constrained
dual-stack profile, not a claim of full IPv6 conformance.

`--internet6` tests AAAA resolution and card-originated HTTP over IPv6. It
requires a working IPv6 default uplink and ip6tables NAT support on Linux.
The host temporarily enables forwarding and adds scoped NAT66 and reply-only
forwarding rules for the card. **It also enables the existing IPv4 gateway,
because DNS server `192.168.2.3` is still reached over IPv4.** This does not
provide an IPv6-only DNS deployment. The TCP connection and HTTP handling run
on the card; the host routes packets rather than proxying application sockets.

The IPv6 journal records rule intent before installation and saves forwarding
and uplink `accept_ra` settings before changes. Uplink `accept_ra=2` preserves
router advertisement reception while forwarding. Cleanup restores those
settings and removes only the recorded rules. `cleanup.py` replays both IP
families after SIGKILL. `--faults` drops one echo data packet per enabled IP
family; `--duration` stresses IPv6 when either IPv6 flag is active.

SIGTERM/SIGHUP and normal exceptions run cleanup. SIGKILL cannot run Python
cleanup: the final device-file release restores RAM when the kernel can prove
it safe, but module unload and routing cleanup require the saved journal:

```sh
sudo python3 /home/mit/i960-rtems-ipv6-20261011/project/rtems/transport/cleanup.py /path/to/previous-output
```

The cleanup tool refuses an interface still held by a live client and refuses
to force-unload an uncertain card. It is not a recovery or reset tool.

## Memory and protocol

| Range | Ownership during a session |
| --- | --- |
| `C0F2C000–C0F4BFFF` | Immutable target text/rodata and padding (128 KiB) |
| `C0F4C000–C0F4C00F` | Immutable lower guard |
| `C0F4C010–C0F9BFEF` | Explicit RTEMS data, BSS, workspace and guarded task stacks |
| `C0F9BFF0–C0F9BFFF` | Immutable upper guard |
| `C0F9C000–C0F9F05F` | RIO1 header, 4 KiB input, 8 KiB output and BIO-style guards |
| `C0F9F060–C0FABFFF` | Untouched remainder of the original 512 KiB staging image |

The established runner/result slots in the extra 8 KiB allocation are borrowed
and restored by the existing guarded transport. Nothing extends into arbitrary
firmware DRAM. The full 512 KiB image and runner/table/result bytes are saved
before use and independently checked after restoration.

`dac960rtems` is derived from the tested persistent-session transport with a
separate module, device, debugfs name and wire magic. It uploads 471,136 bytes
once. Every STEP makes paired reads of that complete prefix, checking immutable
code/guards and response bounds while allowing the explicitly designated
private state to change. Every 32 steps and at close, the audit covers the whole
512 KiB image. User code is never retried. Uncertain execution or restoration
retains module/DMA ownership for inspection rather than forcing an unload.

RIO1 retains the BIO1 header layout at offset `0x70000`, with magic `0x314f4952`.
The supplied clients use the full 8 KiB output capacity. A request body starts
with four little-endian words: `RTM1` magic, operation, elapsed milliseconds
(0–1000), and body length. Operations are poll (0), IPv4/IPv6 input (1), IPv4 DNS/HTTP
fetch (2), status/poll (3), fetch-buffer read (4), and IPv6 DNS/HTTP fetch (5).
The fetch operations explicitly select A or AAAA resolution. Fetch takes a little-endian
16-bit port followed by a hostname; buffer read takes a 32-bit offset.

The network response has twelve words: magic, callback count, worker count,
tick count, report size (24), RX packets, TX packets, drops, fetch state,
fetch length, FNV-1a hash and following-byte count. Normally the following bytes
are length-prefixed IP packets. Bit 31 of the final word marks returned HTTP
bytes instead. The kernel checks the outer framing; the host checks these
application fields independently. TCP/IP uses lwIP raw callbacks exclusively
from one RTEMS task (`NO_SYS=1`); there is no `sys_arch`/socket API claim.

Three stack allocations have lower and upper canaries, checked every callback.
The normal allocations are 2,048, 8,192 and 4,096 bytes. The profile allows
two application tasks plus idle; adding tasks requires changing both RTEMS
configuration and the guarded stack allocator within the established budget. Workspace restoration
and guards do not establish memory protection between RTEMS tasks; all target
code is trusted and shares one address space.

## CPU-port and ABI adaptations

- Correct the generic i960 header's big-endian declaration for this little-endian
  RP build. Assert the context-register offsets used by the assembly switcher.
- Keep all task contexts and interrupt-level changes masked in this cooperative
  profile. Disable RTEMS installation of a hardware interrupt stack.
- Use the historical context-switch/restore assembly, without its ISR wrapper.
  Save an outer return context so explicit RTEMS/lwIP fatal errors can return
  an error to the guarded loader. Hardware faults/runaway code are a separate gap.
- Clear BSS explicitly on first entry; retain private state on later calls.
- Reconcile Newlib's signed integer typedefs with RTEMS's `stdint.h` adapter.
- Pack lwIP's ten-byte DNS answer structure explicitly: i960's aggregate ABI
  otherwise rounds it to sixteen bytes and trips lwIP's sanity assertion.
- Apply the shared `lwip_patches.py` adaptations in target and native builds.
  Besides DNS packing, reject zero-checksum IPv6 UDP before the pinned lwIP
  2.1.3 receive path can accept it; IPv4 retains its optional checksum behavior.
- Use simple binary semaphores for signals. The historical mutex-style binary
  semaphore permits recursive ownership, which is unsuitable for this exchange.

The historical RP BSP cannot safely be copied wholesale: its raw-vector
installer uses `&Prcb`, its vector-cache handling needs review, the generic ISR
assembly has stale symbol naming and a shared global-register save area, and
the old clock ISR writes a board-specific address (`0xFED00000`). The clock
reload constants also assume a different board frequency. These paths are not
used by this implementation; full interrupt/preemption work remains separate.

## Offline verification

```sh
make -C rtems test
python3 rtems/transport/validate_run.py /extracted/run --payload /exact/kernel.bin --symbols /exact/kernel.symbols
python3 rtems/transport/validate_packets.py /extracted/run/packets.pcap
python3 host/audit/artifacts.py --check-git
```

Native tests cover the actual generated transaction under injected command
failures, C/Python wire guards, and the actual lwIP virtual interface under
ASan/UBSan. Capture validators check trace state/ticks, image immutability,
stack guards, restoration and packet checksums/streams. Native tests supplement
the physical-card evidence; they do not emulate all i960 faults or DMA failures.

Original RTEMS and lwIP notices are preserved in `LICENSE-RTEMS`,
`COPYING-RTEMS`, `COPYING-lwIP` and their complete source archives. The source
manifest records primary upstream URLs, including the
[RTEMS release archive](https://ftp.rtems.org/pub/rtems/releases/4.6/4.6.6/) and
[lwIP source](https://github.com/lwip-tcpip/lwip/tree/STABLE-2_1_3_RELEASE).
The single-context integration follows lwIP's
[raw main-loop API](https://www.nongnu.org/lwip/2_1_x/group__lwip__nosys.html).

## Continuing development

Start application work in `net/app.c`: bounded input handling runs in the RTEMS
service task, and semaphore exchange demonstrates a second independent task.
Keep lwIP raw calls in that service task. RTEMS's scheduler can change tasks at
kernel operations, but no hardware tick can interrupt arbitrary application
code in this profile. Split long computations into bounded pieces and yield
back to the host regularly; adding an infinite task loop without blocking can
stop the firmware command from returning.

Use the [integrated development plan](../DEVELOPMENT-PLAN.md) as the current
backlog: M1 generalizes the proven larger loader profile; R1 adds diagnostics
and application support; M2 rebalances owned memory if needed; R2 covers
sys_arch/runtime APIs. M3 and A1–A3 separately address new RAM ownership and
autonomous execution. These stages also account for the unresolved findings.

The complete archived evidence can be checked with:

```sh
python3 rtems/verify_artifacts.py
python3 rtems/verify_ipv6_artifacts.py
```

`transport/live_service_test.py` checks repeated TCP connections and UDP through
the foreground service mode. `transport/live_cleanup_test.py` is an **explicit hardware test** for process
termination and a malformed application request. It also enables temporary
Internet routing to exercise journal cleanup. It is separate from `make test`,
which remains offline. Its SIGKILL case targets an established session, not
every instruction boundary during firewall setup or teardown.

## Owned interrupt execution stack

The isolated `irqctx` and bounded background `muctx` profiles now pass on the
card. See [implementation, context contract and reproduction](interrupt/README.md).
The hardware frame remains in place; this does not enable arbitrary preemption.

## Bounded CPU-bound task preemption

The [switch profile](switch/README.md) now passes hardware tests with two
CPU-bound tasks time-sliced by timer interrupts, each owning its suspended ISR
continuation. Three runs preserved registers and drained every continuation
before full RAM restoration. This remains a finite firmware callback; the
production web server and resident-preemption limitations remain unchanged.
