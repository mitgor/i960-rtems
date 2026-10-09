# Tetris on an Intel i960

Runs Tetris as **native i960 machine code**. The game is compiled with a from-source
i960 cross-toolchain; a small interpreter executes the i960 instructions and acts as a
text terminal (framebuffer + keyboard over shared memory). The same binary and I/O model
are what would run on the physical Mylex DAC960PG (i960RP) card — see [MANUAL.md](MANUAL.md)
for why loading onto that specific card is blocked in software (Mode 3 reset strap).

## Layout
- `game/` — the i960 side: `tetris.c`, `io.h` (shared memory contract), `i960.ld`, `Makefile`.
- `host/` — the Ubuntu side: `emu.c` (i960 interpreter + ANSI terminal), self-check programs.
- `toolchain.sh` — builds the i960 cross-toolchain (binutils 2.27 + gcc 3.3.6).
- `MANUAL.md` — full execution/build notes and the real-card findings.

## Build & run (on the Ubuntu box, toolchain already in ~/i960/tools)
```
cd ~/i960/game && make                 # -> tetris.elf (i960)
cd ~/i960/host && gcc -O2 -o emu emu.c  # host interpreter
./emu ../game/tetris.elf                # play:  a/d move, w rotate, s drop, q quit
```

## Verify it really executes i960 code
```
./emu -t test.elf        # CPU self-check: must match ./ref        (-135781)
./emu -t test_clear.elf  # line-clear logic: must match ./ref_clear (200110)
```
Each test runs the *same* C compiled both for i960 (under the interpreter) and natively;
matching outputs prove the interpreter decodes i960 instructions correctly.
