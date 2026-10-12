# Doom milestone guidance

**New host-only cache/link checkpoint:** [runtime/cache/README.md](runtime/cache/README.md) and
[runtime/relocate/README.md](runtime/relocate/README.md). Opt-in `--wad-cache` requires `--arena-runtime`.
Only the separately allocated bounce base crosses runtime reads; zone interior
pointers stay in the owning application. Single IWAD, no rebind or reopen after
close; no general stdio/filesystem shim. Six host demos match 12,600 hashes with
1 MiB reserved image + at most 6,473,545 dynamic bytes in the 8 MiB arena.
44 engine imports remain. The REL prototype is offline-only; never bypass the
current card whitelist or infer relocation records from pointer-looking words.
Before Doom, admit/test the small relocated proof with full existing audits.

**Runtime-entry/WAD bridge accepted:** [runtime/entry/README.md](runtime/entry/README.md).
`--doom-runtime` requires `--doom-shared`. Only the exact reviewed probe may
enter through the v1 table; this is not arbitrary Doom launch. WAD staging is
separate from UPL1, maximum 512 bytes, one immutable bound file. Copy in the
owning worker after claim/CRC; keep its allocation loan until completion or
cancellation. No cross-task destination pointer, ISR copy, or implicit unpin.
Keep the host WAD query/reply inside the reentrant audit gate, retain full
audits and the 500-tick timeout, and never retry uncertain writes. The live
normal/error/timeout/recovery batch passed; STOP-in-read is native-tested only.
No Doom engine has yet run on card. Next are imports/linking and a WAD cache.

**Shared arena follow-up accepted:** read [runtime/SHARED-ARENA.md](runtime/SHARED-ARENA.md).
Use one task mutex and private per-worker allocation records; retain pins during
unlocked bulk work and reclaim only after both task/IRQ drains. Wrong-task
calls must not write diagnostics. `--doom-shared` requires `--doom-heap`.
Both workers must not block at once: idle still deliberately faults and has no
registered IRQ owner. Keep a control worker runnable or explicitly admit/test
idle ownership. Preserve full audits, exclusive reboot-only release and the
cooperative public service. Earlier single-owner notes below are historical.


Run runtime/test.py and runtime/verify_evidence.py for allocator evidence.
Read [runtime/README.md](runtime/README.md) for the allocation integration.
Opt-in --arena-runtime resolves the five allocation symbols: 631,112 static
bytes, 53 imports remain. The baseline inventory below remains historical.
The resident --doom-heap proof passed on-card; keep the single arena owner and
separate system libc. Do not expose it to another task without shared serialization.

Read [DETERMINISM.md](DETERMINISM.md), [OS-PLAN.md](OS-PLAN.md), README.md and
RAM-CONTRACT.md. The three variable frames were out-of-post sprite reads:
negative fixed-point indices wrapped to 127. Keep bounded_column.h and its
masked-dispatch bounds on both host and target; preserve wall wrapping.
Do not suppress frames, weaken comparisons or zero the heap to hide bad reads.

The current i960 relocatable engine is 627,096 bytes and has 58 unresolved
externals. It is NOT a loadable card image. Runtime code, WAD I/O and arbitrary
application task launch remain. The prior broad host allocation peak is
6,456,649 bytes, including the 6 MiB zone; never count zone contents twice.

The parallel resident-upload profile now has an accepted guarded 8 MiB arena
and an on-card contiguous 6 MiB proof. This does not automatically redirect
libc malloc or prove a final Doom memory manifest. Read residentnet/UPLOAD.md.

Keep the pinned DoomGeneric/Freedoom inputs and licenses. Host captures include
indexed pixels, RGB palettes and game-tic traces; instrumentation stays host-only.
The archived original milestone intentionally retains its old failed comparison.
Use verify_determinism.py for the new corpus, not a changed old verifier.
Finite host repeatability is not i960 correctness or all-WAD compatibility.

Do not touch the parallel RTEMS files, card owner or public service during host
work. Preserve all existing physical memory/ownership audits for target testing.
