# Doom allocation-runtime acceptance — 2026-10-12

**Implemented and tested on the card:** namespaced malloc/calloc/realloc/free/
strdup borrow the resident loader's existing 8 MiB guarded arena. The system
libc heap stays unchanged. No Doom game code has run on-card; the remaining
53 imports, WAD service and arbitrary application task launch are separate work.
[Contract and reproduction](../../game/doom/runtime/README.md).

## Physical result

Opt-in `--doom-heap --resident-upload --owned-mib 12`, with the established
exclusive ownership flags, passed alongside six concurrent dual-stack rounds.
Kernel SHA-256:
`3a791f754316503846e3d6d40f8e448c7f3b3969a7bd415d28b39455fa162d7f`.
The original monitor still fits its immutable window. Upper protected loader
code grows to **10,160 bytes**; runtime BSS ends at **c0f89d60**, below its
c0f94000 code placement. The payload is 436,144 bytes.

Command 8, issued while the uploaded image was pinned, passed a zeroed 6 MiB
calloc, allocation, 128,000→196,608-byte realloc/content preservation, failed
8 MiB realloc preserving the old block, overflowing calloc refusal, strdup and
free. A patterned 65,536-byte allocation remained live until STOP. It was checked
in full and freed only after both workers and owned IRQ contexts drained.
Existing partial-image cancellation, arena-empty proof, boundary guards,
protected-page validation and final reserve scan all passed.

- STOP parked at tick **9,752**, with all **9,256** system-heap allocations and
  **610** shared objects retired. Doom's retained buffer and the image also drained.
- Six network rounds passed with saturation/loss tests (31 expected burst drops).
  Full packet replay and **24 snapshot corruption rejections** passed.
- Command 8 completed in **15.305 seconds**, including PIO queries and scheduling.
  This is not a measured allocator critical-section duration. The new adapter's
  metadata scans are not covered by the old system-heap operation timers.
- Maximum observed whole-session IRQ gap: **10.819 ms**. This is a workload
  observation, not a worst-case latency guarantee. Bulk clear/copy runs with
  interrupts enabled, with a progress/STOP hook every 1 KiB.
- Full upload-journal replay, including command 8, passes against the actual
  C arena/adapter under ASan/UBSan on both the Linux host and the Mac.

The resident module remained retained as required. Reboot returned with a new
boot ID; the cooperative IPv6 server was restored with its existing visitor-log
configuration. An independent request from the Mac received **HTTP 200**.
No flash write occurred. Live visitor statistics are not copied into Git.

## Host and target compilation

The actual 32-bit host Doom engine uses this same allocator through its libc ABI.
Six 2,100-draw cases (**12,600 frames**) match the previously accepted full-frame
SHA-256 corpus (pixels, RGB palettes and game tics), and every heap drains.
A **640 KiB engine reservation** remains pinned beside the allocations. The peak
is **6,456,649 directly requested bytes** and **13 libc blocks**, including one
contiguous 6 MiB zone. The source's many zone allocations do not each consume an
arena slot. Files and the remaining runtime services still come from host libc.

All 80 engine units and three adapter/core units compile for i960. The combined
relocatable object has **631,112 static bytes**, with **53 unresolved externals**.
The five allocation imports are resolved. This is not a final executable link.
Context metadata is caller-provided and separately accounted in the resident BSS.

Native tests cover 128 slots, 5,000 fragmented allocations, large coexistence,
OOM/overflow, grow/shrink, failed realloc preservation, zero size, bad pointers,
extra pins, redzone/metadata faults and STOP during bulk work. Uncertain or corrupt
storage stays retained. The RTEMS regression suite passed; baseline upload tests
and a new actual-core Doom proof run under sanitizers.

## Contents and independent replay

- `live-evidence.tar.gz`: exact resident ELF/binary/map, generated module/source,
  implementation snapshot, complete physical captures, command journal, raw
  packets, diagnostics, build logs and Linux replay results.
- `doom-host-builds.tar.gz`: exact final host executable and sources, i960 objects,
  compiler commands, six host captures/digests/profiles and allocator source.
- `host-results.json`, `unresolved.txt`, `engine-sections.txt`: readable inventory.
- `replay.json`, `upload-replay.json`: Linux verification; `local-*`: independent
  Mac verification. `native-heap.log` and `rtems-tests.log`: native regressions.
- `production-restore.json`, `http-headers.txt`, `http-body.html`: reboot and service
  restoration evidence. `SHA256SUMS.json` and the repository inventory cover files.

Extract `live-evidence.tar.gz` into a fresh directory `capture`, then from the
repository root run:

```sh
python3 rtems/residentnet/verify.py --root capture capture/live
python3 rtems/residentnet/verify_upload.py capture/live --doom-heap --output upload-replay.json
python3 game/doom/runtime/test.py
python3 game/doom/runtime/verify_evidence.py artifacts/doom-runtime-20261012
```

The prior `doom-determinism-20261012` corpus stores the identical full host pixels
and palettes; this step stores their matching per-frame hashes rather than another
copy of all pictures. Original source/WAD archives and licenses remain in
`doom-m1-20261011`. Remote workspace: `/home/mit/i960-doom-runtime-20261012`.

## Remaining boundary

The allocator is serialized by the resident upload worker, not a general RTEMS
multi-task mutex. Before Doom gets its own task, route calls through that owner or
implement one shared task lock across loader/application users, with cancellation
and interrupt-latency tests. Add the remaining runtime functions and read-only
WAD service, then a real executable/import/entry manifest and target comparison.
This run proves the five allocation functions on the admitted arena; it does not
prove all libc, arbitrary task deletion, long-term endurance or on-card Doom FPS.
