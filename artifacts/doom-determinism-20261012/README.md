# Deterministic Doom host output — 2026-10-12

**Passed: 24 fresh 32-bit host runs, 50,400 draws, no repeated framebuffer,
palette or game-tic differences.** Both Freedoom 0.13.0 phases, DEMO1–3, four
heap-fill values each. This is capped host reference output; Doom has not run
on the card. No card lock, module, firmware, reboot or public service was touched.

[Root cause, fix, RAM impact and remaining gates](../../game/doom/DETERMINISM.md).

- `before-captures.json` references both complete pre-fix indexed captures.
  Their seven differing pixels fall in frames 497, 1426 and 1817. `before-*/`
  preserves traces/profiles/logs, and `diagnose-*.gdb/.log` plus `watch.gdb/.log`
  show the invalid sprite source indices. `before-after.json` records every
  corrected pixel against the first old run (148 pixels in 35 frames).
- `captures.json` maps all 24 post-fix runs to full indexed/RGB captures in
  `blobs/`. Blob filenames are SHA-256 of their XZ-compressed contents. Identical
  captures share a blob; no frames are sampled or discarded. Each indexed stream
  is 134,400,000 bytes and each RGB palette stream is 1,612,800 bytes unpacked.
- `runs/` stores each command, heap-fill value, exact executable and WAD hashes,
  memory profile, game-tic/FNV trace, full-frame SHA-256 list and output log.
  `results.json` and `matrix.log` preserve the full test matrix.
- `builds.tar.gz` contains before/after engine sources, all objects, host binaries,
  i960 engine, compiler commands/logs, tool sources and test executables. The
  separate `before-profile.c` reconstructs the exact original profile source
  plus its initial raw-capture edits; the later profile includes palette capture.
  `test-columns.log` is the ASan/UBSan renderer test, `test-profile.log` the
  allocation-accounting regression. These are Linux/i960 artifacts, not Mac apps.
- `environment.txt` records the Linux/compiler environment and ASLR setting.
  `manifest.json` authenticates the exported evidence files; repository-wide
  artifact hashes also cover this directory. Content hashes detect alteration;
  they are not a cryptographic signature by an external party.

The original pinned engine/WAD archives and licenses remain in
[doom-m1-20261011](../doom-m1-20261011/README.md); they are not duplicated here.
That milestone's three-frame failure and independent verifier remain unchanged.

## Replay without SSH

From the repository root:

```sh
python3 game/doom/verify_determinism.py artifacts/doom-determinism-20261012
```

Replay reads every distinct full capture, reconstructs the repeated runs using
content-addressed blobs, checks all per-frame SHA-256 and timing sequences,
verifies the old seven-pixel failure and 148-pixel correction, and rejects six
mutations: pixel, palette, tic, short pixel frame, short palette and trailing data.
The live runner performed direct byte comparisons before archiving; this replay
also verifies all stored files against the manifest. The binary is not executed.

To rerun on Linux, use the commands in `game/doom/DETERMINISM.md` with fresh run
directories. `tools/run_determinism.py` and `tools/pack_determinism.py` in the build
archive reproduce collection and deduplicated packaging. The remote workspace
was `/home/mit/i960-doom-determinism-20261012`; it need not be retained for replay.

## Runtime handoff

The corrected engine is **627,096 bytes** of text/data/BSS (+240 bytes), with the
same **58 unresolved externals**. The parallel RTEMS implementation now has an
accepted guarded 8 MiB arena and a contiguous 6 MiB allocation proof on-card.
Libc adapters, arbitrary application task launch, runtime link and host-backed
WAD reads remain. Host repeatability does not prove i960 equivalence, all levels,
interactive correctness, target stack bounds or target performance.
