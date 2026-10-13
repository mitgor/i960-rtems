# RTEMS-to-Doom implementation plan — 2026-10-13

**N3 actual startup (2026-10-13; implemented, not physically accepted):**
The real private-library Doom engine passes ten native first-frame / STOP /
deadline / read-error / repeat cases, with exact reference pixels and palette.
Both card attempts entered actual initialization but timed out before returning
an accepted frame. The first completed 4,769 WAD requests; the compatibility
retry completed 4,764. Both match the host through request 4,674 and then choose
the same different texture region. Every captured completed WAD fragment matches
the pinned file. Preserve both failures; do not substitute host/model success.

Startup-only `-mold-align` corrects an independently measured allocator/layout
mismatch: 55 Doom/zone/API constants match the 32-bit host and RTEMS callback
offsets stay unchanged. It did **not** remove the hardware failure. Candidate
span 744,608 bytes, 13,231 relocations, admission 797,532 bytes, zero unresolved
imports; no new RAM grant. Its kernel SHA256 is
`25dd26bc206cec40f77e55a9a7666adb6df1f85cf7c6d662d1c301fed1bec4a5`.

The retry preserved 275 full snapshot/RAM pairs plus one complete snapshot and
44 words of its final RAM page; captured fault markers are zero, but the fault
PC and final state are unknown. Packet pumping between four-word audit groups
allowed 36 complete dual-stack rounds, versus six previously. All full audits
remain required. The upload query timed out after 2,772.949 ms and the driver
retained resources until reboot. Startup-only aggregate budget is 90 minutes;
per-engine 30-minute and per-read five-second limits are unchanged.

Keep startup opt-in and N2 as the accepted baseline. Next: independently readable
startup checkpoints/fingerprints around level setup, texture precache, draw and
exit; locate the first state divergence before another full attempt. Then repeat
normal / partial-read STOP / normal with complete replay and drain. Neither this
first-wipe milestone nor visible/browser Doom is accepted yet. Both captures are
saved; reboot cleared retained resources and public IPv6 HTTP returned 200. The
Doom test reservation is released; coordinate with the public relay before reuse.
[Evidence and current status](../../artifacts/doom-startup-20261013/README.md).


**N2 WAD batching checkpoint (2026-10-12):** opt-in `--wad-batch`
uses owned, pinned 4 KiB requests assembled from ordered 512-byte fragments.
CRC, exact lengths, sequence/offset binding, STOP, timeout, full image/RAM audits
and final drain remain enforced. First-frame host trace: 27,648 → 4,747 logical
requests (82.83% fewer), identical delivered bytes. Small on-card cache probe:
24 → 7 requests, mean 3.588 → 1.655 s (2.17×; two runs per size, including report
queries, both using WAB1). No on-card Doom startup or FPS claim. Six host demos
retain all 12,600 frame hashes. Extra peak payload memory is 7,936 bytes plus
allocator overhead, within the unchanged 8 MiB arena.

Physical STOP/drain completed at tick 101,897. The live harness then failed an
obsolete expected-cancellation count (14 rather than 15); the raw failure is
preserved. A labelled derived view recovers the final raw reply and kernel
monitor log, separates and validates exception diagnostics, and passes unchanged
network audits plus full upload/native replay (7,949 commands). Keep this
qualification when citing acceptance; do not call the original live harness a
clean pass. The harness is corrected for future runs. Keep the feature opt-in.
[Evidence, reproduction and limits](../../artifacts/doom-batch-20261012/README.md). Next is N3: bind batching
into a newly authenticated engine image, perform bounded actual Doom
initialization, then verify the first frame. The accepted old diagnostic engine
still uses the 512-byte ABI; do not silently reuse its admission hashes for a
changed engine. Coordinate hardware ownership before testing.

**Current checkpoint — 2026-10-12:** the full-engine-linked diagnostic preflight
is physically accepted, including normal / STOP / normal, exact admission and
post-return code checks, contiguous 6 MiB allocation and complete drain at tick
100,085. Full capture replay now passes. This supersedes the earlier pending
entry/dispatcher gates below, retained as development history. Doom itself has
not initialized on-card. Next: validated WAD batching, bounded initialization,
first-frame verification and browser controls. [Evidence](../../artifacts/doom-progress-20261012/README.md).

**Accepted owned runtime and larger-image checkpoint:** the diagnostic engine
entry and 1 MiB reservation/6 MiB contiguous-zone layout passed physically with
full audits. The dispatcher identity/stack failure was diagnosed and fixed in
an opt-in profile. Native replay now matches the complete physical journal.
Keep the original [failure evidence](../../artifacts/doom-engine-20261012/README.md)
and the [accepted follow-up](../../artifacts/doom-progress-20261012/README.md)
separate. No actual Doom initialization or first-frame result exists on-card.



The engine's 80 selected translation units compile for i960RP; the relocatable
base object has 58 unresolved symbols; the allocation-integrated variant has 53; the new cache + actual compiler-helper
link leaves 44. No Doom image has run on the card.
The [RAM contract](RAM-CONTRACT.md) requests an 8 MiB application arena,
including a contiguous 6 MiB zone. The [exclusive RAM work](../../rtems/residentnet/LARGE-RAM.md)
expands the kernel workspace/stacks separately; tested reserve is not automatically
an application allocator or executable image grant.

Prototype progress: [arena and segmented core](../../loader/segmented/README.md)
passed native 6 MiB allocation tests and real i960 execution from a small BIO arena.
The [resident integration](../../rtems/residentnet/UPLOAD.md) now grants an 8 MiB
arena, proves a contiguous 6 MiB allocation on-card and uploads segments larger
than 64 KiB through PIO. Bootstrap placement and high-tail protection are explicit.
The [allocation adapter](runtime/README.md) now passes actual host Doom and
a resident card proof. [Shared-task arena ownership](runtime/SHARED-ARENA.md)
now passes on the two existing workers. A [runtime-entry/WAD bridge](runtime/entry/README.md)
also runs a reviewed uploaded probe through a versioned function table and reads
the pinned WAD from the host, with timeout/error recovery and full audits. It
does not yet implement Doom file descriptors or cache. Steps 2–3 still need arbitrary task
launch and runtime imports or relocations; production malloc remains unchanged.

## Ordered gates

1. **RAM admission and OS capacity.** Validate progressively larger exclusive
   regions through 10–12 MiB, with engine isolation, owned exceptions, protected
   memory checks, stack stress, networking and STOP. Keep exact image-specific
   evidence. Preserve the stock/cooperative alternative and reboot-only exit.
2. **General arena.** Turn the validated reserve into a guarded application heap.
   Prove at least one contiguous 6 MiB allocation plus all remaining manifest
   allocations simultaneously. Extend the present 64-live-block/request limits
   deliberately: metadata validation currently has fixed, partly quadratic scans,
   so increasing slot counts also needs a measured interrupt-latency budget.
   Test out-of-memory, fragmentation, overflow, realloc/calloc,
   shared pins and cancellation. Measure interrupt latency during large clears
   and copies. Retain memory when a user or hardware access is uncertain.
3. **Executable loading.** The 128 KiB immutable window and 512 KiB upload grant
   remain too small. Implement a segmented copy/zero manifest with independently
   admitted destinations, overflow/overlap rejection, hashes, explicit entry point,
   BSS initialization and instruction-cache ordering. Check cross-segment call
   reach/relocations and define a versioned resident runtime interface. Preserve monitor, control,
   fault and transport ranges. First run a small relocated self-test, then a
   larger code/data test, before admitting Doom. Load through an explicitly
   bounded resident service after takeover: sending another stock firmware
   callback is prohibited. Preserve the resident loader while copying or executing
   application segments; a validated RAM reserve is not a permission to overwrite
   the monitor or kernel.
4. **Real runtime link.** Resolve the exact symbol inventory: formatting/string
   and conversion routines, allocator ABI, soft-float helpers, signed 64-bit
   division, time and platform services. Test actual semantics and i960 ABI;
   no fake successful stubs. Produce a final text/data/BSS/zone/heap/stacks/transport
   manifest. Reject any image that exceeds the granted layout.
5. **Host-backed WAD service.** WADs stay on the host (about 28.8 MB each).
   Provide bounded read-only offset/length requests, pinned file identity, short
   read/error handling, generation IDs and buffer ownership through completion.
   Large reads split into bounded transfers. Define explicit unsupported or
   implemented policies for saves/config writes and filesystem discovery.
6. **Application execution and cancellation.** Run Doom in an owned preemptible
   task; startup/WAD reads and a game tick are not bounded firmware callbacks.
   Control and networking must keep running while Doom blocks or computes.
   The current port has four stack slots (idle, controller and two workers),
   three Classic task objects, and only two task-owned interrupt contexts.
   First replace the synthetic heap worker with Doom, or explicitly expand the
   task/IRQ ownership registry and test every new context before adding a task.
   The current fast PIO path also relies on both test workers polling. Doom must
   either call a bounded service hook often enough or gain an independent control
   service with its own tested interrupt/context ownership. The 100 Hz fallback
   alone can impose one tick per PIO word; measure WAD/frame throughput under real
   rendering load before treating the current network results as Doom performance.
   Implement game time from the monotonic RTEMS clock and yield for sleeps;
   account explicitly for 35 Hz game ticks on the 100 Hz OS clock.
   STOP drains or quarantines all WAD/frame/heap references. Test noncooperation,
   allocation failure, corrupt input, disconnect and timeout with resources live.
7. **Headless correctness.** The [host repeatability fix](DETERMINISM.md) now
   bounds masked sprite sampling; the old three-frame gap is resolved for the
   captured corpus. Use the new pinned Freedoom corpus and deterministic commands;
   capture game state, palette and frame hashes. Compare against the host profile,
   investigating architecture-dependent differences. Measure stack/heap peaks and
   worst observed tick, control and interrupt delays. A single demo is not proof
   of all-level compatibility.
8. **Display and input.** Publish 320×200 indexed frames plus palettes with
   generation/ACK ownership. Provide terminal/browser input, release keys on
   disconnect and bound queues. Measure displayed FPS before considering transport
   shortcuts. Maintain the accepted audit policy until a new one is validated.
9. **Endurance and packaging.** Exercise level transitions, WAD cache eviction,
   sustained input, loss/backpressure and repeated start/STOP sessions. Preserve
   binaries, manifests, captures, source hashes and recovery instructions in Git.

## Budget and scope

The current host/i960 inventory gives 631,112 bytes of engine/allocation-runtime static storage
and a maximum observed 6,456,649 bytes of direct allocations (including the
6 MiB zone). Their sum is 7,087,761 bytes, before the missing runtime, transport
and stack costs. The measured 5,856-byte x86 stack span is not an i960 bound.
These sampled workloads support the 8 MiB planning request, not a universal
Doom/mod memory guarantee.

Plan for 256 KiB kernel workspace, three 64 KiB requested task stacks plus an
idle slot, retained owned interrupt/fault stacks, existing network/control storage,
and an independently admitted 8 MiB application budget. A 12 MiB candidate has
room to pursue this layout, but final link sizes and live allocation peaks decide
acceptance. The application budget already includes its 6 MiB zone; do not count
zone occupancy twice. DMA networking, direct NIC access, audio, general POSIX and
arbitrary mods are not prerequisites for the first playable milestone.

The large allocation and resident segmented-loader self-tests have now passed.
The allocation libc adapter is now tested; next implement shared-task ownership,
the remaining real runtime link and
host-backed WAD reads before loading Doom. The new host corpus supplies a finite
reference; it does not establish i960 correctness by itself.

## Shared-arena scheduling gate (2026-10-12)

The opt-in [shared arena](runtime/SHARED-ARENA.md) preserves two registered
worker IRQ owners. All loader/Doom metadata access uses one task mutex, and
unlocked bulk work keeps pins. The old resident idle task deliberately faults;
blocking both workers is not supported. Before WAD I/O or new task launch,
either keep the control/network worker runnable or explicitly register, stack,
and validate the idle interrupt context. Do not fix this by hiding an idle
fault, force-unlocking a mutex, or relaxing task/IRQ drain.

## Next after accepted runtime entry (2026-10-12)

1. Choose and validate the engine image linking/relocation strategy inside the
   admitted arena; resolve remaining compiler/libc imports without replacing
   RTEMS system allocation or admitting unreviewed code by the probe command.
2. Connect Doom's file operations to one immutable WAD with bounded descriptors,
   seek/read validation and a measured cache budget. Current 512-byte PIO reads
   prove ownership/error handling, not acceptable startup throughput.
3. Run bounded engine initialization, verify zone/cache/image/stack high-water
   and cleanup, then request the first frame and compare its host oracle.
4. Add input/frame scheduling only after startup and STOP/recovery are accepted.
   Preserve worker 0's runnable control path unless idle IRQ ownership is proven.

## Cache/link checkpoint and concrete next gates (2026-10-12)

The [single-WAD cache/backend](runtime/cache/README.md) passes the actual engine
on the host (12,600 reference hashes), reserving 1 MiB for the image inside the
8 MiB arena. Peak dynamic use is 6,473,545 bytes, including cache/bounce and zone.
The partial i960 link now resolves nine compiler helpers and occupies 638,552
static bytes; 44 libc/platform imports still prevent a final link. No card
payload changed at this checkpoint.

1. Admit the [small REL relocation proof](runtime/relocate/README.md) through the
   segmented loader, preserving allocation/pin/CRC/BSS/cache-ordering/whitelist
   checks. Test its initialized data, BSS and indirect pointers on-card. The old
   linker's `--emit-relocs` does not preserve final relocation records; use the
   validated relocatable-object records instead of guessing patch sites.
2. Resolve the remaining import inventory with tested semantics: pure libc,
   application-local formatting/error state, real platform timing/output/input,
   and explicit read-only/unsupported file policies. Do not share kernel stdio
   state or fabricate successful saves/config writes. Recompute the final image.
3. Connect the cache backend to the accepted runtime table in that admitted
   image, measure larger WAD transfer options, and run bounded initialization.
   The small cache alone is not a startup-throughput solution: observed wire
   bytes increase slightly despite modest request-count savings.
4. Compare the first frame, then progress to ticks, input, STOP and endurance.


## Relocated proof accepted (2026-10-12)

The small three-segment proof above has passed physical execution twice,
including data/BSS/pointer postconditions, full paired audits and STOP drain.
[Acceptance record](../../artifacts/doom-relocate-20261012/README.md).
The next work is the remaining 44 libc/platform imports and the target WAD
cache/runtime integration, followed by a fresh RAM/stack budget and bounded
engine initialization. Keep the existing closed admission gate until that
engine-specific contract and teardown are reviewed. The proof restores its
mutable data after each return; this is not yet the engine's persistent state
lifetime model. Eight MiB still needs room for allocator overhead, runtime,
image, zone, cache and any retained buffers.


## Private runtime/cache checkpoint (2026-10-12)

The private Newlib/platform candidate resolves the previous 44 imports. Its
752,804-byte image span and 13,113 retained relocations match independent links
at three addresses. The entire private 32-bit runtime passes sanitizers; its
actual engine execution, i960 setjmp/longjmp and stack peaks remain untested.
The cache bridge now runs on the card with full audits and an independent wire
oracle. [Evidence](../../artifacts/doom-platform-20261012/README.md).

The earlier entry gates below are now accepted as diagnostic proofs (items 1–2).
Items 3–4 remain the next implementation gates:

1. Extend the application runtime with owned yield, owner/STOP queries and safe
   termination. Admit and test a small i960 exit/context proof before engine
   entry, preserving both worker IRQ owners and the runnable control worker.
2. Define the engine entry and persistent data lifetime; admit the larger image
   and relocation manifest using exact build identity. Its relocation-offset
   list alone is 52,452 bytes, so do not embed it in the 32 KiB proof window or
   weaken the whitelist to fit it. Keep image/metadata pins until consumers drain.
3. Measure and improve WAD transfer batching with exact length/CRC/identity/loan
   checks. The seven-read cache probe took 13.2/11.6 seconds under full audits;
   cache hits are correct. The later polled small probe took 0.405/1.218 seconds;
   full startup throughput still needs batching and measurement.
4. Run bounded initialization with the new runtime, record complete image,
   zone/cache/stdio/allocator/stack peaks, compare the first frame, then progress
   through ticks, STOP, browser output/input and endurance.

The old 12,600 host hashes cover the earlier allocator/cache profile, not the
new private Newlib port. Preserve the 1 MiB conservative image reservation;
account for private stdio costs and any retained proof allocations before
claiming final 8 MiB headroom. No general process/filesystem or arbitrary mod
compatibility is claimed.
