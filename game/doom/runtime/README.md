# Doom arena libc integration

This step implements the allocation portion of Doom's runtime: `malloc`,
`calloc`, `realloc`, `free` and `strdup`, through namespaced `doom_*` symbols.
It borrows the resident upload service's **existing 8 MiB arena**. It does not
initialize a second allocator over that RAM or replace the system libc heap.
Other libc, compiler helpers, WAD I/O, task launch and target Doom remain open.

## Ownership contract

`doom_heap_init` attaches zero-initialized, caller-owned metadata to an already
admitted `struct arena`. Metadata is outside the application arena. Initialization
is once per lifetime; resetting metadata never releases a running or poisoned
application. All arena users must share the same serialization discipline.
The caller's enter/leave hooks must refuse ISR/wrong-task calls and serialize
metadata work without masking interrupts for bulk copies. The progress hook runs
outside that lock after at most 1,024 copied/cleared bytes and can cancel work.

The resident proof uses the existing **single upload worker**, not a new mutex:
worker 1 alone accesses loader/application allocations. The ISR handles only the
mailbox. Cleanup runs after both workers and their owned IRQ contexts drain.
The small lock flag detects accidental reentry; it is **not a general multi-task
lock**. Before arbitrary Doom task launch, route arena calls through this owner
or supply and test one shared task lock across loader and application clients.

Every allocation holds an arena generation handle and an application pin until
free. Exact-pointer/length/handle validation precedes release. Extra external
pins refuse free/reallocation/drain. Busy source and destination records protect
unlocked bulk work; cancellation frees only the unpublished destination and
preserves the original realloc pointer. Corruption or failed reentry leaves
uncertain allocations retained. `doom_heap_drain` is legal only after the caller
has proved every application/consumer/IRQ context has drained, not merely after
setting STOP. It prechecks all extra pins before releasing any allocation.

Zero-size malloc/calloc returns a freeable one-byte allocation. `realloc(p,0)`
frees p and returns NULL. Overflow/OOM returns NULL; failed nonzero realloc keeps
p and its contents. `free(NULL)` is harmless; invalid/busy free through the libc
shim invokes the bound fatal handler. Corruption poisons the context/arena.
The context API returns diagnostic status so tests can exercise refusals.
Raw C pointers retain normal C lifetime requirements; generation handles do not
make stale application pointers or arbitrary writes safe.

`doom_libc_bind` binds one application context before engine entry, once per
resident lifetime. Bind a non-returning fatal handler. The engine's allocation
symbols are renamed only with `build.py --arena-runtime`; resident/system libc
continues using its established 171,824-byte heap. No errno/newlib reentrancy or
stdio ABI is claimed by this allocation-only shim.

## Tests and memory

Native ASan/UBSan tests exercise all 128 slots, 5,000 fragmented allocations,
6 MiB calloc with a 640 KiB image reservation and other buffers, grow/shrink,
failed realloc preservation, multiplication overflow, zero size, invalid pointers,
extra pins, metadata/redzone corruption, and STOP during copying/clearing.
The actual resident mailbox/core also runs the opt-in proof under sanitizers.

The 32-bit host engine runs six 2,100-draw demo cases through this allocator:
**12,600 frames match the accepted pixel/palette/game-tic SHA-256 corpus** and
all six heaps drain. Each run reserves **655,360 bytes** for engine storage,
allocates a contiguous **6,291,456-byte zone**, and reaches 13 live libc blocks.
Phase 1's direct peak is 6,444,133 bytes; Phase 2's is **6,456,649 bytes**.
The host still supplies files, formatting, time and other unimplemented services;
this is not a host simulation of the whole RTEMS runtime.

All 80 i960 engine units plus the three runtime/core units compile and combine.
The resulting relocatable object is **631,112 bytes**: 310,960 text, 69,888 data,
250,264 BSS. **53 unresolved externals** remain, down from 58. The adapter context
is caller-provided metadata outside that object; the resident image's linker and
RAM audit account for its actual placement. The 640 KiB host reservation is a
conservative placeholder, not a final executable manifest or card entry address.

## Resident test mode

`rtems/build.py --doom-heap` requires `--resident-upload`, which requires the
exclusive owned-RAM profile. It adds reviewed test command **8** to UPL1; ordinary
profiles and command 7's original proof remain unchanged. Command 8 uses all five
libc functions beside a pinned uploaded image, verifies a zeroed 6 MiB zone,
checks grown-buffer contents and failed-realloc preservation, rejects overflow,
and retains a patterned 64 KiB allocation until STOP. Successful reply value is
`444c4942`. Upload finish checks that retained buffer completely, drains the Doom
heap after the task/IRQ drain, then proves the shared arena empty with the existing
image, guard, reserve and protected-page checks intact.

The opt-in code lives in the protected upper loader section, preserving the
128 KiB monitor limit. `live.py --doom-heap` checks the image's build flag;
`verify_upload.py --doom-heap` replays command 8 through the actual adapter/core.
No arbitrary code launch, flash update or broader RAM ownership is added.

## Reproduction

```sh
python3 game/doom/runtime/test.py
python3 rtems/residentnet/test_upload.py
make -C rtems test
python3 game/doom/build.py --work /path/to/cross --archive /path/to/doomgeneric-source.tar.gz --target i960 --arena-runtime
python3 game/doom/build.py --work /path/to/native --archive /path/to/doomgeneric-source.tar.gz --target host32 --arena-runtime
python3 game/doom/runtime/run_host.py --binary /path/to/native/host32/doom-profile --reference /path/to/accepted/runs --wads /path/to/freedoom-0.13.0 --out /path/to/fresh-results
```

Pinned inputs and the reference corpus are in the previous Doom artifact folders.
[This step's exact builds, captures and physical findings](../../../artifacts/doom-runtime-20261012/README.md)
record what actually passed. Read that evidence before hardware use; exclusive
resident tests retain resources until reboot and must not overlap another owner.
