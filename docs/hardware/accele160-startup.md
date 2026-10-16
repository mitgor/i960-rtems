# AcceleRAID 160 startup and bounded execution design

2026-10-16. This analysis uses the paired stock 6.00-05 flash, not the vendor
7.x reference image. It establishes a boot contract and supplies a compiled
probe; **custom code has not executed on the new card**. No flash or controller
RAM writes, resets, driver changes or reboot were performed in this stage.
Old DAC960PG `0000:37:04.1` remained unbound and untouched.

## Verified startup chain

The offline decoder checks descriptor bounds, both loader/trailer additive
checksums, the initial boot record checksum and the decompressed runtime CRC.
All pass on the accepted stock dump.

1. The initial boot record at flash offset `0xfff30` names reset entry
   `0xfeffc000` and PRCB `0xfeffdd20`.
2. Reset starts with frame pointer `0x80`, stack pointer `0xc0`, and zero g14.
   It initializes hardware, checks serial/board inputs, and moves the frame to
   `0xc0002000`, stack `0xc0002040`, before calling the image loader.
3. Boot code at `0xfeffc8c0` scans descriptor `0xfefe0000` for selector 2.
   Main image occupies flash offsets `0x40000..0xbffff`. Its trailer begins at
   `0xbff60`; the sum of the first 31 little-endian words equals word 31.
4. Trailer fields specify a 24 KiB loader at flash offset `0x41000`, copied to
   `0xc000a000..0xc000ffff`. Its additive checksum also passes. The loader entry
   is `0xc000c590`.
5. Boot calls that entry with g0 = compressed image address `0xfef47000` and
   g1 = destination `0xc0010000`. ZIP1 expands to 685996 bytes, ending at
   `0xc00b77ac` exclusive; CRC32 `d93addd1` passes.
6. Boot obtains the main entry `0xc004cf70` from the trailer, executes `dcctl
   1,0,g1`, then branches through g0 at `0xfeffc124`. This is a startup handoff,
   **not a callable application entry with a return contract**.

The startup program uses both an uncompressed loader below `0xc0010000` and
compressed main code above it. Disassembling the expanded image at VMA zero
produces apparent negative call targets when calls reach the lower loader; those
are not proof of corrupt code. Add `0xc0010000` to runtime disassembly offsets.

## Memory map and confidence

| Address/range | Evidence and use | Ownership implications |
| --- | --- | --- |
| `0xc0000000` | RAM base used by boot tests/initialization | Occupied firmware memory; not available scratch |
| `0xc0000800` | Boot recovery fault table initialization | Do not overwrite |
| `0xc0001000` | Boot recovery structures | Do not overwrite |
| `0xc0002000` / `0xc0002040` | Boot frame / stack | A boot address is not a safe live stack |
| `0xc000a000..0xc0010000` | Verified 24 KiB loader destination | Includes callable support used by runtime |
| `0xc0010000..0xc00b77ac` | Verified expanded main image | Code/data; do not overwrite |
| `0xc00c027c`, `0xc00c3690` | Main entry stores outside expanded file | Shows file end is not end of firmware RAM use |
| `0xc04016a0`, `0xc043bfc4`, `0xc048e6f0`, `0xc04ad650` | Main entry absolute data references | Firmware state reaches beyond 4 MiB; no free-arena inference |
| `0xc0300000..0xc0400000` | Boot recovery copies full flash here | Recovery staging only; not established live scratch |
| `0xfef00000..0xff000000` | 1 MiB flash mapping | Boot block at `0xfeff0000`; no writes |
| `0xe0600000`, `+5` | Boot serial data/status access | Do not poll/write as part of this proof |
| `0x1310`, `0x1320`, `0x1324` | Recovery mailbox/doorbell accesses | Local register addresses, not Linux physical addresses |
| `0xff008100` and nearby | Reset configuration stores | Register names/semantics need primary-manual confirmation |
| host BAR0 `0xee002000..0xee003fff` | Read-only Linux resource snapshot | Only 8 KiB; not an exposed 16 MiB RAM BAR |

Controller information reports 16 MiB RAM and 8 MiB cache. A contiguous
`0xc0000000..0xc1000000` RAM extent is a hypothesis, not a tested ownership map.
The bridge identifies as `8086:2962`; do not silently substitute the old i960RP
register definitions or assert an exact core variant from clock alone.

## Entry-route investigation

The boot recovery dispatcher accepts IOCTL 1, 0x2c, 0x2d and 0x2e in the traced
path (`0xfeff0b40`). The 0x2c/0x2d path shares the staging-transfer handler at
`0xfeff0fd0`; direction is selected at `0xfeff1064`. The 0x2e path calls a
separate routine from `0xfeff1080` with staging base `0xc0300000`—treat it as a
potential programming operation, not an execute request. No generic execute
primitive was found in this dispatcher. Recovery entry itself remains unproven
over SSH on this new board. Do not induce recovery by corrupting flash.

Linux v6.8 `myrs.h` names command 0x01 MEMCOPY but supplies no demonstrated
controller-RAM execution contract. A command name is insufficient evidence for
using arbitrary source/destination addresses. The running firmware's READIMAGE
path only establishes flash-to-host transfer, not arbitrary local RAM access.

Priority for the next investigation:

1. Trace running-firmware opcode 0x01 and image-upload handlers end to end,
   including translation, length checks, allocation ownership and completion.
   Prefer a RAM-only, firmware-owned staging allocation and a verified callback.
2. If that yields no bounded route, decode the new bridge/ATU registers and
   ownership from a primary manual plus read-only current configuration. Design
   a new-card-only window mapping; do not probe by blind register writes or
   interpret the existing BAR as RAM.
3. Only after upload/readback and callback return are proven, execute the probe.
   A firmware patch is a later option if neither route exists; this analysis
   does not justify programming a guessed hook.

## Concrete bounded probe

Source: `host/accele160/startup/probe.S`; linked at zero, position-independent,
no relocations, assembled with binutils 2.27 `-AJX`. This is an ISA build check,
not proof of the physical core or callback ABI. The executable body is 72 bytes;
the binary includes alignment padding. ELF objdump truncates the instruction
immediately before an internal symbol; raw-binary disassembly decodes it fully.

Required caller contract: ordinary i960 CALL/CALLX with a valid firmware-owned
frame/stack; g0 points to an aligned, owned 16-byte **local RAM** result, g1 is a
fresh 32-bit nonce. Preserve any additional state required by the chosen hook.
The probe preserves g1..g14, clobbers arithmetic condition codes, and returns
zero in g0. Local-register changes use the normal call frame. It makes no calls,
performs no MMIO/DMA/cache/interrupt operations, and loops exactly 32 times.

Result words:

| Offset | Expected |
| --- | --- |
| 0 | `0x444f4e45`, completion marker written last |
| 4 | nonce |
| 8 | sum 0 through 31 = 496 |
| 12 | nonce XOR `0x96016001` |

A last-written marker alone does not establish DMA/cache coherence or return.
The future harness must enforce all of these acceptance steps:

1. Global card lock, explicit BDF and exact identity, no disks, old card unbound,
   no pending command. The completed retained selector-4 allocation must stay
   pinned or be cleared by an orderly reboot before ownership changes.
2. Obtain a proven-owned 256-byte code slot and separate 16-byte result with
   64-byte guards on both sides. No hard-coded scratch address until allocation
   ownership is proven. Keep code, result and stack away from firmware state.
3. Upload once; read back the entire code slot and guard regions, compare bytes.
   Establish instruction visibility using the verified new-core cache protocol.
4. Invoke once with a fresh nonce. No background workload, runtime installation,
   DMA engine reprogramming or interrupt changes in the probe.
5. Host observation deadline 1 second; this is **not** a guarantee the card can
   be preempted. On timeout retain resources and stop further commands; collect
   host state and use authorized reboot/power recovery if required.
6. Require normal command/callback return plus exact result and guards. Then
   require a normal controller-info command and unchanged host/card identity.
   A marker without return is a failure. Keep all transfer/ownership audits.
7. Repeat once with a different nonce, compare both records, then release only
   after proven quiescence. No automatic retry after an uncertain completion.

`verify_result.py` validates the future guarded result capture offline. Its tests
use synthetic records and do not imply a live success.

## Reproduction and outcome

See [evidence](../../artifacts/current/accele160-startup-20261016/README.md) for
commands, exact compiled bytes, selected stock disassembly and test receipts.
Nine offline tests pass, including trailer/loader/reset corruption, descriptor
bounds, stale nonce and guard failures. Live activity was limited to identity,
PCI configuration/resource and retained-command status reads, plus compilation
on the host. SSH remained healthy and the old card stayed unbound. No reboot was
needed. The immediate missing piece is a verified upload/call route, not a larger
payload or an assumed free RAM address.
