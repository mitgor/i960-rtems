# Current findings and evidence — 2026-10-12

**Owned runtime and larger-image checkpoint (2026-10-12):** the small owned
runtime proof is physically accepted: pinned i960 setjmp/longjmp, normal / STOP /
normal, stale generation refusal, full audits and STOP drain at tick 21,511.
The full engine-linked **diagnostic preflight** and exact SHA256-authenticated
image/relocation gate pass native sanitizers and three linker oracles. On-card
modified-code/metadata refusal passed; clean entry never ran after interrupt/drain fault bit 64 at tick 46,462. The active-state capture
favors timer slot rejection; its unregistered/active paths share the flag.
Do not relax that guard or claim Doom/engine execution. A native-tested 1 MiB
proof reservation fixes the retained-buffer fragmentation before the 6 MiB zone;
that host change still needs physical acceptance. The candidate spans 754,448
bytes with 13,175 relocations; admission storage is 807,148 bytes. Both bootstrap
code windows stay fully protected. Production IPv6 HTTP is restored (200).
Next: diagnose the timer rejection with the parallel RTEMS audit, accept normal /
STOP / normal preflight and full drain, then WAD batching and real Doom startup.
Keep `--doom-engine` opt-in. The historical global ISR-level getter remains
unfixed; only the new owner predicate uses a read-only PC query.
[Owned evidence](artifacts/doom-owned-20261012/README.md) ·
[Larger gate/failure evidence](artifacts/doom-engine-20261012/README.md).


**Private Doom runtime/cache checkpoint (2026-10-12):** the new private
Newlib/platform candidate has **zero unresolved imports**, a 752,804-byte
code/data/BSS span and 13,113 relocations matching three independent links.
The full private 32-bit library/port passes ASan/UBSan. It does not override
kernel libc and is not admitted for engine launch. The separate 1,760-byte
cache probe passed real i960 execution: both normal hashes matched, cached
repeats made no extra reads, and CRC/short/error/timeout/recovery passed.
Full audits, six network rounds/812 packets, 625-command replay, 48 evidence
mutations and STOP drain at tick 17,855 passed. The upper loader uses 25,312
bytes with unchanged boundaries. Explicit Doom object suffixes fix a linker
wildcard that depended on the workspace name. Public IPv6 HTTP is restored (200).
Next: owned engine entry/yield/STOP and i960 exit boundary, larger manifest
admission, WAD batching/initialization budget, then first frame. Keep the current
closed whitelist; **Doom itself has not run on card**.
[Runtime contract](game/doom/runtime/platform/README.md) ·
[Physical evidence](artifacts/doom-platform-20261012/README.md).

**Relocated code/data/BSS proof accepted (2026-10-12):** the reviewed 184-byte
image executed twice at `0xc02d0050` inside the shared arena, returning
`1228486293` both times. Six trusted relocation sites, 128 zero-filled BSS bytes,
all 32 resulting counters and initialized code/data were checked. Eight admission
refusals, all paired audits, six network rounds and STOP drain at tick 14,903
passed. Native replay covers 593 requests / 1,511 upload ioctls; 24 snapshot,
eight WAD and seven relocation evidence mutations are rejected. TCP replay now
separates reused port tuples only after captured closure and a fresh SYN; gaps,
conflicting retransmissions and echo mismatches still fail. The exact card
build is archived. This is a closed returning proof, **not Doom execution**;
44 engine imports remain. Next: libc/platform imports and i960 cache/runtime
integration, then bounded initialization. Preserve both worker owners, pins,
full audits, and exclusive reboot-only release. The reboot completed and the
original public IPv6 HTTP service is restored (independent HTTP 200).
[Contract](game/doom/runtime/relocate/README.md) ·
[Evidence](artifacts/doom-relocate-20261012/README.md).

**Doom cache/link milestone (2026-10-12; host-only):** the single-WAD backend
now bridges interior zone destinations through a private 512-byte runtime read
buffer and 16 KiB cache. All 12,600 host frame/palette/tic hashes still match,
with a 1 MiB image reservation inside the 8 MiB arena; peak dynamic use is
6,473,545 bytes. Real soft-float helpers reduce unresolved imports from 53 to
44; the 638,552-byte object remains non-loadable. A restricted REL relocation
prototype matches three independent linker outputs and refuses the incomplete
engine. This old linker drops final relocation records despite `--emit-relocs`.
No new card payload was run; public HTTP remained available. Next physical gate:
small relocated code/data/BSS proof, then remaining libc/platform services and
bounded Doom startup. [Contracts](game/doom/runtime/cache/README.md) ·
[Evidence](artifacts/doom-cache-20261012/README.md).

**Doom runtime entry/WAD bridge accepted (2026-10-12):** opt-in
`--doom-runtime` executed a reviewed 736-byte uploaded application using a
96-byte i960 function table, task-owned allocation and bounded host-backed WAD
reads. Both normal runs matched the independent hash; CRC, short response,
host error and 500-tick timeout cases passed, followed by successful recovery.
Six network rounds, full paired audits, 539-command C replay and capture tamper
tests passed. STOP drained at tick 11,672 with no outstanding loans. The first
attempt's refused tail reply is archived; the corrected host keeps query/reply
together relative to full audits and avoids redundant status polls. Target
binary and five-second deadline were unchanged. Keep worker 0 runnable; retain
loans until copy/cancellation completes. **Doom itself is not running yet.**
The final reboot returned and public IPv6 HTTP was restored and verified (200).
Next: engine image linking/imports, WAD file adapter/cache, then bounded startup.
[Contract](game/doom/runtime/entry/README.md) · [Evidence](artifacts/doom-entry-20261012/README.md).

**Shared Doom arena accepted (2026-10-12):** opt-in `--doom-shared` adds one
priority-inheriting task mutex and separate allocation namespaces over the same
8 MiB arena. Two existing workers passed 3,305 wrong-task rejection/check rounds,
a deliberate timeout and recursive refusal, and complete retained-buffer/image
reclamation after task/IRQ drain at tick 9,342. Six network rounds, 804 packets,
full audits, native sanitizers and independent replay passed. The first blocking
proof exposed the fatal-idle constraint: keep a control worker runnable or admit
and test idle IRQ ownership before allowing all tasks to block. No new task,
flash change or relaxed validation. Doom is still not running; the refreshed
relocatable object is 631,176 bytes with 53 imports left. After reboot, the
cooperative public IPv6 HTTP service was restored and verified (200).
[Contract](game/doom/runtime/SHARED-ARENA.md) · [Evidence](artifacts/doom-shared-20261012/README.md).


**Doom allocation runtime accepted (2026-10-12):** namespaced malloc/calloc/
realloc/free/strdup now use the existing 8 MiB resident arena without replacing
system libc. Six host demos / 12,600 frames match the accepted pixel/palette/tic
corpus. The opt-in `--doom-heap` card test passed a 6 MiB calloc, resizing/OOM,
strdup and a 64 KiB allocation retained until confirmed STOP drain, alongside
six network rounds. Full replay and native sanitizers passed; reboot returned
and public IPv6 HTTP is restored (200). The combined i960 object is 631,112 bytes
with 53 unresolved imports. Single-worker ownership remains; arbitrary task
launch, shared allocator serialization and other runtime/WAD services are next.
[Contract](game/doom/runtime/README.md) · [Evidence](artifacts/doom-runtime-20261012/README.md).


**Doom host determinism fixed (2026-10-12):** all three variable frames were
out-of-post sprite reads caused by negative fixed-point samples wrapping to 127.
Bounded masked sampling now passes 24 host runs / 50,400 draws across both
Freedoom IWADs and four heap fills, with complete pixel/palette/tic comparisons.
Focused renderer sanitizers pass. The i960 object is 627,096 bytes (+240), with
58 unresolved symbols unchanged. No Doom ran on-card. The parallel 8 MiB arena
is now proven; libc/task/WAD integration is next. [Findings](game/doom/DETERMINISM.md)
and [exact evidence](artifacts/doom-determinism-20261012/README.md).


**Resident RTEMS upload accepted (2026-10-12):**
[Ownership, bootstrap and protocol](rtems/residentnet/UPLOAD.md) now implement
opt-in `--resident-upload --owned-mib 12`: an 8 MiB guarded arena, protected
monitor/loader/high-tail pages, and a separate 6,416-byte loader section inside
the original upload allocation. A resident PIO transfer loaded 96 KiB code and
98,309 data bytes, zeroed/checked 98,299 BSS bytes, and executed the reviewed
returning probe. A simultaneous 6 MiB allocation passed on-card. Ten concurrent
dual-stack rounds (140 cases, 1,115 packets) and STOP cleanup passed; a partial
image remained pinned until worker/IRQ drain, then the arena was proved empty.
The C-struct wire-padding failure and a host snapshot/relay scheduling failure
are preserved with their fixes. [Exact artifacts](artifacts/rtems-resident-upload-20261012/README.md).
Libc remains on its 171,824-byte heap. Arbitrary application task launch,
imports/relocations and Doom remain next work; there is no second firmware
callback or flash change. The stock/cooperative alternative remains available.
After reboot, cooperative IPv6 HTTP was restored and independently returned 200.

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


**Firmware allocation follow-up:** recovered 8 KiB cache lines and 52-byte
cache descriptors, with the staging allocation inside the firmware cache pool.
The adjacent 240 KiB is not free RAM. Resident TX capacity is now 64 slots within
the existing grant, with board admission checks and queue telemetry. Six concurrent dual-stack rounds,
a deliberately saturated queue and a 60,000-tick autonomous deadline passed;
711 captured packets pass independent replay. Public IPv6 HTTP is restored. SCSI
software counters read 0/0/4/0 after reboot; engine drain and broader RAM ownership remain
open. See [allocation and test contract](rtems/residentnet/RAM-OWNERSHIP.md) and
[batch evidence](artifacts/rtems-ram-ownership-20261011/README.md).



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


**Cache dispatch and resident follow-up:** board selector 6 and the live primary
operation pointer qualify the i960 internal-controller / CPU-XOR path. Firmware
reports 16 MiB. Bootstrap analysis shows board selector 6
installs synchronous CPU XOR, while a different board path installs the external
`4080001c` command / bit-0 completion routines. Address-like cache reads remain
invalid completion evidence. The resident TX queue now uses 32 slots within the
existing grant; no new physical RAM ownership is claimed. Three network rounds
and a 12,000-tick deadline passed, after fixing an RX-busy backpressure bug found
in the first attempt. See [details and remaining gates](rtems/residentnet/DECODE-BATCH.md)
and [captures/recovery status](artifacts/rtems-residentnet-decode-20261011/README.md).


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


**CHIP-8 application milestone (2026-10-11):** bounded RTEMS CHIP-8 and a browser
framebuffer bridge passed 705 native-matching card replies: reset + 300 scripted
updates, then 404 browser callbacks including movement/restart. All 21 periodic full-allocation
audits and both RAM restorations/unloads passed. Median callback latency was
51.43/51.65 ms. Production IPv6 HTTP returned 200; no flash/reboot. The separate
parallel OS batch completed before these sessions. [Evidence](artifacts/chip8-20261011/README.md),
[usage](game/chip8/README.md), [progression and DoomGeneric decision](GAME-PROGRESSION.md).
Next application: fixed-point raycaster and transport measurements. Doom still
needs larger owned RAM and runtime services; FastDoom is an optimization reference.


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
