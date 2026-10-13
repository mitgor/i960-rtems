# Forcing i960RP Mode 0 on the Mylex DAC960PG — hardware-mod manual

**Honest verdict first (read this before reaching for a soldering iron):**

1. The 80960RP is a **BGA** (HL-PBGA, perimeter ball array, ~35 mm body). The strap
   pins are **balls underneath the chip** — there is *no* gull-wing lead to cut or lift.
   Every mod here is therefore a **board-level** change (a strap resistor), not a
   chip-pin change.
2. **Mode 0 by itself will NOT run your code.** When you release the core from reset it
   still fetches its boot record (IBR) from flash at `0xFEFFFF30` and runs the **Mylex
   firmware**. Mode 0 only buys the host a window to set up the card *before* the core
   starts. To actually run your own program you must **control what the IBR points to**,
   which means **reflashing the boot flash** (see §6). If you reflash, you don't even
   need Mode 0.
3. So this mod is **optional and low-value on its own, and physically hard** (fine-pitch
   SMD rework, no board schematic). Do it only if you want the clean "host holds the core
   in reset, loads DRAM, then hands off" bring-up model *in combination with* a reflashed
   loader. For most goals, **skip straight to §6 (reflash)**.

Everything below is for your own card, bench use, hobby/repurposing. Back up the flash
(§6.1) before touching anything.

---

## 1. How the mode is selected (datasheet facts)

The i960Rx samples two pins on the **rising edge of `P_RST#`** (PCI reset deasserting):

| Pin (signal)                 | Reset-sampled meaning          |
|------------------------------|--------------------------------|
| `D/C# / RST_MODE#`           | RST_MODE# strap                |
| `WIDTH / HLTD1 / RETRY`      | RETRY strap                    |

Both are **multiplexed** pins: at the P_RST# edge they're read as straps, then they
revert to their normal function (`D/C#` is a local-bus output; `HLTD1` an output). The
board sets the strap with a **weak pull resistor** to a rail; the resistor is weak enough
not to fight the pin's later output function.

**Initialization modes (manual Table 11-1):**

| RST_MODE# | RETRY | Mode | Primary PCI            | i960 core      |
|-----------|-------|------|------------------------|----------------|
| 0         | 0     | **0**| accepts transactions   | **held in reset** |
| 0         | 1     | 1    | retries config         | held in reset  |
| 1         | 0     | 2    | accepts transactions   | initializes    |
| 1         | 1     | 3 (default) | retries config  | initializes    |

In Mode 0 the host can set up the bridge, ATU, memory controller, and **load code into
local DRAM**, then start the core by **clearing EBCR bit 1 (Core Processor Reset)**.

EBCR = PCI-to-PCI bridge config space, **offset 0x40** (bridge function). Strap-derived
defaults: bit 1 ← inverse of RST_MODE# pin (pin LOW ⇒ bit SET); bit 2 ← RETRY pin
(pin HIGH ⇒ bit SET).

## 2. Current state of *this* card

```
# bridge function 37:09.0, EBCR:
sudo setpci -s 37:09.0 40.w      ->  0018
```
`0x0018` → bit1=0, bit2=0 ⇒ **RST_MODE# strapped HIGH, RETRY strapped LOW ⇒ Mode 2**
(core boots flash, primary PCI accepts config — which is why it enumerates cleanly).

**To reach Mode 0 we need `RST_MODE# = LOW` at reset. RETRY is already LOW — leave it.**
So the whole mod is: **flip the RST_MODE# strap from pull-up to pull-down.**

## 3. Locate the RST_MODE# strap (the hard part)

No board schematic is public, and the ball is under the BGA, so you must find the
**strap resistor** on the `D/C#/RST_MODE#` net:

1. Identify the exact i960RP revision from its top marking and pull the matching Intel
   datasheet (i960 RX datasheet, `bitsavers.org/components/intel/i960/`) for the
   **ballout** — find the `D/C#/RST_MODE#` ball coordinate (e.g. something like `A;`-grid).
2. On the board, that ball breaks out to a via near the chip edge. With a **multimeter in
   continuity mode**, and power off, probe the small resistors clustered around the i960
   for one that connects between that net and a rail:
   - one end to **+3.3 V** (through the resistor) ⇒ it's the current **pull-up** (this is
     the one to change), or one end to the net and the other to the local-bus signal.
   - Confirm by checking the other candidate straps (`WIDTH`, `RETRY` on the
     `WIDTH/HLTD1/RETRY` ball) to make sure you found the right net, not a neighbor.
3. If you cannot positively identify it with a meter, **stop** — guessing risks the
   local-bus `D/C#` net and will brick the card. This step is the real gate on feasibility.

## 4. Make the change

Goal: net `RST_MODE#` reads **LOW** at the P_RST# rising edge.

- If you found a **pull-up to 3.3 V**: remove it and fit a **pull-down to GND**
  (**~4.7 kΩ–10 kΩ**, weak so it doesn't fight the `D/C#` output). Lift the existing
  resistor with hot air / fine iron, bridge the net to a nearby ground pad through the
  new resistor.
- Keep it **weak** (≥4.7 kΩ). A hard tie to GND would fight `D/C#` during normal local-bus
  cycles and can damage the driver.
- Leave RETRY untouched (already LOW).

## 5. Verify

Power up in the host and re-read EBCR:
```
sudo setpci -s 37:09.0 40.w
```
- **bit 1 now = 1** (value like `0x001A`) ⇒ core is **held in reset** ⇒ Mode 0 achieved.
- The card will **not** present as a working RAID controller anymore (expected — the core
  is halted). `lspci` should still show the functions and BAR0.

Bring-up from Mode 0 (host side, Linux):
1. `echo 0000:37:09.1 | sudo tee /sys/bus/pci/drivers/myrb/unbind` (release the RAID driver).
2. `setpci` to size/enable BAR0, map it with `/dev/mem` or a tiny UIO/kernel shim.
3. Program the memory controller + ATU, copy your image into local DRAM.
4. **Clear EBCR bit 1** (`sudo setpci -s 37:09.0 40.w=0018`) to release the core.
5. …at which point **§6's caveat bites**: on release the core fetches the IBR from flash.

## 6. The part that actually makes it a general-purpose computer: reflash

Because the core always boots the IBR at `0xFEFFFF30` (flash), the robust path is to put
**your own** IBR + startup in the boot flash. Then any mode boots your code, and Mode 0
simply lets the host pre-stage DRAM first (nice, not required).

1. **Back up first.** Identify the flash chip (markings near the i960, often a PLCC/TSOP
   NOR like Am29F0xx / AT49F0xx). Read it out with an **external programmer** (TL866/
   XGecko + clip, or desolder). Keep two copies of the original image — this is your only
   un-brick.
2. Study the original image: the i960 IBR (32 bytes at the top of the flash bank) holds
   the initial bus/memory config words and the pointers to the PRCB and first instruction.
3. Build your own image with the i960 toolchain in this repo: an IBR that sets up the
   memory controller for the board's DRAM/flash banks, a startup that sets FP/SP, and your
   program (or a tiny loader that jumps to code the host left in DRAM, à la our Tetris
   `io.h` framebuffer/mailbox model).
4. Flash it back with the programmer. Verify. If it hangs, restore the backup.

**Risks:** fine-pitch SMD/BGA-adjacent rework, ESD, and a wrong flash write bricks the
card. The flash backup is mandatory. None of this is reversible by software.

---

## Bottom line

- **Mode 0 strap mod:** board-level only (BGA), one resistor (`RST_MODE#` pull-up→pull-down),
  hard to locate without a schematic, and **insufficient by itself** to run your code.
- **Reflashing the boot flash** is what actually lets the i960 run your program, and it
  makes the strap mod unnecessary. If the goal is "i960 as a general-purpose computer,"
  §6 is the real manual; §3–§5 are an optional refinement.
- Compare effort: the **emulator harness already in this repo runs your i960 code today**
  with zero hardware risk and the same I/O model you'd use after a reflash.
