# RTEMS-to-Doom implementation plan — 2026-10-12

The engine's 80 selected translation units compile for i960RP; the relocatable
object still has 58 unresolved symbols. No Doom image has run on the card.
The [RAM contract](RAM-CONTRACT.md) requests an 8 MiB application arena,
including a contiguous 6 MiB zone. The [exclusive RAM work](../../rtems/residentnet/LARGE-RAM.md)
expands the kernel workspace/stacks separately; tested reserve is not automatically
an application allocator or executable image grant.

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
7. **Headless correctness.** First resolve the existing host repeatability gap:
   corrected 2,100-frame traces still differ at frames 497, 1426 and 1817. Until
   resolved, the full host trace is not an accepted oracle. Then use pinned Freedoom input and deterministic commands;
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

The current host/i960 inventory gives 626,856 bytes of engine static storage
and a maximum observed 6,456,649 bytes of direct allocations (including the
6 MiB zone). Their sum is 7,083,505 bytes, before the missing runtime, transport
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

The next concrete deliverable after the current RAM batch is a large allocation
and segmented-loader self-test. It should establish the Doom memory grant before
loading the game itself.
