# Old/new Doom delay comparison — 2026-10-17

Both cards were measured sequentially on host boot
`8455d432-692b-47b7-aa76-8ebba64e08f5`. The new card ran first and reached
quiescent STOP before the old-card driver bound. Card selection was explicit:
AcceleRAID 160 `0000:37:09.1`, DAC960PG `0000:37:04.1`. No firmware write.
The old-card driver accepted only PCI ID `1069:0010` and its BDF parameter
was explicitly set to the old function; the new-card driver stayed retained.

## Results and comparison limits

These are **current software-stack measurements, not a matched CPU benchmark**.
The new engine is high detail and retains its original arithmetic, copies,
FNV and scalar WAD service. The old engine uses its accepted low-detail,
fast-render/columns/FixedDiv build, no payload CRC/FNV, direct presentation,
DMA ping-pong and WAD ring. Both render a 320×200 indexed image; flat planes
and half-height are disabled. All ownership and full audit checks remain.

| Measurement | New AcceleRAID | Old DAC960PG |
| --- | ---: | ---: |
| Steady card publication FPS | 2.331 | 6.430 |
| HTTP observation FPS | 2.315 (independent 100 ms-poll receiver) | 6.397 (owner publication) |
| Frame interval | 429.03 ms | 156.32 ms |
| Combined engine work between output callbacks | 274.52 ms | not identically instrumented |
| Renderer phase alone | not isolated | 135.90 ms wall / 132.56 ms sampled CPU |
| Extra contiguous delivery-slot copy | 51.94 ms | eliminated by direct presentation |
| Extra odd-page staging | 78.39 ms | eliminated by DMA |
| Card transport FNV | 24.19 ms | disabled in this accepted play profile |
| Host mapped PCI read | 9.28 ms | different DMA/guarded-capture path |
| Host Python FNV | 19.58 ms | not used |
| Observed generation to HTTP availability | 29.38 ms | 5.18 ms |
| Engine-ready to first host frame | 122.93 s | 103.68 s |

New card: 32 frames, 31 complete disjoint phase samples, first 5,043 WAD
requests match the native oracle (5,045 total). All pixels and palette bytes
match the accepted no-input baseline; the timing trailer differs deliberately.
The final frame carries the first **31** phase samples so publication does not
need to hash or stage the final frame twice. Card timestamps are 100 Hz wall
time, not cycle-exact CPU measurements; zero slot wait means below this
resolution. Host clocks use monotonic nanoseconds. HTTP availability and
observer receipt do not establish browser paint/input-to-photon latency.

Old card: 120 frames, all pixels/palette match its previous accepted exact
build, 47 full paired audits. Pre-reload frames 24–59 give **6.352 FPS**;
post-reload frames 80–118 give **6.397 FPS**. Those fixed windows avoid the
scripted held-slot test at 17/18, menu/reload keys at 60/62/64/66, and final
held slots 119/120. Every interval and audit inside each window is included.
The inclusive 24–118 interval, including the deliberate level reload, gives
**5.462 FPS**; its 2.100 s gap at frame 68 is preserved, not hidden as noise.
Stalled host held both frames unchanged for 3.017 s; STOP/drain passed.
The historical long baseline was 6.617 FPS pooled, with repeat variation.

`old-high-detail-historical.json` separately preserves the October 14
high-detail reference: 2.481 FPS with ~315.5 ms renderer wall and ~158.2 ms
sampled CPU under its former ~50% Doom CPU share. It is neither today's
optimized high-detail result nor evidence that the new CPU is slower.
A matched high-detail engine/flags/core-loop test on both boards remains
necessary before making a processor/DRAM-speed claim.

## What to speed up next

1. **Move host FNV into a native helper, keeping the identical check.** The
   live Python check costs 19.58 ms before HTTP publication. An independent
   host microbenchmark on a captured 64 KiB frame measured Python 10.787 ms
   versus exact C **0.0874 ms**, with seven equality vectors including empty,
   zero/FF, captured and 512 KiB patterned inputs. It is a microbenchmark,
   not an integrated speedup. This should remove roughly 11–20 ms of host
   latency; it need not raise FPS because the new card never waited for a
   free slot during this test.
2. **Port aligned word-copy routines into the new adapter.** Its two extra
   byte loops consume **130.32 ms/frame**. Keep full-frame validation and
   all ownership checks; compare the exact payloads. Their combined cost
   is more promising than another host buffer or a 1 ms scheduler tick.
3. **Use card DMA from an owned contiguous slot.** This removes the 78.39 ms
   odd-page staging loop and the 16 PCI-aperture remaps. Retain/pin both slots
   and host buffers until exact completion/ACK; prove STOP, stalled host and
   WAD channel arbitration. New-card DMA is separately qualified, but not
   integrated into this Doom path. Removing staging alone gives a budget
   estimate of **2.85 FPS (+22%)**, assuming no new limiting cost.
4. **Port direct presentation and optional play-mode FNV.** After DMA removes
   staging, removing its 24.19 ms card transport hash gives a budget of
   **3.06 FPS (+31%)**; removing the extra 51.94 ms copy as well gives
   **3.64 FPS (+56%)**. These are serial-budget estimates, not measured
   candidate results. Direct presentation requires an immutable owned engine
   buffer, not simply ACKing mutable Doom RAM. Keep validation builds hashed.
5. **Port the accepted renderer/FixedDiv/column optimizations and profile the
   new renderer internally.** Even removing all 154.52 ms of measured adapter
   work leaves ~274.52 ms/frame. Transport work alone does not establish
   6–10 FPS. Keep lower detail/flat planes as explicit user quality options;
   no quality-reduction gain is claimed for a high-detail build.

Host-read/check/publication work overlaps the next engine frame and must not
be added to the card's 429 ms interval. The native FNV helper was only
benchmarked; no play default, accepted binary or firmware was changed.

## Evidence and replay

- `new-card-evidence.tar.gz`: exact profiled kernel/image/build, 32 complete
  checked card/HTTP frames, control/cleanup/WAD/audit captures and logs.
- `old-card-evidence.tar.xz`: 120 complete frames, guarded DMA captures,
  all 47 paired system/RAM audits, STOP/drain/control/WAD journals and exact
  old kernel/module plus minimal verifier build metadata. Compression keeps
  the 571 MiB raw evidence in one compact archive.
- `source/`: exact generated profiling source/runner, baseline-to-profile
  generator, explicit old-BDF gate, launch, analysis and host FNV microbench.
- JSON reports preserve full distributions, exact build identities and
  independent verification results. The source baseline is Git `0462bef`.

Run `python3 analyze.py` to recheck the new frame bytes, oracle, source/build
identities, trailer, timing math and HTTP payloads. Run `python3 verify_old.py`
to independently replay old system/frame/profile/drain evidence; optional
`--wad /path/to/freedoom1.wad` also repeats the WAD-byte oracle locally. That
oracle already passed on the host with the pinned Freedoom file.

After reset, boot `0a0ca4da-0da6-4448-b54c-58dd4bf51332` showed both cards
unbound. The exact-BDF read-only `myrsread` driver was then loaded only on the
new card. Two guarded full 1 MiB reads matched stock SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`,
with status/residual/guard changes all zero. Their receipts and the final
binding inventory are included and checked by `analyze.py`. The old card is
unbound; both Doom sessions have ended and no browser game remains running.
