# AcceleRAID 160 card 10112504772: VPP gate-hold measurement

Written 2026-11-21 on branch `experiment/accele160-flash-status2`.
**Built and checked offline only; not run on hardware.**

## Why

Stock FLASHIMAGE fails on this card with writer status 22 (`80/16`) inside
one jiffy, for two different images, with all lock bits clear and a working
command path ([handoff](ACCELE160-CARD-10112504772-FLASH-HANDOFF.md)). The
remaining explanation for an instant refusal of every erase is that VPP at
the flash pin stays at or below the chip's lockout level while the stock
writer's gate is set. That is an inference; VPP has never been measured.
This payload makes the measurement possible without issuing any flash
command.

## What it does

[`stock_gate_hold.S`](../../host/accele160/flash/stock_gate_hold.S) runs once
from RAM under stock IOCTL `0x8f`, through the same launcher path as the
Intel ID/lock probe. It:

1. reads the board context pointer at `0xc04ad650` and its shadow word at
   `+0x50`, and returns without writing anything if the pointer is not a RAM
   address or bit 3 is already set;
2. sets bit 3 in the shadow and writes the low byte to `0xe0500000`, the
   same instructions as stock `c0055424..c0055450`;
3. holds for 16,000,000 polls, about 8 s by the operation-11 calibration
   (0.513 µs per poll);
4. reads `0xe0500000` once, then clears bit 3 the way stock does at
   `c005547c..c00554b4`, and reads the register again;
5. returns through the stock unsupported completion (host status 2).

It never addresses `0xfef00000..0xfeffffff`. With the gate set and no
command written, the chip stays in read-array mode. The stock writer holds
the same gate for about 35 s around its erase and program loops.

`stock_gate_hold.bin` is 252 bytes, linked at `0xc000f900`, SHA-256
`83d2a2bc04f23ca8489686f3f23fc23807f10dfd8b2d10c9bbb475acec73a7bb`.
`test_stock_gate_hold.py` checks that pin, that no word of the image is a
flash-aperture address, and that its only two byte stores go to the gate
register.

## Procedure

1. Power off. Attach a meter lead to the flash VPP net. Take the pin number
   from the Intel datasheet for the package and marking actually fitted on
   this card; a soldered wire or clip on a 0.5 mm pitch pin is safer than a
   hand-held probe on a powered card. Second lead to ground.
2. Cold boot. Take two independent full selector-9 stock reads, as for the
   ID probe.
3. Start the launcher; the hold begins within a second:

   ```bash
   sudo python3 host/accele160/flash/run_stock_gate_hold.py --module ping_probe.ko --payload host/accele160/flash/stock_gate_hold.bin --read0 READ0_DIR --read1 READ1_DIR --out OUT_DIR --cold-power-cycle-observed
   ```

4. Note the VPP reading before, during and after the roughly 8 s hold.
5. Take a third full stock read; it must still match
   `0ca0f4b6…e943`. Cold power cycle before any further `0x8f` call.

The launcher now also refuses a second `0x8f` call in one boot through a
marker in `/run`. `result.json` records the nine report words, the
host-observed command time and `register_reads_back_bit3`.

## Reading the result

| Observation | Meaning |
| --- | --- |
| VPP stays near 0 V during the hold | The gate path on this card does not deliver VPP. Trace the switch between the `0xe0500000` latch and the pin. |
| VPP rises to a level the S3 datasheet accepts for erase | The steady supply path works. Remaining suspects: the chip, a strobe during erase, or a VPP rise too slow for the stock writer, which erases within microseconds of setting the gate. A meter cannot see that; a scope can. |
| VPP rises but sags or sits between lockout and the valid range | Marginal supply. Do not issue FLASHIMAGE: a partial all-block erase can take the boot block. |
| `register_reads_back_bit3` false while `held` is true | The latch is write-only, so the native writer's gate readback check in `flash_backend.c` cannot be relied on. |

## Why the readback flag matters (added 2026-11-22)

Stock code never reads its own gate write back. It reads `0xe0500000` as
input pins: bit 1 in the boot block (`feffc0fc`) and in a 10 s polled wait
(`c0082d6c`, `c0082db4`), bit 0 in the loader (`fef43e8c`) and runtime
(`c0052f64`). Every stock write is the constant 8 or 0 (boot block
`feff18a0`/`feff18dc`, diagnostics `fefcb0b4`/`fefcb0e0`) or the RAM shadow.
So the address is probably an input port on read and a latch on write. The
native `flash_backend.c` and the emulator both assume a read returns the
latch. Against a split-port model the backend returns result 8 with no flash
command, and writes the input bits into the latch. `register_reads_back_bit3`
is the measurement that settles this.

## Limits

- The launcher pins this card's stock image and PCI address. The restored
  first spare now runs native firmware, so it cannot run this payload; a
  reference reading from a known-good card needs that card on its own stock
  image with its own pins, or an equivalent native diagnostic.
- The hold time is calibrated from operation 11 on another card running the
  same stock runtime, not on this card. The launcher allows 60 s.
- If the card faults during the hold, the gate stays set until reset. With
  no flash command issued this leaves the image unchanged; use a cold power
  cycle.
- Bit 3 as "VPP enable" is read from the stock disassembly. The measurement
  is what tests that reading.
