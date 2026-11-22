# Experimental native on-card writer, unqualified

This is an **offline build artifact**, not an approved flash image. Do not
submit `candidate.bin` to the stock FLASHIMAGE procedure or to native APPLY.
The physical write gate, VPP, and cold boot of this image have not been tested.

`candidate.bin` was built from the accepted original-card stock image with
SHA-256 `0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a`.
It is valid only for a card whose fresh, independent full-flash reads match
that exact base. A different spare requires a new per-card pack and review.

| File | SHA-256 |
| --- | --- |
| `candidate.bin` | `867f7320d5f8cc2623cd6b024cecf988df754eaa92dd3eaf6452fecb8e2a6453` |
| `stage2.bin` | `e92ec1fb8a405a3d64f37f1a09227d593ecd84bc17151e5c935594212c0de0b1` |
| `rtems.bin` | `ad07d3b08b17f4c1cb1c9688d485475cf324355ceba77fbf8869e010912b4b5d` |

The clean rebuild matched the image used in the six compiled emulator runs
byte for byte. `pack-receipt.json` records that the stock reset block, x86
option ROM, diagnostics, and descriptor were preserved. `build-manifest.json`
pins the local source files, source archives, stock base, and container image
ID. The build can be repeated with
`rtems/accele160/native_rom/rebuild_writer_offline.sh NEW_OUTPUT_DIR`.

The normal and five injected fault emulator receipts are in
`artifacts/current/accele160-s3-fault-matrix-20261120/`. Those runs test
software behavior and do not establish card electrical behavior.
