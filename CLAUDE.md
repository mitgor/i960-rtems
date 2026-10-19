## Accele160 faster polling / reply DMA — 2026-10-19 (one-hour qualification passed)

Current owner is now `/home/mit/i960-packet-dma-20261019/bundle`, boot
`724cee4d-a331-4cbb-840b-7b5bb5541ccc`. The preceding combined owner closed its
module and shut down cleanly before reset. The new normal profile-5 kernel is
`a3d6722a907ed59dab707d5715d1cb4b476b7dd192662e319e2656b001188503`.
It passed the ordinary 64-frame baseline and loaded the combined module. Do not
start a second owner or modify the frozen live bundle.

The owner now pumps services every 5 ms; full ownership/fault audits remain at
100 ms and heartbeat at 500 ms. Opt-in reply DMA borrows the existing DMA0 and
pinned host slot only after game retirement. It copies the 4 KiB runtime reply
page followed by an exact epoch/sequence marker, drains with a finite observer,
and retains all resources on uncertainty. Upload/request traffic stays PIO.
Native finite-chain, timeout/error, stale-marker, full-page comparison and
quarantine tests pass. See `rtems/accele160/runtime/PACKET-DMA.md`.

The raw hardware trial passed 32 full-page DMA/PIO comparisons, 320 alternating
UDP reply transactions (64/256/1024/1400-byte payloads), and one final full-page
query comparison. Another 200 full-page comparisons passed under mixed load.
Measured DMA speed varied by size; no uniform acceleration is proved. Routed
HTTP medians were about 150 ms for both PIO and DMA. PIO remains the intended
final default. The 3,603-second DMA endurance run passed 78,344 workload events
with zero errors/drops and intact guards. Maximum HTTP/console times were
621/107 ms. Sixty status queries after the run had a 38.5 ms median (old
100 ms polling: 205.6 ms); this is host round-trip latency, not an IRQ bound.
Relay pause/death, broker restart, abandoned client, partial-upload refusal and
module reload passed without changing boot or PCI owner. DMA/PIO comparisons
before and after two epoch transitions bring the full-page total to 235.
The prompt, PIO relay, IPv6 HTTP and browser gateway are active. Evidence and
replay commands: `artifacts/current/accele160-packet-dma-20261019/README.md`.
Eight-hour endurance and fresh packet-DMA hardware fault injection remain open.

Root operational tools are in `/home/mit/i960-packet-dma-20261019`.
`~/rtems-console` points there, via `/run/i960-combined.sock`; `quit` disconnects
only. The previous wrapper is `~/rtems-console.before-packet-dma-20261019`.
Public card HTTP remains `http://[2a02:8106:40:9000::960]/` and was fetched from
the Mac during the DMA run. Internet ingress remains unverified.

IPv4 SSH began retransmitting during connection setup after the raw benchmark;
ICMP and the browser status endpoint still responded. IPv6 SSH works:
`ssh -6 -o HostKeyAlias=192.168.2.75 mit@2a02:8106:40:9000:f662:19ee:dbad:1f1e`.
This uses the existing verified host key. The cause of the IPv4 path issue is
not established; do not attribute it to the card or change unrelated network
settings without evidence. The final IPv4 SSH check succeeded without a network
configuration change. The PC did return from reset without another manual
power cycle being reported.

## Combined networking, console and applications — 2026-10-19

Current operational tools/module: `/home/mit/i960-combined-20261019`.
The hardware owner and kernel remain the earlier reclamation session
`/home/mit/i960-reclaim-ipv6-20261019`, session `20261019T175819Z`;
boot `8cdab7ff-48a3-481f-bb54-0924025016c0`. Do not start a second PCI owner.
The new root-only broker `/run/i960-combined.sock` serializes network/application
RPCs with bounded queues and a 3:1 policy when both classes are queued. Set
`I960_RUNTIME_SOCKET=/run/i960-combined.sock` for the combined client and relay.
The independent diagnostic socket still works without the broker.

The combined lwIP module adds two bounded bundled applications (counter and
uppercase echo). `~/rtems-console` now supports `net`, `app list`,
`app start/stop counter/echo`, and `app echo TEXT`, plus existing diagnostics.
Its previous wrapper is backed up as `~/rtems-console.before-combined-20261019`.
These are callbacks inside Init, not arbitrary concurrent segmented applications
or unrestricted RTEMS task cancellation. Generation tokens apply within one
loaded module instance and must be discarded across unload/reload.

The final mixed run passed **601.417 seconds / 4,837 events / zero errors**.
Maximum observed HTTP/console/echo round trips were 2379.350/236.244/1657.962 ms.
The concurrent full-zone loan wrote/read **6,291,424 bytes in 192 steps**, retained
two cancelled references safely and refused close until release; maximum RPC
was 829.627 ms under load. These are observed host latencies, not IRQ bounds.
The first direct-client run had one HTTP timeout and is retained as failed
evidence; the first broker prototype was stopped early to fix ingress batching.
The precise cause of the initial HTTP timeout is not established.

Use the **root-level** `i960-combined-20261019/public_ipv6.py` for routing
removal/reapply: it handles a missing TUN after relay death. Earlier frozen
bundle helpers predate that correction. Card HTTP remains
`http://[2a02:8106:40:9000::960]/`; LAN access is tested, Internet ingress is not.

DMA archives for profiles 6–13 and the current kernel's prior 64-frame baseline
were replayed, and native DMA ownership tests passed. No fresh DMA fault/NMI was
injected in this combined run. **Packet transport is still PIO; packet DMA
acceleration is unqualified.** The current owner sleeps 100 ms in its idle loop;
qualify fast service polling independently of slower ownership audits before
comparing packet DMA and PIO under identical scheduling. This needs a fresh
owner baseline, not modification of the live process. One-hour/eight-hour
endurance and bounded underlying owner journals remain open.

Recovery passed on the same boot and PCI-owner PID: abandoned client, occupied
upload refusal, relay pause/resume and death, broker death/restart, and interrupted
upload rejection/abort followed by a pristine module reload. Both apps, the
prompt and routed HTTP were restored. This tests host service/module recovery,
not new PCI-owner death, hardware reset or DMA fault injections. The first
recovery attempt stopped before injection on unsupported systemctl spelling;
`--kill-who=main` corrected it. P8 is bounded integration; P9 packet acceleration
is open; P10 has these recovery cases; P11 has the ten-minute stage only.

Design and reproduction: `rtems/accele160/runtime/COMBINED-SERVICE.md`.
Evidence: `artifacts/current/accele160-combined-20261019/README.md`.

## Accele160 idle-zone reclamation and global IPv6 — 2026-10-19

Live bundle: `/home/mit/i960-reclaim-ipv6-20261019/bundle`, session
`20261019T175819Z`, boot `8cdab7ff-48a3-481f-bb54-0924025016c0`.
Kernel SHA256 `26b916dfd1c85a986d24b4bac17c7972b8b5108fed5bb56e9d0028afbed6bc80`.
The original prompt and card-side network service remain the intended final state.

The idle Doom zone now has a guarded, generation-owned loan API. The hardware
qualification wrote and verified **6,291,424 bytes** inside the existing 6 MiB
parent allocation, over 192 bounded calls. It cancelled while two pins remained,
refused new access, premature release and module close, then drained both pins
and returned the loan. Maximum observed RPC was **206.356 ms**, not an interrupt
latency bound. Networking timer calls advanced from 178 to 1666 through the test.
The ordinary baseline passed 64 frames / 5,045 WAD reads; 949 external prompt
exchanges passed. Hello plus two network loads and the existing heap proofs passed.

This makes the retired zone available through a kernel loan API and test wire,
not yet through module imports or RTEMS malloc/workspace. The qualification
returns the loan at the end. No new stock memory was taken, and 10–12 MiB total
ownership is still gated on SXP/DMA exclusion and firmware allocation analysis.
See `rtems/accele160/runtime/RECLAMATION-CANCELLATION.md`.

**Unrestricted task cancellation remains unimplemented.** The module still runs
inside Init and the ISR has exactly four owned contexts. The new cancellation
code revokes allocation access and retains outstanding references; it does not
kill arbitrary tasks, release held RTEMS locks or invent DMA completion. The
contract records the separate application-task/context, supervisor channel,
dependency tracking and fault-test gates required next.

Card global address: **`2a02:8106:40:9000::960`**, HTTP port 80. The global-address
module preserves `10.196.0.2` and `fd96:196:960::2`. Host routing/proxy NDP is
implemented by the corrected **root-level** script
`/home/mit/i960-reclaim-ipv6-20261019/public_ipv6.py`; use it for removal/reapply,
not the earlier helper frozen inside the bundle. The first helper enabled only
interface forwarding; LAN SYNs reached the host but were not forwarded. Linux's
IPv6 forwarding path also requires the global switch. The corrected helper
saves/restores global and interface settings, preserves unrelated interfaces,
and restricts newly enabled IPv6 forwarding to the card. It also enables global
proxy NDP for unicast neighbor refresh. IPv4 forwarding policy is untouched.

Twenty HTTP requests from the Mac passed against the global address; public
TCP/9600 was blocked. Host IPv4/IPv6 ping and HTTP passed. No host HTTP proxy is
involved. Internet reachability is **unverified**: the external fetch tool could
not test an IPv6-literal URL. The upstream router may need an inbound IPv6 HTTP
rule for the card address. Do not call LAN success an Internet test. Routing is
explicit, temporary and prefix-specific; remove it before stopping the TUN relay.

Evidence: `artifacts/current/accele160-reclaim-ipv6-20261019/`. Earlier immutable
runtime bundles and the stock/coexistence option remain preserved.

## Latest Accele160 state — 2026-10-19 resident applications/network

Read `docs/rtems/ACCELE160-PORT-PLAN.md` and `rtems/accele160/runtime/README.md`
before touching the card. Live immutable bundle: `/home/mit/i960-runtime-port-v4-20261019/bundle`;
session `20261019T140746Z`, boot `2433f02b-0e55-4467-a072-0b2c70c8fb48`.
The prompt and card-side IPv4/IPv6 HTTP are running. Root owner sockets:
`/run/i960-rtems-console.sock`, `/run/i960-rtems-runtime.sock`. TUN `accele0`
serves card `10.196.0.2` / `fd96:196:960::2`; host gateway 8088 remains separate.
Do not create a second PCI owner or overwrite this active bundle. The application
service owns its qualified idle lease; browser restarts are refused. Normal
Doom-only profile is preserved at `/home/mit/i960-owned-runtime-20261018/bundle`.
Global shutdown retains the firmware callback, grant and DMA pins until reset.

Profile 19's paused DMA-window reads/restoration passed. DMA/SCSI exclusion and
10–12 MiB ownership remain unproved. The new 512 KiB reservation is within the
already qualified upper arena, split into 384 KiB module and 128 KiB general
heap; existing workspace/stacks are unchanged. Module wire fields are explicit
LE words: i960 structs have different padding. The host opens application
admission only after all idle audits. Disconnected completed clients are retired;
uncertain card I/O remains quarantined. Preserve bundle-generated
`engine_identity.h` matching its engine; the repository's older generated header
must not overwrite it. Tests, rejected runs, binaries and sources are in
`artifacts/current/accele160-qlogic-dma-bank-20261019/` and
`artifacts/current/accele160-runtime-port-20261019/`.

**2026-10-19 Accele160 RISC control:** Profile 18 qualified one-shot pause/release:
HCCR 0000→0020→0000, one poll each, controls/indices unchanged. It does not prove
SXP/DMA drain or new RAM ownership. CONF1 bank bits must be clear before HCCR;
its address aliases DDMA_CONF in the DMA bank. No timeout retry or speculative
rollback; retain all resources for reset on uncertainty. Normal profile 5 and
prompt/gateway are restored. Read the [current checkpoint](docs/rtems/ACCELE160-PORT-PLAN.md),
[profile 18](rtems/accele160/ownership/PROFILE18.md) and
[stop contract](rtems/accele160/ownership/STOP-CONTRACT.md) before card work.

**2026-10-19 Accele160 chip/cache comparison:** Profile 17 confirms chip request
consumer 37 versus cached 0, with software producer 37; response indices are 22.
All four phases/eight passes agree. ISR is zero, semaphore is 2 (STATUS set,
LOCK clear), not an all-zero status. No chip writes, drain proof or new RAM grant.
Normal profile 5 and prompt/gateway are restored. Read the
[current checkpoint](docs/rtems/ACCELE160-PORT-PLAN.md) and
[profile 17 contract](rtems/accele160/ownership/PROFILE17.md) before card work.

**2026-10-19 Accele160 queue snapshot:** Profile 16 checks the exact QLogic
context and captures fixed RAM fields without pointer traversal or chip access.
Physical capacities correct the prior inference to 256/128 entries (16/8 KiB).
Pending/active counts are zero but request indices are 37/0; no hardware drain
or new RAM ownership is proved. Normal profile 5 is restored; consult the
[current checkpoint](docs/rtems/ACCELE160-PORT-PLAN.md) and
[profile 16 contract](rtems/accele160/ownership/PROFILE16.md) before card work.

**2026-10-19 Accele160 QLogic corroboration:** Opt-in profile 15 confirms the
physical secondary device is ISP10160 `1077:1016`, revision 6, memory BAR
`fff00000`, with memory decode and bus mastering enabled. Earlier firmware
revision metadata was zero. The probe restores SOCCAR and never writes device
configuration; no SCSI isolation or extra RAM ownership is established. See
[runtime contract and queue dependencies](rtems/accele160/ownership/PROFILE15.md)
and the [current port checkpoint](docs/rtems/ACCELE160-PORT-PLAN.md) for the
restored service and next gate. Keep normal profile 5 as the prompt owner.

**Cached new-card Doom screen copy — 2026-10-18:**
[Two full card archives](artifacts/current/wide-screen-copy-20261018/README.md)
show the opt-in `game/doom/build.py --wide-screen-copy` reducing the measured
internal screen copy from 6.5 to 3.0 ms/frame and raising the 20-frame steady
card FPS from 16.964 to 17.593 (+3.70%) twice. All pixels, WAD, native,
PIO/DMA/HTTP, owner/STOP/stalled-host, system, tamper and paired pre/post-reset
stock-flash audits pass. Keep `I_VideoBuffer` persistent and DMA slots separate;
this is a faster copy, not safe zero-copy. The option is tested only for the
exclusive cached AcceleRAID low-detail/hash-off build and remains opt-in.


**Cached Doom N3 experiment — 2026-10-18:**
[Clip-copy evidence](artifacts/current/clip-copy-20261018/README.md) shows
cached BSP/walls 27.5 ms, planes 14.5 ms and masked drawing 6.0 ms in the
20-frame steady window. Optional `game/doom/build.py --fast-clip-copy` changes
only the two wall clip-array copies. Native checks and 32 exact-pixel card
frames with full ownership/system/frame/WAD/STOP audits passed, but FPS stayed
16.964 and BSP/walls stayed 27.5 ms. Do not make it default or claim a gain.
Next measure texture/column locality and the 6.5 ms presentation copy.


**CPU-to-SDRAM measurement — 2026-10-18:**
[Full physical-capture replay and method](artifacts/current/cpu-sdram-20261018/README.md)
give new-card cached-map CPU-loop rates of 7.08 MiB/s for repeated 64 KiB
reads, 7.02 MiB/s useful copied bytes, and 36.36 MiB/s write-through clear.
The stock-map 64 KiB rates are effectively the same; that working set exceeds
the 4 KiB cache. These are timed CPU workload rates, not pure DMA or peak bus
bandwidth. Keep the distinction when planning renderer optimizations.

**Current exclusive-Doom cache baseline — 2026-10-18:**
[Matched cached-card baseline](artifacts/current/cache-baseline-20261018/README.md)
checks all 120 old-card and 32 new-card diagnostic frames. The old PG already
caches its 16 MiB RAM with LMT0 (`dcctl4=0x7221`, 2 KiB); the new 160 caches
the owned upper 8 MiB with accepted LMT1 (`dcctl4=0x8221`, 4 KiB). The same
admitted engine has 1 KiB read medians 700 versus 130 ms and word-copy medians
990 versus 570 ms. `rtems/accele160/doom_dma/build.sh` now defaults to the
accepted private map **for exclusive Doom**; set `DOOM_PRIVATE_CACHE_MAP=0`
for the stock-map control. Runtime ownership, register restoration, WAD/control
invalidation and full audits remain required. Long interactive play is unproven.

**N2 cache-map acceptance — 2026-10-18:**
[Exact code, captures and replay](artifacts/current/cache-map-20261018/README.md)
show `DOOM_PRIVATE_CACHE_MAP=1` remapping only LMT1 to reboot-owned
`c0800000–c0ffffff` during Doom, then restoring stock after DMA drain.
Warm 1 KiB reads improve 2.77×; the previously accepted no-benchmark,
low-detail/hash-off Doom engine improves from 9.694 to **16.964 card FPS**
in the 20-frame steady window (+75%). Two 32-frame runs passed full audits,
STOP and paired guarded post-reset stock-flash reads. Retain WAD/control invalidations and all ownership/DMA
checks; longer interactive play and disconnect acceptance remain open.

**Latest N1 cache-scaling result — 2026-10-18:**
[Exact matched card evidence and replay](artifacts/current/cache-scaling-20261017/README.md)
show the AcceleRAID 160's D-cache globally enabled but its reboot-owned
upper-bank Doom arena uncached by both stock logical templates. The DAC960PG
does cache its Doom allocation. Identical admitted code gave 5.35× arithmetic
but only 1.94× warm-read and 1.74× repeated word-copy speedup. Both cards
passed full ownership/system/frame/WAD audits and STOP; final paired new-card
stock-flash reads and archive replay passed. No cache register or flash was
written. N2 is a separate bounded, reboot-only **private-RAM** cache-map
experiment; host-written control/WAD pages must remain coherent and full
audits must stay on. These diagnostic timings are not Doom FPS.

**AcceleRAID direct Doom DMA physical run — 2026-10-17:**
The [exact bounded capture](artifacts/current/accele160-doom-dma-20261017/README.md)
passed 32 guarded channel-0 DMA frames and identical HTTP packets, four full
PIO comparisons, exact native WAD startup order, three-second held-host
buffer immutability, engine cleanup and quiescent STOP with all ownership
and system audits. Exact old optimized low-detail engine pixels/palette match
for all frames. Frames 12–31 give **7.819 card FPS / 7.878 HTTP-observer FPS**,
versus old optimized 6.35–6.40 and previous new high-detail 2.331. The latter
3.35× change combines renderer/quality/transport changes, not CPU speed.
Observed-to-HTTP availability is **2.03 ms**; renderer wall/sampled CPU is
91.5/90.5 ms. Full card transport FNV remains on and native host FNV is now
integrated. Both extra adapter copies disappear after the first four paired
qualification frames. Inclusive FPS with deliberate three-second stall is
4.480. **Two matching guarded full post-reset flash reads now close this run.** No firmware writes, old card unbound, buffers reboot-pinned; never
force-unload. This is a 32-frame gate, not persistent play. An optional card-hash-off run also passed 32 guarded DMA/HTTP frames and
STOP at **9.694 card / 9.643 observer FPS**, with identical pixels/palette and
full system checks and matching paired full post-reset flash reads. Both modes
retain native host hashing; card hashing defaults on. Scalar 4 KiB WAD
service, long interactive STOP and switchable quality remain ports. Half-height stays on hold. Older status below is history.

**Latest 2026-10-17 status:** AcceleRAID Doom startup, two-slot frame output
and a bounded browser/key gate are accepted; earlier bring-up notes below
are historical. The [old/new delay comparison](artifacts/current/card-delay-comparison-20261017/README.md)
passed a 32-frame new-card profile and a fresh 120-frame old-card run with
47 full paired audits plus paired new-card pre/post stock-flash reads.
New adapter copy/staging/FNV totals 154.52 ms/frame; host Python FNV adds
19.58 ms before HTTP. Native host FNV is benchmarked but not integrated.
Old optimized low detail delivers 6.35–6.40 FPS; new high detail 2.331
card-side FPS. This is not a processor-speed ratio. Follow the measured
backlog: exact native host validation, word copies, owned DMA/direct
presentation, then matched engine/quality profiling. Long play and clean
user STOP still need acceptance; half-height remains on hold. Current
accepted defaults and binaries were not changed by this measurement work.

**2026-10-17 AcceleRAID full-WAD service accepted:** [Exact code and
capture](artifacts/current/accele160-doom-wad-service-20261017/README.md).
The new card completed 38 card-requested Freedoom reads across the full
28.8 MB file; bad FNV, stale sequence, timeout and STOP were rejected,
with full cache readback, bank/owner guards, old-card isolation and two
matching guarded post-reset full-flash reads. The bank claim now saves
arbitrary residual page contents, then proves a full reversible 2,048-page
marker/alias/pattern/restore audit. The exact Doom image is admitted but
**not executed**. Next connect the service to the Doom runtime ABI and call
a bounded first-frame entry; keep this WAD protocol and full audits intact.

**2026-10-17 AcceleRAID Doom bridge:** [Physical capture and exact
limits](artifacts/current/accele160-doom-bridge-20261017/README.md) prove a
guarded 900,000-byte engine allocation, contiguous 6 MiB zone candidate,
65,536-byte frame, exact 867,792-byte image admission and relocation, WAD
header input, diagnostic-frame output and retained STOP on the new card.
The bridge is a one-shot, reboot-only operation-13 session; no Doom entry
was called and no full WAD was moved. Upper DRAM retains prior patterns
across boot and stock rewrote its first pages. Preserve the exact card-side
preimage/alias audit and exclude `c0800000..c080ffff` and
`c0ff0000..c0ffffff` from the arena. Do not unload a retained module or
free its grant. Post-reset acceptance passed on boot
`994bfdd8-8664-4516-86a8-36d6555d6a78` with two matching complete guarded
flash reads and an idle stock descriptor.

**2026-10-17 AcceleRAID full-bank/reboot-only update:** [The physical capture](artifacts/current/accele160-fullbank-20261017/README.md) proves distinct, writable `c0800000..c0ffffff` under a held exclusive operation-13 callback. Two firmware-populated pages were saved/restored during the finite proof. The reboot-only image then patterned the entire 8 MiB, kept the stock callback pending, passed all 1,024 host-readable odd-page checks, timer heartbeat and quiescent STOP. A reset is the only release; post-reset flash/cold-boot acceptance passed after a fresh power cycle. Do not unload its pending module, free its grant, use stock commands while retained, or assume Doom's new-board allocator/transport exists. Read [the arena contract](rtems/accele160/ARENA.md) before new work. Older read-only rejection text below is historical.

**2026-10-17 AcceleRAID finite exclusive timer gate:** [Combined two-page RTEMS test](artifacts/current/accele160-exclusive-timer-20261017/README.md) passed with stock CPU path paused, all three DMA channels idle, two patterned pages held during timer-driven preemption, exact STOP/120-tick timeout, full page/context/owner/loader/stage restoration, four complete guarded flash reads, replay and tamper rejection. [Earlier upper-page](artifacts/current/accele160-exclusive-probe-20261017/README.md) and [occupied stock-page](artifacts/current/accele160-occupied-probe-20261017/README.md) reversible probes also passed. All three images **return to stock firmware**. The [read-only survey](artifacts/current/accele160-doom-arena-20261017/README.md) still rejects an **8 MiB** upper-bank arena: selected-page round trips are not full-bank alias freedom or persistent ownership. Do not upload Doom or treat stock-occupied RAM as permanently reclaimed until the [reboot-only exclusive contract](rtems/accele160/EXCLUSIVE-MODE.md) is implemented and physically accepted. Largest stock free run: 1,540,096 bytes.

**2026-10-17 AcceleRAID external-resume gate accepted for a finite transfer:** [Exact procedure and limits](rtems/accele160/dma_external_resume/README.md). The owner died at held DMA; independent recovery sent RESUME at tick 101 (STOP tick 21), and all owner/page/stage, DMA/payload/guard, RTEMS/context, cleanup and four full stock-flash audits passed. The old card remained unbound. Earlier apparent `myrsread` non-binding was caused by omitting mandatory `read_bdf=0000:37:09.1`; exact insertion bound immediately. This does not prove release behind a never-draining PCI transaction.

**2026-10-17 AcceleRAID pre-STOP DMA process-death gate:** [Exact source and limits](rtems/accele160/dma_pre_stop_death/README.md), [accepted captures](artifacts/current/accele160-dma-pre-stop-death-20261017/README.md). Two fresh-buffer runs killed the host owner after `DMA_BUSY` but before STOP; independent recovery retained pin/grant through normal finite DMA completion and tick-300 expiry, then passed full audits and released them. Six full flash reads and 16 replay tamper rejections passed. Do not infer a safe release path for genuinely stalled/erroring PCI DMA or a whole-host crash. Keep resources pinned on uncertainty.

**AcceleRAID 160 two-task post-return lease accepted (2026-10-17):**
[Source and boundary](rtems/accele160/residentworkers/README.md),
[exact image and live captures](artifacts/current/accele160-residentworkers-20261017/README.md).
Init suspends after starting a separate RTEMS worker. The worker polls exact
HALT or tick-300 expiry, resumes Init with task preemption disabled, and
suspends itself before Init shuts down the whole instance. Two HALT/expiry
batches passed at ticks 22/300 with 2/280 worker IRQs, six full flash reads,
three stock inventories, owner/page/stage restoration, replay and ten tamper
rejections. No flash write; old card unbound. A first sleep-based trial stayed
ACTIVE and needed a recovery boot; diagnostic captures are saved. This does
not prove DMA ownership, general resident preemption or recovery from
permanently masked interrupts. Next qualify a bounded DMA owner and prove
completion/timeout drain before the grant is released.

**AcceleRAID 160 post-return RTEMS task accepted (2026-10-17):**
[Exact source and boundary](rtems/accele160/residenttask/README.md),
[two live batches, six full flash reads, inventories and replay](artifacts/current/accele160-residenttask-20261017/README.md).
One RTEMS task started from a retained firmware timer ISR after operation 13
returned; exact HALT stopped it at tick 22, no-host expiry at tick 300.
Stale STOP was ignored. Whole-instance RTEMS shutdown returned to the
retained ISR, which restored timer/vector/map/mask, processor priority and
firmware stack. Both ISR stack guards, task identity/progress/stack, owner,
loader page and staging source passed. No firmware write; old card unbound.
Do not call this DMA ownership, independent watchdog recovery or
service-grade multi-task quiescence. The next physical gate is explicit DMA
and task ownership with full STOP/expiry drain before releasing the grant.

**AcceleRAID 160 callback-free RTEMS timer accepted (2026-10-17):**
[Source and finite boundary](rtems/accele160/residentclock/README.md),
[exact binary, four full flash reads, stock inventories and replay](artifacts/current/accele160-residentclock-20261017/README.md).
RTEMS early initialization preceded operation-13 return; its timer callback
fired at tick 20 after host ENTER in a stock-firmware interrupt frame.
HALT stopped at tick 21 and no-host expiry at tick 300. All timer/vector,
priority, firmware stack, page/stage and allocator state restored. Old card
unbound; no firmware write. **Do not call this a resident RTEMS task:**
multitasking never started. Next prove task continuation and complete
task/ISR/DMA quiescence before grant release. Never force-unload an uncertain
one-shot module; the runner retains the grant for guarded recovery.

**AcceleRAID 160 bounded timer/IRQ gate accepted (2026-10-17):** [RAM-only source and build](rtems/accele160/timer/README.md), [full card evidence](artifacts/current/accele160-timer-20261017/README.md). The unchanged operation-13 firmware admitted a three-page image with separate owned entry and ISR stacks. Exact idle-state guards permitted temporary timer-1/vector-18 borrowing; cached F2 is occupied by firmware and untouched. Two fixed 8-IRQ paths and stale/valid STOP after 13 and 201 IRQs passed. The longer host sample was 1,253.04 IRQs/s at reload 10,000. Three independent pre/post timer/vector inventories, four full guarded 1 MiB flash reads, loader/stage/512-owner restoration, and four offline tamper rejections passed. Firmware SP restored to `c0002100`; no one-shot modules remain. This is a bounded bare ISR proof, **not yet an RTEMS hardware clock or a resident service**. Next integrate the proven ISR with bounded RTEMS clock/task wakeup and STOP/drain/restore.

**AcceleRAID 160 RTEMS task STOP accepted (2026-10-17):** [Exact RAM-only image, build and verifier](rtems/accele160/lease/README.md), [card capture](artifacts/current/accele160-rtems-lease-20261017/README.md). Operation 13 ran a 16-page RTEMS 4.6.6 image without another flash write. A worker task acknowledged nonce/epoch STOP in 48.829 ms after rejecting a stale token; no-host polling exited in 1.503 s. RTEMS shut down, firmware SP returned to `c0002100`, and full same-boot flash, owner, loader-page, stage and stack audits passed. The accepted image rebuild is byte-identical and offline replay rejects four tampered captures. **STOP is cooperative; an uncooperative task still needs a separate enforced deadline/recovery path.** The next gate is guarded short timer/vector/owned interrupt stack with full restore, not networking or Doom yet. Never force-unload a pending one-shot command.

**AcceleRAID 160 owned-stack and cooperative STOP accepted (2026-10-17):** [RAM-only source and boundary](host/accele160/lease_probe/README.md), [full evidence and replay](artifacts/current/accele160-lease-20261017/README.md). A two-page manifest image switched from firmware SP `c0002100` to a worker SP `c0711fc0` in its owned second page, then restored the firmware SP. A stale STOP stayed pending; exact STOP returned ACK in 23.4 ms, and the fixed 2,000,000-poll no-host path returned TIME in 1.04 s. The even code page cannot be read directly through BAR0; the first harness stopped before execution, verified its completed copy and safely released the grant. The corrected run used card-side digests for that page. Loader/stage/512-owner audits and a complete post-call flash read passed; no firmware write occurred. This is cooperative returning code, not forced interruption of an uncooperative image or RTEMS task quiescence. Next integrate STOP into a bounded RTEMS task before timer/vector ownership.

**AcceleRAID 160 reusable RAM admission accepted (2026-10-17):** [Operation-13 source](host/accele160/ram_admit/README.md) and [full acceptance evidence](artifacts/current/accele160-ram-admit-20261017/README.md). A 4,324-byte handler preserves operations 1–12 and adds a manifest-checked, returning 1–127-page RAM entry in the stock-owned 512 KiB grant. Candidate SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd` persisted across reboot. Two distinct RAM probes completed through the same firmware, six bad manifests were rejected, four postboot/postcall complete reads matched, and page/stage/512-owner audits passed. Operation-11 STOP and fixed operation-9 RTEMS were retested successfully. Replay and four tamper variants passed. This is a trusted **returning-image** gate; it does not enforce a finite lease or provide autonomous RTEMS, task-aware STOP quiescence, networking or Doom. Follow [next gates](rtems/accele160/TIMER-NEXT.md) before using it for resident code.

**AcceleRAID 160 vector/mode gate (2026-10-17):** [Accepted operation-12 evidence](artifacts/current/accele160-vector-20261017/README.md) reports live cached vector 18 `0xaaaaaaaa` and vector 130 `0xc0000418`; the guarded first TMR1 mode read was `0`, with count/reload/pending/mask/mapping unchanged. Candidate firmware SHA-256 `93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094` persisted across reboot. Six full guarded flash reads, exact code-tail/page restoration, all 512 owner words, STOP compatibility and replay/tamper tests passed. The 3,868-byte handler extends 244 bytes into the `f000` page, so do not assume that page is all erased; pin its code prefix. Cached vector 18 is a sentinel despite blank ROM, and TINT1 still has undefined mapping field zero. This is not vector/timer ownership. Read [source](host/accele160/vector_gate/) and [next gates](rtems/accele160/TIMER-NEXT.md). [Old/new differences](rtems/accele160/OLD-NEW-DIFFERENCES.md) explain the repeated one-shot flash cycles and the planned reusable RAM admission.

**AcceleRAID 160 sideband STOP (2026-10-17):** [Operation-11 acceptance](artifacts/current/accele160-stop-20261017/README.md) proves an independently writable saved-page control word while the `myrsread` direct command holds `dcmd_mutex`. Exact firmware SHA-256 `ef5635d38bf397ff13fa1140ef6265de0b300c70ad8b157c17427013a1d2abb5` persisted across reboot; two postboot and one post-call full guarded reads matched. Wrong STOP `0xdeadbeef` stayed pending, exact nonce/epoch STOP returned status 0 and ACK in a 21.9 ms host-observed cycle, and no STOP returned stock status 2 after the fixed 20-million-poll deadline (10.26 s). The all-FF loader page and PIATVR restored, all 512 allocator records matched, the old PG stayed unbound, and no test module remains. See [exact source and replay](host/accele160/stop_gate/). This proves a bounded callback STOP path, not RTEMS task quiescence, timer/IRQ ownership, or DMA drain. The live cached vector and timer-1 mode remain unqualified; follow [next gates](rtems/accele160/TIMER-NEXT.md) before a timer write.

**AcceleRAID 160 timer inventory (2026-10-17):** [Fixed operation-10 acceptance](artifacts/current/accele160-inventory-20261017/README.md) passed three read-only card calls. Firmware SHA-256 `9d5d4da2c283d10e1dee9c71ceb477f36e389cd0d0548764a3cc5f8a41a24c49`; two postboot and one post-call full guarded reads match, along with staged readback. Timer-1 count/reload were zero, pending zero, timer-1 mask bit clear; timer-0 count moved. The timer mode registers were deliberately not read because Intel documents a read-clear terminal-count side effect. The report page and all 512 allocator owner records restored. Stock changes two bytes at table-page `0xaa0..0xaa1` outside those records; compare only the exact metadata region. Old card `37:04.1` stayed unbound. [Static vector replay](artifacts/current/accele160-inventory-20261017/vector-static.json) finds timer 1 mapped to undefined vector 2 and blank ROM vector 18, but ICON enables live vector caching and cached word `0x04` has not been read. This is not timer, vector, IRQ-stack or STOP ownership. Follow [next gates](rtems/accele160/TIMER-NEXT.md) before any writes. Exact source and replay are in [inventory_gate](host/accele160/inventory_gate/).

**AcceleRAID 160 RTEMS gate (2026-10-17):** [bounded new-board RTEMS acceptance](artifacts/current/accele160-rtems-20261017/README.md) passed twice from a stock-owned 512 KiB grant. This is RTEMS 4.6.6 task scheduling with ten synchronous software ticks and worker wake at tick five; it is not new-card timer/IRQ/STOP, networking or Doom. Exact firmware SHA-256 `68451b38b96609fa3a95eb9497fe85a34ac92fec45b912c53612969b1209a988`, padded task SHA-256 `318b9f70fe021ce1fb18e3c75465d9231cb55c3ca6893d99511b9b73c383adc0`. Old card `0000:37:04.1` stays unbound; new card `0000:37:09.1` is bound to exact `myrsread`. Read [new-board profile](rtems/accele160/README.md), [handler and host gate](host/accele160/rtems_gate/) and full evidence before further card work. Follow [timer/STOP gates](rtems/accele160/TIMER-NEXT.md); a stock-ROM literal scan is not timer ownership. Never force-unload a pending one-shot companion; full flash and allocator audits are required.

# Current status and artifact policy (2026-10-16)

## AcceleRAID RTEMS-sized bulk transfer accepted — 2026-10-17

On new card `37:09.1`, a single stock-owned 512 KiB grant received 77
validated 4 KiB pages (315,392 bytes) under exact persistent op-8 firmware.
All per-page host readbacks/card FNVs, 77 command statuses, full-region card
FNV `0x11a9edc5`, owner/page/staging restoration, post-test guarded 1 MiB
flash read, replay and tamper checks passed. Upload took 6.118 s and digest
0.101 s in one run. Read
`artifacts/current/accele160-bulkupload-20261017/README.md`. This is a
deterministic transfer scale proof, not an AcceleRAID RTEMS build or task.
A 77-page image leaves 204,800 bytes in the 127-page payload area; actual
BSS/heap/stack needs remain to be measured for a new-board port.

## AcceleRAID owned-RAM exact leaf accepted — 2026-10-17

The exact op-8 candidate SHA `6f056a98…480aa7` persisted after reboot on
new card `37:09.1`; two guarded 1 MiB reads matched. An 80-byte leaf
was uploaded at owned `c0710000`, admitted by an 8 KiB card-computed FNV
`0x699d962b` and exact byte comparison, then called after I-cache invalidate.
It returned normally with nonce `0x16161081` and sum 496. Bad digest and
modified code both returned status 2 before a result write. A second normal
call, full owner/page/staging restoration, post-call full-flash reads, replay
and tamper checks passed. Old `37:04.1` stayed unbound. Read
`artifacts/current/accele160-ownedexec-20261017/README.md` and sources in
`host/accele160/ownedexec/`. This proves an exact leaf, not arbitrary task
execution or an RTEMS board port.

## AcceleRAID owned-image digest accepted — 2026-10-17

The exact op-7 candidate SHA `665cb121…5c708a0` persisted across reboot on
new card `37:09.1`; two guarded 1 MiB reads matched before testing. A single
owned grant received two contiguous 4 KiB pages, and the card returned the
expected whole 8 KiB FNV `0x3201b5c5`. Bad hash and page count 128 returned
stock status 2 without modifying the independently readable target. Full
owner/page/staging restoration, post-call and post-negative flash reads, live
replay and tamper tests passed. Old `37:04.1` stayed unbound. Read
`artifacts/current/accele160-digest-20261017/README.md` and exact sources
in `host/accele160/digest/`. This is transfer admission, not executable code
from the grant; cache-safe entry and RTEMS BSP remain next.

## AcceleRAID card-side even-page copy accepted — 2026-10-17

Read `artifacts/current/accele160-pagecopy-20261016/README.md` first. Exact
firmware SHA-256 `183eed37…d197f4a` persisted on new card `37:09.1`; two
guarded full-flash reads matched before testing. Under a fixed 512 KiB stock
owner at `c0710000`, operation 6 copied 4 KiB from odd staging page
`c078f000` into even page `c0710000` and reported destination FNV
`0x6121fdc5`, matching the staged data. Staging, controls, loader page and all
allocator count/owner words restored; reserve/copy/release status and residual
were zero; three modules unloaded; post-call flash and independent snapshots
passed. Old `37:04.1` stayed unbound. Additional same-boot runs copied indexes 1 and 126 and rejected a bad staged hash
and index 127 with stock status 2; full page/owner/staging audits and a final
guarded 1 MiB flash read passed. One host checker error on the first index-127
run retained resources and was fully cleaned up under exact readback checks.
A separate same-grant two-page session copied indexes 0 and 126, passed independent replay and tamper checks, and left flash unchanged. This is sampled page coverage, not a general RTEMS loader. Whole-image digest,
cache-safe execution and RTEMS BSP remain unproved. See
`docs/hardware/accele160-upload-plan.md` for the next gates.

## AcceleRAID retained 512 KiB grant accepted — 2026-10-16

Read `artifacts/current/accele160-retained-20261016/README.md` first. The exact
1 MiB retained candidate SHA-256 `e7a3a7c5…d6ffc0` persisted across reboot on
new card `37:09.1`; two guarded full-flash reads matched. Fixed operation 4
reserved `c0710000..c078ffff` with owner `0x96016004` across 16 stock blocks.
Separate operation 5 released it; all 256 count and 256 owner words, the loader
page and PIATVR restored. Both modules unloaded, post-call flash matched, and
the old `37:04.1` remained unbound. No RTEMS upload or execution has happened.
BAR0 exposes only odd 4 KiB pages of each 8 KiB pair. A separate
reversible 4 KiB write/read/restore passed at owned page `c0711000`, followed
by full flash, loader-page and allocator snapshots. A general image still
requires a bounded card-side copy or proven DMA to fill even pages. See
`docs/hardware/accele160-upload-plan.md` before extending the firmware.

## AcceleRAID stock allocator operation accepted — 2026-10-16

Read `artifacts/current/accele160-allocator-20261016/README.md` first. Exact
1 MiB candidate SHA-256 `0124657d…799dd5d0` was programmed on **new card
`37:09.1` only**. After reboot, two guarded full-flash reads matched it;
returned fixed 256 KiB stock allocation `c0750000` was freed with identical
caller ID. All 256 count and 256 owner words returned to their preimage. The
first command's session overcompared an adjacent firmware word and needed a
separate verified cleanup; the corrected second call passed normally. Both
result slots were restored, modules unloaded, PIATVR returned to `c0000000`,
independent final table/page snapshots matched and post-call flash matched.
The old `37:04.1` stayed unbound and untouched. The temporary `myrs` blacklist
remains, and custom `myrsread` needs `raid_class` plus exact
`read_bdf=0000:37:09.1` on a fresh boot. This is only a transient allocator
proof; RTEMS still lacks a retained owner-tagged grant, chunk upload and safe
execution. Doom still lacks an 8 MiB owned arena.

## AcceleRAID RAM execution accepted — 2026-10-16

Read `artifacts/current/accele160-ramprobe-20261016/README.md` first. The exact
1 MiB candidate, SHA-256 `1f13799b…6c4aaf`, is **persistently programmed** on
new card `37:09.1`; two same-boot guarded full-flash reads matched it after a
physical power cycle. Valid and bad-signature PING controls passed. Two
independent bounded operation-2 calls executed the pinned 80-byte RAM payload
and returned exact result words with status/residual zero. Full-page captures
proved only the 16-byte result and 80-byte code slots changed; both runs
restored the entire page and PIATVR. An independent final page matched the
preimage; a guarded post-call flash read matched.
Both command modules unloaded; the old `37:04.1` remained unbound and untouched.
The exact live receipts are under `artifacts/current/accele160-ramprobe-20261016/live/`.

**Do not mistake this for a general loader or RAM grant.** Operation 2 only
accepts its embedded 80-byte payload. The read-only high-DRAM survey in
`docs/hardware/accele160-memory-map.md` found zeros but proved no allocator or
exclusive ownership. A later read-only capture found the stock allocator's
256-entry count/owner arrays: lower blocks 154–191 (1,245,184 bytes) and
upper blocks 195–241 (1,540,096 bytes) are currently free, but no allocation
has been granted. `c0066b90`/`c0066430` are the decoded allocation path;
`c0066fc0` is the stock release path. See the memory-map document and pinned
table parser before designing the next helper. RTEMS, web and Doom remain
old-card-only until an owned reservation, chunked upload, timer/IRQ and STOP
are ported. A temporary
`/etc/modprobe.d/i960-accele160-temporary.conf` still blacklists `myrs` so
`myrsread` can bind first after a cold boot; record/remove it when ending this
new-card development session. Never unload a retained pending command.

The 80303 BAR upper half maps **PIATVR + `0x1000`**, and PIATVR is 8 KiB aligned.
Host-accessible loader scratch is therefore in odd 4 KiB pages; the fixed
probe lives at `c000f900`, not `c000e900`. The dedicated run script requires
two same-boot full-flash reads matching the candidate before loading its
companion. Keep the accepted stock ROM for external-programmer recovery.

## AcceleRAID programmed late-PING helper — 2026-10-16

The user accepted recovery risk with an external programmer available. The
exact late-PING candidate was staged on the **new** `37:09.1`, read back as
1 MiB, and programmed via one `FLASHIMAGE` command with status 0. After the
user power-cycled the PC, the card booted; two guarded 1 MiB reads matched the
candidate exactly. Valid PING returned status 0, one-byte-bad signature
returned stock unsupported status 2. The old `37:04.1` remained unbound.
The temporary `myrs` blacklist was removed; `myrsread` remains bound to new
card in the current boot. No further flash command is needed. The accepted
stock image is the external-programmer backup; boot-block recovery remains
untested. See `artifacts/current/accele160-flash-candidate-20261016/README.md`.

Sections below preserve earlier dated findings and may say the candidate was
offline at the time; this accepted flash result supersedes that state.

## AcceleRAID boot recovery gate — 2026-10-16

The accepted stock boot block samples a UART once: `S` enters a copied
recovery handler, while `!` selects manufacturing mode. A flash-control bit
can also select recovery, but is not a safe host-controlled trigger. The live
UART-like probe previously failed. Recovery and stock restoration are **not
physically proven**; do not flash the offline late PING candidate based only
on static recovery code. See
`artifacts/current/accele160-recovery-audit-20261016/README.md` and run
`host/accele160/startup/audit_recovery_route.py` on the accepted stock dump.

## AcceleRAID helper-site audit — 2026-10-16

Offline stock analysis found unused diagnostic subcommand `0x8f` (currently
returns unsupported status `0x104`) and 7,720 erased loader bytes copied to
RAM. A dormant 80-byte probe insertion with recomputed loader/trailer checksums
passes the known analyzer, but no entry is wired, no image is exported, and no
flash write was attempted. The command ABI, compressed-runtime table patch,
owned RAM and recovery remain open. Do not treat this as a flashable image.
See `artifacts/current/accele160-helper-site-20261016/README.md`.

## AcceleRAID debug interface — 2026-10-16

The stock loader's UART presence probe selected disabled callbacks on the live
new card: input always returns `q`, output is a no-op. The debug-menu D-cache
key is `e` (the prior audit mislabeled it `d` due an offset error). Code Manager
offers memory diagnostics, not a safe arbitrary call or I-cache handoff. Do not
try to enter it by patching the cacheable callback table or by using the memory
fill option. The bounded probe still has **not** executed. See
`artifacts/current/accele160-debug-interface-20261016/README.md`.

## AcceleRAID cache gate audit — 2026-10-16

The stock runtime has an interactive debug-menu `dcctl 2,0` and several other
D-cache invalidations, but none is a proven host-command cache gate. Its
verified `sysctl 0x300` reinitializes the processor. Do not post a synthetic
software interrupt by writing pending bits: the 80303 keeps pending priority
internally and can cache vectors. The previous RAM upload succeeded; custom
code still has not run on this card. See
`artifacts/current/accele160-cache-gate-20261016/README.md`.

## AcceleRAID RAM upload route — 2026-10-16

Intel 80303 ATU decoding proves BAR0's upper 4 KiB is a movable local-RAM
aperture. A guarded 256-byte live round trip at local `0xc0001e00` uploaded the
80-byte bounded probe, passed exact readback, restored every original byte, and
left identical full-page SHA-256 snapshots. PIATVR returned to `0xc0000000`, SSH
remained healthy, and old DAC960PG `37:04.1` remained unbound and untouched.

Do not execute through the tempting IOCTL `0x8e` pointer patch. Its callback
table and dispatcher are cacheable, the 80303 does not snoop host writes, and a
stale pointer would run stock `SET_MEM_MBOX`. MEMCOPY is a SCSI/device transfer;
StoreImage/ReadImage do not expose persistent local scratch. The next accepted
gate is a stock cache-maintenance command or a fully decoded unused software
interrupt with exact return/restoration semantics. See
`artifacts/current/accele160-ram-route-20261016/README.md`.

## AcceleRAID startup analysis — 2026-10-16

Stock boot/trailer/loader checksums and runtime CRC pass. Reset entry
`0xfeffc000`; 24 KiB loader copied to `0xc000a000`, entry `0xc000c590`;
main image expands at `0xc0010000`, entry `0xc004cf70`. Firmware state extends
past 4 MiB: do not infer free RAM from the expanded image's end. New BAR0 is
an 8 KiB Messaging Unit plus 4 KiB translated local aperture, not a broad RAM
BAR. A bounded returning probe is assembled and nine offline tests pass;
**no custom code has executed on the new card**. Transport is now proven, while
owned scratch memory and a cache-safe callable entry remain unproven. No reset,
flash write or driver change was used; old PG remains untouched/unbound.
[Memory map, entry-route priorities and exact test contract](docs/hardware/accele160-startup.md).

## AcceleRAID complete stock dump — 2026-10-16

Accepted two identical **1 MiB full-flash reads** via READIMAGE selector 9:
zero residual, unchanged 64 KiB prefix/1 MiB suffix DMA guards. Boot, main
firmware, BIOS, diagnostics and descriptor match independent region captures;
embedded firmware and EZAssist decompression CRCs pass.

Selector 4 is unsafe with the descriptor's compressed length: it decompresses
551,078 bytes directly into host memory, ignoring the requested 164,576-byte
extent. The guarded experiment contained this overrun; selector 4 is now disabled.
Use selector 9 and extract EZAssist offline. No flash writes were issued.

Old DAC960PG `0000:37:04.1` stayed unbound and untouched. New AcceleRAID
`0000:37:09.1` is bound to `myrsread`, firmware 6.00-05; firmware reports
100 MHz, 16 MiB RAM, 8 MiB cache and 1 MiB flash. SSH is healthy. The failed
EZAssist allocation and its pinned companion remain deliberately retained until
reboot; do not force unload/unbind them. Successful raw readers were released.
Temporary myrs blacklist was removed and initramfs updated; existing myrb rules
were preserved. No RTEMS/Doom session is active. New-card code execution and
firmware compatibility are not yet established; explicit BDF selection remains
mandatory. Half-height work stays on hold.

[Evidence, reproduction and next steps](artifacts/current/accele160-guarded-20261016/README.md).

## User direction: half-height on hold — 2026-10-16

Pause further half-height optimization and testing until requested. Keep the
existing option off by default and retain its evidence. The user is replacing
the card with a similar board described as having a 100 MHz i960. Identify the
replacement hardware and firmware before reusing board-specific assumptions;
compatibility and performance have not yet been tested.



## Current half-height result (2026-10-16)

`--runtime-half-height` enables F7/browser control, independent of F6 flat planes,
full height initially. Keep off by default: same-session 920-frame card comparison
normal/half/flat/both = 6.3616/6.4042/7.7235/7.1115 FPS. Half alone +0.67% is not
an established practical gain; half + flat is 7.92% slower than flat alone.
Full audits, DMA ownership, held-slot STOP and stalled-host checks remain intact.
Record both wins and regressions; next investigate half-column/expansion costs.
[Exact results and reproduction](artifacts/current/half-height-20261016/README.md). The bounded ping-pong benchmark blocks
external keys; normal pipeline builds expose F7. Do not advertise the measured
bounded FPS as an interactive guarantee.


<!-- flat-planes-current -->
**2026-10-16 optional flat planes accepted:** playable `--runtime-flat` starts
textured and adds F6/browser toggling. Same-build low-detail ABBA: **6.454 →
7.877 FPS (+22.05%)**, renderer 135.51 → 107.31 ms, planes 40.96 → 13.46 ms.
520 frames / 56 full paired audits, STOP/stall/drain, remote/local replay and
mutation checks pass; native oracle retains exactly the four known differences.
Keep quality optional. The measured ping-pong session is bounded, not a newly
qualified interactive transport; normal pipeline builds expose the live button.
See `artifacts/current/flat-planes-20261016/README.md` and `game/doom/flat_planes/README.md`.
<!-- /flat-planes-current -->

Read `CURRENT-FINDINGS.md` first. It supersedes historical status blocks below.
The stock new-card `c0023000` dispatch page was captured live after boot:
`artifacts/current/accele160-table-snapshot-20261016/` matches all 4096 bytes
of the accepted expanded runtime. Its `0x8f` entry is stock unsupported.
PIATVR was restored; both cards remain unbound. This does **not** prove a
modified loader's write persists after main entry. Use the guarded snapshot
script only for read-only table inspection; never infer cache coherence for
host-written code or pointers.
The preferred **offline** AcceleRAID candidate is now
`artifacts/current/accele160-late-ping-20261016/`: the dispatch write occurs
at the copied loader's common return, after its descriptor pass. The exact
in-memory image has 155 changed bytes and passes known checksums. No modified
image has run; computed main-entry writes, live table persistence and recovery
remain unproved. `dcctl 1` at boot handoff enables D-cache, not invalidates it.
Do not flash this candidate on the strength of the structural receipt.
The earlier AcceleRAID candidate is
`artifacts/current/accele160-ping-handler-20261016/`: an earlier bounded 148-byte i960
PING handler with a structurally audited **in-memory only** image. The traced
mailbox-to-object copy preserves all 64 bytes, and the completion route predicts
status 0/residual 0, but no patched image has booted or run. Its nonce is an
admission marker, not an authenticated response. Do not flash it on the basis
of the receipt; first prove hook timing/table persistence and rollback/recovery.
For AcceleRAID 160, the stock `0x8f` zero-DMA command completed with status 2
and zero residual on the new card only; this is an unsupported result, not code
execution. The native PING validator and exact live capture are in
`host/accele160/helper/` and
`artifacts/current/accele160-ping-contract-20261016/`. Both cards are currently
unbound. Keep BDF `0000:37:09.1` explicit, leave old `0000:37:04.1` untouched,
and do not treat a same-boot driver reload as reliable. No new-card firmware
patch has been programmed or recovery tested.
The earlier `artifacts/current/accele160-dispatch-rehearsal-20261016/`
assembles an offline loader hook and validates an in-memory image with known
checksums. Its `0x8f` target branches to stock unsupported for **every**
request; it is a route rehearsal, not a working PING or flash candidate. Do
not program it or infer boot from its structural receipt. The later bounded
PING candidate resolves the static command-byte and completion trace, while
live behavior and recovery remain open.
`artifacts/README.md` defines retention: keep recovery/build inputs, test fixtures
and concise current results; avoid repeated full build archives and obsolete
binaries. Full audits and ownership checks remain mandatory during hardware tests.
Historical payloads removed from the checkout are recoverable at Git `a8af272`;
restore into a separate directory before replaying them. Do not treat a missing
historical capture as evidence that its experiment failed or repeat flash work.

# Repository guidance for Claude Code

<!-- renderer-current -->
**2026-10-15 fast renderer accepted in bounded low-detail card tests:** opt-in
`game/doom/play/build.py --fast-render` selects exact two-sample spans and `-O2`
only for r_bsp/r_plane/r_draw. The R_PointOnSide -O0 object is byte-identical;
no new renderer state/allocation. Release priority, full audits and all DMA
ownership checks remain. Keep baseline available by omitting the flag.

Four 520-frame A/B/B/A runs: matched **4.831 → 5.334 FPS (+10.40%)**,
renderer **187.64 → 168.18 ms**, planes **57.91 → 40.03 ms**, BSP/walls
**108.31 → 106.50 ms**. Most gain is in planes; this grouped experiment cannot
isolate span code from compiler flags or traversal from wall drawing.
Completion-to-HTTP availability remains low (**5.00 → 4.51 ms**); this is not
input-to-browser-paint latency. Retain validated per-stage latency improvements
even when overall FPS is unchanged.

**2,080 frames / 243 full paired audits** pass, with exact corresponding images,
2,032 exact HTTP payloads, all stall/held-STOP/heap-drain checks and maximum IRQ
gap 10.839 ms. Same four known native pixels differ. Image grows 272 bytes,
protected pages remain 146; mutable bounds unchanged. The flag remains opt-in
for broader scene/high-detail qualification. Next: profile exact arithmetic and
geometry inside the remaining 106.5 ms BSP/wall stage; preserve the point-side
workaround until independent target proof.
Evidence and reproduction: `artifacts/notes/render-20261015.md` and
`game/doom/render/README.md`. Prior release-priority-only FPS limits below are
historical; this combined candidate exceeds 5.19 FPS in the tested workload.
<!-- /renderer-current -->

<!-- release-priority-current -->
**2026-10-15 release priority accepted:** release telemetry now separates shared
host-gate wait from ioctl execution (the latter still includes kernel scheduling).
Pending releases overtake ordinary waiters after the current holder finishes;
priority audits yield the gate between words while still reading every frozen
word and retaining all full paired audits. A validated immutable host frame is
published before its synchronous exact-generation release; ownership is unchanged.
Priority is now the default within opt-in Doom ping-pong; `--release-schedule
baseline` retains the comparison path. Other transports retain their defaults.

Two 520-frame, identical-binary ABBA/BAAB runs reduce mean release gate wait
**13.402 → 2.659 ms** and completion-observation-to-HTTP availability
**25.178 → 4.771 ms**. Sustained matched FPS is **4.837 → 4.835**, effectively
unchanged. HTTP availability is not browser paint latency. A third 520-frame run
with opt-in `--fast-memory` (private Newlib memcpy/memset word paths) reaches
**4.855 FPS**, only +0.40%; this does not establish a meaningful speedup.
Renderer wall time remains about 187 ms. Sustained 5.19 FPS is not achieved;
profile BSP/planes and exact arithmetic next, rather than assume more copy gains.

Across all three runs: **1,560 frames, 186 full paired audits**, stalled-host,
held-slot STOP and heap/IRQ drain pass. All 520 images agree across builds;
the same four known native pixel differences remain. 1,524 received HTTP payloads
match captured images. Maximum IRQ gap is 10.828 ms. Source, binaries, full replay,
mutation checks, timings and restoration evidence:
`artifacts/notes/release-priority-20261015.md`.
<!-- /release-priority-current -->

<!-- bulk-capture-current -->
**2026-10-15 bulk guarded framebuffer capture accepted:** steady ping-pong now
uses one 73,728-byte capture read instead of 72 small reads. Exact epoch/generation,
completion ordering, both guards, full raw journals and separate release remain.
Release credit is granted only after successful full copyout; partial-copy faults
also no longer grant credit in the legacy chunk path. The extended operation-8
buffer is 73,760 bytes despite the legacy ioctl number's size encoding; use the
matching new client/module. Card kernel and Doom engine are unchanged.

100 frames / 51 full paired audits, held-slot stall and STOP, heap drain, native
oracle and 45 evidence mutation checks pass. 95 HTTP payloads match captures.
Capture ioctl time fell **43.178 → 0.278 ms/frame**, completion-to-release
**61.398 → 26.405 ms**. Overall FPS was **5.192 → 4.802 (-7.52%)** in this
comparison; do not claim an FPS gain. Release ioctl waits rose 4.264 → 22.330 ms;
renderer time remains about 190 ms and audit/scheduling phases differ. Repeat
interleaved measurements before attributing the FPS difference to the new path.
Maximum IRQ gap: **10.488 ms**. First 52 card frames/palettes match the accepted
baseline; the same four known native pixel differences remain.

Initial 16 host-started comparison frames retain their old capture path. Bulk
capture is used by the existing opt-in ping-pong profile, not a new card protocol.
Evidence, exact binaries, ABI and replay: `artifacts/notes/bulk-capture-20261015.md`.
Public IPv6 HTTP restored: 200 / 2890 bytes; boot
`27cc6b32-2d2f-4701-ba88-1c6d34484a42`, relay 1555 / supervisor 1552 owns
`dac960auto`. Doom 8087 closed. Historical PIDs below are stale; inspect actual
ownership before use.
<!-- /bulk-capture-current -->


<!-- irq-drain-current -->
**2026-10-15 IRQ gap diagnosed and peer-yield shutdown fixed:** the original
59.855 ms spike occurred after STOP, not during rendering. The inherited outer
priority-31 region covered the remaining shared-buffer byte scan. A targeted
80 KiB shared-pin workload reproduced **55.997 ms drain with zero ticks** and
**60.237 ms maximum IRQ gap**. The fixed run retained all checks, took **60.753 ms
elapsed drain with six timer ticks**, and held maximum IRQ gap to **10.495 ms**.
The fix enables timer IRQs only after both workers cross the existing STOP
arrival barrier, then masks before done/suspend. Pins, allocator/reference locks,
controller ownership checks, IRQ-continuation drain and terminal quiescence remain.

Normal fixed Doom: **5.192 FPS**, **10.731 ms maximum IRQ gap**; instrumented
normal baseline 4.777 FPS / 10.785 ms. The shutdown-only change is not a claimed
FPS optimization; prior peer-yield achieved 5.273 FPS. Both normal repeats ended
with small buffers, so the separate stress pair establishes the long-scan fix.
Four bounded runs total **400 frames / 249 full paired audits**, with held-slot
STOP, global heap drain, Linux/Mac replay and capture-mutation checks. First 52
frames per run retain exact baseline pixels/palettes and only four known native
pixel differences. The stress workload changes input/restart timing; do not use
its fixed frame-66–68 interval as a normal loading/FPS comparison.

Frozen diagnostic page 3 (DRN1 schema 2; archived masked schema 1) is matched to
the raw control journal. New builds require it. Replay gates the fixed build at
**<20 ms full-session IRQ gap**, and checks drain tick progress against elapsed
time even when no subsequent IRQ could expose a final masked interval. This is
bounded acceptance, not a universal hard-real-time guarantee. 146 protected
pages remain; 16 mutable bytes remain in the existing layout. Current fix is in
the opt-in `--peer-yield` build; older images retain their original behavior.
Keep opt-in pending longer interactive qualification. This supersedes the open
59.9 ms-gap warning below. See `artifacts/notes/irq-drain-20261015.md` for exact
sources, binaries, reproduction and restoration status. Historical ownership IDs
below are superseded; inspect actual hardware ownership before use.
Public IPv6 HTTP restored and verified 200 / 2,891 bytes; boot
`a32b6a8c-aedd-4f62-8537-0509ef285a26`, relay 1434 (supervisor 1416)
owns `dac960auto`. Bounded Doom port 8087 is closed.
<!-- /irq-drain-current -->

<!-- peer-yield-current -->
**2026-10-15 optional worker service yielding tested:** reviewed parallel chat
“Find i960MC board design guidance” and implemented `--peer-yield`. Worker 0
completes every network/control/shared-heap pass, then yields only while owned
application code runs. Both workers retain priority 2, controller priority 1,
10 ms ticks and original STOP/drain; ownership checks and full audits remain.
Matched Doom delivery improves **4.517 → 5.273 FPS (+16.73%)**; first-frame
execution **116.923 → 100.105 s**, upload **79.615 → 80.086 s**, warm restart
**2.780 → 2.830 s** (no restart improvement). 100 frames, 58 full paired audits,
held-buffer STOP, global heap drain, exact baseline pixels/palettes, Linux/Mac
replay and 35 capture mutation rejections pass. Four known native pixel
differences remain. Schema 4 adds peer telemetry; maximum completed-service gap
was 200 ms, sampled pass count 45,569, bounded by final worker progress 45,751.
**Keep opt-in:** final maximum IRQ gap was **59.855 ms**, versus baseline
10.546 ms and first candidate 10.623 ms. Aggregate capture cannot locate its
cause. Functional audit success does not qualify worst-case interrupt latency.
Next instrument long IRQ gaps with task/PC/phase attribution before default
promotion. Timer CPU attribution is phase-biased by yielding; use measured
wall/FPS, not a claimed CPU-share gain. First all-session-yield candidate remains
archived: 5.321 FPS but upload regressed to 106.514 s, so preparation now retains
original scheduling. See `artifacts/notes/peer-yield-20261015.md` and
`rtems/exclusive/PEER-YIELD.md`. Historical ownership IDs below are superseded;
check actual remote ownership before hardware work.
Public IPv6 HTTP restored and independently verified: 200 / 2,891 bytes; boot
`74c0c2d0-c166-4185-9c75-8754a93ce11d`, relay 1658 (supervisor 1656)
owns `dac960auto`. Bounded Doom port 8087 is closed.
<!-- /peer-yield-current -->

<!-- screen-copy-current -->
**2026-10-15 remaining screen copy optimized and card-accepted:** fixed 320×200
indexed scale-one presentation uses one exact unrolled aligned word copy rather
than 200 bytewise Newlib row copies. **3.815 → 4.517 FPS (+18.39%)** in the matched
frames 21–50 window; screen copy **44 → 12 ms wall / 22 → 6 ms sampled task CPU**.
Renderer remains ~209 ms wall / ~105 ms sampled CPU. Persistent `I_VideoBuffer`
is retained: cached row pointers, incremental updates and zone ownership cannot
safely alias rotating/pinned DMA slots. Other geometry and unaligned-pointer
fallbacks remain. No libc-wide, DMA, scheduler, ownership or guard changes.
100 frames, **67 full paired audits** at unchanged cadence, held-buffer STOP,
heap drain, exact baseline pixels/palettes and full Linux/Mac replay pass;
33 mutated captures rejected. Four known native pixel differences remain.
Private platform builds use this automatically; WAD ring/ping-pong stay opt-in.
Evidence: `artifacts/notes/screen-copy-20261015.md`. One matched run, not a
long soak; 10 ms telemetry is elapsed/sample-based, not cycle-accurate. Larger
remaining FPS headroom is renderer work/scheduling, not the remaining 12 ms copy.
Historical owner IDs below are superseded; inspect actual ownership before use.
Public IPv6 HTTP restored and verified 200 / 2,891 bytes; boot
`a9a9032f-68fa-4a83-8a6b-27032556f98b`, relay 2619 (supervisor 2617)
owns `dac960auto`. Bounded Doom server 8087 is closed.
<!-- /screen-copy-current -->

<!-- wad-copy-current -->
**2026-10-15 actual WAD-cache word copies accepted:** first-frame loading
**192.075 → 117.566 s (38.79% shorter)**; same-level warm restart
**4.506 → 2.890 s (35.86% shorter)**. All three cache copies total
**93.640 → 17.980 s**. Upload remains separate (~80 s); gameplay stays
**3.803 → 3.815 FPS**, not a demonstrated rendering gain. Equal alignment uses
exact byte prefix/tail plus aligned 32-bit copies; unequal alignment stays
bytewise. No DMA/cache-policy/guard/ownership changes. 100 frames, **68 full paired
audits** at unchanged 3 s cadence, held-buffer STOP and heap drain pass. First 52
frames match baseline and retain only four known native pixel differences.
ASan/UBSan edges, deterministic native runs, full Linux/Mac replay and 33 mutation
rejections pass. See `artifacts/notes/wad-copy-20261015.md` for exact binaries,
sources, timings, reproducibility and service restoration. WAD ring/ping-pong
remain opt-in; next optimize retained staging/direct owned-cache DMA/read-ahead,
not remove audits. Historical profiling baseline and its owner IDs below are
superseded by this acceptance; inspect actual owner before hardware work.
Public IPv6 HTTP restored and verified 200 / 2,891 bytes after normal reboot;
boot `9bef2976-8b43-4c8d-bd4e-1e0b719249b7`, relay 2653 (supervisor 2651)
owns `dac960auto`. Bounded Doom server 8087 is closed.
<!-- /wad-copy-current -->

<!-- wad-profile-current -->
**2026-10-15 bounded WAD/DMA profiling accepted:** opt-in `--wad-profile` builds
retain every ownership/guard check and all full paired audits. A pinned-source
64 × 32 KiB host-to-card benchmark observes **20.605 MB/s** from DMA start to
completion and **6.793 MB/s** through the ordinary guarded transfer routine;
extra full-payload comparisons are timed separately. These are short elapsed
measurements including interrupts, not maximum PCI/RAID throughput or CPU cycles.
Across startup, 100 frames and warm restart, actual WAD-cache filling costs
**77.960 s**, cache/bounce → Doom copies **15.680 s**, target guard scans
**35.802 s**, staging copies **13.597 s**, initialization **8.767 s**,
allocation alone **3.138 s**, freeing alone **2.581 s**. Ordinary DMA completion
intervals total **2.843 s**. Categories have explicit nesting; do not add them
blindly. Cache timings use the existing 10 ms clock; kernel timings use read-only
timer 0 at nominal 4,166,700 Hz. Full-audit gate waits and host Python/ioctl time
are separately recorded and overlap card execution.
Final run: first frame **192.075 s** after preparation (80.113 s upload separate),
warm restart **4.506 s**, fixed-scene sample **3.803 FPS**. No speedup is claimed
for this instrumented build. Two completed runs pass **200 frames / 178 full
audit pairs**, held-buffer STOP, heap drain and local replay; final evidence
rejects 24 frame, three WAD and six timing mutations. First 52 controlled frames
retain exactly the four known native differences and exact palettes.
The initial completed candidate exposed the wrong, unused stdio cache; its zero
cache telemetry is explicitly invalid and preserved. The final build profiles
the actual backend, requires matching engine flags and cross-checks all cache
calls/bytes against runtime counters and WAD requests. Both actual native
52-frame runs prove nonzero backend telemetry before final hardware acceptance.
Next: optimize **actual WAD-cache byte copies**, then retained staging/direct
owned-cache DMA and adaptive read-ahead. Do not reduce guards or full audits.
146 protected pages; final mutable reserve **64 bytes**; no flash/map change.
Evidence/manual: `artifacts/notes/wad-profile-20261015.md`. Exact sources,
binaries, captures, failed instrumentation evidence and replay tools are saved.
All captures were copied/hash-checked/replayed locally before normal reboot.
Public IPv6 HTTP is restored and verified 200 / 2,891 bytes. Current boot
`94855ff1-240c-45ce-a28f-bfd47d4195f1`, supervisor **3570**, relay **3572** owns
`dac960auto`. Doom test server is closed. Inspect current ownership before new
card work; stop the relay normally and never force-unload retained mappings.
<!-- /wad-profile-current -->


<!-- wad-ring-current -->
**2026-10-15 WAD ring bounded acceptance passed:** two guarded 32 KiB host slots,
shared request/response/completion records and 64 KiB read-ahead are opt-in via
`--wad-ring --pingpong --pipeline-test --wad-dma`. Same-build first frame:
**290.087 → 186.566 s (35.69% less, 1.555×)**, excluding ~80 s engine upload.
Warm restart **2.842 → 4.242 s (49.25% slower)**: do not promote the default.
Read-ahead raises total test payload from 20.89 to 59.15 MB. Baseline metadata
queries cost 180.606 s; new RAM-only ioctls plus pending polls cost 3.873 s,
excluding Python/card execution. The first byte-oriented ring passed safety but
regressed startup to 456.109 s; it is archived, not hidden.
All three runs pass: **300 frames, 358 full audit pairs**, exact source/completion
replay, four full frame comparisons per run, frame stall/resume, owned STOP and
heap drain. First 52 controlled frames are identical across card runs and retain
exactly four known native pixel differences; palettes match. Steady FPS is about
3.8–3.9; no sustained renderer speedup is claimed. Guards are fully scanned at
unchanged points using word operations; descriptor/ownership/quiescence checks
and all full audits remain. 146 protected pages, 288-byte mutable reserve;
no flash or memory-map change. Native tests cover publication reread, descriptor
bits, all guard bytes, host timeout and STOP while waiting. Physical mid-WAD
STOP/stall/timeout injection and longer interactive play remain unqualified.
Exact sources/binaries/captures and Linux/Mac replay are preserved in
`artifacts/wad-ring-20261015/`; protocol: `rtems/dma/wad_ring/README.md`.
Next optimize adaptive smaller read-ahead for warm/small reads; arbitrary
unaligned ring reads are not supported by the private cache-fill API.
All test ownership is released after local archive verification and normal
reboot. Public IPv6 HTTP is restored and verified 200 / 2,891 bytes from the Mac.
Boot `cf670f3e-d97f-4bf3-8649-04e1fc937e49`, supervisor **2721** / relay **2723**
owns `dac960auto`; see `restoration.json`. Inspect actual owner before further
card work; stop the relay normally and never force-unload retained mappings.
<!-- /wad-ring-current -->


<!-- doom-pingpong-current -->
**2026-10-15 Doom ping-pong DMA bounded acceptance passed:** task-owned DMA1
handoff drains outstanding framebuffer DMA before publishing a WAD request.
Controlled low-detail Doom **3.503 → 3.887 FPS (+10.96%)**; host transfer/capture
**212.5 → 41.3 ms**, previous-publication wait **81 → 0 ms**. Renderer ~207.6 ms
plus retained screen copy ~44.1 ms now dominate. Estimated card start→host
observation **17–44 ms**, start→validated capture/release **64–92 ms**; these are
not pure DMA or input-to-display latency. Third host buffer estimated ~0–2%
steady benefit in this scene, possible jitter smoothing and +one frame of latency;
not implemented or benchmarked. Keep two buffers.
Controlled 100-frame run: **108 full audit pairs**, four exact DMA/mailbox pairs,
all 100 HTTP payloads exact, both-slot 3-second stall/resume, automatic level
restart with 55 additional WAD DMA reads, held frames 99/100 across STOP, global
drain. First 52 frames retain exactly four known native pixel differences and
matching palettes. Linux/Mac replay and 24 evidence mutations pass. Earlier
52-frame run has 104 audit pairs and browser input; its FPS is not a controlled
comparison. Both have zero active-frame full-snapshot counter: no new physical
overlap claim beyond the earlier v10 synthetic acceptance/native tests.
Kernel helper moved into existing protected engine code; 145 protected pages,
304-byte mutable reserve; no guard/RAM boundary or flash change. Doom is now
admitted only through explicit `--pingpong`; runner currently requires bounded
`--pipeline --pipeline-test --wad-dma`, optional `--wad-load-test` for 100 frames.
Keyboard input is disabled for bounded measurement; ordinary play defaults stay
unchanged. See `artifacts/doom-pingpong-20261015/README.md`, exact archives and
`game/doom/play/PLAY.md`. Tests ended, exact archives saved and replayed locally;
normal reboot released retained mappings. Public IPv6 HTTP is restored and
verified 200 from the Mac. Boot `a7e3490e-127d-4a0c-9f62-bb9466b03d05`, supervisor
4012 / relay 4014 owns `dac960auto`; see `restoration.json`. Inspect actual owner
before new hardware work; stop this relay normally. Never force-unload.
Older service/PID and Doom-excluded notes below are historical.
<!-- /doom-pingpong-current -->


<!-- dma-pingpong-current -->
**2026-10-15 card-initiated ping-pong DMA accepted (v10):** two persistent host
buffers, task-owned payload/completion chains, explicit generation release.
Synthetic producer **7.921 → 14.242 FPS (+79.80%)**, with 256 delivered + 2 held
frames, **20 full audit pairs**, five full mailbox comparisons, two 3-second host
stalls, resumed delivery, owned STOP and global drain. Linux/Mac full replay and
24 evidence mutations pass. Five full system snapshots validated active owned
DMA leases. Card start→host observation estimated mean **8–30 ms**; full validated
capture/release **62–83 ms**. These are not Doom/browser FPS or pure DMA latency.
The final host queries unrelated Upload completion once/second, immediately on
STOP. Ownership checks, full captures, guards and audits remain. Native tests
cover active-transfer STOP, hardware timeout quarantine and the stalled wait bound.
The protected table covers 145 pages; offline capacity check and per-page mutation
tests pass; kernel tail 304 bytes. The faster v9 attempt exposed a snapshot path
that did not recognize owned DMA. V10 validates the exact lease before changing
only its local report; foreign DMA and descriptor corruption remain errors.
All earlier failures are preserved, including v9 whose frame/STOP pass is not full
system acceptance. See `artifacts/notes/dma-pingpong-20261015.md` and
`rtems/dma/pingpong/README.md`. Doom remains excluded from admission: WAD and
frame traffic share DMA1 and need explicit coordination, followed by browser,
input/disconnect and pixel/palette acceptance. No flash change or RAM remap.
Final archives are local and replayed; normal reboot released the test module.
Public IPv6 HTTP is restored and verified 200 from the Mac. Current boot
`2225b1d9-c77e-4cb6-900e-9841154cd719`, supervisor 2569 / relay 2571 owns
`dac960auto`. See `restoration.json`; inspect actual owner before card work and
stop this relay normally. Never force-unload retained mappings.
Older ownership/service notes below are historical.
<!-- /dma-pingpong-current -->


<!-- doom-columns-current -->
**Column kernels accepted in bounded low-detail testing, 2026-10-15:** baseline
**3.478 FPS**, specialized C **3.857 (+10.89%)**, i960 assembly **3.821 (+9.86%)**.
Both reduce renderer wall **211.4 → 180 ms**, sampled CPU **105.9 → 90 ms**.
Assembly has no demonstrated extra advantage; prefer C for a future fixed play
build. `--pipeline --column-test` is a bounded baseline/C/assembly/baseline
experiment requiring `--pipeline-test`; it must not run interactively. Defaults
remain unchanged. 96 target oracle cases (real assembly), 52 guarded frames,
14 full audit pairs, exact first four DMA/mailbox pairs, STOP/drain, Linux/Mac
system/frame/WAD replay and 35 tamper cases pass. All optimized images match
prior card frames exactly; the four existing native/card pixels remain unresolved.
All 52 HTTP payloads match. No new timer policy, firmware or arena expansion.
Evidence: `artifacts/notes/doom-columns-20261015.md`; code/manual:
`game/doom/columns/README.md`. Admission 872,376 bytes; kernel tail still 400.
The exclusive test has ended; archives are saved locally and replayed. Normal
reboot released the test module. Public IPv6 HTTP is restored and verified 200
from the Mac; boot `03e2a874-bffb-4c2e-b4f6-ec6d90e7a3db`, supervisor 1427 /
relay 1432 owns `dac960auto`. See `restoration.json`. Inspect actual owner before
card work; never force-unload retained mappings. Older service/PID notes below
are historical and superseded by this entry.
<!-- /doom-columns-current -->

<!-- doom-detail-current -->
**Low detail accepted, 2026-10-14:** high **2.481 → low 3.178 FPS (+28.09%)**;
low blocks vary 2.908–3.503, including the 884 ms frame-40 interval. All 52
frames, 14 full audit pairs, ownership/ACK, STOP/drain and 35 tamper cases pass.
Renderer wall **315.5 → 210.0 ms**, timer-sampled Doom CPU **158.2 → 105.0 ms**:
approximately half CPU share. This is 10 ms sampled attribution, not cycle-exact
or higher-resolution timing. Prior high-detail card images match exactly; low
has four unresolved native pixel differences in the existing small region.
Build `--pipeline --detail-test` for bounded high/low/low/high; fixed optional
`--low-detail --no-fnv --direct-frame` for a separate interactive candidate.
Do not claim 10 FPS or long interactive acceptance. Evidence and exact binaries:
`artifacts/notes/doom-detail-20261014.md`. Test closed and local replay passed;
Public IPv6 HTTP restored (200), boot `1917f487-902d-4579-bbea-5b5b859db300`;
relay supervisor 1497 / Python 1521 owns `dac960auto`. Stop it normally before
new card work. Consult `restoration.json` there for service state.
Never force-unload retained resources or overlap hardware owners.
<!-- /doom-detail-current -->

<!-- doom-present-current -->
**2026-10-14 presentation accepted:** optional FNV and direct delivery-slot
presentation measured **1.965 → 2.474 FPS (+25.94%)** with full audits. All 52
frames, 14 audit pairs, exact ACK/ownership, STOP/drain and 35 tamper cases pass.
Pixels/palette match the prior card run; known seven native pixel differences
remain. Renderer ~317 ms, retained screen copy ~47 ms, DMA hardware quantized
mean ~3 ms. Profile query/host FNV validation affects measured FPS; do not claim
an uninstrumented or 10 FPS result. Default remains conservative; features opt-in.
The first selector attempt failed and is archived separately; table selection
passes. See `artifacts/notes/doom-present-20261014.md` and
`game/doom/play/PRESENTATION.md`. Test owner closed and evidence verified before normal reboot. SSH has not
returned; user power-cycle requested. Public HTTP restoration pending; see
`artifacts/doom-present-20261014/restoration.json` and `restore.sh`. Never
force-unload retained exclusive mappings.
<!-- /doom-present-current -->

<!-- wad-dma-current -->
**2026-10-14 bulk WAD DMA accepted:** `--pipeline --no-crc --wad-dma` uses
4096-byte host-to-card DMA without WAD/frame payload CRC, retaining ownership,
guards, hardware completion and all full audits. First level: **1642.751 →
318.183 s (5.163×)**; warm same-level restart: **10.291 → 3.068 s (3.354×)**.
52 frames match mailbox exactly; 14 full audit pairs, owned STOP and heap drain
pass. Full system/frame/WAD replay passes on Linux and Mac. Known native pixel
differences remain. Legacy CRC mailbox stays default; image admission is unchanged.
Evidence: `artifacts/notes/wad-dma-20261014.md`; manual: `game/doom/play/PLAY.md`.
The failed pre-WAD startup TCP attempt is preserved. Host now finishes network
proof before large game upload, retaining checks/deadlines/audits. Metadata queries
still cost 181.255 s. No arbitrary in-bounds corruption detection without CRC.
Remote workspace `/home/mit/i960-wad-dma-20261014`; interactive `play` on port 8087, supervisor 1469,
boot `5e6b2f6d-b685-486e-97cc-ca33dcc4e6b4`, live and browser keyboard verified. Do not force-unload retained resources or start another owner.
<!-- /wad-dma-current -->


<!-- doom-pipeline-current -->
**Two-buffer Doom/binary pipeline accepted (2026-10-14):** CRC-on **1.396095 FPS**,
CRC-off **2.070201 FPS (+48.285%)** in 52-frame on/off/off/on testing. All **29
full monitor/RAM pairs**, four exact mailbox/DMA pairs, owned STOP and global
heap drain pass. Linux/macOS replay rejects 35 frame/journal and 24 snapshot
mutations. All 52 binary HTTP packets match; native comparisons retain seven
pixel differences per frame with identical palettes/padding. This is delivery
FPS, not paint FPS or a 3–5× gain. Earlier single-buffer results used different
inputs, so do not attribute their difference solely to buffering or binary HTTP.
Build/run opt-in `--pipeline`; CRC remains on unless `--no-crc` is explicit.
Never remove ownership, generation, bounds, guards or hardware quiescence checks.
The initial run exposed WAD starvation during pending DMA; the host now services
WAD requests during polling. A separate TCP startup failure exposed executor
shutdown suspending audits; failures now request owned STOP while keeping the
control loop active. Both incomplete attempts are preserved, not accepted.
Evidence: `artifacts/notes/doom-pipeline-20261014.md`. Longer interactive and
disconnect acceptance remains future work. No firmware or RAM remap change.
All test ownership is released after archive verification/replay and reboot.
Public IPv6 HTTP returned 200. Current owner: relay supervisor **2796**, Python
**2798**, boot `d18b781d-a8e7-4604-b8fc-4a048e18506e`, bound `dac960auto`.
Stop that relay normally before new tests; never force-unload retained resources.
Ownership records below are historical, not current reservations.
<!-- /doom-pipeline-current -->


<!-- doom-dma-fixed-current -->
**Fixed Doom DMA comparison accepted (2026-10-14):** unchanged engine and full
A/B/B/A protocol pass **28 frames, four exact paired reads, sixteen guarded DMA
captures, 29 full monitor/RAM pairs, owned STOP and global drain**. Mailbox
**0.972816 FPS → DMA 1.376781 FPS (+41.525%)**; mean transfer **503.489 →
228.797 ms (2.2006× faster)**. Every buffer matches the earlier physical run;
known native/card pixel differences remain unchanged. Linux/macOS full replay
passes and rejects 30 frame/journal plus 24 snapshot corruptions. All 28 HTTP
PNGs match; these are delivery measurements, not browser paint rates.
No new runtime change, firmware reflash or relaxed check was needed. Keep DMA
opt-in; next is longer interactive input/STOP/disconnect and mapping lifecycle
acceptance. Evidence: `artifacts/notes/doom-dma-fixed-20261014.md`.
Closed archives were hash-verified and replayed locally before reboot. Test
ownership is released. Public IPv6 HTTP returned 200 from the Mac. Current owner:
public relay supervisor **2120**, Python **2122**, boot
`36938147-8109-4114-b7c8-9dc9dcdaf09d`, bound `dac960auto`. Stop that relay normally
before new hardware work; never force-unload retained exclusive resources.
The older ownership records below are historical, not current reservations.
<!-- /doom-dma-fixed-current -->

<!-- frame-dma-stress-current -->
**Frame DMA stress acceptance (2026-10-14):** the tiny admitted producer
reproduced the timeout at frame 41. A scheduled peer heap check required all
DMA idle and rejected the intentionally owned DMA1 transaction. Frozen evidence
shows software abort, heap error 1, completed bytes and cleanup not yet run.
The ownership-aware isolation check passed **512 frames, 89 active-transaction
checks, 20 exact mailbox/DMA pairs, 30 full monitor/RAM pairs, owned STOP and
global drain**. Full local replay passes; 34 capture and 24 snapshot corruptions
are rejected. Counter-query integration failures are separately archived and
are not accepted runs. No timeout bounds, interrupts or full audits were relaxed.
Synthetic delivery is 2.9759 FPS, mean DMA capture 225.58 ms; this is not Doom FPS.
Keep DMA opt-in. The pinned Doom repeat is now accepted above; longer
interactive acceptance remains next. No firmware reflash was needed.
Evidence: `artifacts/notes/frame-dma-stress-20261014.md`; harness:
`rtems/dma/stress/README.md`. Closed archives were hash-verified and replayed
locally before reboot. Public IPv6 HTTP is restored and returned 200 from the
Mac. Stress ownership is released. Historical owner at stress closure: supervisor 2430,
Python 2432, boot `5ae888c7-143b-400b-80ea-5e2a24392de6`, bound `dac960auto`.
Stop that relay normally before new hardware work; never force-unload a retained
exclusive test module.
<!-- /frame-dma-stress-current -->

<!-- doom-dma-current -->
**Historical first Doom DMA comparison (2026-10-14), before the fix above:** four pinned
frames matched mailbox/DMA exactly; same-frame transfer improved **0.498802 →
0.225233 s (2.2146×)**. Five DMA frames and eleven delivered frames passed, then
frame-12 completion polling timed out. Retained destination bytes match the old
physical frame and guards remain intact, but bus mastering remained enabled.
Do not confuse delivered bytes with quiescence. **No DMA FPS improvement or
final heap drain is accepted.** All 23 recorded full monitor/RAM pairs precede
the first frame; no post-DMA audit was obtained. The full verifier rejects the
run; explicit failed-prefix replay passes and rejects 30 frame/journal and 24
snapshot mutations. Two review-found release races were closed with an atomic
pending check/pointer clear; both earlier startups were stopped before DMA and
archived. Default play remains unchanged; `--dma` / `--dma-test` is experimental.
Next instrument completion/cleanup and terminal fault diagnostics, reproduce the
stall, then repeat full A/B/B/A and STOP/drain. Do not enlarge timeouts, remove
checks or recycle retained resources. The failed capture and exact build are
locally hash-verified. Reboot completed; public IPv6 HTTP returned 200 from the
Mac. Relay Python 1675 (supervisor 1604), boot
`91493f0a-3c46-4afa-a40c-6b62ad8304be`, owns the card. Test reservation released;
stop that relay normally before further exclusive tests.
[Evidence and limits](artifacts/notes/doom-dma-20261014.md).
<!-- /doom-dma-current -->

<!-- exclusive-dma-current -->
**Task-owned asynchronous DMA accepted (2026-10-14):** worker 1 now prepares,
launches and checks DMA1 with interrupts enabled; the MU handler only publishes
jobs and reads status. Host submit/poll calls release the session mutex between
commands. Two physical runs passed **48 exact transfers, 124 full monitor/RAM
pairs, 108 malformed/stale refusals and two canceled 64 KiB jobs**. Explicit
STOP acknowledged in **1.258 ms**; the independent 3,000-tick session deadline
also canceled before launch. Every canceled destination byte remained unchanged.
Maximum IRQ gaps are **10.710 / 10.990 ms**, versus **111.481 ms** synchronously
(90.1–90.4% smaller). All application allocations and shared handles retire.
Full system, DMA and cancellation replays pass on Linux and macOS; current
checks reject 24 DMA mutations, 42 cancellation mutations and 24 snapshot
mutations per applicable capture. The 73,728-byte coherent mapping stays pinned
until reboot. No forced unload, flash change, ATU remap or weakened audit.
This is still opt-in `--dma-proof`, **not Doom DMA/FPS acceptance**. Diagnostic
job wall time increases because source fill/check share CPU time; the measured
benefit is interrupt responsiveness. A physically stuck DMA engine/abort is not
claimed: native tests cover polling exhaustion/error/retention, while hardware
covers explicit STOP and RTEMS session timeout. Next: same-frame DMA/mailbox
comparison with a pinned Doom frame, then measured browser FPS and lifetime work.
Both archives are locally hash-verified and replayed; the public IPv6 page
returned HTTP 200 after reboot. Relay Python 2721 (supervisor 2717), boot
`33cafc40-6142-46dd-9c79-0156c77f2e4e`, owns the card. Test reservation released;
stop the relay normally before new hardware work. The archived physical modules
precede a native-tested logging-only diagnostic follow-up in the current host.
[Evidence, exact binaries and limits](artifacts/notes/dma-async-20261014.md).
<!-- /exclusive-dma-current -->

<!-- doom-bulk-current -->
**Doom mailbox bulk accepted (2026-10-14):** opt-in `--bulk` uses eight-byte
MU beats in fixed 1 KiB reads; no DMA or new RAM aperture. Same-run readback
improves **5.447 → 0.509 s** and delivered FPS **0.167 → 0.999 (5.97×)**.
Four complete same-frame comparisons, 28 frames, 30 full monitor/RAM pairs,
three refusals, exact input/ACK replay and owned/global STOP pass. All 95,622
allocations and 638 shared handles drain. Physical capture and snapshot
mutation tests each reject 24 corruptions. Preserve every audit, generation/
window check, reread, pin, STOP and uncertainty rule; scalar remains default.
The engine is unchanged. Native/card still differs by 6–8 pixels in the known
small region; palettes/padding and the first six previous card frames match.
Startup remains about 23 minutes. Replay timer-wrap coverage now depends on
actual audited elapsed ticks rather than the maximum configured budget.
The test workspace is `/home/mit/i960-doom-bulk-20261014`; port 8087 is stopped.
Both complete archives are saved and hash-verified locally. Reboot completed;
public IPv6 HTTP returned 200 from the Mac. Public relay Python 2127 now owns
the card in boot `cbeb9d86-ab62-4ac1-a830-1b30433e2e46`; the test reservation
is released. Stop the relay normally and coordinate before future card work.
Older ownership and next-step notes below are historical. Next: profile the remaining
render/service/ACK costs before any larger DMA transport.
[Exact results, sources, binaries and reproduction](artifacts/notes/doom-bulk-20261014.md).
<!-- /doom-bulk-current -->

<!-- doom-play-current -->
**Interactive Doom work (2026-10-13; six-frame input/STOP passed):**
The user chose browser play now, with optimization/debugging driven by use.
The opt-in persistent engine, bounded input FIFO, immutable frame/ACK channel,
browser relay and fresh-workspace build/run wrappers are implemented. Sanitized
native 40-frame input runs are deterministic, differ from no-input, and pass
owned STOP/heap drain. Channel bounds, stale ACK, overflow, timeout and STOP
race tests pass. Keep `--point-side-o0`, identity/ownership/guard checks and full
paired audits (normal play interval 60 s; diagnostic interval 3 s).

The corrected card candidate is running in
`/home/mit/i960-doom-play-20261013b`, boot
`83ecfee3-b3a2-47bf-a415-2ce0b7d0602f`, supervisor 2999 / Python 3001. Use browser port **8088**: temporary corrected
keyboard bridge supervisor 118766 / Python 118767 duplicates the existing FD;
the original 8087 owner retains frame/ACK/STOP work. New builds use corrected
163/162 fire/use codes directly on 8087. Do not open competing input clients.
It owns the card exclusively; the public autonomous IPv6 HTTP relay is stopped.
Do not unload or reuse its resources. Six physical frames, forward/release and owned STOP passed; mean readback
5.473 s, delivery 0.169 frames/s. The first 26 full audit pairs passed. A host
comparison finds 7–8 differing pixels in a small region; palettes/padding match.
The fresh session is live: 130 frames and 57 full audit pairs are preserved;
browser turn/fire passed, with muzzle flash and ammo 50→48. The play budget
expires around 23:58 Europe/Berlin October 13. Global shutdown/final file release
is not claimed; both original and duplicated descriptors must close normally. Prior ownership and “next”
statements below are historical. See [current evidence and guide](artifacts/notes/doom-play-20261013.md).
<!-- /doom-play-current -->

## Repository navigation (2026-10-13)

Start with [subprojects](subprojects/README.md) and the
[stock-card-to-applications guide](docs/reproduce.md). Historical root milestone
documents have moved into `docs/firmware`, `docs/loader`, `docs/rtems`,
`docs/games` and `docs/project`; the obsolete root aliases have been removed.
Edit and link canonical files. Tetris source is now `game/tetris/`; its old
source paths remain compatibility symlinks for loader builds. Preserve artifact
captures, source snapshots, binaries and archives. The organization pass updated
only links in 12 artifact navigation documents; see [change record](docs/reorganization-20261013.md).
Other source remains in `loader/`, `host/`, `rtems/` and `game/`.
See [repository policy](docs/repository.md) and [research index](docs/research.md).


<!-- doom-visible-current -->
**Bounded visible Doom and browser delivery accepted (2026-10-13):**
The opt-in `--visible` build skips the opening wipe and returns two 320×200
indexed frames with palettes. Both full card captures match native byte for byte;
ticks 2/3 have identical pixels, so motion and interactive gameplay remain open.
The batch passes **604 full snapshot/RAM pairs, 75 dual-stack rounds, 441
checkpoints / 66 ACKs**, in-engine STOP, repeat and global parked-state drain.
All **322,731 allocations and 9,917 shared handles** retire. Default full native
replay accepts **8,152 replies**; 24 startup, 13 frame and 24 snapshot mutations
are rejected. No shutdown assertion or native replay abort recurred.

Normal result collection takes **1,541.382 / 1,537.299 s**; STOP **26.718 s**.
Two-slot readbacks take **15.340 / 18.087 s**, including full-audit contention;
Mac PNG HTTP delivery averages about **19 ms**. These are not rendering FPS.
The immutable 131,072-byte archive uses the existing 8 MiB arena after private
engine cleanup; next entry and global drain release it. No RAM grant changes.
Keep full paired audits, independent native bytes, checkpoint ACKs and
`--point-side-o0`; uncertain transfers retain the session until reboot.
Next: bounded visible motion, then persistent frame publication/backpressure and
input. Keep this mode opt-in. Both archives are locally hash-verified. Public
IPv6 HTTP and outbound IPv6 are restored in boot
`083c2956-4f85-49e6-abb9-3d485c4d7422`; relay supervisor **1745**, Python **1843**
owns the card. Static gallery PID **1746** serves http://192.168.2.75:8086/ and
never opens the card. Test reservation released; stop the relay cleanly before
future exclusive work, and never force-unload a retained module.
[Exact sources, binaries, captures, browser instructions and limits](artifacts/notes/doom-visible-20261013.md).
<!-- /doom-visible-current -->

**Doom N3 first-frame and shutdown baseline accepted (2026-10-13):**
The bounded two-worker arrival barrier fixes shared cancellation racing a peer's
last acquire. A deterministic actual-allocator test reproduces the old SHCHECK 10
and passes with the barrier; the original card capture did not identify its exact
assertion line. Existing allocator stress and ownership/corruption tests pass.

The new card batch passes **626 full snapshot/RAM pairs**, **75 dual-stack network
rounds**, both normal Doom startups, in-engine STOP, and global STOP/final drain.
All **306,981 allocations** and **10,209 shared handles** retire; parked upload
query and full native replay of **7,832 replies** pass. Both 199-record normal
checkpoint streams match native, with **403 total records / 50 ACKs** across
normal/STOP/normal. Normal times: **1,522.551 / 1,514.546 s**; STOP: **25.922 s**.
Pixel FNV **4000963876**, palette FNV **1611003811**. The 24 startup-evidence
mutations and 24 snapshot corruptions are all rejected.

Native replay now models a 1 ms command transport delay outside target locks;
the target mutex deadline is unchanged. A stale remote checkpoint helper was
also synchronized. `--commands-only` remains explicitly diagnostic and cannot
accept physical drain; default full replay was used for this new capture.
Preserve full paired audits, native oracle, checkpoint ACKs and the narrow
`--point-side-o0` workaround. The engine and 8 MiB arena are unchanged.

This accepts the bounded initial wipe frame, STOP/repeat and system drain—not
visible gameplay, browser Doom or rendering FPS. Next: bounded visible-frame
progression, framebuffer readback and browser delivery, with the same full gates.
After local archive verification and reboot, public IPv6 HTTP returns 200 from
the Mac; outbound IPv6 fetch also passes. Production relay supervisor **4358** /
Python **4359** owns the card in boot `c76b2f32-a14d-4c03-952f-cbfa6b254cb9`.
Test reservation released; coordinate and stop the relay cleanly before reuse.
[Exact sources, binaries, captures, failure reproductions and results](artifacts/notes/doom-shutdown-20261013.md).

**Height/branch diagnosis (2026-10-13; full Doom still unaccepted):**
The first 49 checkpoints match, including all decoded sector-height and side
texture-ID fingerprints. At request 4,670 the card spawns in subsector **1394** /
sector **82** (floor **−72**, ceiling **96**); host and independent WAD decode select
**226 / 0** (floor **0**, ceiling **192**). Both recorded height calls correctly
add viewheight **41** to the card's floor, producing **−31**. Do not patch the
camera height to mask the earlier wrong BSP selection.

A captured `cmpi` / `cmpib` / `testg` ordering loses the intended condition code.
An explicit model predicts the exact wrong sector. A bounded probe outside RTEMS
uses the same **160-byte optimized function body** before linking: optimized
code fails **2/9** vectors, scheduling disabled still fails **1/9**, and `-O0`
passes **9/9**. All **27 transactions / 2,970 commands / 81 paired staging phases**
pass full audit, RAM restoration and clean unload. This confirms a function
miscompilation, not a global compiler fix or full Doom success. Preserve accepted
kernel/toolchain binaries; disabling scheduling alone is not sufficient.

The long run preserved **279 full snapshot/RAM pairs**, 37 network rounds,
27,725 exact WAD fragments and 188 retrieved checkpoints. Last retrieved marker:
planes finished (43). No new post-render/wipe/copy marker was retrieved; this does
not narrow the exact hang beyond the previous masked-render marker or establish
a fault PC. First frame, startup STOP/repeat and final drain remain unaccepted.

Next: audit/fix backend condition-code dependencies (or a narrowly verified
implementation), broaden the small card proof, then rebuild and repeat every
native/ABI/placement and full N3 gate. Add bounded host-confirmed draining for
selected hang markers; current nonblocking logging can outrun host retrieval.

Exact binaries, sources, captures and replays are archived. Public HTTP returned
200 after reboot and the clean probes; reservation released. Production relay
PID **19965**, boot `e7e1bcd3-0421-4d31-8fa9-9d6748d7110e`, owns the card; stop it
cleanly and coordinate before future exclusive work. [Evidence](artifacts/notes/doom-height-20261013.md).


**Startup checkpoints (2026-10-13; divergence localized, N3 still unaccepted):**
The first 50 scalar checkpoints match the native host. Record 51, stage 38,
first differs: player `viewz` is **−31 map units on i960 versus +41 on host**,
at WAD request 4,674, before the differing texture read. Position `(0, −160)`,
angle 90°, view sine/cosine, level counts and the side texture-ID fingerprint
match. Counts do not prove all geometry contents match. BSP, planes and masked
rendering finish; no `DG_DrawFrame` checkpoint or owned exit was captured.

The physical run preserved 170 checkpoint records, 274 full snapshot/RAM pairs,
one extra snapshot plus 40 final RAM words, and 37 network rounds. All 27,725
completed WAD fragments (14,194,884 bytes / 4,764 requests) match the pinned WAD.
An upload-query timeout retained the module. Final fault PC, first frame, STOP,
repeat and drain remain unknown/unaccepted; do not weaken their gates.

The opt-in 144-byte API and separate read-only channel use a non-overwriting
512-record, 16,400-byte registered log inside the existing 8 MiB arena. Native
normal/STOP/deadline/read-error/repeat and the accepted N2 replay pass. Runtime
code fits the existing guarded engine window. Exact card/build archives are local.
After hash verification and reboot, public IPv6 HTTP returned 200 from the Mac.
Exclusive reservation released; production relay PID 3737 in boot
`5e697ec6-a2e7-488d-95b3-4262e31f9b7f` owns the card. Coordinate and stop that relay
cleanly before future exclusive use.

Next: checkpoint player spawn and height calculation (`mo->z`, floor/ceiling,
viewheight, bob, sector/subsector selection), compare relevant field offsets and
signed fixed-point operations. Independently bracket the path from completed
masked rendering to `DG_DrawFrame`; the wrong height does not yet explain the hang.
[Evidence and reproduction](artifacts/notes/doom-checkpoints-20261013.md).


**N3 actual startup (2026-10-13; implemented, not physically accepted):**
The real private-library Doom engine passes ten native first-frame / STOP /
deadline / read-error / repeat cases, with exact reference pixels and palette.
Both card attempts entered actual initialization but timed out before returning
an accepted frame. The first completed 4,769 WAD requests; the compatibility
retry completed 4,764. Both match the host through request 4,674 and then choose
the same different texture region. Every captured completed WAD fragment matches
the pinned file. Preserve both failures; do not substitute host/model success.

Startup-only `-mold-align` corrects an independently measured allocator/layout
mismatch: 55 Doom/zone/API constants match the 32-bit host and RTEMS callback
offsets stay unchanged. It did **not** remove the hardware failure. Candidate
span 744,608 bytes, 13,231 relocations, admission 797,532 bytes, zero unresolved
imports; no new RAM grant. Its kernel SHA256 is
`25dd26bc206cec40f77e55a9a7666adb6df1f85cf7c6d662d1c301fed1bec4a5`.

The retry preserved 275 full snapshot/RAM pairs plus one complete snapshot and
44 words of its final RAM page; captured fault markers are zero, but the fault
PC and final state are unknown. Packet pumping between four-word audit groups
allowed 36 complete dual-stack rounds, versus six previously. All full audits
remain required. The upload query timed out after 2,772.949 ms and the driver
retained resources until reboot. Startup-only aggregate budget is 90 minutes;
per-engine 30-minute and per-read five-second limits are unchanged.

Keep startup opt-in and N2 as the accepted baseline. Next: independently readable
startup checkpoints/fingerprints around level setup, texture precache, draw and
exit; locate the first state divergence before another full attempt. Then repeat
normal / partial-read STOP / normal with complete replay and drain. Neither this
first-wipe milestone nor visible/browser Doom is accepted yet. Both captures are
saved; reboot cleared retained resources and public IPv6 HTTP returned 200. The
Doom test reservation is released; coordinate with the public relay before reuse.
[Evidence and current status](artifacts/notes/doom-startup-20261013.md).


**N2 WAD batching checkpoint (2026-10-12):** opt-in `--wad-batch`
uses owned, pinned 4 KiB requests assembled from ordered 512-byte fragments.
CRC, exact lengths, sequence/offset binding, STOP, timeout, full image/RAM audits
and final drain remain enforced. First-frame host trace: 27,648 → 4,747 logical
requests (82.83% fewer), identical delivered bytes. Small on-card cache probe:
24 → 7 requests, mean 3.588 → 1.655 s (2.17×; two runs per size, including report
queries, both using WAB1). No on-card Doom startup or FPS claim. Six host demos
retain all 12,600 frame hashes. Extra peak payload memory is 7,936 bytes plus
allocator overhead, within the unchanged 8 MiB arena.

Physical STOP/drain completed at tick 101,897. The live harness then failed an
obsolete expected-cancellation count (14 rather than 15); the raw failure is
preserved. A labelled derived view recovers the final raw reply and kernel
monitor log, separates and validates exception diagnostics, and passes unchanged
network audits plus full upload/native replay (7,949 commands). Keep this
qualification when citing acceptance; do not call the original live harness a
clean pass. The harness is corrected for future runs. Keep the feature opt-in.
[Evidence, reproduction and limits](artifacts/notes/doom-batch-20261012.md). Next is N3: bind batching
into a newly authenticated engine image, perform bounded actual Doom
initialization, then verify the first frame. The accepted old diagnostic engine
still uses the 512-byte ABI; do not silently reuse its admission hashes for a
changed engine. Coordinate hardware ownership before testing.

**Accepted engine-preflight baseline (2026-10-12):** the engine-linked diagnostic
passed on-card normal / STOP / normal, changed-code/metadata refusal, executable
revalidation and full drain at tick 100,085. The bit-64 failure was a dispatcher
window: incoming task identity on the outgoing stack. Opt-in `--dispatch-atomic`
keeps interrupts masked through transfer and preserves the caller's saved level.
No IRQ guard or owner admission was relaxed. The 1 MiB initial reservation and
contiguous 6 MiB zone now have physical acceptance; candidate span 754,448 bytes,
13,175 relocations, admission storage 807,148 bytes, measured port peak 6,356,612
bytes plus separate cache/image/proof/stack costs. Both bootstrap windows remain
protected. Keep `--doom-engine`, `--dispatch-atomic` and `--wad-poll` opt-in.
Full native capture replay passes 7,853 commands; instant host replies had failed
the probe's clock-liveness check, fixed only in the replay transport model.
44 runtime/cache/relocation/owned/engine mutations and seven IRQ mutations reject.
Actual Doom initialization/rendering remains pending. The original next step was WAD batching; see the N2 checkpoint above.
Engine initialization and first-frame verification remain pending. Preserve all full audits.
The historical global ISR-level getter remains unfixed; this owner predicate uses
a read-only PC query. Coordinate card ownership before further hardware tests.
[Accepted evidence and replay instructions](artifacts/doom-progress-20261012/README.md).


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
[Physical evidence](artifacts/notes/doom-platform-20261012.md).

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
[Evidence](artifacts/notes/doom-relocate-20261012.md).

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
[Evidence](artifacts/notes/doom-cache-20261012.md).

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
[Contract](game/doom/runtime/entry/README.md) · [Evidence](artifacts/notes/doom-entry-20261012.md).

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
[Contract](game/doom/runtime/SHARED-ARENA.md) · [Evidence](artifacts/notes/doom-shared-20261012.md).


**Doom allocation runtime accepted (2026-10-12):** namespaced malloc/calloc/
realloc/free/strdup now use the existing 8 MiB resident arena without replacing
system libc. Six host demos / 12,600 frames match the accepted pixel/palette/tic
corpus. The opt-in `--doom-heap` card test passed a 6 MiB calloc, resizing/OOM,
strdup and a 64 KiB allocation retained until confirmed STOP drain, alongside
six network rounds. Full replay and native sanitizers passed; reboot returned
and public IPv6 HTTP is restored (200). The combined i960 object is 631,112 bytes
with 53 unresolved imports. Single-worker ownership remains; arbitrary task
launch, shared allocator serialization and other runtime/WAD services are next.
[Contract](game/doom/runtime/README.md) · [Evidence](artifacts/notes/doom-runtime-20261012.md).


**Doom host determinism fixed (2026-10-12):** all three variable frames were
out-of-post sprite reads caused by negative fixed-point samples wrapping to 127.
Bounded masked sampling now passes 24 host runs / 50,400 draws across both
Freedoom IWADs and four heap fills, with complete pixel/palette/tic comparisons.
Focused renderer sanitizers pass. The i960 object is 627,096 bytes (+240), with
58 unresolved symbols unchanged. No Doom ran on-card. The parallel 8 MiB arena
is now proven; libc/task/WAD integration is next. [Findings](game/doom/DETERMINISM.md)
and [exact evidence](artifacts/notes/doom-determinism-20261012.md).


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
are preserved with their fixes. [Exact artifacts](artifacts/notes/rtems-resident-upload-20261012.md).
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
IPv6 HTTP was restored. [Exact captures](artifacts/notes/segmented-loader-20261012.md).
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
See [RAM contract](rtems/residentnet/LARGE-RAM.md), [captures](artifacts/notes/rtems-large-ram-20261012.md), and [Doom OS plan](game/doom/OS-PLAN.md).

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
[Evidence](artifacts/notes/journal-20261011.md) · [Play instructions](game/raycaster/journal/USER-TESTING.md).


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
[the captures and remaining work](artifacts/notes/browserqueue-20261011.md).


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
[Contract](game/raycaster/slotopt/README.md), [complete measurements/artifacts](artifacts/notes/slotopt-20261011.md).
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
[Contract](game/raycaster/combined/README.md), [measurements and captures](artifacts/notes/ackpublish-20261011.md).


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
[Contract](game/raycaster/queue/README.md), [measurements and failure evidence](artifacts/notes/framequeue-20261011.md).



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
[profiles, artifacts and next bottleneck](artifacts/notes/callback-20261011.md).


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
and [captures/recovery status](artifacts/notes/rtems-residentnet-20261011.md).


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
[measurements and artifacts](artifacts/notes/word-memory-20261011.md).
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


**Game application track (2026-10-11):** [CHIP-8 → framebuffer → raycaster → Doom](docs/games/GAME-PROGRESSION.md).
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
[evidence](artifacts/notes/irq-lifecycle-20261011.md).
Logical unbind is tested; the later failed-control checkpoint above covers
synthetic omissions during teardown. Physical hot-unplug remains unproven. Task shutdown still cooperates with a stop flag.


**Concurrent host control (2026-10-11):** three card runs passed with STOP
issued by an ioctl on a second host thread while the firmware callback was
pending. A separate control mutex/window is joined before completion/cleanup;
wrong epochs, duplicate STOP and late requests were refused. Both ISR contexts
drained; full RAM/MU restoration and unload passed. IPv6 HTTP restored.
[API and lifetime contract](rtems/switch/CONCURRENT.md),
[evidence](artifacts/notes/irq-concurrent-control-20261011.md).
Workers remain stop-aware. Live alias-close coverage is not final-close or
physical-removal fault injection; next are broader lifecycle failure tests and
non-cooperative task containment.


**Live web system information (2026-10-11):** the IPv6 Vader page now shows
card runtime uptime, RTEMS/lwIP and CPU details, memory capacities, HTTP counts
and RX/TX/drop counters. CPU utilization and temperature are explicitly
unavailable; measured timer-bus frequency is not labelled as CPU frequency.
24 live HTTP checks and full cleanup/restart passed. Production module is now
`autonet-module-system-info`, paired with the updated `autonet` image.
[Details](rtems/net/SYSTEM-INFO.md), [artifacts](artifacts/notes/rtems-system-info-20261011.md).


**Nested STOP and timeout checkpoint (2026-10-11):** all twelve `stopcases`
card runs passed. STOP at critical depths 2/1 was recorded at ticks 18/30 but
controller dispatch/drain waited until outer release at tick 40. Missing STOP
reached the 128-tick event deadline; missing RELEASE exhausted its finite loop
and returned with only the expected `0x4000` flag. All contexts, guards, paired
RAM/MU restoration and unload checks passed; no reboot/flash. IPv6 HTTP restored.
[Implementation](rtems/switch/STOP-CASES.md),
[evidence](artifacts/notes/irq-stop-cases-20261011.md).
Next: concurrent user-control/lifetime design and non-cooperative task containment.
These workers remain stop-aware; deliberate message omission is not a full host
crash or proof of recovery from permanently masked interrupts.


**Pending-callback MU STOP milestone (2026-10-11):** three `mustop` card runs
accepted a one-shot host STOP at ticks 34/41/52 while both owned ISR contexts
were live and firmware sequence 1 was still pending. Workers observed the stop
flag, both contexts drained, and the card acknowledged before host RELEASE
allowed the callback to return. Zero faults; full RAM/MU restoration and module
unload passed. IPv6 Vader HTTP restored. [Evidence](artifacts/notes/irq-mu-stop-20261011.md).
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
restart. [Evidence](artifacts/notes/irq-deferral-20261011.md).
Next: integrate independent MU STOP with the two CPU-bound task contexts and
prove safe draining during an active callback. Resident operation and general
interrupt nesting remain unproven; production stays on `autonet`.


**Two-task interrupt-switch milestone (2026-10-11):** three bounded card runs
passed timer-driven switching between CPU-bound RTEMS tasks. Each run recorded
32 IRQ-path handoffs, 31 observations of both ISR continuations live, and 16
entries/returns per task. Separate task/ISR stacks, register sentinels, frame
ownership, draining and full restoration passed; web service restored without
reboot/flash. [Implementation](rtems/switch/README.md),
[evidence](artifacts/notes/irq-switch-20261011.md). This is bounded preemption,
not a resident monitor; next are deferred-dispatch stress and MU STOP integration
while the CPU-bound task contexts are active.

**Owned ISR stack milestone (2026-10-11):** an owned, guarded C interrupt stack
and explicit GPR/TC preservation passed 126 isolated stress interrupts and 546
bounded RTEMS/control interrupts. Deep call chains, sentinels, PC/TC roundtrips,
frame/guard checks and independent STOP/HALT passed; full cleanup and web restart
passed without reboot/flash. The hardware entry frame stays in place: movable
per-task interrupt contexts and unrestricted preemption remain future work.
[Implementation](rtems/interrupt/README.md),
[evidence](artifacts/notes/owned-interrupt-stack-20261011.md).

**Framed control milestone (2026-10-11):** CTL1 messages, retries and invalid-frame
rejection passed over IMR1/OMR1. Independent STOP froze bounded RTEMS at tick 362;
subsequent STATUS confirmed it, then independent timer HALT took 9.48 ms. Firmware
sequence stayed 1 → 1 throughout. Full cleanup passed, without reboot/flash;
Vader service restored. [Implementation](rtems/control/MU-FRAMED.md),
[evidence](artifacts/notes/mu-framed-20261011.md). This does not establish
runaway-task STOP or unrestricted preemption. Next: owned IRQ stack and complete
asynchronous context preservation before lowering task interrupt priorities.

**MU echo milestone (2026-10-11):** a timer ISR echoed an IMR1 word through OMR1
in 11.02 ms while firmware sequence stayed 1 → 1. Full timer/RAM/MU restoration
and module unload passed. The first trial retained resources after an incorrect
local OISR acknowledgement; a host reboot and host-side acknowledgement fix
preceded the successful retry. [Implementation](rtems/control/MU-ECHO.md),
[evidence](artifacts/notes/mu-echo-20261011.md). Independent STOP and unrestricted
preemption remain unproven; next is framed control plus independent STOP.


**Current work (2026-10-11):** card-hosted IPv6 HTTP and stock-coexisting autonomous RTEMS now pass live tests. A hardware timer delivered 2,009 ticks/task wakeups during 20 seconds without host polling; the network build advanced 509 ticks during five silent seconds. IPv6 Internet HTTP, dual-stack echo, a one-minute IPv6 stress run, and kernel STOP-before-restore cleanup passed. See [current work report](artifacts/rtems-web-autonomous-20261011/README.md) for artifacts, failed trials, limitations and the published server.

**Current development roadmap:** [loader memory extension, RTEMS and remaining gaps](docs/rtems/DEVELOPMENT-PLAN.md). Next: M1, generalize the proven larger RAM profile; preserve scalar/BIO1 compatibility.


**Current index (2026-10-11): [findings, evidence and unresolved questions](CURRENT-FINDINGS.md).** Earlier milestone notes below retain their historical context.

**IPv6 is implemented and tested on the card (2026-10-11):** dual-stack ping, UDP/TCP echo, AAAA and IPv6 Internet HTTP. [Usage](rtems/README.md#ipv6-usage-and-scope), [preserved evidence](artifacts/rtems-ipv6-20261011/README.md). Use the new `i960-rtems-ipv6-20261011` launcher with `--ipv6` or `--internet6`; the latter also routes IPv4 DNS. The cooperative execution model and RAM limits remain unchanged.

**RTEMS now runs on the card (2026-10-11): [implementation and usage](rtems/README.md).** RTEMS 4.6.6 tasks persist across bounded firmware callbacks; lwIP 2.1.3 provides ICMP, UDP/TCP echo and card-originated DNS/HTTP through a Linux TUN/NAT gateway. The original `net` profile uses host-supplied ticks; the newer `autonet` profile uses hardware timer interrupts with bounded work and preserves stock firmware service. [Exact artifacts and findings](artifacts/rtems-20261011/README.md). No additional flash programming or reboot.


**T4 complete (2026-10-10): [play Tetris over SSH](docs/games/TETRIS-TERMINAL.md).** The terminal client passed a 30-minute real-SSH test: 35,846 native-matching frames, 68 restarts, 19.91 Hz. Quit, Ctrl-C, connection loss/reconnect and resize cleanup passed. Use `ssh -t mit@192.168.2.75 /home/mit/i960-tetris-t4/play.sh`. Full RAM restored, module unloaded; no reboot or flash.


**T5 complete (2026-10-10): [persistent BIO1 sessions](docs/loader/PERSISTENT-SESSION.md).** 1,000 frames matched native output at 41.1 ms median; a separate 400-frame run sustained 20 Hz. Process-kill/ownership cleanup and full final RAM restoration passed. `host/session/` keeps paired code/payload checks every frame and full staging audits every 32 frames and close. The subsequently completed T4 terminal client uses this transport; no reboot or flash.


**T3 complete (2026-10-10): [long Tetris hardware replay](docs/games/TETRIS-REPLAY.md).** 1,000-call main replay plus 64 repeat calls matched native state/frame bytes; all RAM restored and probes unloaded. Median full CLI latency 306 ms (~3.26 updates/s), payload-command interval ~6.18 ms. This baseline motivated the now-completed T5 session optimization; T4 terminal play is now complete; see the latest milestone above. No reboot or flash.

**T2 complete (2026-10-10): [bounded Tetris steps](docs/games/TETRIS-STEP.md) run on the card.** Explicit 240-byte state, 20-tick bound, 24×80 rendering; 1,024 native/interpreted transitions agree, and nine live transactions match the native reference byte for byte. RAM restored; no reboot/flash. T3 replay, T5 persistent sessions and T4 terminal play subsequently passed.

**T1 complete (2026-10-10): [bounded text/framebuffer I/O](docs/loader/BUFFER-IO.md) is hardware validated.** BIO1 supports 4 KiB input / 8 KiB output; live text, 24×80 frame, capacity rejection and repeat/scalar regression passed with RAM restored. T2 subsequently converted the blocking game into hardware-tested returning steps.

**Next work:** M1 in [the integrated plan](docs/rtems/DEVELOPMENT-PLAN.md): generalize the proven larger loader profile inside the existing allocation. Tetris T1–T5 and cooperative RTEMS/networking are already implemented. The older [Tetris plan](docs/games/TETRIS-ON-CARD-PLAN.md) records its milestone history; [the RTEMS roadmap entry point](docs/rtems/RTEMS-HOST-NETWORK-PLAN.md) maps original milestones to the integrated plan.

**Latest hardware milestone (2026-10-10): [runtime software loader](docs/loader/SOFTWARE-LOADER.md) works after PC startup.** Three live executions (two C programs) passed without reboot or another flash write. Use `host/loadrun/` and `loader/runtime/` from the repository root; earlier internal-RAM and pre-programming plans below are historical. Supports cooperative returning functions up to 64 KiB, with one argument and a 32-bit result. RAM restored and module unloaded after each run. Recovery remains untested.


**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](docs/firmware/FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


Latest: [one-shot programming harness](docs/firmware/ONE-SHOT-PROGRAMMING.md) is implemented in `host/program/`
(repository-root relative). Native transport/failure tests and a 105-command live
RAM-only rehearsal passed. Wrong activation token rejected before driver
registration; no programming doorbell issued. Full stock RAM restored and probe
unloaded. Exact binaries/captures are in `artifacts/one-shot-harness-20261010/`.
At this rehearsal milestone programming was still pending. Programming, full
readback and patched boot subsequently passed; see FIRMWARE-PROGRAMMED.md.
Recovery testing remains excluded.


Latest (2026-10-10): [programming preflight and live CPU verification](docs/firmware/PROGRAMMING-PREFLIGHT.md)
passed. The CPU read all 512 KiB of the candidate through programmer alias
C1F2C000 with explicit cache invalidation and matched CRC32 2012D01F. All 105
commands completed cleanly; original staging/table/code restored, probe unloaded.
The descriptor policy and bytewise post-program flash-readback route are now
documented. Next implement the one-shot programming state machine and its
failure tests. No flash programming or recovery test occurred. Exact evidence
is in `artifacts/programming-preflight-20261010/` from the repository root.


Latest live experiment: [ROM-FETCH-LIVE.md](docs/loader/ROM-FETCH-LIVE.md). A wrapped
staging-relative `0x21` upload changed command-table word `C001F9BC`, and
`0x6F` executed RAM handlers. After cache and RAM-call controls passed, a
callback called a stock flash `RET` at **FEFB022C** after startup and returned
`017F`. All RAM bytes and the stock table were restored; the module was
unloaded. The earlier `FEFC8208` timeout used a wrong physical address:
the disassembly's FEFC8000 label is not the component's full-ROM location.
Read the live 8-bit flash-bus mapping evidence before choosing flash targets.
The *new* FEFE001C handler remains unflashed and untested. No flash write or
recovery check was performed. This supersedes the older execution boundary.
The [live staging rehearsal](docs/loader/STAGING-REHEARSAL.md) now passed: all six full
512 KiB captures match stock/candidate/restored-stock hashes; 74 commands
completed cleanly, original staging restored, module unloaded. Sources and
binaries are in `artifacts/staging-rehearsal-20261010/`. Next resolve CPU cache
visibility in the 2B/1 programming path, exact updater inputs, update-time
handler behavior and fresh physical flash readback. Candidate remains
`flash_ready: false`; recovery testing is excluded by the user.

Historical step-4 result: [ROM-HANDLER-STEP4.md](docs/loader/ROM-HANDLER-STEP4.md).
The exact ROM-backed candidate has an offline Fujitsu type-2 MIMG wrapper,
and a fixed live read verified opcode `0x6F` dispatch word `C001F9BC` still
contains stock handler `C001FE98`. The read-only probe was unloaded. The
MIMG has not been accepted by a vendor updater; at step 4 no table write,
code execution or flash instruction fetch after EBCR setup had been tested. The
candidate remains `flash_ready: false`.

Current step-3 candidate: [ROM-HANDLER-STEP3.md](docs/loader/ROM-HANDLER-STEP3.md).
`loader/romhook/` and `artifacts/romhook-20261010/` place the PING handler at
FEFE001C in verified firmware flash padding. Stock staging memory was rejected
because reachable stock paths free it. The image is still `flash_ready: false`:
post-startup flash instruction fetch, table visibility, recovery and programming
interaction remain untested. Keep the older DRAM candidate for comparison.

Latest DRAM audit: [DRAM-HOOK-AUDIT.md](docs/loader/DRAM-HOOK-AUDIT.md). The pinned stock
bootstrap clears C0120000 before the metadata hook, the reviewed allocator
starts at C0140000, and a fixed live read found 64 zero bytes. This does **not**
reserve C0120000 for the lifetime of the firmware. The stockhook candidate
remains `flash_ready: false`; next investigate firmware-owned handler storage.

Current offline candidate: [STOCK-PRESERVING-HOOK.md](docs/loader/STOCK-PRESERVING-HOOK.md). An 84-byte metadata hook installs opcode `0x6F` as a returning PING, then enters the original stock firmware. The candidate is not flashed; `C0120000` remains an unproven exclusive DRAM location. Build sources are in `loader/stockhook/`, artifacts in `artifacts/stockhook-20261010/`.

Historical execution analysis: [LIVE-EXECUTION-HANDOFF.md](docs/loader/LIVE-EXECUTION-HANDOFF.md) did not account for wrapped 32-bit upload offsets. The later live experiment above established a RAM callback handoff.

Latest: [RAM-WRITE-VERIFIED.md](docs/loader/RAM-WRITE-VERIFIED.md). Fixed 16-byte scratch upload/readback/restoration passed at C0FAC010 in the extra staging allocation block. All 22 commands clean; original 64 bytes restored, probe removed. No execution/recovery/flash.

Latest: [RUNTIME-READ-VERIFIED.md](docs/loader/RUNTIME-READ-VERIFIED.md). Paired live reads verified entry bytes, board C0110780, alias C1000000 and 512 KiB callbacks. Hardened exact read allowlist passed; no upload/execution/recovery/flash.

Latest: [STAGING-POINTER-VERIFIED.md](docs/loader/STAGING-POINTER-VERIFIED.md). Live paired four-byte reads confirmed C0F2C000 at C0112A70. Fixed-purpose read gate only; no upload, execution, recovery entry or flash. Probe removed cleanly.

Allocator derivation: [STAGING-ALLOCATION.md](docs/loader/STAGING-ALLOCATION.md). Enquiry2 plus the traced allocator predicted C0F2C000; [STAGING-POINTER-VERIFIED.md](docs/loader/STAGING-POINTER-VERIFIED.md) later confirmed it by direct read. The normal harness still rejects out-of-window offsets.

Latest: [SSH recovery-entry investigation](docs/firmware/SSH-RECOVERY-ENTRY.md) and [serial preparation](docs/firmware/SERIAL-RECOVERY-SETUP.md). Physical access is available; serial comes later. Read-only SSH preflight passed; RAM-offset lead remains unproven and no recovery transition was attempted.

Latest: [BOOT-RECOVERY.md](docs/firmware/BOOT-RECOVERY.md) establishes an embedded recovery monitor (PCI 1069:0011) and partial vendor validation. Entry/restoration remain untested; continue over SSH without forcing a flash fault.

Latest programming audit: [PROGRAMMING-RECOVERY.md](docs/firmware/PROGRAMMING-RECOVERY.md). The matching 512 KiB route uses 2B/1 and rewrites the lower 496 KiB; 22 returns an error on this route. An offline experimental MIMG package is archived, but vendor acceptance and recovery remain unverified.

Current test preparation: [LIVE-TEST-PREFLIGHT.md](docs/loader/LIVE-TEST-PREFLIGHT.md). Read-only host preflight passed; v2 candidate guards all three DMA channels and suppresses the option ROM before releasing PCI retry. No custom execution or flash yet.

Latest development: [POSTINIT-LOADER.md](docs/loader/POSTINIT-LOADER.md) documents an offline DRAM-loader patch prototype and the recovered metadata handoff. Sources are in loader/postinit/. It is not flashed or hardware validated; do not use the legacy image builder for the full dump.

**Local handoff:** See [artifacts/ROM-INVENTORY.md](artifacts/ROM-INVENTORY.md) and [artifacts/ROM-DUMP-WORKLOG.md](artifacts/ROM-DUMP-WORKLOG.md). Original Fujitsu packages (29 and 39), decoded ROMs, all snapshot sessions, disassemblies and collector are local; SSH is unnecessary for offline analysis.

Read **[SNAPSHOT-RECOVERY.md](docs/firmware/SNAPSHOT-RECOVERY.md)** first. In-system recovery
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

See the [staged preemption and DMA plan](docs/rtems/RTEMS-PREEMPTION-DMA-PLAN.md). Order: independent control
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

## AcceleRAID 160 combined RTEMS/timer gate (2026-10-17)

Use [rtems/accele160/autoclock/README.md](rtems/accele160/autoclock/README.md)
and [exact accepted evidence](artifacts/current/accele160-autoclock-20261017/README.md)
before any next-board clock work. The RAM-only 17-page operation-13 image
passed two repeated STOP/no-host batches: an RTEMS worker woke at hardware
timer-1 tick 5 and sustained 52 ticks during each bounded CPU loop. Its PC
priority was 0; timer-1 mask/map/reload and owned ISR stack were observed.
Both paths restored stock timer/vector/firmware context, loader page, stage
and all owner records. Six paired full 1 MiB flash reads and independent
inventories matched the unchanged firmware. Old card `0000:37:04.1` was
unbound and untouched. Offline replay and four tamper tests pass.

**Do not reuse the earlier candidate's `modpc` form.** On i960 the output
operand supplies the replacement PC bits; use an initialized `+r` operand
with mask `0x1f0000`. The output-only form left the worker at priority 31,
blocking further timer interrupts. Guard only timer-1 pending bit `0x2000`;
stock timer 0 can be pending at `0x1000` while RTEMS starts masked. The
accepted binary SHA-256 is `d7234b9309e5e435456ddd50905787b4ddbab4e7fd9e0ea18d5094ca09a39db5`.
The accepted test is bounded tick delivery, not unrestricted ISR-driven task
preemption or a resident network/Doom runtime. Next qualify a bounded task
switch with an independent finite STOP/quiescence path. For physical runs,
confirm exact new-card BDF, old card unbound, no retained modules, stock
timer/vector state and two same-boot full flash reads. Never force-unload a
pending operation-13 command.

## AcceleRAID 160 bounded RTEMS preemption (2026-10-17)

The new-card [two-worker preemption gate](rtems/accele160/preempt/README.md)
passed two card batches, each with STOP and finite 120-tick no-host exit. The
owned timer-1 ISR calls `_Thread_Dispatch()` after RTEMS clock accounting;
three separate 8 KiB ISR continuations prevent a suspended task's ISR stack
from being reused. Two CPU-bound equal-priority workers made 8 and 120
hardware-tick handoffs; all per-task entries/returns matched, and the stock
timer/vector, firmware SP, loader page, stage and all owner records restored.
Six paired full flash reads and independent inventories matched the unchanged
firmware. The [exact accepted binary/evidence](artifacts/current/accele160-preempt-20261017/README.md)
has offline replay and four tamper tests. The first diagnostic host check
failed only because it read even grant page 20; accepted traces are written
to odd page 21. Use exact source and image SHA pins in the physical runner,
keep old card `0000:37:04.1` unbound, and never force-unload pending op13.
This is a bounded proof with interrupt-enabled tasks, not a resident runtime
or recovery of a task that disables interrupts indefinitely. Next: finite
resident lease and independently enforceable quiescence, then network/Doom
memory and DMA admission.

## AcceleRAID 160 STOP-ignoring containment (2026-10-17)

The [new-card containment profile](rtems/accele160/contain/README.md) passed
two physical STOP/no-host batches on the existing operation-13 RAM gate. Two
CPU-bound workers do not read STOP or yield. The RTEMS controller observes
four more timer ticks of progress after STOP, suspends each worker, retains
one live ISR continuation per worker, and checks scheduler state, progress and
stack/ISR checksums 10,000 times before returning to stock firmware. STOP
ended at 14 ticks in about 259 ms; no-host expiry ended at 124 ticks in about
1.36 s. Four full flash reads and independent post-run timer/vector
inventories matched stock. [Exact binary and evidence](artifacts/current/accele160-contain-20261017/README.md)
replay offline and reject four tamper cases. No firmware write or old-card
change occurred. **Do not call this a callback-free resident service or a
watchdog:** permanently masked interrupts, scheduler corruption and active
DMA remain outside this finite controller lease. Preserve both retained ISR
contexts until the whole instance returns; never reclaim either task stack
while its continuation is live. The next gate is callback-free bounded
residency or independently enforced recovery plus explicit RAM/DMA ownership.

## AcceleRAID 160 callback-free handoff (2026-10-17)

The [RAM-only finite handoff](rtems/accele160/handoff/README.md) now passed
on the new card with no firmware write. Operation 13 returned in about
10.6 ms; a later host ENTER was consumed in a stock-firmware interrupt
frame. No-host expiry reached exactly 300 timer-1 ticks in 3.048 s, and
valid HALT took four ticks / 88.5 ms after a wrong token stayed pending.
Both paths restored firmware priority, SP, timer/vector/map/mask, loader,
stage and every allocator record. Four same-boot full flash reads and
independent pre/post inventories passed; [exact image and captures](artifacts/current/accele160-handoff-20261017/README.md)
replay offline with four tamper rejections. Image SHA-256 is
`1f448cdf017d3410e03a493f45f7ad37a8e4f4f3268c05270e5bc7fe10952f2a`.
For i960 `modpc`, use priority mask `0x1f0000` and an initialized replacement
value; the interrupt-frame saved PC at `FP-16` is process controls, not an
instruction address. This is a bare finite monitor, not resident RTEMS or
an independent watchdog. Keep the old card unbound. Next prove a bounded
resident RTEMS control task, task/ISR/DMA quiescence and explicit RAM/DMA
ownership before moving network or Doom services to the new card.

## AcceleRAID 160 channel-0 DMA checkpoint (2026-10-17)

Read the [corrected register inventory](rtems/accele160/dma_inventory_corrected/README.md)
and [bounded transfer result](rtems/accele160/dma_transfer/README.md) before
new-card DMA work. The 80303 DMA MMIO block is at i960 **local**
`0x00001400..0x000014ff`. The earlier `0xff001400` all-zero inventory is
invalid DMA evidence; its [failure record](artifacts/current/accele160-dma-inventory-20261017/README.md)
is deliberately retained. Corrected inventory showed channel 1 holding a
stock descriptor, while channel 0 and 2 were idle in sampled words.
Three 256-byte channel-0 card-to-host writes then passed to separately
pinned, guarded, coherent host buffers: initial HALT, reuse HALT and reuse
no-host expiry. Card descriptor fetch, byte count zero, inactive channel,
exact host bytes and both 4 KiB guards were checked before buffer/grant
release. The reuse image SHA-256 is
`2e2858b30cc89799549eca7aa0626128b36d1529d5bea7a0b1a967ee3e84dcae`;
[evidence and independent replay](artifacts/current/accele160-dma-transfer-attempt-20261017/README.md)
include eight full flash reads in four pairs and ten tamper rejections.
The old card remained unbound; no flash write occurred. This proves a
completed small transfer under finite RTEMS ownership, **not** abort/drain
of a genuinely stalled active DMA. On uncertain completion, retain host
buffer, card grant and modules; clearing CCR enable merely suspends DMA.

The subsequent [finite-chain STOP gate](rtems/accele160/dma_chain_stop/README.md)
passed twice: the card saw STOP while channel 0 was active at tick 21,
finished 13,000 descriptors / 26,624,000 bytes at tick 48, then permitted
host pin and stock-grant release after complete audits. Six full flash
reads, independent replay and ten tamper cases are archived. This proves
normal completion after an active STOP, **not** abort of a genuinely stuck
DMA transaction. The initial no-cache-invalidation attempts are negative
evidence. A fresh inventory verifier now treats stock channel-1's PCI
address as variable across boots while still checking its fixed descriptor,
local address and DCR. Keep channel 1 and the old card untouched.

The [active DMA suspend/resume gate](rtems/accele160/dma_suspend/README.md)
then passed twice with an unchanged image: STOP at tick 21 while CSR active,
CCR=0 until tick 25, two stable DAR/NDAR/BCR snapshots during the hold,
CCR=1 on resume, and final chain completion at tick 52. Host payload,
guards, channel-inactive state, grant, loader/stage and RTEMS restoration
were fully checked before release; four full flash reads matched stock.
[Exact artifacts and replay](artifacts/current/accele160-dma-suspend-20261017/README.md)
reject twelve mutations. CCR=0 **suspends, never cancels**. A genuinely
stalled/erroring channel and process-death cleanup remain unproved; retain
the host pin and card grant on any uncertainty.

The [host-timeout retention gate](rtems/accele160/dma_timeout/README.md)
held active channel-0 DMA from tick 21 through tick 101 in two unchanged-image
runs. During the hold, a 150 ms host wait deadline elapsed and premature
pin release returned `EBUSY`; the grant and buffer stayed owned. The finite
chain then completed at tick 128, after which full card/host/RTEMS audits
permitted release. Four full flash reads matched stock and
[replay](artifacts/current/accele160-dma-timeout-20261017/README.md) rejects
sixteen altered captures. This tests timeout retention, **not** actual PCI
fault recovery or killed-host-process cleanup. Do not free a DMA target on
timeout alone.

The [DMA host-process death gate](rtems/accele160/dma_process_death/README.md)
passed twice with the exact same finite-chain image. The owner process
deliberately killed itself after `DMA_HELD`; a new process found its PID
absent, the pin and grant retained, and early release denied with `EBUSY`.
After card resume at tick 101 and completion at tick 128, full card,
host, owner and RTEMS audits allowed release. Six full flash reads matched
stock; [captures and replay](artifacts/current/accele160-dma-process-death-20261017/README.md)
reject fifteen mutations. This does **not** establish cancellation of a
genuinely stuck/erroring PCI transaction, a death before the held checkpoint,
or whole-host crash recovery. Keep both allocations retained on uncertainty.

## AcceleRAID Doom browser gate (2026-10-17)

Read [the accepted live transport](rtems/accele160/doom_play/README.md) and
[replayable evidence](artifacts/current/accele160-doom-live-20261017/README.md)
before extending new-card play. Two generation-numbered RAM frame slots use
16 odd 4 KiB pages per 64 KiB frame because PIATVR cannot expose even pages.
The host checks full-frame FNV before exact-generation ACK; missing ACK is
bounded. A 32-frame card run passed at 2.329 card-side FPS. A separate
browser run delivered 32 byte-identical binary HTTP frames, acknowledged a
W press/release, and passed WAD, owner, bank, STOP and paired pre/post stock
flash audits at 2.320 card-side FPS. These are finite gates, not sustained
interactive play or browser-paint FPS. Retain the old card unbound, the full
audits and reboot-only callback release. Next qualify long-session STOP and
then DMA frame delivery.
**Card-profile boundary — 2026-10-18:** `card_profiles/README.md` is the
entry point for adding another i960 PCI device. Firmware, RTEMS and Doom
builders now validate explicit workflow/card pairs. `rtems/build.py --profile`
names an RTEMS experiment; `--card-profile` names hardware. DoomGeneric and
the private i960 Newlib/ABI port are shared; board clocks live in
`game/doom/runtime/platform/card_clock_*.c`. Do not copy PG flash offsets,
AcceleRAID FLASHIMAGE commands, RAM/cache maps or DMA code across profiles.
New-card admission requires exact identity, read-only stock archive, bounded
RAM proof, ownership/STOP, full post-reset audits and a dedicated transport.
The profile registry is a guard, not proof that a new card is safe to flash.

**Persistent new-card Doom — 2026-10-18:** `./doom` starts the installed
AcceleRAID bundle via SSH/systemd; `./doom status` and `./doom stop` report
and stop it. See `game/doom/play/accele160/README.md` and
`artifacts/current/doom-persistent-20261018/README.md`. A 1,058-frame input/STOP
run passed all full audits and paired pre/post-reset stock-flash reads. The
reader driver is explicitly initialized on fresh boots. One session per boot;
retained resources must never be force-unloaded. Ordinary capture retention
is bounded, but every frame keeps guard/hash/marker/owner checks and a JSONL
receipt. Multi-hour soak and separate physical signal/disconnect tests remain.

**Exclusive-session reuse investigation:** `game/doom/play/accele160/reuse`
and `artifacts/current/doom-reuse-investigation-20261018` prove native actual
Doom STOP/fresh-image Quit/fresh-image STOP in one process with unchanged
arena/fixed pins and identical first 32 frames. Outer-runtime ASan/UBSan also
passes; it is not i960/DMA/IRQ restart acceptance. The installed card is
confirmed in terminal QUIE and remains reset-only. Next implement audited
RTEMS idle/rearm, fresh template/data/BSS admission and monotonic transport
counters with explicit stale-key discard. Never reset the live arena or
force-unload mappings. Linux exposes PM reset, but it was not attempted.

**Reusable AcceleRAID candidate (2026-10-18):** `DOOM_REUSABLE=1` and
`run_bridge.py --reusable` retain RTEMS and fixed/DMA ownership between games.
Ops 9/8 audit/rearm a retired image, followed by a fresh original template +
zero BSS + relocation admission. Global counters persist; slot parity is local
to each engine run. Never reinitialize the arena or call a retired engine.
Native policy sanitizer/browser/DMA tests pass. Physical STOP / fresh
image / menu Quit / fresh image / STOP passed 65/43/65 frames, both rearms,
96 paired PIO frames and all stale gates. Both final guarded 1 MiB
post-reset flash reads pass unchanged. The old card was then removed; explicit
peer checks now accept confirmed absence, while target selection stays strict. Positive browser/CLI idle restart and idle host-loss gates remain. See `artifacts/current/doom-rearm-20261018`.
Installed bundle-v2 remains accepted and reset-only. Do not promote the new
candidate, adopt a dead daemon's resources, or clear terminal QUIE to resume.

**2026-10-18 AcceleRAID optional flat planes:** `game/doom/play/accele160/build.py
--runtime-flat` reuses the shared F6 renderer and emits validated FLT1 frame
telemetry. The new browser shows confirmed mode and hides/rejects F6 without
the engine option. One cached low-detail binary starts textured; half-height
is off. Full ABBA card run: 512 frames, 128 paired PIO frames, three rearms,
full ownership/system/STOP audits and WAD/native/HTTP/tamper replay pass.
17.975 textured vs 22.129 flat card FPS (+23.109%); planes 13.81 vs 2.44 ms.
See `artifacts/current/accele160-flat-20261018`. Final post-reset read pair is
pending. The optional `i960-doom-flat` wrapper is prepared; ordinary launcher
unchanged. Preserve full audits and the four documented native differences.
