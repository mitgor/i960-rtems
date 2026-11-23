# One-shot in-host attempt on spare 10112504772

The user explicitly requested a third in-host FLASHIMAGE attempt on this
spare. Its stock writer already returned `80/16` on two distinct staged and
read-back-verified candidates. No hardware fault or VPP condition has been
resolved; another rejection or a partial erase is possible. The working
Firmware injection v1 card `10112500320` must be removed and stored before
this attempt.

The exact corrected native candidate is the 1 MiB local file
`artifacts/current/accele160-second-native-candidate-20261123/candidate.bin`,
SHA-256 `a56b4a1b84a8ef452be094ecc803c9f26d449c066eb023ad895c78828b9e1e68`.
Its paired stock SHA-256 is
`0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`.
The corrected RTEMS image includes UPD1 v2 and the on-card Intel S3 writer,
but the stock writer performs this installation; native code cannot help
until it boots.

`preflight.py` pins only this stock/candidate pair for Slot 5. The existing
guarded `stage_native_spare.py` requires two independent full reads from the
same boot, the sole BDF-limited card, no storage, an idle descriptor and the
pinned STOREIMAGE module. A separate full READIMAGE must match the candidate
byte for byte. `flash_second_spare_once.py` then requires that exact staged
readback, the pinned auto-sense FLASHIMAGE module, the same card and boot, an
absent peer and an unused persistent attempt marker. Its default mode is
preflight only. With `--execute`, it writes the marker before loading the
module and submits one `0x2e` request. On failure or timeout it retains the
module and records status/sense for inspection; there is no automatic retry.
On success it releases the module and still requires a cold-boot full
readback. The marker is not a safety guarantee if manually removed.

This preparation does not program any card. The first live gate is physical
identification of the swapped spare, then two same-boot stock reads.
