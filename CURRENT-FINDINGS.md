## Accele160 P3c — active-DMA fault/NMI containment qualified

Both real `faulte` and host-doorbell NMI entered with DMA0 CSR=0x400. The
finite 64 MiB repeated-source chains completed after CPU containment, while
STOP left the firmware command `done=0 released=0` and ordinary DMA-buffer
module removal was refused. Stack/host guards, peer registers, owner table,
full payload, source/chain fingerprints and visible-page checks passed.
The initial host source check incorrectly duplicated odd aperture pages; its
failure and retained resources are archived alongside the correction.

Fresh paired firmware reads close both reset-recovery gates. The original
qualified profile-5 kernel is restored on boot
`b92db15d-de4d-4a57-9997-f6236dafa06a`, session `20261018T215108Z` under
`/home/mit/i960-owned-runtime-20261018`. It passed 64 frames, 5,045 WAD reads,
541 external console exchanges with zero errors, and three owned-state audits.
`~/rtems-console` works; the game is at verified idle and gateway 8088 is active.

[Evidence](artifacts/current/accele160-active-dma-exceptions-20261018/README.md)
and [design](rtems/accele160/fault/ACTIVE-DMA.md). Profiles 6/7 are isolated
experiments, not the default prompt. Physical stalled-DMA/abort behavior,
reclaim without reboot, SCSI/cache exclusion and task resumption remain open.
The bounded timeout/error policy has native simulated evidence only.
Earlier live-session references below are historical.

## Accele160 P3b — normal owned-exception runtime qualified

Profile 5 (owned fault/NMI handlers and ISP, no deliberate injection) passed
normal execution, two-game rearm and global STOP on the card. Six fresh
ownership captures verified the exact handlers, all 32 fault entries, ISP,
guards and zero IRQ faults. Timer ticks/task handoffs grew from 8/8 to
18,922/16,595. All 128 guarded frames, 64 paired PIO comparisons, 10,090 WAD
reads and 965 external console exchanges passed. Worst reply latency was
4938.153 ms, near the existing 5 s deadline; no tighter bound is claimed.

The first candidate's controller-task sampling timed out while Init was inside
Doom. That failure reached QUIE with retained resources and is preserved. The
accepted correction uses worker 0 as the sole runtime snapshot writer; Init
takes the final snapshot after worker/ISR drain. No deliberate fault is injected
by profile 5. The already qualified shutdown-safe admission module is preserved.

Fresh boot `b0732f10-debf-4bb3-8adc-e7e0bdc0fa91` and paired guarded firmware
reads close acceptance reset recovery. The same kernel is left live for
the prompt after a separate 64-frame restoration run with 525 successful
external exchanges. The existing streaming gateway is also restored. [Evidence](artifacts/current/accele160-owned-runtime-20261018/README.md)
and [implementation](rtems/accele160/fault/OWNED-RUNTIME.md).
Earlier mode-0 and pending-qualification entries below are historical.

## Accele160 P3b recovery complete — normal prompt restored

Fresh boot `aea81f51-24ce-493b-a7d2-114195611d5b` passed both guarded full
firmware reads, closing the real-NMI test's reset gate. Both hardware exception
tests now have verified recovery. The accepted mode-0 normal image ran one
64-frame Doom game, returned to audited idle, and completed 577 external console
exchanges without connection errors. `apps`, `stats`, and `mem` work through the
installed Linux shortcut. Service remains live in idle; **do not reset it merely
to close this task**.

Use `~/rtems-console` on Linux or `./rtems-console` from the Mac repository.
Session: `/home/mit/i960-fault-20261018/sessions/20261018T204122Z`.
This image is software-terminal-only: normal running with the new owned
fault/NMI vectors and ISP remains the next distinct qualification. This live
session has no global STOP receipt. [Evidence](artifacts/current/accele160-exceptions-20261018/README.md).
Earlier offline/reset notices below are historical.

## Accele160 P3b — real NMI also passed

Mode 4 passed on boot `5caaf490-19ac-4b1b-ab1c-c01cacc9c924`: actual host
PCI doorbell NMI, vector 248, raw record `2002,9002,f8,0`, NISR `100`, IISR `f`,
IDR `80000010`, IIMR `73`. Owned entries/ISP and guards passed; repeated records
and STOP left admission/pins retained. Independent archive replay passes.
The paired full guarded firmware reads close mode 3's reset recovery.

The final reset was requested. Mode 4 recovery and normal prompt restoration
are still pending. Restore the accepted mode-0 bundle from
`/home/mit/i960-fault-20261018/bundle`, not the exceptions bundle (still mode 4).
The console error fix is deployed to Linux `~/rtems-console`; the Mac shortcut
now uses it. Normal runtime with owned vectors/ISP remains a future qualification.
[Evidence](artifacts/current/accele160-exceptions-20261018/README.md).
Previous checkpoints below are historical.

## Accele160 P3b — real processor fault passed

Mode 3 passed on boot `b748d05a-16d1-40bf-b96d-973127ab6856`: the actual
`faulte` instruction reached the owned handler at tick 18. Raw fault record
`2002,9002,50001,c0716230` resolves to the exact compiled instruction. All 32
fault entries, cached NMI pointer, owned ISP and guards passed; the terminal
record stayed identical after STOP with admission and DMA pins retained.
Local archive replay verifies symbols, source/kernel hashes and both guarded
full firmware reads. Those reads close the previous normal runtime's reset
recovery. No actual NMI delivery or active-DMA fault containment is claimed.

The mode-4 NMI image is built and saved locally. Mode 3's own recovery and
mode 4's card test await the next fresh boot. The prompt is offline during
these isolated tests. [Evidence](artifacts/current/accele160-exceptions-20261018/README.md)
and [resume steps](rtems/accele160/fault/OWNED-EXCEPTIONS.md).
Older blocked/live-session entries below are historical.

## Accele160 P3b — owned exception candidate; hardware tests pending

Implemented opt-in owned fault/NMI entries, all 32 local fault-table entries,
a guarded architectural interrupt-entry stack, and separate real `faulte` and
host-doorbell NMI test modes. Native C/host tests pass, including all stock and
owned table bit corruptions, failed vector write, guards, and NMI alias checks.
This is not yet a hardware-qualified ownership profile.

The previous normal service shut down cleanly: raw QUIE/ACK, 128 drained frames,
pending admission and intact DMA guards are archived. The reset afterwards
left `192.168.2.75` refusing SSH. **Prompt offline; physical recovery required.**
The first mode-3 binary cross-built and is saved locally, but neither new test
ran on the card. Current source adds further checks and mode 4; rebuild it
before testing. No new firmware writes or RAM expansion occurred.

[Implementation and resume steps](rtems/accele160/fault/OWNED-EXCEPTIONS.md),
[evidence ledger](artifacts/current/accele160-exceptions-20261018/README.md).
The older P3a runtime status below is historical and superseded by this update.

## AcceleRAID P3a — recovery verified and prompt restored

[The opt-in terminal profile](rtems/accele160/fault/README.md) passed both
software-terminal tests: explicit fatal `7d001` with intact private stack
guards, and deliberate private guard corruption reporting `7d002`/bad guard.
Both parked at tick 18, rejected stale triggers, kept stable records after STOP,
and retained admission/DMA with unchanged DMA guards. Native tests and physical
archive replay pass. Mode 1's fresh-boot firmware pair is now closed.

Mode 2 boot: `03bd813b-ac1c-4925-9270-34e1f0a1fad8`. The live inventory
captures NMI `c00521b0`, ISP `c0001000`, and sixteen fault entries
`(c0053400,0)` followed by sixteen zeros. These remain stock-owned paths;
software containment does not qualify hardware fault/NMI or SCSI exclusion.

**Recovery and normal-runtime follow-up passed** on boot
`f999aba6-1276-470b-9130-1c589ed25d55`: both full guarded firmware reads match,
closing mode 2's reset gate. The mode-0 profile (terminal handling enabled,
deliberate injection disabled) ran two 64-frame Doom games with audited idle
and rearm. Console clients remained responsive across loading/rendering/restart.
The prompt is restored: `~/rtems-console` on Linux or `./rtems-console` from the
Mac repository. The isolated owner remains in verified idle with 128 frames. Replay verifies
10,090 WAD reads and 1,398 card replies; 1,397 external exchanges had no errors.
Median reply latency was 8.468 ms, worst 4.846 s, close to the unchanged 5 s
deadline; no hard response-time bound is claimed.
Its own global STOP/post-reset qualification remains separate; no such receipt
is claimed for this live mode-0 session.
[Exact evidence and current state](artifacts/current/accele160-fault-20261018/README.md).

## AcceleRAID RTEMS prompt — 2026-10-18

[Source and exact evidence](artifacts/current/accele160-service-20261018/README.md)
add an opt-in read-only command service (`help`, `version`, `uptime`, `tasks`,
`mem`, `apps`, `stats`) through the sole Linux owner. Two 64-frame Doom games,
rearm, three card protocol gates, all frame/WAD/ownership checks and global
STOP passed. Replay validates 172 replies, all 128 frames and 10,090 WAD reads.
The corrected host passed its physical follow-up through loading, 64 frames,
and audited idle: oversized input returns clean error/EOF, and abandoned/slow
clients do not stop the owner. Both post-reset guarded firmware reads match.
The isolated service is left running; use `./rtems-console` from this repository.
The kernel adds no task/IRQ/DMA owner or RAM grant. Response latency remains
workload-dependent; this is not an IRQ-gap or hard-real-time claim. See the
ledger for exact counts and latency, and the distinction between the closed
first run and the live follow-up session.

## Cached Doom presentation copy — 2026-10-18

[Two complete AcceleRAID runs](artifacts/current/wide-screen-copy-20261018/README.md)
qualified an opt-in exact 8-byte screen copy for the new-card exclusive Doom
build. On frames 12–31, presentation copy fell **6.5→3.0 ms** and card FPS
rose **16.964→17.593 (+3.70%)** in both 32-frame runs. All 64,768
pixel/palette bytes matched the cached baseline in every frame. Native
sanitizers and 40-frame play, full WAD/PIO/DMA/HTTP/ownership/STOP/stalled-host
audits, independent replay, and both runs' paired pre/post-reset 1 MiB stock
flash reads passed. The 10 ms stage clock and short fixed window limit timing
precision; this is not sustained interactive qualification. The candidate
remains opt-in as `game/doom/build.py --wide-screen-copy`. Doom's persistent
screen and two rotating DMA slots still require a copy; true zero-copy needs a
separate partial-redraw and pin-ownership design.


## Cached Doom clip-copy experiment — 2026-10-18

[The exact candidate and comparison](artifacts/current/clip-copy-20261018/README.md)
re-profile the accepted cached build at 48.0 ms renderer wall per frame:
27.5 ms BSP/walls, 14.5 ms planes and 6.0 ms masked drawing (frames 12–31).
The optional exact-count halfword replacement for two wall clipping copies
passed native sanitizers and deterministic play, and all 32 card frames matched
the cached baseline pixel/palette bytes. Full frame, native WAD, PIO, HTTP,
ownership, stalled-host and STOP checks passed. BSP/walls remained 27.5 ms
and card FPS remained **16.964** in the matched steady window. Keep the
candidate off by default; investigate texture/column locality and the
separately measured 6.5 ms presentation copy. Post-reset flash audit status
is recorded in the experiment README.


## CPU-to-SDRAM application-loop throughput — 2026-10-18

[The matched physical CPU-loop analysis](artifacts/current/cpu-sdram-20261018/README.md)
replays 120 old-card, 32 new-stock and 32 new-cached diagnostic frames with
identical admitted engine bytes and full original audits. On the new cached
map, a repeated 64 KiB read yields **7.08 MiB/s** of useful CPU loads, a
64 KiB word copy **7.02 MiB/s** useful copied bytes, and write-through clear
**36.36 MiB/s** stores. The stock map gives 7.02/7.02/38.10 MiB/s: bulk
working sets exceed the 4 KiB cache and hardly benefit from remapping. These
are timed RTEMS CPU loops with 10 ms clock resolution, not peak SDRAM bus
bandwidth or DMA throughput. Small hot reads and Doom rendering benefit from
the cache map; prioritize renderer locality over DMA bandwidth claims.

## Exclusive Doom cached baseline — 2026-10-18

The accepted private cache map is now the default in the new-card **exclusive
Doom** build; `DOOM_PRIVATE_CACHE_MAP=0` reproduces the stock-map control.
[The matched cached-card audit](artifacts/current/cache-baseline-20261018/README.md)
verifies 120 old PG and 32 new 160 whole-frame diagnostic records with the
identical admitted engine. The old card already caches its Doom allocation via
LMT0 over all 16 MiB (`dcctl4=0x7221`, 2 KiB). The new card caches its owned
upper 8 MiB via LMT1 (`dcctl4=0x8221`, 4 KiB). New/old medians are 5.38×
for warm 1 KiB reads and 1.74× for 64 KiB word copy. The accepted new-card
gameplay baseline is 16.964 card FPS over frames 12–31, low detail and card
FNV off. These are short bounded runs, not sustained interactive acceptance.

## N2 private-RAM cache mapping — 2026-10-18

The [bounded physical acceptance](artifacts/current/cache-map-20261018/README.md)
changed only the AcceleRAID 160's LMT1 from stock `c0400002/ffe00001`
to `c0800002/ff800001` while its reboot-owned upper 8 MiB arena was active.
The exact stock logical map was restored after Doom and DMA drained; DLMCON,
LMT0, control and WAD transport rules were unchanged. The originally opt-in
`DOOM_PRIVATE_CACHE_MAP=1` build checks incoming/readback registers and the
frame trailer proves the target mapping was live for all 32 frames.

With identical benchmark engine bytes, warm 1 KiB reads fell **360→130 ms
(2.77×)**, 4 KiB reads **490→255 ms (1.92×)**, while 64 KiB streaming reads
and word copies were essentially unchanged. In a second run using the exact
previously accepted no-benchmark low-detail engine with card FNV off, frames
12–31 delivered **16.964 card / 17.178 HTTP-observer FPS**, versus the
accepted stock-map **9.694 / 9.643**: **+75% card FPS** on that short fixed
window. Mean measured renderer time fell **91.5→48 ms**. This is a 32-frame
qualification, not long interactive play. Both runs passed full system,
ownership, frame/HTTP, native WAD, PIO, guard, stalled-host and STOP audits;
two complete guarded post-reset flash reads after each run matched the stock
SHA-256. Archived exact binaries and independent replayers pass. Keep the
full runtime checks in place while qualifying longer interactive STOP/disconnect.

## N1 cache scaling audit — 2026-10-17

The new card has D-cache globally enabled (`0x8221`, 4 KiB), but the stock
logical templates cache only `c0000000–c05fffff`. DLMCON is zero. The exclusive
upper 8 MiB Doom arena and RTEMS grant at `c0710000` fall outside those ranges,
so their data is uncached. This is a measured cache-map mismatch, not evidence
of a slower CPU clock. All 32 refined new-card records agree; no logical cache
register was written. Exact register values and source-path audit are in
[the N1 audit](artifacts/current/cache-scaling-20261017/AUDIT.md).

The opt-in `--cache-bench` engine preserves ownership and all system audits;
its extra workload makes diagnostic FPS unsuitable for gameplay comparison.
Identical engine bytes and eight bounded workloads ran four times per card.
Median new/old speedups were 5.35× for integer arithmetic, 1.94× for warm
1 KiB reads, 3.45× for 64 KiB reads, 1.74× for repeated 64 KiB word copies,
and 5.52× for clears. Adding 4,096 invalidations to the same 1 KiB read
loop cost the old card 235 ms but the new card only 5 ms (10 ms clock
resolution), consistent with the observed cache maps. These timings include
RTEMS scheduling and are neither cycle counts nor gameplay FPS. Both runs
passed exact workload results, guards, owner checks, full system/frame/WAD
audits and STOP. Native malformed-trailer and deterministic Doom tests pass.
The final new-card paired post-reset 1 MiB flash audit passed on boot `29dd7853-2614-40e9-8666-2b49b6764324`: both reads matched stock SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd` with zero residual and guard changes. The combined archive replay passed.
See [the N1 artifact index](artifacts/current/cache-scaling-20261017/README.md).
The next priority is a **bounded cache map for exclusively owned private RAM**,
keeping host-written control and DMA-input pages coherent. Do not globally
cache all memory, weaken validation or change SDRAM timing. Normal play defaults
and half-height-on-hold remain unchanged.

# Current findings — 2026-10-17

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

**AcceleRAID Doom startup and bounded browser gates accepted:**
The variable WAD startup stop was a same-owner timer interrupt reentering
RTEMS `_Thread_Dispatch` while its earlier ISR continuation was still active.
An exact trace caught the active flag `1` and the interrupted dispatch address;
the 1,401 preceding WAD requests matched the native oracle. The bounded ISR
now counts that reentry and returns without overwriting its owned save area.
Two unchanged full-audit runs each served 5,045 WAD requests, rendered 32 frames, passed
cleanup/STOP/old-card checks, and measured **3.660 card-side FPS** over 31
frame intervals. They counted 10 and 11 nested interrupts, with no
owner fault. Paired full pre/post flash reads passed for both runs. A separate
two-slot browser gate delivered 32 byte-identical HTTP frames and acknowledged
W press/release at 2.320 card-side FPS, also with full pre/post audits. Long
interactive ownership and Doom DMA delivery remain open.
[Trace, exact build and replay](artifacts/current/accele160-doom-startup-20261017/README.md).

**Old/new delay comparison measured:** New-card profiling passed 32 frames
with unchanged baseline pixels/palette and 2.331 card-side / 2.315 HTTP-observer
FPS. Per frame, the adapter spends 51.94 ms copying, 78.39 ms staging odd
pages and 24.19 ms hashing; combined engine work between callbacks is 274.52
ms. Host PCI reads cost 9.28 ms and Python FNV 19.58 ms, giving 29.38 ms
observed-to-HTTP latency. A fresh old-card optimized **low-detail** DMA run
passed 120 frames/47 paired audits at 6.35–6.40 steady FPS and 5.18 ms
observed-to-HTTP latency. Including its scripted level reload gives 5.462
FPS. New is high detail with older engine routines, so this compares current
software paths, not CPU performance. Exact native host FNV measured 0.0874
ms in an isolated microbenchmark; integrate it first for latency, then port
word copies and owned DMA/direct presentation. Both runs replay and final
new-card paired stock-flash reads pass. [Full table, limits and estimates](artifacts/current/card-delay-comparison-20261017/README.md).

**First real Doom frame on the AcceleRAID 160:** A third retained RTEMS run
served all 5,043 engine WAD reads in the exact native request order and
captured a real 320×200 Doom frame plus palette through 16 checked readback
pages. The engine returned at its owned first-frame boundary, released all
loans, preserved its executable text hash, passed arena/owner/old-card and
STOP quiescence checks. Startup to frame took 123.54 seconds; this is a
one-frame milestone, not browser play or an FPS measurement. [Exact
capture](artifacts/current/accele160-doom-first-frame-20261017/README.md).
Post-reset acceptance passed on new boot `c9773c0f-9b64-414b-8712-4d9e6bf1ae5e`: idle descriptor, old card unbound, and two guarded full 1 MiB reads matched unchanged stock firmware. Next: make successive frames and input/host delivery work on the new card, then benchmark play.

**Earlier AcceleRAID 160 first-entry stalls:** The
[new-card first-frame attempts](artifacts/current/accele160-doom-first-frame-20261017/README.md)
connect the owned Doom runtime to the accepted full-WAD service. A corrected
run served 1,401 requests before startup stopped making progress. A second,
instrumented run crossed that point and served 3,801 requests in about
95 seconds; every recorded offset/length matched the native trace. The last
reply had matching sequence, length, status and FNV, but no next request or
frame appeared for 120 seconds. The host published STOP; the engine did not
reach a cooperative checkpoint, so the grant and callback remain reset-only.
Those were failed first-frame attempts. The first run's post-reset
paired 1 MiB guarded READIMAGE audits matched unchanged firmware and the old
card stayed unbound; the second run's post-reset paired audit also passed. The third run crossed both stalls and captured a frame; the first two still document intermittent startup pauses.

**AcceleRAID 160 full-WAD service physically passed; actual Doom entry is next:**
[Exact source and acceptance capture](artifacts/current/accele160-doom-wad-service-20261017/README.md)
show 42 card-requested, host-backed reads spanning the pinned 28,795,076-byte
Freedoom WAD: 38 accepted, bad FNV/stale sequence/five-second timeout/STOP
refused, and every non-STOP 4 KiB cache image read back and matched. The
867,792-byte Doom image admission and diagnostic framebuffer also passed.
Earlier Doom allocations persisted across reset, so the new reversible
pre-claim saves and restores each of 2,048 page preimages instead of
requiring a particular pattern; lower-bank, code, DMA and guard audits
passed. STOP held the firmware callback until reset. On a new boot, the
stock descriptor and PIATVR were normal, the old card remained unbound,
and two complete guarded flash reads matched unchanged firmware. **No Doom
entry was called or real gameplay frame rendered on this new card.** Next:
wire this WAD service into the admitted Doom runtime ABI and execute a
bounded first-frame call in an owned RTEMS task.
Before production use, handle the rare post-copy cache checksum failure by
restoring or quarantining the cache; the tested pre-copy refusal paths are
unchanged-cache proofs.

**AcceleRAID 160 Doom bridge physically passed; Doom execution is next:**
[Exact code, build and capture](artifacts/current/accele160-doom-bridge-20261017/README.md)
show guarded 900,000-byte image, 6 MiB zone and 64 KiB frame allocations in
the exclusive upper bank. The card admitted and relocated the exact
867,792-byte Doom image after 212 sequenced upload chunks, rejected premature
admission, rejected a changed Freedoom WAD header, accepted the exact header,
and served a 65,536-byte deterministic diagnostic frame in 16 checked pages.
All 2,048 bank pages passed the reversible pre-claim audit; guards, retained
ownership and STOP at tick 7,380 passed. The old card stayed unbound. The
first pages of upper RAM had changed on fresh boot while 1,022 odd pages
retained the old pattern; the new preflight preserves those stock-touched
pages and requires the remaining pages to match exactly. This is **not** a
Doom frame or Doom entry execution. After reset, new boot
`994bfdd8-8664-4516-86a8-36d6555d6a78` had an idle descriptor, default
PIATVR and old card unbound; two guarded complete flash reads matched the
unchanged firmware. Next build
the new-card Doom runtime ABI and a full-WAD service, then invoke a bounded
engine entry and validate its first real frame.

**AcceleRAID 160 8 MiB upper bank and reboot-only prototype (2026-10-17):** [Exact physical evidence](artifacts/current/accele160-fullbank-20261017/README.md) now supersedes the earlier read-only rejection. A card-side full word census found only two populated 4 KiB pages (`c0ffa000`, `c0ffe000`, 53 nonzero words) in `c0800000..c0ffffff`; all 1,024 odd pages were zero. After saving those two pages into an owned grant, two returning STOP/timeout tests simultaneously marked all 2,048 pages, checked lower-bank alias guards, filled/read/restored every word of each page, and restored stock state. Four guarded complete post-test flash reads matched the firmware. A separate image then claimed all 8 MiB and kept operation 13 pending: the host checked every odd page byte for byte, observed timer heartbeat 6→262, and sent STOP. RTEMS entered quiescence while the command remained pending, establishing the intended reboot-only lifetime. **Post-reset acceptance passed after a fresh power cycle:** new boot ID `a11703ca-57d6-4fc9-bc69-ed0581332d78`, no retained module, default PIATVR, idle descriptor, old card unbound, and two guarded complete flash reads matching the exact firmware. Doom itself has not run on this board. [Implementation boundary](rtems/accele160/ARENA.md).


**Finite timer-driven exclusive borrowing accepted (2026-10-17):** The [combined RAM-only RTEMS image and live capture](artifacts/current/accele160-exclusive-timer-20261017/README.md) held distinct four-word patterns on upper page `c0f01000` and stock expanded-runtime page `c0011000` while two CPU-bound RTEMS workers were preempted by owned timer 1. The host observed the complete held pages through further ticks. STOP completed at 10 ticks/165.129 ms; no-host expiry at 120 ticks/1,267.623 ms. Both drained ISR continuations and restored complete pages, timer/vector/mask, firmware SP, owner/page/stage, with all three DMA channels idle before/after and four matching complete guarded flash reads. Offline replay and four tamper rejections passed. This remains a **returning callback**, not a persistent reboot-only RTEMS takeover or an 8 MiB arena claim. [Exact contract and remaining gates](rtems/accele160/EXCLUSIVE-MODE.md).

**AcceleRAID exclusive RAM borrowing passed, persistent takeover remains open (2026-10-17):** Two RAM-only operation-13 images ran on the new card with the stock CPU command path paused at priority 31 and CCR/NDAR/BCR idle on all three DMA channels. The first changed and restored four words on zero upper-bank page `c0f01000`; the second repeated that test and changed/restored four words on nonzero stock expanded-runtime page `c0011000`. For both STOP and no-host timeout, card-side full-page FNV and independent host 4 KiB before/after snapshots matched. Loader, staging, all 512 allocator records, owned stacks and firmware SP restored; two complete guarded flash reads before and after each batch matched the current firmware. [Upper-page capture](artifacts/current/accele160-exclusive-probe-20261017/README.md), [occupied-page capture](artifacts/current/accele160-occupied-probe-20261017/README.md), and [exclusive-mode contract](rtems/accele160/EXCLUSIVE-MODE.md) contain exact binaries, sources and limits. Stock firmware resumes after these callbacks. This is **not** a persistent 8 MiB claim, full alias test, or Doom admission.

**AcceleRAID Doom arena admission rejected safely (2026-10-17):** The [read-only live survey and replay](artifacts/current/accele160-doom-arena-20261017/README.md) found thirteen stable zero upper-bank pages, but the stock allocator's largest free run is 1,540,096 bytes and its ownership table ends at `c07fffff`. The exact firmware has aligned literals addressing the proposed `c0800000..c0ffffff` bank. No ownership or alias proof exists, so no upper-bank write or Doom upload ran. PIATVR and the idle descriptor restored; two guarded complete firmware reads matched stock. An exclusive stock/DMA handoff and small saved/restored alias test must precede an 8 MiB pattern test.

**External-resume DMA gate accepted for a bounded finite transfer (2026-10-17):** The [exact capture and replay](artifacts/current/accele160-dma-external-resume-20261017/README.md) show owner SIGKILL at `DMA_HELD`, independent RESUME at tick 101 after STOP at tick 21, terminal tick 300/reason 1, denied early pin release, and complete payload/guard, DMA, owner/page/stage, RTEMS/context and cleanup audits. Two full stock-flash reads before and two after matched SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`. The old PG remained unbound. Earlier driver non-binding was my missing mandatory `read_bdf=0000:37:09.1` module parameter; exact insertion bound immediately. This does not prove safe release behind a never-draining PCI transaction.

**Pre-STOP DMA host-process death/recovery gate accepted:** The [new RAM-only test](rtems/accele160/dma_pre_stop_death/README.md) killed the starter immediately after the card published `DMA_BUSY`, before any STOP. Two separate recovery processes found the original PIDs absent, retained the pinned buffers and stock RAM grants, saw `EBUSY` on early pin release, and waited for normal chain completion and tick-300 lease expiry. Exact 26,624,000-byte payloads, guards, inactive DMA channels, owner/page/stage, RTEMS stacks and timer/vector restoration passed before release. Six full flash reads matched stock; [archived evidence](artifacts/current/accele160-dma-pre-stop-death-20261017/README.md) replays and rejects 16 tampered captures. This covers death after a durable `DMA_BUSY` checkpoint and **normal finite completion**; it does not establish hardware CSR activity at the instant of death, pre-checkpoint recovery, whole-host crash recovery or safe freeing behind a never-draining PCI transaction. Retain resources on uncertainty.

**DMA host-process death/recovery gate accepted:** The [new test](rtems/accele160/dma_process_death/README.md)
used the unchanged finite-chain image and deliberately killed the host owner
after `DMA_HELD`. Two independent recovery processes found their original
PIDs absent while the DMA pin and stock RAM grant remained owned. Premature
pin release returned `EBUSY`. The card resumed at tick 101 and completed at
tick 128; only then did recovery pass the exact payload/guards, inactive
channel, owner/page/stage, RTEMS stacks, timer/vector and stock-channel
audits and release resources. Six pre/mid/post full-flash reads matched
stock. [Exact evidence](artifacts/current/accele160-dma-process-death-20261017/README.md)
replays and rejects fifteen altered captures. This covers a dead host
process **after a saved held checkpoint and normal finite completion**.
A real PCI fault that never drains, death before that checkpoint and a
whole-host crash remain unproved; do not free on uncertainty.

**Host-timeout retention gate accepted:** The [long-hold DMA test](rtems/accele160/dma_timeout/README.md)
passed twice with an unchanged image. The card suspended active DMA at tick
21, held channel 0 until tick 101, then completed the finite chain at tick
128. While the channel was held, the host crossed a 150 ms wait deadline,
and an attempted early pin release returned `EBUSY`; the pinned buffer,
guards and stock RAM grant remained owned. Exact payload, channel state,
owner/page/stage, RTEMS stacks and timer/vector audits passed before real
release. Four full flash reads matched stock; independent replay rejects
sixteen tamper cases. [Exact artifacts](artifacts/current/accele160-dma-timeout-20261017/README.md)
are archived. This proves timeout **retention followed by normal drain**,
not recovery of an actual PCI error or a killed host process.

**Active DMA suspend/resume gate accepted:** The [new card test](rtems/accele160/dma_suspend/README.md)
paused channel 0 after STOP arrived with CSR active at tick 21, held it
with CCR disabled for four 10 ms ticks, observed stable settled DAR/NDAR/BCR,
then resumed and completed all 13,000 descriptors at tick 52. Two
unchanged-image runs with fresh pinned host buffers passed exact payload,
both guards, channel inactivity, stock channel-1, allocator, staging,
loader-page, RTEMS stack, timer and firmware-continuation checks before
release. Four guarded full-flash reads matched the stock SHA-256. Offline
replay and twelve tamper cases pass; [exact evidence](artifacts/current/accele160-dma-suspend-20261017/README.md)
is archived. This proves a **controlled pause and resume of finite DMA**,
not cancellation or safe release of a genuinely stalled/erroring channel.
The host must still retain the pin and grant on uncertainty.

**DMA STOP timing gate accepted:** The [finite-chain test](rtems/accele160/dma_chain_stop/README.md)
now passes twice on the new card with an unchanged image. Each run copied
26,624,000 bytes through 13,000 descriptors to a fresh pinned host buffer.
The card observed STOP at tick 21 while CSR indicated active DMA, then let
the chain finish normally at tick 48 before the host checked exact payload,
both guards, inactive CCR/CSR, final DAR, zero NDAR/BCR, owner records,
worker/ISR stacks and timer/vector restoration and released both sides.
Six guarded full 1 MiB flash reads in three pairs matched unchanged firmware;
independent replay and ten tamper cases pass. The host runner and card image
are archived with the [exact evidence](artifacts/current/accele160-dma-chain-stop-20261017/README.md).
This proves safe STOP deferral for a **normally completing finite chain**.
Cancellation/drain of hardware that is actually stalled or erroring and
process-death recovery remain unproved. An initial 3.3 MiB chain completed
before STOP, a first longer run was rejected by an incorrect prior DCR word,
and a second longer run missed the PCI-written STOP until D-cache
invalidation was added to the DMA poll loop. Those negative captures are
preserved separately and are not counted as accepted runs.

**Correction to the DMA inventory below:** The Intel 80303 DMA registers
are at i960 local `0x00001400..0x000014ff`, not `0xff001400..0xff0014ff`.
The first all-zero samples came from the wrong, reserved address range and
cannot establish DMA channel state. A first transfer using that address
never fetched its descriptor; the host retained its pinned buffer and card
grant, then requested a recovery reboot. The exact failed capture is kept.

The [corrected inventory](rtems/accele160/dma_inventory_corrected/README.md)
then passed two HALT/expiry batches and six full flash reads at the true
`0x00001400` block. Channel 0 and 2 were idle in the sampled words;
channel 1 held a stock descriptor and was left untouched. The following
[bounded channel-0 transfer](rtems/accele160/dma_transfer/README.md) passed
three times with fresh pinned host buffers: initial HALT, reuse HALT, and
reuse no-host expiry. Each delivered exactly 256 bytes in two card-side
polls, left 4 KiB guards and the unused payload unchanged, and reached
inactive CCR/CSR with BCR/NDAR zero before release. Eight full flash reads
in four pairs and all owner/page/stage, worker and timer/vector audits passed.
This is a small completed-transfer proof. Cancellation/drain of a genuinely
stalled DMA transaction, sustained throughput and persistent service are
still unproven.

The [first DMA-address experiment](rtems/accele160/dma_inventory/README.md)
passed two finite RTEMS HALT/expiry batches and six guarded full flash reads.
Its register values are invalid as DMA evidence because of the address error
above. The RTEMS lease and ownership evidence still replay, and the old card
stayed unbound. No DMA channel can be selected from those samples.

The [AcceleRAID 160 STOP-ignoring worker gate](rtems/accele160/contain/README.md)
now passes twice. Two CPU-bound workers never read STOP or yield; the
higher-priority RTEMS controller lets them advance for four more hardware
ticks after the host request, then suspends both and verifies stable progress,
original live ISR frames and stack checksums across 10,000 checks. STOP
finished after 14 ticks in about 259 ms; the no-host lease expired after 124
ticks in about 1.36 s. Four full flash reads and independent post-run stock
inventories passed. This is bounded whole-instance containment while timer
interrupts and scheduling work, **not** a callback-free resident runtime or
hardware recovery from permanently masked interrupts.

The [new-card bounded RTEMS preemption gate](rtems/accele160/preempt/README.md)
now passes twice. Two CPU-bound workers are time-sliced from the owned timer-1
ISR with separate task-owned ISR continuations: STOP completed after 8 ticks
and 8 handoffs in about 145 ms; the no-host deadline completed at 120 ticks
and 120 handoffs in about 1.258 s. Both continuations drained before stock
state restoration. Six complete matching flash reads and independent post-run
inventories passed. This proves bounded preemption while interrupts remain
enabled; a finite resident service and containment of interrupt-masking code
remain separate gates. The earlier hardware-clock result below is its baseline.

The [AcceleRAID 160 combined RTEMS/timer gate](rtems/accele160/autoclock/README.md)
now passes twice: hardware tick 5 wakes the worker, 52 ticks continue through
a bounded CPU loop, and STOP/no-host cleanup restores the borrowed timer,
vector, mapping, mask and firmware context. Six full flash reads and three
independent stock-state inventories passed. This accepts bounded hardware
clocking, while unrestricted preemption and a resident service on the new
card remain future work. The accepted DAC960PG runtime below is separate.

## AcceleRAID 160 timer/STOP gate — 2026-10-17

The latest [RAM-only timer acceptance](artifacts/current/accele160-timer-20261017/README.md)
temporarily borrowed timer 1 and cached vector 18, leaving stock-owned
vector F2 untouched. Two fixed eight-interrupt paths and two stale/valid
STOP paths passed; the longer run acknowledged STOP after 201 interrupts.
Ticks 5→201 gave a host-observed 1,253.04 interrupts/s with reload 10,000.
The ISR used an owned C stack (`c0711100` observed), the entry used a separate
owned stack (`c0712fc0`), and firmware SP returned to `c0002100`. The exact
stock vector, mask, map, timer registers, loader page, staging source and
512 allocator records restored. Independent inventories before and after
each active batch and four guarded full flash reads matched. The image
rebuilt byte-for-byte; offline replay rejected four mutations. **This is a
bounded bare ISR proof, not an RTEMS hardware clock.** The next gate is to
deliver timer ticks into bounded RTEMS and prove worker wakeup, STOP, drain
and restoration. The earlier software-tick result below is historical.

## AcceleRAID RTEMS task gate — 2026-10-17

The new AcceleRAID 160 now runs a newly linked RTEMS 4.6.6 task image from a
stock-owned 512 KiB grant. Two 15-page uploads passed per-page copy checks,
whole-image digest, wrong-hash/count rejection, normal RTEMS return, complete
loader/staging/allocator restoration, and four guarded full post-boot flash
reads. A worker woke at synchronous software tick five of ten. This is **not**
a hardware timer, interrupt-driven scheduler, independent STOP, network server
or Doom port. Firmware SHA-256 `68451b38b96609fa3a95eb9497fe85a34ac92fec45b912c53612969b1209a988`;
[payload, runner and full evidence](artifacts/current/accele160-rtems-20261017/README.md).
The 2026-10-16 statement below that no block was granted is historical and
superseded by the intervening retained-grant and upload gates.

## AcceleRAID bounded RAM execution — 2026-10-16

The exact 1 MiB firmware image, SHA-256 `1f13799b…6c4aaf`, adds a strict
zero-DMA operation 2 for one pinned 80-byte payload. The flash command finished
with status 0 and zero residual. After physical power cycle, two independent
guarded full-flash reads matched the exact candidate; valid PING returned 0 and
one-byte-bad PING returned stock unsupported status 2. **Two bounded RAM calls
then executed and returned normally on the new card**, each reporting the exact
four result words `444f4e45,16102671,000001f0,80114670`. Both full 4 KiB
loader-page preimages matched the saved image, the only changed bytes in the
post-call capture were the 16-byte result and 80-byte code slots, and each run
restored the whole page and PIATVR. An independent read-only final 4 KiB page
capture after the repeat also matched the original. A further guarded full-flash read after the
first call still matched the candidate. Command modules released/unloaded;
`myrsread` remains bound to new card `37:09.1`, old PG `37:04.1` stayed unbound.

A separate read-only DRAM survey found stable zero 4 KiB samples at local
`c0501000`, `c0801000`, `c0c01000` and `c0f01000`; the runtime sample at
`c0011000` was stable nonzero. **These samples do not grant RAM ownership.**
Subsequent static tracing and paired live table reads identified the stock
32 KiB block allocator at `c0066430`: its count/owner arrays are at
`c03852a0`/`c03856a0`. The two snapshots were identical. They show 38 free
contiguous lower-pool blocks (1,245,184 bytes) and 47 free contiguous
upper-pool blocks (1,540,096 bytes), while other blocks are stock-reserved or
allocated. This is a concrete stock allocator route for a minimal RTEMS
reservation, but **no block has yet been granted to our code**. The largest
free run is far short of Doom's 8 MiB arena; reclaiming or using the upper
physical 8 MiB needs a separate ownership proof.
The flashed helper accepts only the exact 80-byte probe, so it is not yet an
RTEMS loader. General chunked upload, an owned code/data/stack arena, timer and
interrupt adaptation, web transport and Doom remain new-board work.
[Exact candidate and live evidence](artifacts/current/accele160-ramprobe-20261016/README.md);
[memory-map limits](docs/hardware/accele160-memory-map.md).

## AcceleRAID programmed late-PING helper — 2026-10-16

The user accepted skipping proven recovery because an external programmer is
available. The exact audited 1 MiB late-PING candidate was staged with zero
residual and unchanged DMA guards, then independently read back in full. A
one-byte-mutated readback was rejected by preflight. One `FLASHIMAGE` command
completed in 37.2 s with status 0. After a physical power cycle, the new card
initialized, and **two independent guarded full-flash reads** matched the
candidate byte for byte (SHA-256 `e708c1da…e2b23d3d0`). The valid zero-DMA
PING returned status 0; one changed signature byte returned stock unsupported
status 2. The old PG remained unbound and untouched. This proves a bounded
patched handler running after boot, not a general code upload/call route or
boot-block recovery. The temporary `myrs` blacklist was removed; `myrsread`
remains bound to the new card in this boot.
[Exact image, command evidence and replay](artifacts/current/accele160-flash-candidate-20261016/README.md).

## AcceleRAID stock recovery route — 2026-10-16

An exact-flash offline audit found the boot block's one-byte serial `S`
recovery trigger, its distinct `!` manufacturing route, and the 20 KiB
ROM-to-RAM recovery handler copy. The flash-control bit-1 alternative is not
a safe SSH switch: the same register is written by the erase/program routine.
The similar live UART probe previously selected disabled callbacks, so this
board's physical serial recovery remains unproved. Both cards remain unbound;
no card command or flash write was made. The late PING patch remains offline
until a physical recovery entry and bounded stock restore are demonstrated.
[Exact anchors and acceptance procedure](artifacts/current/accele160-recovery-audit-20261016/README.md).

## AcceleRAID live stock table — 2026-10-16

A guarded new-card-only PIATVR read mapped local `c0023000` and captured the
stock dispatch page. **All 4096 bytes match** the accepted stock runtime;
`0x8e` points to `c002371c` and `0x8f` to `c0023790`. PIATVR was restored to
`c0000000`, default BAR pages before/after were identical, both cards stayed
unbound and SSH stayed healthy. Main-entry direct-store inspection found no
absolute reference to the `0x8f` word, but computed writes or broad copies
remain possible. This stock observation does **not** prove the unflashed late
hook survives main initialization. No firmware was programmed or executed.
[Snapshot, guard script and offline replay](artifacts/current/accele160-table-snapshot-20261016/README.md).

## AcceleRAID late-loader PING placement — 2026-10-16

The normal copied-loader path expands the runtime, calls stock setup, then
finishes a descriptor pass at common return `c000c9cc`. A revised 4-byte
branch at that return installs the strict PING handler **after** the loader's
initialization. Its 144-byte handler and an in-memory image pass exact-code,
runtime-identity, changed-byte and known checksum audits: 155 changed flash
bytes, nine helper and eleven startup tests. Intel's i960 Jx manual says the
boot handoff's `dcctl 1` enables D-cache; it does not invalidate the table
write. Main-entry computed writes and live persistence are still unproved.
The untouched boot block has a recovery dispatcher, but no practical recovery
entry or stock restore has been tested on this board. **No image was exported,
flashed or run**; both cards remain unbound. The prior early-hook candidate is
superseded for future offline work.
[Exact route, binaries, receipt and recovery boundary](artifacts/current/accele160-late-ping-20261016/README.md).

## AcceleRAID bounded PING candidate — 2026-10-16

Stock Linux GEM writes all 64 mailbox bytes; the stock firmware copies four
16-byte quads into the command object before IOCTL dispatch. Static completion
tracing supports a status-0, residual-0 zero-DMA response. A strict 148-byte
i960 PING handler is assembled in the copied-loader cave: accepted envelopes
reach stock completion; every mismatch reaches stock unsupported. An in-memory
candidate changes 157 flash bytes, preserves the compressed/runtime image and
passes both known additive checksums. Six helper and eleven startup tests pass.
**No candidate image was exported, programmed or run on the card**; nonce
echo/authentication, hook timing, boot and recovery are unproved. The old card
was untouched. [Exact source, ABI trace and receipt](artifacts/current/accele160-ping-handler-20261016/README.md).

## AcceleRAID offline `0x8f` routing rehearsal — 2026-10-16

A 28-byte loader-cave hook and four-byte loader callsite change can be
assembled without unresolved relocations. Offline validation against the exact
stock flash shows 37 changed bytes, unchanged compressed/decompressed runtime,
and passing known loader/trailer checksums. The hook would call stock setup,
change only the expanded `0x8f` table word, and route all requests straight to
stock unsupported. It is deliberately **fallback-only**, not an active PING or
flash-qualified firmware. No card command or firmware write was made in this
batch; both cards remain unbound. Next: prove the internal request-byte mapping
and completion response, implement a strict bounded handler, then decide a
recovery/rollback path before live flashing.
[Exact source, disassembly, receipt and limits](artifacts/current/accele160-dispatch-rehearsal-20261016/README.md).

## AcceleRAID stock helper transport — 2026-10-16

A first-boot, new-card-only `myrs8f` derivative submitted one zero-DMA stock
IOCTL `0x8f` request. It completed in 50.3 ms of host observation with
host-visible status `2`, zero residual and the exact 64-byte mailbox; the old
card remained unbound. This establishes an unsupported completion and safe
command cleanup, **not** helper execution. A native strict version-1 PING
admission model passes sanitizer and mutation tests. It has not been installed
on firmware, and reserved-byte transport, cache-safe execution, boot and
recovery remain unproven. The temporary module and `myrs` boot override were
removed after the test; both cards are currently unbound, and SSH is healthy.
[Protocol, capture and replay](artifacts/current/accele160-ping-contract-20261016/README.md).

## AcceleRAID helper-site audit — 2026-10-16

The stock IOCTL dispatcher maps unused diagnostic subcommand `0x8f` to its
unsupported completion (`0x104`), while normal `0x8e` reaches `SET_MEM_MBOX`.
The loader has 7,720 erased bytes copied to local RAM, with no aligned absolute
references in the verified loader/runtime. An in-memory, **dormant** 80-byte
probe insertion plus known additive checksum updates passes structural checks;
the compressed runtime and old card are unchanged. This neither wires a new
command nor proves boot, code-site ownership, or recovery. The subsequent
stock `0x8f` transport test and native admission model are recorded above;
the next gate is an offline helper/dispatcher patch and structural verification.
[Exact anchors and limits](artifacts/current/accele160-helper-site-20261016/README.md).

## AcceleRAID debug interface — 2026-10-16

The stock loader tests a UART register and selects real callbacks only when
its readback is `1`. A read-only live table snapshot shows the disabled branch:
input is a fixed `q`, output is a no-op. The debug menu's `e` key invalidates
D-cache, but no host-controlled input path to it is active; its Code Manager
`u` option offers memory diagnostics rather than a cache-safe returning call.
The earlier audit mislabeled `e` as `d`; its jump-table index was right only
because two offset errors cancelled. No live probe was attempted and custom
code has not run on the new card. The next useful milestone is a bounded,
recoverable firmware helper design with explicit RAM and cache ownership.
[Exact anchors and evidence](artifacts/current/accele160-debug-interface-20261016/README.md).

## AcceleRAID cache gate audit — 2026-10-16

The accepted stock runtime has D-cache invalidation in its interactive debug
menu and several transfer/memory-test paths, but no verified host-command route
that also invalidates I-cache before a normal-return call. Its identified
`sysctl 0x300` is a processor reinitialize operation. Host-written software
interrupt pending bits would not reliably update the 80303's internal pending
priority, and vectors may be cached. No new controller command or code execution
was attempted. [Static audit and next gate](artifacts/current/accele160-cache-gate-20261016/README.md).

## AcceleRAID RAM upload route — 2026-10-16

Intel 80303 ATU decoding proves BAR0's upper 4 KiB is a movable local-RAM
aperture. A guarded 256-byte live round trip at local `0xc0001e00` uploaded the
80-byte bounded probe, passed exact readback, restored every original byte, and
left identical full-page SHA-256 snapshots. PIATVR returned to `0xc0000000`, SSH
remained healthy, and old DAC960PG `37:04.1` remained unbound and untouched.

Execution was deliberately withheld. The apparent IOCTL `0x8e` hook is backed
by cacheable callback and dispatcher memory; the 80303 does not snoop host writes.
A stale read could run stock `SET_MEM_MBOX`, so the required cache-safe call and
normal-return contract is not established. MEMCOPY is a SCSI transfer, and
StoreImage/ReadImage do not provide a persistent local allocation. Next prove a
stock cache-maintenance gate or a fully decoded unused software-interrupt route.
[Full result and next gate](artifacts/current/accele160-ram-route-20261016/README.md).

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
`0000:37:09.1` reports firmware 6.00-05, 100 MHz, 16 MiB RAM, 8 MiB cache
and 1 MiB flash. The failed EZAssist allocation's pinned companion was cleared
by the intervening reboot; successful raw readers were released. As of the
stock `0x8f` test above, both cards are unbound, SSH is healthy, the temporary
`myrs` override is removed and initramfs updated; existing `myrb` rules are
preserved. No RTEMS/Doom session is active. New-card code execution and
firmware compatibility are not yet established; explicit BDF selection remains
mandatory. Half-height work stays on hold.

[Evidence, reproduction and next steps](artifacts/current/accele160-guarded-20261016/README.md).

This is the current state, not a chronological experiment log. Follow
[reproduction](docs/reproduce.md), [subprojects](subprojects/README.md), and
[artifact retention/restoration](artifacts/README.md). The narrative remains in
[STORY.md](STORY.md); dated conclusions remain in [milestone notes](artifacts/notes/).

## Working

| Component | Accepted result |
| --- | --- |
| Firmware | Complete 512 KiB in-system stock dump; Fujitsu 4.07-0-29 main firmware matches. Patched firmware programmed, paired full readbacks and boot validation passed. |
| Loader | Upload and execute i960 code after host startup; returning firmware-callback route preserved for Tetris and future research. |
| RTEMS | Exclusive resident runtime, owned interrupt stack/context, shared heap and bounded STOP/drain. 12 MiB owned RAM profile supplies an 8 MiB Doom arena and 6 MiB zone. |
| Games | SSH Tetris, browser raycaster, and playable browser Doom. Doom uses card-initiated two-buffer DMA, WAD request/completion rings, bulk transfers and ownership checks. |
| Network/web | RTEMS IPv4/IPv6 through host relay; autonomous web profile is a separate deployment from exclusive Doom. One hardware owner at a time. |
| Validation | Full paired system audits, pinned DMA ownership, STOP/stalled-host checks and native/capture comparisons remain required. |

The accepted programmed image SHA256 is
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
See [programmed firmware](docs/firmware/FIRMWARE-PROGRAMMED.md) before any firmware work.

## Doom defaults and performance

- **Half-height option tested:** `--runtime-half-height` adds F7/browser switching,
  independent of F6 flat planes, full height initially. 920-frame matched card run:
  normal **6.362 FPS**, half **6.404 (+0.67%)**, flat **7.723**, both **7.111**.
  Half + flat is **7.92% slower than flat alone**. Keep half height off by default;
  no useful FPS gain established. Plane work falls, but columns/expansion absorb
  the savings. Full audits and STOP/stall/drain pass.
  [Evidence](artifacts/current/half-height-20261016/README.md).

- **New optional quality control:** `--runtime-flat` enables F6/browser switching
  between textured and solid-color floors/ceilings in one build, textured initially.
  Same-session low-detail ABBA windows measured **6.454 → 7.877 FPS (+22.05%)**;
  plane rendering **40.96 → 13.46 ms**. 520 frames, 56 full paired audits,
  STOP/stall/drain and replays passed. This is a bounded ping-pong scene benchmark,
  not a general interactive FPS guarantee. [Results](artifacts/current/flat-planes-20261016/README.md).


- Exact fast FixedDiv is enabled by default in playable builds; `--no-fast-fixed-div`
  retains the old path. Specialized C columns (`--fast-columns`) and fast renderer
  (`--fast-render`) remain opt-in. Benchmark flags are not all deployment defaults.
- `--runtime-detail` provides the high/low-detail switch. Quality reductions must
  remain explicit options with normal rendering available in the same build.
- `--span-four --fast-render`, `--fast-point-side` and `--fast-walls` are experimental
  options. Four-span has no established performance benefit. Wall profiling is
  diagnostic, disabled by default; its overhead affects comparisons.
- Recent fixed-low-detail measurements are approximately **6.4–6.8 FPS** in the
  tested scene/configuration, not a guarantee across levels. The earlier exact four-span comparison
  averages **6.6172 baseline vs 6.4493 four-span FPS**, with unexplained baseline
  repeat variance. [Final measurements](artifacts/current/doom/README.md).
- Keep validated latency improvements even when total FPS is unchanged. Delivery
  to HTTP availability does not measure browser paint or input-to-photon latency.

## Unresolved or not demonstrated

- Physical recovery remains **untested**. A spare card is not evidence of recovery.
- Four known native-reference pixel differences remain (positions 29260, 29261,
  29580, 29581); accepted card variants agree with one another.
- The faster repeat of the identical two-span baseline remains unexplained. Do not
  discard it or claim a four-span speedup from only the first pair.
- Preserve the compiler comparison/point-side workaround unless a replacement has
  independent target proof. Exact optional helpers are not blanket permission to
  optimize all legacy i960 code at higher compiler settings.
- Direct Mylex-to-NIC networking, 10 FPS across scenes, and 20–30 ms complete-frame
  latency are not established. The working network path goes through host RAM.
- A previous reboot sometimes needed a physical power cycle. No claim is made that
  this cleanup fixed hardware shutdown/recovery behavior.

## Next useful hypotheses

1. Broaden flat-plane quality testing across maps and high detail; keep it optional.
2. **On hold by user request:** specialize half-height column loops and time/unroll row expansion. The tested
   switch works, but adding it to flat planes currently reduces FPS by 7.92%.
3. Use longer matched runs and resolve baseline variance before promoting further
   exact renderer optimizations. See [Doom backlog](game/doom/BACKLOG.md).

Full old runs and intermediate binaries are recoverable at Git `a8af272`.
Their dated statements of “next” or “not yet working” do not override this status.

## New-card callback-free handoff — 2026-10-17

The AcceleRAID 160 now has an [accepted RAM-only finite timer handoff](rtems/accele160/handoff/README.md).
Operation 13 returned in about 10.6 ms, then a host ENTER token was serviced
in a stock-firmware interrupt frame. The no-host path expired at exactly 300
timer-1 ticks in 3.048 s; valid HALT ended after four ticks in 88.5 ms while
a wrong token stayed pending. Processor priority, firmware SP, timer/vector/
map/mask, loader page, stage and all 512 owner records restored. Four same-boot
full flash reads and independent pre/post inventories passed; [evidence](artifacts/current/accele160-handoff-20261017/README.md)
replays offline and rejects four tamper cases. This is a bare monitor, not
resident RTEMS or an interrupt-independent watchdog. The next new-card gate
is an RTEMS control task under this finite lease, followed by explicit RAM/
DMA ownership and quiescence for network and Doom services.

## New-card Doom FPS gate — 2026-10-17

The AcceleRAID 160 has now passed two unchanged-image 32-frame RTEMS runs.
Each served 5,045 WAD requests, including the complete 5,043-request native
startup prefix, rendered all 32 frames, passed ownership/STOP/full-bank
audits, and measured 847 card ticks over 31 presentation intervals at 100 Hz:
**3.660 card-side FPS**. Pixels and palette match byte-for-byte across runs.
The fault behind variable startup stalls was same-owner timer ISR reentry
while the previous ISR continuation was still active in RTEMS dispatch; the
bounded nested path counts and returns without replacing that context. It
counted 10 and 11 reentries in the two runs, with no owner fault. The two
full guarded flash reads before and after each run matched stock firmware.
No browser delivery or input has
yet been tested on this card. The preserved `myrsread` driver requires
`read_bdf=0000:37:09.1` on each boot. [Code and status](rtems/accele160/doom_first_frame/README.md) ·
[Exact replayable evidence](artifacts/current/accele160-doom-startup-20261017/README.md).

## New-card two-slot Doom frame transport — 2026-10-17

The first live-slot build failed full-frame FNV because PIATVR only exposes
the odd 4 KiB page in each 8 KiB pair. The corrected RAM-only build stages
each 64 KiB frame in 16 owned odd pages, keeps two generation-numbered slots,
and requires a verified host read before exact-generation ACK. A 32-frame
physical run passed 5,045 WAD reads and the native startup oracle, all 32
payload checks, owner/bank/arena/STOP/quiescence audits, and two full stock
firmware reads both before and after the run. The old card remained unbound.
Card presentation averaged **2.329 FPS** across 31 intervals, including
staging and ACK; the prior render-only gate was **3.660 FPS**. This is not
browser FPS or DMA. The optional HTTP/binary-frame/key/STOP server passes
host tests. A separate physical browser gate captured all 32 HTTP generations
and compared them byte-for-byte with card receipts; a W press/release reached
the card with sequence and ACK both two. It passed WAD, owner, bank, cleanup
and STOP checks at **2.320 card-side FPS**. Paired pre-run and post-reset full
flash reads passed with zero residual/guard changes and matching stock SHA.
`verify_browser.py` replays the evidence. This accepts the bounded browser
transport and input gate; it is not a long playable session yet.
[Code](rtems/accele160/doom_play/README.md) ·
[Evidence and replay](artifacts/current/accele160-doom-live-20261017/README.md).
## New-card renderer profile and compiler check — 2026-10-18

The accepted cached/wide-copy Doom build remains the faster tested default
at **17.593 card FPS** in the fixed frames-12–31 window. The old DAC960PG
wall-region timer helper produced wrapped AcceleRAID values even though the
first 32-frame DMA/browser/WAD/ownership/STOP and full flash audits passed.
Strict replay now rejects advertised malformed wall timing. The corrected
opt-in new-card clock had zero faults in a second full card run and measured
30.53 ms BSP/walls: 1.77 ms traversal, 5.36 ms other subsector work, 7.33 ms
wall setup and 16.06 ms inner wall loop including column calls. An
unprofiled selective `r_segs.c -O2` run matched all 32 reference pixel and
palette blocks but remained **17.593 FPS**, so `--fast-walls` stays opt-in.
This narrows the next exact-output experiment to generated column/texture
access and cache layout; merely switching the pinned compiler target has no
evidenced benefit. Complete run and remaining post-reset audit status are in
[the experiment](artifacts/current/renderer-tune-20261018/README.md).
