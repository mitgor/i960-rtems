# AcceleRAID 160 startup and bounded execution design

The later [stock recovery audit](../../artifacts/current/accele160-recovery-audit-20261016/README.md)
traces the serial `S` boot path and the separate destructive restore command.
It does not establish a usable UART or a successful restoration on this board;
the offline PING firmware remains unflashed.

2026-10-16. This analysis uses the paired stock 6.00-05 flash, not the vendor
7.x reference image. It establishes a boot contract and supplies a compiled
probe; **custom code has not executed on the new card**. A later guarded test
proved host-to-local-RAM upload, exact readback and byte-for-byte restoration,
but deliberately stopped before execution because no cache-safe call handoff is
yet proven. No flash write, controller reset, driver change or reboot was used.
Old DAC960PG `0000:37:04.1` remained unbound and untouched.

The subsequent [stock `0x8f` test](../../artifacts/current/accele160-ping-contract-20261016/README.md)
submitted a zero-DMA diagnostic request on `37:09.1` and observed status `2`
with zero residual and exact mailbox capture. It does not change this
execution conclusion; the native PING validator is an offline model only.

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
   1,0,g1` (enable D-cache on the integrated 80960JT), then branches through
   g0 at `0xfeffc124`. This is a startup handoff,
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
| `0xc0001000..0xc0001fff` | Upper half of the live inbound BAR; reset/recovery references the page, while it is all zero in the running image and has no absolute main-runtime reference | Suitable only for a self-restoring bounded experiment; still not firmware-owned application RAM |
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
| host BAR0 `0xee002000..0xee003fff` | 80303 primary inbound ATU: first 4 KiB Messaging Unit, second 4 KiB translated local memory | A real movable 4 KiB aperture, not a 16 MiB RAM BAR |

Controller information reports 16 MiB RAM and 8 MiB cache. A contiguous
`0xc0000000..0xc1000000` RAM extent is a hypothesis, not a tested ownership map.
The bridge identifies as `8086:2962`; do not silently substitute the old i960RP
register definitions or assert an exact core variant from clock alone.

## Proven inbound RAM aperture

The Intel 80303 Developer's Manual sections 15.2.1.1 and 15.7 define the live
configuration exactly. PCI function `37:09.1` reports:

| Register | PCI offset | Live value | Meaning |
| --- | --- | --- | --- |
| PIABAR | `0x10` | `0xee002008` | 8 KiB prefetchable host BAR |
| PIALR | `0x40` | `0xffffe000` | 8 KiB inbound mask |
| PIATVR | `0x44` | `0xc0000000` | local translation base |

The first 4 KiB is reserved for the Messaging Unit. BAR offsets
`0x1000..0x1fff` therefore translate to local `0xc0001000..0xc0001fff`.
Read-only remapping of PIATVR also captured arbitrary 8 KiB-aligned local pages;
every test restored PIATVR to `0xc0000000` under an exit trap. This resolved the
previous ambiguity around BAR0 without changing its size or the Messaging Unit.

A live guarded upload used BAR offset `0x1e00` / local `0xc0001e00`. The target
256 bytes were checked as zero before the first store. The replacement contained
64-byte guards, the accepted 80-byte probe and a distinct marker. Replacement
readback passed, all original bytes were restored, and complete before/after
4 KiB snapshots both have SHA-256
`ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7`.
This proves a bounded **upload/readback route**, not ownership for a resident
payload.

## Entry-route investigation

The boot recovery dispatcher accepts IOCTL 1, 0x2c, 0x2d and 0x2e in the traced
path (`0xfeff0b40`). The 0x2c/0x2d path shares the staging-transfer handler at
`0xfeff0fd0`; direction is selected at `0xfeff1064`. The 0x2e path calls a
separate routine from `0xfeff1080` with staging base `0xc0300000`—treat it as a
potential programming operation, not an execute request. No generic execute
primitive was found in this dispatcher. Recovery entry itself remains unproven
over SSH on this new board. Do not induce recovery by corrupting flash.

Linux v6.8 `myrs.h` names command 0x01 MEMCOPY, but the stock dispatcher sends
it to runtime `0xc0023030`, which resolves a controller/channel/target and starts
the ordinary SCSI transfer state machine. It is not arbitrary local-memory copy.
IOCTL `0x2c` and `0x2d` dispatch through callbacks `0xc0050690` and
`0xc0050630`; these are StoreImage and ReadImage paths using allocator-owned
temporary state. IOCTL `0x2e` reaches a separate programming path and remains
prohibited. None supplies a persistent RAM upload/call contract.

IOCTL `0x8e` eventually dispatches through function-table slot `+0xfc` (live
value `0xc0023910`) and appears attractive as a temporary call hook, but its
unmodified operation is `SET_MEM_MBOX`. The slot lives in cacheable RAM. The
80303 manual sections 4.3.5 and 4.4.6 explicitly state that external writes do
not snoop the instruction or data caches. The stock reset code enables caching
for `0xc0000000..0xc05fffff`, covering the dispatcher and callback table. A
host-side patch could therefore execute the stale, destructive original path.
That fails the bounded-call precondition and was not attempted.

Priority for the next investigation:

The subsequent [stock debug-interface trace](../../artifacts/current/accele160-debug-interface-20261016/README.md)
found that the live console table selects fixed-input/no-output stubs after
the loader's UART presence probe failed. Its `e` command is a D-cache
invalidate, while `u` opens memory diagnostics, not a safe upload/call route.
Serial wiring alone will not activate the current running firmware console.

1. Continue tracing stock host-command callbacks for a **proven** D-cache and
   I-cache maintenance sequence with normal return. The [cache-gate audit](../../artifacts/current/accele160-cache-gate-20261016/README.md)
   found a debug-menu D-cache invalidation and transfer/memory-test sites, but
   no accepted host-command path. Its only verified runtime `sysctl` uses
   `0x300`, Intel's reinitialize message.
2. Do not post a synthetic software interrupt by writing pending bits through
   PCI. The 80303's internal software-priority state needs a core-side `sysctl`
   check, and vector caching can hide a host-written handler. A doorbell uses
   existing firmware-owned hardware-interrupt routing. A software-interrupt
   route needs a verified core-side trigger and complete return/restoration ABI.
3. If stock firmware offers neither path, build a recoverable firmware-resident
   helper with an authenticated upload/call/cache-maintenance IOCTL, then
   validate it on the spare new card. That is a separate firmware patch
   milestone; this RAM-only test did not justify programming a guessed hook.

The [subsequent helper-site audit](../../artifacts/current/accele160-helper-site-20261016/README.md)
identifies unused diagnostic subcommand `0x8f` and 7,720 erased bytes in the
loader copy. An in-memory, dormant probe insertion passes the known loader and
trailer checksums without changing the compressed runtime. Neither site is
proven safe for active execution, and the `0x8f` table is inside the compressed
runtime. The command ABI, ownership, table patch timing and full vendor-image
checks remain open before any flash write.

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
   64-byte guards on both sides. The successful self-restoring `0xc0001e00`
   round trip proves transport only and is not sufficient ownership for this
   step. Keep code, result and stack away from firmware state.
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

See [startup evidence](../../artifacts/current/accele160-startup-20261016/README.md)
and [RAM-route evidence](../../artifacts/current/accele160-ram-route-20261016/README.md)
for commands, exact compiled bytes, selected stock disassembly and receipts.
Nine offline tests pass, including trailer/loader/reset corruption, descriptor
bounds, stale nonce and guard failures. The live upload/readback/restoration test
passed without reboot; PIATVR and the full aperture were restored, SSH remained
healthy, and the old card stayed unbound. The remaining blocker is specifically
a cache-safe, normally returning invocation route. Treating transport as
execution would risk running the stale `SET_MEM_MBOX` handler, so the probe was
not called.
