# DoomGeneric milestone 1 evidence — 2026-10-11

This batch performed compilation and host profiling only. It did not load code,
write flash, acquire the card lock, or change the production service. Concurrent
RTEMS card tests rebooted the host several times; accepted builds and workload
runs completed after those interruptions. Linux gcc-multilib was installed for
32-bit host profiling; the installation log is preserved.

## Accepted results

- 80 i960RP engine translation units compiled; ELF32/i960 relocatable output.
- Text 306,720 + data 69,888 + BSS 250,248 = **626,856 bytes**, before runtime,
  stacks or dynamic allocations. COMMON symbols are assigned storage explicitly.
- **58 unresolved symbols**, inventoried by calling object; final-link failure
  preserved. No fake stubs and no loadable firmware claim.
- **20 bounded 32-bit workloads / 42,000 draws**, with 6 MiB zone baseline and
  smaller-zone comparisons. Peak direct allocation **6,456,649 bytes**; the zone
  is included. Outside-zone peak **165,193 bytes**.
- Peak non-purgeable zone data including headers **2,211,560 bytes**; all cached
  data can nearly fill the zone. A host-backed WAD read requests up to **224,280
  bytes**. Maximum observed instrumented engine stack span **5,856 bytes**.
- Four low-zone workloads fail explicitly with Z_Malloc allocation errors.
- Accounting unit test passes. Startup-wipe initialization fixes early hashes,
  but three later frames differ in repeated 2,100-frame traces. Memory figures
  repeat exactly. This remains an explicit headless-correctness follow-up.

See [the full report](../../game/doom/README.md) and
[the proposed 8 MiB ownership contract](../../game/doom/RAM-CONTRACT.md). The
8 MiB request contains estimates for runtime/stack/guards and is not a RAM grant.
No host FPS number is used to predict i960 performance.

## Files

- `doomgeneric-source.tar.gz`: untouched pinned engine source and license.
- `freedoom-0.13.0.zip`: original release, both IWADs, license, credits and manuals.
- `newlib-headers.tar.gz`: exact patched headers used plus COPYING.NEWLIB.
  Original newlib source/patch identities are already in `rtems/sources.json`;
  the existing toolchain provenance is in `artifacts/toolchain-20261011`.
- `doom-builds.tar.gz`: final i960 objects/relocatable image, section/symbol/ABI
  inventories, expected failed final-link output, host executable/objects/maps/
  stack-usage files, patched sources, profiling tools, accounting test binary/log,
  dependency-install log and initial compile diagnostics. Earlier object variants
  are preserved as diagnostic records; final acceptance uses `cross/i960` and
  `native/host32` only. All build files are hashed in `build-files.json`.
- `doom-profiles.tar.gz`: final per-run commands, logs and JSON, low-zone failures,
  short/full frame traces, initial summary, final summary and repeatability report.
  The initial summary is preliminary and not part of accepted final measurements.
- `summary.json`: derived sizes, symbol categories, observed peaks and provisional
  RAM budget. `profiles.json` and `low-memory.json` preserve machine-readable runs.
- `repeatability.json`: exact later-frame differences; do not claim full hash match.
- `archive-hashes.json`: size/hash of every source/build/data archive.
- `verification.json`: independent archive/ELF/summary/workload verification.

The host profiler counts requested bytes at engine allocation call sites, not
process RSS or glibc/FILE internals. Its static measurement registry, instrumentation
and function-entry overhead are excluded from target engine sizing. Zone usage
counts block headers and is inside the single reserved zone allocation. Reported
zone purges count cache-pressure frees in Z_Malloc. Host stack observations exclude
uninstrumented libc interiors and do not bound the i960 ABI/interrupt stack.

Workloads stop at 2,100 draws (including startup/wipe draws), with a synthetic
clock. They are sampled prefixes rather than full demos/all maps/interactive
endurance. Sound is disabled. Warp cases have no player input. FreeDOOM WADs are
not mapped wholesale into memory: read calls go through the stdio-backed service.

## Verify

```sh
python3 game/doom/verify_evidence.py artifacts/doom-m1-20261011
```

This hashes archived build inputs/outputs, independently checks ELF machine,
sections and undefined symbols, recomputes the summary, checks all workload
records and preserves the known hash discrepancy. It does not execute Linux or
i960 binaries on the verifying host. To rebuild/rerun, follow `game/doom/README.md`
on Linux using fresh output directories. No card access is required.
