# Repository organization — 2026-10-13

46 historical root Markdown documents moved into `docs/firmware`, `docs/loader`,
`docs/rtems`, `docs/games` and `docs/project`. Root README, Claude guidance,
current/consolidated findings and story remain project-wide entrypoints.
The six `subprojects/` entrypoints organize firmware, loader, RTEMS, Tetris,
Doom and web-server work.

## Artifact navigation changes

Only link destinations changed in the following 12 existing artifact documents
(61 links). These are intentional navigation metadata edits; their checksum
inventory must be refreshed with this change. No capture, binary, archive or
historical source snapshot was modified.

- [artifacts/README.md](../artifacts/README.md)
- [artifacts/ROM-DUMP-WORKLOG.md](../artifacts/ROM-DUMP-WORKLOG.md)
- [artifacts/ROM-INVENTORY.md](../artifacts/ROM-INVENTORY.md)
- [artifacts/live-handoff-20261010/README.md](../artifacts/live-handoff-20261010/README.md)
- [artifacts/tetris-t4-20261010/README.md](../artifacts/tetris-t4-20261010/README.md)
- [artifacts/tetris-t5-20261010/README.md](../artifacts/tetris-t5-20261010/README.md)
- [artifacts/romhook-20261010/README.md](../artifacts/romhook-20261010/README.md)
- [artifacts/dma-research-20261011/README.md](../artifacts/dma-research-20261011/README.md)
- [artifacts/stockhook-20261010/README.md](../artifacts/stockhook-20261010/README.md)
- [artifacts/romhook-step4-20261010/README.md](../artifacts/romhook-step4-20261010/README.md)
- [artifacts/dram-hook-audit-20261010/README.md](../artifacts/dram-hook-audit-20261010/README.md)
- [artifacts/chip8-20261011/README.md](../artifacts/chip8-20261011/README.md)

Root compatibility aliases were then removed. The four live source files
`host/dump/dac960dump.c`, `host/kmod/dac960probe.c`, `host/mkimage.py` and
`loader/live-handoff/return_status.s` received comment/help references to the
canonical documentation; executable behavior is unchanged.

## Tetris source grouping

`game/tetris/` now owns the core/header, native oracle, C test and two validation
scripts. Shared `io.h` and `i960.ld` remain in `game/`, linked from the subproject.
Old source/script names are relative symlinks so existing loader includes and
`make -C game` remain valid. Python scripts resolve the canonical directory
before locating repository inputs. Its own Makefile provides `test` and
`test-live` targets.

Both `make -C game/tetris test` and `make -C game test` passed native ASan/UBSan
with `RESULT=1161671136`. Both canonical and alias `check_live.py` validated all
nine saved T2 runs and produced byte-identical JSON. No new card execution or
cross-build is claimed by this organization pass.

## Link validation and retained history

The repository Markdown check scanned 1,420 relative file links after alias
removal and found no new unresolved destinations. 41 already-unresolved links
remain inside historical partial source/build snapshots; those captured
documents assume their original checkout and are preserved byte-for-byte.
Live documentation links pass. `git diff --check` also passes.

Two ignored `.DS_Store` files were removed. The ignored flash USB image remains
because its contents and recovery value have not been established. Build
caches used by parallel work and all archaeological evidence are retained.
