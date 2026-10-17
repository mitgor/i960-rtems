# AcceleRAID 160 RTEMS task lease

This is the first RAM-only AcceleRAID 160 image that runs the STOP protocol
inside an RTEMS 4.6.6 worker task. It uses the accepted operation-13 firmware
unchanged. The card's stock allocator grants `c0710000..c078ffff`; this image
occupies its first 16 pages, with the last page held for the entry stack.
RTEMS's worker stack is separately allocated inside the image's BSS/workspace.
The last grant page, `c078f000`, remains the upload staging page.

The entry saves firmware PFP, PC, SP and `g8..g15`, changes SP to
`c071ffc0`, calls RTEMS, then restores firmware context before returning to
operation 13. The worker announces READY, polls the separately host-writable
nonce/epoch STOP word, yields cooperatively, and has a fixed 2,000,000-poll
no-host exit. It deletes itself; the Init task observes completion and shuts
RTEMS down. This is cooperative STOP of a task, **not** forced preemption or
an independently enforced deadline for a hung task. Hardware timer/interrupt
ownership and resident execution remain separate gates.

The accepted [card capture](../../../artifacts/current/accele160-rtems-lease-20261017/README.md)
uses image SHA-256
`0eb6e4591739dbf8c46363b74f0c645dd990b5cc139461ac6eb2635ad329263f`
and FNV `8622b536`; the raw kernel SHA-256 is
`e44d1ddab2892623cc6bb876b37ada1bc13d5b9c5aaa28515a825bcb3ebca41e`.
`kernel.bin` and `image.bin` are 65,536 bytes each. The latter replaces the
linker's final entry-stack page with `0xa5` guard bytes.

Rebuild on the Linux host with the pinned GCC 3.3.6, binutils 2.27 and
accepted RTEMS core. The following reproduced both hashes byte-for-byte:

```sh
bash rtems/accele160/lease/build.sh \
  /home/mit/i960-accele160-rtems-20261017/accele160 \
  /home/mit/i960/tools/bin \
  /home/mit/i960-accele160-rtlease-20261017/rebuild
```

`run_rtems_lease.py` is the physical harness. Its arguments name exact
reserve/release/copy/digest/admission modules, pinned firmware and handler,
the two same-boot full flash reads, image and output directory. It refuses a
bound old card, block devices, unexpected stock descriptor, changed module
or image hashes, and existing one-shot modules. Each of 16 upload pages gets
a card-side copy receipt. The even grant pages cannot be directly read from
BAR0; the accepted check uses card-side FNV for every page, direct PCI readback
for odd pages and a whole-image card digest before execution. It keeps the
grant/module on an uncertain result for inspection; use `recover_failed.py`
only after the command is complete and the saved loader/owner/stage state
matches. Do not force-unload a pending callback.

Offline replay and four evidence mutations:

```sh
python3 rtems/accele160/lease/verify_live.py artifacts/current/accele160-rtems-lease-20261017
python3 rtems/accele160/lease/test_verify_live.py artifacts/current/accele160-rtems-lease-20261017
```

The first two attempts reached READY but returned status 2: the worker had
inherited Init's default task argument instead of the session nonce. The
third call completed STOP; its host decoder then rejected a successful result
because it read the telemetry one word off. Each retained grant was inspected,
released and followed by a full guarded flash read. The corrected acceptance
ran STOP and no-host exit through the same grant and firmware, then restored
the entire loader page, staging page and all allocator owner/count records.
