# AcceleRAID 160 stock PCI BIOS capture — 2026-10-16

Two complete, identical 28,672-byte PCI option-ROM reads were obtained over SSH,
without unbinding `myrs`, sending mailbox commands, resetting either card, or
programming flash. This is **not a complete controller flash backup** and is not
sufficient for firmware recovery/programming.

- New card: `0000:37:09.1`, `1069:0050`, subsystem `1069:0054`, `myrs`.
- Old DAC960PG: `0000:37:04.1`, `1069:0010`, remained unbound and untouched.
- Boot: `164a6af9-4bc8-43f2-9eb0-805a0ce43f68`.
- Both binary SHA256: `96d5d8996099ad587533f50caebe18c0211eb4a555f17027a75763f4e633b47a`.
- Header `55aa`; header size 56 × 512 = 28,672 bytes; whole-image byte sum modulo
  256 = 0. PCIR at offset 40, vendor/device `1069:0050`, image length 56 sectors,
  code type 0 (x86), last-image flag set.
- PCI config before/after is identical. Expansion ROM resource is 32 KiB, but
  the image declares 28 KiB. Buffered reads are required: one unbuffered read
  initially returned only 4096 bytes; that incomplete duplicate is not retained.
- BIOS contains version text `6.01-08`; running controller firmware reports
  `6.00-05`. These are separate components, not a version mismatch diagnosis.

Files: paired exact ROM binaries, PCI config before/after, resource allocation,
and JSON identity/hash receipt. No obsolete build trees are retained.

## Reproduction

Copy `host/accele160/read_option_rom.py` and `rtems/transport/card_select.py`
together, preserving repository-relative paths. On the Linux host:

```sh
sudo python3 host/accele160/read_option_rom.py --bdf 0000:37:09.1 --out /path/to/new-capture
```

The tool requires the exact AcceleRAID identity and `myrs` binding. It temporarily
writes 1 then 0 to that card's sysfs `rom` access gate; this enables reading, not
flash programming. Review `result.json` for both successful reads; compare both
files, their declared length/checksum, and config-before/config-after. A missing
or short image is not success. Do not use the PG runtime/module on this card.

## Firmware-interface findings and next step

Linux 6.8 [`myrs.h`](https://github.com/torvalds/linux/blob/v6.8/drivers/scsi/myrs.h)
and [`myrs.c`](https://github.com/torvalds/linux/blob/v6.8/drivers/scsi/myrs.c)
use the newer SCSI-based firmware interface. Its command opcode 0x20 is IOCTL;
it must not be interpreted as the old PG LoadImage opcode. The current driver
has no generic userspace firmware-image read API. No retained controller SCSI
generic device was found on this host.

FreeBSD's [`mlyreg.h`](https://github.com/freebsd/freebsd-src/blob/releng/12.4/sys/dev/mly/mlyreg.h)
names STOREIMAGE 0x2c, READIMAGE 0x2d, FLASHIMAGES 0x2e. This establishes a
promising command name, **not its image selector, offsets, length semantics,
or whether it reads persistent flash rather than an image staging area**.
The inspected driver does not supply a usable READIMAGE implementation.
No guessed command was submitted. Full stock flash remains undumped.

Next: establish READIMAGE parameters from a compatible vendor utility or
protocol documentation, then design a bounded read with owned DMA storage,
completion/timeout retention and repeated byte-for-byte validation. Preserve
`myrs` ownership until that interface is understood. CPU clock remains
user-reported 100 MHz; Linux's processor attribute says absent and does not
verify it. Kernel reports 16 MB memory; cache sysfs reports 8 MB.

## Explicit selection changes and validation

Primary RTEMS transport, relay, resident runtime and Doom play launcher now
require `--bdf`. `Board` verifies all four PCI identity fields against the PG
profile before any hardware operation, rechecks under its lock, rejects a bound
card and rejects a module-option BDF override. Requests record the identity.
Cleanup requires the selected BDF to match the saved request and loaded module.
Newly built base/derived PG modules no longer default to a BDF; their PCI match
remains PG-only. No AcceleRAID compatibility was added to them.

Six fake-sysfs selector tests passed (exact match, wrong card, missing/short BDF,
wrong subsystem, binding, missing device); all changed Python files compiled.
Live SSH PG-profile selection of the new card was rejected before hardware use.
No runtime was launched on either card. Kernel module builds were not exercised.
Historical experiment callers of `Board` without `bdf=` now fail closed and need
migration before reuse. Historical prebuilt modules/scripts are not made safe
by changing source: do not run them based on their former BDF assumptions.
For an explicitly requested future old-card run, primary launchers require
`--bdf 0000:37:04.1`; this investigation did not run that card.
