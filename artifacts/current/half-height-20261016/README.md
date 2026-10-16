# Half-height rendering — 2026-10-16

One engine, independently switchable full/half height and textured/flat planes.
Implementation and limitations: [half height](../../../game/doom/half_height/README.md).

## Predeclared comparison

920 frames, low horizontal detail, fast FixedDiv, C columns, two-sample spans,
direct presentation without FNV, WAD ring/profile, peer-yield and priority
ping-pong release. Full paired audit interval stays 3 seconds. Level reload at
60/62/64/66 precedes measurement. Half-height F7 events: 12,24,220,420,620,820.
Flat F6 events: 20,32,320,720. Each event is down/up through the input FIFO.

Steady windows are 161–218, 261–318, 361–418, 461–518, 561–618, 661–718,
761–818, 861–918: normal / half / both / flat / flat / both / half / normal.
`measure.py` checks modes before pooling interval counts and elapsed time.
This controls run order within one scene/session, not cross-level performance.
Browser delivery is the existing 320×200 binary format; no transport bytes are
saved. FPS and HTTP availability are not input-to-paint latency measurements.

## Reproduction

Remote isolated workspace: `/home/mit/i960-half-20261016`.
`build.sh build`, `run.sh acceptance`, `verify.sh acceptance build` record the
exact dependency-seeded build and bounded acceptance. Generic fresh build:

```sh
python3 game/doom/play/build.py --work NEW_DIRECTORY \
  --runtime-half-height --runtime-flat --pipeline --pingpong --wad-ring \
  --wad-profile --peer-yield --low-detail --no-fnv --direct-frame \
  --fast-render --fast-columns
```

A normal interactive deployment omits the bounded ping-pong and WAD profiling
options. Enable `--runtime-detail` too for independent F5 horizontal quality.
Do not run a ping-pong admission as an ordinary interactive image.

The originally planned windows began at 141 + 100k. An additional native input
probe finished around frame 145, so all eight windows were shortened symmetrically
to start at 161 + 100k before calculating any FPS. This excludes host CPU work
from every reported window; full captures retain the excluded frames.

## Measured result

| Mode | FPS | Renderer | Planes | BSP/walls | Sprites + row expansion |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full height, textured | 6.3616 | 138.448 ms | 43.879 ms | 77.500 ms | 17.069 ms |
| Half height, textured | 6.4042 | 136.379 ms | 26.121 ms | 85.172 ms | 25.086 ms |
| Full height, flat | 7.7235 | 109.741 ms | 13.276 ms | 78.621 ms | 17.845 ms |
| Half height, flat | 7.1115 | 121.207 ms | 10.172 ms | 84.483 ms | 26.552 ms |

Half height alone is **+0.67%**, too small to call a useful FPS improvement from
this session. Half + flat is **7.92% slower than flat alone**. Both quality
reductions beat full-height textured by 11.79%, but flat alone wins by 21.41%.
Normal repeats are 6.36167/6.36151 FPS; half repeats 6.38263/6.42596;
flat repeats 7.74436/7.70269; both repeats 7.08064/7.14255.

The plane stage saves 17.76 ms in textured mode, but BSP/wall drawing grows about
7.67 ms and sprites/expansion about 8.02 ms. The new generic column loop and row
expansion are plausible targets, not yet separately timed explanations. Shading
half the rows does not halve geometry work, and the 64 KiB delivery is unchanged.
Do not enable half height by default or recommend it over flat-only for speed.
Next experiment: specialize the half-column inner loops and measure expansion
separately; then consider a true compact-height viewport if the budget warrants it.

HTTP availability after host observation averages 4.52 / 4.65 / 5.20 / 4.79 ms
(normal / half / flat / both). There is no established transfer-latency gain.
CPU sampling is 10 ms; stage averages pool 116 frames per quality combination.

## Validation details

Native normal output matches the previous accepted baseline for 52 frames.
The actual native engine repeats all 52 captured mode combinations exactly;
card differences remain the known four pixels. In full-height mode their indices
are 29260,29261,29580,29581; alternate-row sampling moves them to
29580,29581,29900,29901, exactly as predicted. Palette and remaining pixels match.
The inherited discrepancy is not silently excused as a new generic tolerance.

An extra native test initially missed F5 when F5/F6 were scheduled on the same
frame: `I_GetEvent` breaks after a key-up, and the test only offered events on an
exact frame number. Pending native events now remain eligible until consumed.
The combined F5/F6/F7 test passes all 40 frames, movement, repeat, STOP and heap
cleanup; this changes the test harness, not the card input or renderer ABI.

920 frames and **67 full paired audits** pass, including both held slots unchanged
through a 3.010-second host stall and held-slot STOP. Maximum IRQ gap is
**10.521 ms**. 32,566 heap allocations were freed. System/frame/WAD replays pass
on both Linux and the Mac. Mutation suites reject 24 frame corruptions and four
drain corruptions. All **849** observed HTTP payloads match the archived card
captures exactly. Normal-mode screenshots and all four quality images are saved.

`accepted-inputs.tar.gz` contains the admitted engine, kernel, transport and build
metadata; `acceptance-card.tar.gz` contains the full paired evidence. Dependencies
and WAD retain their existing pinned paths. Source hashes name the current code;
`test_all_switches.sh` reproduces the extra native test. Do not add duplicate
build trees or obsolete failed native binaries to Git.

The admitted image uses **875,068 bytes** of the existing 900,000-byte
admission limit; no arena, firmware or DMA ownership change was needed.

## Service handoff

After the clean card STOP/drain and local archive hash checks, the host was
rebooted to release the retained exclusive module. SSH had not returned at the
end of this work; a physical power cycle was requested. Public IPv6 HTTP has
**not yet been restored**. Once Linux returns, verify no other owner/bound module,
run the archived `restore.sh`, and test the global IPv6 HTTP URL from the Mac
(the host's own global-address request does not traverse ingress DNAT).
See `restoration.json`. Do not report a live playable session on port 8087.
