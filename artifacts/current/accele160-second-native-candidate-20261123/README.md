# Native writer candidate for spare 10112504772

Prepared 2026-11-23 from this spare's own accepted 1 MiB stock image,
SHA-256 `0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`.
The candidate is `candidate.bin`, SHA-256
`a56b4a1b84a8ef452be094ecc803c9f26d449c066eb023ad895c78828b9e1e68`.
It contains the corrected native RTEMS writer from branch
`codex/accele160-writer-integration`: stage two
`e92ec1fb8a405a3d64f37f1a09227d593ecd84bc17151e5c935594212c0de0b1`
and RTEMS `e903a46a21e135d2de17921c0e1947fd5fe31254882fb35acc0f451a02c433a5`.

The packer changed 510,899 bytes only within the eight mutable firmware
blocks `0x40000..0xbffff`. The entire mutable region is byte-identical to
the corrected candidate prepared for card `10112500320`; the x86 option ROM,
diagnostics, descriptor, serial and reset block are preserved from **this**
spare's stock image. [Pack receipt](pack-receipt.json) and
[independent region review](review.json) pin these facts.

This is an **offline candidate**, not a qualification to program the card.
Card `10112504772` booted stock but twice returned stock FLASHIMAGE writer
failure `80/16`; in-system flashing is not the route for this experiment.
The candidate has not been cold booted on hardware, and its native erase and
program routine has not been exercised on a physical flash chip. The working
Firmware injection v1 card `10112500320` should remain untouched while
testing this spare.

Before any external-programmer write, read the exact chip twice and compare
both 1 MiB reads to the stock SHA above. If the reads, chip marking, package
orientation or programmer's exact Intel E28F008S3 profile differ, stop.
Keep one verified stock copy for restoration. After programming, read back
the complete chip and require the candidate SHA above. Then install only
this spare, observe HP beep and Linux enumeration, and capture two full
firmware reads if the controller starts. A failure is evidence about this
spare and image; restore its own stock bytes with the programmer before
using it again.

The complete 1 MiB candidate stays local at
`artifacts/current/accele160-second-native-candidate-20261123/candidate.bin`.
Only this note and small receipts belong in Git. No card was programmed as
part of this preparation.
