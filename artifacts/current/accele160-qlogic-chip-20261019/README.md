# Accele160 chip queue comparison — 2026-10-19

Profile 17 tested on physical `0000:37:09.1` at `mit@192.168.2.75`.
No chip writes, disable/reset commands, new RAM grants or firmware programming.
PC resets separate isolated runtime sessions and restore the accepted service.

## Findings

| Observation | Software cache | Actual chip |
| --- | --- | --- |
| Request producer / consumer | 37 / **0** | Consumer **37** |
| Response producer / consumer | 22 / 22 | Producer **22** |
| ISR | — | 0 |
| Semaphore | — | 2: STATUS set, LOCK clear |

Ready, frame32, idle and final STOP each have two identical chip passes.
The request-consumer cache is stale; equal observed indices are not a hardware
drain or isolation proof. Pending head/tail and active-exchange count remain
zero. Ring capacities remain 256/128 entries (16/8 KiB); the mailbox resource
word 578 is not an active-work count. All firmware ranges remain reserved.
The decoder keeps `status_zero=false` for semaphore 2 and never grants ownership.

[Access contract, report layout and limitations](../../../rtems/accele160/ownership/PROFILE17.md).

## Acceptance and provenance

- `tested-live.tar.xz`: immutable test bundle, kernel/image, modules, source,
  manifests, paired flash reads, frame/WAD captures, runtime reports and client
  results. Session `20261019T105126Z`, boot `91c44f87-bf3e-4d82-a94a-9731e978ba81`.
- `tested-replay.json`: 64 frames, 5045 WAD reads, 709 external exchanges,
  zero errors; maximum observed console reply 3249.679 ms.
- `tested-final.tar.xz`, `stop-replay.json`: unchanged earlier samples, final
  phase-1 sample, QUIE/ACK, retained callback and DMA pins, unchanged guards.
- `observations.json`: four phases/eight equal passes and cache comparison.
- `source-check.json`, `compiled-check.json`, `chip-access.dis`, `app.dis`:
  captured probe sources match the repository; actual `ldos` and normal-identical
  exception object. The admission source/module remain the accepted immutable
  versions; unrelated local admission changes were not deployed.
- `native-tests.txt`, `linux-tests.log`, `build.log`: sanitizer refusal/order/
  envelope tests, inherited containment tests and i960 build.
- `references/`: exact FreeBSD source snapshots with URL/SHA provenance and
  original license notices. `firmware-queue-access.dis` captures relevant reads
  from the pinned expanded firmware (SHA
  `09e84895223627edeff8f1a6902d2a9a573c2c3e7769a5ea16caaa32cf07e3db`).
- `previous-final.tar.xz`: prior normal session's clean STOP, saved before reset.
- `restored-live.tar.xz`, `restored-replay.json`, `recovery.json`, prompt/service
  text: fresh-boot firmware checks and restored normal runtime.

## Reproduce verification from repository root

```sh
python3 rtems/accele160/ownership/verify_inventory.py artifacts/current/accele160-qlogic-chip-20261019/tested-live.tar.xz
python3 rtems/accele160/ownership/verify_stop.py artifacts/current/accele160-qlogic-chip-20261019/tested-live.tar.xz artifacts/current/accele160-qlogic-chip-20261019/tested-final.tar.xz
python3 rtems/accele160/fault/verify_runtime.py artifacts/current/accele160-qlogic-chip-20261019/restored-live.tar.xz --live
bash rtems/accele160/fault/test.sh
```

The normal owner is `/home/mit/i960-owned-runtime-20261018/bundle`, session
`20261019T105649Z`, boot `417ae821-f1d1-4305-9e91-614598e4a5cb`. It passed
64 frames, 5045 WAD reads and 713 external exchanges. `~/rtems-console`
is restored at idle, zone loan zero; gateway 8088 returns HTTP 200. Normal kernel:
`55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`. No physical recovery was required.

Next: establish ISP RISC/SXP/DMA and stock-callback stop/isolation semantics
before disabling engines or reclaiming these ranges. Preserve host ATU/MU and
DMA1 dependencies. This observation is not approval to reuse the queue memory.
