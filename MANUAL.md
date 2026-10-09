# i960 Project — Execution Manual (handoff for next session)

Goal: **run Tetris on the i960, text mode.** Game logic executes as i960 machine
code; the Ubuntu host is a dumb terminal (renders a framebuffer, feeds keys).

## 1. Access the remote machine

One persistent SSH connection is already configured at `~/.ssh/i960.conf` (Mac side).
Use the alias — it multiplexes over one socket (ControlPersist 4h), so it's cheap:

```bash
ssh -F ~/.ssh/i960.conf i9 '<command>'      # mit@192.168.2.75, passwordless sudo
scp -F ~/.ssh/i960.conf file i9:path/        # copy to remote
```

Spend minimum tokens: run remote commands directly over SSH, batch them, keep output
short (`| tail`, `| cut -c1-N`). Do NOT use screen capture / browser for this.

## 2. The toolchain (already built on remote)

In `~/i960/tools/bin` on the remote, on `PATH` via `~/.bashrc`. Rebuild recipe:
[toolchain.sh](toolchain.sh) (also at `~/i960/toolchain.sh` remote).

- `i960-coff-gcc` = GCC 3.3.6 (last gcc with i960). Use `-mrp` for the i960RP core.
- `i960-elf-{as,ld,objcopy,objdump,...}` = binutils 2.27 (last gas with i960, ELF only).
- GCC targets COFF but drives the ELF as/ld through `i960-coff-*` symlinks. Output is
  `elf32-i960`, **little-endian**. C symbols get a leading `_` (`main` -> `_main`).
- Version limits are hard: binutils >=2.29 dropped i960; gas 2.27 only keeps ELF flavour.

Compile/link/inspect:
```bash
i960-coff-gcc -mrp -O2 -ffreestanding -c foo.c -o foo.o
i960-elf-ld -T i960.ld foo.o start.o -o foo.elf
i960-elf-objdump -d foo.elf        # see exactly which opcodes GCC emitted
```

## 3. The real card — what we learned (read-only, nothing changed persistently)

- Mylex DAC960PG RAID controller, Intel **i960RP** core.
  - Bridge: PCI `37:09.0` `[8086:0960]`. Controller: `37:09.1` `[1069:0010]`.
- Linux `myrb` driver binds `37:09.1`. No disks on it. Unbind / rebind:
  ```bash
  echo 0000:37:09.1 | sudo tee /sys/bus/pci/drivers/myrb/unbind
  echo 0000:37:09.1 | sudo tee /sys/bus/pci/drivers/myrb/bind
  ```
- Host sees ONE fixed 8 KB memory window (BAR0) at PCI `0xee000000`. The ATU config
  registers (offsets 0x40/0x44) did not accept writes from the host side → can't move
  the window in software.
- **Can we load our own code onto the card?** Not in software as-wired. i960Rx manual
  (Intel doc 272736, `datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF`): a host
  can load code only in **Mode 0** (CPU held in reset), then clear EBCR bit 1
  (Core Processor Reset) to start it. Reset mode is strapped by the RST_MODE#/RETRY
  pins at P_RST#. Live read of the card's EBCR (bridge `37:09.0`, PCI config offset
  0x40): **`0x0018`** → bit 1 = 0 → board is in **Mode 3**: the i960 boots its own
  flash firmware at power-on and is already running. The strap is hardware; software
  can't switch it. So on THIS card the clean host-load path is closed without a board
  mod or reflashing the firmware (last resort, needs an external programmer, risky).
  - i960 boots from the Initialization Boot Record (IBR) at fixed addr `0xFEFFFF30`.

Because of this, Tetris runs in our own **i960 interpreter on the Ubuntu box**
(task 2). The I/O model (framebuffer + key mailbox in shared memory) is chosen so the
exact same binary would run on the card if loading ever becomes possible.

## 4. How we "execute code" — the harness (the deliverable)

Flat little-endian RAM (1 MB, base 0). Program loaded from the ELF. Memory-mapped I/O
struct at a fixed address both sides agree on (see `game/io.h`):

- `fb[24][80]` : framebuffer, ASCII. Host renders it to the terminal.
- `key`        : last keypress byte, written by host.
- `doorbell`   : game stores here to yield; interpreter services I/O synchronously
                 (render frame + poll key), then returns. One doorbell = one frame.
- `frame`      : monotonic frame counter (host-maintained), game uses it for gravity.
- `halt`       : game stores non-zero → interpreter stops (game over / quit).

Interpreter (`host/emu.c`, runs on remote x86): loads ELF into RAM, sets up the initial
i960 call frame (FP/SP), executes REG/MEM/COBR/CTRL-format instructions, traps stores to
`doorbell`/`halt` as device actions, renders `fb` to the terminal with ANSI, reads stdin
(raw mode) for keys. This genuinely decodes i960 machine code — NOT a recompile to x86.

Build which opcodes to implement from the disassembly (`objdump -d`), not from guessing.

### Self-check (must pass before claiming it runs)
A tiny i960 program computes a checksum over a buffer; the SAME C compiled natively
computes it too; the two must match. If they differ, the interpreter is wrong — debug
the opcode, don't paper over it. (superpowers:systematic-debugging)

## 5. Status / next steps

- [x] SSH + sudo + persistent connection.
- [x] i960 cross-toolchain built & smoke-tested on remote.
- [x] Card characterized; host-load path confirmed closed (Mode 3 strap). Driver rebound.
- [x] `game/`: tetris.c (freestanding), i960.ld, io.h. (No crt0 needed — the interpreter
      builds the initial i960 call frame and enters `_main` directly.)
- [x] `host/emu.c`: i960 interpreter + terminal front-end.
- [x] Self-check passes (CPU + line-clear match native exactly); Tetris playable over SSH.

### Interpreter bugs found & fixed during bring-up (for reference)
1. Register map was inverted: on i960, reg numbers **0–15 = locals r0–r15, 16–31 = globals
   g0–g15** (not the reverse).
2. `ret` must use the **full** RIP; only the PFP (frame pointer) carries return-type bits
   in its low 4 bits. Masking RIP corrupted 8-aligned return addresses → infinite calls.
3. Opcodes **0x20–0x27 are `test{cond}`** (set reg from condition code), NOT compare-and-
   branch. Only **0x30–0x3f** are cmpob*/cmpib*. Lumping them together branched to garbage.

Lazy rule in force (ponytail): implement only the opcodes GCC actually emits; no full
i960 ISA. Leave the calibration knob for timing (gravity frames) tunable.
