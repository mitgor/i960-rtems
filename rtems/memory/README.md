# Word-copy and clear helpers

**Card-validated:** 2,105 native-matching replies across five restored sessions.
Copy is 3.30× faster and clear 4.63×; full-frame kernel time fell 3.91%.
[Measurements and preserved evidence](../../artifacts/notes/word-memory-20261011.md).

`word.c` implements RAM-only `memcpy` and `memset` using aligned 32-bit loads
and stores. The raycaster's isolated target builder selects these by default;
`--memory byte` selects the original byte helpers for comparisons. Other RTEMS
profiles, the production network service and their interrupt/ownership paths
continue to use their existing helpers.

## Contract

- Copy uses words only when source and destination have the same address modulo
  four. It consumes a byte prefix to align both, whole words while at least four
  bytes remain, then a byte tail. Different alignments use the byte loop.
- Clear expands the low eight bits of its `int` argument into a 32-bit word,
  aligns the destination with bytes, writes words, then handles the tail.
- Neither helper accesses bytes outside the requested interval. Zero length
  accesses no memory. Both return the original destination.
- The `may_alias` word type permits accesses to arbitrary object representations
  with GCC/Clang strict aliasing enabled. A compile-time check requires a 32-bit
  unsigned int; supported builds use ILP32 i960 or LP64 native hosts.
- `memcpy` callers still require nonoverlapping ranges. The retained `memmove`
  implementation uses forward copy for destination-before-source and backward
  bytes otherwise; the forward algorithm is safe for that internal use.
- These are ordinary RAM operations, not MMIO, cache maintenance, atomic stores,
  DMA synchronization, or a replacement for volatile register accesses.

No loop unrolling, wide unaligned accesses, or speculative reads are used.
The i960 GCC 3.3.6 build emits `ld`/`st` in the copy body and `st` in the clear
body. All external callers retain the existing C ABI and `-fno-builtin`.

## Validation

```sh
make -C rtems/memory test
make -C game/raycaster test
python3 game/raycaster/build_target.py --work FRESH --sources ARCHIVES \
  --memory word --memory-check
```

The native test renames symbols so sanitizer/system libc operations cannot
accidentally exercise or replace the implementation under test. It checks
33 lengths (zero, every length through 17, word/block boundaries and 4095–4097),
all 8×8 source/destination offsets, return values, source preservation and all
surrounding sentinel bytes. That gives 2,112 copies, 2,112 overlapping/equal
moves and 1,056 clears (eight offsets × four values × 33 lengths). Values include
zero, 255, 0x123 and -2. Separate inaccessible guard pages check beginning/end
boundaries for 513 lengths and both equal/different pointer alignments.

The `--memory-check` target runs the exact same reference/sentinel checks in
264 bounded batches, one before each of its first 264 raycaster requests. Any
failure escapes via `bounded_fatal` before a successful application reply; a
complete native-matching trace of at least 264 requests therefore establishes
that every batch passed. The guard-page tests are native-only. The card has no
corresponding per-buffer page protection. The checking image has three extra
4,160-byte buffers and is kept separate from the measured optimized image.

Use the existing exclusive card lock, full audit cadence, restoration verification
and exact payload/module capture process. Do not run card tests during another
chat's hardware experiment. Profile separate `--memory byte` and `--memory word`
builds with the same driver and requests, preferably in byte/word/word/byte order.
The raycaster profiler reports host command intervals and differential estimates,
not instruction cycles or raw PCI bandwidth. See the artifact report for actual
hardware acceptance and measurements.
