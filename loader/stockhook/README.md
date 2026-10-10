# Stock-preserving command hook

Successor: [ROM-HANDLER-STEP3.md](../../ROM-HANDLER-STEP3.md) and
`loader/romhook/` place PING in firmware flash padding. This directory
preserves the first DRAM-backed design for comparison.

Memory audit: [DRAM-HOOK-AUDIT.md](../../DRAM-HOOK-AUDIT.md). C0120000 was zero
in a fixed live read, but exclusive lifetime ownership is unproved. This exact
candidate remains an offline artifact and is not flash-ready.

`start.s` is entered through the existing boot metadata handoff. It copies a
20-byte `PING` callback into candidate DRAM at `C0120000`, patches the one
previously unsupported opcode `0x6F` in the decompressed command table, and
branches to the original stock entry `C004A2E0`.

The source is linked at `FEFE0000` in the archived image's zero padding.
`link.ld` checks that the callback is exactly 20 bytes, the code remains in
the 4 KiB padding slot, and no data or BSS is needed. `build_image.py` accepts
only the pinned stock dump, unpacked program and inspected target binary. It
produces a raw offline candidate and JSON manifest, not a vendor updater file.

Build on the SSH host with the archived i960 toolchain:

```sh
make CROSS=/home/mit/i960/tools/bin/i960-coff-
```

Rebuild the full image from the project root (choose a new output path):

```sh
python3 loader/stockhook/build_image.py \
  --stock artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin \
  --unpacked artifacts/vendor-fujitsu/4.07-0-29/unpacked.bin \
  --hook artifacts/stockhook-20261010/stockhook.bin \
  --out /tmp/stockhook-rebuild.bin
python3 -B -m unittest discover -s loader/stockhook -p 'test_*.py'
```

See [STOCK-PRESERVING-HOOK.md](../../STOCK-PRESERVING-HOOK.md) for exact
addresses, what the image preserves, and the unresolved DRAM ownership gate.
Do not use this raw image as a flashing file.
