# Native updater staging prototype, 2026-11-20

Superseded by [the corrected build](../accele160-native-updater-20261120/README.md).

This directory contains an **offline-built** image for the Slot 5 card with
serial `10112502260`. It was packed from that card's own stock 1 MiB read. The
currently installed passive image is SHA-256
`4cdfbf29ea7fddb8b667bc3eddd7efa43e95d160df4fcbd51070a974c00edc5b`;
the staged-updater candidate is SHA-256
`02137cafe736a9db4331e0b314231760274657760038666fa47c75f05a5fefd2`.
The [manifest](update-manifest.json) identifies one changed 64 KiB block,
`0x40000`, between those images. The [pack receipt](pack-receipt.json) verifies
that the reset block, x86 ROM and card descriptor match the stock base.

The [offline PCI retry gate](config-retry-gate.json) passed at release cycle
1,355,953, and RTEMS reached `PASS` in the interpreter. This proves neither
the host BAR upload transport nor a physical flash write. The
[host review](host-offline-review.json) validated the manifest against the two
complete images without contacting the remote PC.

The new `ACCELE160_UPDATER_STAGING=1` build polls two host-visible DRAM pages:

| Local page | PIATVR value | BAR0 offset | Purpose |
| --- | --- | --- | --- |
| `c0801000` | `c0800000` | `0x1000` | Control and acknowledgements |
| `c0803000` | `c0802000` | `0x1000` | One 4 KiB data chunk |

The full received image occupies `c0900000..c09fffff`. Control word 0 is
`UPD1` (`0x31445055`); word 10 is version 1. The host writes base and target
SHA-256 at control bytes 32 and 64, then submits `BEGIN` (1), 256 ordered
`CHUNK` (2) commands, and `SEAL` (3). For each command it writes the sequence
word last. The device writes status, state, and next expected chunk to words
7, 8, 9, then acknowledges in word 2 last. The source is hashed before
admission; each chunk has FNV32 transport checking; the full target is SHA-256
checked at seal. Bytes outside `0x40000..0xbffff` must match the source.

`stage_native_update.py --live` would stop after seal. There is **no flash
command** in this build. `updater.c` has a callback-based 64 KiB block apply
function for a future independently qualified E28F008S3 writer; it is not
linked to the service and no hardware writer exists. Its callback contract
requires full block programming and byte-for-byte readback before success.

The installed passive image has no `UPD1` endpoint. Thus the new candidate
cannot be loaded through this protocol on the card currently in the PC. The
host tool checks the `UPD1` magic and version before its first BAR write and
restores PIATVR on every exit. A deployment route still needs the card's
stock mailbox (after restoring stock firmware), an independently proven host
flash path, or an external programmer/flash bridge. No live flash operation
was performed for this artifact.

The earlier `accele160-native-updater-20261119` directory contains an
intermediate build superseded by this `-v2` directory.
