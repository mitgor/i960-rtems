# Remaining screen-copy optimization — 2026-10-15

Physical 100-frame test passed. Baseline is the accepted WAD-copy candidate in
`../wad-copy-20261015/card.tar.gz` (`live-copy`), with identical low-detail,
no-FNV, direct-frame, profiling, WAD-ring and ping-pong settings.

Only private engine presentation changes: a fixed 320×200 indexed, scale-one
copy replaces 200 row `memcpy` calls. Four aligned words per loop iteration;
unaligned pointers retain byte copying and other geometry retains the original
row/scaling path. The persistent Doom screen is not eliminated: cached row
pointers, incremental updates and zone ownership must remain separate from
rotating DMA-pinned delivery slots. No DMA, scheduler, audit or ownership changes.

`build.sh` rebuilds native/i960 engines, platform, admission, kernel and module
using the accepted WAD-copy build dependencies. `native-frames.py` repeats the
52-frame native oracle. `run.sh` runs the bounded 100-frame full-audit loading/
restart/held-buffer STOP test, only after the actual card owner releases it.
`verify-remote.sh` runs full replay and 33 tamper cases. Do not force-unload
retained DMA mappings. `replay.sh` takes an extracted candidate/capture directory
and pinned WAD; `compare.py` takes baseline/candidate capture paths and `--native`.

## Controlled measurements

| Metric | Prior WAD-copy build | Screen-copy build |
| --- | ---: | ---: |
| Delivered FPS, frames 21–50 (29 intervals) | 3.815406 | 4.517024 |
| Mean frame interval over those intervals | 262.10 ms | 221.38 ms |
| Screen-copy wall time, frames 21–50 | 44.00 ms | 12.00 ms |
| Screen-copy sampled task CPU | 22.00 ms | 6.00 ms |
| Renderer wall time | 208.67 ms | 209.33 ms |
| Renderer sampled task CPU | 104.33 ms | 104.67 ms |
| First frame, upload excluded | 117.566 s | 116.923 s |
| Engine upload, separate | 80.250 s | 79.615 s |
| Same-level restart, frames 66–68 | 2.890 s | 2.780 s |
| Full audit pairs | 68 | 67 |

**FPS improves 18.39%; the screen-copy bracket falls 72.73%.** This is one
matched candidate against the preceding accepted baseline, not repeated A/B/B/A
or a long gameplay benchmark. All intervals are retained. Small loading-time
changes are not claimed as a WAD optimization; the request counts are identical:
1,755 before first frame, 1,805 total and 38 during restart. The requested full
paired audit cadence is unchanged at 3 seconds; shorter execution explains the
one fewer pair. Renderer CPU work is essentially unchanged.

Card timing resolves 10 ms and includes scheduling/preemption; sampled task CPU
is not a cycle counter. Frame 21's previous-publication field carries the deliberate
held-buffer stall (2,580/2,740 ms). It is preserved, not silently trimmed. The
separate frames 22–50 previous-wait means are 0/0.69 ms. FPS starts at observation
of frame 21 and therefore does not include that earlier stall. Mean HTTP fetch
is 28.86 ms; 98 observed frame payloads match captures exactly. HTTP receipt is
not browser paint or input-to-photon latency.

## Why the copy stays

The linked Newlib `memcpy` uses `ldob`/`stob` for every byte (see
`newlib-memcpy-disassembly.txt`). This was repeated 200 times per frame. The new
helper uses four `ld`/`st` word pairs per iteration (`screen-disassembly.txt`),
without requiring 16-byte alignment. It is selected only for the exact geometry
and format supported by the specialization. No libc-wide behavior is changed.

`I_VideoBuffer` remains Doom-owned persistent storage: `r_draw.c` caches `ylookup`
pointers into it, HUD/menu/display updates can be incremental, and shutdown frees
it through the zone allocator. Delivery slots have different lifetimes and rotate
only after the existing exact-ACK ownership gate. Aliasing the persistent screen
to a rotating or in-flight slot is not safe as a local edit. Thus the copy is
optimized rather than removed. Palette/trailers, mark 96/97/98 timing boundaries,
DMA pinning, full guards and STOP are unchanged. At the measured 221 ms interval,
eliminating the remaining 12 ms alone would have only about 6% theoretical FPS
headroom under an unchanged schedule; renderer work is the next larger target.

## Validation and artifacts

- 100 physical frames, 67 full audit pairs, four complete DMA/mailbox comparisons.
- Three-second two-slot stall/resume; frames 99/100 held across owned STOP;
  final global heap drain and 146 protected pages pass.
- First 52 controlled card frames have identical pixels/palettes to the baseline,
  with exactly the same four native differences at 29260, 29261, 29580 and 29581.
- Two native 52-frame runs repeat exactly and match the previous native pixels/
  palettes. The ordinary native input/STOP test also passes.
- ASan/UBSan: 64 exact-edge 64,000-byte copies, all pointer alignments, source
  preservation and destination-prefix guards. Build transport/ping-pong checks pass.

`candidate.tar.gz` contains exact runtime sources, binaries and build results;
`card.tar.gz` contains closed captures and native oracle. Adjacent SHA-256 files
verify both archives. `source-check.json` matches 793 runtime/build source files.
`comparison.json` records complete timings; the replay scripts preserve all
system/frame/WAD/profile checks and 24 frame + three WAD + six profile mutations.

Kernel: `82c7f571861c6c3fc2b34b8a6c1c2211483abd6df237cfce20d9875c248ff863`.
Module: `32f24c5f5dd551cb2f3af4af9dd9f028f0ac3f31670006adecfd4bb4b2c2f336`.
Engine: `33e77433b4b52827b92f1e046a92274a72d778a81053638d4293edd79bafa701`.
RAM audit: 146 protected pages, 28,576-byte upload helper, 22,080-byte engine
helper, 64 bytes of mutable reserve. No flash/map/scheduler changes. Private
platform builds use the fast path automatically; WAD ring/ping-pong remain opt-in.
The bounded Doom server closes after STOP. Public-service restoration is recorded below. Full Linux and
Mac system/frame/WAD/profile replay passed, with all 33 tamper cases rejected.
Both archives were copied, hash-checked and replayed locally before reboot.

## Restored service

After normal reboot, boot `a9a9032f-68fa-4a83-8a6b-27032556f98b`, supervisor
2617 and relay 2619 own `dac960auto`. The unchanged public IPv6 service returned
HTTP 200, 2,891 bytes and RTEMS content from the Mac. See `restoration.json`.
The bounded Doom server on 8087 is closed. Recheck actual ownership before future
work; these IDs describe completion of this batch, not a permanent reservation.
