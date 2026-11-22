# Corrected native writer image for card 10112500320: offline only

Prepared 2026-11-22 on branch `codex/accele160-writer-integration`. This is
**native firmware with flash tool**, built with UPD1 v2 and the linked Intel
28F008S3 writer. It incorporates Claude's split-port gate correction: write
the stock constants `8` and `0`, report the gate-port read in UPD1 word 15,
and let the flash chip status determine VPP failure. The source was taken
from the frozen previous writer build and changed only where recorded by the
branch commits. This image is **not approved for a physical flash or APPLY**.

| Identity | SHA-256 |
| --- | --- |
| Card `10112500320` archived stock base | `93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094` |
| Card's currently installed Firmware injection v1 image | `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd` |
| Corrected native candidate `candidate-10112500320.bin` | `b35b1e8312336532fae9175fdc3d0d0be7b80b14281434f42af1db294662c695` |
| Stage two | `e92ec1fb8a405a3d64f37f1a09227d593ecd84bc17151e5c935594212c0de0b1` |
| Corrected RTEMS | `e903a46a21e135d2de17921c0e1947fd5fe31254882fb35acc0f451a02c433a5` |

The packer used this card's own archived preflash stock image. The exact
currently installed Firmware injection image was read twice from the live
card on boot `4b10bf1b-7fcb-4d07-b52d-88c62a334a3c`; both full reads
matched its pinned hash. The new image preserves all bytes outside the
mutable `0x40000..0xbffff` firmware area, including the x86 option ROM,
diagnostics, reset block and descriptor serial `10112500320`. Compared with
the installed image it changes 515,165 bytes across the eight mutable 64 KiB
blocks. `pack-10112500320.json` and `current-card-review.json` record the
independent checks. The source build from the archived toolchain produced
the same corrected RTEMS SHA as Claude's branch; a second complete rebuild
reproduced the per-card candidate byte for byte. `build-manifest.json`
describes the first build against the original-card stock base; the separate
per-card pack receipt and frozen command below identify the `10112500320`
candidate. Rebuild with:

```sh
bash rtems/accele160/native_rom/rebuild_writer_10112500320.sh NEW_OUTPUT_DIR
```

The source-level packer, S3 writer, gate-hold and updater model tests passed
in the isolated integration checkout: 29 passed, one full-image replay
deliberately skipped. Sixteen host update-tool tests passed; both C updater
test programs compiled and ran with AddressSanitizer and UndefinedBehavior
Sanitizer. The emulator rebuilt from the integrated source with SHA-256
`2e2667c1edfd29007b0f077c5e0d9543ffc53c7c42211dc8fd57a942c3edb200`,
byte-for-byte identical to the binary used for the following runs. The
compiled i960 interpreter accepted all 256 UPD1 chunks, sealed the target,
and completed modeled APPLY to one changed block (`0xb0000`, target SHA-256
`1c842af220cb5f48dc0b1d3a26e8219285ee6bcebc736730953e7446a8c82d5d`)
with status 0/state 3. With the board gate stuck off, APPLY
returned status 9/state 4, the S3 writer reported result 5/status `0xa8`,
and later ABORT/APPLY were refused. The two complete emulator receipts are
`emulator-apply-normal.json` and `emulator-gate-stuck-off.json`.

These are software results. No physical UPD1 transfer, VPP measurement,
write strobe, on-card erase/program, or cold boot of this image has occurred.
The corrected gate writes constants `8` and `0`, but the stock writer also
uses a RAM shadow; whether other latch bits must be preserved in native mode
is not established. The working Firmware injection card is the only current
in-system-flashable baseline and should not be consumed merely to repeat an
emulator pass. The separate stock card `10112504772` returned stock writer
`80/16` with two candidates; this corrected native image cannot repair that
card's stock firmware writer. The first physical on-card update still needs
an identified recovery path, a measured gate/VPP result, and explicit
post-APPLY readback and cold-boot checks.

The complete candidate and model target are kept locally. Only small
receipts and this note are intended for Git to keep the repository size
under control.
