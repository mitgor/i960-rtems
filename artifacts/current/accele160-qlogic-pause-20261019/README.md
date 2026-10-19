# Accele160 one-shot QLogic pause/release — 2026-10-19

Profile 18 on physical `0000:37:09.1`, `mit@192.168.2.75`.
The only chip writes were HCCR `2000` and `3000` after strict identity, queue,
bank and control gates. No DMA/ICR/CONF1/PCI-device writes, SCSI reset, firmware
programming or memory reclamation. PC resets separate the runtime sessions.

## Result

| Field | Before | Paused | Released / after |
| --- | --- | --- | --- |
| HCCR | 0000 | 0020 | 0000 |
| Polls | — | 1 | 1 |
| CONF1 | 0074 | — | 0074 |
| ICR | 0006 | — | 0006 |
| ISR / semaphore | 0 / 2 | — | 0 / 2 |
| Chip request consumer / response producer | 37 / 22 | — | 37 / 22 |

The origin-sequence-1 record is identical through frame32, idle and STOP;
there is no repeat. Both tick observations are 10, which does not establish a
precise duration. This demonstrates RISC pause/release on a quiet workload,
not SXP/DMA completion or hardware isolation. All firmware RAM remains reserved.

[Profile/protocol](../../../rtems/accele160/ownership/PROFILE18.md) and
[stop contract/dependency findings](../../../rtems/accele160/ownership/STOP-CONTRACT.md).

## Evidence

- `tested-live.tar.xz`: immutable source/kernel/image/module bundle, manifests,
  paired flash reads, full frame/WAD/control captures and external client result.
  Session `20261019T131024Z`, boot `5c6b3e15-f29b-4ce1-93f1-47595fdcb283`.
- `tested-replay.json`: 64 frames, 5045 WAD reads, 713 external exchanges,
  zero errors; maximum observed console reply 2714.825 ms.
- `tested-final.tar.xz`, `stop-replay.json`: final STOP, unchanged prior samples,
  QUIE/ACK, callback and pins retained, no guard changes.
- `observations.json`: four records with the same one-shot transaction payload.
- `source-check.json`, `compiled-check.json`, `pause-access.dis`, `app.dis`:
  captured probe source matches repository, halfword `ldos/stos`, two HCCR writes
  with `syncf`, bounded polls and normal-identical exception entry object.
- `native-tests.txt`, `linux-tests.log`, `build.log`: sanitizer tests including
  refused prerequisites, both timeouts, changed state and no retry. Timeout
  failures are simulated; the physical run exercised success only.
- `firmware-stop-access.dis`, `firmware-anchor.json`: reset/pause/bank/release
  sequence from the hash-pinned expanded stock firmware. It is not invoked.
- `references/driver-sources.tar.xz`, `references/sources.json`: exact primary
  driver sources with URLs, hashes and license notices.
- `previous-final.tar.xz`, `previous-final-check.json`: old normal session's
  clean STOP, saved locally before reset.
- `previous-profile-replay.json`: current verifier accepts the profile-17 archive.
- `restored-live.tar.xz`, `restored-replay.json`, `recovery.json`, prompt/service
  captures: fresh boot, paired firmware reads and normal prompt restoration.

The accepted admission source/module were cloned unchanged; unrelated local
admission changes were not deployed. The probe has no RAM-release path.

## Verification

```sh
python3 rtems/accele160/ownership/verify_inventory.py artifacts/current/accele160-qlogic-pause-20261019/tested-live.tar.xz
python3 rtems/accele160/ownership/verify_stop.py artifacts/current/accele160-qlogic-pause-20261019/tested-live.tar.xz artifacts/current/accele160-qlogic-pause-20261019/tested-final.tar.xz
python3 rtems/accele160/fault/verify_runtime.py artifacts/current/accele160-qlogic-pause-20261019/restored-live.tar.xz --live
bash rtems/accele160/fault/test.sh
```

Normal service: `/home/mit/i960-owned-runtime-20261018/bundle`, session
`20261019T131711Z`, boot `4cdd0e35-4d6a-4430-bbe9-be167070673e`. Normal kernel
`55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002` passed 64 frames,
5045 WAD reads and 709 external exchanges. `~/rtems-console` is restored
at idle with zone loan zero; gateway 8088 responds HTTP 200. No physical recovery
was needed. Next: qualify paused banked DMA observation with unconditional bank
restoration before attempting a drain/disable policy or reclaiming any RAM.
