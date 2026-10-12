# i960 relocation prototype — offline only

The current engine plus real compiler helpers contains 11,967 `R_960_32`
relocations and still has 44 undefined imports. It is not a loadable image.
`../link_inventory.py` links the installed soft-float libgcc archive, records its
hash/callers and verifies that final linking still fails. Nine actual compiler
helpers are resolved; no addresses are invented for the remaining imports.

The old i960 linker accepts `--emit-relocs` but drops relocation sections in its
final executable. All three final outputs in the evidence show that behavior. A
future relocator must not infer relocation sites by scanning addresses or trust
that option to preserve them.

`pack.py` therefore experiments with retained records from an **import-free ELF
REL object**. It supports only little-endian ELF32/i960, canonical non-overlapping
text/data/BSS placement, internal `R_960_32` references, and an explicit entry
symbol. It refuses undefined/absolute references, unsupported relocation kinds,
escaping addends, duplicate patch sites, unaligned/overflowing bases, excess
memory and missing relocation records. It computes each relocation from symbol
section placement, symbol value and addend. Debug sections are not loaded.

The 184-byte proof has 128 bytes of BSS, internal calls, a data pointer into BSS,
and a runtime-table argument. Six relocation sites were applied. Output at
`0x10000`, `0x200000` and `0xc02d0050` matches separately linked binaries **byte for byte**;
ten malformed-input cases are rejected. The incomplete Doom object is refused.
These are linker-oracle checks, not i960 execution or a production ELF loader.
The rebased bytes have never been admitted to the card.

Next: integrate this restricted relocation manifest with the existing segmented
loader's allocation, CRC, pin, zero-fill and cache-ordering checks, and whitelist
only the proof program. Execute it on the card before extending admission to
Doom. Keep both registered task/IRQ owners, the runnable control worker, full
paired audits and reboot-only exclusive release. Do not relax the currently
accepted runtime probe's whitelist to allow arbitrary binaries.
