# Serial preparation for DAC960PG recovery

This is preparation for identifying and observing the serial interface, not a
verified pin-to-pin wiring diagram. Physical access is available; the serial
adapter will come later. Continue software work over SSH meanwhile.

## Identify the connection before buying or connecting an adapter

1. Shut down the PC, disconnect mains power and photograph both sides of the card.
   Capture the full board, PCB revision, unpopulated headers and jumper labels,
   plus readable markings on nearby small ICs and oscillators. Keep existing
   jumpers in their original positions and photograph them first.
2. Identify the UART and any line-driver chip from markings and traces. We must
   determine whether the accessible signals are logic-level UART or RS-232,
   and determine the required voltage. The firmware's register map alone cannot
   distinguish their electrical interfaces.
3. With the board unpowered, use continuity measurements to identify ground and
   trace candidate pins to the UART/driver. Do not guess from header shape or
   another DAC960 model's pinout. Document the resulting pin numbering and view.
4. Select an adapter for the confirmed interface: a correctly rated USB UART for
   logic levels, or USB RS-232 for RS-232. These are not interchangeable. Do not
   connect the adapter's VCC/power pin to this powered PCI card.

Mylex's [DAC960PG installation guide, connector table](https://manualzilla.com/doc/7409909/mylex-dac960pg-installation-guide)
identifies J5 as battery backup with a required loopback plug when the battery is
absent, JP10 as manufacturing diagnostics, and JP12 as the processor-voltage
selection. **J5's loopback is not evidence of a serial loopback connection.** Leave
JP12, the battery loopback and JP10 unchanged during identification. Exact board
revision still needs checking against the guide.

## First connection: receive only

After identifying the interface and pinout, make connections with power off:
card ground to adapter ground, card TX to adapter RX. Leave adapter TX, VCC,
RTS and DTR disconnected. Power the PC normally and record the complete boot
output with terminal local echo and hardware/software flow control disabled.
This lets us observe the port without injecting a recovery trigger.

Boot code writes divisor low=6, high=0 and line-control=07 to a 16550-like UART
at E0600000. **If it follows that UART convention**, this implies 8 data bits,
no parity and 2 stop bits (8N2), with baud = UART input clock / 96. For a
1.8432 MHz UART clock that would be 19200 baud; the actual clock is not yet known.
These interpretations follow the [TI PC16550D register description](https://www.mouser.com/datasheet/2/405/pc16550d-443503.pdf).
Identify the clock or measure TX bit duration before treating 19200 as established.
A scope/logic analyzer must also be rated for the confirmed signal levels.

If output is garbled, resolve signal levels, polarity, bit duration and framing
before connecting adapter TX. Save raw logs with the board revision and settings.

## Later recovery-entry experiment

Only after clean receive-only output and a verified TX/RX connection should we
prepare a controlled entry test. Boot code transmits `S`; receiving `S` in its
startup window selects the fallback monitor. Receiving `!` selects manufacturing
mode, which is a different path. We have not verified the timing or physical
trigger. Do not short arbitrary pins or continuously send characters yet.

The expected result of fallback is PCI ID 1069:0011, followed by bounded,
read-only descriptor/image checks from Linux. The monitor lacks Enquiry2, so the
existing normal-mode dump harness is not suitable unchanged. No erase/program
command is needed merely to prove recovery entry. Restore the normal physical
configuration before a later normal boot; cold-boot return remains to be tested.

See BOOT-RECOVERY.md for the exact code paths and their limits. In particular,
a custom loader that hangs after passing boot validation need not automatically
enter recovery.
