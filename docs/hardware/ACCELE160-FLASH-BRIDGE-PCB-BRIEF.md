# AcceleRAID 160 flash bridge: PCB design brief

**Status:** design input, 2026-11-11. No schematic, PCB, or replacement-memory boot has been validated. This document is intended to be copied into a separate hardware-design project together with the cited evidence. Treat all unmeasured electrical details as questions to resolve before fabrication.

## 1. Objective and success criterion

Design a removable bridge between the Mylex AcceleRAID 160 controller's Intel E28F008S3-120 flash footprint and a BeagleBone AI (or another 3.3 V wireless SBC). The bridge must let us select and test full 1,048,576-byte firmware images without repeatedly soldering the card's flash or committing each experiment to the card's only nonvolatile memory. It must preserve a reliable way to boot the **same card's original stock image**.

The critical success test is a cold boot of the HP Z400 with a known-good stock image through the bridge, followed by a complete image readback and normal Linux enumeration. Only after that baseline passes should an experimental image be selected. A POST beep alone does not establish i960/RTEMS startup.

The intended split is: the SBC stores images, selects modes, loads memory, verifies hashes, logs measurements, and offers Wi-Fi/Bluetooth control. **Local hardware on the bridge** supplies the parallel flash bus at reset-time speed. Linux GPIO or PRU code must not be on the read-critical path.

## 2. Verified project context

| Item | Evidence / value |
| --- | --- |
| Card | Mylex AcceleRAID 160, PCI `1069:0050`, subsystem `1069:0054`, revision `02`; Intel 80303/i960-family controller, 16 MiB reported DRAM. This is distinct from the older DAC960PG/i960RP card in the repository. |
| Flash | Marking read from the photographed failed spare: **Intel E28F008S3-120**, 8 Mbit = 1 MiB, ×8 parallel flash, nominal 3.3 V, 40-lead TSOP, 120 ns read access. Confirm exact package orientation and pinout against the *S3* datasheet and the actual card before layout. |
| First spare stock image | `artifacts/current/accele160-spare-rom-20261025/restore-first-spare-stock-1MiB.bin`; SHA-256 `fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816`. It contains that spare's unique descriptor at offsets `0xe0000..0xeffff`. |
| Failed image | `artifacts/current/accele160-spare-rom-20261025/native-rom-spare-prototype.bin`; SHA-256 `6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd`. |
| Programmer read | `/Users/mit/Downloads/E28F008S3.BIN`, archived as `artifacts/current/accele160-spare-rom-20261025/programmer-read-0.bin`, is exactly 1 MiB and byte-identical to the failed image. The original FLASHIMAGE command wrote the requested bytes; a partial write is not the explanation for the failure. |
| Second spare | Its own stock image has SHA-256 `0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`; 18 bytes differ from the first spare inside the unique descriptor. Never cross-program these board-specific stock images without explicit analysis. |
| Physical failure | The programmed first spare hangs the HP Z400 **before the usual POST beep**. Removing it restores the boot. Disabling HP Slot 6 option-ROM download, both Mylex BIOS boot procedures, and SATA RAID option ROM did not make the failed spare boot. The cause remains unknown. |
| Existing software model | The exact failed image reaches an RTEMS PASS marker in the exploratory i960 interpreter, but the physical 80303/PCI/BIOS behavior is incompletely modeled. This does not qualify a new flash candidate. |

The relevant repository records are [first spare evidence](../../artifacts/current/accele160-spare-rom-20261025/README.md), [second spare and slot-ROM experiment](../../artifacts/current/accele160-second-spare-20261026/README.md), [startup analysis](accele160-startup.md), and [emulation limits](../../rtems/accele160/native_rom/EMULATION.md).

## 3. Architecture to design

```text
                 ┌────────────────────────── AcceleRAID 160 ──────────────────────────┐
                 │  existing E28F008S3 TSOP-40 pads: A[19:0], DQ[7:0], CE#, OE#,     │
                 │  WE#, RP#, RY/BY#, VCC, GND, VPP, any NCs                         │
                 └───────────────────────────────┬───────────────────────────────────┘
                                                 │ short, controlled interposer
                              ┌──────────────────┴─────────────────────┐
                              │ FLASH BRIDGE PCB                       │
                              │                                         │
                              │  stock-flash path ◀── mode selector ──▶│ SRAM path
                              │  own flash, unchanged image             │ 1 MiB × 8
                              │                                         │      ▲
                              │ card-domain isolation and power sense   │      │
                              │ flash-command monitor / small FPGA      │ image loader
                              │ test points, configuration, debug UART  │      │
                              └─────────────────────────────────────────┴──────┼─────┘
                                                                                │ SPI or other
                                                                                │ low-pin-count link
                                                                        BeagleBone AI
                                                                        storage + wireless
```

The diagram is a functional target, **not** a validated circuit. The design may use CPLD/FPGA, fast bus switches, latches, and a 1 MiB × 8 asynchronous SRAM. The FPGA/CPLD should handle mode arbitration, output gating, command observation, and deterministic status signals; the SRAM should answer ordinary reads directly. A candidate part is ISSI `IS61WV10248EDBLL` (1 MiB × 8, 2.4–3.6 V, 8/10 ns options), subject to footprint, availability, current, and timing analysis. It is **not pin-compatible** with the Intel TSOP-40; the interposer must remap pins.

### Required modes

1. **STOCK / pass-through:** The original flash, moved to the bridge or an equivalent exact replacement containing the spare's own stock image, is electrically presented as it was on the card. All necessary signals, including `WE#`, `RP#`, `RY/BY#`, and `VPP`, must retain their measured behavior. This path is the baseline and recovery fallback. Prefer a physical jumper or switch whose setting is unambiguous and persists through power loss.
2. **SRAM / read experiment:** A full image is preloaded and verified while the card is off and isolated. At PC power-on, the bridge presents read-only contents with timing compatible with E28F008S3-120. The card's `WE#` must **not** reach SRAM `WE#` during this mode. All writes/command attempts must be captured or handled by local logic; ignoring them is acceptable only after proving that the startup path needs array reads only.
3. **LOAD / maintenance:** Only the SBC/loader owns the SRAM bus. The card side is isolated or unpowered. Switching into or out of this state must be impossible while the card is actively reading, unless a verified reset/hold sequence is provided. Do not let the SBC drive an unpowered card through address or data pins.

If the stock flash is absent, the board must fail into a defined, observable state; it cannot claim a safe fallback. A true fallback requires a physical stock flash path that remains functional without firmware running on the BeagleBone or FPGA.

### Why simple parallel wires are insufficient

The flash is 1,048,576 × 8, so it needs 20 address and 8 data signals plus control/status. Shared BeagleBone/card connections create bus contention during loading, can back-power whichever side is off, and add capacitance/stubs to a 120 ns interface. The BeagleBone AI's P8/P9 signals are 3.3 V and **must not be driven when its power is absent**. Route only a modest-speed management interface to the SBC; keep the full parallel bus local to the bridge. See [BeagleBone AI expansion rules](https://docs.beagleboard.org/boards/beaglebone/ai/04-expansion.html) and [PRU pin access](https://docs.beagleboard.org/boards/beaglebone/ai/03-design-and-specifications.html).

## 4. Electrical and logic requirements

### Flash footprint and pin contract

- Derive an **exact 40-row pin table** from the Intel **E28F008S3-120** datasheet, the chip's pin-1 mark, PCB silkscreen, and continuity measurements. Record pad number, signal, direction, measured voltage in stock power states, and bridge net. Do **not** copy a pin table from E28F008SA, SC, S5, or a reverse-pinout package by assumption.
- Include `A0..A19`, `DQ0..DQ7`, `CE#`, `OE#`, `WE#`, `RP#`, `RY/BY#`, `VCC`, ground, `VPP`, and all no-connect pins. Check whether the card actually drives/samples every signal at startup. `VPP` is particularly important: do not connect a potential programming voltage to 3.3 V logic or SRAM.
- Preserve the card's original loading, rise/fall behavior, and read timing. A fast SRAM data sheet number alone is insufficient; budget address/CE/OE arrival, selectors, translators, interposer, load, and setup time at the card. Measure with an oscilloscope/logic analyzer on stock hardware.
- Capture flash-command behavior. Intel flash is a state machine, not just an array: writes may request identifier, status, reset/read-array, block lock, or program/erase behavior. The read-only SRAM path must either emulate the needed commands or be explicitly qualified only for a traced read-only boot path. `RY/BY#` behavior must be defined; a hard pull-up is a hypothesis, not a known substitute.
- Provide address/data/control test points and a high-impedance analyzer connection. A small logic-analyzer header with ground returns is preferable to long flying leads on the active bus.

### Arbitration and power

- No mode may allow two active output drivers on `DQ[7:0]`. Hardware interlock must disconnect SBC loading when card read mode is selected; firmware promises alone are insufficient.
- The BeagleBone must never source card VCC, and card VCC must never source the BeagleBone rail unintentionally. Common ground is required for signals, but the two power domains need explicit isolation and a measured sequencing plan.
- The bridge must be able to hold a fully loaded SRAM image **before the PC is turned on**. Options: independently powered bridge/SRAM with card-facing powered-off-isolated buffers, or another documented sequence that guarantees image readiness before the card's first fetch. Simply powering SRAM from the PCI card cannot meet this preload requirement unless card reset can be held safely during loading.
- Card-facing parts must have specified powered-off high-impedance/Ioff behavior. Choose and verify the actual bus-switch/translator parts for this behavior. Avoid applying signals to unpowered BeagleBone pins.
- Supply supervisor / power-good should prevent output drive until card VCC is in range. Define behavior for BeagleBone reset, cable disconnect, SBC crash, brownout, and PC power cycle. An image switch or mode change must require card power-off or a separately proven safe hold/reset.
- Use a board-local nonvolatile configuration record or physical switch for selected image/mode. If SRAM is used, its *contents* are volatile; the bridge must prove current image hash before advertising READY. Never silently treat an old SRAM state as valid.
- Add accessible current measurement points, rail filtering/decoupling, ESD protection on external management connectors, and clearly labeled grounds. Size the supply for flash/SRAM, logic, and pre-power operation after measuring actual current.

### BeagleBone connection

Use BeagleBone AI as a **management computer**, not as a per-read data source. A low-pin-count SPI (or USB/UART plus local MCU) interface is enough to transfer 1 MiB before PC power-on. Include commands for load, full readback, hash comparison, mode request, status/power telemetry, and captured bus events. If the loader is an FPGA, specify its own configuration source and boot time; it must reach a valid state before the card does. A first design could instead use a small MCU for loading and a CPLD for bus logic.

Wi-Fi/Bluetooth are conveniences for image selection and logs. The bridge's safe stock mode must not depend on network availability, Linux startup, or GPIO initial states. Leave physical access to the mode switch and diagnostic connector when the card is installed.

## 5. Mechanics and fabrication

- Survey the AcceleRAID 160 in its PCI slot: flash pad orientation, nearby components, available height, adjacent card clearance, bracket clearance, airflow, and case closure. The TSOP-40 is fine pitch; specify rework method, pad geometry, strain relief, and inspection criteria. Prefer a short rigid/flex or rigid interposer over a long bundle of parallel wires.
- Do not mount a heavy BeagleBone or large cable directly from TSOP pads. The bridge may be mechanically supported from a separate bracket or standoff; allow card removal without stressing the flash footprint.
- Preserve the removed original flash intact, labelled with its card identity and an independent external-programmer dump. A socket on the bridge can simplify replacement, but characterize its contact and added bus parasitics.
- Expose mode, power, READY, and error indicators. Mark pin 1 and both sides of every connector. Design to avoid confusing first-spare and second-spare stock images.

## 6. Firmware, protocol, and image handling

The bridge controller should implement a small auditable state machine:

```text
OFF / NO_CARD_POWER
  -> LOAD (card isolated)
  -> VERIFY (full byte comparison + SHA-256 recorded by host)
  -> ARMED (image immutable, loader disconnected)
  -> CARD_POWERED / SERVE_READS
  -> CARD_POWER_LOST -> ARMED or invalidated per measured rail design
```

On any unexpected reset, invalid image, or conflicting mode request, report a fault and make the outputs electrically defined. Do not automatically switch images during an active boot. Log the selected image hash, mode, rail states, time to READY, command writes, status reads, and reset/CE/OE activity in a bounded buffer. A trace buffer must not introduce latency in the read path; overflow should be signalled.

For stock pass-through, the easiest first milestone is **transparent operation**: avoid interpreting flash commands and verify that the original flash still boots. In SRAM mode, start with read-only array emulation only after capture proves that mode can satisfy the actual startup sequence. If the host or i960 issues Intel commands, implement the necessary command/read responses in deterministic local logic, with explicit tests for read-array return and reset.

An external programmer read of the first spare's failed flash already matches its candidate. The board should support a complete readback of every loaded SRAM image before arming, and ideally expose the stock flash to an external programmer **with the card physically isolated and unpowered**. Do not imply that a BeagleBone connected to the same nets can program an installed flash without arbitration and `VPP` analysis.

## 7. Acceptance plan

1. **Bench characterization, no new PCB:** photograph and measure the flash footprint; identify pin 1, rail and `VPP` levels, reset/CE/OE/WE/RY-BY behavior, and first-fetch timing using the known-good stock card. Make a 40-pin signed-off net/power table. Preserve complete stock dumps with SHA-256.
2. **Schematic review:** verify every pad against the S3 datasheet and continuity; calculate worst-case read timing and power sequence; review bus contention, powered-off isolation, flash-command behavior, and mechanical stresses. Produce a test matrix before ordering.
3. **Unconnected PCB bring-up:** inspect assembly, check shorts/opens, power rails/current, firmware configuration, bus arbitration, isolation while each side is off, and full 1 MiB SRAM write/readback with walking address/data patterns and hash checks.
4. **Standalone flash-bus fixture:** drive addresses and controls at/above expected card rate; compare every byte against the source image in STOCK and SRAM modes; exercise CE/OE/WE/RP transitions, status/ID commands if observed, brownouts, and repeated cold starts. Check setup/hold and bus fight on a scope.
5. **First card insertion:** use a **recoverable spare**, stock image only, physical STOCK mode first. Confirm normal HP POST beep, Linux boot, PCI identity, and same-card full flash read. Then repeat with the *same stock bytes* served from SRAM. This A/B test is the main gate for whether the emulator is electrically faithful.
6. **Experimental image:** only after repeated stock-SRAM cold boots pass, load the known failed image into SRAM and capture card-side flash bus traces from power-on through the pre-beep hang. Compare stock versus candidate for first divergent command/reads/timing. The goal is diagnosis, not merely a second failing boot.
7. **Recovery proof:** power down, select physical STOCK mode, and cold-boot again. Confirm Linux and full image integrity. The test is incomplete until recovery is demonstrated.

Record exact card serial/identity, HP BIOS settings, slot, image SHA, bridge hardware revision, BeagleBone/logic firmware revision, voltage traces, analyzer traces, and observed POST outcome for every physical run. Do not test on the original working card while the spare provides sufficient evidence.

## 8. Required PCB project deliverables

1. S3-specific pin/voltage/continuity table with photos and pin-1 orientation.
2. Block diagram, schematic, BOM with manufacturer part numbers, availability and substitutes, PCB layout, fabrication/assembly files, and mechanical clearance drawing.
3. Timing budget for STOCK and SRAM paths; signal-integrity and power-sequencing analysis, including off-state leakage/backfeed and FPGA configuration time.
4. Mode state machine and truth table for every control line in OFF, LOAD, VERIFY, STOCK, SRAM, FAULT, and power-transition states.
5. Loader/management protocol and independently testable logic firmware with bounded trace format.
6. Bench fixture and automated tests for full 1 MiB image transfer, exhaustive byte readback, command sequence handling, switching interlock, and power faults.
7. A step-by-step first-power and first-card bring-up procedure, with explicit stop conditions and a stock fallback path.

## 9. Open questions to resolve before PCB layout

- What are the **actual** S3-120 pin assignments on this card, including `VPP` and `RY/BY#`, and what voltages occur at power-up and during stock firmware operation?
- Does either the i960 reset code or x86/host side issue flash commands before POST completes? Which command responses and busy timing must be emulated?
- Is any flash write signal asserted during ordinary boot? How does the card react if writes are ignored by SRAM?
- What is the earliest card read relative to PC power-good, and can a separately powered bridge be safely armed before then?
- What read setup/hold and bus load does the controller impose? How much interposer and switch delay is tolerable?
- Can the original chip be removed/reinstalled safely with the available tools, and is there room for a small interposer plus cable in the HP Z400?
- Is an external stock flash on the bridge preferable to permanently soldering the original chip back, and how will stock-chip uniqueness be labelled?
- What exact BeagleBone model will be used? BeagleBone AI and AI-64 have materially different wireless hardware and header details; do not treat their names as interchangeable.

## 10. Primary component references

- [Intel E28F008S3-120 datasheet index](https://www.alldatasheet.com/datasheet-pdf/pdf/66033/INTEL/E28F008S3-120.html): exact family, density, 120 ns and package. Obtain and review the complete **S3** PDF for the final pin map and AC/DC limits.
- [ISSI IS61/64WV10248EDBLL datasheet](https://www.issi.com/WW/pdf/61-64WV10248EDBLL.pdf): candidate 1 MiB × 8 SRAM, supply, timing and pinout.
- [BeagleBone AI expansion](https://docs.beagleboard.org/boards/beaglebone/ai/04-expansion.html) and [design/PRU pin access](https://docs.beagleboard.org/boards/beaglebone/ai/03-design-and-specifications.html): header voltage, power-off restriction and available signals.

The project's saved binaries and physical-test records are the authority for *which image belongs to which card*. Datasheets are the authority for component pins and absolute maximum ratings. Every electrical assumption above must be checked on the specific card before routing a PCB.
