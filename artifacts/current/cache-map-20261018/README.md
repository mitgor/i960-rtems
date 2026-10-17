# N2: private-RAM cache template on the AcceleRAID 160

This experiment changes **only** logical memory template 1 while the
reboot-only RTEMS Doom owner is active. The incoming new-card registers are
`DLMCON=0`, `LMADR0/LMMR0=c0000002/ffc00001`, and
`LMADR1/LMMR1=c0400002/ffe00001`. After the upper 8 MiB bank is independently
proved and claimed, the guarded build disables template 1, invalidates,
sets `LMADR1/LMMR1=c0800002/ff800001`, and invalidates again. This covers
`c0800000–c0ffffff` and no lower address. Template 0 and the uncached
default are unchanged. The host-written WAD and control path is outside the
new range. The engine's frame source is in the owned range; the i960 data
cache is write-through. After Doom returns and DMA drains, the build restores
the exact incoming template and checks every logical register. STOP still
leaves the callback and DMA resources retained until reboot. No firmware
flash write occurs. See the [Intel Jx memory-configuration manual](https://datasheets.chipdb.org/Intel/80960/manuals/27248302.pdf),
sections 13.6.1–13.6.7, for mask, cacheability and ordered LMT stores.

At the time of physical acceptance the map was selected explicitly by
`DOOM_PRIVATE_CACHE_MAP=1` in `rtems/accele160/doom_dma/build.sh`. It is now the
default for this exclusive Doom build; `DOOM_PRIVATE_CACHE_MAP=0` reproduces
the stock-map control. See the [cached-card baseline](../cache-baseline-20261018/README.md).
The admitted engine bytes, relocations and benchmark workloads are identical
to [N1](../cache-scaling-20261017/README.md). Frame trailers independently
record the live cache status and all five logical registers. The first 32
frames show the expected target map and a cacheable benchmark allocation.
`compare.json` contains all four 10 ms-clock samples for each case.

| Case | Stock map median | Private-cache median | Speedup |
| --- | ---: | ---: | ---: |
| Integer xorshift | 130 ms | 125 ms | 1.04× |
| Warm 1 KiB read | 360 ms | 130 ms | **2.77×** |
| 4 KiB read | 490 ms | 255 ms | **1.92×** |
| 64 KiB read | 570 ms | 565 ms | 1.01× |
| 320-byte stride | 590 ms | 590 ms | 1.00× |
| Repeated 64 KiB word copy | 570 ms | 570 ms | 1.00× |
| Repeated 64 KiB word clear | 105 ms | 110 ms | 0.95× |
| Warm 1 KiB read + invalidations | 365 ms | 365 ms | 1.00× |

Cache-sized reads benefit; streaming and write-through copy do not. The
same Doom renderer segment fell from **91.5 to 49 ms mean** across frames
12–31 (10 ms timer resolution). The diagnostic steady interval rose from
**1.904 to 2.320 FPS**, but each frame deliberately runs a CPU/memory
benchmark; these are not gameplay FPS. Actual gameplay FPS requires a
separate no-benchmark run with the same cache-map option.

The cache-enabled diagnostic run completed 32 direct-DMA frames, four full PIO
comparisons, 32 identical independent HTTP frames, exact native WAD startup,
three-second held-host buffer immutability, whole-frame hashes, guards,
ownership/system audits, engine cleanup and quiescent STOP. The unchanged
[full replay](../accele160-doom-dma-20261017/verify.py) passed including
the post-reset paired stock-flash reads, both with zero residual and guard
changes. `cache-bench.tar.xz` holds its exact binaries, sources and captures.

To measure gameplay rather than injected diagnostics, a second 32-frame run
used the **previously accepted no-benchmark, low-detail engine** from the
[hash-off baseline](../accele160-doom-dma-20261017/README.md), with the same
private-cache mapping in RTEMS. Its first four full PIO frames, all 32 HTTP
frames, native WAD order, whole-frame hashes, retained guards/ownership,
stalled host, cleanup and STOP passed pre-reset replay. Frames 12–31 delivered
**16.964 card FPS / 17.178 HTTP-observer FPS**, versus the accepted stock-map
**9.694 / 9.643 FPS**: **+75.0% card FPS** over that short matched engine/
quality/hash-off window. Mean renderer wall time dropped from 91.5 to 48 ms.
Inclusive FPS is only 6.418 because it includes the intentional three-second
stall. Its full archive replay and both guarded post-reset 1 MiB stock-flash
reads passed on boot `866fa8b0-1ff2-4f1e-ba87-6b183320db96` with zero
residual and guard changes. The earlier diagnostic run's paired post-reset
reads passed on boot `a919c8ca-cb6b-41c5-b84f-0c48770da897`. Both pairs
match unchanged SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
The final new-card driver is read-only `myrsread`; the old card is unbound and
the stock descriptor is idle.

Rebuild with the exact archived `app.c`, `build.sh`, admitted engine and
`DOOM_PRIVATE_CACHE_MAP=1 DOOM_FPS_FRAMES=32`; `run-cache.sh` records the
physical command. `compare.py` independently rejects wrong map geometry,
cache state, workload results and record sequence before reporting medians.
The N1 archive supplies the stock-map comparison frames. The accepted
hash-off archive supplies the exact no-benchmark engine and baseline FPS.
The final `cache-bench.tar.xz` and `plain.tar.xz` archives hold exact admitted
engines, RTEMS sources/binaries, DMA module, full frame/HTTP captures, owner
audits and paired pre/post flash reads. Their SHA-256 values are
`237f287c41549062603edbc4261e5f4c64375fcbc90c7a069f5b39fabb58461a`
and
`2c02565cb983f7fd4df4639c850fa5e0bc0eeed1a400143c63c38a4110320f1b`.
Replay either with
`python3 artifacts/current/accele160-doom-dma-20261017/verify.py --archive <archive>`;
both archived replays passed. `test_map.py` checks the exact region geometry
and non-overlap. `full-replay.json`, `plain-replay.json`, `compare.json`, and
the preserved build/run logs contain the measured evidence.

This is a 32-frame, fixed low-detail qualification, not long interactive
acceptance. The accepted map is now the exclusive Doom build default;
`DOOM_PRIVATE_CACHE_MAP=0` explicitly chooses the stock map.
Do not apply the template in stock-firmware coexistence mode. Repeated long
play, disconnect, STOP during rendering and runtime quality changes remain
follow-up gates before promoting a default.
