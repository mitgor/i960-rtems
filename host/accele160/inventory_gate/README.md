# AcceleRAID read-only timer inventory

This is the next gate after the accepted op-9 RTEMS software-clock run. The
fixed op-10 command records selected 80303 timer and interrupt registers in
the previously erased loader page at `c000f8a0`. It does not access TMR0 or
TMR1 (`ff000308`, `ff000318`): Intel's 80303 manual section 18.1.1.1 says a
read clears terminal-count status. It neither changes a timer/interrupt
register nor borrows a vector or allocator grant. The host must save and
restore the complete loader page and check the unchanged owner table.

The register list and order are explicit in `handler.S`. `ff008700` is the
current PRCB pointer; the last eight words are read from the stock ROM PRCB
at `feffdd20`, whose address is pinned by the stock initial boot record. No
live pointer is dereferenced. A sample does not prove that a timer or vector
is free. Repeat it on separate commands and compare flash and owner state
before considering any timer writes.

The accepted 2026-10-17 result is in
[the current artifact](../../../artifacts/current/accele160-inventory-20261017/README.md).
The handler is assembled with `i960-coff-gcc -mrp -c handler.S`, linked with
`i960-coff-ld -T handler.ld`, and flattened with `i960-coff-objcopy -O
binary`; the accepted flat handler is 3,108 bytes and has no relocations.
`audit.py` pins the preceding flash and handler hashes, checks the exact
cave preimage, regenerates the two checksums and refuses any runtime, boot
block or loader-hook drift. `inventory_command.c` is the one-shot, zero-DMA
Linux companion; build it against the test PC's current kernel with
`obj-m += inventory_command.o`. An unfinished command pins itself and its
parent driver. Never force-unload it.

After two same-boot full guarded flash reads, `run_inventory.py` requires the
exact candidate, command module and board identities. It saves the entire
loader page and allocator table, runs two fresh commands, checks the exact
report extent and the 512 owner/count words, then restores the loader page
and PCI aperture. Its 20 ms observed cycle includes host polling. Re-run
`verify_live.py artifacts/current/accele160-inventory-20261017 --tamper-test`
from the repository root to replay all captures and four corruptions. The
first live call's overly broad owner-page check and exact recovery are kept
in `recover_first.py` and the artifact; the bytes at `0xaa0..0xaa1` are
outside the owner/count arrays.

Primary reference: [Intel 80303 I/O Processor Developer's Manual, order
273353](https://bitsavers.trailing-edge.com/components/intel/i960/273353-001_Intel_80303_IO_Processor_Developers_Manual_May2000.pdf),
especially sections 8.7 and 18.1–18.3.
