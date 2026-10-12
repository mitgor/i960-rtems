# Doom milestone guidance

**Private Doom runtime/cache checkpoint (2026-10-12):** the new private
Newlib/platform candidate has **zero unresolved imports**, a 752,804-byte
code/data/BSS span and 13,113 relocations matching three independent links.
The full private 32-bit library/port passes ASan/UBSan. It does not override
kernel libc and is not admitted for engine launch. The separate 1,760-byte
cache probe passed real i960 execution: both normal hashes matched, cached
repeats made no extra reads, and CRC/short/error/timeout/recovery passed.
Full audits, six network rounds/812 packets, 625-command replay, 48 evidence
mutations and STOP drain at tick 17,855 passed. The upper loader uses 25,312
bytes with unchanged boundaries. Explicit Doom object suffixes fix a linker
wildcard that depended on the workspace name. Public IPv6 HTTP is restored (200).
Next: owned engine entry/yield/STOP and i960 exit boundary, larger manifest
admission, WAD batching/initialization budget, then first frame. Keep the current
closed whitelist; **Doom itself has not run on card**.
[Runtime contract](../../game/doom/runtime/platform/README.md) ·
[Physical evidence](../../artifacts/doom-platform-20261012/README.md).

**Relocated code/data/BSS proof accepted (2026-10-12):** the reviewed 184-byte
image executed twice at `0xc02d0050` inside the shared arena, returning
`1228486293` both times. Six trusted relocation sites, 128 zero-filled BSS bytes,
all 32 resulting counters and initialized code/data were checked. Eight admission
refusals, all paired audits, six network rounds and STOP drain at tick 14,903
passed. Native replay covers 593 requests / 1,511 upload ioctls; 24 snapshot,
eight WAD and seven relocation evidence mutations are rejected. TCP replay now
separates reused port tuples only after captured closure and a fresh SYN; gaps,
conflicting retransmissions and echo mismatches still fail. The exact card
build is archived. This is a closed returning proof, **not Doom execution**;
44 engine imports remain. Next: libc/platform imports and i960 cache/runtime
integration, then bounded initialization. Preserve both worker owners, pins,
full audits, and exclusive reboot-only release. The reboot completed and the
original public IPv6 HTTP service is restored (independent HTTP 200).
[Contract](../../game/doom/runtime/relocate/README.md) ·
[Evidence](../../artifacts/doom-relocate-20261012/README.md).

**New host-only cache/link checkpoint:** [runtime/cache/README.md](runtime/cache/README.md) and
[runtime/relocate/README.md](runtime/relocate/README.md). Opt-in `--wad-cache` requires `--arena-runtime`.
Only the separately allocated bounce base crosses runtime reads; zone interior
pointers stay in the owning application. Single IWAD, no rebind or reopen after
close; no general stdio/filesystem shim. Six host demos match 12,600 hashes with
1 MiB reserved image + at most 6,473,545 dynamic bytes in the 8 MiB arena.
44 engine imports remain. That REL checkpoint was host-only; the small proof is now accepted above.
Never bypass its closed card whitelist or infer relocation records from
pointer-looking words. Doom engine admission remains separate work.

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
