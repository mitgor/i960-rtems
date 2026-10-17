# Current findings — 2026-10-17

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
