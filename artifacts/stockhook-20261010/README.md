# Stock-preserving hook build artifact — 2026-10-10

Successor: [ROM-HANDLER-STEP3.md](../../ROM-HANDLER-STEP3.md) archives a
ROM-backed handler at FEFE001C. This directory preserves the earlier
DRAM-backed image for comparison.

The later [DRAM audit](../../DRAM-HOOK-AUDIT.md) found C0120000 zero on the
running card, but did not establish exclusive ownership. This image remains
`flash_ready: false`.

This directory contains the exact offline target build and 512 KiB candidate
described in [STOCK-PRESERVING-HOOK.md](../../STOCK-PRESERVING-HOOK.md). The
archived inputs are `start.s`, `link.ld`, `Makefile` and `build_image.py`. The
target outputs are `stockhook.bin`, `.elf`, `.dis` and `.map`. The reconstructed
raw image and its report are `candidate-full-rom.bin` and `.bin.json`.

Hook: 84 bytes, SHA-256
`2a96bc45edd69b665dbd42b4dd17bd6594817ba64b34525c2e88e4e1faf0d16a`.
Candidate: 524,288 bytes, SHA-256
`25dd3cc627096b9e66889d67451edbba199d881084058656bd41ca5ef6778e4b`.
Exactly 76 bytes differ from stock. The candidate has not run on the card and
is not ready for flash programming.
