# Current Doom evidence

This folder retains the final aggregate reports from the 2026-10-16 four-span
experiment. Full captures, exact binaries and scripts are in Git `a8af272` under
`artifacts/span-four-20261016/`; see the artifact index for restoration.

- Four 520-frame runs: 2,080 corresponding images and 228 full paired audits passed.
- Mean measured FPS: baseline **6.6172**, four-span candidate **6.4493**.
- Baseline repeats differed (**6.4311 vs 6.8144 FPS**). Cause unresolved; neither
  a reliable speedup nor a causal regression is established. Four-span stays opt-in.
- STOP, stalled-host, heap/IRQ drain, replay and mutation checks passed.
- Maximum IRQ gap **10.862793 ms**; 1,942 observed HTTP payloads matched captures.
- The existing four native-reference pixel differences remain; cross-build card
  images agree. HTTP availability is not browser paint or input latency.

`comparison.json` contains the aggregate timings; the other JSON reports preserve
acceptance, image comparison, build checks, repeatability and service restoration.
See [current status](../../../CURRENT-FINDINGS.md) for defaults and open questions,
and [the backlog](../../../game/doom/BACKLOG.md) for experiments.
