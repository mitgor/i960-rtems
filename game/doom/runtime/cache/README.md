# Single-IWAD cache and engine backend

## Current cache-copy implementation (2026-10-15)

The engine backend supports 512-, 4096- and 65536-byte negotiated reads; ring
mode uses 128 cache lines and one aligned 64 KiB read-ahead window. The older
milestones below describe how this evolved, not the current maximum geometry.

All three data-copy sites use the same exact-bounds helper. Equally aligned
source/destination pointers use a byte prefix, aligned 32-bit words and a byte
tail. Unequal alignments use bytes. This never reads beyond a short EOF line,
requires no unaligned i960 accesses, and preserves metadata publication after
the successful copy. Source and destination are distinct owned allocations;
the helper is not `memmove`. DMA pinning, cache policy and all full audits are
unchanged. `rtems/dma/wad_ring/test_cache.py` tests exact allocation edges,
all alignments and multi-window reads under ASan/UBSan with profiling off/on.

Physical results and matched baseline: [cache-copy evidence](../../../../artifacts/notes/wad-copy-20261015.md).

**Original host/cross-build milestone; the cache bridge now also passes a
closed card probe.** The complete
DoomGeneric engine uses this backend in six 2,100-frame host runs. All 12,600
pixel/palette/tic hashes match the accepted corpus. The card remains on the
original public service. [Evidence](../../../../artifacts/notes/doom-cache-20261012.md).

## Ownership and read behavior

`cache.c` wraps runtime ABI v1 with 32 direct-mapped 512-byte lines: 16,384 bytes
of cache, a separately allocated 512-byte bounce buffer, and 300 bytes of
metadata on the 32-bit host ABI. Only the exact bounce allocation crosses the
runtime read API. Validated bytes are copied into the cache, then into the
owning application's destination, including interior pointers into Doom's zone.
The runtime still pins the bounce allocation during a host read. Both cache
allocations belong to the same private application namespace. Metadata is
single-task; this adds no new shared ownership or IRQ caller.

A cache line becomes valid only after an exact successful read, allowing a short
line solely at file EOF. Failed/short reads do not publish a partial line. A
multi-line read can return its completed prefix on error; Doom sees a short
read and follows its existing error path. `last_error` preserves the cause.
Offset bounds use subtraction to avoid unsigned overflow. Cache hits do not
call the host. Diagnostics are unsigned 32-bit counters, not unbounded totals.

Close/reentrant reads refuse while an operation is active. The application must
not free the destination or close the backend until its read completes. Existing
STOP task/IRQ drain still governs final arena reclamation. Native tests combine
this cache with the actual runtime mailbox, allocator and loan code; card tests
of this added layer remain a future gate. The previously accepted runtime read
service itself is unchanged.

`backend.c` replaces only Doom's WAD file class under `--wad-cache`. It admits
one explicitly bound path, one open file, and read-only offset access. It cannot
open a second WAD, rebind identity, or reopen after close; a stale descriptor
therefore cannot become valid again. It does not implement general filesystem,
config/save writes, file discovery, or stdio. Remaining engine imports still
need real implementations or explicit unsupported policies. No successful
filesystem stubs were introduced.

The host test adapter snapshots the file into read-only host memory outside the
simulated card arena. Cache and bounce allocations use the actual Doom arena.
Host-only read traces and statistics do not enter the target build.

## What the measurements say

The 32-line cache requires 28,229–30,610 wire reads across the six demos. Against
an independent uncached exact-512-byte model, this is a few percent fewer
requests but slightly **more** bytes due to aligned reads. Simulations from 8 to
512 lines show little extra benefit from a larger cache, so 16 KiB remains the
initial setting. This is an ownership/correctness bridge, not a card throughput
claim. WAD transfer batching and startup latency remain important work.

The host profile now reserves **1 MiB** for the future image, replacing its old
640 KiB reservation only when `--wad-cache` is enabled. Maximum dynamic use is
**6,473,545 bytes**, including cache/bounce and the 6 MiB zone. Together this is
**7,522,121 bytes**, leaving 866,487 bytes of the 8 MiB budget before allocator
guards/alignment and unimplemented costs. Stacks/network/kernel memory use their
separate admitted regions. This is a finite-workload budget, not a final target
memory manifest or an all-level/mod guarantee.

Run `test.py` for ASan/UBSan cache/backend checks and `../entry/test.py` for the
actual runtime/loan integration. Build Doom with `--arena-runtime --wad-cache`.
`../run_host.py` compares frame hashes and records logical WAD reads;
`analyze.py` independently replays the cache, including alternatives.
`verify.py` checks an extracted evidence archive against the tracked corpus.


## Physical bridge follow-up

A 1,760-byte, eleven-relocation probe executes this exact cache implementation
through the runtime table on existing worker 1. It checks cached repeats,
cross-line copies into an interior destination, EOF, CRC/short/error/timeout and
fresh-entry recovery. All full paired audits and the earlier runtime/relocation
proofs remain enabled. The two normal entries require seven wire reads each and
take 13.218/11.608 seconds under audits; this is correctness acceptance rather
than an engine startup-speed result. STOP-in-read and same-cache retry remain
native coverage; physical STOP followed the completed entries.
[Exact evidence](../../../../artifacts/notes/doom-platform-20261012.md).

New runtime builds include only the closed reviewed cache image in command 15.
It receives the ordinary segmented CRC/cache/pin checks, then an exact-byte gate
and trusted relocation sites. Post-entry code bytes must still match, the
original template is restored, and cache synchronization precedes completion.
The new private Newlib engine candidate is link-complete but remains outside
this whitelist. Do not use a successful cache probe as engine admission.

## N2 batching

The cache also accepts the explicitly negotiated batch API (version 0x10001,
features 15, max_read 512 or 4096). Adjacent misses within a logical read are
coalesced, stopping at hits or eight lines; there is no speculative read-ahead.
The legacy v1/512 adapter remains supported. Host testing opts in with
`DOOM_WAD_BATCH_BYTES=4096`; card builds use `--wad-batch` and the separately
admitted cache probe. See [protocol](../batch/README.md) and
[evidence](../../../../artifacts/notes/doom-batch-20261012.md). A new authenticated
engine image must explicitly bind this API before actual Doom benefits on-card.
