# Supporting another i960 card

The reusable pieces are the compiler, integer application cores, native oracles,
RTEMS concepts and host display/network frontends. The current firmware loader,
PCI transport and RAM map are specific to the accepted DAC960PG profile.
No second card is qualified by this guide.

| Establish on the new board | Why it matters | Reusable reference |
| --- | --- | --- |
| Exact CPU variant, endian mode and ABI | i960 variants and instruction sets differ | [toolchain](../artifacts/toolchain-20261011/README.md), [runtime](../loader/runtime/README.md) |
| PCI IDs, BARs, mailbox and DMA addressing | Host transport must reach the right registers and memory | [firmware protocol](firmware/FIRMWARE-PROTOCOL.md) |
| Flash geometry, reset/IBR and original image | Existing patch offsets are not portable | [ROM inventory](../artifacts/ROM-INVENTORY.md), [firmware](../subprojects/firmware/README.md) |
| Executable RAM, aliases and cache rules | The failed internal-data-RAM path cannot execute code | [postinit](loader/POSTINIT-LOADER.md), [DRAM analysis](loader/DRAM-ANALYSIS.md) |
| Allocation/lifetime and stock coexistence | A zero-filled address is not a RAM ownership grant | [research](research.md), [Doom memory contract](../game/doom/RAM-CONTRACT.md) |
| Clock, IRQ vector/context and STOP | Board-specific timer/vector assumptions cannot be copied blindly | [interrupt implementation](../rtems/interrupt/README.md) |
| Recovery and independent image preservation | A spare similar card is not a proven recovery route | [recovery](firmware/BOOT-RECOVERY.md) |

Begin with read-only identification and a validated ROM archive. Then prove a
bounded returning function and restoration, followed by buffer I/O. Reuse Tetris
or the small loader demo as the first execution test. Qualify RTEMS task/interrupt
ownership and the memory arena before loading Doom. Keep board configuration and
expected preimages explicit; do not weaken validation to make another card pass.

A future board abstraction should separate discovery/profile, mailbox operations,
RAM ownership/cache maintenance, timer/interrupt implementation and application
ABI. Extract it from two measured implementations rather than assuming the first
board's fixed addresses are a universal i960 API.

## AcceleRAID 160 status (2026-10-17)

The AcceleRAID 160 (`1069:0050`, subsystem `1069:0054`) is now a measured
second target, with its old DAC960PG neighbor kept unbound. The [stock 1 MiB
flash](../artifacts/current/accele160-guarded-20261016/README.md) is archived.
The persistent helper uses stock allocation to retain a fixed 512 KiB grant
at `c0710000`, copies validated pages from the host-addressable final odd
page into any sampled owned payload page, and computes a bounded contiguous
image digest. It has passed card tests for indexes 0, 1 and 126, two pages
under one grant, bad-hash and out-of-range rejection, an 8 KiB whole-image
FNV, and negative digest controls. Each accepted run restored the staging
page, loader controls and all allocator owner/count words; full guarded flash
reads stayed identical. See [page copy](../artifacts/current/accele160-pagecopy-20261016/README.md),
[digest](../artifacts/current/accele160-digest-20261017/README.md) and the
[live memory map](hardware/accele160-memory-map.md).

An exact-leaf [owned-RAM execution proof](../artifacts/current/accele160-ownedexec-20261017/README.md)
now passes: the already accepted 80-byte leaf ran normally from `c0710000`
after whole-image digest, exact-code check and I-cache invalidate, then
repeated in a fresh grant. Bad hash and altered code rejected before call.

The DAC960PG RTEMS and Doom binaries still cannot be run directly on this
board. Their host transport, timer and interrupt wiring, memory map, lifecycle
and Doom's 8 MiB arena are board-specific. An RTEMS-sized [77-page transfer](../artifacts/current/accele160-bulkupload-20261017/README.md)
now passes with full digest and restoration; this does not run the old image.
Port a newly linked minimal RTEMS task/clock/STOP image with an explicit
AcceleRAID memory manifest, then the host-backed network/web profile. Doom needs a separate, measured 8 MiB ownership design. FNV is a
transfer-error check, not a cryptographic authenticity proof. Keep exact-card
selection, full flash audits, owner checks, bounded timeouts and restoration.
