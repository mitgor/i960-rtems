# Single-IWAD cache and engine backend

**Host/cross-build milestone, not a new card acceptance.** The complete
DoomGeneric engine uses this backend in six 2,100-frame host runs. All 12,600
pixel/palette/tic hashes match the accepted corpus. The card remains on the
original public service. [Evidence](../../../../artifacts/doom-cache-20261012/README.md).

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
