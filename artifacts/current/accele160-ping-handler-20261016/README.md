# AcceleRAID 160 bounded PING: offline image audit

The [late-loader variant](../accele160-late-ping-20261016/README.md)
supersedes this placement for future offline work: it installs the table entry
after the loader's descriptor pass. This record remains reproducible evidence
of the earlier candidate.

2026-10-16. This is an **unflashed, unexecuted** successor to the
[fallback-only routing rehearsal](../accele160-dispatch-rehearsal-20261016/README.md).
It uses the exact accepted 6.00-05 stock image. No command was sent to either
card during this batch; Linux at `192.168.2.75` supplied the i960 toolchain
only. The old DAC960PG `0000:37:04.1` was untouched.

## Command and completion evidence

The preserved Linux v6.8 `myrs.c`/`myrs.h` are GPL-2.0 sources, with their
upstream SPDX headers intact. Their SHA-256 values are
`22df649eaea262c4baa149aa803ea395b89b629395445d4e09014e823a8a0aa2`
and `4e6b8d12cee6a289c2deab6d2e57d44b7fbe902dc5cee59c2a44385d729b8924`.
`DAC960_GEM_write_cmd_mbox` (`myrs.c:2479`) copies words 1–15, issues a write
barrier, then writes word 0 and issues another barrier. GEM is the PCI ID path
selected for this board (`myrs.c:3110`). Thus the 64-byte host command is
published in order, including the proposed signature and nonce at bytes 24–31.

In the accepted stock firmware, `c004fa7c` passes the host mailbox pointer
and length four quads to `c0050480`. Its `ldq/stq` loop copies **all 64 bytes**
into a command object. `c004fa88` then clears host ring word 0;
`c004facc → c004fd50 → c004e380` queues the same object. The IOCTL dispatcher
at `c00232a8` reads its subcommand from object byte `+0x15`; adjacent stock
code at `c0022b00` also reads byte `+0x16`. This supports the raw-mailbox
offsets used by the candidate. It remains a *static* path analysis; live
execution of the modified image is unproved.

Stock initializes internal status `+0x56` and residual accounting `+0x2f0`
to zero at `c00229d0`. Unsupported `0x8f` sets internal status `0x104` at
`c0023790`, then enters normal completion. The live stock command returned
host status **2**, residual **0**. The zero-status path at `c004e940` continues
to completion without error processing. The completion packer at
`c004e7dc..c004e7fc` emits command ID, status and residual to the 8-byte
mailbox described by `struct myrs_stat_mbox` (`myrs.h:863`); the GEM interrupt
handler copies these fields to the host command (`myrs.c:2580`). This predicts
status 0 and residual 0 for an accepted zero-DMA PING. The nonce is **checked
for nonzero only**: it is neither echoed nor authenticated by this candidate.
The status prediction needs live confirmation.

## Bounded handler and receipt

[`ping_handler.S`](../../../host/accele160/helper/ping_handler.S) assembles to
the exact [148-byte binary](ping_handler.bin) at copied-loader cave
`c000e1d8`. Its first 24 bytes call original setup and change only the
expanded `0x8f` table entry to `c000e1f0`; the existing `0x8e` entry is left
alone. It reads only 64 bytes from the copied request object, requires the
zero-DMA/version-1/PING envelope, `I960` signature and nonzero nonce, clears
internal status, and branches to stock normal completion. Any mismatch
branches to stock unsupported. It allocates nothing, accesses no DMA/MMIO
register and has no open-ended loop. The [disassembly](disassembly.txt) is from
the raw binary; the i960 ELF disassembler misreports the two absolute `lda`
operands. The ELF had no remaining relocations.

[`audit_ping_candidate.py`](../../../host/accele160/helper/audit_ping_candidate.py)
requires the exact stock image, reviewed binary SHA-256
`0ea35c1381dd17938cfc42b112a353aad6cb5299036e17c75b9e586d463f0e44`,
and reviewed 4-byte callsite. It checks the erased cave and lack of aligned
stock references, untouched stock `0x8e`/`0x8f` words, assembly anchors,
unchanged compressed/decompressed runtime, a changed-byte whitelist and both
known additive checksums. It constructs the candidate **only in memory** and
exports a [receipt](receipt.json), never a flashable image. The candidate hash
is `6d18c80c46eb9cd8d2c96470da19c82e0d1e6ca8999a598cfb10675c25ea3650`;
157 flash bytes differ, including checksum fields. These are structural
properties, not boot or recovery qualification.

Reproduce from the repository root:

```sh
python3 host/accele160/helper/audit_ping_candidate.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin \
  artifacts/current/accele160-ping-handler-20261016/ping_handler.bin \
  artifacts/current/accele160-dispatch-rehearsal-20261016/dispatch_callsite.bin
python3 -m unittest discover -s host/accele160/helper -p 'test_*.py'
python3 -m unittest discover -s host/accele160/startup -p 'test_*.py'
```

The source was assembled on the Linux toolchain host with `i960-elf-as -AJX`,
linked with [`ping_handler.ld`](../../../host/accele160/helper/ping_handler.ld),
then extracted with `i960-elf-objcopy -O binary`. The three new mutation tests,
three earlier helper tests and eleven startup tests passed. The native C PING
model passed AddressSanitizer/UndefinedBehaviorSanitizer with 58 single-byte
mutations. No i960 emulator or target run has checked the handler's dynamic
register and cache behavior.

## Remaining gates

1. Independently verify the startup hook runs after loader copy and before the
   first relevant command, and that a later runtime initializer does not
   overwrite `c00234fc`. The static audit cannot prove this.
2. Establish a working rollback/recovery route before considering a flash
   experiment. A spare card is useful, but not proof of recovery for this one.
3. If eventually tested live, use explicit new-card BDF, bounded zero-DMA
   PING, stock-vs-patched completion comparison and readback/health checks.
   A status-0 response alone would still not authenticate the nonce.
4. For upload/execute, define owned code/data/stack memory, I/D-cache
   maintenance, returning call, STOP and timeout semantics separately.
