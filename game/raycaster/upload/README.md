# Upload completion bottleneck: UART diagnostic experiment

The stock 4.07-0-29 upload implementation at `c004ced0` prints
`\nOff%X Siz%X` before calling the same DMA transfer helper used for reads.
The formatter at `c000a2a0` calls the blocking UART character routine at
`c000a120`. Its transmit-ready loop has no host-controlled deadline. This is
an upload-only latency candidate; measurements must establish its live cost.

`audit.py` checks every disassembly row against the preserved vendor bytes and
prints the bootstrap method installation, formatter, UART and DMA paths.
`build.py --quiet` derives the exact-validation optimized raycaster transport.
The default without `--quiet` is its comparison baseline. The payload, command
completion loop, DMA preparation, guards, status/ID checks, callback disarm,
paired response comparisons, every-32nd full audit and restoration stay intact.

## Data-only, scoped change

After ordinary OPEN saves and verifies the image and installs the pinned cache
and runner code, the first STEP performs its existing request upload and cache
handshake. With the maintenance callback still installed, the quiet extension
verifies paired live reads of:

- Controller pointer at `c011e22c` -> `c0110780`.
- Read/write methods at `c0110860` -> `c004ce90`, `c004ced0`.
- All 256 formatter bytes and 104 UART bytes from the bootstrap copy.
- The 16-byte format/padding and adjacent 64-byte upload function, at `c004cec0`.

It replaces only the format's first newline with NUL using a fixed four-byte
upload (`00 4f 66 66`, leaving three bytes unchanged). It invokes the already-installed cache invalidation callback once, requiring
status `017d`, then proceeds to the normal sentinel/runner arm. Paired reads
verify all 80 bytes; subsequent STEPs repeat that check before consuming their
sequence or uploading the request. No general firmware-write interface is exposed.

CLOSE first requires paired reads to match exactly the original or suppressed
80-byte region. It then restores the pinned four original bytes while the maintenance callback is
still available, invalidates caches, verifies the PING table, and compares all
80 original bytes twice. Then the normal full RAM/runner/result restoration runs.
The formatter still executes its normal interrupt-disable/count/restore path;
only this diagnostic's serial characters disappear. Other diagnostics and error
messages remain enabled. Nothing is written to flash.

`quiet_dirty` is set before the first possible write and participates in both
session pinning and driver-removal retention checks. A pending command or
uncertain user callback forbids quiet restoration. Any failed verification keeps
the state dirty. A failed quiet activation may leave original or suppressed data;
cleanup writes only the pinned original word, verifies neighbors and never retries
user software. An uncertain result requires recovery, not forced unload.

## Reproduce

```sh
python3 game/raycaster/upload/audit.py
python3 game/raycaster/upload/test.py
python3 game/raycaster/upload/build.py --out FRESH-module --quiet
make -C /lib/modules/$(uname -r)/build M=FRESH-module CC=gcc-12 modules
python3 game/raycaster/check_card.py --payload KERNEL --module FRESH-module/dac960rtems.ko --output FRESH-capture --command-profile
python3 game/raycaster/verify_card.py FRESH-capture --payload KERNEL --module FRESH-module/dac960rtems.ko
python3 game/raycaster/transfer/profile.py FRESH-capture
python3 game/raycaster/upload/verify_quiet.py FRESH-capture
```

Use the unchanged word-memory raycaster payload. `--coarse` omits detailed command
profiling while keeping normal diagnostic evidence and phase timing. Respect the
shared hardware lock and parallel card work. Build in a fresh isolated directory,
verify prior HTTP shutdown and full final restoration, then restore HTTP.

This is a separate opt-in bounded-session experiment. Do not propagate the string
change into flash, production networking or resident RTEMS. Pinning the exact
method/bytes is mandatory; other firmware or boards may use a different path.

## Startup regression found on hardware

The first candidate suppressed the string during OPEN and added a cache/PING
roundtrip. It passed 421 requests once, but its second opening returned four
PING statuses (`017e`) where the first STEP expected the cache callback (`017d`).
RAM table readbacks matched. The gate refused user execution and restored the
format, RAM and module normally. This is evidence of stale dispatch visibility;
no instruction/data-cache mechanism beyond that observation is claimed.

The accepted ordering keeps OPEN and the first STEP's original cache handshake
unchanged. Suppression follows that handshake without an intervening PING or
table rewrite. User callbacks are never retried. Ten consecutive four-request
sessions qualified repeated startup before the fresh comparison batch. A native
cache model reproduces the stale-PING hazard and checks the corrected ordering.
The exploratory successful run and rejected run are preserved separately.

## Accepted measurements

Five final sessions passed 2,105 native-matching replies and all restorations.
Three upload completion waits fell 32.129 → 0.368 ms (98.85%); full-frame kernel
transactions fell 55.840 → 24.141 ms (56.77%). The coarse release passed at
23.876 ms. All audits remain. [Detailed results, rejected startup and binaries](../../../artifacts/upload-20261011/README.md).
