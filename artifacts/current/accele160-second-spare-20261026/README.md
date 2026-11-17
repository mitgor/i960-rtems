# Second AcceleRAID 160 spare, 2026-10-26

The user installed an unmodified second spare and booted the PC. Linux boot
ID `a8dda292-3e9c-4e77-86a3-be80bbcde5a8` shows two `1069:0050`,
subsystem `1069:0054`, revision-02 controllers: the new spare at
`0000:37:04.1` and the original card at `0000:37:09.1`. The original card
remained unbound. The reviewed `myrsread` driver was loaded with
`read_bdf=0000:37:04.1` and bound only to the spare; neither card exposed
storage.

Two guarded [full reads](rawflash-0/result.json) and
[their independent repeat](rawflash-1/result.json) returned identical
1 MiB stock images, SHA-256
`0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`.
Both returned status/residual/guard changes zero, released their DMA, and
unloaded the reader module. The new image differs from the first spare's
stock capture in 18 bytes, all inside its card-specific descriptor
`0xe0000..0xeffff`. The x86 option ROM and main firmware match exactly.

The [stock-preserving native image](native-rom-second-spare.bin) was built
from **this spare's** capture with the previously tested stage-two loader
and RTEMS scheduler diagnostic. Its SHA-256 is
`32f86984f52183c392ceca34995609ddd07d050851bd0e735a5aff8f72d77976`.
The [no-x86-ROM variant](native-rom-second-spare-no-x86-rom.bin), SHA-256
`33f7a5585c41850690ee0fa05a56382c626e75cd17c8e5185a764f57f741f221`,
changes only flash byte `0x30000` from `0x55` to `0x00`. Loader, RTEMS,
trailer, descriptor, and i960 reset block remain identical to the card-specific
native image. The [same-boot preflight](romless-preflight.json) accepted this
exact candidate and both stock reads; it records no STOREIMAGE or FLASHIMAGE.

The [QEMU BIOS comparison](romless-post.json) with this card-specific image
repeated the prior result: with the valid x86 ROM, experimental SeaBIOS
entered its BAR polling loop and did not reach a test boot sector in eight
seconds; with the signature disabled, it reached the boot-sector marker with
zero Mylex BAR accesses. The [i960 interpreter run](romless-i960.log) of the
exact variant reached the RTEMS `PASS` record and intentional park after
1,608,278 instructions. The interpreter uses an exploratory board-ID-11
response, not a measured reset-time peripheral model.

The exact no-x86-ROM variant was then **staged only in spare controller RAM**.
The [STOREIMAGE result](stage/result.json) returned zero status, residual,
and guard changes; its module released and unloaded. The independent
[READIMAGE readback](staged-readback-0/result.json) returned the exact
candidate SHA-256 with zero status, residual, and guard changes. The
original card stayed unbound. No FLASHIMAGE command was issued. After saving
the evidence, `myrsread` was unloaded; both cards are now unbound and no
reader, stage, or flash module remains loaded.

This is a complete preflash evidence set, but a physical HP BIOS cold start
and native i960 startup remain untested for this variant. The first spare's
native image already failed before POST beep; QEMU's SeaBIOS result may not
predict this PC's HP `786G3 v03.15` BIOS. The earlier flash script remains
pinned to the **first** spare image and does not accept this one. Current
confidence in a successful cold boot is below the requested 80% threshold.

## Physical preflash discriminator

The HP Z400 QuickSpecs document per-slot option-ROM control. Live SMBIOS
identifies the unmodified second spare as `SLOT 6` (PCI bus address
`0000:37:04.0`, RAID function `.1`); the original is `SLOT 5`. The Linux
`lspci` expansion-ROM `[disabled]` flag is only the current PCI decode state,
not evidence that BIOS skipped the ROM during POST.

The next useful physical experiment is to disable **only SLOT 6 Option ROM
Download** in F10 setup while the second spare remains stock, then cold-boot
and confirm Linux still enumerates both cards. After power-off, replace the
second spare in SLOT 6 with the first, already-failed native-ROM card and
cold-boot again. If POST now completes, the previous pre-beep failure is
strong evidence for an x86 option-ROM interaction. A failure would instead
leave i960 reset, PCI behavior, and other host initialization suspects open.
Neither step flashes a card; the failed first spare can be removed again to
restore the known-good configuration. The slot-6 ROM setting must be restored
or kept documented before testing future images. Do not infer that a
successful POST proves RTEMS runtime operation.

HP source: https://www.hp.com/canada/products/landing/workstations/files/13276_na.pdf

## Physical Slot 6 test result

The user set HP F10 `Slot 6 Option ROM Download = Disable`, disabled the
Mylex BIOS boot procedures on both then-installed stock cards, and also
disabled the SATA RAID option ROM. With the original card in Slot 5 and the
unmodified second spare in Slot 6, the HP Z400 booted Linux; live PCI
enumeration found both `1069:0050` functions at `0000:37:09.1` and
`0000:37:04.1`, respectively. We then issued `systemctl poweroff` remotely
and confirmed SSH became unavailable. The user replaced the Slot 6 stock
spare with the first native-ROM-flashed spare while leaving the original in
Slot 5. On power-up, the PC **again hung before the beep**. No flash command
was issued during this experiment.

This result makes the x86 option ROM an insufficient explanation of the
observed hang if the HP Slot 6 setting took effect as configured. It does
not independently prove that the BIOS skipped expansion-ROM execution, nor
identify which i960 reset/PCI-visible failure caused the hang. Do not
advance the second spare to flash on the strength of the SeaBIOS experiment.
The failed spare should be removed to restore the known booting setup; its
post-test flash contents and physical recovery remain unverified.

On 2026-11-10, an external-programmer read of the failed first spare proved
its 1 MiB flash is byte-for-byte the intended native image. See the
[first-spare recovery evidence](../accele160-spare-rom-20261025/README.md).
This rules out a partial FLASHIMAGE write as the explanation of the failed
POST. The prepared second-spare no-option-ROM image still carries the same
i960 reset/stage-two/RTEMS path and is **not flash-qualified**.

## Offline host-visible startup comparison, 2026-11-15

The read-only [state comparison](offline-host-state-3.json), made with
[`compare_host_state.py`](../../../rtems/accele160/emulator/compare_host_state.py),
replays this spare's exact stock and no-ROM candidate images under the same
exploratory reset selector 11. At cycle 1,608,278, the native image has its
RTEMS `PASS` report and parks. Stock at the *same* cycle still executes its
loader. Both have board context zero, PIRSR zero, and MU inbound mask
`0xffffffff`. This avoids treating an early stock state as a candidate
failure.

By cycle 48,565,709 stock reaches its runtime and subsequently creates board
context `c048b520`, kind `0x20`, and PIRSR `0x0e`. The native image never
reaches that startup code: it intentionally stops after the scheduling
diagnostic. The offline comparison therefore identifies a concrete native
firmware task: initialize the PCI/interrupt and mailbox-facing state and
answer the host's early requests before considering another cold-boot test.
It cannot prove that this missing runtime caused the HP pre-beep hang. Some
register reads in this interpreter are placeholders rather than verified
physical reset values, and the two late milestones occur at different
times. No hardware was accessed.
