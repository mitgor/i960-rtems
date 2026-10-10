# i960 flash loader (`loader/`)

A two-stage firmware for the DAC960PG: **stage 1** is a tiny loader that lives in
the card's boot flash; **stage 2** is whatever program the host pushes over PCI at
runtime. Flash the loader **once**, then iterate on real code (Tetris, test stubs,
anything) by sending it over the bus — no reflash per change, no external
programmer per change.

Why this beats the full-image reflash (`../host/mkimage.py` used alone): you take
the brick risk exactly once, for a ~few-hundred-byte loader that never needs to
change. Everything after is a software push you can repeat freely.

## The channel

The loader talks to the host through the i960Rx **Messaging Unit** — four 32-bit
hardware registers in the card's BAR0 window. They are silicon, not firmware, so
they work the instant the loader runs: **no DRAM, no memory-controller setup**.
Mapping (`i960 local 0x1300+X` ⇒ `host BAR0+X`), confirmed against the stub, the
kernel module, and the stock 80960Rx layout:

| i960 local | host BAR0 | reg  | dir        | use                          |
|------------|-----------|------|------------|------------------------------|
| `0x1310`   | `+0x10`   | IMR0 | host→i960  | command argument             |
| `0x1314`   | `+0x14`   | IMR1 | host→i960  | `(seq<<16)\|opcode` (commits)|
| `0x1318`   | `+0x18`   | OMR0 | i960→host  | `(ackseq<<16)\|status`       |
| `0x131C`   | `+0x1C`   | OMR1 | i960→host  | read-back (OP_READ)          |

Handshake is a **sequence number** (not the doorbell IRQ bits): host writes IMR0
then bumps the seq in IMR1; loader echoes the consumed seq in OMR0's high half.
Polling, no interrupts, and robust to a host restart mid-session.

Opcodes (`mu.h`): `PING`, `SET_ADDR`, `WRITE` (word, pointer auto-increments),
`READ`, `GO`. A whole program is `SET_ADDR` + a stream of `WRITE` + `GO`.

## Files

| file          | side  | what                                                        |
|---------------|-------|-------------------------------------------------------------|
| `mu.h`        | both  | register offsets + opcodes (shared contract)                |
| `start.s`     | i960  | reset entry: stack into internal RAM, call the C loader     |
| `loader.c`    | i960  | the protocol loop (no static storage, no libgcc, shallow)   |
| `loader.ld`   | i960  | links the loader at its flash run address                   |
| `hello.c`     | i960  | demo payload: writes `0xBEEF00EE` to OMR0 (proves hand-off) |
| `payload.ld`  | i960  | links a tiny payload into internal RAM at `0x200`           |
| `loadctl.c`   | host  | sender over `/dev/mem` BAR0                                 |
| `Makefile`    | both  | builds all of the above                                     |

## Build

On the remote box (cross-toolchain on PATH):

```bash
cd ~/i960/loader && make          # -> loader.bin, hello.bin, loadctl
```

Assemble the loader into a flashable image (reuses the validated builder; needs a
decoded stock firmware image as the IBR/PRCB donor):

```bash
make image STOCK=~/fwpkg/decoded/<stock>.bin   # -> loader-fw.img
```

## Bring-up, in milestones (each is a real checkpoint)

**1 — loader boots, channel works (no DRAM).** Flash `loader-fw.img`, power on.
```bash
sudo ./loadctl 0xee000000 status     # OMR0 low half == 0x600D (READY)
sudo ./loadctl 0xee000000 ping       # ack status=0x0002
```
READY at `BAR0+0x18` means your loader is running from flash and the bidirectional
channel is live. This is the milestone — nothing below matters until it passes.

**2a — load and run code (still no DRAM).** Push the demo into internal RAM and jump:
```bash
sudo ./loadctl 0xee000000 load 0x200 hello.bin
sudo ./loadctl 0xee000000 go   0x200
sudo ./loadctl 0xee000000 status     # OMR0 now 0xBEEF00EE -> loaded code ran
```
The magic can only change if the i960 executed code the host sent. Full chain proven.

**2b — real programs (needs DRAM).** Internal RAM is ~1 KB (shared with the loader
stack), so anything bigger than the demo goes in the card's 16 MB DRAM. That
requires bringing up the i960Rx memory controller first — its registers are known
(MCON block in the local register space) but the **refresh/timing values are
board-specific**. Get them from the stock firmware's early boot code (disassemble
the decoded image) or the on-card DRAM part's datasheet, do a one-time DRAM-init
`WRITE` sequence (or extend `start.s` to init DRAM before the loop), then
`SET_ADDR <dram> ; load tetris.bin ; go <dram>`.
<!-- ponytail: DRAM timing is the one real hardware unknown; left as a tunable
     step rather than fabricated values. Milestones 1 and 2a don't need it. -->

## Gates / honesty

- **Untested.** Written against the datasheet + this repo's verified facts; not yet
  compiled or run (needs the box powered on; the i960 side needs the cross-toolchain).
- **Flashing is still irreversible without a backup.** Same gate as `REFLASH.md`:
  the vendor flasher cannot dump, so take an external-programmer flash backup before
  writing `loader-fw.img`. After that, the *loader* is the last thing you ever flash.
- The loader assumes the stock PRCB (kept by `mkimage.py`) leaves the register cache
  usable at reset; `start.s` sets its own stack so a shallow call can't fault. If
  milestone 1 shows READY but `ping` times out, that assumption is where to look.
