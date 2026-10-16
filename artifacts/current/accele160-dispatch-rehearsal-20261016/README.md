# AcceleRAID 160 offline dispatcher wiring rehearsal

2026-10-16. This batch tests the **routing mechanics** against the accepted
paired stock 6.00-05 image. It did not create a flashable output file, program
either card, or run code on the controller. The old card was untouched; the
Linux PC was used only as an i960 toolchain host.

The stock reset chain enters the 24 KiB copied loader at `0xc000c590`. Its
`0xc000c634` call passes the compressed source and destination to the loader
routine before the original `0xc000c638: call 0xc000c6c0` setup call. The
[four-byte callsite](dispatch_callsite.bin)
instead calls `0xc000e1d8`, the first word of the loader's erased copied cave.
The [28-byte hook](dispatch_stub.bin) calls the original setup, then stores
`0xc000e1f0` into the expanded runtime's IOCTL `0x8f` table word at
`0xc00234fc`. That fallback branch goes directly to the stock unsupported
handler at `0xc0023790`. The adjacent `0x8e` entry at `0xc00234f8` is not
changed. Every request, including a candidate PING, would still be rejected.
This is a structural route rehearsal, **not an implemented helper**.

The GNU i960 binutils 2.27 build has no remaining ELF relocations; the exact
instructions are archived in [disassembly.txt](disassembly.txt). The source is
[`dispatch_stub.S`](../../../host/accele160/helper/dispatch_stub.S) and
[`dispatch_callsite.S`](../../../host/accele160/helper/dispatch_callsite.S), with
their adjacent linker scripts. Rebuild on the Linux toolchain host:

```sh
for name in dispatch_stub dispatch_callsite; do
  /home/mit/i960/tools/bin/i960-elf-as -AJX -o "$name.o" "$name.S"
  /home/mit/i960/tools/bin/i960-elf-ld -T "$name.ld" -o "$name.elf" "$name.o"
  /home/mit/i960/tools/bin/i960-elf-objcopy -O binary "$name.elf" "$name.bin"
  /home/mit/i960/tools/bin/i960-elf-readelf -r "$name.elf"
done
```

[`audit_dispatch_rehearsal.py`](../../../host/accele160/helper/audit_dispatch_rehearsal.py)
requires the exact accepted stock 1 MiB hash and exact reviewed machine code.
It checks the original call instruction, fully erased cave, stock `0x8e` and
`0x8f` table words, lack of aligned cave references, both known additive
checksums, unchanged decompressed runtime and a whitelist of changed flash
bytes. The [receipt](receipt.json) gives the in-memory candidate hash
`3f99d0cd1966d86498b11a680065366f9087c39ac5ce741ba1c60fa8f833fc18`,
**37 changed bytes** and passing known checksums. No candidate image is
exported by the tool. Three new mutation/structure tests and all eleven
existing startup tests pass. The source scanner finds no aligned absolute
loader or runtime reference to either `0xc00234f8` or `0xc00234fc`; this
does not exclude computed writes.

Replay from the repository root:

```sh
python3 host/accele160/helper/audit_dispatch_rehearsal.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin \
  artifacts/current/accele160-dispatch-rehearsal-20261016/dispatch_stub.bin \
  artifacts/current/accele160-dispatch-rehearsal-20261016/dispatch_callsite.bin
python3 -m unittest discover -s host/accele160/helper -p 'test_*.py'
python3 -m unittest discover -s host/accele160/startup -p 'test_*.py'
```

## Remaining gates

1. Prove the loader hook is reached on this board and that the `0x8f` table
   write survives later initialization. In particular, the runtime-table
   materialization and absence of later computed writes need independent
   target proof. Static layout and checksums do not
   prove boot behavior; the image has not been programmed. Preserve the
   board's recovery/rollback plan before a live flash experiment.
2. Trace the internal command object's bytes `+0x16..+0x1f` from the host
   mailbox, and design a response that binds the nonce to completion. The
   stock `0x8f` capture proves byte `+0x15` dispatch and status cleanup only.
3. Replace the fallback with a fully bounded PING handler, including strict
   rejection and no DMA, then validate its i960 machine code and control flow.
   The native C admission model is not installed firmware.
4. Establish owned code, stack and result storage, cache maintenance and a
   returning call before implementing an upload/execute operation. This
   routing rehearsal neither grants that ownership nor qualifies recovery.
