# AcceleRAID startup evidence and candidate execution probe

Status: offline startup verified and probe assembled. The later guarded transport
test uploaded these exact bytes and restored them, but **did not execute them**.
[Analysis and bounded live-test design](../../../docs/hardware/accele160-startup.md).
The existing full flash is reused; no duplicate full firmware binary is stored.

- `analysis.json`: mechanically decoded boot contract and checksum results.
- `boot-evidence.txt`: selected stock boot disassembly, absolute flash addresses.
- `runtime-entry.txt`: main entry disassembly; file offsets need `+0xc0010000`.
- `probe.bin`, `probe-raw.dis`, `relocations.txt`: candidate payload, decoded bytes
  and absence of relocations. `probe.dis` demonstrates the ELF symbol-boundary
  display issue, not an invalid instruction; raw disassembly is authoritative.
- `live-readonly-state.txt`: unchanged boot, old card unbound, new card identity,
  resources and completed retained selector-4 test allocation.
- `tests.txt`: nine offline tests. Result-record tests are synthetic, not live.

Reproduce from repository root:

```sh
python3 host/accele160/startup/analyze.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin
python3 -m unittest discover -s host/accele160/startup -p 'test_*.py'
```

Assemble in an isolated directory on the Linux build host, with `probe.S` and
`probe.ld` copied from `host/accele160/startup`:

```sh
/home/mit/i960/tools/bin/i960-elf-as -AJX -o probe.o probe.S
/home/mit/i960/tools/bin/i960-elf-ld -T probe.ld -o probe.elf probe.o
/home/mit/i960/tools/bin/i960-elf-objcopy -O binary probe.elf probe.bin
/home/mit/i960/tools/bin/i960-elf-objdump -D -b binary -m i960 probe.bin
/home/mit/i960/tools/bin/i960-elf-readelf -r probe.elf
```

Build workspace: `/home/mit/i960-accele160-startup-20261016`. No board operations
are part of this build. The repo already retains the matching binutils toolchain.
No reboot, driver unload, firmware write or old-card access was required.
The subsequent live receipt is in
[`../accele160-ram-route-20261016/`](../accele160-ram-route-20261016/README.md).
