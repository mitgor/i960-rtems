# Accepted AcceleRAID 160 pre-STOP process-death recovery

`accepted/source/` contains the exact card build, starter, separate recovery, replay and tamper-test sources. `accepted/image/` holds the i960 image and map; `accepted/host/` holds the pinned-DMA module. `accepted/live/attempt-0` and `attempt-1` preserve durable death markers, observed missing PIDs, initial/terminal captures and ownership checks. Six guarded complete flash reads surround the runs. `accepted/replay.json` and `accepted/tamper.json` record offline verification. The [subproject README](../../../rtems/accele160/dma_pre_stop_death/README.md) explains the procedure and proof boundary.

Run from the repository root:

```sh
python3 rtems/accele160/dma_pre_stop_death/verify_live.py artifacts/current/accele160-dma-pre-stop-death-20261017
python3 rtems/accele160/dma_pre_stop_death/test_verify_live.py artifacts/current/accele160-dma-pre-stop-death-20261017
```

The replay depends on the neighboring [accepted held-process-death evidence](../accele160-dma-process-death-20261017/README.md) for exact prior channel state. It accepts two pre-STOP deaths, 26,624,000 bytes per run, tick-300 terminal expiry, all six stock-firmware matches and 16 tamper rejections. Image SHA-256: `0477635a365a3ff40ca7b35759860884ec0aef7663ce70c72842c23dbe28427c`. Stock firmware SHA-256: `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
