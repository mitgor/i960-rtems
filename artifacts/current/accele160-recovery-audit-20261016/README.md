# AcceleRAID 160 boot recovery route, stock 6.00-05

2026-10-16. This is an **offline route audit**, not a recovery test. It uses the
accepted 1 MiB stock flash SHA-256
`0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a`.
The accompanying [receipt](audit.json) pins 18 instruction anchors. A one-byte
mutation of the `S` anchor makes the audit fail. No command, card memory write,
flash write, driver bind, or reboot occurred. A read-only SSH check found both
`37:04.1` (old PG) and `37:09.1` (new AcceleRAID) unbound.

## What the boot code does

At `feffc700`, reset tests a 16550-like UART by writing `1` to scratch register
`e0600007`, zero to `e0600006`, and reading scratch back. Only readback `1`
sets its RAM-present flag at `0x34`. It configures divisor low `6`, high `0`,
line control `7`, and FIFO control `5`; the input clock and physical UART pinout
are unknown, so the baud rate is **not established**.

If the UART was detected, reset checks receive-ready once at `feffc0cc` and
reads one byte. ASCII `S` (`0x53`) selects recovery mode 1; ASCII `!` (`0x21`)
selects manufacturing mode 2. A subsequent read of `e0500000` bit 1 also
forces mode 1. This is a flash-control/status register used by the programming
routine, **not an established safe host recovery switch**. Do not set it over
PCI as a shortcut. A missed serial byte falls through to normal boot.

Mode 1 reaches `feffca58`, initializes the boot recovery environment, copies
`0x5000` bytes from boot ROM `feff0000` to RAM `c0010000`, then hands off to
`c0010170`. The copied code starts the recovery command path and copies the
current full flash into staging RAM `c0300000`. Invalid main-image descriptors
or checksums also lead toward recovery. A valid-checksum image that hangs after
handoff need not enter it. Mode 2 branches elsewhere to a selector-5
manufacturing-image path; it is not the intended restore route.

The recovery dispatcher includes a flash-image command. Its `feff1080` path
calls `feff1880`, which asserts `e0500000` control value `8` and loops over
sixteen 64 KiB blocks to erase/program the complete 1 MiB from staging RAM.
That is a destructive path and was **not invoked**. This static trace does not
prove the boot mailbox can be addressed by the Linux host in recovery, that
stock restoration succeeds, or that this board exposes a functioning UART.
The separate [live debug-interface trace](../accele160-debug-interface-20261016/README.md)
showed disabled UART callbacks after a similar scratch-register test. It does
not reveal whether the cause is absent hardware, pin strapping, or timing.

## Next acceptance gate before firmware patching

1. Identify the board's UART header, signal ground, logic voltage and input
   pin from board documentation or electrical inspection. Do not guess a DB9
   RS-232 level or feed an adapter's supply voltage into the board.
2. With a correctly level-matched serial adapter, capture the power-on output
   and determine clock/baud empirically. Send `S` during the reset sampling
   window. Do not send `!`.
3. Prove recovery is responsive with a non-programming, bounded identification
   or read command, then power-cycle into stock firmware. Compare a fresh full
   read to the accepted 1 MiB SHA-256. Keep the old PG untouched.
4. Decode and rehearse the full restore command and staging bounds against
   this exact image before any patched flash experiment. A boot-time UART
   trigger alone is not a tested rollback path.

Until those gates pass, the late-loader PING candidate remains offline and
unflashed. There is no safe SSH-only recovery entry established by this audit.

Re-run:

```sh
python3 host/accele160/startup/audit_recovery_route.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin
```
