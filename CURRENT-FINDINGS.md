# Current findings — 2026-10-16

This is the current state, not a chronological experiment log. Follow
[reproduction](docs/reproduce.md), [subprojects](subprojects/README.md), and
[artifact retention/restoration](artifacts/README.md). The narrative remains in
[STORY.md](STORY.md); dated conclusions remain in [milestone notes](artifacts/notes/).

## Current hardware handoff

The half-height test passed and evidence is saved in Git. Cleanup reboot completed;
the public RTEMS IPv6 web relay is restored and verified from the Mac (HTTP 200).
It currently owns `0000:37:09.1` through `dac960auto`; no Doom session is running.
[Exact handoff](artifacts/current/half-height-20261016/README.md#service-handoff).

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
2. Specialize half-height column loops and time/unroll row expansion. The tested
   switch works, but adding it to flat planes currently reduces FPS by 7.92%.
3. Use longer matched runs and resolve baseline variance before promoting further
   exact renderer optimizations. See [Doom backlog](game/doom/BACKLOG.md).

Full old runs and intermediate binaries are recoverable at Git `a8af272`.
Their dated statements of “next” or “not yet working” do not override this status.
