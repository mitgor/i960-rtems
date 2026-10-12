# Doom WAD cache, compiler-runtime link and relocation proof — 2026-10-12

**Offline/host acceptance passed. No new payload was run on the card.**
The public cooperative service continued running during this work.
[Cache contract](../../game/doom/runtime/cache/README.md) ·
[Relocation gate](../../game/doom/runtime/relocate/README.md).

## Results

- The single-WAD backend passes six 2,100-frame DoomGeneric/Freedoom demos:
  **12,600 complete frame/palette/tic hashes match** the tracked deterministic
  corpus. Every run drains the simulated arena. The final host executable is
  SHA-256 `bf37f49626f1859bbc089a146b350a3f2cd900449e0835fe904a5c5c2ed85b61`.
- Real allocations include a **16,384-byte cache + 512-byte bounce buffer**.
  Each run reserves **1,048,576 bytes** for the future image inside the 8 MiB
  arena. Peak dynamic storage is **6,473,545 bytes** including the 6 MiB zone,
  with at most 15 live allocation records observed. Peak plus image reservation
  is **7,522,121 bytes**. The remaining 866,487 bytes are before guards/alignment
  and unimplemented runtime costs; this is not a complete target RAM proof.
- The cache produces **28,229–30,610** wire reads and about 14.45–15.67 MB
  transferred per case. It saves a few percent of requests against uncached
  512-byte splitting, but transfers slightly more bytes. Independent trace
  replay exactly reproduces measured counts; larger cache simulations show
  limited extra benefit. No card throughput improvement is claimed.
- The updated i960 object plus real soft-float libgcc helpers contains **318,064
  text + 69,888 data + 250,600 BSS = 638,552 bytes**. Debug sections are not part
  of that loaded-size sum. Nine compiler helpers resolve; **44 imports remain**.
  Final linking is deliberately checked to fail, preserving all missing services.
- Engine/runtime relocation inventory: **11,967 R_960_32 records**. The old
  linker drops final relocation sections even with `--emit-relocs`. A restricted
  prototype applies retained REL records and matches three independent final links
  for an import-free proof: **184 file bytes / 320-byte span / six relocations**.
  Ten malformed cases are rejected. This proof has **not executed on the card**.
- ASan/UBSan cover 10,000 random reads, conflicts/hits, EOF/overflow, partial
  errors, timeout, allocation rollback, active close/reentry and stale descriptor
  refusal. A separate native test composes the real cache, runtime mailbox,
  allocator and read loans. The RTEMS offline suite passes.

`evidence.tar.gz` includes the exact build sources, pinned engine source archive,
final host executable, i960 objects, maps/symbols/build commands, compiler archive
identity, missing-import callers, final-link refusal, linker-oracle binaries,
all six run reports/frame digests and WAD read traces. WADs and identical frame
pixels are already in the earlier tracked input/corpus artifacts and are not
duplicated. Intermediate development runs are not used as final evidence.

## Reproduction and next gate

Remote build workspace: `/home/mit/i960-doom-cache-20261012`. Source compilation:

```
python3 game/doom/build.py --work WORK --archive SOURCE_TAR --target host32 --arena-runtime --wad-cache
python3 game/doom/build.py --work CROSS --archive SOURCE_TAR --target i960 --arena-runtime --wad-cache --newlib NEWLIB_SOURCE
python3 game/doom/runtime/link_inventory.py CROSS/i960/doom-engine.o --out LINK
python3 game/doom/runtime/relocate/test.py --out RELOCATION_PROOF
```

After extracting the evidence archive, verify frame digests and linking on the
Mac, and replay WAD-cache choices using the pinned Freedoom files:

```
python3 game/doom/runtime/cache/verify.py EXTRACTED --reference artifacts/doom-determinism-20261012/runs --output verification.json
python3 game/doom/runtime/cache/analyze.py EXTRACTED/reserved-runs --wads WAD_DIRECTORY --output cache-replay.json
```

The next card step is the small relocated code/data/BSS proof through existing
admission and full audits. Remaining engine work includes 44 real platform/libc
imports, a final memory manifest, bounded startup and WAD transfer performance.
No general filesystem, arbitrary executable admission or Doom-on-card success
is implied by this checkpoint.
