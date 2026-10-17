# Host side of the bounded exclusive-page gate

`run_probe.py` pins the current firmware, operation-13 handler, command modules
and RAM image by SHA-256. It requires two same-boot complete guarded flash
reads, the exact AcceleRAID BDF, an idle stock descriptor, no block device,
and the old DAC960PG unbound. Each uploaded page gets a card copy receipt;
the whole image gets a card FNV check. It compares the upper 4 KiB page before
and after each STOP/timeout run, validates the eight-word DMA/write/restore
report, then restores the loader page, staging and all allocator count/owner
records before releasing the grant. On uncertainty, it retains resources.

Run `verify_live.py` against the [archived physical capture](../../../artifacts/current/accele160-exclusive-probe-20261017/README.md).
The replay checks the exact image, both run modes, four full flash read
records, upper-page restoration and stock-state audits; altered probe or
upper-page bytes are rejected. Reuse only the exact saved hardware profile.
