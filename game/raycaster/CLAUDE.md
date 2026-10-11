# Raycaster application guidance

Hardware acceptance passed: 548 native-matching replies, two clean restorations,
and restored IPv6 HTTP. Timing findings are differential estimates.

Read README.md and the corresponding artifacts/raycaster-20261011/README.md
from repository root. The renderer is bounded and freestanding; the target
adapter runs it on the existing cooperative RTEMS session. Keep this work
separate from the active leaseirq/ownership profile and production autonet.

No profiling timer is borrowed. Host timestamps measure command intervals and
paired audit overhead. Differential batch slopes are estimates, not CPU cycles.
Do not weaken validation or audit cadence to report a faster frame rate.

Use the existing exclusive hardware lock and wait for parallel card work to
finish. Always retain exact binaries/captures, verify full restoration and
restore HTTP. Build in a fresh isolated directory. No flash changes required.

`make -C game/raycaster test` runs native bounds, geometry, sliced-frame and
protocol tests. Target/host replies are serialized explicitly, never memcpy
of a padded i960 struct. Only complete frames are published; keys are sampled
at frame start. The next optimization should follow the measured bottleneck.

Word-memory builds: `build_target.py --memory word` is now the raycaster default;
`--memory byte` preserves the exact original binary. Read `rtems/memory/README.md`
and `artifacts/word-memory-20261011/README.md` for scope and measured acceptance.
Do not silently propagate these helpers into production/autonet or IRQ profiles.
The `--memory-check` image injects 264 correctness batches; exclude it from
performance results. A/B comparison must preserve output and all audits.
