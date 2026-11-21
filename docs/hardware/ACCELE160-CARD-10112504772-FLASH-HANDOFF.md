# AcceleRAID 160 card 10112504772: FLASHIMAGE failure handoff

Updated 2026-11-21. This is the evidence and next-step handoff for investigating
the **stock firmware's in-system flash writer** on one physical card. The
current card is the sole AcceleRAID in HP Z400 Slot 5, PCI
`0000:37:09.1`, serial `10112504772`, PCI device `1069:0050`, subsystem
`1069:0054`, revision `02`. The PC is currently booted into Linux after a
successful cold power cycle. The card still has its exact stock firmware.

## Answer in brief

The host can read this card's Intel 28F008S3, stage a complete image in card
RAM, and read that staged image back exactly. The card's **stock** FLASHIMAGE
command has now failed twice with internal writer status 22 (`80/16` in sense
bytes 12–13), using two different, card-specific candidate images. Each
command returned within one host jiffy with status 2. On both occasions, a
subsequent cold boot succeeded and complete flash reads matched the stock
image byte for byte. Thus the issue is upstream of a persistent image or
RTEMS boot test on this card. The exact failing circuit or condition has
not been measured.

By contrast, the same host FLASHIMAGE command path (with an earlier version
of the host module before auto-sense was added) completed in roughly 35
seconds with status 0 on two other AcceleRAID cards. One restored first spare
also cold booted native RTEMS after its successful write. That makes a
card-specific flash write-path condition the leading hypothesis, while not
proving it. The current card's flash remains intact and it is suitable for
flashless RAM experiments.

## Exact identities and evidence

| Item | Value / source |
| --- | --- |
| Current card stock 1 MiB SHA-256 | `0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943` |
| Current card stock recovery file | [`stock-for-programmer.bin`](../../artifacts/current/accele160-october-handler-current-spare-20261121/stock-for-programmer.bin); use only for this serial |
| Native-writer diagnostic candidate SHA-256 | `50a4d7da197fa2beb2b9f7836f2c06237822ef03c0aee2b9034f2e2a0c79ca64` |
| October-style Firmware injection v1 candidate SHA-256 | `ce3e632c80df475d4fa372cad61255c73b5438aad76c2022308889c10c5c9af4` |
| Exact October accepted candidate SHA-256 | `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd` |
| Flash module SHA-256, auto-sense version | `1ba32738d7d055349db23d4bb17257364cd279f3ed048800f0b4c7c7b6d59bd3` |
| Current flash command | Stock `FLASHIMAGE`, IOCTL `0x2e`, selector 9, zero DMA payload after `STOREIMAGE` |
| Both failures | `done=1 status=2 residual=0 elapsed_ms=0`, `sense_len=14`, `sense=7000090000000007000000008016` |

`elapsed_ms=0` is whole-jiffy host accounting. It means the command completed
very quickly, not that execution time was literally zero or precisely under
one millisecond.

The [first diagnostic attempt](../../artifacts/current/accele160-diagnostic-flash-20261121/README.md)
used the native-writer candidate. It passed paired stock reads, a same-boot
sense-path probe, STOREIMAGE, and independent full staged READIMAGE. The
FLASHIMAGE failure was followed by a successful beep/Linux cold boot and two
full stock-image reads. The persistent one-attempt marker prevented a retry.

The [second attempt](../../artifacts/current/accele160-october-handler-current-spare-20261121/README.md)
used **Firmware injection v1**, not the native firmware. The candidate is
the physically accepted October image rebased onto this card: the only
differences from that October candidate are four serial-number bytes. The
4324-byte handler is identical. Compared with this card's stock image, the
image changes only the known loader hook, handler, and two required checksums;
the runtime, reset/boot block, and descriptor serial are preserved. Its
[`audit.json`](../../artifacts/current/accele160-october-handler-current-spare-20261121/audit.json)
is a **build-time** audit: its `flash_command_issued: false` field describes
the candidate creation step, not the later live flash attempt. The actual
attempt is recorded in
[`live-8118/attempt.json`](../../artifacts/current/accele160-october-handler-current-spare-20261121/live-8118/attempt.json)
and [`live-8118/flash/status.txt`](../../artifacts/current/accele160-october-handler-current-spare-20261121/live-8118/flash/status.txt).

On boot `81182258-15c8-4513-963c-d6cc688802f3`, both preflash full reads
matched stock. The unsupported-IOCTL auto-sense probe returned internal
`0x104`, validating the sense transfer path. STOREIMAGE completed and an
independent full staged READIMAGE matched the Firmware injection v1 candidate
byte for byte. One FLASHIMAGE was issued; it returned the same `80/16`
writer failure. Two full reads immediately afterward were byte-identical to
stock. After physical power off/on, the HP Z400 beeped and booted Linux.
On boot `c2b26a79-7b7b-4451-bfd1-454ae9a86316`, the read-only driver
first bind passed. Two independent full reads had zero status, residual and
guard changes, and were again byte-identical to the original stock image.
The cold-boot receipts are under
[`post-cold-c2b2/`](../../artifacts/current/accele160-october-handler-current-spare-20261121/post-cold-c2b2/).
Full 1 MiB captures are retained locally and on the remote under
`/home/mit/i960-october-handler-test-20261121/`, with only small receipts
tracked in Git to keep the repository size under control.

## What has and has not been ruled out

- **Host command transport and RAM staging work on this card.** Independent
  full staged READIMAGE returned the intended candidate both times. The
  sense probe and card descriptor also respond normally.
- **The native candidate's image layout is not sufficient to explain the
  refusal.** The accepted October-style handler candidate produced the same
  writer code. There could still be an unrecognized common precondition in
  both images, though stock writer disassembly has not shown an image-content
  check in its FLASHIMAGE handler.
- **A partial persistent image is ruled out for these two attempts.** After
  each cold boot, full readback matched the exact stock image. This does not
  prove that no erase command was ever issued; the status path may have
  rejected an operation before a destructive pulse.
- **Intel lock bits are not the obvious cause.** A volatile Intel ID/lock
  probe reported manufacturer `0x89`, device `0xa6`, master lock clear, and
  all sixteen 64 KiB block locks clear on this card before the diagnostic
  attempt. See the [lock evidence](../../artifacts/current/accele160-stock-flash-locks-20261121/README.md).
- **VPP, write-enable, control strobes and flash-pin waveforms are unknown.**
  They have not been measured on this card. The read-only PCI path cannot
  establish them. The stock writer's gate at `0xe0500000` has a software
  shadow; the register's readback semantics are not known.
- **Revision field alone is not an explanation.** This card reports board
  revision `A` and count `1`; the earlier first spare that completed a flash
  also had `A` and `1`. The later successful card had `B` and `5`.
- **The RAM route works independently of flash.** On this same stock card,
  [Ram injection v1](../../artifacts/current/accele160-volatile-stock-20261121/README.md)
  installed the October handler temporarily, then ran bounded RTEMS and
  40 Doom frames from RAM. This is a usable development route while the
  writer is investigated.

The [firmware status investigation](ACCELE160-FLASH-STATUS-2-INVESTIGATION.md)
pins the relevant stock disassembly. Host status 2 alone is generic; sense
`80/16` identifies internal writer failure 22. If execution reached the
writer, it attempts to erase all sixteen blocks and only programs after
all erases succeed. Each block erase issues `FF 50 20 D0`, polls status bit 7,
then checks VPP-low/status bit 3, status bit 4, and blankness. The trace is
static analysis, not a flash-bus observation, so it does not pinpoint the
hardware failure. The stock erase path includes the boot block: another
attempt can brick the card even though the last two left it intact.

## Next steps for the card-specific investigation

1. **Keep card 10112504772 identified and retain its stock backup.** Do not
   use another card's image. The current Linux session is read-only after
   the cold-boot verification; there is no reason to issue a third FLASHIMAGE
   merely to reproduce `80/16`.
2. **Compare this card physically with the known flashing first spare while
   power is off.** Record high-resolution photographs of both sides, flash
   marking, JP3 position, regulator/charge-pump parts, solder damage and
   rework. The board guide labels JP3 “Maintenance Mode”; it does not prove
   that JP3 is a flash write-protect jumper. Do not change it by guesswork.
3. **Trace the flash write supply and control path from the board schematic
   or continuity measurements.** Establish which pin or gate enables VPP
   and which board latch drives it. Compare the failing and successful cards
   first with power off. A 3.3 V logic level at the host does not prove the
   required voltage is present at the flash pin during erase.
4. **If another write experiment becomes necessary, instrument it.** Measure
   VPP and relevant chip-enable/write-enable/status pins at the 28F008S3
   during one bounded, reviewed attempt, with the external programmer and
   this exact stock recovery image ready. Avoid a blind third full-image
   attempt; the two existing results already establish repeatability.
5. **Use the proven flashless route in parallel.** Ram injection v1 can load
   RTEMS/Doom on this stock card without consuming another flash cycle.

For anyone revising the writer or host tool: the two failures come from the
**stock card firmware's writer**, before any custom RTEMS flash tool runs.
Changing the native updater code alone cannot repair this test path. A useful
fix must explain why the stock FLASHIMAGE command returns `80/16` on this
serial and succeeds on otherwise similar cards.

## Should we test another spare?

**Yes for forward progress, but first identify which spare it is.** The
restored first spare has already completed a stock FLASHIMAGE in 34.9 seconds,
cold booted, released PCI configuration retry, and run native RTEMS; its
[receipt](../../artifacts/current/accele160-restored-first-spare-updater-20261120/README.md)
is the strongest control for continuing native-firmware work. Keep the
current failing card intact for electrical comparison. If the other card is
a different, untested stock spare, first capture its own two full stock reads,
serial, flash ID and lock state, and preserve its exact recovery image. A
card-specific minimal Firmware injection v1 image is a better first
persistent test than an unproven native image, but it still carries the
all-block erase risk and should only be tried with recovery ready. Do not
apply this card's `candidate.bin` to any other serial.

The old first-spare **pre-beep** failure was a distinct problem: a native
image was written successfully and verified by an external programmer, but
the HP Z400 then hung before the beep. The restored first spare's later native
image corrected the modeled PCI configuration-retry release and cold booted
successfully. Do not conflate that boot-path failure with this card's
FLASHIMAGE `80/16` writer refusal.
