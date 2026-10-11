# Bounded fixed-point raycaster and RTEMS profiling

**Hardware-validated (2026-10-11):** 548 replies match native replay; both
sessions restored/unloaded and production HTTP is restored. Browser movement,
turning/reset passed. See the [measured findings](../../artifacts/raycaster-20261011/README.md).

The renderer produces an 80×60 indexed frame in a returning RTEMS worker. It
uses Q10 positions/directions, an offline cosine table, a 12×12 map, collision
checks and flat, side-shaded walls. There is no floating point on the target.
The browser expands a ten-color palette and handles keyboard input. This is a
small graphics workload, not a Doom port.

## Build and run

```sh
make -C game/raycaster test
python3 game/raycaster/server.py --port 8098
```

Open <http://127.0.0.1:8098/> for native simulation. Arrow keys/WASD move and
turn; reset returns to (2.5,2.5). Movement is per completed frame (1/16 cell and
4/256 turn per active direction), not wall-clock physics. Opposite forward/back
keys cancel; opposite turn keys cancel. Requests are serialized; blur clears
keys. The server is loopback-only and displays its actual backend.

Target build uses an isolated snapshot of the existing bounded RTEMS session:

```sh
python3 game/raycaster/build_target.py --work /path/to/FRESH-work \
 --sources /home/mit/i960-rtems-web-20261011/sources
python3 game/raycaster/transfer/build.py --out /path/to/FRESH-module --fast --coarse
make -C /lib/modules/$(uname -r)/build M=/path/to/FRESH-module CC=gcc-12 modules
```

The hardware must have one exclusive owner. Do not interrupt a parallel OS
experiment. Stop the production web service normally and verify restoration and
unload before loading the game. The existing lock/driver checks also enforce
exclusive use. Run `check_card.py --payload WORK/session/kernel.bin --module
MODULE/dac960rtems.ko --output FRESH-CAPTURE` for the scripted/profiling matrix.
Use the same arguments with `server.py --backend card` for browser output. An
SSH local forward provides browser access without exposing the control server.
Ctrl-C performs the audited close; restore and check production HTTP afterwards.
No driver validation checks or memory permissions are weakened for profiling.

## Faster validated framebuffer readback

The recommended transport command above uses the hardware-tested exact-count
and range-validation optimization. It reduces full-frame kernel time from
57.83 to 55.74 ms in repeated comparisons, with the same command sequence,
paired reads, bytes checked and audit cadence. The i960 payload is unchanged.
For detailed upload/arming timings, omit `--coarse` and pass `--command-profile`
to `check_card.py`. See [contract and profiling tools](transfer/README.md) and
[preserved results](../../artifacts/transfer-20261011/README.md).
Run `make -C game/raycaster test-transfer` before changing these validators.

## Memory helper variants

The target builder now defaults to `--memory word`: aligned 32-bit RAM copy and
clear with byte prefixes/tails and a byte-copy fallback for different alignments.
`--memory byte` reproduces the original payload exactly. `--memory-check` adds
264 bounded reference-check batches to a separate checking image; do not use
that image for performance comparisons. The normal word build adds 160 bytes of
code and no data/BSS. Both variants retain the same renderer, wire protocol,
RTEMS scheduler, memory layout, host checks and audit cadence.

See [memory contract and tests](../../rtems/memory/README.md). The production
network service and parallel interrupt/ownership profiles are unchanged. Original
byte-build measurements below remain historical; current A/B evidence is in
[the word-memory report](../../artifacts/word-memory-20261011/README.md).

## Bounds and protocol

`RAY1` uses eight little-endian request words: magic `0x31594152`, operation,
column budget, key bitmap, pixel-output flag, benchmark kind, repetitions,
reserved zero. Invalid requests and insufficient output capacity cannot mutate
application state. Operations:

- 0: reset. Budget, keys, kind and reps must be zero.
- 1: render 1..80 columns. Key bits: forward=1, backward=2, left=4, right=8.
  Movement applies only when beginning a new frame. Additional keys received
  during a partial frame do not change its frozen viewpoint.
- 2: snapshot, with zero budget/keys/kind/reps. Useful transfer baseline.
- 3: benchmark, with zero budget/keys, kind 0..8 and 1..128 repetitions.

Pixel flag 0 returns a 64-byte header; 1 returns 64 + 4,800 bytes. Header words:
magic, frame generation, next column (80 means complete), Q10 x/y, angle 0..255,
cumulative grid steps for the current frame, published frame FNV-1a hash,
benchmark digest, pixel byte count, benchmark kind/reps, four reserved zeros.
The frame counter wraps modulo 2^32. Each ray performs at most 32 grid steps;
map accesses are checked. A full batch writes at most 4,800 pixels. Completing a
frame copies and hashes a fixed 4,800 bytes, then atomically publishes it with
respect to serialized host calls. Partial replies contain the previous complete
frame. Reset publishes an empty frame. State is private to one RTEMS session.

The target uses a 20,000-byte aligned state reservation, with runtime size check,
and 48 KiB RTEMS workspace. Measured linked image: 23,792 bytes text, 468 data,
71,040 BSS. Source uses the existing 128 KiB immutable region and guarded private
RIO1 region. It neither claims additional RAM nor leaves interrupts running.

## What the profiler measures

The derived host module adds six monotonic timestamps around the existing
session transaction. It retains all original pending/dirty checks and cleanup:

- Upload: request validation/copy and fixed RIO block upload.
- Arm: first-entry handshake (first callback only), result sentinel and table arm.
- Execute: `issue(0x6f)`, including host command preparation, firmware dispatch,
  callback, completion polling and command status validation.
- Verify: paired table/result reads and checks.
- Audit: paired payload/staging reads and response/immutable validation.

The five phase durations sum to kernel total. `check_card.py` also measures
whole `Board.step`, including Python capture verification and audit compression.
That wall interval excludes its native oracle and phase-JSON rewrite. The
existing Board trace records a narrower write/read interval. These quantities
must not be mislabeled renderer CPU time or PCI bandwidth.

The matrix covers 160 full-frame renders, forty 10-column batches, twenty each
header-only/full snapshots, and five repeats at 1/16/64/128 operations for each
benchmark kind. Kind 0 is empty; 1 aligned memcpy(4096); 2 unaligned memcpy(4096);
3 memset(4096); 4 overlapping memmove(4096); 5 equal-buffer memcmp(4096);
6 strlen(4095); 7 RTEMS semaphore request/reply roundtrip; 8 rtems_clock_tick.
Memory operations call the selected byte/word RTEMS session libc helpers with
builtins disabled. Handoffs add real worker wake/block/context-switch pairs. Software
clock ticks run with this workload's otherwise idle watchdog queues; they are
not an asynchronous ISR benchmark. The native oracle checks digest/result
semantics but does not emulate RTEMS scheduling cost.

`profile.py CAPTURE/phases.json` computes median phase timings and estimates
per-operation slopes after subtracting empty-benchmark medians at each batch
size. Fits below R²=0.9 or nonpositive slopes are marked unresolved. Repeated
operations warm the same buffers; setup, checksums and transport remain in the
intercept. No card timer registers are read or written for profiling. Results
are differential command-time estimates, not cycle-accurate microbenchmarks.

A smaller reply does not reduce this driver's fixed request/output allocation
or paired staging reads: ordinary paired payload reads cover 942,272 bytes;
every 32nd callback reads 1,048,576 bytes. Host debugfs access/copying adds further
work. Preserve this verification contract when proposing transport optimization.

## Tests and evidence

ASan/UBSan exercises 2,000 partial render/movement batches, bounds, output guards,
request rejection and all benchmark kinds. Native tests compare sliced/full
rendering, cardinal geometry and independent slab intersections across a full
turn, collision bounds, snapshots, benchmark digests and HTTP input validation.
The C and Python tests run on both the Mac and remote Linux host.

`verify_card.py` replays archived replies against the native core, checks
payload/module identities, required audit lengths, RIO immutability and full
restoration. Initial audit captures contain only the 471,136-byte prefix; they
must not be counted as full 512 KiB reads. Final close checks the full allocation.

[Hardware results and profiling findings](../../artifacts/raycaster-20261011/README.md)
are recorded separately from this protocol. The production server and parallel
OS profiles remain separate applications.

## Upload latency follow-up

The opt-in [quiet upload transport](upload/README.md) suppresses one blocking
firmware UART diagnostic during a bounded session and restores it afterward.
It retains every existing check and adds paired checks of the modified region.
Use `python3 game/raycaster/upload/build.py --out FRESH-module --quiet --coarse`.
Repeated card runs reduced full-frame kernel time 55.84 → 24.14 ms; this is not a
browser FPS measurement. [Evidence and the corrected startup hazard](../../artifacts/upload-20261011/README.md).
