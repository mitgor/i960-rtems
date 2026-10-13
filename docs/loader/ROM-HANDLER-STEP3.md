# Step 3: ROM-resident command handler — 2026-10-10

**Later result:** [ROM-FETCH-LIVE.md](ROM-FETCH-LIVE.md) verified a changed
RAM table word and a post-startup call to a stock flash `RET`. The FEFE001C
handler itself remains unflashed and unexecuted; the update procedure and
recovery exclusions below still apply.

**Result:** a second offline stock-preserving image now places the PING handler
in its own verified flash padding at `FEFE001C`. It does not use `C0120000`
or the stock staging allocation. The candidate has **not** been flashed or
executed and remains `flash_ready: false`.

## Why the staging block was rejected

The previous [DRAM audit](DRAM-HOOK-AUDIT.md) proposed deferring PING until the
stock staging allocation existed. That allocation is not held for the whole
command lifetime. The matching decompressed program calls the free routine
`C001EB90` and clears `C0112A70` at `C004D1E4–C004D1FC` and
`C004D440–C004D454`; the `WrongFl` error path at `C004D6D0–C004D6FC`
does the same. These are reachable stock flash/error paths, so a table entry
into the extra staging block could outlive the allocation. The successful
scratch write at `C0FAC010` proved RAM access, not persistent ownership.

## New image

The pinned stock image contains a zero-filled slot at full-ROM offset
`0x60000–0x60FFF` (local `FEFE0000–FEFE0FFF`) inside its type-2 firmware
component. The existing metadata handoff already enters `FEFE0000` in the
offline design. The new 48-byte target hook at that address stores
`FEFE001C` into decompressed command-table word `C001F9BC`, restores `g14=0`,
and branches to the original stock entry `C004A2E0`. PING is the unchanged
20-byte status `0x017E` handler, ending in the stock completion function
`C004BAD0`. Opcode `0xEF` is the high-bit alias of `0x6F` and selects the
same table entry.

The target-built hook SHA-256 is
`91b445806f67b20ac0b90d4ec72cca63ad56a097759a0f60534f8ecdcb7b821d`.
The archived disassembler cannot decode the final high-address `bx (g1)`;
the checked raw last instruction is `00 50 04 84`.
The 512 KiB image SHA-256 is
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
Only 48 bytes differ from the pinned stock image, inside the hook slot and
the metadata entry/checksum words. The boot block, PCI BIOS, descriptor,
bootstrap and compressed stock program are byte-identical. The metadata
word sum is valid. The exact source, target ELF/bin/disassembly/map, image
and manifest are archived in [artifacts/romhook-20261010/](../../artifacts/romhook-20261010/README.md).
An independent byte-layout checker also verified the exact changed-byte set,
metadata sum and preserved component windows; its report is archived there.

## What remains before a live test

The stock bootstrap demonstrably executes from flash before the metadata
handoff, and normal firmware later reads flash data. We have **not** proved
instruction fetch from `FEFE001C` after stock startup writes `8` to EBCR
at `C004E840`. That must be validated on hardware. The RAM command-table
store also needs a live visibility/cache check. The normal `2B/1` programming
route rewrites the lower 496 KiB, including this slot, so the handler's
lifetime during a firmware update is unresolved; do not run programming
commands against this candidate until that interaction is designed and tested.

Serial recovery entry, a verified restoration route and complete vendor
packaging remain separate preconditions for flashing. This step used SSH only
for the i960 cross-build; no PCI probe, RAM upload, controller reset, reboot,
custom execution or flash write occurred. The original DRAM-backed candidate
is preserved for comparison, but this ROM-backed image is the current offline
direction.
