# AcceleRAID 160 callback-free RTEMS timer acceptance, 2026-10-17

`image/` holds the exact linked ELF, 17-page raw and guarded image, map and
symbols. The guarded image SHA-256 is
`6e8e0d60bd6f4b8e48756ae6acbb50740dc1477d517b91da36da3df150d9fd25`
and FNV is `364f75fd`. The stock-coexisting operation-13 firmware is unchanged
at SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
Source and reproducible build are in
[`rtems/accele160/residentclock`](../../../rtems/accele160/residentclock/README.md).

`live/attempt-3` is the accepted two-path card run, not one of the diagnostic
rejections. Callback return took 31.067 ms for expiry and 31.127 ms for HALT.
After return, host ENTER was recorded in stock-firmware interrupt frames. The
RTEMS one-shot timer callback fired at tick 20 after ENTER in both paths. With
no HALT, expiry occurred at tick 300 / 3,076.707 ms. A wrong token stayed
pending, and exact HALT finished at tick 21 / 286.276 ms. Both paths logged
zero ISR faults and exact timer/vector/mask/map, processor priority, firmware
stack, loader page, staging page and all 512 allocator-record restoration.
The ISR stack changed by 156 bytes with 64-byte end guards intact.

`live/pre-flash-{0,1}` and `live/post-flash-{0,1}` are four complete guarded
1 MiB reads from boot `b2f20226-62c9-4f6e-acf1-d543078224f3`, each matching
the firmware SHA above. `live/preflight` and `live/postflight` independently
observed the stock timer-1 count/reload/mode zero, pending clear, mask `10c7`,
map `80000`, and cached vector 18 `aaaaaaaa`. The new card was
`0000:37:09.1` under `myrsread`; old `0000:37:04.1` stayed unbound.
No firmware write was issued.

Replay from repository root:

```sh
python3 rtems/accele160/residentclock/verify_live.py artifacts/current/accele160-residentclock-20261017
python3 rtems/accele160/residentclock/test_verify_live.py artifacts/current/accele160-residentclock-20261017
```

The replay passed. Five independent tamper checks altered flash, owner,
ISR-fault, stale-token and RTEMS-callback fields; all were rejected.
`history/attempt-{0,1,2}` retains compact status, diagnostic loader-page and
guarded-recovery evidence for the three pre-arm status-2 returns. Earlier
full flash reads for those rejected runs are omitted here because the accepted
batch includes fresh paired pre/post reads from the same boot. They remain on
the remote host under `/home/mit/i960-accele160-residentclock-20261017/evidence`.

This is a finite RTEMS **timer-callback** proof after the firmware call, not a
resident RTEMS task or an independent watchdog. No DMA, networking or Doom
was admitted in this experiment.
