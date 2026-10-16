# Tetris

Canonical game core, native oracle and validation scripts live here. Tetris
runs on the card through returning firmware callbacks; it does not require
RTEMS. The Linux terminal frontend lives in [host/session](../../host/session/README.md),
and the target wrapper lives in [loader/runtime](../../loader/runtime/README.md).

| File | Purpose |
| --- | --- |
| `tetris.c`, `tetris.h` | Bounded deterministic rules, serialized state and ASCII framebuffer |
| `test_tetris.c`, `check_tetris.py` | Native sanitizer and optional i960 interpreter comparisons |
| `oracle.c`, `check_live.py` | Fresh native replay of the preserved nine T2 card transactions |
| `io.h`, `i960.ld` | Links to shared parent ABI and linker layout |

From the repository root:

```sh
make -C game/tetris test
make -C game/tetris test-live
# Optional, where the cross tools are installed:
python3 game/tetris/check_tetris.py --cross /home/mit/i960/tools/bin/i960-coff-
```

The first command uses ASan/UBSan; the second reads saved evidence and never
opens the card. `make -C game/tetris` builds the original emulator-style target
with the installed cross tools. For the actual returning card payload, use
`make -C loader/runtime`; the shared core is the same.

[Play instructions](../../subprojects/tetris/README.md),
[T4 terminal acceptance](../../artifacts/notes/tetris-t4-20261010.md),
[T5 persistent transport](../../artifacts/notes/tetris-t5-20261010.md).

Old `game/tetris.c`, `game/tetris.h`, oracle/test/script paths are relative
compatibility symlinks, so existing loader includes and `make -C game test`
continue to work. Both Python scripts resolve the canonical path before locating
the repository. Preserve these links when copying the checkout; copying only
the aliases without their targets is not a complete source package. Historical
artifact source snapshots remain unchanged.
