# Session handoff — i960 project (context for a future session)

> **What this project is (read first, so nothing here is misread):** the user owns a
> retired Mylex DAC960PG RAID controller (built on an Intel i960RP CPU) and one Ubuntu
> box that exists *only* for this hobby project. The goal is to **repurpose that i960 as
> a small general-purpose computer and run Tetris on it in text mode** — classic vintage-
> hardware tinkering on their own equipment. Everything done here is on the user's own
> machine and card: building a cross-compiler, writing a game, writing an emulator, and
> reading/strapping the card's own registers. No networks, services, or third-party
> systems are involved. Nothing is exfiltrated. This is a workbench repurposing project,
> full stop.

## The machine & how to reach it
- Remote box: `mit@192.168.2.75`, passwordless sudo, Ubuntu 22.04.5, kernel 6.8, 12 cores.
- One persistent multiplexed SSH connection is set up (Mac side) at `~/.ssh/i960.conf`:
  ```bash
  ssh -F ~/.ssh/i960.conf i9 '<cmd>'     # alias i9 -> mit@192.168.2.75
  scp -F ~/.ssh/i960.conf f i9:i960/...  # copy
  ```
  Keep SSH output short and batched (minimum tokens; no screen capture).
- Remote project tree lives in `~/i960/` (toolchain in `~/i960/tools/bin`, on PATH).

## The card (all reads were non-destructive; driver left as found)
- Mylex DAC960PG. PCI: bridge `37:09.0 [8086:0960]` (i960RP), controller `37:09.1 [1069:0010]`.
- Linux `myrb` driver owns `37:09.1`; no disks attached. Unbind/bind:
  `echo 0000:37:09.1 | sudo tee /sys/bus/pci/drivers/myrb/{unbind,bind}` (rebind is slow,
  ~90 s, because the driver probes the controller — this is normal, not a hang).
- Host sees one fixed 8 KB BAR0 window at PCI `0xee000000`. ATU window registers did not
  accept host-side writes, so the window can't be moved in software.
- **Boot/mode:** the i960 boots from its Initialization Boot Record (IBR) at fixed
  `0xFEFFFF30` (flash). Mode is set by the `RST_MODE#`/`RETRY` straps sampled at `P_RST#`.
  Live `EBCR` (bridge fn0, PCI cfg offset `0x40`) read back `0x0018` ⇒ **Mode 2**
  (core boots flash, primary PCI accepts config). See `MODE0.md` for the full analysis.
- **Consequence:** you cannot software-load code onto this specific card as-wired; the
  core always runs its flash firmware. So the game runs in an emulator (below), using an
  I/O model that would carry over to real silicon after a flash reprogram.

## The toolchain (built from source on the box; recipe = `toolchain.sh`)
- Last releases that support i960: **binutils 2.27** (gas keeps only the ELF flavour) +
  **GCC 3.3.6** (COFF target, driven through the ELF as/ld via `i960-coff-*` symlinks).
- Use `i960-coff-gcc -mrp -O2 -ffreestanding -fno-builtin` (`-mrp` = i960RP core).
  Output is `elf32-i960`, **little-endian**; C symbols get a leading `_`.
- GCC 3.3 inserts a `__main()` ctor call into `main`; provide an empty `void __main(void){}`
  stub to avoid pulling libgcc's `atexit`.
- Build gotchas on a modern host are baked into `toolchain.sh` (gnu89, -fcommon, no fortify).

## The deliverable: emulator harness that runs the i960 code
- `game/` — i960 side: `tetris.c` (freestanding, all 7 pieces/rotate/collide/clear/score/
  gameover), `io.h` (shared-memory I/O contract), `i960.ld`, `Makefile`.
- `host/emu.c` — a compact i960 **interpreter** (runs on the box's x86) that loads the ELF,
  builds the i960 call frame, decodes/executes the actual i960 instruction set GCC emits,
  and renders a framebuffer to the terminal + feeds keystrokes. I/O model:
  framebuffer `fb[24][80]`, `doorbell` (game yields a frame), `key`, `frame`, `halt` — the
  same model you'd use with the real card's shared memory.
- Build & play: `cd ~/i960/game && make && cd ../host && gcc -O2 -o emu emu.c &&
  ./emu ../game/tetris.elf` (keys `a`/`d`/`w`/`s`/`q`). `build.sh` syncs+builds+self-checks.

## Verification (evidence, not assertion)
Two self-checks compile the *same C* for i960 (under the interpreter) and natively on x86;
outputs match exactly ⇒ the interpreter decodes i960 correctly:
- `./emu -t test.elf`   → `-135781` == `./ref`        (arith, shifts, mul, divi/remi, loops, call/ret)
- `./emu -t test_clear.elf` → `200110` == `./ref_clear` (the line-clear algorithm)

## Interpreter bugs found & fixed during bring-up (don't reintroduce)
1. Register map is **0–15 = locals r0–r15, 16–31 = globals g0–g15** (not the reverse).
2. `ret` uses the **full** RIP; only the PFP carries return-type bits in its low 4 bits.
   Masking RIP corrupts 8-aligned return addresses → infinite call loop.
3. Opcodes **0x20–0x27 are `test{cond}`** (set a reg from the condition code, no branch);
   only **0x30–0x3f** are `cmpob*/cmpib*` compare-and-branch. Don't lump them together.
4. i960 `call`/`callx`/`ret` do the frame work in hardware (no register-saving prologue);
   the interpreter models it with a stack of local register files + `g15`=FP.

## Real-hardware paths (optional, documented in MODE0.md)
- **Mode 0 strap mod:** board-level only (80960RP is BGA — strap pins are balls under the
  chip, no leg to cut). One resistor: `RST_MODE#` pull-up → weak pull-down. **Insufficient
  alone** — on reset release the core still boots the flash IBR.
- **Reflash the boot flash** (external programmer, mandatory backup): the actual way to run
  custom code on the silicon; makes the strap mod unnecessary. A bad write bricks the card.
- Lowest risk by far: the emulator harness already runs the i960 code today.

## Git
This project is its own repo **inside** `/Users/mit/Documents/!Projects/i960` (I ran
`git init` here). Note: `/Users/mit` itself is *also* a git repo (unexpected) — **never
`git add -A` from the project dir thinking it's scoped; it would stage the whole home
directory.** Always add explicit paths, and the nested repo keeps this project isolated.

## Status: complete
Toolchain ✓, Tetris ✓, interpreter ✓, both self-checks pass ✓, card characterized ✓,
Mode 0 / reflash paths documented ✓. See `README.md` and `MANUAL.md` for the rest.
