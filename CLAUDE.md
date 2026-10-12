# Repository guidance for Claude Code

**Allocator/segmented-loader core (2026-10-12):**
[New core and integration gates](loader/segmented/README.md) provide a guarded
128-slot arena, generation handles, pins/cancellation, and an eight-segment
copy/CRC/BSS/cache-sync state machine. Native sanitizers passed a contiguous
6 MiB allocation and failure tests. Three real-card BIO rehearsals passed; the
second executed copied code reading a separate data segment. The live arena
was 3,728 bytes; this does **not** grant the 12 MiB reserve to applications or
extend production RTEMS malloc. Full RAM restoration/module unload passed;
IPv6 HTTP was restored. [Exact captures](artifacts/segmented-loader-20261012/README.md).
Next: high-tail protection, bootstrap placement, RTEMS ownership/libc adapters,
and bounded resident PIO upload without another firmware callback.

**12 MiB exclusive RAM checkpoint (2026-10-12):** `--owned-mib 12`
passed four startup patterns over `c0240000..c0e40000`, a 35-minute resident run,
48 dual-stack rounds and independent replay of 3,812 packets. RTEMS now initializes
after takeover, with a 256 KiB kernel workspace and three 64 KiB requested task
stacks (plus the idle slot). Both workers checked live 12 KiB stack objects;
a real 128 KiB workspace allocation survived the run, was fully checked and freed.
All 220,066 application allocations and 16,402 shared objects drained at tick
210,002, with both task IRQ contexts drained and two timer-counter carries.
The complete 11,993,024-byte reserve passed its final scan. Both workers now
service PIO; chunked shutdown scans keep control responsive. Observed word-ioctl
median/P95/max: 0.182/2.931/10.644 ms; draining maximum 1.845 ms versus the earlier
4.459-second blocked scan. These are workload observations, not latency bounds.
Maximum ISR gap was 11.038 ms: broader checks add cost, so this is not an IRQ-latency
improvement over the previous smaller profile. The application heap stays
171,824 bytes; the reserve is not yet a general allocator or executable grant.
The high protected-tail inventory and segmented loader remain gates before Doom.
Two incomplete 10 MiB sessions and their fixes are preserved. Cooperative profiles
remain available; no flash write. The post-run reboot returned; cooperative public IPv6 HTTP is restored and verified.
See [RAM contract](rtems/residentnet/LARGE-RAM.md), [captures](artifacts/rtems-large-ram-20261012/README.md), and [Doom OS plan](game/doom/OS-PLAN.md).

**Fallback queue reclaimed; network work preemptible (2026-10-11):**
Opt-in `--queue-reclaim` requires the shared/general heap, validated extra RAM,
owned exceptions and secondary SCSI reset. After copying any startup packets
and irreversibly switching to the external queue, the old 102,000-byte object
becomes a guarded 101,872-byte second application arena. Total arena capacity
is 171,824 bytes; largest permitted request is 101,808 bytes, subject to free
contiguous space. Kernel workspace, task stacks, lwIP pools and upload size do
not grow. RX leases and unpublished TX buffers let lwIP/copy work run at priority
20, with only ownership transfers masked. Every 32nd shared cycle uses 80 KiB
in reclaimed storage. The forty-round, thirty-minute card run passed at tick
180,008: all 189,150 allocations and 14,138 shared objects drained, including both
IRQ contexts. Guard and metadata corruption each passed physical terminal
containment with live resources retained. Maximum observed ISR gap was 10.688 ms
(previous RNT7 endurance: 13.270 ms); 182 network-processing brackets spanned
interrupts. These are measured workloads, not worst-case guarantees. Full raw
packet replay, native regressions and offline tests passed. Failed host lookup
attempt and exact binaries are preserved. No flash write or new RAM range grant.
The post-test reboot returned; the cooperative public IPv6 RTEMS/Vader page
is restored and verified HTTP 200.
See [contract and evidence](rtems/residentnet/QUEUE-RECLAIM.md).

**Shared heap, latency and endurance (2026-10-11):** `--heap-shared` adds
explicit two-task references/pins and cancellation to the existing 69,952-byte
heap. Pinned or uncertain holders retain memory; no arbitrary task deletion or
automatic reclamation is authorized. Busy reservations let calloc/realloc copy
work restore the caller's interrupt priority. Measured protected maxima fell
from 14.804 ms to 0.261 ms for calloc and 11.064 ms to 1.985 ms for realloc; these
are observed sections, not whole-system bounds (maximum ISR gap: 13.270 ms).
The final card run passed forty dual-stack rounds, timer wrap and 180,008 ticks;
all 194,154 allocations and 14,764 shared objects drained, including both IRQ
contexts. Each large-memory path spanned interrupts in 180 calls. Native stress
passed 200,000 worker updates and a legitimate fragmentation refusal. A prior
HTTP endurance timeout exposed full packet-history rewrites on the host; an
append journal reduced recording from 188.43 to 0.200 ms in the matched benchmark
while preserving every byte and strict replay. Partial/failed attempts are kept.
No flash writes or new RAM grant. At this baseline the 102,000-byte internal
fallback queue remained reserved; the opt-in queue-reclamation follow-up reuses
it after external handoff. The baseline profile still reserves it.
Post-test reboot succeeded; cooperative public IPv6 HTTP is restored and verified.
That batch proposed fallback-queue reuse and less masked network work; the
queue-reclamation follow-up implements those. Broader task/resource ownership
and control-path latency remain future work. Read the
[contract, measurements and thirty-step evidence](rtems/residentnet/SHARED-HEAP.md).


**Metadata journal card acceptance complete (2026-10-11):**
Opt-in `--queue-metadata journal` passed nine physical sessions: **1,635 replies/full
paired audits**, 1,586 targeted slots, 55,636 commands and nine restorations.
The clean browser ABBA comparison improves RAF delivery **13.20 → 15.19 FPS
(+15.0%)** and metadata writes **9.50 → 0.23 ms/request**; kernel time stays near
24.4 ms. Idle/limit/SIGTERM/disconnect pass; 12 corruption cases reject. An extra
run overlapping offline replay is preserved but excluded from timing. All full
audits remain, and rewrite stays the reference default. Public IPv6 HTTP restored
and checked; no flash write/reboot. The bounded raycaster is ready for user testing.
[Evidence](artifacts/journal-20261011/README.md) · [Play instructions](game/raycaster/journal/USER-TESTING.md).


**Browser queue accepted (2026-10-11):** `game/raycaster/server.py --backend
card-queue` now uses the accepted combined queue and unchanged card binaries.
Seven sessions passed **663 replies/full paired audits**, **640 targeted slots**,
22,608 commands and seven verified restorations. Chromium displayed 640 frames
with movement, reset, blur and single-flight checks. Idle expiry, frame limits,
SIGTERM during a request and TCP reset all close safely; uncertain requests are
never retried. Lossless gzip level 1 reduces full-audit archive cost **21.61 →
5.94 ms**. Together with browser pacing, observed delivery improves **9.79 →
13.10 FPS**; kernel time remains about 24.4 ms. These are headless Chromium/SSH
measurements, not physical monitor scanout or asynchronous card rendering.
Every full audit remains. Native remains the default backend; queue sessions
are bounded to 512 updates/30 s idle by default. Public IPv6 HTTP was restored
and returned 200. No flash write or reboot in this batch. Read
[the bridge contract](game/raycaster/browserqueue/README.md) and
[the captures and remaining work](artifacts/browserqueue-20261011/README.md).


**General application heap (2026-10-11):** `--general-heap` adds 69,952 bytes
at `c022ee80..c023ffc0` using RTEMS 4.6.6's real allocator. It requires
`--extra-ram --fault-owner --secondary-reset` and grants no additional RAM range.
The 128-slot packet queue remains intact; kernel workspace/task stacks stay in
the upload region. Allocation has a 64-live-block limit, exact-pointer checks,
redzones, bounded metadata validation and ISR refusal. Outer-guard, allocation
suffix, metadata-extent and saved-offset corruption each passed physical containment
tests with both live allocations retained; no forced unload or recovery resume.
The hardened non-injection image passed 36,000 ticks, ten spaced dual-stack
rounds, saturation/TCP loss recovery, and all 36,100 allocations freed before
both IRQ contexts drained. All six reboots returned normally; cooperative public
IPv6 HTTP is restored and checked. Do not enable `--heap-test` in production. See the
[heap contract and evidence](rtems/residentnet/GENERAL-HEAP.md).


**Slot validation batch accepted (2026-10-11):** all fifteen steps in
[the batch ledger](game/raycaster/slotopt/BATCH.md) completed. Target-only word
hashing plus exact word metadata/guard checks reduce full-frame callback time
**11.219 → 10.081 ms (10.14%)** and kernel time **25.165 → 24.158 ms (4.00%)**.
Ten sessions passed **1,691 replies and paired full audits**, 59,284 commands and
ten complete restorations, including 806 two-slot stress requests. Hash cost falls
24.97%; complete slot validation 33.63%. The accepted kernel module and full audit
coverage are unchanged. The extra 0.016 ms kernel advantage over hash-only is
within host variation; both remain opt-in. Use `--queue-slots words` with the
accepted combined/fast-render flags; diagnostic opcode 5 is excluded from release
images. Public IPv6 HTTP restored. No flash/reboot in this card batch. The queue
retains its original RAM grant and does not inherit the parallel ownership work.
[Contract](game/raycaster/slotopt/README.md), [complete measurements/artifacts](artifacts/slotopt-20261011/README.md).
Next: browser integration of the verified combined queue with full audits and
measured displayed-frame delivery.


**Exclusive exception/RAM follow-up (2026-10-11):** real constraint faults and
a real PCI doorbell NMI (vector 248) entered owned terminal handlers. The cached
NMI vector, all fault entries and interrupt stack are owned before SCSI reset.
A fixed 256 KiB range passed four patterns with protected-range checks; only
its guarded 192,000-byte packet queue is granted with `--extra-ram`. The
128-slot queue passed 24,000 ticks, six dual-stack rounds, saturation and TCP
loss recovery with IRQ contexts drained at the deadline. General
RAM reclamation remains disabled. The dedicated NMI ioctl exists only in a
module pinned to `--fault-test 3`; do not put it in production. All exclusive
resources remain retained until reboot. The final reboot succeeded and public
IPv6 HTTP is restored and checked. Preserve cooperative profiles and check
the live card owner before experimenting. [Contract and evidence](rtems/residentnet/FAULT-OWNERSHIP.md).


**Combined ACK-and-PUBLISH accepted (2026-10-11):** the opt-in queue operation
validates the exact occupied slot and next generation before replacing it. Four
sessions passed **586 replies, 586 paired full audits and four restorations**;
80 steady frames are identical across all four runs. Kernel time improves
**39.958 → 25.078 ms/frame (37.24%)**, wall time 43.364 → 26.908 ms, and host CPU
11.367 → 6.503 ms. The exact accepted kernel module is unchanged; every request
still reads both complete 512 KiB snapshots and all targeted bytes. Combining
operations saves one transaction/audit pair per frame, never audit coverage per
request. Input rejection preserves queue and renderer state; uncertain execution
is never retried. HTTP is restored; no flash/reboot in this batch. Keep this
opt-in with `--frame-queue --queue-combined`; single-frame defaults remain.
Next: profile slot validation/publication hashing while retaining all checks.
[Contract](game/raycaster/combined/README.md), [measurements and captures](artifacts/ackpublish-20261011/README.md).


**SCSI stop boundary (2026-10-11):** the identified secondary Symbios 53C895
remained in bus reset for 36,000 ticks and ten spaced concurrent IPv4/IPv6
rounds, including saturation, TCP loss recovery and autonomous task shutdown.
This is forced stop/discard, not graceful SCSI drain or a disk flush. The opt-in
`--secondary-reset` build retains reset and resources until reboot; never force
unload it. Default/cooperative profiles remain available. Useful resident queue
storage is now 72 × 1,500 bytes inside the existing 512 KiB grant. **No broader
RAM grant:** stock cached NMI and fault paths remain; the NMI handler can
reinitialize the secondary interface. The candidate RAM-transfer policy is
offline only. The final reboot returned normally; public IPv6 HTTP is restored
and checked from the Mac. Follow the [contract and evidence](rtems/residentnet/SCSI-STOP.md) before further tests.


**Bounded frame queue accepted (2026-10-11):** two fixed slots with epoch,
generation and explicit ACK passed four sessions, 518 native-matching replies,
518 paired full audits and four restorations. All requests retain both complete
512 KiB reads. The separate PUBLISH/ACK prototype costs **39.947 ms/frame versus
20.596 ms baseline**; keep the previous single-frame path as the default.
Targeted publication reads take 0.591 ms but do not replace auditing. The first
module missed three capture-array loop bounds and faulted the host; evidence is
preserved, the bounds/storage checks and generated-driver lifecycle tests are
fixed, and the accepted batch ran after reboot. Public IPv6 HTTP is restored.
Next: validate combined ACK-and-PUBLISH while keeping full audits per request;
no asynchronous producer, broader RAM ownership or relaxed audit policy is proven.
[Contract](game/raycaster/queue/README.md), [measurements and failure evidence](artifacts/framequeue-20261011/README.md).



**Callback/render optimization accepted (2026-10-11):** exact word-at-a-time
request validation and equivalent renderer loops reduce full-frame callback time
**11.925 → 7.360 ms (38.28%)**, with kernel transaction time **24.169 → 19.471 ms
(19.44%)**. Eight sessions pass 3,368 native-matching replies, 104 periodic full
allocation audits and eight restorations; public IPv6 HTTP is restored. All paired
read coverage, guards, deadlines and quiet-string restoration remain intact.
The optional 20 us completion poll saves 0.269 ms of audit time but costs 17.19%
more host CPU; retain 50 us as the recommendation. Coarse release: 19.352 ms.
Use `build_target.py --request-words --render-fast` and
`game/raycaster/callback/build_transport.py --out DIR --coarse`; existing target
builder defaults and production remain unchanged. [Contract](game/raycaster/callback/README.md),
[profiles, artifacts and next bottleneck](artifacts/callback-20261011/README.md).


**Resident decode follow-up:** live board selector 6 and dispatch `c000d540`
qualify synchronous CPU XOR / internal DRAM, not the alternate external-cache
bit-0 completion path. Firmware reports 16 MiB. Resident networking now has
32 TX slots inside the original grant; three IPv4/IPv6 rounds and 12,000 ticks
passed. No outside RAM grant or all-engine drain is claimed. Preserve cooperative
profiles, never force-unload retained resident resources, and check the current
remote owner before testing. [Findings, thirty steps and remaining gates](rtems/residentnet/DECODE-BATCH.md).


**Upload UART bottleneck resolved (2026-10-11):** the stock upload method prints
through a blocking UART before DMA. A scoped RAM-only change to one format byte
reduces three upload waits **32.129 → 0.368 ms** and full-frame kernel time
**55.840 → 24.141 ms (56.77%)**. All existing checks remain, with additional paired
format/handler checks. Five final sessions passed 2,105 native-matching replies;
ten startup sessions passed 40 more. An exploratory stale-PING rejection restored
cleanly; the final ordering preserves the original first-entry cache handshake.
Quiet data and all borrowed RAM restore before unload; HTTP returned 200 afterward.
No flash/reboot. Use `game/raycaster/upload/build.py --quiet --coarse` only for the
pinned bounded raycaster path; production remains autonet.
[Contract](game/raycaster/upload/README.md), [findings and captures](artifacts/upload-20261011/README.md).


**Resident networking (2026-10-11):** `residentnet` runs RTEMS/lwIP after one
ARM callback, using message-register PIO with PCI bus mastering disabled. Card
IPv4/IPv6 UDP, 4,096-byte TCP echo, HTTP 200, maximum-size packets and deliberate
TCP loss passed. STOP/deadline parked at 533/6,000/846 ticks with all task IRQs drained;
packet requests after parking were rejected and the module retained until reboot.
Offline replay validates 236 IP packets and rejects 57 corrupted snapshots.
All state stays in the existing mutable allocation; **no broader RAM grant**.
The exact firmware's cache completion wait/ack sequence is located, but live
address-like register reads do not establish cache-engine completion or drain.
Keep `autonet` for production and preserve all cooperative profiles. See the
[contract](rtems/residentnet/README.md), [30-step ledger](rtems/residentnet/BATCH.md)
and [captures/recovery status](artifacts/rtems-residentnet-20261011/README.md).


**Framebuffer transport profiling (2026-10-11):** 43,904 profiled commands
show about 32 ms waiting for the three request/sentinel/table uploads per frame.
Exact-count DMA scans and equivalent immutable-range comparisons reduce full-frame
kernel time 57.83 → 55.74 ms (3.61%), with readback/audit 12.22 → 10.61 ms (13.15%).
Five sessions passed 2,105 native-matching replies, 65 periodic full audits and
five full restorations/unloads. Optimized coarse build: 55.64 ms. Payload, bytes
transferred, paired comparisons, guards and audit cadence are unchanged. HTTP
restored; no flash/reboot in this batch. [Contract](game/raycaster/transfer/README.md),
[evidence](artifacts/transfer-20261011/README.md). Use the optimized module only
for the accepted bounded application path; batching/ownership remain separate gates.


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
[Exclusive contract and remaining gates](rtems/exclusive/README.md),
[30-iteration ledger](rtems/exclusive/BATCH.md). Production remains `autonet`.


**Word-memory raycaster milestone (2026-10-11):** aligned RAM copy/clear
helpers passed 5,280 on-card reference cases and 2,105 native-matching replies
across five restored sessions. Native sanitizer/guard-page tests also passed.
Copy is 3.30× faster; clear 4.63×. Repeated byte/word comparisons reduce full-frame
kernel time from 60.31 to 57.95 ms (3.91%), with unchanged output and audit cadence.
The raycaster builder defaults to word helpers; other OS profiles and production
autonet are unchanged. IPv6 HTTP verified after testing. [Contract](rtems/memory/README.md),
[measurements and artifacts](artifacts/word-memory-20261011/README.md).
Next: profile constituent upload/arming commands; do not weaken ownership or checks.


**Callback-free monitor milestone (2026-10-11):** `handoff` passed five final
sessions: 20 bounded entries from the timer ISR after the ARM firmware callback
returned, five omitted-RELEASE expiries and ten denied DMA/SCSI transfer
requests. Every final close restored RAM and unloaded. The initial token-repeat
failure required recovery; a second build exposed an i960 compiler condition-code
bug in the diagnostic policy. Both failures and corrections are preserved.
Stock firmware uses DMA0/1; idle registers do not grant ownership. This is a bare
monitor prerequisite, not callback-free RTEMS scheduling or permanent takeover.
Production IPv6 HTTP is restored. [Contract and next gates](rtems/handoff/README.md),
[16-step batch](rtems/handoff/BATCH.md).


**Raycaster/profiling milestone (2026-10-11):** an 80×60 fixed-point renderer
and browser bridge passed 548 native-matching RTEMS card replies, including
partial frames, movement/reset and OS-helper benchmarks. Six native tests and
sanitizer checks passed; 16 periodic full-allocation audits plus two initial
prefix snapshots verified, and both sessions restored RAM/unloaded. HTTP is
restored. Median full-frame kernel time: 60.38 ms; upload+arming about 32.8 ms;
render/publication increment about 7.54 ms. Byte-loop memcpy: 2.88 MiB/s;
semaphore roundtrip: 102.4 µs; software tick: 4.96 µs (differential estimates).
[Findings and evidence](artifacts/raycaster-20261011/README.md),
[contract/reproduction](game/raycaster/README.md). Next: validated word-copy/clear
helpers and finer command-cost profiling; preserve all ownership/audit checks.


**Continuous execution lease (2026-10-11):** `leaseirq` now keeps preemptible
RTEMS workers running continuously inside a parked firmware callback. Sideband
grant/renew/STOP, a 512-tick renewal deadline, a non-renewable 24,000-tick cap and
per-tick timer/vector/mask/MU checks make the execution lease explicit. Nine
sessions passed 23 callbacks and 13 leases, including 60 seconds of renewed
execution, 115 seconds to the cap, expiry and transitive quarantine. All 40,111
hardware checks reported no drift; all closes restored RAM and unloaded.
Native tests, 1,610 actual-report mutations and production IPv6 HTTP passed.
[Contract, ownership table and evidence](rtems/leaseirq/README.md). Firmware stays parked; DMA/SCSI
ownership and unrestricted coexistence are not established. Production remains
autonet. Earlier next-step descriptions below are historical.


**Game application track (2026-10-11):** [CHIP-8 → framebuffer → raycaster → Doom](GAME-PROGRESSION.md).
DoomGeneric is the chosen porting base; FastDoom is an optimization reference.
CHIP-8 passed 705 native-matching RTEMS card replies, browser keys/restart,
21 periodic full-allocation audits and two clean restorations/unloads. Production IPv6 HTTP restored.
See [application contract](game/chip8/README.md). Keep this bounded application
separate from active interrupt/ownership profiles and production autonet.


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

## RAM ownership follow-up (2026-10-11)

See [rtems/residentnet/RAM-OWNERSHIP.md](rtems/residentnet/RAM-OWNERSHIP.md). The resident queue is now 64 slots inside the
existing 512 KiB grant. Board/dispatch/staging identity is checked before network
initialization. Snapshot RNT2 words 57–59 are queue telemetry, not cache status.
The adjacent 240 KiB belongs to the stock cache data pool; never reclaim it from
size or zero software counters alone. Fixed page 15 observes SCSI bookkeeping;
hardware drain remains unproved. Cooperative net/autonet stays available.
