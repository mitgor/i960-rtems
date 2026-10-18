# DAC960PG → AcceleRAID 160 RTEMS feature port

## Latest P3b checkpoint — recovery complete, prompt restored

Both hardware exception tests and both post-reset firmware pairs passed.
Normal mode 0 is restored on boot `aea81f51-24ce-493b-a7d2-114195611d5b`,
with one 64-frame game, verified idle and 577 successful console exchanges.
Leave this owner live for the user's prompt. Next is normal runtime with owned
vectors/ISP; mode 0 remains software-only. Active-DMA fault containment and
engine exclusion are still separate open gates. Earlier entries are historical.

## Latest P3b checkpoint — both hardware exception tests passed

Actual `faulte` and actual MU-doorbell NMI passed with stable raw terminal
records, owned table/NMI/ISP, guards and retained resources. Mode 3 reset
recovery is closed; mode 4 recovery and normal prompt restoration follow its
final reset. The accepted mode-0 prompt remains software-only. Normal runtime
with owned ISP, active-DMA containment and engine exclusion remain open.
See [current evidence](../../artifacts/current/accele160-exceptions-20261018/README.md).
Earlier checkpoints below are historical.

## Latest P3b checkpoint — actual fault test passed

Mode 3 passed on Accele160: exact hardware fault/IP, owned vectors/table/ISP,
guards, stable record and STOP resource retention. Paired guarded firmware reads
close the prior normal-runtime reset. Mode 3 recovery and real NMI mode 4 are
still open; mode 4 is built and archived for the next fresh boot. Prompt offline.
See [current evidence](../../artifacts/current/accele160-exceptions-20261018/README.md).
The earlier checkpoints below are retained as history.

## Latest P3b checkpoint — awaiting physical recovery

The owned fault/NMI candidate is implemented and passes native tests; on-card
qualification has not begun. The previous normal prompt was shut down cleanly,
its raw STOP evidence saved, and the subsequent reset left SSH unavailable.
Rebuild current source after recovery: the archived first mode-3 build predates
additional checks and the real-NMI host path. Modes 3 and 4 install ownership;
mode 0 remains software-only and must not be described as owned-fault coverage.
See [owned exception design and exact resume sequence](../../rtems/accele160/fault/OWNED-EXCEPTIONS.md)
and [evidence](../../artifacts/current/accele160-exceptions-20261018/README.md).
Earlier live-session status below is historical.

Planning baseline: 2026-10-18. The original review used existing evidence;
the checkpoints below record subsequent implementation and physical tests.

## P1/P2 implementation checkpoint

[The service batch](../../artifacts/current/accele160-service-20261018/README.md)
now contains an opt-in kernel and host prompt. Two 64-frame games, rearm,
card protocol tests and global STOP passed; the accepted kernel and complete
captures are archived. The corrected host then passed a fresh-boot physical
follow-up through startup, 64 frames and audited idle, with clean oversized-line
EOF and bounded abandoned/slow clients. The first run's post-reset firmware pair
matches. P1/P2 diagnostic service acceptance is complete. Its follow-up owner
later shut down and passed reset checks during P3; the current prompt is the
mode-0 owner described below. The default installed Doom/CHIP-8 bundle is not
promoted.

## P3a checkpoint — both terminal tests passed

[Software terminal diagnostics](../../rtems/accele160/fault/README.md) passed
both physical tests: explicit fatal and deliberately corrupted private guard,
with stable records, stale-trigger refusal and retained resources after STOP.
Both terminal tests' post-reset firmware pairs are now closed. The mode-0
normal profile ran two 64-frame games, audited idle/rearm and console traffic;
the prompt is restored and its owner left running in verified idle. The live
mode-0 session's global STOP/reset qualification is still separate.
[Evidence](../../artifacts/current/accele160-fault-20261018/README.md).
Hardware fault/NMI ownership and engine exclusion remain further P3 gates.

## Goal and current evidence

Turn the AcceleRAID's application-specific, reusable RTEMS runtime into a
multi-service platform with a host-accessible prompt, general application
loading, owned shared memory and card-side IPv4/IPv6. Preserve the accepted
Doom path and the DAC960PG implementation as independent build profiles.
Exclusive, reboot-only ownership is the initial target. Stock/RTEMS coexistence
remains a separate future track, not a prerequisite.

The old introductory new-board notes are historical. The new card already has
hardware ticks, preempted tasks, a qualified upper-bank arena, DMA frames,
persistent Doom and engine-only stop/reload. Do not repeat initial bring-up or
claim those features are absent. Conversely, a Doom-specific success does not
qualify an arbitrary task, allocator or network service.

| Capability | DAC960PG reference | AcceleRAID baseline / remaining port |
| --- | --- | --- |
| RTEMS core and clock | RTEMS 4.6.6, owned interrupt continuations | Already present; generalize task/ISR ownership beyond fixed Doom owners |
| Persistent application lifecycle | Resident workers, upload and cancellation | Persistent Doom plus audited idle/rearm exist; general application lifecycle is missing |
| RAM | Validated exclusive 12 MiB layout; 8 MiB application arena | Verified 8 MiB upper bank, with guarded application interval `c0810000..c0ff0000`; do not copy PG's 12 MiB grant |
| Allocation | Guarded general heap, shared references/pins and cancellation | Engine/zone/frame allocation exists; general shared-service heap and cancellation need integration |
| Loader | Segmented image core, resident upload and versioned runtime ABI | Operation-13 bootstrap and relocated Doom admission exist; general resident upload/service ABI remains |
| DMA | Frame and WAD transports with ownership gates | Channel-0 frame DMA, held-host and finite drain gates exist; generic packet/input DMA remains |
| Network | lwIP 2.1.3 raw API, host-backed IPv4/IPv6, HTTP | Browser HTTP currently runs on Linux; card-side IP stack/packet relay is a port |
| Fault containment | Exclusive NMI/fault records and resource retention | Local fatal/guard paths exist; comprehensive board-specific fault ownership needs audit and qualification |
| Command prompt | No general interactive shell established | New shared feature for both boards, not a finished PG component to copy |

Evidence: [persistent Doom](../../artifacts/current/doom-persistent-20261018/README.md),
[rearm](../../artifacts/current/doom-rearm-20261018/README.md),
[current launcher](../../game/doom/play/accele160/README.md),
[DMA contract](../../rtems/accele160/doom_dma/README.md),
[arena](../../rtems/accele160/ARENA.md),
[PG shared heap](../../rtems/residentnet/SHARED-HEAP.md),
[PG upload](../../rtems/residentnet/UPLOAD.md), and
[PG fault ownership](../../rtems/residentnet/FAULT-OWNERSHIP.md).
The closed 1,058-frame persistent gate includes its post-reset flash pair;
newer bundles must retain their own explicit pending/closed status.

## Architecture and boundaries

Reuse algorithms and protocols, not register constants, old-board binaries,
linker maps or Linux ioctl numbers. Keep board operations explicit: clock,
interrupt entry/exit, cache maintenance, admitted ranges, sideband exchange,
DMA submit/completion and terminal retention. Do not refactor every historical
experiment; extract only code exercised by the new service profile.

Keep one Linux hardware owner. SSH terminal clients, network relay and browser
clients connect to that supervisor; they do not open competing card sessions.
Control/STOP and heartbeat must remain serviceable during upload, network load,
frame ACK waits and full audits. Snapshot reads remain serialized consistently.

The current kernel map starts at `c0710000`, bounds text/data/BSS below
`c0724000`, reserves four IRQ stacks through `c072c000`, and places the entry
stack next. Staging starts at `c078f000`. These are constraints to re-budget,
not permission to place a larger kernel into apparent padding. Keep the active
bootstrap, ISR/entry stacks, descriptors and control pages out of reclaimed RAM.
The accepted private cache template covers the upper 8 MiB; all CPU/host/DMA
producer-consumer transitions must retain the appropriate invalidation and
visibility rules. Pins establish lifetime, not cache coherence or mutual exclusion.

## Ordered implementation gates

### P1 — Freeze the service baseline and ownership map

Create an opt-in AcceleRAID service build from the accepted reusable runtime.
Record source revision, firmware/engine/kernel/module hashes, exact board identity,
link map, all task/IRQ owners, callbacks, DMA channels, cache mappings and RAM
ranges. Confirm the current live owner before any physical work. The old card
may be physically absent; preserve strict target selection rather than requiring
its presence or assuming both cards can run together.

Acceptance: reproduce the selected baseline, run existing native validators,
and repeat idle → application → idle → application → global STOP with its full
paired audits. Keep installed Doom unchanged until this candidate passes.

### P2 — General control channel and minimal command prompt

Add a versioned, length-bounded request/reply channel using the independently
accessible sideband, with epoch, sequence, operation, status and output chunks.
Add a bounded RTEMS command worker and a host terminal client, multiplexed by
the existing supervisor. Start with `help`, `version`, `uptime`, `tasks`, `mem`,
`apps` and `stats`. Read-only snapshots come first; no arbitrary memory writes,
jump command or forced task deletion. This is a small diagnostic interpreter,
not Bash or a claim that RTEMS's standard shell/POSIX I/O is already ported.

Acceptance: actual card-produced output over SSH while idle and while Doom
runs; stale/duplicate/oversized requests, slow readers, disconnect/reconnect,
output overflow and simultaneous STOP. Bound per-command work and queue space;
measure response latency and maximum IRQ gap under full audits. A lost terminal
client must not kill the supervisor or change ownership.

### P3 — Board fault and hardware ownership coverage

Audit every enabled timer/interrupt/fault/NMI path against the 80303 board and
current stock handler. Port the PG terminal-record/retention policy only after
mapping the new board's vectors, registers and live stacks. Account for all
three DMA channels and SCSI/cache/other bus masters; an idle snapshot alone is
not proof of permanent engine exclusion. Add deterministic terminal diagnostics
outside reclaimable memory, readable without calling failed application code.

Acceptance: controlled faults and guard corruption in isolated runs, full
surviving record validation, no return into overwritten stock state, no unsafe
unpin, then verified reset recovery. Interrupt-enabled deadlines do not prove
recovery from permanently masked interrupts; independent watchdog recovery
remains a separate hardware research gate.

### P4 — General task ownership and cancellation

Replace fixed application assumptions with bounded task records containing
identity/generation, stack/IRQ lifetime and resources. Reuse PG cancellation and
resource-dependency policy, including the worker-arrival barrier from
`rtems/exclusive/worker_stop.h`. Separate application STOP, service shutdown,
terminal containment and engine rearm. Preserve old IRQ owners until their
saved continuations drain; never suspend a resource holder and free its objects.

Acceptance: two synthetic apps plus the controller; STOP during nested critical
sections, shared-resource use and IRQ preemption; stale STOP, deadline, final
close and failed-control paths. Prove either complete drain or explicit retained
ownership. Start with bounded task counts; unrestricted arbitrary task creation
is not implied by this gate.

### P5 — General heap, workspace and stack budget

Port the board-independent arena/heap policy and shared handle/ref/pin contract
from `loader/segmented` and `rtems/residentnet`. Assign separate budgets for
kernel workspace, task/IRQ stacks, packet queues, console and applications.
Derive addresses from the new linker manifest; keep Doom's contiguous zone
requirement and the upper-bank exclusions. Expand kernel placement only after
protecting the bootstrap and proving all newly used intervals. Do not promise
10–12 MiB of new-board ownership based on PG evidence.

Acceptance: allocation/reallocation/alignment/exhaustion, fragmentation, stale
handles, shared cancellation while pinned, deliberate metadata/redzone failure,
repeated app reload and final zero-live-object accounting. Measure allocation
latency and maximum IRQ masking. If Doom + services do not fit, reduce explicit
budgets or qualify more RAM as a separate experiment; never silently overlap.

### P6 — General resident segmented upload and application ABI

Reuse the PG segmented loader's validation and the new card's exact admission,
relocation and cache handling. Define board/ABI versions, declared segments,
entry/BSS/stack bounds, imports and capabilities. Add bounded begin/chunk/verify/
commit/query/abort operations through the single supervisor. Keep the currently
running service and loader outside upload destinations. Reload from pristine
image bytes with zero BSS after retired references/IRQ contexts are gone.

Acceptance: load two different small apps without flash or reset, get text
output, cancel one and reload; reject overlaps, wrong-board images, unsupported
imports/relocations, bad checksums and stale epochs. Test interrupted uploads,
STOP at each phase and no jump into a partially admitted image. Retain resources
on uncertain completion. Application code remains trusted in one address space.

### P7 — Card-side IPv4/IPv6 over bounded PIO

Port `rtems/net` and the resident packet queue behind a new-board transport.
Start with one task owning lwIP and its timers. Current settings are `NO_SYS=1`,
with sockets/netconn disabled: preserve the raw API instead of assuming BSD
sockets or calling lwIP concurrently from multiple tasks. Add a Linux TUN relay
inside/coordinated with the hardware owner, with bounded queues and explicit
packet ownership. Use static test addresses and routes first.

Acceptance: IPv4/IPv6 ping, UDP, TCP HTTP served by the card, outbound traffic
and DNS as supported by the existing stack; malformed/oversized packets, queue
pressure, packet loss and relay reconnect. Compare response bodies with card
counters to distinguish RTEMS HTTP from the host browser server. Full snapshots,
console and application STOP must remain responsive under traffic. Internet
routing and public IPv6 reachability are separate host/router configuration gates.

### P8 — Multiplex networking, console and applications

Integrate fair per-service budgets, bounded audit groups, packet draining and
upload/frame progress in the supervisor. Keep the stack's single-owner model;
other tasks exchange messages instead of directly entering lwIP. Expose queue
drops, high-water marks, deadlines, task progress and IRQ latency via the prompt.

Acceptance: Doom plus dual-stack HTTP/UDP plus console commands and attempted
upload/cancellation. Reject incompatible operations explicitly. Record baseline
and stressed frame latency, network latency, command latency and IRQ gaps.
Set numerical pass limits from P2/P7 measurements before the acceptance run;
do not extend deadlines merely to hide starvation.

### P9 — DMA packet/input acceleration, after PIO correctness

Adapt channel-0 ownership to packet or WAD input only when its direction,
descriptors and coherent host windows are separately validated. Arbitrate with
frame output; channels 1/2 are not free just because unused by this application.
Use epoch/generation completions, bounded descriptors, guard regions and explicit
source/destination reuse rules. Preserve a PIO comparison path.

Acceptance: byte-exact PIO/DMA comparison, stale completion, backpressure, STOP
while active, owner death and finite timeout. A genuinely stalled/erroring DMA
transaction retains pins until proven reset/drain. Measure actual throughput and
CPU/IRQ cost before enabling by default. Direct Mylex↔NIC DMA is separate research.

### P10 — Persistent service lifecycle and recovery qualification

Generalize accepted engine idle/rearm to the qualified app set. Keep a single
session epoch and distinguish client reconnect from adopting a dead hardware
owner. Test idle and active heartbeat loss, SIGTERM, SIGKILL, browser/terminal
loss, failed control during teardown and blocked DMA completion. Global STOP
remains terminal/reset-only unless a separate return-to-stock proof is accepted.

Acceptance: resources are demonstrably drained or retained, never accidentally
reused. Collect evidence before reset; verify paired post-reset stock flash and
fresh boot ownership. A missing SSH return requires physical recovery, not an
automatic claim that reset succeeded. Preserve the PG coexistence route separately.

### P11 — Endurance and release bundle

Run staged 10-minute, one-hour, then eight-hour mixed workloads only after prior
gates pass, with periodic full audits, repeated app stop/reload and bounded log
retention. Track allocation/reference/stack/queue trends and packet/frame losses.
Archive exact binaries, linker maps, source manifest, module/firmware identities,
raw captures, replay/tamper results and reset evidence under a fresh dated artifact.

Acceptance: no unexplained resource growth, guard change, lost ownership or
missed control bound; native replay and on-card checks both pass. Update current
findings, agent guidance and reproduction docs with exact limits before promoting
an installed bundle. Historical captures remain immutable.

### P12 — Optional OS facilities after core parity

Consider a richer shell, host-backed read-only files/VFS, standard descriptors,
wall-clock synchronization and socket/POSIX adapters based on application needs.
These are additional features, not existing PG parity requirements. First audit
which RTEMS 4.6.6 components are actually built and supported by the pinned i960
Newlib port. A modern RTEMS upgrade, writable block filesystem, audio, independent
watchdog, arbitrary process isolation and direct NIC driving are separate projects.

## Dependencies and recommended first batch

Critical path: **P1 → P2 → P3/P4 → P5 → P6/P7 → P8 → P10 → P11**.
P9 is optional acceleration after P7/P8; P12 follows a usable service baseline.
P3 and P4 can be prepared independently, but hardware work remains serialized.
Full P6 upload is not required to statically link the first P7 network prototype.

Start with P1 and P2: freeze the current reusable image, inventory its owners,
add read-only command/reply messages, and prove `help`, `uptime`, `tasks`, `mem`
and `stats` during real Doom play without degrading STOP or audits. This gives
the requested RTEMS prompt early and instrumentation for the remaining ports.
Do not start by reflashing, replacing the working kernel wholesale, or extending
RAM ownership. Subsequent batches should close one ownership/transport gate at
a time rather than treating all eleven implementation stages as one card run.
