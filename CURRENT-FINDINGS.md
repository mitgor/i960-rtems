# Current findings and evidence — 2026-10-11

**Persistent asynchronous epochs (2026-10-11):** `persistirq` preserves one
RTEMS instance across host calls and tracks a transitive two-mutex dependency
chain A/B/C. Five normal sessions passed 120 callbacks, 29 clean rollback/handoffs
and 46 follow epochs with the quarantined chain unchanged while Other ran.
An intentional six-callback early-close session retained resources despite a
completed QUIESCED handshake. Replay verified 126 reports and rejected 5,922
mutations; the full native suite passed. The retained-close reboot recovered;
a fresh 18-callback session passed and production IPv6 HTTP returned 200.
[Contract and evidence](rtems/persistirq/README.md). RTEMS interrupts run inside bounded epochs and are
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
[Contract, matrix and evidence](rtems/ownirq/README.md). These remain bounded one-shot experiments,
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
[Contract, evidence and next integration gate](rtems/ownership/README.md). Earlier next-step
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
preflight passed; production IPv6 HTTP is restored. [Results and next gate](rtems/switch/CONTAINMENT-BATCH.md).
General resident task cancellation, permanent interrupt masks and DMA ownership
remain unproven; keep production on bounded autonet.

**STOP-ignoring worker containment (2026-10-11):** three live `contain`
sessions passed. Both workers continued four ticks after STOP, then the
controller externally suspended them, restored the timer and returned. Each
worker retained one live ISR continuation; task/ISR stacks were kept intact
until callback return, with 10,000 stable checks. The distinct QUIESCED token
and exact-image-pinned host gate prevent confusing suspension with draining.
Full RAM/MU restoration and unload passed each time; HTTP restored, no reboot
or flash. [Contract, results and limits](rtems/switch/CONTAINMENT.md).
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
[Contract, findings and reproduction](rtems/switch/FAILED-TEARDOWN.md).
Next: non-cooperative task containment; production stays on bounded autonet.

**Final-close / driver-unbind checkpoint (2026-10-11):** six final hardware
runs passed: three closes of the sole user descriptor and three sysfs unbinds
while callback/control syscalls were active. Release/removal waited for the
operations; restoration preceded BAR unmapping, and late calls were refused.
All target contexts and full RAM/MU cleanup passed; HTTP restored, no reboot/flash.
An initial truncated removal log was preserved and its publication fixed before
rerunning. [Contract and findings](rtems/switch/LIFECYCLE.md),
[evidence](artifacts/irq-lifecycle-20261011/README.md).
Logical unbind is tested; the later failed-control checkpoint above covers
synthetic omissions during teardown. Physical hot-unplug remains unproven. Task shutdown still cooperates with a stop flag.


**Concurrent host control (2026-10-11):** three card runs passed with STOP
issued by an ioctl on a second host thread while the firmware callback was
pending. A separate control mutex/window is joined before completion/cleanup;
wrong epochs, duplicate STOP and late requests were refused. Both ISR contexts
drained; full RAM/MU restoration and unload passed. IPv6 HTTP restored.
[API and lifetime contract](rtems/switch/CONCURRENT.md),
[evidence](artifacts/irq-concurrent-control-20261011/README.md).
Workers remain stop-aware. Live alias-close coverage is not final-close or
physical-removal fault injection; next are broader lifecycle failure tests and
non-cooperative task containment.


**Live web system information (2026-10-11):** the IPv6 Vader page now shows
card runtime uptime, RTEMS/lwIP and CPU details, memory capacities, HTTP counts
and RX/TX/drop counters. CPU utilization and temperature are explicitly
unavailable; measured timer-bus frequency is not labelled as CPU frequency.
24 live HTTP checks and full cleanup/restart passed. Production module is now
`autonet-module-system-info`, paired with the updated `autonet` image.
[Details](rtems/net/SYSTEM-INFO.md), [artifacts](artifacts/rtems-system-info-20261011/README.md).


**Nested STOP and timeout checkpoint (2026-10-11):** all twelve `stopcases`
card runs passed. STOP at critical depths 2/1 was recorded at ticks 18/30 but
controller dispatch/drain waited until outer release at tick 40. Missing STOP
reached the 128-tick event deadline; missing RELEASE exhausted its finite loop
and returned with only the expected `0x4000` flag. All contexts, guards, paired
RAM/MU restoration and unload checks passed; no reboot/flash. IPv6 HTTP restored.
[Implementation](rtems/switch/STOP-CASES.md),
[evidence](artifacts/irq-stop-cases-20261011/README.md).
Next: concurrent user-control/lifetime design and non-cooperative task containment.
These workers remain stop-aware; deliberate message omission is not a full host
crash or proof of recovery from permanently masked interrupts.


**Pending-callback MU STOP milestone (2026-10-11):** three `mustop` card runs
accepted a one-shot host STOP at ticks 34/41/52 while both owned ISR contexts
were live and firmware sequence 1 was still pending. Workers observed the stop
flag, both contexts drained, and the card acknowledged before host RELEASE
allowed the callback to return. Zero faults; full RAM/MU restoration and module
unload passed. IPv6 Vader HTTP restored. [Evidence](artifacts/irq-mu-stop-20261011/README.md).
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
restart. [Evidence](artifacts/irq-deferral-20261011/README.md).
Next: integrate independent MU STOP with the two CPU-bound task contexts and
prove safe draining during an active callback. Resident operation and general
interrupt nesting remain unproven; production stays on `autonet`.


**Two-task interrupt-switch milestone (2026-10-11):** three bounded card runs
passed timer-driven switching between CPU-bound RTEMS tasks. Each run recorded
32 IRQ-path handoffs, 31 observations of both ISR continuations live, and 16
entries/returns per task. Separate task/ISR stacks, register sentinels, frame
ownership, draining and full restoration passed; web service restored without
reboot/flash. [Implementation](rtems/switch/README.md),
[evidence](artifacts/irq-switch-20261011/README.md). This is bounded preemption,
not a resident monitor; next are deferred-dispatch stress and MU STOP integration
while the CPU-bound task contexts are active.

**Owned ISR stack milestone (2026-10-11):** an owned, guarded C interrupt stack
and explicit GPR/TC preservation passed 126 isolated stress interrupts and 546
bounded RTEMS/control interrupts. Deep call chains, sentinels, PC/TC roundtrips,
frame/guard checks and independent STOP/HALT passed; full cleanup and web restart
passed without reboot/flash. The hardware entry frame stays in place: movable
per-task interrupt contexts and unrestricted preemption remain future work.
[Implementation](rtems/interrupt/README.md),
[evidence](artifacts/owned-interrupt-stack-20261011/README.md).

**Framed control milestone (2026-10-11):** CTL1 messages, retries and invalid-frame
rejection passed over IMR1/OMR1. Independent STOP froze bounded RTEMS at tick 362;
subsequent STATUS confirmed it, then independent timer HALT took 9.48 ms. Firmware
sequence stayed 1 → 1 throughout. Full cleanup passed, without reboot/flash;
Vader service restored. [Implementation](rtems/control/MU-FRAMED.md),
[evidence](artifacts/mu-framed-20261011/README.md). This does not establish
runaway-task STOP or unrestricted preemption. Next: owned IRQ stack and complete
asynchronous context preservation before lowering task interrupt priorities.

**MU echo milestone (2026-10-11):** a timer ISR echoed an IMR1 word through OMR1
in 11.02 ms while firmware sequence stayed 1 → 1. Full timer/RAM/MU restoration
and module unload passed. The first trial retained resources after an incorrect
local OISR acknowledgement; a host reboot and host-side acknowledgement fix
preceded the successful retry. [Implementation](rtems/control/MU-ECHO.md),
[evidence](artifacts/mu-echo-20261011/README.md). Independent STOP and unrestricted
preemption remain unproven; next is framed control plus independent STOP.


The current implementation backlog is [the integrated development plan](DEVELOPMENT-PLAN.md),
including a gap ledger G01–G12 and the next loader milestone M1.

This is the current-state index. Earlier reports and artifact source snapshots
record the state at their own milestone; their future-tense plans are historical.
The earlier preservation audit was read-only. The subsequent RTEMS work loaded
RAM payloads and exercised the card. The later MU cleanup trial required a host
reboot; no additional flash programming or recovery testing occurred.

## Established on this card

| Finding | Evidence and usable implementation |
| --- | --- |
| A complete 512 KiB ROM can be recovered while the card is installed, without an external programmer. | [ROM inventory](artifacts/ROM-INVENTORY.md), original dumps and Fujitsu packages in `artifacts/private-dumps/` and `artifacts/vendor-fujitsu/`. |
| Stock DRAM initialization has been traced, including two candidate board-register profiles; decoded timings in nanoseconds have not been established. | [DRAM analysis](DRAM-ANALYSIS.md). Stock initialization is retained. |
| A stock-preserving patch has been programmed once and validated after reboot. | [Programming result](FIRMWARE-PROGRAMMED.md), paired full readbacks and postboot PING in `artifacts/programmed-rom-20261010/`. |
| The boot-installed `0x6F` dispatch target is `FEFE001C`; PING returns `017E`. Boot straps remain Mode 3. | Postboot paired table reads and calls; this is software extension of stock firmware, not Mode 0 boot. |
| Returning i960 programs can be uploaded and executed after the PC has booted, without further flash writes. | [Software loader](SOFTWARE-LOADER.md), `host/loadrun/`, `loader/runtime/`. Cache invalidation and restoration are part of the protocol. |
| The 64 KiB scalar limit is policy, and a larger RAM profile is already proven. | The initial RTEMS profile uses a 310,772-byte image (the dual-stack revision uses 315,108 bytes) and 471,136-byte prepared upload inside the existing 512 KiB staging window. [Memory limits and extension stages](DEVELOPMENT-PLAN.md#what-can-be-extended-now). This does not establish ownership of the rest of the card's 16 MiB DRAM. |
| BIO1 returns bounded text/frame data; Tetris has an explicit bounded update/render ABI. | [Buffer I/O](BUFFER-IO.md), [Tetris step](TETRIS-STEP.md), `game/`. 4 KiB input, 8 KiB output; Tetris uses 256-byte requests and 2,160-byte responses. |
| Repeated execution and persistent sessions are hardware-tested. | [T3 replay](TETRIS-REPLAY.md): 1,000 + 64 calls. [T5 session](PERSISTENT-SESSION.md): 1,000 frames and a separate 400-frame cadence test. |
| A card-hosted IPv6 HTTP server works. | GET from the Mac to the host global IPv6 port 8080 reached the card through DNAT; bounded HTTP request tests passed. The autonomous service is running for user testing. [Current report](artifacts/rtems-web-autonomous-20261011/README.md). |
| Hardware timer interrupts can wake RTEMS tasks. | Eight interrupts/eight higher-priority task wakeups during a bounded busy-loop experiment; timer/vector/mask and RAM restored. Background execution passed 2,009 ticks/wakes in 20 host-silent seconds; networking advanced 509 ticks in five silent seconds. SIGTERM/SIGKILL/error cleanup passed. |
| IPv6 networking works on the current cooperative RTEMS port. | [Dual-stack implementation and live evidence](artifacts/rtems-ipv6-20261011/README.md): ICMPv6, UDP/TCP, AAAA and IPv6 Internet HTTP through NAT66. Static addressing; DNS transport remains IPv4; fragmentation, SLAAC, sockets and TLS remain gaps. |
| RTEMS Classic tasks and card TCP/IP execute after PC startup. | [Cooperative RTEMS port](rtems/README.md), [exact artifacts](artifacts/rtems-20261011/README.md). Persistent tasks, lwIP ICMP/UDP/TCP, DNS and HTTP through Linux TUN/NAT; clock/progress depend on host polling. |
| Tetris is playable over SSH. | [Terminal instructions](TETRIS-TERMINAL.md), `host/session/`. T4's five automated SSH runs validated 36,380 frames; the 30-minute run contributed 35,846 at 19.91 Hz. |

Original full-ROM SHA256:
`43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93`.
Installed patched candidate SHA256:
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
The unchanged final 16 KiB boot block is part of the programming validation.
The known card is `0000:37:09.1`, `1069:0010`, firmware 4.07-0-29, 16 MiB DRAM.

These hashes identify validated images, not every file called `stage-*` or
`candidate-*`: runtime captures also contain transient RAM overlays. Those
files must not be used as flash images. Historical stock-preimage rehearsals
are expected to reject the now-patched card; do not bypass their pinned hashes.

## Limits and unresolved questions

- General scalar loading is still capped at 64 KiB; BIO1 has a separate 32 KiB
  code boundary. RIO1 supports larger images but is not yet a shared general
  loader profile. Memory outside the staging allocation is unowned for application
  purposes until proved otherwise. See M1–M3 / G12 in the integrated plan.
- Recovery has not been demonstrated. The user excluded recovery testing;
  serial wiring/photos and adapter work remain future work. A spare card does
  not establish that this card is recoverable.
- SSH returned late after programming/reboot. The user reported the PC back,
  but did not confirm a power cycle or explain the delay. Its cause is unknown.
- No RAID disk-I/O compatibility or general production-stability validation was
  performed. Tests used an otherwise idle card with its storage driver unbound.
- DRAM register component identity, bit meanings, clock and timing units remain
  unresolved. Recovered register literals are not a complete timing specification.
- Payloads must return cooperatively; the host cannot preempt a runaway call.
  The RTEMS profile adds explicit BSS initialization, private persistent state
  and three guarded task stacks. The autonomous profiles additionally borrow timer 1 with verified restoration;
  full Newlib/POSIX support and memory isolation are not established.
- Persistent sessions check the full payload/code/input/output region every
  frame, and the entire 512 KiB staging image every 32 calls and at close.
  Corruption outside the per-frame region can remain undetected for 31 calls.
  Uncertain execution/restoration retains resources rather than retrying code.
- SIGKILL cleanup, ownership and many command failures were tested, but real
  hardware command-failure injection and hot unbind were not. Native fault
  simulation is not evidence of every physical failure mode.
- T4's half-hour acceptance run used scripted keys, with game-over periods and
  68 restarts. It is not a human gameplay or uninterrupted-running-game claim.
- RTEMS tasks and host-routed TCP/IP now work in the [cooperative profile](rtems/README.md).
  Bounded background RTEMS and its hardware clock now pass live tests;
  independent host transport and exclusive takeover remain unvalidated. The [integrated plan](DEVELOPMENT-PLAN.md) describes
  those additional gates in A1–A3; a working cooperative session does not satisfy them.

## Preservation and current host observation

The [preservation audit](artifacts/preservation-audit-20261011/README.md) maps
remote files to local files or archive members by SHA256. It preserves missing
historical builds without replacing current source. The exact Linux cross tools
and original source packages are in [the toolchain archive](artifacts/toolchain-20261011/README.md).
Root `toolchain.sh` remains the build recipe. Kernel modules are specific to
`6.8.0-138-generic`; historical binaries are evidence, not automatically safe
programs to run on a different card or kernel.

At the start of the October 11 audit a separate terminal session was running
under `/home/mit/i960-tetris-t4/sessions/20261011-000116/`, PID 17974, on the
same boot `a9429ca4-0144-452d-8a80-7189608ce99b`. It was left untouched.
The previous test's “driverless/module unloaded” result describes its cleanup,
not the machine while this new session is active. See the audit for collection
status; unfinished traces do not prove final restoration or module unload.

That session subsequently exited normally during the audit. Its complete archive
and independent validation are now preserved: 2,224 native-matching frames,
111.387 seconds, successful RAM restoration and unload. The final host snapshot
again showed no DAC960 module or bound controller driver, on the same boot.
This session is additional to the five scripted T4 acceptance runs.


The subsequent [RTEMS implementation](rtems/README.md) completed a separate
half-hour TCP test: 29,352 callbacks, 4,430 exchanges and 18,896,608 exact echoed
bytes. Independent checks covered 918 saved RAM audits and 45,267 IP packets.
Task-stack guards and full close restoration passed. Final rebuild tests also
covered explicit fatal return, SIGTERM and established-session SIGKILL cleanup.
The original firmware's vectors/timers and flash remain unchanged by this work.

A final Tetris SSH regression after RTEMS matched all 204 frames against native
C and restored terminal settings/RAM before unloading. The RTEMS foreground
service also passed twelve sequential TCP connections and UDP.

## Preemption and DMA roadmap (2026-10-11)

See the [staged preemption and DMA plan](RTEMS-PREEMPTION-DMA-PLAN.md). Order: independent control
and ownership prerequisites → arbitrary application-task preemption → host-RAM
DMA networking → gated direct peer experiments. Read-only direct-DMA research
has started; current NIC and Mylex occupy separate PCI branches. This is a plan
and initial inventory, not implemented preemption or verified peer DMA. Keep
the active web service on the existing bounded runtime.

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
