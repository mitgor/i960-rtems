# AcceleRAID 160 live stock dispatch-table snapshot

2026-10-16. The new card `0000:37:09.1` (`1069:0050`, subsystem `1069:0054`)
was running stock firmware with no driver bound. Old DAC960PG
`0000:37:04.1` was also unbound and untouched. Boot ID was
`cf1ad15a-0e2f-4e19-ae9b-3041ced1877f`. No card command, DMA, firmware
write, driver bind, reset or reboot was used.

The root-run [snapshot script](../../../host/accele160/helper/snapshot_stock_table.sh)
checked both BDFs, the new card's identity, absence of drivers, PCI COMMAND
`0002`, and PIATVR `c0000000`. It first read BAR0's default upper 4 KiB.
It changed **only** new-card PIATVR (`PCI config 0x44`) to `c0023000`, used
the existing read-only `mmio_snapshot` helper to capture BAR0 offset `0x1000`
for 4096 bytes, restored PIATVR under an exit trap, then reread the default
page. The default before/after pages were identical, both SHA-256
`ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7`.
PIATVR read back as `c0000000`, PCI COMMAND remained `0002`, and both cards
remained unbound. SSH stayed healthy.

The retained [4 KiB live page](table-page.bin) maps local
`c0023000..c0023fff`. Its SHA-256 is
`6e5964cbbb5d3f38c861e3d651b52143697dfe29902eb84ae766ed84023db110`.
[`audit_stock_table.py`](../../../host/accele160/helper/audit_stock_table.py)
extracts the runtime from the exact paired stock flash and compares **every
one of the 4096 bytes**. All match. The live `0x8e` entry at `c00234f8` is
`c002371c`; the live stock `0x8f` entry at `c00234fc` is `c0023790`, its
unsupported handler. See the [machine-readable receipt](receipt.json).

The stock main entry at `c004cf70` begins with processor-mode setup,
state stores outside the dispatch page, hardware initialization and its
command loop. Scanning aligned words in the complete 685,996-byte expanded
runtime found **no direct absolute reference to `c00234fc`**. Of 239
aligned values pointing into the table page, 238 lie inside that page as
dispatch data; one outside value at `c002413c` points to `c0023fa0`.
This narrows obvious direct-write candidates but does not exclude computed
addresses, broad copies, or writes by later callbacks. An exact stock page
after boot **cannot prove** that a modified loader's table write would
persist: a later initializer could reconstruct the same stock bytes. No
modified firmware has run.

Reproduce the **offline comparison** from the repository root:

```sh
python3 host/accele160/helper/audit_stock_table.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin \
  artifacts/current/accele160-table-snapshot-20261016/table-page.bin
python3 -m unittest discover -s host/accele160/helper -p 'test_*.py'
```

The live snapshot script intentionally refuses a bound card, changed identity,
unexpected PIATVR or unexpected PCI COMMAND. It requires an explicit root
invocation, an isolated output directory and the compiled read-only
`host/accele160/startup/mmio_snapshot.c`. Do not turn this into a host-written
dispatch patch: external PCI writes do not invalidate the 80960JT caches.
