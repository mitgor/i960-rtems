# Framed MU live acceptance — 2026-10-11

**Passed on the card, without reboot or flash programming.**
The original web service stopped with full restoration before the experiment and
was restarted with its existing production binaries afterward.

| Check | Result |
| --- | --- |
| STATUS and PING over CTL1 fragments | Passed; PING returned 0960CAFE |
| Exact PING retry | Identical cached response and heartbeat |
| Wrong epoch / damaged checksum | Rejected with statuses 2 / 1; valid sequence preserved |
| Independent STOP | RTEMS stopped at tick 362, control heartbeat 363 |
| STOP retry and later STATUS | Tick 362 and heartbeat 363 unchanged; stopped=true |
| Independent final timer HALT | 2F000000 acknowledgement, 9.480348 ms |
| Firmware sequence throughout all nine ioctls | 1 → 1; only the initial arm STEP preceded them |
| Framed transaction latency | 643.87–657.81 ms, including complete response readout |
| Cleanup | Full RAM, timer/vector/mask, message words and message-1 pending restoration; module unloaded |

The STOP transaction took 648.85 ms including serialization and response fetching.
It is not a sub-millisecond emergency-stop mechanism. The existing firmware
cleanup transaction was issued **after** independent STOP/HALT; it remains
necessary before reclaiming RAM. This is evidence for bounded background RTEMS,
not unrestricted preemption or stopping a task with interrupts masked.

- `live.tar.xz`: exact `muctl` target binary/ELF/build, Linux module/generated
  source, `muctl-live1` raw ioctl buffers, parsed exchanges, preflight/open/close
  captures, MU snapshots, acceptance/restoration JSON, and relevant sources.
- `build.log`, `live.log`: build and hardware acceptance output.
- `offline-tests.log`: complete RTEMS native regression suite, including shared
  framed target/host code with ASan/UBSan. Watchdog and several failure cases are
  simulated evidence, not live fault injection.
- `http-check.txt`: HTTP verification after restarting the original Vader service.

[Implementation and limitations](../../rtems/control/MU-FRAMED.md).

Recheck the archived binaries, raw responses, counters and full RAM restoration:

```sh
python3 rtems/control/verify_framed.py artifacts/mu-framed-20261011/live.tar.xz
```
