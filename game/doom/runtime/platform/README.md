# Private Doom Newlib/platform candidate

## i960-specific Doom port boundary (2026-10-18)

The pinned DoomGeneric renderer remains shared source. This directory is its
i960 application port: private Newlib 1.11.0, soft-float ABI, owned allocator,
WAD read bridge, input, framebuffer and RTEMS runtime callbacks. The build
records a physical `card_profile`, but CPU-independent engine code does not
contain board register addresses. The old PG and new AcceleRAID wall clocks
are linked from `card_clock_dac960pg.c` and `card_clock_accele160.c`
respectively. Frame/WAD transport and RTEMS boot/linker stay in each card's
own implementation; see [the profile contract](../../../../card_profiles/README.md).
This is the reusable i960 port for another board once its measured adapters
pass ownership, timing and full system audits.

**Current checkpoint — 2026-10-12:** the full-engine-linked diagnostic preflight
is physically accepted, including normal / STOP / normal, exact admission and
post-return code checks, contiguous 6 MiB allocation and complete drain at tick
100,085. Full capture replay now passes. This supersedes the earlier pending
entry/dispatcher gates below, retained as development history. Doom itself has
not initialized on-card. Next: validated WAD batching, bounded initialization,
first-frame verification and browser controls. [Evidence](../../../../artifacts/doom-progress-20261012/README.md).

This is an offline link and runtime-semantic gate. The engine candidate now
resolves the previously missing libc/platform imports, using pinned Newlib
1.11.0 sources and the actual soft-float compiler archive. A successful final
link is not card execution or executable admission. The current UPL1 whitelist
still accepts only the reviewed proofs.

## Isolation and supported behavior

`build.py` compiles a selected Newlib archive, records every source hash and
command, then renames its defined libc/port symbols and their references.
Engine references are renamed with the same map. Newlib's reentrancy object,
errno, ctype table, streams and allocation calls therefore belong to the
application. Neither kernel stdio nor the kernel heap is overridden. Compiler
archive references to libc, such as abort, use the same private mapping.

The application port is single-owner and binds the exact runtime ABI v1 once.
It uses that table's allocation/release functions over the existing shared arena;
it does not initialize another allocator over the card RAM. A bounded 128-record
client ledger supplies size checks for calloc/realloc and permits bulk copying
without borrowing an interior pointer. Failed realloc preserves the old block.
The table's existing task-owned allocator remains responsible for guards, pins
and ownership. The client ledger and kernel heap metadata are different layers. `strdup` and
its reentrant wrapper use the caller-owned allocation path: Newlib otherwise
routes them through `_malloc_r`, which would misclassify a returned string as
private internal storage. Finish must refuse that live caller-owned string.

Read-only stdio admits four live descriptors for one exact immutable IWAD path.
IDs are not reused and stop before Newlib's signed 16-bit FILE descriptor field
can overflow. Open/seek/read/EOF, stdio buffering and error flags use actual
Newlib code. Reads go through the existing 16 KiB cache and exact 512-byte bounce
allocation. Unknown paths return ENOENT; writes/create/truncate, mkdir, remove and
rename fail with EROFS; system fails with ENOSYS. There is no successful fake
save/config write or shell execution. This stdio cache is separate from the
engine WAD-class cache and is accounted for if both are live.

Formatting/scanning, float conversion, 64-bit numbers, strings and ctype use
real Newlib routines. `fabs` masks the IEEE sign bit, including signed zero.
One upstream Newlib defect is patched in a build-local copy: `%lln` used
`quad_ptr_t *` although `quad_ptr_t` is already a pointer. The corrected
indirection is recorded with before/after text and hashes; shared upstream
sources remain untouched. The native i386 setjmp build uses Newlib's
`_I386MACH_ALLOW_HW_INTERRUPTS` hosted setting so longjmp does not execute
privileged CLI/STI. The i960 assembly is unchanged. The separate owned-runtime proof now tests it
on the card; the larger preflight is documented separately.

Platform hooks retain real bounded output: 4 KiB log ring with explicit drop
counts, the latest 320×200 indexed framebuffer and 768 RGB palette bytes with
hashes, a 32-event key queue, and the actual runtime clock. The v1 fallback sleep waits on that preemptible clock. An owned bind uses
bounded RTEMS waits and owner-safe STOP handling.
Consumers may copy output only under this application's owner/lifetime contract;
no concurrent browser publisher is admitted here.

`doom_platform_call` arms the private setjmp/longjmp exit boundary. Exit records
status and returns to that owner; it does not implement a general process exit
or libc atexit facility. The owner must perform teardown. `finish` refuses live
file descriptors, active invocation, or caller-owned outstanding allocations,
closes private standard streams, frees remaining private Newlib internal storage,
and retires the context. It never resets live metadata to simulate cleanup.
This cleanup is native-tested; future card entry must also prove task/IRQ drain.

## Build and tests

Build the engine with `--arena-runtime --wad-cache --platform-runtime --target
i960`, then build the private port against that object and the same extracted
engine headers:

```
python3 game/doom/runtime/platform/build.py --target i960 --engine ENGINE/doom-engine.o --newlib NEWLIB --doom ENGINE_SOURCE --out PRIVATE
python3 game/doom/runtime/platform/pack_engine.py --build PRIVATE --out RELOCATION --cross /home/mit/i960/tools/bin/i960-coff-
```

The native test uses the same Newlib/port sources at 32 bits and the actual
arena/heap core. It does not interpose on the host's libc:

```
python3 game/doom/runtime/platform/build.py --target host32 --newlib NEWLIB --doom ENGINE_SOURCE --out NATIVE
python3 game/doom/runtime/platform/test.py --build NATIVE --newlib NEWLIB --doom ENGINE_SOURCE
```

Tests cover formatting/truncation/scanning/%lln, allocation/overflow/failed
realloc, immutable stdio cache/EOF/error paths, explicit unsupported operations,
frame and palette bytes, key/log bounds, clock wait, exit and full heap drain.
The same checks also pass with the entire private library and port built under
ASan/UBSan (`--sanitize` on the host32 build). They are platform-unit tests,
not complete Doom gameplay under this libc.
The existing host Doom corpus remains the prior allocation/cache profile.

## Next admission gates

The [owned runtime](../owned/README.md) supplies real RTEMS yielding and
invocation STOP; its small physical proof accepts the pinned i960 exit boundary.
The [larger gate/preflight](../engine/README.md) supplies exact-build image and
metadata admission, owner binding and diagnostic teardown. Actual private-libc
preflight and the corrected retained-buffer layout pass 32-bit native sanitizers.

The physical larger batch refused modified code/metadata but stopped at timer
ISR slot rejection before clean entry. Keep it opt-in and investigate that
registered-owner/active-continuation path before claiming physical acceptance.
See [captures and reproduction](../../../../artifacts/notes/doom-engine-20261012.md).

Then measure and batch WAD initialization reads, add reviewed engine startup,
tic safe points and complete engine allocation cleanup, and recompute the image,
zone/cache/allocator/stack peaks. Compare the first real Doom frame with the
established host oracle before browser input and endurance. The known-pattern
preflight framebuffer is not a Doom frame or a startup performance result.

### Selective private memory speed build

`build.py --fast-memory` compiles only pinned Newlib `memcpy.c` and `memset.c`
with `-O2 -fno-strict-aliasing` after the normal `-Os` flags. This enables their
existing aligned-word implementations; unaligned copies retain the byte path.
All other private-library units and the engine keep their existing flags. Symbol
namespacing and allocation ownership are unchanged. The top-level
`game/doom/play/build.py` forwards the same option; admission records
`fast_memory` in its manifest. This does not optimize the explicit byte loops
in the platform's `calloc`/`realloc` implementations.

Run `test_fast_memory.py --newlib PATH` on Linux with the 32-bit sanitizer runtime.
It tests the actual pinned source, all pointer alignments 0–7, copy lengths
0–4096, every fill byte and lengths 0–1024, and exact guard-page ends. Native
engine replay and target assembly inspection remain required; native timings
are not evidence of i960 speed. Hardware results are recorded in
`artifacts/notes/release-priority-20261015.md`.
