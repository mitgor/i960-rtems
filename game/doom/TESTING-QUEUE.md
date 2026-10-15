# Sequential Doom optimization testing

Read `BACKLOG.md` and `PERFORMANCE-RESEARCH.md` for the broader research handoff.
This file records the execution order and accepted scope in Git independently
of that parallel research work.

1. **Done:** exact two-sample spans and selective renderer O2. Matched low-detail
   card runs measured 4.831 → 5.334 FPS with identical corresponding images.
2. **Measured, opt-in:** fixed specialized C columns on that span baseline.
   5.330 → 6.204 FPS (+16.4%), renderer 168.70 → 141.81 ms. Both candidates match
   all 520 reference images; the final unchanged baseline repeats one menu image
   at frame 64. All measured-window images agree. The strict full-run image
   comparison retains this failure. Full system/frame/WAD audits and lifecycle
   checks pass. See [evidence](../../artifacts/columns-20261015/README.md).
3. **Done:** one-binary runtime high/low detail selection (`--runtime-detail`).
   Native and card tests confirm low/high/low with F5 and safe STOP/drain. Fixed
   benchmark builds remain fixed. See [controls and proof](../../artifacts/columns-20261015/QUALITY.md).
4. **Measured, opt-in:** exact bounded FixedDiv via unsigned i960 `ediv`.
   `--fixed-div-profile` measures 47 source call sites; `--fast-fixed-div`
   selects the candidate and currently requires that profiling flag. Matched
   instrumented A/B/B/A: **6.047 → 6.309 FPS (+4.34%)**, renderer 144.94 →
   138.08 ms, inclusive divide brackets 9.588 → 3.669 ms/frame. All 2,080 images
   and call-count traces agree; 231 full paired audits and 66,560 on-card
   arithmetic comparisons pass. See [evidence](../../artifacts/fixeddiv-20261016/README.md).
   Preserve saturation, signs, rounding and the original INT_MIN fallback.
5. **Next:** qualify the exact divide without per-call profiling/self-test
   overhead. Do not equate this instrumented benchmark with ordinary-play FPS.
6. **Validation follow-up:** record the frame/tic consuming scripted input;
   the latest batch agrees, but it does not explain the earlier transient menu
   difference in the asynchronous pipeline.
7. Then test bounded BSP changes, further selective compiler settings, measured
   memory hot spots and cache/layout changes one at a time on the latest baseline.

Quality reductions must have explicit independent controls, preferably at runtime
in one build, with normal rendering available. Flat floors, smaller viewports and
alternative fuzz remain unimplemented; do not silently enable them. Keep full
audits and ownership checks. Retain demonstrated stage-latency improvements even
when overall FPS does not improve. Report mixed-quality timing separately from
matched performance comparisons.
