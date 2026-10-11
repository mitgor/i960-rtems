# Games on the Mylex: CHIP-8, framebuffer, raycaster, Doom

Updated 2026-10-11. This application track follows the working Tetris and RTEMS
milestones. It does not supersede the interrupt/ownership work in the parallel
**Review loader improvements (2)** chat or its production-service decisions.

## Browser delivery and host audit cost

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

The journal is implemented and passes host benchmarks and offline replay.
Next: fresh physical browser/lifecycle acceptance and measured delivery; retain
the rewrite default until then. See [journal evidence](artifacts/journal-20261011/README.md).
Keep all paired reads, native-frame comparisons and audit snapshots. The larger
Doom framebuffer/heap contract and asynchronous ownership remain separate work.

## Slot checks: fifteen-step measured follow-up

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
The browser integration follow-up is accepted above.

## Combined ACK-and-PUBLISH: fewer fully audited transactions

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

## Frame queue prototype: measured, still fully audited

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

## Decision: use DoomGeneric; borrow measured ideas from FastDoom

Chosen base: [ozkl/doomgeneric](https://github.com/ozkl/doomgeneric), inspected at
`e257a09527062bfb986b6e5e0780839b6cbd5b71`.
Comparison: [viti95/FastDoom](https://github.com/viti95/FastDoom), inspected at
`9a7b435a9b95db1ba38f89f1139050d748d32fde`. These are research pins, not vendored
or completed i960 ports.

DoomGeneric exposes platform hooks for initialization, display, time, sleep and
keys, plus a callable `doomgeneric_Tick`. Its
[header](https://github.com/ozkl/doomgeneric/blob/e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric/doomgeneric.h)
has an 8-bit `CMAP256` pixel option. Start the port at 320×200 indexed color,
with palette conversion/scaling on the host, and sound disabled. The default
640×400×32-bit output alone occupies 1,024,000 bytes; a 320×200 indexed image
occupies 64,000 bytes. Existing engine buffers and the output buffer can still
be separate allocations. Selecting a smaller output buffer is not sufficient
to reduce the engine's internal rendering resolution.

FastDoom explicitly targets DOS 386/486 PCs; its
[build requirements and features](https://github.com/viti95/FastDoom/blob/9a7b435a9b95db1ba38f89f1139050d748d32fde/README.md)
include OpenWatcom, NASM and DOS extender tooling. Porting that platform layer
would consume effort before benefiting the i960. Its flat floors/ceilings, flat
sky, reduced horizontal detail and distance culling remain useful ideas to
benchmark after the portable baseline runs. Do not assume published x86 speedups
carry over to i960, or copy x86/VGA assembly into this port.

DoomGeneric still needs significant port work: allocator, WAD reads/seeks,
formatting/string routines, time/input hooks, compiler helpers and a defined
fatal/exit path. Audit floating-point and 64-bit dependencies rather than
assuming that a fixed-point renderer makes every source file freestanding.
`doomgeneric_Tick` is an integration entry, not a proven worst-case execution
bound; startup and resource loads also require cancellation/yield analysis.

The pinned
[zone allocator platform code](https://github.com/ozkl/doomgeneric/blob/e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric/i_system.c)
sets both default and fallback minimum to 6 MiB, with a command-line override.
This is the selected source's allocation policy, not a universal minimum for
all possible Doom ports. Its actual peak working set must be measured. Physical
16 MiB on the card does **not** establish ownership of that memory.

## Checked against the parallel OS backlog

Read the parallel chat's latest eight turns and the current findings on
2026-10-11. Its `persistirq` batch progressed while this application was being
built: the new report records five normal sessions/120 callbacks, 29 clean
rollback/handoffs, 46 quarantine follow epochs and an intentional six-callback
retained close. The evidence remains owned by that parallel work; this milestone
did not rerun it. Its [remaining work](rtems/persistirq/README.md#remaining-work)
is host-side admission/rejection, broader reference/dependency tracking,
persistent-session teardown faults, and a firmware resource reservation before
leaving interrupts armed between callbacks. Production remains `autonet`.

This work is primarily lifecycle correctness, not yet a measured libc or graphics
speedup. The application track must respect these dependencies:

| OS / loader backlog | Game requirement and integration gate |
| --- | --- |
| Persistent async contexts, restart generations, quarantine, resource dependency closure | Later supervise a game task and shared frame/WAD resources. Start with bounded callbacks; do not bypass retained-resource decisions. |
| M1 shared memory profile and G06/G12 stack/heap limits | Record code, BSS, workspace and stack bounds per game; use the proven RIO1 layout for CHIP-8. |
| M2 rebalancing; M3 genuinely owned larger RAM | Required before a multi-megabyte Doom heap. Rebalancing 512 KiB alone cannot supply it. No speculative writes to unused-looking RAM. |
| R1 diagnostics and backpressure | Measure interpreter/render time, full host callback latency, copy volume, queue high-water marks and drops separately. |
| R2 libc and compiler helpers | Add the subset Doom actually calls, allocator failure handling and read-only WAD access; current byte-loop helpers are not full newlib/POSIX. |
| G07 verification cost | Keep paired checks, guards, the 32-step full audit and final restoration. Optimize transport only with an explicit ownership/validation contract. |
| Host-RAM DMA networking and eventual direct-peer research | Potential later transport improvement. Direct NIC DMA is not a prerequisite for the first game. Software leases do not prove DMA completion. |

Sources in this repository: [integrated plan](DEVELOPMENT-PLAN.md),
[current findings](CURRENT-FINDINGS.md), [preemption/DMA plan](RTEMS-PREEMPTION-DMA-PLAN.md),
[ownership](rtems/ownership/README.md), [async ownership](rtems/ownirq/README.md).
Historical gap entries in the integrated plan can lag newer hardware findings.

## Progression and acceptance gates

1. **CHIP-8 core and RTEMS adapter — implemented and card-tested.**
   [Source and instructions](game/chip8/README.md),
   [preserved target and tests](artifacts/chip8-20261011/README.md).
   Fixed 4 KiB guest RAM, no dynamic allocation, at most 1,000 instructions per
   request, deterministic keys/timers, 256-byte monochrome framebuffer. Separate
   RTEMS worker with persistent guest state and semaphore request/reply. Card
   testing followed completion of the parallel OS batch and normal web-service
   cleanup; no concurrent PCI ownership.
2. **Browser framebuffer — native and card paths validated.**
   Shared C8G1 protocol and a serialized host bridge, with explicit native/card
   labeling, keyboard state and restart. Reset + 300 scripted card updates and
   404 browser callbacks all matched native replay (705 total), with 21 periodic full-allocation
   audits and two complete RAM restorations/unloads. Browser arrow movement and
   restart passed over SSH. Median callback latency was 51.43/51.65 ms; maximum
   below 75 ms in both sessions. Production IPv6 HTTP returned 200 afterward.
   Broader ROM conformance and a longer interactive soak remain follow-ups.

3. **Bounded fixed-point raycaster — implemented and card-tested.**
   80×60 indexed output, 1..80 columns per call, a fixed map and bounded grid
   traversal. All 548 scripted/browser replies matched native replay, including
   partial rendering, movement/reset and runtime-helper benchmarks. Both sessions
   restored RAM and unloaded; production IPv6 HTTP returned 200. The browser
   delivered 10.18 responses/s during a short run. Full-frame kernel time was
   60.38 ms median; upload+arming accounted for about 32.8 ms and render/publication
   added about 7.54 ms over a snapshot. [Measured findings and artifacts](artifacts/raycaster-20261011/README.md).

4. **Runtime/performance preparation for Doom.** Benchmark aligned and unaligned
   memcpy/memset/memmove, overlap handling, framebuffer clears, fixed-point multiply/
   divide and allocator behavior on actual i960 memory. Compare with independent
   native references and retain guard checks. Count scheduler transitions and
   unnecessary copies before changing OS routines. Larger RAM reservation and
   an application/transport memory manifest remain required independent work.
5. **DoomGeneric platform port and first timedemo.** Pin sources/licenses; compile
   and record missing symbols; implement platform and read-only WAD service.
   Budget zone heap, other allocations, code, stacks, palettes and frame buffers.
   Establish recoverable task/transport shutdown, then headless demo first,
   display second, interactive controls third. Record frame hashes and latency.
   Use an explicitly supplied WAD or suitable freely distributable game data.
6. **Optimize the measured bottleneck.** Borrow FastDoom's portable rendering
   reductions one at a time, with the same timedemo and documented visual tradeoff.
   Avoid promised FPS before hardware measurements. Audio and network multiplayer
   follow a stable single-player renderer.

The current 8 KiB RIO response can carry a CHIP-8 frame easily. A 64,000-byte
Doom indexed frame needs at least eight such chunks even before scheduling and
copy overhead. At 20 frames/s the image payload alone is 1.28 MB/s. The older
Tetris 41.1 ms median session-call measurement is a warning about command/audit
latency, **not** a measured Doom throughput prediction. Also, a logical 304-byte
CHIP-8 reply does not shrink the driver's fixed buffers or paired staging reads.

Word-copy/clear is now implemented and card-validated in the isolated raycaster
build: 3.30× copy, 4.63× clear, and a 3.91% full-frame kernel-time reduction across
repeated byte/word sessions. All 2,105 replies matched native output, with full
restoration. [Evidence](artifacts/word-memory-20261011/README.md).

Upload/arming profiling and exact validation acceleration are also accepted:
43,904 measured commands, unchanged paired read volume, and 3.61% lower full-frame
kernel time (57.83 → 55.74 ms). Readback/audit fell 13.15%. The three upload
completion waits at that milestone consumed about 32 ms. [Evidence](artifacts/transfer-20261011/README.md).

The next investigation found an upload-only blocking UART diagnostic. Temporarily
suppressing one format byte, with pinned preimages, paired checks and full
restoration, reduces upload waits 32.129 → 0.368 ms and full-frame kernel time
55.840 → 24.141 ms. The final matrix passes 2,105 replies; ten repeated startup
sessions cover the corrected cache ordering. [Evidence](artifacts/upload-20261011/README.md).

Callback/readback profiling is now complete. Exact word request scans and
renderer loops reduce callback 11.925 → 7.360 ms and kernel time 24.169 → 19.471 ms
(19.44%). Eight sessions pass 3,368 identical replies and full restoration.
The 20 us polling experiment saves 0.269 ms audit time but costs 17.19% more host
CPU; the recommended 50 us coarse release measures 19.352 ms kernel time.
[Evidence](artifacts/callback-20261011/README.md).

The originally proposed next action, now completed above, was a generation-checked frame queue with
explicit ownership, stale-frame rejection, cancellation and an equivalent
immutable-memory audit contract. Read completion waits still cost about 9.46 ms,
with 942,272 bytes read per ordinary frame. Keep current paired coverage until a
replacement is proven; do not silently reduce it to improve the timing. Align
that design with the parallel internal-controller/ownership findings. Faster
callbacks do not establish physical DMA drain or reserve Doom's larger heap.
