# CPU-side staging verification

The fixed 128-byte callback reads the full candidate through `C1F2C000`, the
source alias used by the stock flash programmer. It computes CRC32 and returns
`017F` for `2012D01F`, otherwise `0180`. The live rehearsal passed and restored
all RAM. See [PROGRAMMING-PREFLIGHT.md](../../PROGRAMMING-PREFLIGHT.md).

`start.s` contains an `EXPECTED_CRC` marker. Generate its assembly by replacing
that marker with `0x2012d01f`, then compile with the existing `i960-coff-gcc -mrp`,
link with `link.ld` and extract the raw binary. Exact compiled bytes and source
are archived in `artifacts/programming-preflight-20261010/build/`.

`build_probe.py --binary <probe.bin> --out <new-build-directory>` validates the
pinned callback and prepares a fixed variant of `host/dump`. That variant runs
CPU verification while the candidate is staged, restores table/code, then
restores full stock staging. It does not enable flash programming.

`validate_live.py` checks all archived image, RAM, table and command evidence.
`program_plan.py` emits the custom full-image programming design, including
preserved descriptor/boot-block policy and the fresh readback route. It has no
hardware access. The CPU visibility result includes prior explicit D-cache
invalidation; do not infer that the alias is intrinsically uncached.
