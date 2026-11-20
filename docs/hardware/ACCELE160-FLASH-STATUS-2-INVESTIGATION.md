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

The accepted stock runtime's FLASHIMAGE handler at `0xc00509f0` checks
for a staged-image pointer and calls the erase/program routine at
`0xc0055410`. That handler stores status `0x105` when the pointer is absent
and status 22 if the writer reports failure. Status 2 is compatible with
rejection before that writer, but the exact path is not proven: the
firmware's dispatch tables and live branch were not traced. Flash lock,
write-enable voltage, JP3, and hardware fault remain unmeasured.

Card 10112504772's descriptor contains board revision `A` and a count
field of 1; the previously successful card 10112502260 has `B` and 5.
The first spare, which did flash successfully, also has `A` and 1. Thus
neither descriptor difference alone is an established cause.

## Next discriminating checks

A new [volatile stock-RAM route](../../artifacts/current/accele160-stock-ram-route-20261120/README.md)
ran a 28-byte marker under IOCTL `0x8f` without flashing. The host restored
the dispatch word and loader page, and a full flash read remained stock.
Because i960 cache visibility after host restoration is not established,
the prepared Intel ID/lock payload requires a cold power cycle before its
first call. That read-only payload is now the next executable check.

1. With power off, compare JP3 position, flash chip part number, and
   visible rework/damage on card 10112504772 against the known successful
   first spare. Record photos before changing a jumper. The AcceleRAID 160
   installation guide labels JP3 "Maintenance Mode" but does not describe
   it as a flash write-protect switch.
2. If the board can be instrumented, read the Intel flash ID and block-lock
   bits, then measure the chip's VPP during a controlled stock flash attempt.
   ID/lock reads do not establish VPP or that the PCI write path works.
3. Trace the stock command dispatcher or capture its live state to identify
   which check returns status 2. Do not infer this from the zero-millisecond
   display; the module measures only whole jiffies.
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
