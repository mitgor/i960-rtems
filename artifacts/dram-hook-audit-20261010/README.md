# Fixed C0120000 read, 2026-10-10

`live/` contains the 15-command result log and paired binary captures from
the matching 4.07-0-29 card. `dram-hook-a5.bin` and `dram-hook-5a.bin` are
each 64 zero bytes, SHA-256
`f5a5fd42d16a20302798ef6ed309979b43003d2320d9f0e8ea9831a92759fb4b`.
The transaction log SHA-256 is
`d1a95c2c478dbf3a1dc5efb2a1ba46362be879ddb55350dd00d3e741bed57064`.

The exact Linux 6.8.0-138-generic probe build is archived as
`dac960dump.ko` (455,440 bytes, SHA-256
`2df02f601379274bc58be826831a447d1c0180630830147a0fe3d00f2979a9e4`).
Its `.c`, two headers and `Makefile` are copied here with it; development
sources remain in `host/dump/`. This module is tied to that kernel build.

Validate with:

```sh
python3 -B host/dump/validate_dram_hook.py artifacts/dram-hook-audit-20261010/live
```

The source is in `host/dump/`. This read established current contents only;
see [DRAM-HOOK-AUDIT.md](../../docs/loader/DRAM-HOOK-AUDIT.md) for the static analysis and
remaining ownership gap. No flash or custom code was run.
