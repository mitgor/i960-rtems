# AcceleRAID 160 renderer/compiler experiment

The accepted cached, low-detail Doom build with wide screen copy is the
unprofiled reference: **17.593 card FPS** over frames 12–31 in each of two
32-frame runs. It retains the exact pinned DoomGeneric source, private cache
map, optimized C columns/spans/FixedDiv, two owned DMA slots and the full
browser, WAD, ownership, stall, STOP and guarded whole-flash audits. See
[`wide-screen-copy-20261018`](../wide-screen-copy-20261018/README.md).

The first run in this directory added the older `--wall-profile` diagnostic.
All 32 card frames, 32 binary HTTP captures, the native 5,043-request WAD
prefix, DMA ownership, held-host test, STOP and both pre/post whole-flash
pairs passed. Its wall trailer is **invalid**: that helper treats timer 0 as
a continuously decreasing 4.1667 MHz counter, but it wraps on this new card.
Some cumulative regions consequently underflow to values near `2^32`.
`profile-bad-clock.tar.xz` is kept as the exact diagnostic capture, not as
performance evidence. [The previous general replay](bad-clock-base-replay.json)
confirms all non-timing gates and both post-reset stock-flash pairs; strict
replay now decodes an advertised wall trailer and rejects this capture. The
ordinary unprofiled baseline still replays.

The corrected opt-in `--wall-profile-accele160` combines the owned timer-1
count with RTEMS's 100 Hz clock, checking for a tick crossing and pending
timer interrupt. It reports in the existing WAL1 scale and marks fallback or
nonmonotonic samples as faults, which independent replay rejects. A second
32-frame run also selected `--fast-walls`, compiling only `r_segs.c` at `-O2`
instead of `-Os`. The 40-frame native deterministic input/STOP/heap-drain
test passed. Card pixels and palette matched the reference exactly for all
32 generations; the WAD oracle, complete paired PIO/DMA guards, browser
payloads, held-host test, ownership and STOP checks passed. The corrected
WAL1 record decoded on every frame with **zero clock faults**. The paired
pre-run stock-flash reads matched SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

| Corrected-profile steady frames 12–31 | Mean elapsed time |
| --- | ---: |
| Whole renderer | 51.0 ms |
| BSP root including wall work | 30.53 ms |
| Traversal/culling outside subsectors | 1.77 ms |
| Other subsector work | 5.36 ms |
| Wall setup outside inner loop | 7.33 ms |
| Inner wall loop including column calls | 16.06 ms |
| Planes | 14.0 ms |
| Masked stage | 6.5 ms |

These are elapsed intervals that include interrupt/preemption time, not
processor cycles. The profiled candidate measured **16.964 card FPS** over
frames 12–31. Its timer probes add work; comparing that number directly with
the unprofiled 17.593 FPS baseline would misstate the compiler effect. The
corrected-profile run's two post-reset whole-flash reads matched stock.

An otherwise identical **unprofiled `--fast-walls` build** passed native
determinism/STOP, admission and a third 32-frame card/HTTP run. All 32
pixel/palette blocks match the accepted unprofiled reference byte-for-byte.
Its WAD oracle, four full paired PIO/DMA captures, remaining DMA guards,
generation/source/epoch checks, 32 browser payloads, held-host test,
ownership, full pre-reset flash audits, cleanup and STOP passed. The fixed
steady window measured **17.593 FPS**, exactly the accepted reference's
17.593 FPS; frame-profile renderer means were both 49 ms. The result does
not support enabling `--fast-walls` by default on the AcceleRAID. The
unprofiled run's two guarded whole-flash reads on fresh boot
`bdcfd659-9239-45e9-8c05-60a46388831e` also matched stock, with zero
command status/residual/guard changes. The [complete replay](fast-walls-plain-replay.json)
passes 32 frames, 18 tamper rejections, the WAD oracle, ownership/STOP and all
pre/post-reset audits. The old DAC960PG remained unbound throughout; no flash
write was issued.

The corrected partition makes the next target more specific: the inner wall
loop and its column calls average 16.06 ms, while wall setup averages 7.33 ms.
The already accepted C column kernel is active. A next experiment should
inspect the generated i960 column loop and try one bounded scheduling/layout
change there, with exact pixels and an unprofiled card A/B check. A blanket
target-flag switch has no evidence of benefit here; the pinned GCC 3.3.6
supports `-mrp` but not an i960RM `-mrm` switch.

Reproduce offline from the repository root:

```sh
python3 game/doom/wall_profile/test.py
python3 artifacts/current/accele160-doom-dma-20261017/verify.py \
  --archive artifacts/current/renderer-tune-20261018/fast-walls.tar.xz
python3 artifacts/current/renderer-tune-20261018/compare.py \
  artifacts/current/wide-screen-copy-20261018/repeat.tar.xz \
  artifacts/current/renderer-tune-20261018/fast-walls.tar.xz
python3 artifacts/current/renderer-tune-20261018/compare.py \
  artifacts/current/wide-screen-copy-20261018/repeat.tar.xz \
  artifacts/current/renderer-tune-20261018/fast-walls-plain.tar.xz
python3 artifacts/current/accele160-doom-dma-20261017/verify.py \
  --archive artifacts/current/renderer-tune-20261018/fast-walls-plain.tar.xz
```

The second command includes all 32 exact pixel/palette and HTTP payload
checks, native WAD request oracle, DMA marker/guard/source/epoch validation,
18 deliberate tamper rejections, ownership/STOP checks, and corrected wall
trailer decoding. The comparison command uses the same fixed 12–31 window
and rejects any pixel or palette change before reporting timing.

The exact complete archives are `profile-bad-clock.tar.xz` (SHA-256
`ba021c4424c78622c2a5adc3dad8665f6cec1477cc01ab9021dcefadc3c3d5c9`),
`fast-walls.tar.xz` (`ff8f09b6682cb1d72d65dd13f2913ffce0144a8631796d49f32dabd4d85ac5b4`)
and `fast-walls-plain.tar.xz`
(`137271248e3f3d3c6a4b7a922df433a32171f7a37a5b5e19974866a7ce29e705`).
Each includes the 1 MiB stock-flash read pairs before and after its run;
the final two include exact build/admission manifests, native oracle, browser
packets, candidate source and full card captures.
