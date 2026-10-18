# Persistent AcceleRAID Doom acceptance

The new card now runs a persistent, browser-controlled Doom session through
the same owned two-buffer DMA transport. From the Mac repository, run
**`./doom`** and open **http://192.168.2.75:8087/**. The installed remote
command is `/home/mit/.local/bin/i960-doom`. [Run, controls, STOP and rebuild](../../../game/doom/play/accele160/README.md).

The card kernel's `DOOM_PERSISTENT=1` mode removes its 32-frame and 30-minute
lease limits. The private i960 platform's `--persistent-play` removes its
separate 30-minute engine budget. The host publishes a heartbeat; missing
heartbeat, missing slot ACK and missing DMA completion retain bounded paths.
Normal STOP asks the engine to retire first, verifies its final published
frame/code/heap, then stops RTEMS. Exclusive ownership and DMA buffers stay
pinned until reset. No flash programming command is part of this path.

The first physical session on boot `bdcfd659-9239-45e9-8c05-60a46388831e`
completed **1,058 frames**, including browser movement/firing and **52 fully
acknowledged key events**, before browser STOP. All 1,058 complete guarded DMA
captures are archived, with matching frame hashes, markers, source/epoch/
generation/ACK ownership, independent PIO checks for the first four frames,
the exact 5,043-read native startup oracle, six later WAD requests, final
frame readback, code integrity, empty application heap, restored cache map,
four IRQ-owner lifetime/stack checks, DMA drain and reboot-only quiescence.
The old PG stayed unbound. [Replay summary](replay.json) also rejects four
tampered captures and matches the first 32 pixel/palette blocks to the
accepted wide-copy baseline.

| Measurement | Result |
| --- | ---: |
| Engine entry to first frame, card clock | 73.95 s |
| Matched steady frames 12–31 | 17.5926 card FPS |
| Last 64 frames after player input | 19.3252 card FPS |
| Independent HTTP payloads sampled on the Mac | 53, all exact |
| Native host test | Three 256-frame runs; deterministic repeat, input difference, STOP and heap drain passed |

This is a longer functional gate, not a multi-hour soak. Scene changes after
input explain why the final window is not a matched optimization comparison.
The sparse Mac observer is a byte-integrity witness, not a browser paint-FPS
measurement. The [screenshot](browser.png) shows the actual canvas during
play. The selected renderer is the accepted low-detail, optimized-column,
wide-copy, private-cache-map engine with card FNV off and native host FNV on.
Flat planes and half-height are off.

The required reset did not return through SSH and needed a physical power
cycle. Both complete guarded [post-reset readbacks](post-0/result.json) and
[the second readback](post-1/result.json), on boot
`31291627-dcd0-44bd-9c81-50708c818d80`, match the full stock 1 MiB hash
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`
with zero status, residual and guard changes. On this fresh boot the reader
driver was not autoloaded; the launcher now provisions its exact gated
`myrsread.ko` and selects `read_bdf=0000:37:09.1`. It refuses a conflicting
driver or any retained previous exclusive session. A fresh no-frame-limit
service was then launched through `./doom`.

That fresh no-limit session subsequently completed **1,565 frames** with
browser input and exited through Doom's own Quit path. The last mailbox event
was Y key-up: 97 events were consumed and the final release arrived after
the engine had already quit. Full final engine/frame/heap/cache/IRQ/DMA/owner
checks passed. Its [result](fresh-session-result.json) and
`fresh-session.tar.xz` retain the ordinary sampled captures plus all frame/WAD
receipts. This is a separate user-play run; its next post-reset flash pair is
pending. The closed 1,058-frame acceptance above includes its complete pair.
The service is now stopped, resources remain retained, and `./doom` correctly
refuses another launch until reset. The active-service idempotent launch also
returned the existing browser URL before the user-play session ended.

`acceptance-pre-reset.tar.xz` is SHA-256
`7b7a75a97c5eb557a92e7e54df75dbfd10e6028133701366bac4367151d9d8e6`.
It contains the exact tested kernel, admitted engine/relocations, host and
card sources, command/pin/reader modules, all 1,058 frames, receipts and
pre-run whole-flash reads. Post-reset reads, native results, HTTP samples and
service log are beside it. `installed-host.tar.xz` contains the final installed
host sources, bundle inventory and gated driver; its defaults allow five
minutes for browser reconnection. The tested kernel and engine are unchanged.
Freedoom is referenced by its existing pinned archive in
`artifacts/doom-m1-20261011`; it is not duplicated in the evidence archives.

Replay from the repository root:

```sh
python3 artifacts/current/doom-persistent-20261018/verify.py
python3 game/doom/play/accele160/test_launch.py
python3 rtems/accele160/doom_dma/test_browser.py
```

Remaining qualification: multi-hour play, level transitions, physical
SIGTERM/disconnect/process-death runs and repeat fresh-boot launch after
future kernel updates. Browser STOP is physically accepted; the other
graceful requests share that engine-stop path, but are not separate physical
acceptance claims. The older stalled-host/DMA gates remain archived; this
session did not deliberately stall ACKs.
