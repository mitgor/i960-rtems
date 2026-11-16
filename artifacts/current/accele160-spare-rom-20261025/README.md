# AcceleRAID 160 native-ROM spare test, 2026-10-25

The installed spare at `0000:37:04.1` has PCI identity `1069:0050`, subsystem
`1069:0054`, revision 02. The original working card at `0000:37:09.1` was
unbound throughout this test. The host boot ID was
`c4317f3b-4759-4039-ac51-a39cc0b368be`.

Two guarded full-flash reads of the spare (`rawflash-0`, `rawflash-1`) matched
byte-for-byte, SHA-256
`fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816`.
Both had status/residual/guard changes zero. Compared with the original
card's saved stock image, the BIOS, main firmware, diagnostics, and reset block
are identical. Twenty bytes differ inside the card-specific descriptor at
`0xe0000..0xeffff`; this descriptor is preserved in the spare candidate.

`native-rom-spare-prototype.bin` is the 1 MiB native-ROM experiment based on
the **spare's own** stock capture, SHA-256
`6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd`.
The offline packer kept all bytes outside selector-2 main firmware unchanged,
including the spare's descriptor and stock reset block. Nine offline tests
passed. The candidate still relies on the stock reset block for DRAM/PCI
initialization; it replaces the stock runtime with a stage-two loader and
small RTEMS scheduling diagnostic.

`preflight.json` records the exact same-boot stock captures. `stage/` records
STOREIMAGE selector 9 into controller RAM: status/residual/guard changes zero.
The independent full `staged-readback-0/` returned the exact candidate SHA,
again with zero status/residual/guard changes. The modules released and
unloaded normally.

`flash/` records one FLASHIMAGE selector-9 command to the spare. It completed
in 35.1 seconds with status and residual zero; the flash module released and
unloaded. The original card remained unbound. The PC was then shut down for a
cold-start test. On power-on, the user reported that it did **not reach the
normal beep or Linux boot** with the programmed spare installed. This is a
failed hardware acceptance test. The user was advised to power off and remove
only the programmed spare. The user then reported that the PC beeps and boots
Linux normally with that card removed and the original card left installed.
The candidate's arrival at the RTEMS entry is unknown, as is whether the stop
occurred earlier in PCI/BIOS startup. **Persistent contents and
RTEMS boot are not proven.** No autonomous recovery mechanism is proven for
this failed native boot. Do not repeat the flash with the remaining spare on
the strength of the current offline checks.

Subsequent offline [controller emulation](../accele160-emulator-isa-20261025/README.md)
ran the exact saved spare candidate under an exploratory initial board byte
of 11. It copied the RTEMS payload, completed 64 worker iterations, wrote
PASS, and parked with code zero. The spare's stock image reached its runtime
entry in the same model. This narrows the unexplained cold-boot failure but
does not show what the physical card did: reset-time peripheral responses,
the host PCI/BIOS interaction, and the card's post-flash contents remain
unverified. The remaining spare is still reserved.

A later [QEMU PCI option-ROM probe](../accele160-qemu-pci-probe-20261025/README.md)
presented the measured identity and BAR and executed the unchanged x86 ROM
from both stock and failed-spare images. SeaBIOS made no BAR0 access in that
bounded run, so the traces were identical and still did not reproduce the
physical pre-beep failure.

## External-programmer recovery image

The physical chip on the failed first spare has been identified from its
marking as Intel E28F008S3-120, a 1 MiB, 8-bit, 3.3 V parallel flash in
TSOP-40. `restore-first-spare-stock-1MiB.bin` is a byte-for-byte copy of
`rawflash-0/data.bin`. Both independent preflash stock reads and this
recovery copy are exactly 1,048,576 bytes and have SHA-256
`fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816`.
This is the **first spare's own** original image, including its unique
descriptor. Do not substitute the original card's or second spare's stock
image.

Before writing, read the failed chip twice with the external programmer and
save both complete files. Check exact size, matching hashes, chip identity,
orientation, and 3.3 V setup. Compare the two reads to the intended failed-
spare candidate (`6f16d713...`) and the stock recovery image to determine
what persisted. Then write the stock recovery image and verify the complete
programmed contents against this file with an independent read.

## First physical chip read, 2026-11-10

The user supplied `E28F008S3.BIN`, reported as an external-programmer read
from the failed first spare. It is archived here as `programmer-read-0.bin`;
the supplied file was not altered. It is exactly 1,048,576 bytes, SHA-256
`6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd`,
and `cmp` finds **zero differences** from both `native-rom-spare-prototype.bin`
and the preflash staged readback. Thus the flash contents persisted exactly
as requested, assuming the programmer read really came from this chip.
The pre-beep failure is not explained by a partial or incorrect flash write.
A second independent programmer read is still requested to check read
repeatability before restoration. No external-programmer write or stock
readback verification has been reported.
