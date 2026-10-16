# AcceleRAID 160 late-loader PING route, offline only

2026-10-16. The prior [early PING candidate](../accele160-ping-handler-20261016/README.md)
wrote the `0x8f` dispatch entry immediately after stock setup. This revision
places the write at the loader's **common return**, after the loader's stock
descriptor pass. It is the preferred offline candidate. No firmware image was
exported, programmed or executed; neither card received a command in this
batch. The Linux host supplied the i960 assembler/linker only.

The boot descriptor selects copied-loader entry `c000c590`. Its normal path
expands the main ZIP image (`c000c634`), calls stock setup (`c000c638`), enters
the descriptor pass (`c000c650 → c000c780`), and returns at `c000c9cc`.
The [four-byte branch](late_ping_callsite.bin) changes that `ret` to
`b c000e1d8`. The [144-byte hook and PING](late_ping_handler.bin) sets
`c00234fc` to its own `c000e1ec` PING entry, then executes the displaced
`ret`. It leaves g0 untouched and clobbers g1. The hook no longer calls setup
twice.

After the loader returns, stock boot executes `dcctl 1,0,g1` at `feffc120`,
then branches through the main entry at `feffc124`. In Intel's
[i960 Jx Developer's Manual](https://datasheets.chipdb.org/Intel/80960/manuals/27248302.pdf),
`dcctl` operand 1 **enables** the D-cache; operand 2 invalidates it. The
[80303 datasheet](https://www.bitsavers.org/components/intel/i960/80303/273358-009_80303_IO_Processor_Data_Sheet_200206.pdf)
identifies its core as 80960JT. Thus that boot instruction does not invalidate
the freshly written table word. The table write is after the loader's own
descriptor initialization, but **main-entry initialization and computed
writes remain unproved**. The static audit checks the exact boot and loader
instructions and verifies no aligned absolute references to the erased cave;
it is not a whole-program control-flow or cache proof.

The PING body has the same strict 64-byte, zero-DMA admission rule as the early
candidate. A valid envelope branches to stock normal completion with internal
status zero. Any mismatch branches to stock unsupported. The nonce is checked
for nonzero but not returned or authenticated. No upload/call route is present.
[Raw i960 disassembly](late_ping_handler.dis) and
[branch disassembly](late_ping_callsite.dis) record the exact instructions. Both
linked ELF files had **no relocations**.

[`audit_late_ping.py`](../../../host/accele160/helper/audit_late_ping.py)
requires the exact paired stock image and exact reviewed binaries. Its
[receipt](receipt.json) reports an in-memory candidate SHA-256 of
`e708c1dadbc4813dd378e8ca8c6f0e929cc29064614b9f8a27210e5e2b23d3d0`,
**155 changed flash bytes**, unchanged decompressed runtime, a strict
changed-byte whitelist and passing known loader/trailer checksums. It does
not emit the candidate. The handler SHA-256 is
`dbbfa3c99bdc30895a811b4e8828d2edc38203eb2762170cb2304a549bd1bf45`.
Nine helper tests and eleven startup tests pass, including mutations of the
branch, handler, loader, runtime table, boot handoff and boot record.

Replay from the repository root:

```sh
python3 host/accele160/helper/audit_late_ping.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin \
  artifacts/current/accele160-late-ping-20261016/late_ping_handler.bin \
  artifacts/current/accele160-late-ping-20261016/late_ping_callsite.bin
python3 -m unittest discover -s host/accele160/helper -p 'test_*.py'
python3 -m unittest discover -s host/accele160/startup -p 'test_*.py'
```

Sources are [`late_ping_handler.S`](../../../host/accele160/helper/late_ping_handler.S)
and [`late_ping_callsite.S`](../../../host/accele160/helper/late_ping_callsite.S),
with adjacent linker scripts. Rebuild on the Linux toolchain host using
`i960-elf-as -AJX`, `i960-elf-ld -T`, and `i960-elf-objcopy -O binary`.

## Recovery boundary and next experiment

The stock boot block is separately located at flash `0xf0000..0xfffff` and
was not changed by the in-memory candidate. Its startup checks the main-image
descriptor/checksums. On a detected failure it enters a boot-block recovery
path whose dispatcher accepts IOCTL `1`, `0x2c`, `0x2d`, and `0x2e`; `0x2e`
reaches a programming handler. This is **not a proven recovery procedure**.
A valid-checksum patch that hangs later can loop before the boot block elects
recovery. The boot block's host/serial reachability, flashing format, and
rollback operation have not been tested on this card. A spare card preserves
experimentation capacity but does not restore a bricked one. No fault was
induced and no programming command was sent.

Before any live flash test, establish a board-specific means to enter and
leave recovery without deliberately corrupting the only bootable image, plus
a verified way to restore the accepted stock 1 MiB dump. The next useful
read-only target check is a guarded snapshot of the stock table after boot and
a disassembly audit of the main-entry initialization for computed writes to
`c00234fc`. Even those will not prove a modified image boots; a live test
would need explicit new-card BDF, readback, bounded PING, health checks and a
physical rollback plan.
