# AcceleRAID 160 programmed late-PING helper

2026-10-16. The user accepted skipping a proven recovery entry and has a team
with an external programmer that can restore this card. **The new card was
programmed, booted after a physical power cycle, and passed paired full-flash
readback plus positive/negative PING tests.** The old DAC960PG `0000:37:04.1`
stayed unbound and untouched. The exact [offline acceptance replay](acceptance.json)
pins the result to the saved evidence.

## Exact image and offline controls

The accepted stock 1 MiB image is SHA-256
`0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a`.
[`candidate.bin`](candidate.bin) is the 1 MiB late-loader PING candidate,
SHA-256 `e708c1dadbc4813dd378e8ca8c6f0e929cc29064614b9f8a27210e5e2b23d3d0`.
It changes 155 bytes in the loader cave, branch and checksum fields. The boot
block and expanded runtime contents are byte-identical to stock. The
[export receipt](export.json) matches the in-memory audit in the
[late-PING analysis](../accele160-late-ping-20261016/README.md). The export
tool independently recomputed the candidate and rejected a differing digest.
Twelve helper and eleven startup unit tests passed.

The exact Fujitsu DACFL6 0.74 binary's [command audit](vendor-audit.json)
pins `STOREIMAGE` (`0x2c`), `FLASHIMAGE` (`0x2e`), selector, offset and DMA
fields. The stage-only and flash modules were compiled for
`6.8.0-138-generic`; their exact tested binaries and sources are retained.
The stage and flash modules are deliberately separate. Merely loading the
flash module submits no command; its exact start token is
`FLASHIMAGE selector=9` plus newline.

For a new host kernel, rebuild the three companion modules from
`host/accele160/flash/` using the exact `myrs.h` in
`artifacts/current/accele160-guarded-20261016/tested-readers.tar.gz` and that
kernel's headers. The `myrsread.ko` parent used here is retained in
`artifacts/current/accele160-readimage-20261016/`. The Python wrappers pin
the card BDF, accepted image hash, same-boot receipts and ownership checks;
the flash wrapper refuses an altered readback before it loads the flash
module. These are specific to this card and image, not a general flash tool.

## Hardware sequence and current boundary

1. The first attempted `myrsread` bind on the previous boot returned mailbox
   status 2. No staging or programming command ran. We removed that unbound
   module, temporarily blacklisted stock `myrs` and rebuilt the initramfs.
   After a fresh boot, exact-BDF `myrsread` bound to `37:09.1` and the old card
   stayed unbound. The temporary file is
   `/etc/modprobe.d/i960-accele160-temporary.conf` on the host.
2. [Stage request](live-stage/request.json) sent selector 9, offset 0, full
   1 MiB through `STOREIMAGE`. The host DMA allocation was compared byte for
   byte to the candidate before command submission. Completion took 0.72 s,
   status 0, residual 0, and both DMA guard regions stayed unchanged.
3. The previously accepted guarded `READIMAGE` selector 9 read the image path
   back in 0.079 s. Its **entire 1 MiB** matched the candidate SHA-256; status,
   residual and guard changes were all zero. This proves the staging path,
   not persistent flash. A deliberate one-byte readback mutation made the
   flash preflight reject before loading the flash module.
4. [Flash preflight](live-flash/preflight.json) required the same boot ID,
   exact stage/readback hashes, card identities, status and guard receipts.
   It issued one `FLASHIMAGE 0x2e`, selector 9, zero-DMA command. Completion
   took 37.2 s with status 0 and residual 0. The module released normally;
   SSH was healthy immediately afterward. No second flash command was issued.
5. The PC did not return over SSH after the initial reboot, as has happened
   after earlier ordinary controller sessions. The user power-cycled it. On
   boot ID `bdc099fb-36ee-4a5b-a9d0-a5983f8590f4`, the new card initialized
   cleanly as firmware `6.00-05`; the old card stayed unbound. Two independent
   guarded [full reads](persistent-0/) and [second reads](persistent-1/) each
   returned status 0, residual 0 and guard changes 0. Their complete 1 MiB
   byte streams match each other and `candidate.bin` exactly, SHA-256
   `e708c1dadbc4813dd378e8ca8c6f0e929cc29064614b9f8a27210e5e2b23d3d0`.
   This proves persistent programmed contents after power cycle.
6. A new-card-only zero-DMA [valid PING](ping-valid.txt) returned host status
   **0**, residual 0. The same request with one changed signature byte
   [returned](ping-bad-signature.txt) stock unsupported status **2**, residual
   0. The 64-byte captures differ only at that signature byte. This is a
   bounded live execution proof for the helper and a fallback check; it does
   not supply an upload/call route, nonce echo or general-purpose software
   loader yet. The `ping_probe` companion was released and unloaded normally.

The temporary `myrs` blacklist was removed and initramfs rebuilt. The
reviewed `myrsread` derivative remains bound to **only the new card** in the
current boot; ordinary `myrs` will be eligible on a later boot. No test module
or DMA allocation remains pinned. Do not force-unload the bound controller
driver merely to tidy up. The external-programmer backup remains the accepted
stock 1 MiB dump, and recovery by the boot block is still untested.

Replay offline:

```sh
python3 host/accele160/flash/verify_flash_acceptance.py \
  artifacts/current/accele160-flash-candidate-20261016 \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin \
  artifacts/current/accele160-late-ping-20261016/late_ping_handler.bin \
  artifacts/current/accele160-late-ping-20261016/late_ping_callsite.bin
```

Sources: `host/accele160/helper/export_late_ping.py` and
`host/accele160/flash/{audit_vendor_commands.py,stage_image.c,stage_image.py,flash_image.c,flash_image.py,ping_probe.c,verify_flash_acceptance.py}`.
The exact stock ROM is [here](../accele160-guarded-20261016/rawflash-0/data.bin).
