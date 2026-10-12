# i960 relocation proof — physically accepted

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
Those original checks were host-only. The closed proof has now also executed
twice on the card at `0xc02d0050`; it is still not a production ELF loader.
See [physical evidence](../../../../artifacts/doom-relocate-20261012/README.md).

The segmented integration below is now accepted for this proof only. Next:
resolve the remaining engine imports and connect the WAD cache through the
runtime table before attempting bounded Doom startup. Keep both registered task/IRQ owners, the runnable control worker, full
paired audits and reboot-only exclusive release. Do not relax the currently
accepted runtime probe's whitelist to allow arbitrary binaries.

## Closed card admission implementation

New `--doom-runtime` builds also define `I960_DOOM_RELOCATE`. `build.py` first
runs the three independent linker comparisons and ten malformed-object checks,
then generates the zero-base template, exact section geometry, entry offset and
six patch offsets from the reviewed `probe.c`. This metadata is compiled into
protected loader code; the host cannot submit a relocation recipe.

UPL1 command 13 admits only that complete three-segment image after ordinary
segmented CRC verification, BSS zero-fill and cache preparation. It checks every
file-backed byte against the template and all 128 BSS bytes against zero. The
existing allocation pin stays held. After entering RUNNING under the shared
metadata mutex, the owning worker adds the actual allocation address to the six
trusted words and synchronizes data/instruction caches before calling the entry
through the existing runtime table. Bulk work stays outside the metadata lock.

On return it verifies the expected result, every one of the 32 BSS counters and
every initialized code/data byte against the rebased template, including the
pointer into BSS. Any post-entry discrepancy quarantines the image and aborts the
exclusive session. A successful call restores the original template and zero
BSS, synchronizes caches again, and completes the image under the mutex. Thus a
second call must pass the same full admission gate. Command 14 reports only the
READY image's offset within the existing arena; it does not accept an address.

The closed proof has no general import resolver, task launcher or engine ABI.
Native sanitizer testing uses the actual loader/allocator/runtime and a clearly
marked arithmetic model in place of i960 instruction execution. It exercises two
allocation addresses, repeated calls and rejection of altered entry/code/data,
nonzero BSS and incomplete images. Physical execution is established separately
by the live capture. Reproduce the native check with:

```
python3 rtems/residentnet/test_relocate.py --entry BUILD/residentnet/entry
```

Retain worker 0 as the runnable network/control owner. Keep full paired audits,
WAD query/reply serialization, generation handles and STOP task/IRQ drain. Never
force-unload exclusive resources; reboot and restore the cooperative public
service after the batch.
