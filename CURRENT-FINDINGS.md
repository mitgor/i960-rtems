# Current findings — 2026-10-16

## AcceleRAID helper-site audit — 2026-10-16

The stock IOCTL dispatcher maps unused diagnostic subcommand `0x8f` to its
unsupported completion (`0x104`), while normal `0x8e` reaches `SET_MEM_MBOX`.
The loader has 7,720 erased bytes copied to local RAM, with no aligned absolute
references in the verified loader/runtime. An in-memory, **dormant** 80-byte
probe insertion plus known additive checksum updates passes structural checks;
the compressed runtime and old card are unchanged. This neither wires a new
command nor proves boot, code-site ownership, or recovery. Next: decode the
`0x8f` command/completion ABI and implement a native admission model before
considering a live patch.
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
`0000:37:09.1` is bound to `myrsread`, firmware 6.00-05; firmware reports
100 MHz, 16 MiB RAM, 8 MiB cache and 1 MiB flash. SSH is healthy. The failed
EZAssist allocation and its pinned companion remain deliberately retained until
reboot; do not force unload/unbind them. Successful raw readers were released.
Temporary myrs blacklist was removed and initramfs updated; existing myrb rules
were preserved. No RTEMS/Doom session is active. New-card code execution and
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
