# Opcode 0x6F handler DRAM audit — 2026-10-10

**Result:** `C0120000` was readable and contained 64 zero bytes in two live,
sentinel-distinguished reads. The matching stock bootstrap clears it before the
metadata hook, and the reviewed allocator starts at `C0140000`. **Exclusive
ownership is still unproved.** The offline stock-preserving image remains
`flash_ready: false`; do not install it on the card on this evidence alone.

## Exact build and startup order

The pinned full ROM SHA-256 is `43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93`.
Its installed boot-block SHA-256 is `d10cca35861b66ef38c74de9b7409438b5a46ed3c3b238d5abfcc879d32bd85c`.
The decompressed program SHA-256 is `21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195`.

The matching [bootstrap disassembly](../../artifacts/vendor-fujitsu/4.07-0-29/bootstrap.dis)
at `FEFC813C–FEFC816C` clears `C0000000–C013FFFF` in 16-byte stores, then copies
its runtime and calls the decompressor. The patched metadata entry runs **after**
that copy/decompression. Thus the bootstrap clear will not erase a handler
installed by this hook. This is a control-flow observation, not a lifetime
reservation.

The reviewed allocator at `C001EA70–C001EB88` returns addresses of the form
`C0140000 + index × unit`. Fresh Enquiry2 geometry and the live board object
show unit `0x2000`, count `0x739`, and the existing staging pointer
`C0F2C000`. The board's `+0x128` field is `0xEC0000`; references of the form
`C013FFC0(+0x128)` therefore resolve to `C0FFFFC0`, near the top of reported
16 MiB DRAM, rather than into the proposed `C0120000` window. This allocator
cannot return `C0120000` under the observed profile. Other indirect users and
DMA are not excluded by that fact.

Direct decoded address references were checked in the matching bootstrap,
decompressed program, and installed boot block. There were no direct
`C012xxxx` instruction operands. The highest direct bootstrap references below
the candidate window are around `C011E230`; the program has four `C013xxxx`
operands, all associated with the variable-relative top-of-memory/parity path.
Disassembly is incomplete evidence: computed pointers, tables, DMA and
asynchronous activity can reach addresses without a literal operand.

An older `artifacts/private-dumps/remote-analysis/bootblock.dis` contains a
`C0120000` recovery-copy destination. **That is not the installed boot block.**
The exact fresh-dump [boot-block disassembly](../../artifacts/private-dumps/snapshot-fresh-20261010T125336Z/bootblock.dis)
uses `C0140000`, `C0160000`, `C0180000` and `C01A0000` for successive flash
banks in that path (`FEFFDCA4–FEFFDD18`). Do not mix these two memory profiles.

## Live fixed read

The read-only probe was gated behind the already verified pointer and runtime
checks. Only `opcode 0x20`, 64 bytes, offset `FF1F4000` relative to staging
`C0F2C000` was newly allowed. It issued two reads with A5 and 5A DMA sentinel
patterns. Both returned 64 zeros with matched completion IDs, status zero and
unchanged DMA guards. All 15 commands completed, `pending=0`, and the module
was removed. The card is driverless again. No upload, custom execution, reset,
reboot, recovery entry or flash write occurred.

The [capture](../../artifacts/dram-hook-audit-20261010/README.md) includes the complete
transaction log and paired binary responses. The validator reports 64 zero
bytes, `exclusive_ownership_proven: false`. A zero snapshot only establishes
occupancy at the sampled time; it cannot show what normal firmware may do
later or under a different workload.

## Decision for the candidate

The 20-byte PING code currently lives at `C0120000` and the command-table word
at `C001F9BC` points there. Its startup ordering and allocator exclusion are
supported, but no firmware-owned reservation protects it from indirect uses,
DMA or later activity. The current image is therefore still an offline design,
not a live-test image.

The next implementation step should make handler storage firmware-owned for
the entire command lifetime, then repeat the hook build and image checks.
One concrete route to investigate is a deferred patch after the stock staging
allocation exists, using its extra owned block; that route must prove the
allocation remains held and does not conflict with image-transfer commands.
Alternatively, identify a provably unused resident code region. The present
zero snapshot is not a substitute for either ownership proof.

**Step-3 update:** [ROM-HANDLER-STEP3.md](ROM-HANDLER-STEP3.md) traced stock
staging free paths and rejected the deferred staging-block idea. A successor
offline image places PING in verified firmware flash padding instead. It still
requires live instruction-fetch and recovery validation before flashing.
