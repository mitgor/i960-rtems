# AcceleRAID 160 STOP-ignoring worker containment — accepted 2026-10-17

`image/` contains the exact 27-page accepted RAM image, linked kernel, map, symbols and source snapshot. The maintained [implementation and physical runner](../../../rtems/accele160/contain/README.md) live under `rtems/accele160/contain`. SHA-256: image `42e97872951539f5cb4c7418c466364919007d0d35a2dbf81dbf014d58e3ffde`; kernel `4ae72fd5aab5fc5f167bed6bcf60f62352d15549034844300735c906bb5b024e`; firmware `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

`live/attempt-0` and `live/accept-1` are both accepted physical batches. Each has STOP and no-host expiry captures, all 27 per-page copy receipts, whole-card digest, original/stale/valid sideband words, retained ISR/worker-stack samples, owner/page/stage snapshots and final result. `live/after-attempt0-flash-{0,1}` and `live/after-accept1-flash-{0,1}` are complete paired post-batch 1 MiB reads. `live/preflight-0`, `live/post-attempt0` and `live/post-accept1` record independent stock timer/vector inventories. All were taken on boot ID `2fef3a5a-8027-4067-9d7e-2a8f8f6c6b84` with the new card at `0000:37:09.1` and the old card unbound.

Both batches show STOP after 14 hardware ticks and the finite no-host exit after 124; both workers ignored STOP for four ticks, then were suspended externally with one original ISR continuation retained each. Their progress and stack/ISR checksums remained stable through 10,000 checks. All four full flash reads matched the unchanged pinned firmware; no flash write occurred. The loader page, staging source, allocator records, timer/vector state and firmware stack restored.

Offline replay and four tamper cases:

```sh
python3 rtems/accele160/contain/verify_live.py artifacts/current/accele160-contain-20261017
python3 rtems/accele160/contain/test_verify_live.py artifacts/current/accele160-contain-20261017
```

This evidence supports bounded whole-instance disposal while interrupts and scheduling work. Read the [scope and remaining gates](../../../rtems/accele160/contain/README.md) before extending it to a resident service.
