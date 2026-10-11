# DoomGeneric RAM request for RTEMS

Status: milestone 1, host measurements and i960 compile inventory. This document
requests an ownership contract; it grants no card address range. No Doom image
has been loaded on the card. Exact measurements are linked from `README.md`.

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
2. Prove the memory grant and loader layout on the card independently of Doom.
3. Run a bounded headless workload with memory guards, WAD identity and safe STOP.
4. Compare frame/state results, then connect palette/frame publication and input.

The frame hashes in host profiling diagnose repeatability; they do not establish
cross-architecture correctness or predict card FPS. Audio, networking and arbitrary
WAD/mod compatibility are outside this first-port contract.
