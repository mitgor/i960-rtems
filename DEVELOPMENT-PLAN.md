# Integrated plan: loader memory, RTEMS and remaining gaps

Updated 2026-10-11. This is the current implementation backlog. Read
[CURRENT-FINDINGS.md](CURRENT-FINDINGS.md) for evidence, not future promises.
The working baseline is commit `4eb6133`; preserve its binaries and captures.
This planning update performs no hardware operations.

## What can be extended now?

**Yes: 64 KiB is a policy/linker limit, not an established i960 or firmware
transfer ceiling.** The scalar loader enforces it in
[policy.h](host/loadrun/policy.h) and [payload.ld](loader/runtime/payload.ld).
Its uploader already loops over bounded chunks. Increasing total image size
must not increase a single command beyond its existing `0xF000`-byte limit.

The RTEMS implementation has already demonstrated a larger, distinct profile:
310,772 bytes of linked image, prepared as a 471,136-byte RIO1 upload, with
persistent writable state and explicit BSS initialization. This ran through
29,352 calls in the half-hour test. It is evidence for extending the general
loader **within the established staging allocation**, not permission to write
any of the card's reported 16 MiB.

There are several different limits; do not call all of them “payload size”:

| Profile / quantity | Current value | Meaning |
| --- | --- | --- |
| Scalar returning loader | 64 KiB | Flat image cap; linker rejects implicit BSS; uses the existing call environment |
| BIO1 / Tetris code | 32 KiB before fixed I/O | BIO1 starts at image offset `0x8000`; simply raising the scalar cap cannot move it |
| RIO1 immutable code/rodata reservation | 128 KiB | Entry must be in this region; includes any padding |
| RIO1 private writable reservation | 327,648 bytes (320 KiB minus 32 bytes) | Data, BSS, RTEMS workspace, heap and task stacks share this budget |
| RIO1 maximum flat image extent | `0x6FFF0` = 458,736 bytes | End before upper guard; not all executable text or application heap |
| RIO1 prepared upload extent | `0x73060` = 471,136 bytes | Includes fixed I/O and guards at/after offset `0x70000` |
| Session snapshot/restoration | 512 KiB | Whole staging image; bytes after the prepared upload remain unchanged |
| Extra staging allocation block | 8 KiB | Contains borrowed runner/result slots and other reserved bytes; not a free extra heap |
| Reported installed DRAM | 16 MiB | Includes firmware-owned state; usable application size outside staging is unproved |

RIO1 offsets relative to `C0F2C000` are half-open intervals:

```text
00000..20000  immutable code / rodata / padding
20000..20010  lower guard
20010..6FFF0  private persistent data / BSS / heap / stacks
6FFF0..70000  upper guard
70000..73060  RIO1 request / response / guards
73060..80000  untouched remainder, covered by full staging audits
80000..82000  extra allocation block: existing runner/result reservations
```

A flat binary's extent includes gaps and zero-filled BSS in this build. It is
not a measure of useful code size, nor of remaining free RAM. Link maps and
separate memory budgets must accompany every larger-image claim.

## Order and dependencies

1. **M1: generalize the already-proven larger profile.** This is the next task.
2. **R1: improve cooperative RTEMS observability and application support** on M1.
3. **M2: optional layout rebalancing inside 512 KiB**, driven by R1 measurements.
4. **R2: RTEMS network OS adaptation / socket support**, only if applications
   need it; it need not wait for autonomous execution or multi-megabyte RAM.
5. **M3: survey and establish additional RAM ownership**; its read-only research
   can run alongside R1/R2. A usable reservation must precede any large load.
6. **A1–A3: independent transport, explicit ownership transfer and autonomous
   RTEMS**, with the recovery/failure gates below. These are a separate track.

M1 → R1 → R2 is the practical cooperative route. M1 → M2 increases flexibility
without new memory ownership. M3 can produce a stock-compatible reservation;
if it cannot, multi-megabyte loading instead depends on A1/A2 quiescence and an
owned memory map. A3 depends on that ownership and independent communication.
A larger payload alone never enables preemption or removes the callback timeout.

## M1 — Supported general loader profile above 64 KiB

**Goal:** make today's RTEMS memory capability reusable without silently changing
scalar/BIO1 behavior. No new flash patch, new address range or interrupt work.

- Define a shared versioned profile description for base, image extent, entry
  region, immutable regions, writable regions, I/O, guards, runner and result.
  Generate/validate host C policy, Python framing and linker constants from it;
  replace fragile scattered substitutions where appropriate. Keep existing
  scalar64, BIO1 and RIO1 profiles distinguishable and reject mismatched clients.
- Expose the existing RIO1 layout as an opt-in general persistent-runtime
  profile. Its first implementation should retain the proven addresses and
  limits exactly. Preserve Tetris's ABI, CLI defaults and artifacts.
- Specify startup, BSS zeroing, stack ownership, persistent state and a bounded
  return ABI. A larger image does not grant a larger firmware stack: provide
  an explicitly reserved guarded stack before accepting larger stack usage.
  Retain the known runner and restore its borrowed state.
- Add an image manifest with target/profile identity, entry, initialized ranges,
  zero-fill ranges, stack/heap reservations, extent and digest. Initially build
  it from linked ELF on the host; continue loading validated flat images rather
  than adding a target-side ELF parser. Reject overflow, overlaps, loads into
  reserved regions, wrong endianness/machine and entries outside code. Enforce
  immutable regions during execution, after the validated initial upload.
- Review every bound together: CLI checks, firmware request allocation, kernel
  load policy, upload/read loops, cache handling, response validation, snapshots
  and linker assertions. Preserve `0xF000` chunking, exclusivity, no execution
  retries, failure pinning and complete final restoration.

**Acceptance:** native boundary/failure tests plus live images around 64 KiB,
including an executed function beyond offset `0x10000`, not just padding there.
Exercise initialized data and BSS on both sides of chunk boundaries; keep entry
inside the permitted code area. Test the largest valid layout with guard checks,
then reject over-limit/wrong-profile/overlapping images before a card command.
Run large persistent state, explicit fatal return, process-exit cleanup and
scalar/BIO1/Tetris/RTEMS regressions. Verify all borrowed bytes on close.

**Deliverables:** shared profile/manifest specification, a general returning
large-image example, generated policy/linker inputs, build commands, exact
binaries and captures. Name it a RAM loader profile, not a flash image format.

## R1 — Make cooperative RTEMS easier to develop and diagnose

**Existing baseline:** Classic task switching, simple semaphores, message queues,
software ticks, guarded stacks, raw lwIP, routed DNS/HTTP and cleanup all passed.
Do not spend the next milestone rediscovering that baseline.

- Add a bounded console/control protocol with kernel/application version,
  task states, heap/queue usage, per-task stack observations, fatal code and
  supplied-time counters. Keep control/console responsive under network load.
- Budget each allocation explicitly. The current network profile permits two
  application tasks plus idle, with three fixed guarded stacks; increasing task
  count requires changing the allocator and RTEMS configuration together.
- Add representative application workloads, simultaneous task/network/console
  stress, queue/heap exhaustion tests and explicit output truncation reporting.
  Stack canaries/high-water samples remain measurements, not worst-case proofs.
- Specify host stalls and disconnect behavior: RTEMS pauses without polling;
  capped catch-up must not turn one callback into unbounded work. Test short and
  long polling gaps, tick accounting, reconnect as a fresh session, and task
  state reset. Do not advertise resume after process death without new evidence.
- Make network addressing/DNS configurable through a validated configuration
  rather than unrelated host/target constants. Preserve scoped gateway rules,
  journal cleanup, per-run captures and rejection of conflicting routes.
- Audit cleanup at each gateway setup/teardown boundary. The established-session
  SIGKILL test does not cover every rule-install/journal-write interval. Test
  simulated failures first; record pre-existing TCP retransmissions separately
  from newly established streams, as the final capture required.

**Acceptance:** deterministic console/task checks, bounded clock catch-up,
exhaustion without loss of control, repeat start/stop cycles, injected packet
loss/backpressure, exact TCP data, then a longer mixed-workload soak with paired
readbacks and a clean close. Pick duration/traffic from measured limits; the
existing 30-minute run is a baseline, not production qualification.

## M2 — Rebalance the known staging window when measurements justify it

The current fixed layout gives 128 KiB to immutable code and about 320 KiB to
private writable state. More text can be obtained by reducing writable space;
more heap can be obtained only from an explicitly smaller code/other budget.
The fixed RIO1 block and untouched tail are not automatically spare application
memory. Changing them is a new profile/protocol with new verification.

First generate a link-map budget report and demonstrate which section is the
actual constraint. If needed, introduce an additional fixed, versioned layout
with a reviewed code/data boundary and matching guards. Consider separating
file bytes from zero-fill memory extents to reduce transfer size; this improves
loading efficiency, not total owned RAM. Defer general ELF loading until there
is a concrete benefit over a host-validated manifest.

**Acceptance:** full region/overflow tests, maximum-size live image, writes at
each writable boundary, immutable-code corruption rejection, explicit guarded
stack/heap limits, cache visibility and all M1 regressions. Full verification is
the default. Any reduced audit frequency is a separate measured tradeoff with
its detection delay stated explicitly; do not trade away checks just to fit.

## R2 — RTEMS-integrated network APIs and runtime completeness

Keep the working lwIP 2.1.3 raw/`NO_SYS=1` profile as a baseline. For applications
that need blocking networking, implement an RTEMS `sys_arch` with a dedicated
lwIP task, mailboxes, semaphores, time conversion and correct protection rules.
Audit waits carefully: a cooperative session must still have a runnable path
back to firmware. The current fatal-on-idle hook is not a general OS idle loop.

Stage delivery: mailbox/timeout tests → inter-task packet exchange → netconn
APIs → sockets only after libc, errno, descriptors and reentrancy are defined.
Inventory missing libc/libgcc facilities and supply only the selected support
with tests; Newlib headers plus current freestanding helpers are not full Newlib.
Keep integer-only applications as the supported baseline until FP support is
separately implemented and validated.

**Acceptance:** multiple clients/tasks, blocked calls/timeouts that still yield
to the host, queue/PCB exhaustion, connection churn, loss/retransmission,
console responsiveness and complete session cleanup. Record code/RAM growth
against M1/M2 budgets. TLS remains a later milestone requiring a suitable
library, real entropy, time/certificate policy and memory/performance evidence;
HTTP success and the deterministic current PRNG do not satisfy those needs.
IPv6 is now implemented and live-tested in the existing RIO1 allocation; see
[IPv6 evidence](artifacts/rtems-ipv6-20261011/README.md). Static dual-stack
addressing, AAAA lookup and NAT66 Internet HTTP work; DNS transport is IPv4.
IP fragmentation/reassembly and larger HTTP response storage are optional
application-driven extensions, each requiring explicit memory/MTU bounds and
negative/interop tests; they are not prerequisites for M1 or the current IPv4
service. Keep them marked unsupported until such tests pass.

## M3 — More RAM than the current staging allocation

**Research first:** reconcile firmware allocator boundaries, allocation/free
paths, stack/vector/queue locations, staging lifetime, SCSI/DMA engines and
address aliases. Use existing firmware analysis and bounded read-only captures.
Zero-looking memory is not free memory; a read/write pattern is not ownership.
Do not change DRAM initialization to obtain this result.

Choose one route based on evidence:

- **Stock-compatible reservation:** prove a callable allocator/reservation
  contract, cache behavior and lifetime across callbacks, including error and
  shutdown paths. Prove firmware cannot free/reuse or DMA into the reservation
  while it is borrowed. If this cannot be established, do not proceed with it.
- **Exclusive ownership:** after A1/A2, stop relevant firmware work/DMA and
  reserve boot state, monitor, transport, vectors and stacks before claiming
  remaining DRAM. Account for actual memory decoding and aliases; subtract all
  reservations from installed RAM. Neither 16 MiB usable nor a particular
  multi-megabyte target is promised in advance.

Only then perform bounded pattern/alias tests in the owned region. Expand in
stages, for example toward a 1 MiB image first if the resulting map permits it.
Extend address validation, snapshots/restoration where meaningful, cache rules,
Linux resource lifetime and transfer accounting to cover every new region.
A firmware-owned live region cannot safely be “restored” from a stale snapshot.

**Acceptance:** documented ownership/lifetime and usable map, verified loads and
execution across the old staging boundary, heap/stack stress, fault paths,
no alias into monitor/firmware state, and a demonstrated release or reset path.
Report file size, image extent, private heap and remaining RAM separately.

## A1–A3 — Autonomous RTEMS track

**2026-10-11 completed intermediate milestone:** `irq` proved eight hardware
interrupts/eight task wakeups during a busy loop. `auto` proved 2,009 ticks and
wakeups in 20 host-silent seconds. `autonet` proved 509 ticks in five silent
seconds plus IPv6 Internet HTTP, dual-stack echo and a minute of IPv6 stress.
The pinned transport stops timer 1 before restoring RAM, including live SIGKILL
and application-error cleanup. See [evidence and failed trials](artifacts/rtems-web-autonomous-20261011/README.md).
This stock-coexisting, bounded runtime does not complete the independent
transport, exclusive handoff or unrestricted BSP gates below.

**A1, independent communication:** audit RP registers/BAR/translation ownership;
prototype bounded polled control, console and packet exchange without depending
on stock `20/21/6F` servicing. The 8 KiB BAR is not an arbitrary DRAM mapping.
Prove coexistence/visibility first, then preserve transport across handoff.
Add sequence/credit/reset semantics and priority for control traffic. Start
without host-memory DMA; add it only with explicit mapping, cache and lifetime
proof. Reuse the tested TUN gateway and card stack where possible.

**A2, monitor and ownership transfer:** build a small monitor in an established
reservation. Audit/quiesce DMA, SCSI work, interrupts and watchdogs. Make handoff
an acknowledged transition with a new ready state and explicit host resource
ownership, not a timed-out firmware command whose error is ignored. Establish
M3's exclusive map if the allocator route was unavailable. Stock return after
this transition is a new proof obligation, not inherited from callback cleanup.

**A3, autonomous DAC960PG BSP:** preserve known DRAM startup; audit/replace the
historical port's raw vector pointer handling, interrupt-level operations,
shared ISR save area, stale symbol references and board-specific clock writes.
Measure timer frequency. Implement fault reporting, interrupt stacks and
register-window preservation before enabling hardware ticks/preemption.

**Gates:** monitor heartbeat and bidirectional console → owned RAM/load → task
switching → calibrated tick/timed sleeps → nested-interrupt/context tests →
network plus console under scheduler stress → disconnect/reset tests and soak.
A proven exit/reset route and an explicit recovery/risk decision precede live
exclusive takeover or fault injection that could wedge the card. Recovery work
remains excluded under the existing user direction; keep offline analysis and
cooperative milestones moving while that gate is parked. A spare card does not
prove recovery of this one. No new flash change is required for M1/R1/M2/R2.

## Gap ledger from CURRENT-FINDINGS.md

| ID | Unresolved point | Work / evidence needed | Dependency or status |
| --- | --- | --- | --- |
| G01 | Recovery not demonstrated | Preserve originals; serial wiring/boot-block/reset procedure and an observed recovery test if reopened | Deferred under user direction; A2/A3 risk gate, not an M1 blocker |
| G02 | Delayed SSH return after programmed reboot | Collect console/boot logs at a future observed boot; distinguish firmware, Linux and network delay | Cause remains unknown; do not reboot just to amend a narrative |
| G03 | No RAID I/O coexistence / production qualification | First audit arbitration, staging ownership, DMA and binding; only later design a disposable-media I/O test with a defined data-safety scope | Current applications retain exclusive idle-card use; no concurrent storage claim |
| G04 | DRAM component/register/timing decode incomplete | Board photos/markings and firmware/register analysis; derive clocks/units from evidence | Independent research; retain stock initialization throughout initial work |
| G05 | Runaway callbacks / no hardware preemption | Bound application work in R1/R2; A1–A3 for a hardware-clock runtime and independent control | A host timeout cannot stop executing card code |
| G06 | Stack, heap, BSS and OS-runtime limits | M1 manifest/startup/stacks; R1 accounting; R2 libc/sys_arch | Partly solved in RTEMS only, not automatically in the scalar ABI |
| G07 | Delayed detection outside per-step checked regions | M1/M2 explicit immutable/writable classification; measure optional full-audit mode and its cost | Existing full staging audit every 32 steps plus close remains baseline |
| G08 | Physical command failures and hot unbind untested | Extend native fault simulation first; design limited live cases with an exit/reset route and pinned DMA ownership | Successful SIGKILL cleanup is not proof of arbitrary DMA/command failure safety |
| G09 | Scripted Tetris evidence is not human play or production soak | Optional interactive feedback and broader endurance workload, keeping labels accurate | Not a blocker for loader or RTEMS development |
| G10 | Autonomous transport, interrupts and timers absent | A1–A3; historical ISR/BSP audit and measured clocks | Separate from already-working cooperative RTEMS/TCP/IP |
| G11 | Network/libc feature gaps and hardcoded configuration | R1 configuration/diagnostics; R2 sys_arch/APIs; later TLS/entropy if needed | Raw IPv4/IPv6 HTTP works; sockets/TLS/fragmentation and IPv6-only DNS remain gaps |
| G12 | General loader remains 64 KiB / larger memory ownership unknown | M1 supported larger profile; M2 optional rebalance; M3 new reservation | Larger RIO1 profile proven; arbitrary multi-megabyte loading unproved |

## Evidence and completion rules

Every implementation milestone supplies source/build/profile identities, link
maps, raw and prepared image hashes, exact modules, native checks and its live
captures under a new dated artifact directory. Include failed experiments and
why they failed. Re-run applicable scalar/Tetris/RTEMS regressions after changes
to shared transport or memory policy; packet captures and native oracles provide
independent checks. Verify full restoration or clearly record retained ownership
when cleanup cannot be proven. Preserve the current working binaries separately.

Update CURRENT-FINDINGS.md when evidence changes, this plan when dependencies
change, and Claude guidance when the operational contract changes. Keep one
current roadmap; historical reports remain evidence for their own dates.

**Next concrete deliverable: M1's shared memory-profile/manifest specification,
generated validation/linker constants, and an opt-in >64 KiB returning example,
followed by its boundary tests and card validation.** No M3 memory claims or
interrupt takeover should be bundled into that first change.
