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
