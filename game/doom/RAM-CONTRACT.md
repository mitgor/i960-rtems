# DoomGeneric RAM request for RTEMS

**N3 host startup measurement (2026-10-13; both physical startups failed before frame return):**
The actual private-Newlib first-frame path peaks at 6,445,535 private allocation
bytes in 13 blocks. Native total heap use including retained 64 KiB / 96 KiB
proof buffers and direct cache allocations is 6,629,855 bytes. The admitted
compatibility engine occupies 797,532 bytes (744,608-byte span plus 13,231 relocation words);
the native proof conservatively reserves 900,000 bytes. Allow a further 4,352
bytes for target batch staging plus allocator overhead. These remain within the
existing 8 MiB arena; no new memory grant or guard movement. The initial 1 MiB
layout reservation is released before engine admission, as on the card; retaining
that whole temporary reservation fragments the later 6 MiB zone allocation.
The native normal / STOP / deadline / read-error / repeat cases drain completely.
No completed physical startup peak or drain is established. Gameplay peaks and later frames are not established by this first-wipe test.
[Startup contract](runtime/startup/README.md).

**N2 measured addition (2026-10-12):** 4 KiB batching uses a 4,096-byte cache
bounce (3,584 bytes above the 512-byte baseline), plus a separately allocated and
borrowed 4,352-byte assembly buffer (eight 136-word fragments). Additional peak
payload is 7,936 bytes plus allocator metadata/alignment. Both allocations remain
inside the owned 8 MiB arena; staging is returned/freed before the read returns,
including timeout, STOP and validation failure. No kernel BSS/guard boundary
expansion. The six batched host demos peak at 6,477,129 arena bytes plus the
1,048,576-byte image reservation; allow a further 4,352 staging bytes on-card.
That host profile is not a measured private-Newlib Doom startup peak. The small
cache probe has on-card evidence and final drain; actual engine initialization
is N3. See [N2 evidence](../../artifacts/doom-batch-20261012/README.md).

**Accepted later baseline (2026-10-12):** 754,448-byte engine span with 13,175
relocations; 807,148-byte admission storage within a conservative 1 MiB initial
reservation. Physical preflight allocated a contiguous 6 MiB zone and measured
6,356,612 bytes in six port blocks. The separate cache/bounce uses 16,896 bytes;
image, guards, retained proof allocations and RTEMS stacks are additional.
Do not treat diagnostic peak as a complete Doom gameplay budget. Normal / STOP /
normal and full arena drain passed. [Exact evidence](../../artifacts/doom-progress-20261012/README.md).
The older estimates below retain their original host/linkage assumptions.

Status: milestone 1, host measurements and i960 compile inventory. This document
records the application budget; it grants no address range itself. The later
[resident-upload profile](../../rtems/residentnet/UPLOAD.md) now proves an 8 MiB
guarded arena and contiguous 6 MiB allocation on-card. The [scoped allocation adapter](runtime/README.md) now passes a resident card
proof; system libc and arbitrary task integration remain separate. The later full-engine-linked diagnostic image has now loaded and run on-card;
actual Doom initialization has not run. See README.md and
[the determinism follow-up](DETERMINISM.md) for the base engine. The allocation-integrated object is 631,112 bytes; context
metadata also needs explicit resident accounting. The earlier estimated combined
budget rises to 8,033,736 bytes, leaving 354,872 bytes; final linkage still decides.

## Proposed first port

Use pinned DoomGeneric, sound disabled, 320×200 indexed output, a read-only WAD
service supplied by the host, and an explicitly owned **8 MiB application arena**.
This is a conservative planning request, not a proven complete link size or a
universal minimum for Doom. Reject admission if the final memory manifest exceeds
its budget. Preserve the existing cooperative profiles and the public server.

The arena must accommodate engine text/data/BSS, a contiguous 6 MiB zone, a
separate ordinary allocator, game stack, transport slots/windows, runtime code
and guards. Do not add zone occupancy to the already reserved zone size; the
engine's internal 64,000-byte drawing buffer lives inside that zone. The separate
DoomGeneric 64,000-byte output buffer belongs to the ordinary allocation budget.
Two transport publication slots are additional buffers if the bridge retains the
existing two-slot model. A future zero-copy design requires its own ownership
proof before removing a buffer from this budget.

The source's zone default is 6 MiB. Lower `-mb` settings are experimental. A
small-zone success for one demo does not establish all-level compatibility:
non-purgeable data varies by level and cache pressure increases host WAD reads.
The 32-bit host runs approximate pointer/layout costs; i960 stack size and any
remaining ABI differences still require target measurements.

## Required ownership and loader work

- Prove ownership of the chosen arena after stopping firmware engines and owning
  interrupt/fault paths. Physical 16 MiB DRAM is not an allocation authorization.
- Separate executable/immutable data from writable BSS, heaps, stacks and DMA
  buffers. The current loader's 128 KiB immutable/code window and total 512 KiB
  staging grant are insufficient for this engine even before its zone heap.
- Provide a checked segmented upload/zero manifest with destination bounds,
  hashes, overlap checks, BSS initialization and instruction-cache ordering.
- Preserve guards and paired/full validation during first card tests. Define a
  new audit range contract for a larger arena; do not extrapolate the current
  512 KiB audit or silently reduce coverage to achieve FPS.
- WAD files remain on the host. Serve bounded, read-only offset/length requests;
  validate arithmetic, short reads and file identity. Split requests that exceed
  the transport window while keeping the destination allocation alive.
- A game tick, startup or WAD read is not yet a bounded firmware callback. Use
  owned task/interrupt contexts with STOP/timeout containment. Uncertain access
  retains the arena; cancellation must not free a zone or frame still in use.
- Keep publication generations, ACK ownership, restart epochs and dependency
  closure for WAD buffers and frame slots. No concurrent public-web/card owner.

## Runtime integration

Use the exact unresolved-symbol inventory, not assumed full POSIX availability.
The existing checked copy/clear routines can satisfy a subset. The guarded RTEMS
allocator needs a larger owned arena and the required libc entry points. Add
checked read-only WAD operations and explicit policies for config/savegame writes,
filesystem discovery and fatal exit. Remove desktop shell/dialog invocation from
the target error path. Preserve evidence on allocation and transport failure.

The engine still references soft-float helpers and signed 64-bit division. A
fixed-point renderer does not eliminate floating-point configuration, input or
timedemo-reporting code. Either implement/test those helpers or remove/replace
each calling path explicitly, then regenerate the unresolved-symbol report.

## Next acceptance gates

1. Finish runtime/platform link without fake successful stubs; generate a final
   code/data/BSS/heap/stack/transport manifest and check it against the arena.
2. Integrate the already tested resident arena/segmented loader with the final
   Doom manifest, libc adapters and owned application task.
3. Run a bounded headless workload with memory guards, WAD identity and safe STOP.
4. Compare frame/state results, then connect palette/frame publication and input.

The frame hashes in host profiling diagnose repeatability; they do not establish
cross-architecture correctness or predict card FPS. Audio, networking and arbitrary
WAD/mod compatibility are outside this first-port contract.

## Owned engine preflight / fragmentation checkpoint — 2026-10-12

The new engine-linked image is 754,448 bytes including BSS. Authenticated
relocation metadata adds 52,700 bytes; the image admission allocates 807,148
bytes (807,184 with guards/alignment). This remains within the conservative
1 MiB image allowance. Native private-libc preflight peaks at 6,356,596 tracked
bytes / six blocks, excluding the direct 16,896-byte WAD cache/bounce and guards.
Including retained legacy proof buffers and the image leaves roughly 1 MiB
before further guard/consumer costs. This is not a measured Doom startup peak.

The old 320 KiB proof image places retained buffers where they fragment the
future image + contiguous 6 MiB zone. An actual guarded-heap/native-port test
reproduces OOM there and succeeds when 1 MiB is reserved during proof setup.
The engine host harness now uses that layout, without releasing another owner's
retained buffers or changing the 8 MiB grant. Physical acceptance remains pending
the interrupt/drain bit-64 investigation; no engine entry ran in the failed
batch. See [exact evidence](../../artifacts/doom-engine-20261012/README.md).
