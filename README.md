# i960 card computer

This project turns a Mylex DAC960PG RAID controller into a computer that runs
our code after the PC boots. The tested card has an Intel i960RP, 16 MiB DRAM
and stock firmware 4.07-0-29 extended with a small, boot-validated ROM hook.
Linux supplies the loader, display/input transport and network gateway.

Start with [stock card to applications](docs/reproduce.md). Read
[the story](STORY.md) for how we discovered and built it, or use the
[subproject index](subprojects/README.md) to work on one component.

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
resident runtime owns a 12 MiB region with an 8 MiB Doom arena. Doom has
produced fully verified bounded frames and now has an opt-in persistent browser
profile. Its first physical test delivered six frames with forward/release input
and clean owned STOP, at about one frame every six seconds. See the
[play guide](game/doom/play/README.md) and [dated findings](artifacts/doom-play-20261013/README.md)
for the active session, controls and remaining limitations. Optimization and
debugging now follow actual use.

[Latest findings](CURRENT-FINDINGS.md) and the relevant dated evidence report
establish acceptance; an old milestone's “next step” is historical context.
The [visible Doom report](artifacts/doom-visible-20261013/README.md) records
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
