# AcceleRAID 160 bounded RTEMS hardware clock — accepted 2026-10-17

This folder retains the **accepted candidate-7** exact `image.bin`, `kernel.bin`, map, symbol list and `app.c` source snapshot. The common build/entry/ISR/cache/linker source and physical harness are in [rtems/accele160/autoclock](../../../rtems/accele160/autoclock/README.md). Candidate-1 through candidate-6 folders retain only small source snapshots; obsolete binaries were dropped. The `live/` tree keeps the two complete accepted batches (`accept-7`, `accept-7-repeat`), their six paired full-flash audits, three independent stock timer/vector inventories, and focused earlier diagnostic captures.

Accepted image SHA-256: `d7234b9309e5e435456ddd50905787b4ddbab4e7fd9e0ea18d5094ca09a39db5`. Kernel SHA-256: `b592bc5a711e6847cc208cc9753e9b672940d17d0c2c2e7c9c3f328f3e695150`. Firmware SHA-256 throughout: `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`. Card: new AcceleRAID 160 `0000:37:09.1` bound to `myrsread`; old DAC960PG `0000:37:04.1` unbound. Boot ID: `2fef3a5a-8027-4067-9d7e-2a8f8f6c6b84`.

| Batch | STOP host time | No-host time | No-host ticks | Worker polls | Post-call full audit |
| --- | ---: | ---: | ---: | ---: | --- |
| `accept-7` | 100.506 ms | 555.830 ms | 52 | 500,000 | two matching 1 MiB reads |
| `accept-7-repeat` | 100.299 ms | 558.102 ms | 52 | 500,000 | two matching 1 MiB reads |

Both batches rejected stale STOP, acknowledged exact STOP, woke the RTEMS worker at hardware tick 5, ran the worker at PC priority 0, and restored timer-1/vector/mask/map, firmware SP, loader page, stage and all owner records. Each used two prior matching full reads; all six retained readback receipts show status/residual/guard changes zero. Read-only inventories after both batches found cached vector 18 `0xaaaaaaaa`, timer-1 mode/count/reload/pending zero, interrupt mask `0x10c7` and map `0x00080000`. No new firmware flash write occurred.

The earlier captures explain why the final guard and priority code matter. `accept-4/rejected-page.bin` shows timer preflight code 6 with stock timer-0 pending `0x1000` but timer-1 pending clear. `accept-6/result.json` shows worker PC `0x001f2002` (priority 31), interrupt mask `0x2000` and pending timer 1, which kept the long loop at six ticks. Candidate-7 corrects `modpc` and reaches 52 ticks with PC `0x00002002`. Candidate-2's no-host status-2 call was retained and cleared by reboot, not force-unloaded. `accept-1` is the initial hardware-wake/STOP proof; it did not establish sustained ticks. These are investigative captures, not deployable binaries.

Replay and tamper checks:

```sh
python3 rtems/accele160/autoclock/verify_live.py artifacts/current/accele160-autoclock-20261017
python3 rtems/accele160/autoclock/test_verify_live.py artifacts/current/accele160-autoclock-20261017
```

The verifier checks all six full-flash contents and receipts, image/FNV pins, card identities, exact page/owner bounds, copy and digest receipts, STOP/timeout reports, ISR stack telemetry and each post-call stock inventory. The tamper test rejects altered flash, STOP report, ISR stack and owner evidence.
