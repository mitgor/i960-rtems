# Live RAM execution handoff — 2026-10-10

**Superseded finding:** [ROM-FETCH-LIVE.md](ROM-FETCH-LIVE.md) later used a
wrapped 32-bit staging-relative upload offset to change the live command
table, execute RAM callbacks and call a stock flash `RET`. The no-callback
conclusion below is retained as historical analysis of the unwrapped path.

## Result

The stock 4.07-0-29 firmware can copy host data into the verified staging
allocation, but the reviewed stock command path has **no host-controlled branch
or live callback-table write**.  A direct, safe SSH-only execution test is not
available from the present interface.  This is a useful result: uploading a
stub to `C0FAC010` alone cannot make the i960 execute it.

The next viable execution route is a patched-boot image installed through a
separately validated programming and recovery path. The earlier exclusive
post-init loader intercepts stock startup after its early PCI setup. It is not
ready to flash.

Update: [STOCK-PRESERVING-HOOK.md](STOCK-PRESERVING-HOOK.md) now contains an
offline candidate for this patched-boot route. Its metadata hook installs one
returning PING command and resumes the normal firmware entry; exclusive DRAM
ownership and live recovery are still unverified.

## Evidence for the boundary

The board object was read live at `C0110780`; its upload callback at `+E4` is
`C004CED0`.  That handler obtains the staging pointer through `C004D230`, adds
the mailbox offset, and calls the DMA helper `C004C010` with control value 14.
It has no destination field from the host other than that staging-relative
offset.  The successful 16-byte upload at offset `0x80010` proves this route as
a data transfer only.

The central command dispatcher at `C001F7B0` chooses a firmware-owned handler
from the static table at `C001F804`.  Its asynchronous handlers store only
firmware addresses in each request's `+0x40` continuation slot.  The examined
maintenance gates dispatch through the board's fixed callbacks: `+D0` for
descriptor reads, `+D4` descriptor upload, `+D8/+DC` extended descriptor work,
`+E0/+E4` image transfer, `+E8` legacy unsupported image program and `+EC`
programming.  None accepts a host pointer as an i960 instruction address.

`C0016710`, the callback at board `+F4`, is also not an escape hatch.  It finds
the per-controller request/state object, initializes it through `C001F7B0`,
then tail-branches to its firmware-owned `+0x40` state handler.  The board
initialization sequence in the bootstrap at `FEFCB78C` writes this fixed address
to `+F4`.  The live pointer is not reachable through opcode 0x20 or 0x21.

The only reviewed callback that could write the lower ROM is `+EC` through
maintenance subcommand `2B/1`; it erases/programs flash and is explicitly out
of scope.  Opcode 0x22 does not provide a separate execution service on this
profile.  No command in this analysis was sent beyond the already documented
read and fixed scratch-upload sequence.

## Offline return-status stub

`loader/live-handoff/return_status.s` contains a 20-byte proof stub linked at
`C0FAC100`.  If entered as a normal request callback, it leaves `g0` intact,
stores status `0x017e` at request `+0x18`, then tail-branches to the stock
completion function `C004BAD0`.  Seeing that status through the normal mailbox
would prove execution and a clean return, without using an MMR marker.

The address is inside the allocator-derived extra block only after the exact
4.07-0-29 profile and allocator checks.  The previous experiment validated and
restored a separate 16-byte slot; this 20-byte binary has not been uploaded.
The CPU instruction-cache question is not
the present blocker: an instruction address that has never been fetched is a
cold I-cache line after DMA upload.  A patched-boot loader must nevertheless
perform its explicit `icctl 2` before jumping to a newly uploaded payload,
because it supports repeated payload replacement.

## Preconditions for a future execution test

1. Have a tested recovery route, or accept that a stalled card may need a
   power cycle.  Serial recovery is prepared but unverified.
2. Prove a mechanism that installs a callback pointer in controller RAM, or
   boot the existing post-init loader from a separately validated ROM image.
3. Validate the exact live runtime code, board object, staging pointer and
   allocation extent again before any write.
4. Upload the stub and read it back with paired transfers before installing the
   handoff.  Preserve and later restore every altered callback word.
5. Trigger exactly one normal completion and require observed status `0x017e`.
   A timeout or unknown completion keeps DMA mappings and evidence pinned; do
   not unbind or reset through the probe.

Until condition 2 is met, there is no further low-risk SSH action that advances
from RAM data transfer to CPU execution.  The most productive next work is
continued offline review of the bootable post-init loader and a physical serial
recovery setup.
