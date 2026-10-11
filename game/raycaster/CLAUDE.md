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

Validated transport acceleration: use `transfer/build.py --fast --coarse` for
ordinary bounded raycaster sessions. Omit `--coarse` with `check_card.py
--command-profile` to capture complete command timing. Read `transfer/README.md`
and `artifacts/transfer-20261011/README.md`. All read coverage and exact guard
counts are retained; never replace paired snapshots with sampling/checksums.
The three upload completion waits dominate; their cause is not proven to be a
removable firmware delay. Run `make -C game/raycaster test-transfer` for changes.

UART follow-up: the opt-in `upload/build.py --quiet --coarse` is card accepted.
Read `upload/README.md` and `artifacts/upload-20261011/README.md`. Never move
suppression into OPEN or insert PING between the first cache handshake and runner
arming: the exploratory build exposed stale dispatch and was correctly rejected.
Preserve fixed preimages, per-step paired 80-byte checks, dirty retention and
prechecked exact restoration. `python3 game/raycaster/upload/test.py` covers the
cache-order regression and failure paths. Other profiles remain unchanged.

Callback/readback candidates live in `callback/`. Read its README and
`artifacts/callback-20261011/README.md` for current acceptance status. The flags
`build_target.py --request-words --render-fast` are explicit opt-ins; retain
`ray.c` as the independent oracle. `callback/build_transport.py --poll20` changes
only the completion observation interval, never validation or read coverage.
`make -C game/raycaster test-callback` covers differential responses and every
request bit mutation. The seven-session comparison plus coarse release passed: 3,368 replies, 104 full
audits, eight restorations. Recommended 50 us transport + both target flags gives
19.44% lower kernel time; 20 us costs 17.19% more host CPU for 0.269 ms less audit
time. Keep it optional. Preserve full paired coverage and coordinate hardware
through the existing lock; production remains autonet.

Bounded frame queue: `queue/` is an opt-in cooperative profile. Read its README
and `artifacts/framequeue-20261011/README.md`. Four accepted sessions verify 518
replies and 518 paired full allocation audits. Separate PUBLISH+ACK costs 39.947 ms
versus 20.596 ms baseline; it is not the default performance path. Full audits
remain mandatory every STEP. READY is not an asynchronous DMA/cache barrier.
The first driver faulted because three capture loops still used 54 after the
array grew to 60; preserve that failed evidence. `make test-queue` now tests actual
generated allocation/publication/copy/free and read_pair storage guards, as well
as the protocol and failure paths. Always update all lifecycle bounds together.
Next is a validated combined ACK-and-PUBLISH, with no audit reduction.
