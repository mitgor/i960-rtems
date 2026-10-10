# Tetris on an Intel i960

**In-system firmware recovery succeeded.** See [SNAPSHOT-RECOVERY.md](SNAPSHOT-RECOVERY.md)
for the validated 512 KiB capture, exact 4.07-0-29 firmware match, saved files,
and corrected flash layout. [CLAUDE.md](CLAUDE.md) contains current agent guidance.

See [PROJECT-REVIEW.md](PROJECT-REVIEW.md) for the broader review. The loader
still has an internal-RAM execution architecture blocker.

Runs Tetris as **native i960 machine code**. The game is compiled with a from-source
i960 cross-toolchain; a small interpreter executes the i960 instructions and acts as a
text terminal (framebuffer + keyboard over shared memory). The same binary and I/O model
are what would run on the physical Mylex DAC960PG (i960RP) card — see [MANUAL.md](MANUAL.md)
for why loading onto that specific card is blocked in software (Mode 3 reset strap).

## Layout
- `game/` — the i960 side: `tetris.c`, `io.h` (shared memory contract), `i960.ld`, `Makefile`.
- `loader/` — flash loader and Linux sender; see [loader/README.md](loader/README.md)
  and [loader/REVIEW.md](loader/REVIEW.md) for protocol fixes and validation status.
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

## Documentation

- **[FINDINGS.md](FINDINGS.md)** — consolidated technical findings (start here): hardware,
  the in-system command channel, the cracked GlobalFlash encoding, the firmware command
  protocol, BIOS, toolchain.
- [MANUAL.md](MANUAL.md) — build/run the toolchain, game, and emulator; card facts.
- [FIRMWARE-PROTOCOL.md](FIRMWARE-PROTOCOL.md) — the host→i960 mailbox channel, proven in-system
  (Enquiry) with a kernel module; register map and milestones.
- [FIRMWARE-PACKAGE.md](FIRMWARE-PACKAGE.md) — the official Fujitsu firmware package, the
  cracked GlobalFlash encoding, and the StoreImage/flash-write protocol.
- [BIOS-ANALYSIS.md](BIOS-ANALYSIS.md) — disassembly of the card's x86 option ROM.
- [MODE0.md](MODE0.md) — forcing i960 Mode 0 by hardware strap (and why it's not the path).
- [REFLASH.md](REFLASH.md) — reflashing the boot flash to run custom i960 code.
- [SESSION.md](SESSION.md) — full session context / handoff.
- [host/globalflash_decode.py](host/globalflash_decode.py) — verified GlobalFlash decoder.
- [artifacts/](artifacts/) — the card's x86 BIOS dump + disassembly.
