# Subprojects

Choose a component, then follow its source/build/evidence links. Run commands
from the repository root unless its guide says otherwise. These entrypoints
organize shared source without creating divergent copies or changing archived
build paths.

| Component | Source | Start here |
| --- | --- | --- |
| Firmware | `host/dump`, `host/program`, `loader/romhook` | [Firmware](firmware/README.md) |
| Loader | `loader/runtime`, `loader/segmented`, `host/loadrun`, `host/session` | [Loader](loader/README.md) |
| RTEMS | `rtems` | [RTEMS](rtems/README.md) |
| Tetris | `game/tetris/`, `host/session` | [Tetris](tetris/README.md) |
| Doom | `game/doom`, `rtems/residentnet` | [Doom](doom/README.md) |
| Web | `rtems/net`, `rtems/transport`, `rtems/autonomous` | [Web](web/README.md) |

The common hardware path is firmware → loader → application. Tetris uses the
returning firmware callback directly. Doom uses the resident RTEMS runtime.
The web server's accepted autonomous profile coexists with firmware; it is a
separate deployment from exclusive resident Doom. Do not start two owners of
the same PCI function.

[End-to-end reproduction](../docs/reproduce.md) · [repository map](../docs/repository.md)
