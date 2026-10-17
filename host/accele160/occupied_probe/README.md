# Host acceptance for occupied-page borrowing

`run_probe.py` is derived from the pinned AcceleRAID RTEMS lease runner. It
checks exact firmware, handler, module and RAM-image identities, two same-boot
guarded complete firmware reads, card IDs, old card unbound, empty block-device
set and idle descriptor. It uploads sixteen pages with per-page card receipts
and a whole-image digest, checks both upper and stock-runtime 4 KiB pages
before/after STOP and timeout, then restores loader, stage and all 512 owner
records before releasing resources. Any uncertain result retains the grant.

`verify_live.py` replays the [physical evidence](../../../artifacts/current/accele160-occupied-probe-20261017/README.md)
using the preceding exclusive-page run's two full reads as preflight. Altering
the card report or the restored stock page is rejected.
