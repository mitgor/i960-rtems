# Bounded WAD batching (N2)

`wire.c` assembles one logical read of up to 4096 bytes from up to eight existing
512-byte PIO replies. The original WAD1 ABI and original API version remain
available. Batching uses WAB1 (`0x31424157`) and the explicitly negotiated runtime
API version `0x00010001`, features 15. Its structure layout is unchanged; max_read
is exactly 4096, or 512 for a controlled comparison. Unknown combinations refuse.
The card profile requires `--wad-batch --wad-poll --dispatch-atomic --doom-engine`
and the existing owned/shared arena flags. This does not start Doom itself.

## Wire and lifetime contract

The existing request snapshot is eight words: magic, sequence, state, file ID 1,
starting offset, requested length, immutable file size, rejected count. One
logical request consumes one nonwrapping sequence. Each ordered reply is:

| Word | Meaning |
|---|---|
| 0 | WAB1 magic |
| 1 | Logical request sequence |
| 2 | Immutable file ID 1 |
| 3 | Starting offset plus fragment index × 512 |
| 4 | This fragment's byte count, at most 512 |
| 5 | Status: 0 success, 1 host error |
| 6 | CRC32 of this fragment's bytes |
| 7 | Original requested length, binding the fragment to the whole batch |

Each packet uses the existing 32-byte header and at most 512 data bytes, padded
with zeros to four bytes. The kernel's ioctl, epoch checks, word-index bounds,
uncertainty policy and paired audits are unchanged. The host obtains a request
once, then sends ordered fragments without per-fragment request snapshots. It
never retries an uncertain write. A fresh sequence is required for another read.

Control code stages fragments and checks fixed header/order/bounds; the owning
application validates **every** length, CRC, status and padding byte before
copying any destination byte. EOF alone permits a short final fragment. Missing,
reordered, duplicate or stale fragments cannot publish a partial destination.
The assembly buffer cannot be changed once ready/claimed. A failed batch leaves
cache tags/data and that batch's caller destination untouched. An earlier fully
completed batch may still form a short-read prefix, as in the old cache contract.

The application owner must be runnable and registered. The destination is an
exact allocation pinned for the requested capacity; interiors are refused.
The 4352-byte staging allocation is separately pinned until cancellation/drain.
Both loans remain held through validation and copy; staging is freed before
return. STOP/global STOP and the existing five-second total deadline cancel
partial assembly and return both loans. The deadline is not reset per fragment.
No ISR allocation, new DMA path, arbitrary task or idle ownership is introduced.

## Cache and memory

The 32 × 512-byte direct-mapped cache coalesces consecutive misses only within a
single logical read, stopping at a cache hit or eight lines. It neither reads
ahead nor increases data volume. Bounce allocation grows from 512 to 4096 bytes.
With 4352 bytes of transient staging, extra dynamic payload at a pending read is
**7936 bytes**, plus allocator alignment/metadata. Metadata remains single-owner.
The staging allocation occupies the existing 8 MiB application arena, not kernel
BSS. Small batch wire routines occupy spare space in the already protected engine
code window. Link boundaries and all bootstrap protections remain unchanged.

## Checks and measurements

`test.py` uses actual wire/runtime/allocator/loan/cache code under ASan/UBSan:
first through last fragment corruption, short reply, error, STOP and timeout;
unchanged destination on failure; staging allocation exhaustion; wrong/interior
owner; EOF; sequence exhaustion; duplicate/reordered controls; 10,000 reads and
final drain. `rtems/residentnet/test_batch_client.py` checks the real host server.
`profile.c` replays captured logical reads against real file bytes through the
actual cache and wire assembly. Host profile opt-in is
`DOOM_WAD_BATCH_BYTES=4096`; this changes the older host engine/cache adapter,
not the private Newlib engine ABI accepted on the card.

For the first-frame trace, 2183 logical reads and 13,804,084 delivered bytes match
exactly: **27,648 → 4,747 requests**, still 27,648 payload fragments and 14,155,460
wire data bytes. This removes request-snapshot overhead; it does not eliminate
PIO per-word data transfer. The six host demos also retain all 12,600 frame hashes.
Physical timing and acceptance status belong in the [evidence record](../../../../artifacts/notes/doom-batch-20261012.md).

The closed cache probe has command 20 for 4096-byte batching, command 22 for the
same WAB1 workload at 512 bytes, and command 21 for its eight-word counters.
Each entry uses owned invocation generation/STOP handling and the same exact
relocated code whitelist. Existing engine preflight still uses its accepted
512-byte ABI/image. Selecting batching in the private engine's runtime binding
and building a newly authenticated engine image belongs with the next bounded
initialization milestone; do not silently substitute it into the accepted image.
