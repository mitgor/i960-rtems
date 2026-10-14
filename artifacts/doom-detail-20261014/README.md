# Doom low detail and task CPU sampling — 2026-10-14

**Bounded physical acceptance passed: high detail 2.481 FPS, low detail 3.178 FPS (+28.09%).** Workspace `/home/mit/i960-detail-20261014`;
initial boot `e20b227d-5c5a-4432-b11d-1f6842271218`, card unbound and no relay
owner. Parallel RTEMS chat was idle and had explicitly left Doom resources alone.

## Design

`--low-detail` selects Doom's existing low-detail renderer at display setup:
half as many horizontal view samples, doubled columns, unchanged 320×200 indexed
frame plus palette. Persistent-screen and owned direct-presentation semantics
remain. This is not a lower-resolution transport or browser scaling change.

`--detail-test` selects high detail for frames 1–16 and 41–52 and low detail for
17–40, using a bounded lookup table. It implies CPU/frame profiling, no FNV and
direct presentation. Host frame CRC is off throughout. It requires the bounded
52-frame pipeline test; interactive launch of the mixed engine is refused.
Full periodic monitor/RAM audits, all guarded captures, first four exact paired
DMA/mailbox reads, ownership, generation, ACK, STOP and global drain remain.

`--cpu-profile` adds an independent Doom-task sample counter at timer interrupt
entry, before timer processing/dispatch. Only interrupted worker 1 (the Doom
owner) is counted. RTEMS 4.6.6's `ticks_executed` is deliberately not used: pinned
`threaddispatch.c` increments it on context switches as well as timer ticks.

**This is sampled CPU attribution at 10 ms resolution, not cycle-exact timing.**
Phase boundaries record cumulative samples via owned callback stage 102. Samples
exclude time attributed to other tasks, but periodic sampling can alias with
scheduling and assigns IRQ overhead to the interrupted task. Short phases can
have zero samples. The scheduler tick and hardware timer configuration are
unchanged. Higher-resolution task-switch/interrupt accounting remains future
work; no unverified timer register writes or CPU-frequency changes are made.

A `CPU1` trailer follows PFR1 at byte 64832: magic, version, actual renderer
detail, sample period (10 ms), renderer/BSP/planes/sprites/screen-copy/adapter
sample deltas, two reserved zero words. Remaining padding stays zero. All bytes
are covered by paired readback and independent full-frame journal replay.

## Build and run

```sh
python3 game/doom/play/build.py --work /home/mit/doom-detail-build \
  --pipeline --detail-test
sudo python3 game/doom/play/run.py --work /home/mit/doom-detail-build \
  --output /home/mit/doom-detail-capture --pipeline --pipeline-test --wad-dma --port 8087
```

For a fixed low-detail interactive candidate, build with
`--pipeline --low-detail --no-fnv --direct-frame --frame-profile --cpu-profile`
and run `--pipeline --no-crc --wad-dma`. Do not overlap owners or force-unload a
retained module. Physical acceptance of the fixed interactive build is not implied
by bounded mode-switch testing.

## Accepted measurements

| Block | Frames | Delivered FPS | Renderer wall | Sampled renderer CPU |
|---|---:|---:|---:|---:|
| High before | 5–16 | 2.442 | 312.7 ms | 157.3 ms |
| Low first | 17–28 | 3.503 | 207.3 ms | 103.6 ms |
| Low second | 29–40 | 2.908 | 212.7 ms | 106.4 ms |
| High after | 41–52 | 2.521 | 318.2 ms | 159.1 ms |

Each FPS is eleven within-block intervals; pooled high and low each use 22.
The first frame of each block is excluded from phase averages as well, avoiding
view-setup costs. All full audits remain in the experiment; no slow interval is
discarded. Pooled high **2.481032 FPS**, low **3.177992 FPS**, ratio **1.280915**.
Low blocks vary substantially: frame 40 has an **884 ms delivery interval**, with
**758 ms host completion wait**, **14 ms guarded readback**, and hardware DMA
below the 10 ms clock resolution. Its renderer still took 220 ms. The delay is
retained in the 3.178 FPS result; its exact software-side cause remains open.
Do not quote 3.503 FPS as sustained performance or call the completion wait bus
time. This is one bounded no-input scene, not all levels or long interactive play.

Across equal-sized phase samples, renderer wall time falls **315.5 → 210.0 ms**
and sampled task CPU **158.2 → 105.0 ms**. Low-detail phase means: BSP/setup
120.9 ms wall / 60.5 ms sampled CPU; planes 63.6 / 32.3; sprites 25.5 / 12.3.
The retained full screen copy still takes 46.4 ms wall / 23.2 ms sampled CPU.
The engine is attributed roughly **50% CPU share** during rendering, consistent
with the existing peer-task scheduling. This is statistical evidence, not an
exact separation of preemption, IRQ, idle and task costs. Tick configuration,
priorities, peer checks and audit cadence are unchanged.

The next useful experiment is a controlled scheduling-policy comparison that
retains peer ownership/isolation checks, full audits and bounded STOP. Follow
with profiling/optimization of BSP/column/span loops or a smaller view. Even
low-detail sampled renderer CPU alone is ~105 ms before screen copy and other
work, so **10 FPS is not demonstrated or guaranteed**. Higher-resolution task
switch/IRQ accounting remains future work; this batch improves attribution, not
clock resolution.

## Correctness and limits

- 52 full guarded DMA captures; first four complete DMA/mailbox frames identical.
- 14 full paired monitor/RAM audits, generation/bounds/ownership checks, owned
  STOP and global allocation drain all pass. All 35 journal tamper cases reject.
- Two deterministic 52-frame native runs; native input/STOP/heap tests and 320
  adapter ownership cases pass under sanitizers without reported errors.
- All 28 high-detail pixel/palette payloads match the previous accepted card run
  exactly. The existing seven native/card pixel differences remain.
- All 24 low-detail frames have four native/card pixel differences, at
  `(140,91), (141,91), (140,92), (141,92)`, within the previously affected small
  region. Palettes match. This discrepancy remains unresolved; **low detail is
  not byte-exact with the native oracle**. Every difference/value is retained in
  `measurements.json`; `visual-check.json` records the prior-card comparison.
- All 52 HTTP binary payloads match their guarded captures by SHA-256. This is
  endpoint delivery FPS, not measured browser painting or input latency.
- Kernel RAM audit retains 400 bytes of mutable-tail space. No firmware write,
  arena expansion, timer-rate change or ownership weakening.

[High-detail card capture](card-high.png) and [low-detail card capture](card-low.png)
are decoded from frames 12 and 28. Only pixels/palette are used for PNG export;
raw captures retain both profiling trailers unchanged.

## Reproducibility

Exact accepted identities:

- kernel `05b6e210ac198cec464837b06348963d53897fa6c68818cdb68f7073a0b52f12`
- module `36895753f725aceea792e7d0e7acc028e64c2bdf3399295aee2c269a1ae3252e`
- engine `5cfa66689f5f966054e053bc8a8d2e10b2366c736afdfb78b428334e653801d9`
- `build-evidence.tar.gz` SHA-256 `8f3130b706c9fb4f02248513aa21efe27baa76154cd3051debf10e107d748684`
- `card-evidence.tar.gz` SHA-256 `a8cb7a60d96a27768f79743c2c514e4dd37bc8ae431cfde623f3f5f24cbfda43`

Build evidence contains exact sources, objects, admitted image, kernel/module,
native frames, tests/logs, RAM audit and disassembly. Card evidence contains every
frame/guard, control/transfer journal, full snapshots, STOP/drain and replay/tamper
results. Both archives were copied and hash-verified locally, then independently
replayed on macOS before reboot. `local-*.json` and `http-verification.json`
record those checks. `preliminary.json` predates final shutdown and has only nine
snapshots; it is explicitly superseded by `measurements.json` with fourteen.

From this artifact directory:

```sh
python3 replay.py --wad /path/to/freedoom1.wad
```

The verifier checks the WAD's pinned identity. `build.sh` reuses a private copy of
the accepted prior dependency tree; the fresh-checkout build command above is the
standalone route. An initial transport build lacked the pinned artifact symlink
and stopped before hardware use. That dependency was supplied; the completed
build additionally records actual `detailshift` rather than requested mode.
The card ran only the final identities listed above.

The test owner closed on boot `e20b227d-5c5a-4432-b11d-1f6842271218`.
Normal reboot was requested after local verification. See `restoration.json`
for final reachability/service state and `restore.sh` for the exact relay command.

**Final service state:** SSH timed out after the release reboot. A user power
cycle was requested; public IPv6 HTTP restoration remains pending. No retained
module was force-unloaded. All accepted evidence was already verified locally.
