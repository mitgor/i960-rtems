# One-attempt October handler comparison on the current stock spare

Card `0000:37:09.1` (serial `10112504772`) has stock full-flash SHA-256
`0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`.
Its previous native-writer FLASHIMAGE returned internal status `80/16` in
less than one host jiffy. A later cold boot produced two complete stock reads
with no changed byte. All sixteen flash block locks and the master lock read
as clear; VPP and write strobes have not been measured.

The proposed `candidate.bin` is the exact October RAM-admission handler
firmware, rebased onto this spare. It differs from the physically accepted
October image `1c4995ad...a74b89bd` **only at the four serial-number bytes**.
Its SHA-256 is
`ce3e632c80df475d4fa372cad61255c73b5438aad76c2022308889c10c5c9af4`.
The [builder](../../../host/accele160/flash/build_october_handler_for_current_spare.py)
pins both stock images, the October candidate and exact handler. It verifies
that the only change to this spare's stock image is the October loader hook,
4324-byte handler, and two required checksum words. The compressed runtime,
boot block and serial are unchanged. `audit.json` records the full checks.
`stock-for-programmer.bin` is this card's exact 1 MiB stock READIMAGE backup.

The flash tool has an explicit `--october-handler-proof` mode for this one
candidate on Slot 5. It requires a new-boot pair of full stock reads, a
same-boot auto-sense probe, STOREIMAGE and independent staged READIMAGE,
and creates `october-handler-attempt.json` *before* FLASHIMAGE so it cannot
repeat by accident. The ordinary quarantine remains in force. The PC must
first cold boot because the preceding RAM-only Doom run retained RTEMS/DMA
ownership until reset.

This experiment is not a harmless write of only the handler bytes: stock
FLASHIMAGE erases all sixteen blocks, including the boot block, before it
programs. If erase begins but fails partway, the card may no longer boot and
will require the external programmer. The user has authorized one comparison
attempt and has another clear spare available. A second `80/16` would support
a card-specific write-path problem but would not alone identify its component.
Success requires a cold boot, two full matching reads of the candidate, and a
working persistent handler ping before running RTEMS or Doom.

Status: candidate built and copied to the remote host for the next cold boot; no
FLASHIMAGE of this candidate has been issued yet.
