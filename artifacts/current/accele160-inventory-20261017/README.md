# AcceleRAID 160 timer/interrupt inventory gate

Status, 2026-10-17: **read-only operation 10 accepted on the AcceleRAID
160.** The new card `0000:37:09.1` was bound to the exact `myrsread` driver,
and the old DAC960PG `0000:37:04.1` remained unbound. This is a register
inventory, not hardware timer/interrupt or STOP ownership.

The accepted preceding full flash was SHA-256
`68451b38b96609fa3a95eb9497fe85a34ac92fec45b912c53612969b1209a988`.
The [new candidate](candidate.bin) is exactly 1 MiB, SHA-256
`9d5d4da2c283d10e1dee9c71ceb477f36e389cd0d0548764a3cc5f8a41a24c49`.
Its [handler](../../../host/accele160/inventory_gate/handler.S) is 3,108
bytes, SHA-256
`bd03b07ca13b4b59feadae624def17f22ad0c7360ece4f4567362ff17201c736`.
The [offline audit](../../../host/accele160/inventory_gate/audit.py) found
2,622 changed bytes, all confined to the previously allocated loader cave
and the two image checksum words. The decompressed runtime, boot block and
loader return hook are unchanged. The candidate checksums pass; three
mutations of the handler, prefix and preceding flash were rejected. The ELF
had no remaining relocation entries.

The [full preflash READIMAGE](live/preflash-read/result.json) returned the preceding SHA exactly, with status,
residual and DMA guard changes zero. STOREIMAGE staged the new candidate,
and an [independent full staged READIMAGE](live/staged-readback/result.json)
returned its exact SHA with the same zero error/guard fields. [FLASHIMAGE](live/flash/result.json)
then completed in 37.04 s, also with status and residual zero. The PC
restarted from boot ID `ccdf3abd…` to `82ee0014…`; two [independent](live/persistent-0/result.json)
[postboot reads](live/persistent-1/result.json) matched the candidate
byte-for-byte with status, residual and DMA guard changes zero. A
[post-call full read](live/postcall-flash/result.json) also matched.

Operation 10 is bounded and observational. It saves 15 address/value pairs
and eight words from the fixed stock-ROM PRCB to `c000f8a0..c000f947`;
the host harness restores the complete loader page. The register list uses
the [Intel 80303 Developer's Manual](https://bitsavers.trailing-edge.com/components/intel/i960/273353-001_Intel_80303_IO_Processor_Developers_Manual_May2000.pdf)
sections 8.7 and 18.1–18.3, and the
[i960 Jx manual](https://bitsavers.trailing-edge.com/components/intel/i960/272483-001_Intel_i960_Jx_Microprocessor_Users_Manual_Sep94.pdf)
for the PRCB and stack-pointer registers. Reads of TMR0/TMR1 mode are
excluded because they clear terminal-count status. No timer, mask, vector,
DMA or flash register is written by operation 10. A read showing zero does
not establish ownership.

The first [inventory call](live/inventory-run/) completed with status 0 and
the expected 168-byte report. The initial host harness intentionally stopped
on two changed bytes at owner-page offsets `0xaa0..0xaa1`. Those are just
past the 512 count/owner words at `0x2a0..0xa9f` and had also changed in the
earlier allocator acceptance. We captured the entire page, verified all 512
actual records unchanged and the loader page unchanged outside the report,
then [restored the saved loader page and released the completed module](live/inventory-run/run-0-recovery.json).
The corrected [pinned harness](../../../host/accele160/inventory_gate/run_inventory.py)
ran [two more fresh command cycles](live/inventory-repeat/result.json),
both status 0. It verified the full loader page outside the report and its
exact restoration, all 512 owner records, the old card's unbound state, the
PCI aperture and module release. Observed host command cycles were 22.4 and
22.5 ms, including host polling; they are not card execution times. No
companion module remains loaded.

All three reports agreed on timer-1 reload/count `0/0`, pending `0`, mask
`0x10c7` (timer-1 bit 13 masked), mapping `0x00080000` (timer-1 field 0;
timer-0 field 8), PRCB `feffdd20`, ISP `c0001000`, and the fixed stock-ROM
PRCB words. Timer 0's reload was `0x4c4b4` while its count moved across
samples. These values describe the observed stock runtime only. Since the
mode registers were not read, we cannot yet assert that timer 1 is disabled;
even a zero count and masked interrupt do not grant ownership of its vector
or stack. The 80303 manual says a timer interrupt can be posted just after a
disable store, so a future timer experiment needs a drain and restoration
check.

[Independent replay](../../../host/accele160/inventory_gate/verify_live.py)
passed all five full flash captures, staged/flash receipts, all three
inventory reports, actual owner records, loader-page bounds and first-call
recovery. Four mutations (report, loader byte outside report, owner word and
unclassified dynamic field) were rejected. The exact module SHA-256 is
`e3bf8856c0746f80305b8d9668e70ff85bd14eb431556d8e2b6a54aa83402333`;
its [binary and linked handler](build/) are archived. The isolated remote
workspace is `/home/mit/i960-accele160-inventory-20261017`; the archived
`live/` directory is sufficient for replay.

Next: inspect the stock interrupt table/vector and qualify timer-1 mode with
its read-clear semantics, then design an exact bounded timer experiment with
an owned interrupt stack, state restoration and independent host STOP. Do not
declare timer or STOP ownership from this observation alone.
