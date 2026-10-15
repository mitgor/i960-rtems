# BSP and plane experiment — 2026-10-15

Predeclared acceptance: identical 520-frame scripted input, WAD, full audit
cadence and priority delivery; two baseline/candidate pairs in reversed order
(A/B then B/A) if first candidate passes. Frames100–499 are the measurement
window, with all intervals retained. Compare every pixel and palette to baseline;
keep the known four native differences separately. Measure renderer wall and
sampled CPU components, publication/delivery FPS, release and HTTP availability.

Candidate: private `--fast-render`; -O2 only for r_bsp/r_plane/r_draw and an
exact two-sample span kernel. Keep R_PointOnSide -O0 workaround, all guards,
full paired audits, DMA ownership and STOP/stalled-host tests. No new arena
allocation or traversal stack. No fast-memory change. Keep latency improvements
if FPS is unchanged; reject speed claims without matched measurements.
