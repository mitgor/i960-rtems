# Card profiles and the i960 port boundary

`dac960pg.json` and `accele160.json` are the explicit, measured board records.
The Python loader validates their schema and refuses unknown cards and
unqualified workflows. PCI selection reads the exact vendor, device and
subsystem tuple from these same records. A profile is **an admission gate**, not
a claim that different controllers share a flash command or memory map.

| Layer | Shared | Per-card implementation |
| --- | --- | --- |
| Firmware | archive/digest/identity discipline | ROM hook and one-shot PG programmer; AcceleRAID STOREIMAGE/FLASHIMAGE path and its exact candidate checks |
| RTEMS | Classic task core, application contract, bounded ownership rules | boot/linker, RAM grant, cache maintenance, timer/IRQ, mailbox/DMA, STOP |
| Doom | pinned DoomGeneric source, i960 ABI, private Newlib, renderer and WAD/cache code | clock adapter, RTEMS image, transport/host bridge and frame ownership |

Build gates use `--card-profile` (defaulting to the historical card in legacy
commands). `rtems/build.py --profile` is a **runtime experiment** selector;
`--card-profile` selects the physical board. The AcceleRAID exclusive-Doom
shell builder accepts `CARD_PROFILE=accele160` and rejects other profiles.
The old playable-Doom builder is explicitly PG-only. The shared Doom engine
records `card_profile` in `build.json`; platform build and engine admission
carry it forward. Old manifests without a card field remain readable for
archived experiments. New images should always carry the field.

To add an i960 card, first archive and hash a read-only stock image and record
all four PCI ID words. Add a JSON record and a *disabled* workflow matrix.
Then build and test a separate firmware reader/patcher with exact preimages,
bounded ranges and post-write readback. Prove a returning RAM function,
ownership and recovery before enabling RTEMS. Supply card-specific linker,
timer/IRQ, cache and DMA code, with STOP and timeout tests. Finally select the
shared i960 Doom engine and write a clock adapter plus a frame/WAD bridge for
the new board. Enable each workflow only after its individual qualification.
Never reuse another board's flash offsets, cache register values or PCI BDF.

Offline checks: `python3 -m unittest card_profiles.test_profile` and
`python3 rtems/transport/test_card_select.py`. These do not test real hardware.
