# Stock FLASHIMAGE status 2 on Slot 5 card 10112504772

On 2026-11-20 the stock AcceleRAID 160 in Slot 5 completed STOREIMAGE
and an independent full staged READIMAGE. The staged bytes matched the
per-card candidate exactly. One FLASHIMAGE (IOCTL `0x2e`, selector 9,
zero DMA) completed with status 2 and residual 0 in less than one kernel
millisecond. After a cold boot, two full READIMAGE captures matched the
original stock flash byte for byte (`0ca0f4b6...6e943`). The card boots
Linux and its current stock descriptor reports `state=0 status=0 residual=0`.

## What this narrows down

The pinned `flash_image.ko` had already issued the same mailbox command
successfully on two other cards: the earlier first spare (35.1 seconds,
status 0) and Slot 5 card 10112502260 (35.7 seconds, status 0). The
rejected card has the same executable stock runtime, boot block and flash
layout. Its stock image differs from the first spare's stock image in only
four serial-number bytes. Consequently, a generic mailbox-layout error or
candidate-packing error does not explain the observed difference by itself.

## Correction, 2026-11-21: host status 2 does not locate the failure

An earlier version of this note read "status 2, not 22" as evidence that the
command was rejected before the erase/program writer. That inference is wrong.
The static trace below is pinned by
`host/accele160/flash/audit_flash_status.py`, which passes on this card's
stock dump. It is disassembly only; nothing here was observed on hardware.

- **Every failure reads as 2.** The completion routine at `0xc004e940` loads
  the internal status word from command offset `0x56`. If it is non-zero and
  the mailbox has `no_autosense` set, it stores plain 2. Otherwise it copies up
  to 14 sense bytes to the host and stores `0x0e02`, which the host also sees
  as status 2. Internal 22 (writer failed), `0x105` (no staged image) and
  `0x104` (unsupported) are indistinguishable in the status byte.
- **The internal code is in the sense data.** The builder at `0xc0069330`
  writes sense byte 12 = `0x80 | code >> 8` and byte 13 = `code & 0xff`:
  `80/16` for a writer failure, `81/05` for no staged image. The pinned
  `flash_image.ko` set `no_autosense`, so the 2026-11-20 attempt discarded it.
- **The traced handler does not inspect the staged image.** IOCTL `0x2e` dispatches through
  `0xc0023694` to the continuation `0xc0050750`, which requeues the command
  while the controller is not quiescent and otherwise calls board method
  `0xf8`, the handler at `0xc00509f0`. That handler tests only that the
  staged-image pointer `0xc0494cf0` is non-null, then calls the writer at
  `0xc0055410`. No checksum, header or descriptor check appears in this
  handler; a check elsewhere in the command path has not been ruled out.
- **The staged pointer was set.** It is cleared in one place, the free routine
  at `0xc0051040`, called only by READIMAGE when that read allocated its own
  buffer, by FLASHIMAGE after the writer, and by the `WrongFl` method. A
  STOREIMAGE followed by a READIMAGE that returned the candidate leaves it
  set, assuming no untraced command changed it before FLASHIMAGE.
- **If the handler reached the writer, its failure path fits the result.** The
  writer attempts to erase all sixteen 64 KiB
  blocks (the boot block too after a selector-9 STOREIMAGE), ORs the results
  without stopping early, and programs only if every erase succeeded.
- **How an erase fails.** `0xc0055240` issues `FF 50 20 D0`, polls status with
  no timeout until bit 7 is set, then fails the block if status bit 3 (VPP
  low) or bit 4 is set, or if the block is not blank afterward. A locked block
  takes the last route. A prompt status failure could leave data intact.

This route fits the observations: completion inside one jiffy, and a cold read
with no changed byte. The readback proves no persistent data change; it does
not establish whether erase commands reached the chip. If the erase poll ran,
block 0 begins with `0x50` in array mode (bit 7 clear), so an ineffective write
strobe would likely leave that unbounded poll spinning. This conditional clue
does not prove the live path entered the poll.

If sense data later confirms internal writer status 22, candidates include VPP
not reaching the chip during the gated window (board control bit 3 at
`0xe0500000`, a jumper, or a failed part), lock bits or the master lock set on
this chip, or a different flash part. The scheduler that invokes the `0x2e`
continuation was not traced, so rejection outside this handler remains open.

Two implications for the experimental native writer. It uses the same gate
and chip, so native APPLY may meet the same condition on this card. Also,
`flash_backend.c` reads `0xe0500000` back, whereas stock never reads that
register and keeps a shadow at board context `+0x50`; if the latch is
write-only, the native gate check is unreliable.

Card 10112504772's descriptor contains board revision `A` and a count
field of 1; the previously successful card 10112502260 has `B` and 5.
The first spare, which did flash successfully, also has `A` and 1. Thus
neither descriptor difference alone is an established cause.

## Next discriminating checks

A new [volatile stock-RAM route](../../artifacts/current/accele160-stock-ram-route-20261120/README.md)
ran a 28-byte marker under IOCTL `0x8f` without flashing. The host restored
the dispatch word and loader page, and a full flash read remained stock.
After a cold boot on 2026-11-21, two fresh full READIMAGE captures matched the
stock SHA-256 `0ca0f4b6...6e943`. The prepared Intel ID/lock payload then ran
once through the volatile RAM route. It reported Intel manufacturer `0x89`,
device `0xa6` (28F008S3), master lock `0`, and a zero lock mask for the six
mutable blocks at flash offsets `0x40000..0xbffff`. The RAM dispatch word and
loader page were restored; a subsequent full READIMAGE still matched stock.
The result does not report lock state for the other ten blocks or measure VPP.
The full local evidence is in
`artifacts/current/accele160-flash-id-live-20261121/` (local, untracked).

The auto-sense `flash_image.c` also compiled against the remote's
`6.8.0-138-generic` headers. The resulting module's SHA-256 is
`1ba32738d7d055349db23d4bb17257364cd279f3ed048800f0b4c7c7b6d59bd3`.
It was not loaded or used for FLASHIMAGE, and its hash is not pinned in
`flash_native_spare.py`.

1. With power off, compare JP3 position, flash chip part number, and
   visible rework/damage on card 10112504772 against the known successful
   first spare. Record photos before changing a jumper. The AcceleRAID 160
   installation guide labels JP3 "Maintenance Mode" but does not describe
   it as a flash write-protect switch.
2. If the board can be instrumented, measure the chip's VPP during a
   controlled stock flash attempt. The ID/lock reads do not establish VPP or
   that the PCI write path works. A later RAM-only probe could also read the
   lock state at the remaining ten block offsets after a separate cold boot,
   once the relevant identifier-mode addresses are verified.
3. Review the compiled auto-sense `flash_image.ko`, then pin its new SHA-256
   in `flash_native_spare.py` only as part of a reviewed later flash attempt.
   Its firmware auto-sense copy for this IOCTL is untested on hardware.
4. Rebuild a card-specific candidate only after a measured cause or changed
   condition. Require new same-boot full stock reads, STOREIMAGE, independent
   staged readback, and preflight. A rejected or pending command gets no
   same-boot retry. Cold readback is required after any accepted flash.

`flash_native_spare.py` now quarantines this exact stock image for an actual
FLASHIMAGE request. `--preflight-only` remains available. Remove or replace
the quarantine only as part of a reviewed fix supported by new evidence.

Evidence: `artifacts/current/accele160-live-stock-20261120-48e3bca2/`,
`artifacts/current/accele160-post-rejected-flash-20261120-1648696d/`,
`artifacts/current/accele160-spare-rom-20261025/flash/`, and
`artifacts/current/accele160-pci-release-live-20261119/slot5-flash/`.
