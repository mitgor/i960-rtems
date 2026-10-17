# AcceleRAID direct Doom DMA — 2026-10-17

The first bounded physical run passed 32 complete guarded DMA frames, all
32 binary HTTP payloads, four full paired PIO comparisons, the exact native
5,043-request startup prefix, all 5,045 WAD reads, retained full-bank/arena/
owner/text audits, engine cleanup and quiescent STOP. Channel 0 alone was
used. The old card remained unbound. No firmware write occurred.

**Post-reset acceptance passed:** both guarded complete 1 MiB reads on boot
`9d404b50-32ce-4ab3-8825-183ba02d24a9` match the accepted firmware. The
old card remained unbound. This closes the first bounded DMA run.

| Measurement | Previous new-card path | This new-card candidate | Old optimized path |
| --- | ---: | ---: | ---: |
| Steady FPS | 2.331 | **7.819 card / 7.878 HTTP observer** | 6.352–6.397 |
| Observed frame to HTTP availability | 29.38 ms | **2.03 ms** | 5.18 ms |
| Renderer wall / sampled CPU | not isolated | **91.5 / 90.5 ms** | 135.9 / 132.6 ms |

The fixed steady window is frames 12–31, inclusive, 19 intervals. It excludes
the first-four PIO shadow comparisons and deliberate generation-eight host
stall. The inclusive first-to-last result is **4.480 FPS**, including that
three-second pause. The independent HTTP observer polls every 20 ms; its FPS
has endpoint sampling uncertainty and does not measure browser paint latency.
The short steady run is a qualification result, not a sustained-play claim.

This ports the exact old optimized **low-detail** engine, fast renderer,
columns and FixedDiv, direct double-buffer presentation and word copies.
Pixels and palette for all 32 frames match the old card's accepted exact
build. Low detail is a deliberate benchmark quality choice; flat planes and
half-height remain off. The earlier new-card path was high detail, so the
3.35× gain combines software and quality changes. It is not a matched CPU
benchmark. The old/new low-detail engine is identical, but their adapters,
WAD service, timer attribution and audit schedules still differ.

The new adapter removes both its extra contiguous copy and odd-page staging
after the first four qualification frames. Each source drains before engine
reuse; each coherent destination stays immutable until exact generation ACK.
A second chained DMA descriptor publishes the marker after the frame. Every
frame keeps card transport FNV, native host FNV, full DMA prefix/suffix and
marker checks. Preparation and checking remain outside interrupt context.
The three-second stalled host retained the exact full buffer and marker.
Normal module unload was tested and denied; buffers remain reboot-pinned.

WAD startup is about 84 seconds from engine call, compared with the previous
123 seconds. It still uses 4 KiB scalar requests, not the old shared WAD ring.
Both figures include engine initialization and waits rather than pure DMA.
Persistent interactive play, switchable quality and WAD ring/read-ahead
remain follow-up gates. The first matching old
engine here fixes low detail only for the bounded comparison.

## Optional hash-off run

A second bounded run with `CARD_FNV=off` passed the same 32 DMA/HTTP frames,
four complete PIO comparisons, all old pixels/palette, native WAD prefix,
full system/owner/guard audits, three-second held-host test and STOP. Its
predefined frames 12–31 reached **9.694 card FPS / 9.643 HTTP-observer FPS**,
with **1.975 ms** observed-to-HTTP availability. Renderer wall/sampled CPU
was 91.5/91.0 ms. Inclusive FPS including the pause is **5.041**. This is
24.0% above the first hash-on window and 4.16× the previous new-card path;
the previous path used higher quality. It is still a short qualification.

The default stays `CARD_FNV=on`. Off mode removes only the per-frame card
transport hash; host full-frame FNV/SHA, complete buffer guards, marker,
ownership and all system/arena/STOP audits remain. The admitted engine's
presentation hash was already disabled in both modes, as on the old setup.
Final engine-frame and text integrity checks stay enabled.
Both modes preserve the same optimized engine and the same low-detail setting;
no flat planes, half-height or new quality reduction was added between them.

The second kernel additionally fixes a timer-boundary identity hazard:
completion marker time now copies the announced publication tick rather than
sampling the interruptible timer again. Native tests deliberately separate
those times. Consequently these are two exact documented kernel versions,
not a same-kernel alternating-mode long A/B test. **Both hash-off post-reset
full guarded flash reads passed** on boot
`6ca7613a-2c72-40d2-a8a4-238fe994b9bd`, matching the accepted firmware.
Its complete captures are saved in `hash-off.tar.gz`.

## Reproduce and inspect

`accepted.tar.gz` holds exact source, kernel/image/map, admitted engine and
relocations, Linux pin module, native helper, paired full pre/post flash reads,
full-frame DMA captures, HTTP packets, control/owner/arena/STOP/WAD captures
and original run log. `old-pixels.json` pins accepted old pixels/palette.
The selected engine is recorded by its exact manifest, not a stale entry
literal. `fail0.tar.gz` preserves the rejected first launch: a stale host
entry check stopped after admission, before engine call/DMA. STOP reached
quiescence and resources remained retained; it required reset.

Run `python3 verify.py` for the fully closed hash-on run. Use
`python3 verify.py --archive hash-off.tar.gz` for the fully closed hash-off run. Independent replay checks
all complete DMA buffers, hashes, metadata, HTTP bytes, native WAD request
order, full-bank report, kernel/image/engine/module/source identities,
STOP/drain and firmware reads. Eighteen negative mutations reject changed
payloads, guards, marker fields and ownership receipts.

Native production-header tests passed under 32-bit ASan/UBSan on the host:
DMA chain/reuse/markers/peer isolation/admission and error/timeout retention;
all copy alignments, 64 KiB transfers and protected tails. Clearing CCR is
never treated as an abort, and uncertain transfers never release memory.

The latest source and `live-32-manifest.json` bind the second kernel. Both
exact source versions remain in their corresponding archives. Build, run and
native-test instructions live in `rtems/accele160/doom_dma/README.md`;
coherent-buffer lifetime is documented in `host/accele160/frame_dma/README.md`.
The current wrapper chooses card hashing through `CARD_FNV=on|off`.
