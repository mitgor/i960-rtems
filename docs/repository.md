# Repository map and preservation policy

`subprojects/` is the component-oriented entrypoint; `docs/` explains how the
components fit together. The canonical implementations keep their established
paths during the interactive Doom work:

| Path | Responsibility |
| --- | --- |
| `loader/` | Target loaders, firmware hook and staged execution experiments |
| `host/` | Linux transports, programmer/dumper, emulator and evidence auditing |
| `rtems/` | CPU/board adaptation, profiles, allocator, task/interrupt lifetime and network relay |
| `game/` | Tetris, CHIP-8, raycaster and Doom application code |
| `artifacts/` | Immutable dated sources, exact binaries, firmware, captures and reports |
| `docs/` | Reproduction, portability and research navigation |
| `subprojects/` | Firmware, loader, RTEMS, Tetris, Doom and web project entrypoints |
| `docs/{firmware,loader,rtems,games,project}/` | Historical reports grouped by topic, indexed in [history](history.md) |
| `STORY.md` | Narrative history |
| `CURRENT-FINDINGS.md`, `CLAUDE.md` | Current evidence/limitations and agent operating guidance |

This organization pass physically moves 46 historical documents into topic
directories and fixes navigation and stale root status. Live Markdown links
point directly to their canonical new paths. The old root names are removed.
Documentation links in 12 artifact navigation files were updated intentionally;
captured sources, binaries and archives remain unchanged. Tetris source moved
into `game/tetris/`, with old source paths retained as compatibility symlinks
for existing loaders. Other source under active development stays put. The subproject directories are
entrypoints, not duplicate source trees or independently installable packages.

## Why artifacts remain dated

An old failed run can explain a later fix. Exact binaries identify which code
actually executed, while full RAM captures and transcripts let validators
recheck claims. Vendor images, the stock dump, patched image and staging RAM
captures have different meanings even when bytes match. Do not deduplicate
or move them based only on their names or an apparent repeated result.

`artifacts/SHA256SUMS` and `artifact-inventory.json` bind file paths to content.
Use `python3 host/audit/artifacts.py --check-git` to check preserved Git blobs.
Never refresh the inventory merely to hide a missing or changed file. Keep
source updates outside old evidence directories and create a new dated batch.
Navigation-only link fixes in artifact README/index prose may be updated with an
explicit change record and intentional inventory refresh; see the
[organization change record](reorganization-20261013.md).

## Cleanup completed / deferred

The root README's superseded chronology has been replaced by current navigation;
its original text remains in Git history. Only ignored `.DS_Store` files are
safe disposable cleanup in this pass. Preserved tarballs, binaries and captures
are not junk. The ignored `i960-flash-usb.img` is retained because its current
contents and recovery value have not been established. Python caches in active
source trees are left alone while the parallel build is running.

A later source migration can move canonical apps into `subprojects/`, but
must update import roots, generated includes, packaging/deployment scripts and
current documentation together, then reproduce each build. Historical evidence
must continue to resolve its original source layout. A half-move with duplicate
live copies would make reproduction less reliable.

## Documentation locations

- [Firmware](firmware/README.md): dump, boot, patching, programming and recovery.
- [Loader](loader/README.md): RAM, dispatch hooks, buffered I/O and software loading.
- [RTEMS plans](rtems/README.md): OS/network, ownership, preemption and DMA roadmaps.
- [Games](games/README.md): Tetris milestones and application progression.
- [Project history](project/README.md): original manual, review and session record.

Root `README.md`, `CLAUDE.md`, `CURRENT-FINDINGS.md`, `FINDINGS.md` and
`STORY.md` remain the stable project-wide entrypoints. Future prose should
link to the canonical `docs/` paths, not create new historical reports at root.
Historical checkouts retain the original layout. Snapshot documents inside old
source archives keep their original references; those are historical context,
not live navigation.
