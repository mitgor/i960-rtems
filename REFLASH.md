# Reflashing the DAC960PG boot flash to run your own i960 code

This is the **fast, reliable** path to a general-purpose i960: whatever sits in the card's
boot flash is what the core runs at power-on, in **any** reset mode — so no strap mod
(MODE0.md) is needed. You replace Mylex's firmware with your own boot record + code.

Your own hardware, bench use. **The original flash image is your only un-brick — back it
up twice before writing anything.**

---

## 0. The one idea that makes this safe

The i960 reads an **Initialization Boot Record (IBR)** from flash at power-on. The IBR's
first bytes are the **boot-bus config** (PMCON) for *this board's* flash/DRAM timing and
width — values you cannot easily derive, but which are **already correct in the stock
image**. So the method is:

> **Dump the stock flash → keep its IBR bus-config bytes verbatim → only redirect the
> "first instruction" and "PRCB" pointers to your code → fix one checksum word → append
> your code into unused flash → write back.**

That reuses Intel/Mylex's hard-won memory setup and changes the minimum.

## 1. The boot structures (datasheet facts)

**IBR** — 12 words at `0xFEFFFF30` (the top of external memory; `0xFF000000`+ is on-chip
register space):

| CPU address | Word | Meaning |
|-------------|------|---------|
| `FEFFFF30`  | 0 | PMCON14_15 byte 0  (boot-bus config; byte in bits 7:0, rest reserved) |
| `FEFFFF34`  | 1 | PMCON14_15 byte 1 |
| `FEFFFF38`  | 2 | PMCON14_15 byte 2 |
| `FEFFFF3C`  | 3 | PMCON14_15 byte 3 |
| `FEFFFF40`  | 4 | **First instruction** — address the core jumps to |
| `FEFFFF44`  | 5 | **PRCB pointer** — address of the Process Control Block |
| `FEFFFF48`–`FEFFFF5C` | 6–11 | checksum / bus-confidence words |

**Boot checksum (do not skip):** the core reads the IBR's **8 words** at startup. The i960
manual phrases the check as summing the 8 words with the constant `0xFFFFFFFF` and booting
only if the result is 0 — i.e. `word0 + … + word7 ≡ 1`. **Measured reality differs:** on both
the vendor images and this card's recovered dump, `word0 + … + word7 ≡ 0 (mod 2³²)` exactly
(verified byte-for-byte by `host/mkimage.py`, which reproduces the stock checksum word).
Follow the measurement — solve the free "checksum word" so the 8 words sum to **0**. Get this
wrong → the core asserts **FAIL#** and halts with a fail code of form `0xFEFFFFnn` (dead card).

**PRCB** — pointed to by IBR word 5; holds base addresses the core caches at init: fault
table, control table, interrupt table, system procedure table, initial AC image, fault
config word, and the initial stack pointer. The PRCB and the tables it names must be in
memory the core can read **before** it runs your first instruction → put them in **flash**
(not DRAM, which isn't up yet). The i960 toolchain's standard startup provides minimal
versions.

**Address → flash-offset mapping:** the flash's top byte maps to `0xFEFFFFFF`. For a flash
of size `S`, CPU address `A` in the boot region is flash offset `A - (0xFF000000 - S)`.
So the IBR starts at offset `S - 0xD0` (e.g. for a 512 KB / `0x80000` flash: `0x7FF30`).
The reset image lives at the very top of the chip; the rest of the chip is free for your
code.

**Confirmed on this card (from the recovered 512 KB dump — see
[SNAPSHOT-RECOVERY.md](SNAPSHOT-RECOVERY.md)):** flash size `S = 0x80000`, base
`0xFF000000 - 0x80000 = 0xFEF80000`. The IBR sits at offset `0x7FF30` → `0xFEFFFF30`, with
firstIP `0xFEFFC400`, PRCB `0xFEFFD4D0`, and `sum8 = 0`. Crucially, firstIP/PRCB point into
the **boot block** (vendor `FWTCBBLK`, at flash offset `0x7C000`), **not** into the main
firmware payload (at `0x30000`). A custom image must therefore keep the boot block's IBR and
startup intact (or relocate deliberately) and place new code in free space — redirecting a
"firmware-payload IBR," as an earlier draft of `mkimage.py` assumed, is the wrong structure
and will not boot.

## 2. Identify the flash chip(s)

1. Power off, pull the card. Find the flash near the i960 — usually a **PLCC-32 NOR**
   (sockets make this easy; markings like `Am29F010`/`Am29F040`, `AT29C010`,
   `SST39SF010/040`, `28F0xx`). Note the size from the part number (128 KB–512 KB typical).
2. **Dual-flash boards exist** (some DAC960 variants populate two EEPROMs, e.g. near
   U47/U34). If there are two, they're likely a **16-bit even/odd pair** — dump both and
   determine the interleave (byte 0→chip A, byte 1→chip B, …). The IBR's one-byte-per-word
   spacing suggests the **boot region is read 8-bit**, so confirm width from the stock
   dump's IBR layout.
3. Read the **JEDEC ID** with your programmer to confirm part, size, and sector map.

## 3. Dump and archive the stock image (mandatory)

> **We now have a validated in-system 512 KB image** of this card
> (`artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin`; firmware,
> boot block and BIOS all match independent references, IBR checksum valid). **But it was
> read through the controller's command path — a staging copy — not off the chip.** So it is
> a strong *reference* (diff your programmer read against it), not a certified un-brick
> backup. The external-programmer read below is still mandatory before you write anything.

- Best: an **external programmer** (TL866II Plus / XGecko) with a **PLCC clip**, or desolder
  the chip into a socket/adapter. Read it **twice**, confirm the two reads are identical,
  and keep both plus a third copy off-machine.
- Record: chip part/size, and for dual-flash, which socket is which byte lane.
- From the dump, extract and **save the 12 IBR words** at offset `S - 0xD0`. These are your
  known-good PMCON bytes and the checksum word layout to mimic.

## 4. Build your replacement image (use this repo's toolchain)

1. Write a boot stub for i960 — `boot.s` + a linker script that places:
   - the **IBR** at `0xFEFFFF30` with: PMCON words **copied verbatim** from the stock dump;
     First Instruction = your `_start`; PRCB pointer = your PRCB.
   - a minimal **PRCB** + fault/interrupt/control/sysproc tables in flash (the toolchain's
     `crt0`/libgloss bits give workable defaults).
   - `_start`: set FP/SP, bring up DRAM only if you need it, then run your program (reuse the
     freestanding model from `game/` — e.g. the `io.h` framebuffer/mailbox contract).
2. Compute the **checksum word** so `sum(word0..word7) ≡ 1 (mod 2³²)`; write it into the
   corresponding IBR slot. (A 6-line host script over the assembled image does this.)
3. `i960-elf-objcopy -O binary` the linked ELF; create a flash image of exactly size `S`,
   place your reset image at the top (IBR at `S-0xD0`), put code/tables where your linker
   script mapped them, pad the rest with `0xFF`. For a dual-flash 16-bit pair, de-interleave
   into two files (even/odd bytes).
4. Sanity-check the image offline: re-run the checksum verify; disassemble the First
   Instruction target with `i960-elf-objdump` to confirm it's your `_start`.

## 5. First target: proof-of-life, not Tetris

Flash something trivial first to validate the whole boot→run→observe chain:

- Minimal `_start` that sets up the **ATU inbound window** to expose a page of local memory
  through the card's **BAR0** (host-visible at PCI `0xee000000`), writes a **magic signature**
  (e.g. `0xC0FFEE01`) there, then spins.
- Host check: `sudo setpci` to enable BAR0 + unbind `myrb`, map `0xee000000` via `/dev/mem`,
  read the magic. If you see it → your i960 code is running from your flash. **That is the
  milestone.** Only then port the real program (Tetris via the `io.h` model).
- If the host sees nothing / card is dead: the checksum or a PMCON word is wrong → restore
  the stock image and recheck step 4.

## 6. Write it

- With the external programmer: erase, write your image(s), **verify** (programmer read-back
  == file). For dual-flash, write both lanes.
- Reinstall the card, power on, run the step-5 host check.
- **Recovery:** any failure → reflash the stock image you saved in §3. As long as that
  backup is good and the chip is socketed/clip-accessible, the card is un-brickable.

## 7. After the first success

Once your own code runs from flash, it can **reprogram the flash in-system** (the i960 can
erase/program its own NOR, which is how Mylex shipped field updates) — so further iterations
no longer need the external programmer. Keep the stock backup regardless.

---

## Risks / reality check
- SMD/socket rework + ESD; a wrong write or bad checksum bricks the card until you restore
  the backup. The backup is non-negotiable.
- The unknowns are the flash geometry/width (settled by the dump + JEDEC ID) and the PMCON
  bytes (settled by copying the stock IBR). Everything else is standard i960 bring-up that
  this repo's toolchain already produces.
- Lowest-risk alternative, already working today: the emulator harness in `host/emu.c` runs
  the same i960 binary with no hardware risk. Reflashing is worth it only for real silicon.
