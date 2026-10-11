# Repository guidance for Claude Code

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


**Current work (2026-10-11):** card-hosted IPv6 HTTP and stock-coexisting autonomous RTEMS now pass live tests. A hardware timer delivered 2,009 ticks/task wakeups during 20 seconds without host polling; the network build advanced 509 ticks during five silent seconds. IPv6 Internet HTTP, dual-stack echo, a one-minute IPv6 stress run, and kernel STOP-before-restore cleanup passed. See [current work report](artifacts/rtems-web-autonomous-20261011/README.md) for artifacts, failed trials, limitations and the published server.

**Current development roadmap:** [loader memory extension, RTEMS and remaining gaps](DEVELOPMENT-PLAN.md). Next: M1, generalize the proven larger RAM profile; preserve scalar/BIO1 compatibility.


**Current index (2026-10-11): [findings, evidence and unresolved questions](CURRENT-FINDINGS.md).** Earlier milestone notes below retain their historical context.

**IPv6 is implemented and tested on the card (2026-10-11):** dual-stack ping, UDP/TCP echo, AAAA and IPv6 Internet HTTP. [Usage](rtems/README.md#ipv6-usage-and-scope), [preserved evidence](artifacts/rtems-ipv6-20261011/README.md). Use the new `i960-rtems-ipv6-20261011` launcher with `--ipv6` or `--internet6`; the latter also routes IPv4 DNS. The cooperative execution model and RAM limits remain unchanged.

**RTEMS now runs on the card (2026-10-11): [implementation and usage](rtems/README.md).** RTEMS 4.6.6 tasks persist across bounded firmware callbacks; lwIP 2.1.3 provides ICMP, UDP/TCP echo and card-originated DNS/HTTP through a Linux TUN/NAT gateway. The original `net` profile uses host-supplied ticks; the newer `autonet` profile uses hardware timer interrupts with bounded work and preserves stock firmware service. [Exact artifacts and findings](artifacts/rtems-20261011/README.md). No additional flash programming or reboot.


**T4 complete (2026-10-10): [play Tetris over SSH](TETRIS-TERMINAL.md).** The terminal client passed a 30-minute real-SSH test: 35,846 native-matching frames, 68 restarts, 19.91 Hz. Quit, Ctrl-C, connection loss/reconnect and resize cleanup passed. Use `ssh -t mit@192.168.2.75 /home/mit/i960-tetris-t4/play.sh`. Full RAM restored, module unloaded; no reboot or flash.


**T5 complete (2026-10-10): [persistent BIO1 sessions](PERSISTENT-SESSION.md).** 1,000 frames matched native output at 41.1 ms median; a separate 400-frame run sustained 20 Hz. Process-kill/ownership cleanup and full final RAM restoration passed. `host/session/` keeps paired code/payload checks every frame and full staging audits every 32 frames and close. The subsequently completed T4 terminal client uses this transport; no reboot or flash.


**T3 complete (2026-10-10): [long Tetris hardware replay](TETRIS-REPLAY.md).** 1,000-call main replay plus 64 repeat calls matched native state/frame bytes; all RAM restored and probes unloaded. Median full CLI latency 306 ms (~3.26 updates/s), payload-command interval ~6.18 ms. This baseline motivated the now-completed T5 session optimization; T4 terminal play is now complete; see the latest milestone above. No reboot or flash.

**T2 complete (2026-10-10): [bounded Tetris steps](TETRIS-STEP.md) run on the card.** Explicit 240-byte state, 20-tick bound, 24×80 rendering; 1,024 native/interpreted transitions agree, and nine live transactions match the native reference byte for byte. RAM restored; no reboot/flash. T3 replay, T5 persistent sessions and T4 terminal play subsequently passed.

**T1 complete (2026-10-10): [bounded text/framebuffer I/O](BUFFER-IO.md) is hardware validated.** BIO1 supports 4 KiB input / 8 KiB output; live text, 24×80 frame, capacity rejection and repeat/scalar regression passed with RAM restored. T2 subsequently converted the blocking game into hardware-tested returning steps.

**Next work:** M1 in [the integrated plan](DEVELOPMENT-PLAN.md): generalize the proven larger loader profile inside the existing allocation. Tetris T1–T5 and cooperative RTEMS/networking are already implemented. The older [Tetris plan](TETRIS-ON-CARD-PLAN.md) records its milestone history; [the RTEMS roadmap entry point](RTEMS-HOST-NETWORK-PLAN.md) maps original milestones to the integrated plan.

**Latest hardware milestone (2026-10-10): [runtime software loader](SOFTWARE-LOADER.md) works after PC startup.** Three live executions (two C programs) passed without reboot or another flash write. Use `host/loadrun/` and `loader/runtime/` from the repository root; earlier internal-RAM and pre-programming plans below are historical. Supports cooperative returning functions up to 64 KiB, with one argument and a 32-bit result. RAM restored and module unloaded after each run. Recovery remains untested.


**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


Latest: [one-shot programming harness](ONE-SHOT-PROGRAMMING.md) is implemented in `host/program/`
(repository-root relative). Native transport/failure tests and a 105-command live
RAM-only rehearsal passed. Wrong activation token rejected before driver
registration; no programming doorbell issued. Full stock RAM restored and probe
unloaded. Exact binaries/captures are in `artifacts/one-shot-harness-20261010/`.
At this rehearsal milestone programming was still pending. Programming, full
readback and patched boot subsequently passed; see FIRMWARE-PROGRAMMED.md.
Recovery testing remains excluded.


Latest (2026-10-10): [programming preflight and live CPU verification](PROGRAMMING-PREFLIGHT.md)
passed. The CPU read all 512 KiB of the candidate through programmer alias
C1F2C000 with explicit cache invalidation and matched CRC32 2012D01F. All 105
commands completed cleanly; original staging/table/code restored, probe unloaded.
The descriptor policy and bytewise post-program flash-readback route are now
documented. Next implement the one-shot programming state machine and its
failure tests. No flash programming or recovery test occurred. Exact evidence
is in `artifacts/programming-preflight-20261010/` from the repository root.


Latest live experiment: [ROM-FETCH-LIVE.md](ROM-FETCH-LIVE.md). A wrapped
staging-relative `0x21` upload changed command-table word `C001F9BC`, and
`0x6F` executed RAM handlers. After cache and RAM-call controls passed, a
callback called a stock flash `RET` at **FEFB022C** after startup and returned
`017F`. All RAM bytes and the stock table were restored; the module was
unloaded. The earlier `FEFC8208` timeout used a wrong physical address:
the disassembly's FEFC8000 label is not the component's full-ROM location.
Read the live 8-bit flash-bus mapping evidence before choosing flash targets.
The *new* FEFE001C handler remains unflashed and untested. No flash write or
recovery check was performed. This supersedes the older execution boundary.
The [live staging rehearsal](STAGING-REHEARSAL.md) now passed: all six full
512 KiB captures match stock/candidate/restored-stock hashes; 74 commands
completed cleanly, original staging restored, module unloaded. Sources and
binaries are in `artifacts/staging-rehearsal-20261010/`. Next resolve CPU cache
visibility in the 2B/1 programming path, exact updater inputs, update-time
handler behavior and fresh physical flash readback. Candidate remains
`flash_ready: false`; recovery testing is excluded by the user.

Historical step-4 result: [ROM-HANDLER-STEP4.md](ROM-HANDLER-STEP4.md).
The exact ROM-backed candidate has an offline Fujitsu type-2 MIMG wrapper,
and a fixed live read verified opcode `0x6F` dispatch word `C001F9BC` still
contains stock handler `C001FE98`. The read-only probe was unloaded. The
MIMG has not been accepted by a vendor updater; at step 4 no table write,
code execution or flash instruction fetch after EBCR setup had been tested. The
candidate remains `flash_ready: false`.

Current step-3 candidate: [ROM-HANDLER-STEP3.md](ROM-HANDLER-STEP3.md).
`loader/romhook/` and `artifacts/romhook-20261010/` place the PING handler at
FEFE001C in verified firmware flash padding. Stock staging memory was rejected
because reachable stock paths free it. The image is still `flash_ready: false`:
post-startup flash instruction fetch, table visibility, recovery and programming
interaction remain untested. Keep the older DRAM candidate for comparison.

Latest DRAM audit: [DRAM-HOOK-AUDIT.md](DRAM-HOOK-AUDIT.md). The pinned stock
bootstrap clears C0120000 before the metadata hook, the reviewed allocator
starts at C0140000, and a fixed live read found 64 zero bytes. This does **not**
reserve C0120000 for the lifetime of the firmware. The stockhook candidate
remains `flash_ready: false`; next investigate firmware-owned handler storage.

Current offline candidate: [STOCK-PRESERVING-HOOK.md](STOCK-PRESERVING-HOOK.md). An 84-byte metadata hook installs opcode `0x6F` as a returning PING, then enters the original stock firmware. The candidate is not flashed; `C0120000` remains an unproven exclusive DRAM location. Build sources are in `loader/stockhook/`, artifacts in `artifacts/stockhook-20261010/`.

Historical execution analysis: [LIVE-EXECUTION-HANDOFF.md](LIVE-EXECUTION-HANDOFF.md) did not account for wrapped 32-bit upload offsets. The later live experiment above established a RAM callback handoff.

Latest: [RAM-WRITE-VERIFIED.md](RAM-WRITE-VERIFIED.md). Fixed 16-byte scratch upload/readback/restoration passed at C0FAC010 in the extra staging allocation block. All 22 commands clean; original 64 bytes restored, probe removed. No execution/recovery/flash.

Latest: [RUNTIME-READ-VERIFIED.md](RUNTIME-READ-VERIFIED.md). Paired live reads verified entry bytes, board C0110780, alias C1000000 and 512 KiB callbacks. Hardened exact read allowlist passed; no upload/execution/recovery/flash.

Latest: [STAGING-POINTER-VERIFIED.md](STAGING-POINTER-VERIFIED.md). Live paired four-byte reads confirmed C0F2C000 at C0112A70. Fixed-purpose read gate only; no upload, execution, recovery entry or flash. Probe removed cleanly.

Allocator derivation: [STAGING-ALLOCATION.md](STAGING-ALLOCATION.md). Enquiry2 plus the traced allocator predicted C0F2C000; [STAGING-POINTER-VERIFIED.md](STAGING-POINTER-VERIFIED.md) later confirmed it by direct read. The normal harness still rejects out-of-window offsets.

Latest: [SSH recovery-entry investigation](SSH-RECOVERY-ENTRY.md) and [serial preparation](SERIAL-RECOVERY-SETUP.md). Physical access is available; serial comes later. Read-only SSH preflight passed; RAM-offset lead remains unproven and no recovery transition was attempted.

Latest: [BOOT-RECOVERY.md](BOOT-RECOVERY.md) establishes an embedded recovery monitor (PCI 1069:0011) and partial vendor validation. Entry/restoration remain untested; continue over SSH without forcing a flash fault.

Latest programming audit: [PROGRAMMING-RECOVERY.md](PROGRAMMING-RECOVERY.md). The matching 512 KiB route uses 2B/1 and rewrites the lower 496 KiB; 22 returns an error on this route. An offline experimental MIMG package is archived, but vendor acceptance and recovery remain unverified.

Current test preparation: [LIVE-TEST-PREFLIGHT.md](LIVE-TEST-PREFLIGHT.md). Read-only host preflight passed; v2 candidate guards all three DMA channels and suppresses the option ROM before releasing PCI retry. No custom execution or flash yet.

Latest development: [POSTINIT-LOADER.md](POSTINIT-LOADER.md) documents an offline DRAM-loader patch prototype and the recovered metadata handoff. Sources are in loader/postinit/. It is not flashed or hardware validated; do not use the legacy image builder for the full dump.

**Local handoff:** See [artifacts/ROM-INVENTORY.md](artifacts/ROM-INVENTORY.md) and [artifacts/ROM-DUMP-WORKLOG.md](artifacts/ROM-DUMP-WORKLOG.md). Original Fujitsu packages (29 and 39), decoded ROMs, all snapshot sessions, disassemblies and collector are local; SSH is unnecessary for offline analysis.

Read **[SNAPSHOT-RECOVERY.md](SNAPSHOT-RECOVERY.md)** first. In-system recovery
succeeded: two matching 512 KiB image captures contain the exact 4.07-0-29
firmware, exact FWTCBBLK boot block, and independently verified PCI BIOS.
Archived binaries are in artifacts/private-dumps/ and are intended for Git; hashes
and transaction evidence are in artifacts/analysis/snapshot-20261010/.

The live layout uses the 512 KiB profile, with firmware at offset 0x30000.
Earlier 256 KiB/offset-0x8000 assumptions and claims that no firmware dump exists
are superseded. `host/dump` defaults to Enquiry2 and uses fixed opt-in gates for
read, upload and RAM dispatch experiments; never use `0x21` to retrieve data.
The controller remains driverless. Do not automatically
unbind myrb, upload, program, or reset it. Paired staging reads do not replace
the independent backup gate before flashing.

Read **DRAM-ANALYSIS.md** for the remote environment exploration, successful
i960 target build, g14 startup fix, and the two recovered board-register profiles.
Their DRAM bit-field meanings remain unverified.

Read **PROJECT-REVIEW.md** for the 2026-10-10 whole-project review focused on
in-system firmware dumping. It qualifies earlier impossibility claims and flags
the probe's opcode truncation/completion/DMA issues. Its no-dump status is historical; prioritize offline analysis of the recovered
firmware and boot block.

**Hardware correction:** internal RAM at 0x000..0x3ff is DATA ONLY. The loader's
hello-at-0x200 execution plan is invalid (Intel manual §4.1), despite passing native
tests. Do not treat the previous loader milestone as hardware-ready.

This repository contains native i960 code, a host emulator, firmware analysis,
and a DAC960PG flash loader. Start with README.md and FINDINGS.md for context.

For **loader/** work, read loader/CLAUDE.md, loader/README.md,
loader/PROTOCOL.md, and loader/REVIEW.md. These describe the 2026-10-10 protocol
fixes, address policy, native tests, and outstanding hardware/target-build gates.
The loader demo now marks execution in OMR1 and preserves OMR0's GO ACK.

Run `make -C loader test` to validate loader software without hardware. Target
builds require the i960 cross-toolchain. Do not equate emulator/native tests with
physical card validation. Firmware replacement must follow REFLASH.md and its
external-programmer backup gate.

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
