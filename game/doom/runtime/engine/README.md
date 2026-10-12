# Exact-build larger image and owned engine preflight

This gate admits the full engine-linked private-library object through **one
reviewed diagnostic entry**. It does not invoke `doomgeneric_Create`, initialize
Doom, advance a game tic, or publish a Doom frame to the browser.

`platform/engine_entry.c` binds the owned runtime and immutable WAD backend,
checks real Newlib 64-bit/float formatting including `%lln`, allocates and
checks a contiguous 6 MiB zone, renders a known indexed framebuffer/palette
through the platform hooks, reads the IWAD header into an interior allocation,
then performs bounded owned waits. Normal completion and invocation STOP both
close the WAD backend, release caller allocations and retire private Newlib.
It returns only after teardown. Every invocation gets a fresh image; retired
libc globals and engine globals are never reset while live.

The port's owned sleep hook yields through RTEMS in chunks of at most 1,000 ms.
STOP exits only through an armed owner boundary. An invalid owner cannot force
a nonlocal jump across a critical section. The actual private libc preflight
has separate 32-bit ASan/UBSan tests. The small owned proof establishes the
pinned i960 setjmp/longjmp context on physical hardware.

## Admission and protected placement

Build the private engine with `platform/build.py`, then `platform/pack_engine.py`.
The packer requires canonical text/data/BSS, no unresolved imports, only unique
aligned internal R_960_32 sites and valid addends. Three independent links must
match. `engine/admit.py` produces:

- The canonical template and packed little-endian relocation offsets.
- Exact section geometry, diagnostic entry and result bounds.
- A small kernel header with SHA256 identities for the entire initialized image,
  relocation metadata and immutable text. The host cannot choose these identities.

The engine host harness reserves a 1 MiB initial image while running the earlier
heap/peer proof. This places its retained buffers above the future image +
contiguous 6 MiB zone. The previous 320 KiB reservation fragments that span;
native private-libc tests reproduce its OOM and prove the corrected layout.
The corrected host reservation has not yet passed a complete physical batch.

Pass that directory to `rtems/build.py --doom-engine DIR` with the existing
resident upload/shared Doom runtime options. The SHA and gate code occupy
`0xc0f8c000..0xc0f94000` inside the already owned bootstrap allocation.
BSS is bounded below `0xc0f8c000`; upper upload code retains its existing
`0xc0f94000..0xc0f9bff0` limit. Both code windows are included in the generated
host bootstrap verifier and target protected-page checks. No RAM ownership
or mutable audit range is expanded to accommodate them.

UPL1 command 18 checks the exact four-section geometry, canonical gap bytes,
streaming image/metadata SHA256, ordered/aligned/ranged sites and zero BSS.
The image stays pinned. Hash work is chunked to 1 KiB with RTEMS yields;
relocation work yields every 256 sites. It authenticates metadata before
applying any fixup and synchronizes code before the owned entry. The metadata
is authenticated again after return, and the executable text is independently
checked by reversing only its authenticated relocations and hashing the
canonical bytes. Writable globals are discarded with the one-shot image after
owner cleanup, never treated as immutable data. Unexpected output, scope/drain,
text or metadata conditions quarantine the image and abort; no retry/reclaim.
Command 19 reports the twelve copied result words.

## Evidence and boundaries

`engine_client.py` performs no-image refusal, CRC-valid altered-code refusal,
CRC-valid altered-metadata refusal, then normal / STOP / normal with independent
invocation generations. It retains full paired audits and the existing
runtime/cache/relocation regressions alongside network traffic. The preflight
frame and palette hashes have independent byte oracles, and WAD replies must
match the pinned file and CRC on the captured wire. Engine WAD and owned-control
journals are separate so prior regression claims stay reproducible.

`test_engine_gate.py` runs the actual SHA/admission/segment/arena core with an
explicitly modeled entry: altered identity, dirty BSS, admission STOP, failed
scope and changed post-execution text. It does not execute i960 instructions.
`engine_replay.py` likewise replays the actual admission and lifetime core,
modeling only the engine invocation from independently checked physical fields;
the native private-libc preflight is the separate real C execution test.
`test_engine_evidence.py` rejects eleven altered capture cases after a clean
baseline passes. Physical acceptance is recorded in the artifact README.

## Next gate: actual Doom startup

Keep gameplay unadmitted. Measure and batch initialization WAD reads without
weakening sequence/offset/CRC/loan validation. Add explicit engine-owned startup,
tic safe points and teardown for all engine allocations, then admit that new
entry/build identity separately. Compare the first real Doom frame to the
established deterministic host oracle before adding browser input/lifetime.
The 6 MiB diagnostic zone is allocated and released; it is not a initialized
Doom zone or evidence of a game frame.
