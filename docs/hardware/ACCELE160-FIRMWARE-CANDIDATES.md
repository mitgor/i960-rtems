# AcceleRAID 160 firmware candidate index

Updated 2026-11-22. Start here before choosing an image, interpreting an old
test, or packing a new card. This index covers the recent October–November
2026 AcceleRAID 160 work. [Experiment names](ACCELE160-FIRMWARE-NAMES.md)
define the vocabulary; the [card 10112504772 flash handoff](ACCELE160-CARD-10112504772-FLASH-HANDOFF.md)
holds the detailed failure analysis.

**A firmware family is not a transferable binary.** Every complete 1 MiB
image contains card-specific descriptor bytes. Match a fresh, independent
pair of full reads to the exact base image, then build and audit a candidate
for that card. Never use an image made for one serial on another card.

## Status at a glance

| Family and image | Main capability | Physical result | Present decision |
| --- | --- | --- | --- |
| **Firmware injection v1**, accepted October image `1c4995ad…a74b89bd` | Stock RAID runtime plus persistent `0x8f` RAM admission handler; host loads RTEMS/Doom into RAM | Flashed, cold-read verified and used on its original card | Accepted for that exact card and returning-code path |
| **Ram injection v1** | Same handler installed temporarily into stock card RAM; RTEMS/Doom loaded without a flash write | Passed on stock card `10112504772`, including 15-page RTEMS and 40 Doom frames | Working flashless development route |
| **native firmware handler v1**, passive image `4cdfbf29…a974c00edc5b` | Native RTEMS boot and host-facing handler, no UPD1 service or card-side flash writer | Stock FLASHIMAGE passed on card `10112502260`; host cold booted | Hardware boot milestone; cannot self-flash |
| **Native updater, receiver only**, first-spare image `17804234…3acca790f` | Native RTEMS plus UPD1 receive/seal/abort service; **no linked Intel writer** | Flashed restored first spare, cold booted and ran RTEMS `PASS`; UPD1 interface not physically exercised | Best proven native boot base, not a proven update path |
| **Native updater, receiver only**, verified image `2aa1d5a8…2a620289a3dab9fe2` | Corrected UPD1 v2 and post-write verification logic, with no writer linked | Offline interpreter/QEMU/Linux-guest tests only | Do not treat as hardware-qualified |
| **Native firmware with flash tool**, experimental image `867f7320…e2a6453` | Native RTEMS, UPD1 v2, **linked Intel 28F008S3 erase/program/readback routine** | Built and tested in an S3 software model; **never flashed or booted on hardware** | **Prepared, but unqualified for physical flashing or APPLY** |
| **Native firmware with flash tool**, corrected card `10112500320` image `b35b1e83…4662c695` | Same service with the split-port gate correction and this card's exact descriptor | Reproducible cross-build; compiled i960 normal APPLY and gate-off fault passed in the model; **never flashed or booted on hardware** | **Latest offline candidate; not qualified for physical flashing or APPLY** |
| **Firmware injection v1**, failed comparison image `ce3e632c…10c5c9af4` | October handler rebased onto serial `10112504772` | STOREIMAGE/readback passed; FLASHIMAGE failed `80/16`; cold reads stayed stock | Do not retry blindly on that card |

Short hashes above are labels only. The full hashes and evidence below are the
identities used for any automated gate.

## Card map

| Card | Stock full-flash SHA-256 | Latest established state |
| --- | --- | --- |
| Current Slot 5 card, serial `10112500320` | `93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094` | [Accepted Firmware injection v1](../../artifacts/current/accele160-working-injection-return-20261122/README.md) `1c4995ad…a74b89bd`; Linux boot and two matching full reads on 2026-11-22 |
| Previous Slot 5 card, serial `10112504772` | `0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943` | Stock after two `80/16` FLASHIMAGE refusals; cold boot and paired full reads passed on 2026-11-21 |
| Unidentified spare tried on 2026-11-22 | Unknown; no full read yet | HP Z400 did not reach beep with it installed; it was removed without our software accessing or flashing it |
| Restored first spare | `fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816` | Native UPD1 receiver image `17804234…3acca790f` flashed and booted; no linked writer |
| Former Slot 5 card, serial `10112502260` | `1ee91ea1c172069dd0c98ec68fdf7ebae45e7477466f90b94e36e160f20f3f65` | Passive native image `4cdfbf29…a974c00edc5b` flashed and booted; no UPD1 endpoint |
| Original-card base used by the experimental writer build | `0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a` | Build input only for image `867f7320…e2a6453`; do not assume the physical card is in the PC |

The PCI BDF changes with slot placement; it is not a stable card identity.
Use the card's own stock SHA-256 and serial, plus its physical label, when
preparing a candidate or recovery image.

## The native image with the on-card flash tool

The first offline candidate in the **native firmware with flash tool** family
is local file `artifacts/current/accele160-experimental-writer-unqualified-20261120/candidate.bin`,
SHA-256 `867f7320d5f8cc2623cd6b024cecf988df754eaa92dd3eaf6452fecb8e2a6453`.
The binary and large test captures remain local; the documentation is tracked.
That image is a complete 1 MiB build from original-card stock SHA-256
`0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a`.
It is **only** appropriate as a binary for a card whose two fresh full reads
match that base exactly. In particular, it is not a binary for current Slot 5
serial `10112500320`, former Slot 5 serial `10112504772`, or the restored first spare.

For current Slot 5 card `10112500320`, the newer
[corrected per-card build](../../artifacts/current/accele160-writer-gate-corrected-offline-20261122/README.md)
has SHA-256 `b35b1e8312336532fae9175fdc3d0d0be7b80b14281434f42af1db294662c695`.
It replaces the gate readback assumption and is reproducible, but remains
offline-only. The older `867f…` image is not the binary to test on this card.

The build uses `ACCELE160_UPDATER_STAGING=1` and
`ACCELE160_FLASH_WRITER_EXPERIMENTAL=1`. Its UPD1 v2 service receives 256
ordered 4 KiB chunks, checks transport and full-image hashes, seals a target,
and has an explicit APPLY command. The linked writer probes the Intel chip ID
and locks, permits only full 64 KiB blocks at `0x40000..0xbffff`, gates the
board flash-control bit around each operation, checks S3 status, and verifies
erased/programmed bytes. APPLY also rehashes the whole 1 MiB target. A failed
write latches the session so ABORT/retry cannot disguise a partial result.
The host-side staging and apply code lives under `host/accele160/flash/`; the
card-side service and backend live under `rtems/accele160/native_rom/`.

The [build record](../../artifacts/current/accele160-experimental-writer-unqualified-20261120/README.md)
and `pack-receipt.json` show that the stock reset block, x86 option ROM,
diagnostics and descriptor were preserved. A reproducible offline rebuild
matched the tested candidate byte for byte. Six compiled interpreter runs
exercised one successful modeled update plus gate-off, low-VPP, wrong-ID,
locked-block and unchanged-byte faults. The [fault matrix](../../artifacts/current/accele160-s3-fault-matrix-20261120/README.md)
records the resulting UPD1 and writer states. Its S3 model represents the
gate and VPP as logical switches; it does not reproduce voltage, bus timing,
power loss or the physical card.

**The image has not been submitted to stock FLASHIMAGE, has not cold booted
on a physical card, and has not performed a physical on-card update.** The
presently observed `80/16` failure on card `10112504772` was returned by
the *stock* Mylex writer, before this experimental native writer could run.
It makes hardware qualification of the write supply and gate more urgent;
it is not a test of this candidate's APPLY implementation. The experimental
image must be repacked from a selected card's own stock read and reviewed
before any future physical trial. Do not infer a deployable image merely
from the working emulator path.

## Other images and supersession

### Firmware injection v1 and Ram injection v1

The [accepted October handler](../../artifacts/current/accele160-ram-admit-20261017/README.md)
has full-image SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`
and handler SHA-256
`8d8c79c3b8c206608ef7221000991c0d75eb101ce06581fedc2a74522648ad34`.
It preserved the stock reset, x86 ROM and RAID runtime. After a 36.84-second
successful FLASHIMAGE and cold readback, the handler accepted bounded RAM
code. Later RTEMS and Doom ran through that stock-firmware route.

On 2026-11-21, [Ram injection v1](../../artifacts/current/accele160-volatile-stock-20261121/README.md)
installed the same handler in *volatile* RAM on card `10112504772` and ran
bounded RTEMS and 40 Doom frames without a flash command. A later cold boot
and two full reads confirmed the stock flash remained intact. The
[rebased persistent candidate](../../artifacts/current/accele160-october-handler-current-spare-20261121/README.md)
for that card, SHA-256
`ce3e632c80df475d4fa372cad61255c73b5438aad76c2022308889c10c5c9af4`,
was staged and read back but its FLASHIMAGE returned `80/16`. Two full reads
after another cold boot were exactly stock. These are separate experiments:
the volatile handler works; the persistent writer attempt failed.

### Native boot and updater progression

The [first native ROM spare image](../../artifacts/current/accele160-spare-rom-20261025/README.md)
SHA-256 `6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd`
was successfully written and later externally read back exactly, but the
HP Z400 hung before the beep with that image. The card was restored with its
own programmer backup. This was a **boot-path failure after a successful
flash**, distinct from the current card's writer refusal.

Later native images added early PCI configuration-retry release. The passive
image SHA-256 `4cdfbf29ea7fddb8b667bc3eddd7efa43e95d160df4fcbd51070a974c00edc5b`
was written to card `10112502260` with stock FLASHIMAGE status 0 in about
35.7 seconds; it is a hardware boot milestone, but it has no UPD1 service or
writer. The [restored first spare's native updater image](../../artifacts/current/accele160-restored-first-spare-updater-20261120/README.md)
SHA-256 `17804234a6198963753674e4c6b074777a95c7fbab717e5d914d5376ad54dc29`
was also written successfully in 34.9 seconds. On cold boot the host beeped
and reached Linux, PCI retry was released, and RTEMS reported `PASS`. It has
UPD1 receive/seal logic but **no linked Intel flash writer**. The physical
UPD1 control and staging pages were not yet tested in that installed image.

The receiver-only candidate sequence for card `10112502260` is:

| Artifact | Revision | Result |
| --- | --- | --- |
| [`accele160-native-updater-20261119-v2`](../../artifacts/current/accele160-native-updater-20261119-v2/README.md) | UPD1 v1 with overlapping hash/state fields | Superseded |
| [`accele160-native-updater-recovery-20261120`](../../artifacts/current/accele160-native-updater-recovery-20261120/README.md) | UPD1 v2; fixed hash placement and RAM-session ABORT | Superseded |
| [`accele160-native-updater-verified-20261120`](../../artifacts/current/accele160-native-updater-verified-20261120/README.md) | UPD1 v2 plus independent post-write block readback and whole-image checks | Latest receiver-only offline build; no linked writer |

The verified receiver-only image SHA-256 is
`2aa1d5a8dfbfc99be8d9b1c302a6adaf30ad9f569a6b3ff2a620289a3dab9fe2`.
Its interpreter, QEMU, Linux guest and software fault gates test protocol
behavior. They are not a hardware flash qualification. Also, the installed
passive image on card `10112502260` has no UPD1 endpoint, so it cannot receive
the newer image through UPD1 without another deployment path.
The intermediate `accele160-native-updater-20261120` directory is a local-only
archive symlink; the corrected `-recovery` and `-verified` records above are
the stable references.

## Recent experiment sequence

| Date | Observation | Meaning |
| --- | --- | --- |
| 2026-10-17 | Firmware injection v1 flashed in 36.84 s; cold readback and RAM admission passed | Stock runtime plus persistent handler works on that specific card |
| 2026-10-25 | First native ROM flashed in 35.1 s, but HP Z400 hung before beep; external programmer later read back the exact candidate | Successful programming does not guarantee physical native boot |
| 2026-11-19 | A passive native image with PCI retry release was flashed to card `10112502260` with status 0 | A native boot path without self-flashing became available |
| 2026-11-20 | Restored first spare accepted native UPD1 receiver image in 34.9 s and cold booted to RTEMS `PASS` | Native updater admission code is installed there, but its writer is absent and the UPD1 interface remains untested on hardware |
| 2026-11-20 | Corrected UPD1 v2 receiver-only image and separate Intel-writer image passed offline gates | Protocol and model behavior advanced; no physical on-card update was proven |
| 2026-11-21 | Card `10112504772` rejected both a native-writer diagnostic image and the October handler image with `80/16`; cold reads stayed stock | Its stock flash writer path is the immediate hardware blocker |
| 2026-11-21 | The same stock card ran Ram injection v1, bounded RTEMS, and 40 Doom frames | RTEMS/Doom work can proceed without another flash write |
| 2026-11-22 | An unidentified spare stopped HP POST before beep; the user replaced it with working Firmware injection v1 card `10112500320`, whose exact accepted image was confirmed by two full reads | The no-beep spare needs its own offline chip/board diagnosis; the working card provides a known-good baseline |

## Card-specific failure and next decision

Card `10112504772` last read as exact stock SHA-256
`0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`.
It has twice staged and independently read back different complete images,
then returned stock writer sense `80/16` immediately. Each failed attempt
left the flash stock after a cold boot. All sixteen block locks and the master
lock read clear; VPP and write-enable waveforms remain unmeasured. See the
[card-specific handoff](ACCELE160-CARD-10112504772-FLASH-HANDOFF.md).

The practical next split is:

1. Keep the current working Firmware injection v1 card `10112500320` as a
   known-good RTEMS/Doom baseline. The former stock card `10112504772` can
   continue RTEMS/Doom development through **Ram injection v1** without
   touching its flash.
2. Investigate serial `10112504772` as a separate write-path problem: compare
   its board and jumper state to a successful card, then measure VPP and chip
   control signals during a reviewed, instrumented attempt if needed. A third
   blind full-image FLASHIMAGE would add little evidence and could erase the
   boot block.
3. For persistent native development, use a card identified by serial and
   fresh full reads. The restored first spare has the best physical native
   boot evidence. Repack any future candidate from that card's exact base;
   keep its own programmer recovery image ready. Qualify the on-card writer
   separately before relying on host-only future updates.
4. Label the unidentified no-beep spare, read its chip twice with the
   external programmer, and compare its bytes with a card-specific stock
   reference before deciding whether its problem is image, board or slot
   interaction. Its identity is not established by its appearance alone.

The directory name `artifacts/current/` is an archive location, not a
statement that an image is installed, newest, or approved. Prefer the exact
SHA-256 and physical result above over a filename, date or old pack receipt.
