# Application runtime entry and host-backed WAD reads

This is the next bridge from the accepted shared 8 MiB arena to Doom. It is a
reviewed uploaded application probe, not a Doom executable or a general ELF
loader. The application runs on existing worker 1. Worker 0 stays runnable and
services network/control traffic; this does not admit an idle IRQ context.

Physical acceptance passed; see the [exact captures and measured results](../../../../artifacts/notes/doom-entry-20261012.md).

## ABI v1

`api.h` defines `DRT1`, version `0x00010000`, features 7. On i960 the table is
96 bytes: eighteen 32-bit scalar words, four function pointers, two reserved
zero words. The scalar words carry the ABI shape, 8 MiB arena size, maximum
512-byte read, immutable file ID/length and SHA-256 identity. Pointer offsets are
72 (allocate), 76 (release), 80 (nominal milliseconds), and 84 (read).

The caller validates the exact version/size and pointer width before use. This
is a trusted-code ABI, not a sandbox. Newlib's system heap remains separate.
Allocation uses the task-owned Doom namespace; callers cannot release another
worker's allocation. The clock derives from the existing 10 ms RTEMS ticks.

The first application has no globals, static data or external imports. The
cross-build requires identical bytes at two link addresses, zero data/BSS, and
no unresolved symbols. Entry accepts only that exact reviewed byte sequence in
one RX segment. The normal segmented loader still checks geometry, CRC,
zero-fill, cache synchronization, generation handles and live image pins. It
calls the probe with the table and expects a bounded return. Arbitrary binaries
are not admitted by this command.

## Read contract and lifetime

The host reads one WAD into immutable Python bytes before binding it once. The
card can request only file ID 1, offset and length, never a pathname. Requests
are limited to 512 bytes; EOF can shorten a read. A successful reply must contain
exactly the requested bytes up to EOF. Short non-EOF data, wrong sequence,
wrong file/offset, malformed lengths, CRC failure and nonzero padding are refused.
SHA-256 identifies the host snapshot; CRC detects chunk corruption. This is not
cryptographic authentication of an untrusted host.

`read` takes an exact base pointer in the caller's allocation namespace. It pins
that allocation with one outstanding loan and a monotonically increasing loan
token. Free, resize and drain refuse while borrowed. Tokens are never reused
within the namespace lifetime; exhaustion refuses new loans. A stale return
cannot release a later loan. Zero-length/EOF reads do not touch the destination.

A separate 544-byte WAD mailbox leaves the UPL1 command reply intact while entry
runs. Control context accepts bounded words and fixed header checks only. The
application claims the staging buffer, checks payload CRC/padding and copies
with interrupts enabled. Replies cannot modify staging while claimed. Only
worker 1 copies into its own destination; there is no cross-task raw pointer
copy or DMA. It releases the loan after completion or cancellation. A failed
loan return is fatal and retains ownership rather than pretending to reclaim.

Read results: nonnegative byte count; `-1` invalid input/admission; `-2` bad
payload; `-3` host read failure; `-4` timeout or STOP while waiting; `-5` fatal
loan-release failure. STOP observed after claiming also returns a negative
result without copying. Waiting is bounded to 500 nominal ticks (5 seconds),
with worker 1 yielding and worker 0 runnable. Final reclamation still requires
the existing task/IRQ drain proof. Native tests cover STOP during a read; the
physical batch covers timeout followed by successful reads and ordinary final
STOP, not a separately timed STOP-in-read injection.

UPL1 commands: 10 bind eleven words (`WAD1`, file ID, size, eight SHA words);
11 reviewed entry; 12 indexed runtime diagnostics. WAD ioctl operations 3/4
query/answer the separate mailbox, using the same session mutex, epoch and
uncertain-operation retention policy as existing upload/network commands.

## Validation and next step

`python3 game/doom/runtime/test.py` checks allocation loans and the portable WAD
state machine under ASan/UBSan. `python3 game/doom/runtime/entry/test.py` executes
the real runtime/allocator/probe logic with deterministic host replies, including
CRC, short read, host failure, timeout and STOP. The physical harness uses the
pinned Freedoom 0.13.0 `freedoom1.wad`, with header, directory and tail reads and
an independent FNV oracle. `verify_upload.py --doom-runtime --wad PATH` replays
captured replies through the actual C runtime and checks the WAD bytes separately.

Next is an application image link/relocation strategy plus the remaining
libc/compiler imports and a bounded WAD cache. The probe's table does not yet
replace Doom's `open/read/lseek`, stdio, startup or renderer integration. Keep
this profile opt-in and preserve all full paired audits.
