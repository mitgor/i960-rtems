# Guarded arena and segmented image prototype

2026-10-12: native sanitizer tests and three bounded tests on the actual i960 card
passed. The second test executed copied position-independent code which read a
separately loaded data segment. All runs restored staging RAM and unloaded the
probe. [Evidence](../../artifacts/notes/segmented-loader-20261012.md).

The original core rehearsal used **3,728 bytes in the BIO output grant**.
The subsequent [resident integration](../../rtems/residentnet/UPLOAD.md) now uses
this core in RTEMS with an explicitly guarded 8 MiB arena, resident PIO upload,
and an on-card contiguous 6 MiB allocation proof. It is opt-in and does not change
libc malloc: that existing heap remains 171,824 bytes. The original core captures
below are historical evidence, not the full resident acceptance record.

## Arena contract

`arena_init` accepts an already admitted, 16-byte-aligned buffer and length.
It does not establish hardware ownership. Metadata must be outside that buffer;
initialize it once per lifetime, never to clear a live or quarantined session.
The caller owns serialization, interrupt policy and the metadata itself.

The arena supports 128 live allocations, 16-byte alignment and prefix/suffix
redzones. Handles combine a slot with a 24-bit generation; exhausted generations
retire the slot rather than wrap. Allocation finds gaps without embedding free
list pointers in user memory. A damaged extent or redzone poisons the arena.
Metadata validation checks bounds before touching allocation redzones.

A pin protects lifetime. Cancel blocks new pins but preserves existing pointers;
release requires all pins to be explicitly retired. Cancellation is not evidence
that a CPU, task, DMA engine or interrupt has stopped using memory. The caller must
prove completion before unpinning. Unknown completion requires retention.
Handles are not security capabilities: trusted code with raw RAM access can bypass
these checks, and the caller must not reset/copy metadata or retain released pointers.

All operations have fixed metadata bounds, but some scans are quadratic in 128
slots. Do not put them under a long interrupt mask in RTEMS without measuring it.
This API supplies allocation/pinning/release; libc calloc/realloc, shared-task
reference accounting and interrupt-latency instrumentation still need adapters.
The existing RTEMS allocator and shared-reference implementation remain intact.

## Segmented image contract

`seg_begin` accepts ABI 1 and up to eight **relative** segments in one allocation.
It checks extents, overflow, overlap, alignment, flags, and an entry in initialized
RX bytes. Segments are RX or RW; executable segments are whole words and have no
zero-fill tail. There are no absolute destination writes, relocations or imports.
Images must be position independent. The ABI identifies this manifest contract,
not a completed RTEMS runtime symbol table.

`seg_write` accepts sequential offsets within each segment, up to 1,024 bytes per
call. Duplicate, skipped, oversized and out-of-range writes fail. The caller must
supply valid source buffers. After all file bytes arrive, `seg_prepare` rereads
at most 1,024 bytes for CRC32 or zeroes at most 1,024 BSS bytes per invocation.
CRC32 covers initialized bytes and detects accidental corruption; it is not an
authentication mechanism. After all segments pass, a required platform hook
synchronizes caches for each RX range before READY is published. Hook work must
also be bounded by the platform. No transport retry/epoch semantics are implied.

The entire image remains pinned through LOADING, VERIFYING, READY and RUNNING.
`seg_start` returns an entry address; the caller supplies the execution context.
Cancellation during execution changes state to CANCELLING and preserves storage.
Only `seg_complete`, after every execution context has drained, may retire it.
Checksum/cache uncertainty or `seg_uncertain` quarantines the image permanently
for this arena lifetime. It cannot be restarted, cancelled away or reused.
RX/RW are loader policies, not hardware memory protection.

## Reproduction

```sh
python3 loader/segmented/test.py
make -C loader test
# Linux host with pinned i960 toolchain; building does not touch hardware:
python3 loader/segmented/build_card.py --out /path/to/target
```

`card_test.c` uses only the BIO output window for metadata and arena storage.
`card_code.s` is the tiny position-independent test program. The card test loads
RX code and RW data/BSS, executes the code against the data, requests cancellation,
checks that pinned release fails, confirms completion, then rejects the stale
handle. The BIO result contains SEG1, test status, computed result, prepare-step
count and arena size, followed by zeros. Its caller verifies full staging
restoration. This cooperative rehearsal must not run during exclusive RTEMS.

## Integration history and remaining gates

Items 1–2 and the resident mailbox in item 4 are now implemented by the
[resident profile](../../rtems/residentnet/UPLOAD.md). Libc/task adapters, arbitrary
application execution and larger endurance remain. The original ordering follows.

1. Inventory/protect the high tail excluded from the current large-RAM hashes.
   Define separate grants for runtime, application arena, executable storage and
   monitor/transport; replace reserve pattern checks only for granted bytes.
2. Decide bootstrap placement. The accepted resident image has only 1,456 bytes
   of immutable-code headroom; this prototype cannot simply be linked there.
   Use a reviewed staged layout or recover sufficient space with size assertions.
3. Connect the arena to RTEMS task ownership and shared cancellation. Test a live
   6 MiB allocation plus other consumers, OOM, large clears/copies and IRQ latency.
   Decide libc adapters and allocation-slot budget from Doom's actual trace.
4. Add a resident PIO upload service with image identity, epochs, bounded commands,
   disconnect/STOP behavior and independent capture/replay. No stock callback
   after takeover. The current test exercises the core locally, not host streaming.
5. Add relocations or a defined PIC/toolchain strategy, runtime imports and owned
   task creation. Test larger code/data, cross-segment calls, execution faults and
   uncertain completion before Doom. Keep the cooperative alternative available.
