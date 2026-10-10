# Tetris on an Intel i960

Repurposing a retired Mylex DAC960PG RAID controller (Intel **i960RP**) into a
general-purpose computer that runs Tetris. Hobby/bench project, all on the owner's
own hardware.

## Status

- ✅ **Tetris runs as real i960 machine code.** Built with a from-source i960
  cross-toolchain; a small interpreter executes the actual i960 instructions and
  acts as a text terminal (framebuffer + keyboard over shared memory). Two
  self-checks prove the interpreter decodes i960 correctly (below).
- ✅ **Full in-system flash dump recovered and validated.** A constrained
  coherent-DMA kernel module read the card's flash while installed, yielding a
  512 KiB image whose firmware, boot block and x86 BIOS each match independent
  references exactly, with a checksum-valid i960 IBR. See
  [SNAPSHOT-RECOVERY.md](SNAPSHOT-RECOVERY.md) and
  [artifacts/ROM-DUMP-WORKLOG.md](artifacts/ROM-DUMP-WORKLOG.md).
- ⏸️ **Custom-firmware / flash loader: in progress, paused.** The dump corrected
  the real boot geometry (512 KiB flash based at `0xFEF80000`; live IBR at
  `0xFEFFFF30` → boot block, not the firmware payload). A blocker was also found:
  the i960 faults on instruction fetch from internal data RAM, so loaded code must
  live in external DRAM. See [loader/README.md](loader/README.md) and
  [PROJECT-REVIEW.md](PROJECT-REVIEW.md).

The same Tetris binary and I/O model are what would run on the physical card once a
custom-firmware path is finished; today it runs under the interpreter with no
hardware risk. The card boots its own flash firmware at power-on (reset **Mode 2**,
from EBCR `0x0018`), so code can't be loaded purely in software as-wired — hence the
reflash/loader route.

## Layout
- `game/` — the i960 side: `tetris.c`, `io.h` (shared-memory contract), `i960.ld`, `Makefile`.
- `host/` — the Ubuntu side: `emu.c` (i960 interpreter + ANSI terminal), self-checks,
  `kmod/` (PG mailbox probe), `dump/` (the flash-dump kernel module + validators).
- `loader/` — flash loader and Linux sender (paused); see [loader/README.md](loader/README.md).
- `toolchain.sh` — builds the i960 cross-toolchain (binutils 2.27 + gcc 3.3.6).
- `artifacts/` — the validated 512 KiB dump, vendor firmware references, BIOS, logs;
  start at [artifacts/ROM-INVENTORY.md](artifacts/ROM-INVENTORY.md).

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

**ROM dump & flash (current work):**
- [SNAPSHOT-RECOVERY.md](SNAPSHOT-RECOVERY.md) — the validated 512 KiB capture, exact
  4.07-0-29 match, and corrected flash layout.
- [artifacts/ROM-DUMP-WORKLOG.md](artifacts/ROM-DUMP-WORKLOG.md) — how the dump was done,
  what validates it, and the honest limits (staging read, not a certified physical backup).
- [artifacts/ROM-INVENTORY.md](artifacts/ROM-INVENTORY.md) — index of every archived file.
- [host/dump/README.md](host/dump/README.md) — the dump kernel module and validators.
- [DRAM-ANALYSIS.md](DRAM-ANALYSIS.md), [VENDOR-READ-PATH.md](VENDOR-READ-PATH.md),
  [FIRMWARE-HANDLERS.md](FIRMWARE-HANDLERS.md), [FIRMWARE-40729.md](FIRMWARE-40729.md),
  [DUMP-ATTEMPT.md](DUMP-ATTEMPT.md) — supporting analysis.

**Reference:**
- [FINDINGS.md](FINDINGS.md) — consolidated technical findings (hardware, command channel,
  GlobalFlash encoding, firmware protocol, BIOS, toolchain).
- [PROJECT-REVIEW.md](PROJECT-REVIEW.md) — broader review, including the loader blocker.
- [MANUAL.md](MANUAL.md) — build/run the toolchain, game, and emulator; card facts.
- [FIRMWARE-PROTOCOL.md](FIRMWARE-PROTOCOL.md) — the host→i960 mailbox channel and register map.
- [FIRMWARE-PACKAGE.md](FIRMWARE-PACKAGE.md) / [FLASHER.md](FLASHER.md) — Fujitsu firmware
  package, GlobalFlash decoding, and the DOS flasher / MIMG format.
- [BIOS-ANALYSIS.md](BIOS-ANALYSIS.md) — the card's x86 option ROM disassembly.
- [MODE0.md](MODE0.md) / [REFLASH.md](REFLASH.md) — reset-strap and reflash routes to custom code.
- [SESSION.md](SESSION.md) — full session context / handoff.
- [host/globalflash_decode.py](host/globalflash_decode.py) — verified GlobalFlash decoder.
