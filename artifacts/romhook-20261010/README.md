# ROM-backed stock hook build artifact — 2026-10-10

This directory holds the exact step-3 target build and 512 KiB offline image
described in [ROM-HANDLER-STEP3.md](../../docs/loader/ROM-HANDLER-STEP3.md). `start.s`,
`link.ld`, `Makefile` and `build_image.py` are the archived build inputs.
`romhook.elf`, `.bin`, `.dis` and `.map` are the target outputs; the raw image
and JSON manifest are `candidate-full-rom.bin` and `.bin.json`.
`verify_layout.py` is an independent byte-contract checker; its result is
`layout-check.json`.

Hook: 48 bytes, SHA-256
`91b445806f67b20ac0b90d4ec72cca63ad56a097759a0f60534f8ecdcb7b821d`.
Candidate: 524,288 bytes, SHA-256
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
The image differs from stock in 48 bytes. It has not run on the card and is
not ready for flash programming.

Step 4 adds `experimental-firmware.img` and its manifest. The MIMG is a
229,898-byte offline wrapper of the exact candidate; SHA-256
`4c32da1011bcf182b08998a8a00148a665e957d3958593e76d81605a1e72dc2b`.
The package builder and its regression tests are copied here as exact inputs.
`recovery-audit/` holds the existing partial vendor/boot-monitor check applied
to this exact wrapper; it does not establish a working recovery procedure.
See [ROM-HANDLER-STEP4.md](../../docs/loader/ROM-HANDLER-STEP4.md). It has not been
accepted by the updater or programmed on the card.
