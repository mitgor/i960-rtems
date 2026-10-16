# Preemptive RTEMS and DMA networking plan

## October 14 DMA checkpoint

The user authorized exclusive DMA ownership, memory remapping, and firmware
changes if needed. The [bounded DMA1 proof](../../rtems/dma/README.md) now passes
24 card-to-host transfers with 61 full audit pairs, exact destination/guard
checks and normal system drain. No ATU remap or flash change was necessary.
This advances H0 and the card-to-host portion of H1, not the full bidirectional
or active-abort/lifetime gates. The first wrong-DAR timeout is preserved alongside
the corrected accepted run in [the evidence](../../artifacts/notes/dma-owned-20261014.md).

Before Doom or H2 queues, move preparation/checking out of interrupt context
(the proof measured a 111.481 ms maximum IRQ gap), add task-owned asynchronous
completion and test pending-job STOP/deadline/disconnect. Keep coherent mappings
retained on uncertainty. Then compare DMA/mailbox bytes of identical frozen
frames with all full audits. Existing entries below describe the earlier roadmap;
"no changing active ATU windows" was the initial test gate, not a standing ban
on the newly authorized remapping investigation.


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
[Exclusive contract and remaining gates](../../rtems/exclusive/README.md),
[30-iteration ledger](../../rtems/exclusive/BATCH.md). Production remains `autonet`.


**Callback-free monitor milestone (2026-10-11):** `handoff` passed five final
sessions: 20 bounded entries from the timer ISR after the ARM firmware callback
returned, five omitted-RELEASE expiries and ten denied DMA/SCSI transfer
requests. Every final close restored RAM and unloaded. The initial token-repeat
failure required recovery; a second build exposed an i960 compiler condition-code
bug in the diagnostic policy. Both failures and corrections are preserved.
Stock firmware uses DMA0/1; idle registers do not grant ownership. This is a bare
monitor prerequisite, not callback-free RTEMS scheduling or permanent takeover.
Production IPv6 HTTP is restored. [Contract and next gates](../../rtems/handoff/README.md),
[16-step batch](../../rtems/handoff/BATCH.md).


**Continuous execution lease (2026-10-11):** `leaseirq` now keeps preemptible
RTEMS workers running continuously inside a parked firmware callback. Sideband
grant/renew/STOP, a 512-tick renewal deadline, a non-renewable 24,000-tick cap and
per-tick timer/vector/mask/MU checks make the execution lease explicit. Nine
sessions passed 23 callbacks and 13 leases, including 60 seconds of renewed
execution, 115 seconds to the cap, expiry and transitive quarantine. All 40,111
hardware checks reported no drift; all closes restored RAM and unloaded.
Native tests, 1,610 actual-report mutations and production IPv6 HTTP passed.
[Contract, ownership table and evidence](../../rtems/leaseirq/README.md). Firmware stays parked; DMA/SCSI
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
[Contract and evidence](../../rtems/persistirq/README.md). RTEMS interrupts run inside bounded epochs and are
restored between callbacks; this is not free-running firmware coexistence.
Keep production on autonet. Earlier next-step descriptions are historical.


**2026-10-11 asynchronous resource integration:** [ownirq](../../rtems/ownirq/README.md)
now composes nested-critical deferral, a real mutex dependency, software-reference
deferral and original IRQ-frame preservation. Known owner/waiter quarantine lets
unrelated interrupt-driven work continue. Completed quiescence with an unresolved
lease is rejected by the host cleanup gate. This advances the resource part of
P4 but does not establish P2 firmware takeover or an unrestricted resident P3 BSP.

Next: (1) extend the supervisor's explicit dependency registry to two resources
and transitive waiters, including acquisition order and admission closure;
(2) test generation-safe reuse only after all real IRQ continuations and references
are drained, preserving quarantine otherwise; (3) establish persistent interrupt
and RAM reservation before repeated resident asynchronous epochs; (4) add actual
host-buffer lease acknowledgements and verified hardware drain/reset before
host-RAM DMA. A timer deadline, QUIESCED token or callback return is not a DMA
completion. Direct NIC access remains downstream of those ownership gates.


**2026-10-11 ownership batch:** [persistent resource contracts](../../rtems/ownership/README.md)
now pass on the card in a separate bounded profile. Owner checkpoint cancellation
rolls back before real mutex handoff; external software references defer retirement;
quarantined owners and dependents retain locks/stacks while an unrelated task
continues. Premature final close pins host resources despite pending=0. This does
not satisfy P2's firmware reservation or make P3 an unrestricted resident OS.

The next sequence is: (1) integrate a real held mutex and generation ledger into
the owned-ISR-stack profile; (2) deliver cancellation through the independent
channel and test critical-section/reference deferral; (3) quarantine the known
dependency pair without reclaiming its continuations while unrelated work runs;
(4) add multiple-resource dependency closure and bounded timeout tests; (5) prove
real external-buffer completion/drain plus RAM/interrupt/DMA reservation before
host-RAM DMA networking. Physical DMA and direct-NIC work remain downstream of
those ownership gates. Keep production on bounded autonet.


**2026-10-11 batch follow-up:** [critical-section and failure containment](../../rtems/switch/CONTAINMENT-BATCH.md)
now pass on the card. Six final critical sessions defer control until outer
release; three failure cases retain resources, including an invalid report after
completion. Earlier next-step statements below are historical. Resident resource
ownership and cancellation remain separate design gates.

**2026-10-11 follow-up:** [STOP-ignoring worker containment](../../rtems/switch/CONTAINMENT.md) passed
three card sessions: external suspension, retained live ISR stacks, restored
timer and full cleanup after callback return. This is one-shot instance disposal,
not permanent-interrupt-mask recovery or resident resource-safe cancellation.
Earlier next-step statements below describe their historical checkpoints.

**2026-10-11 follow-up:** [failed-control teardown tests](../../rtems/switch/FAILED-TEARDOWN.md) now pass
on the card for omitted STOP/final close and omitted RELEASE/unbind. Pending
resources remain pinned; unload is refused and recovery requires reboot. This
covers synthetic control failure, not physical disappearance or non-cooperative
task containment. Earlier next-step statements below are historical.

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
[hardware/source findings](../../artifacts/notes/dma-research-20261011.md).

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

[Two per-task ISR continuations and bounded time-slicing](../../rtems/switch/README.md)
now pass live. Next test dispatch deferral through critical sections, then
integrate a bounded MU STOP request and explicit drain handshake while the
CPU-bound tasks run. The resident monitor and general network-task preemption
remain open; production `autonet` stays on its existing bounded profile.

## P0/P1 audit and prototype checkpoint (2026-10-11)

The [interrupt audit](../../rtems/control/INTERRUPT-AUDIT.md) is written. The
[control protocol prototype](../../rtems/control/README.md) passes native tests
and a two-process shared-memory demo, and cross-compiles for i960. Read-only
PCI configuration confirms PIATVR=C0000000 and the existing 8 KiB window.
No live independent control writes are enabled: the MU overlay/index interrupt
side effects and stock mailbox/stack ownership still require a proven reservation.
This completes the offline prototype, not P1 physical validation or preemption.

## Control ownership follow-up (2026-10-11)

The [matching-firmware ownership trace](../../rtems/control/OWNERSHIP.md) identifies active handler/fault
data and mailbox/interrupt-stack uses in the BAR window. No RAM slot is reserved.
Three read-only MU samples found IMR1/OMR1 zero with message interrupts masked.
These are selected for a separate, driver-serialized bounded echo experiment;
no live sideband writes have occurred. Use the pinned 4.07-0-29 evidence, not the
older 4.07-0-39 `remote-analysis` reference.

## Live MU checkpoint (2026-10-11)


**MU echo milestone (2026-10-11):** a timer ISR echoed an IMR1 word through OMR1
in 11.02 ms while firmware sequence stayed 1 → 1. Full timer/RAM/MU restoration
and module unload passed. The first trial retained resources after an incorrect
local OISR acknowledgement; a host reboot and host-side acknowledgement fix
preceded the successful retry. [Implementation](../../rtems/control/MU-ECHO.md),
[evidence](../../artifacts/notes/mu-echo-20261011.md). Independent STOP and unrestricted
preemption remain unproven; next is framed control plus independent STOP.

## Framed control checkpoint (2026-10-11)

**Framed control milestone (2026-10-11):** CTL1 messages, retries and invalid-frame
rejection passed over IMR1/OMR1. Independent STOP froze bounded RTEMS at tick 362;
subsequent STATUS confirmed it, then independent timer HALT took 9.48 ms. Firmware
sequence stayed 1 → 1 throughout. Full cleanup passed, without reboot/flash;
Vader service restored. [Implementation](../../rtems/control/MU-FRAMED.md),
[evidence](../../artifacts/notes/mu-framed-20261011.md). This does not establish
runaway-task STOP or unrestricted preemption. Next: owned IRQ stack and complete
asynchronous context preservation before lowering task interrupt priorities.

## Owned-stack checkpoint (2026-10-11)

**Owned ISR stack milestone (2026-10-11):** an owned, guarded C interrupt stack
and explicit GPR/TC preservation passed 126 isolated stress interrupts and 546
bounded RTEMS/control interrupts. Deep call chains, sentinels, PC/TC roundtrips,
frame/guard checks and independent STOP/HALT passed; full cleanup and web restart
passed without reboot/flash. The hardware entry frame stays in place: movable
per-task interrupt contexts and unrestricted preemption remain future work.
[Implementation](../../rtems/interrupt/README.md),
[evidence](../../artifacts/notes/owned-interrupt-stack-20261011.md).

## Two-task switch checkpoint (2026-10-11)

**Two-task interrupt-switch milestone (2026-10-11):** three bounded card runs
passed timer-driven switching between CPU-bound RTEMS tasks. Each run recorded
32 IRQ-path handoffs, 31 observations of both ISR continuations live, and 16
entries/returns per task. Separate task/ISR stacks, register sentinels, frame
ownership, draining and full restoration passed; web service restored without
reboot/flash. [Implementation](../../rtems/switch/README.md),
[evidence](../../artifacts/notes/irq-switch-20261011.md). This is bounded preemption,
not a resident monitor; next are deferred-dispatch stress and MU STOP integration
while the CPU-bound task contexts are active.

## Nested dispatch deferral checkpoint (2026-10-11)

**Nested dispatch-deferral milestone (2026-10-11):** three `defer` card runs
kept task A executing through four timer ticks at dispatch depth 2 and four at
depth 1. All eight IRQs observed a pending switch to a different heir; task B
started only after the outer enable. A resumed at tick 9, depth 0. Each run
finished at tick 32 with zero faults, 20/20 and 12/12 ISR entries/returns,
verified RAM restoration and module unload. IPv6 Vader HTTP returned 200 after
restart. [Evidence](../../artifacts/notes/irq-deferral-20261011.md).
Next: integrate independent MU STOP with the two CPU-bound task contexts and
prove safe draining during an active callback. Resident operation and general
interrupt nesting remain unproven; production stays on `autonet`.

The next bounded experiment combines the proven framed MU control path with
owned per-task ISR continuations. The host must send STOP while a callback is
actively running CPU-bound workers. The ISR must defer any scheduler transfer
inside a critical section, record STOP, and permit the controller to drain both
continuations before returning to firmware. Keep a finite local deadline and
verify duplicate/status behavior, register sentinels, timer/MU restoration and
all borrowed RAM. A successful callback return is required before considering
resident execution; host-RAM DMA networking follows those control/lifetime gates.

## Pending-callback STOP checkpoint (2026-10-11)

**Pending-callback MU STOP milestone (2026-10-11):** three `mustop` card runs
accepted a one-shot host STOP at ticks 34/41/52 while both owned ISR contexts
were live and firmware sequence 1 was still pending. Workers observed the stop
flag, both contexts drained, and the card acknowledged before host RELEASE
allowed the callback to return. Zero faults; full RAM/MU restoration and module
unload passed. IPv6 Vader HTTP restored. [Evidence](../../artifacts/notes/irq-mu-stop-20261011.md).
This is a serialized host-driver experiment, not a concurrent control ioctl,
CTL1 framing, or forced termination of code that ignores the stop flag. Next:
exercise STOP during nested dispatch deferral and the missing-host deadline;
then generalize the control API and non-cooperative task containment.

The first combined control/lifetime test uses READY → STOP → DRAINED → RELEASE
in IMR1/OMR1. A host-side hook exchanges these tokens while the original command
is pending, retaining the existing session mutex. The target wakes its controller
from the timer ISR; the controller lets both stop-aware workers finish and their
ISR continuations return. It restores the timer before DRAINED. The host's RELEASE
then permits target MU cleanup and callback return; Linux acknowledges OISR only
after validating the returned report and paired reads.

Remaining gates before resident preemption/DMA work:

1. Deliver STOP during nested dispatch-disable sections and prove deferred
   scheduling plus eventual drain; exercise the local deadline without a host
   STOP and missing RELEASE with controlled failure evidence.
2. Design a user-triggered control operation that can run concurrently with an
   outstanding callback while protecting device removal, session close and DMA
   lifetime. The current synchronous session mutex intentionally remains intact.
3. Define containment for arbitrary code that does not check a stop flag. Current
   probes time-slice without yielding but cooperate in shutdown; they do not prove
   forced cancellation, safe abandonment of interrupt frames, or resident ownership.
4. Reintroduce framed epochs, retries/status and explicit stop-state semantics
   around that lifetime protocol; then revisit resident execution and host-RAM DMA.

## Critical-section STOP and omission deadlines (2026-10-11)

**Nested STOP and timeout checkpoint (2026-10-11):** all twelve `stopcases`
card runs passed. STOP at critical depths 2/1 was recorded at ticks 18/30 but
controller dispatch/drain waited until outer release at tick 40. Missing STOP
reached the 128-tick event deadline; missing RELEASE exhausted its finite loop
and returned with only the expected `0x4000` flag. All contexts, guards, paired
RAM/MU restoration and unload checks passed; no reboot/flash. IPv6 HTTP restored.
[Implementation](../../rtems/switch/STOP-CASES.md),
[evidence](../../artifacts/notes/irq-stop-cases-20261011.md).
Next: concurrent user-control/lifetime design and non-cooperative task containment.
These workers remain stop-aware; deliberate message omission is not a full host
crash or proof of recovery from permanently masked interrupts.

The preceding checkpoint's first gate is now hardware-tested: STOP remains
pending through the nested levels, missing STOP times out and drains at tick
128, and missing RELEASE returns after its loop budget. Three runs per case
passed full restoration. The next implementation gate is a concurrent user
control path with explicit session/command/removal ownership, followed by a
separately defined policy for non-cooperative tasks. Do not treat these bounded
stop-aware cases as arbitrary cancellation or resident firmware takeover.

## Concurrent host control checkpoint (2026-10-11)

**Concurrent host control (2026-10-11):** three card runs passed with STOP
issued by an ioctl on a second host thread while the firmware callback was
pending. A separate control mutex/window is joined before completion/cleanup;
wrong epochs, duplicate STOP and late requests were refused. Both ISR contexts
drained; full RAM/MU restoration and unload passed. IPv6 HTTP restored.
[API and lifetime contract](../../rtems/switch/CONCURRENT.md),
[evidence](../../artifacts/notes/irq-concurrent-control-20261011.md).
Workers remain stop-aware. Live alias-close coverage is not final-close or
physical-removal fault injection; next are broader lifecycle failure tests and
non-cooperative task containment.

## Final-close and driver-removal checkpoint (2026-10-11)

**Final-close / driver-unbind checkpoint (2026-10-11):** six final hardware
runs passed: three closes of the sole user descriptor and three sysfs unbinds
while callback/control syscalls were active. Release/removal waited for the
operations; restoration preceded BAR unmapping, and late calls were refused.
All target contexts and full RAM/MU cleanup passed; HTTP restored, no reboot/flash.
An initial truncated removal log was preserved and its publication fixed before
rerunning. [Contract and findings](../../rtems/switch/LIFECYCLE.md),
[evidence](../../artifacts/notes/irq-lifecycle-20261011.md).
Logical unbind is tested; physical hot-unplug and failing control during teardown
remain unproven. Task shutdown still cooperates with a stop flag.


## Task-owned DMA acceptance — 2026-10-14

The [asynchronous DMA batch](../../artifacts/notes/dma-async-20261014.md)
passes 48 transfers, 124 full audit pairs, explicit STOP and session-deadline
prelaunch cancellation. Worker 1 owns preparation/polling/checking; no third
interrupt-stack owner was introduced. Maximum IRQ gap falls from 111.481 ms to
10.710–10.990 ms. This completes the task-context prerequisite for a same-frame
Doom DMA/mailbox experiment, not production networking DMA or direct NIC access.
Next preserve the immutable frame/generation/ACK pin, compare all bytes through
both transports, then measure browser FPS. Keep the retained-until-reboot rule;
physical hung-engine recovery and reusable buffer lifetime remain open.
