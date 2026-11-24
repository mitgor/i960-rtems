# i960 card computer

This project turns a Mylex DAC960PG RAID controller into a computer that runs
our code after the PC boots. The tested card has an Intel i960RP, 16 MiB DRAM
and stock firmware 4.07-0-29 extended with a small, boot-validated ROM hook.
Linux supplies the loader, display/input transport and network gateway.

Start with [stock card to applications](docs/reproduce.md). Read
[the story](STORY.md) for how we discovered and built it, or use the
[subproject index](subprojects/README.md) to work on one component.
The [Linux host guide](host/README.md) locates the versioned launchers, routing
code and required deployment inputs.
For the AcceleRAID 160 native firmware work, start with the
[firmware candidate index](docs/hardware/ACCELE160-FIRMWARE-CANDIDATES.md).
It separates flashed and booted images from the experimental native image
that includes an on-card flash writer.

## Subprojects

| Project | What it contains |
| --- | --- |
| [Firmware](subprojects/firmware/README.md) | Original ROM, in-PC dump, analysis, minimal patch, programming and postboot proof |
| [Loader](subprojects/loader/README.md) | Returning RAM programs, buffer I/O, persistent sessions and segmented resident uploads |
| [RTEMS](subprojects/rtems/README.md) | i960 port, interrupt/task ownership, memory arenas, libc integration and network transport |
| [Tetris](subprojects/tetris/README.md) | Card-executed game with SSH terminal input/output |
| [Doom](subprojects/doom/README.md) | DoomGeneric/Freedoom, native oracle, i960 runtime and browser display |
| [Web server](subprojects/web/README.md) | Card-hosted IPv4/IPv6 HTTP, system information, Vader art and host visitor statistics |

Other application experiments live in [CHIP-8](game/chip8/README.md) and
[raycaster](game/raycaster/README.md). The raycaster preserves the display
transport experiments that informed Doom.

## What works

The ROM patch and postboot execution are accepted. Tetris passed a 30-minute
SSH run at 19.91 updates/s. RTEMS/lwIP serve IPv6 HTTP through the host and the
resident runtime owns a 12 MiB region with an 8 MiB Doom arena. The optimized
AcceleRAID Doom profile has completed persistent browser play with guarded DMA,
FIFO input and pushed frames. See the [current Doom setup](doom_commands.md)
for its measured 17.59–19.33 card FPS and 20.40 Mac-received stream FPS.
The earlier DAC960PG and 2.33 FPS AcceleRAID experiments are historical.
The installed AcceleRAID card now runs native RTEMS diagnostic/updater firmware;
the FI1-based Doom launcher needs a compatible card or a native Doom port.

[Latest findings](CURRENT-FINDINGS.md) and the relevant dated evidence report
establish acceptance; an old milestone's “next step” is historical context.
The [visible Doom report](artifacts/notes/doom-visible-20261013.md) records
604 full audit pairs, native replay, STOP/repeat/shutdown and browser delivery.

## Navigation and reproduction

- [Reproduce the stages](docs/reproduce.md): prerequisites, stock versus patched card, build/run entrypoints and success criteria.
- [Repository map](docs/repository.md): source ownership, shared dependencies and artifact policy.
- [Research and evidence](docs/research.md): firmware coexistence, rejected approaches, recovery, DMA and OS progression.
- [Support another i960 card](docs/porting.md): separate CPU/runtime reuse from board-specific assumptions.
- [Historical documents by topic](docs/history.md): all original root milestone reports.
- [Artifact inventory](artifacts/README.md), [ROM inventory](artifacts/ROM-INVENTORY.md) and [checksums](artifacts/SHA256SUMS).
- [Claude guidance](CLAUDE.md): operational contracts and current working state.

Source paths remain `loader/`, `host/`, `rtems/` and `game/` so tested build
scripts and archived experiments remain reproducible. `subprojects/` is the
human-facing component index. Historical reports now live by topic under
`docs/`; live navigation and artifact index links use those canonical paths.
[Repository map](docs/repository.md) explains source ownership and preservation.
