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

## AcceleRAID 160 status (2026-10-16)

The AcceleRAID 160 (`1069:0050`, subsystem `1069:0054`) boots an audited
firmware patch and answers bounded zero-DMA PING and RAM-call operations. The
current image passed paired post-power-cycle full-flash reads. Its **fixed
80-byte payload ran and returned twice**, with full-page restoration and a
post-call flash audit. See the [exact acceptance](../artifacts/current/accele160-ramprobe-20261016/README.md)
and [memory map](hardware/accele160-memory-map.md).

Therefore the existing RTEMS and Doom images cannot yet be run on this board.
They are coupled to the DAC960PG (`1069:0010`) firmware loader, PCI transport,
owned DRAM arena and interrupt/timer implementation. Their i960 application code
is reusable, but the board support and host module are not interchangeable.

The RAM-call handler validates the exact payload, performs card-side cache
maintenance, calls normally, and checks the nonce/result report. Its erased
loader-cave page is a self-restoring test site. It does not provide a chunked
upload protocol or an RTEMS-sized owned arena. Four high-DRAM samples were
stable zeros; that observation does not establish ownership.
Keep the exact-card selection, DMA guards, ownership checks, timeouts and full
before/after audits. Next, reserve an arena through a decoded stock allocator
or an explicit exclusive firmware handoff, implement chunked upload with
whole-image validation, and qualify a minimal RTEMS task/clock/STOP test.
Then adapt the host network transport and web service before Doom startup,
WAD loading and framebuffer delivery. Do not feed a DAC960PG RTEMS/Doom image
to the AcceleRAID transport as a substitute for these gates.
