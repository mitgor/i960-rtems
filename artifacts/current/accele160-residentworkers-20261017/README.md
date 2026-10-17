# AcceleRAID 160 post-return two-task RTEMS lease, 2026-10-17

`image/` holds the exact linked ELF, kernel and 19-page guarded image, map and
symbols. The image SHA-256 is
`890ca49efdd1ea2228ae305ca3b78402cbd4104cc407f34a05d268123bd8544f`
and whole-image FNV is `a2cdcd12`; the linked kernel SHA-256 is
`43c23db3d547108c08e2d1cc0a0db53582ee3785d2c1f455554ed139d97b7826`.
An independent pinned remote rebuild was
byte-identical. [Source, build and ownership boundary](../../../rtems/accele160/residentworkers/README.md)
are maintained outside this artifact directory.

`live/accept-{0,1}` each contains HALT and no-host expiry, all 19 page-copy
receipts, card-side whole-image digest, returned firmware callback, ACTIVE,
stale-token and terminal snapshots, both ISR pages, task identities/stacks,
worker suspension and progress, allocator checks and page/stage restoration.
HALT ended at tick 22 (301.425 and 304.246 ms); expiry at tick 300 (3,080.969
and 3,079.843 ms). The worker received 2 and 280 timer IRQs respectively.
Both paths had zero ISR faults and restoration flag 1.

`live/pre-flash-{0,1}`, `mid-flash-{0,1}` and `post-flash-{0,1}` are six
complete guarded 1 MiB reads from boot
`7f7e351e-dc82-4bef-bb1e-ceeb8dae827a`; every read matches unchanged
firmware SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
The three stock inventories show timer-1 count/reload/mode zero, pending
clear, mask `10c7`, map `80000` and cached vector 18 `aaaaaaaa`.
New card `0000:37:09.1` remained under `myrsread`; old DAC960PG
`0000:37:04.1` remained unbound. No flash write was issued.

Replay from the repository root:

```sh
python3 rtems/accele160/residentworkers/verify_live.py artifacts/current/accele160-residentworkers-20261017
python3 rtems/accele160/residentworkers/test_verify_live.py artifacts/current/accele160-residentworkers-20261017
```

Both pass; ten targeted mutations of flash, owner, ISR, token, callback,
supervisor and worker evidence are rejected. `diagnostic/` retains compact
captures of the prior sleep-based trial, which stayed ACTIVE with HALT pending
until a reboot; no completion or cleanup was claimed for that trial. Its
obsolete binary and duplicate full flash reads are excluded.

This is a finite two-task drain proof, not DMA ownership or an independently
recoverable resident service.
