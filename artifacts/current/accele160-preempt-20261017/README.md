# AcceleRAID 160 bounded RTEMS preemption — accepted 2026-10-17

The `image/` directory contains the exact accepted 27-page `image.bin`, linked `kernel.bin`, symbol/map files and source snapshot. The maintained implementation and physical runner are in [rtems/accele160/preempt](../../../rtems/accele160/preempt/README.md). SHA-256: image `514dfc5b1c8ea1a2ef114ad421f88a12f015a7669dea8af70981dfead107405f`; kernel `3f211bf02b85e911836259cd7f83be27b4ffb0c4e93d2aa1c80d89e669bd4f7f`; pinned firmware `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

`live/accept-0` and `live/accept-1` each contain a valid-STOP and finite-no-host path with all 27 copy receipts, card-side whole-image digest, admission reports, ISR/entry-stack samples, page/stage/owner snapshots and final result. `live/after-accept{0,1}-flash-{0,1}` are paired full 1 MiB post-batch reads. `live/post-accept{0,1}` hold independent stock timer/vector inventories. `live/attempt-0` records the first returned call, rejected only because the host tried to read a trace from an even grant page; `host-recovery.txt` and `after-attempt0-flash-{0,1}` show guarded recovery and two complete matching flash reads. `preflight-0` records stock state before any call in this batch. These captures are from boot ID `2fef3a5a-8027-4067-9d7e-2a8f8f6c6b84` and the exact new-card BDF `0000:37:09.1`; old card `0000:37:04.1` was unbound.

Both accepted batches delivered 8/120 timer ticks and 8/120 task handoffs for STOP/no-host. The workers' ISR continuations entered and returned 4/4 and 60/60 times, with overlapping live continuations observed. Full owner/page/stage restoration passed; all six full flash reads matched the same firmware. No firmware write occurred.

Replay the binary identities, every full read/receipt, page-copy and digest evidence, STOP ACK/deadline, stack and owner records, and independent inventories with:

```sh
python3 rtems/accele160/preempt/verify_live.py artifacts/current/accele160-preempt-20261017
python3 rtems/accele160/preempt/test_verify_live.py artifacts/current/accele160-preempt-20261017
```

The tamper test rejects altered image, full flash, STOP and owner evidence. Read the maintained [scope and remaining gap](../../../rtems/accele160/preempt/README.md) before treating this bounded experiment as a resident service.
