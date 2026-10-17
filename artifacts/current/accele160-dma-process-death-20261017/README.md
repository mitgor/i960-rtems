# Accepted AcceleRAID 160 DMA process-death recovery evidence

`accepted/source/` holds the exact starter, independent recovery and replay code. `accepted/image/` and `accepted/host/` hold the reused accepted i960 image and DMA pin module. `accepted/live/attempt-0` and `attempt-1` include the pre-kill `DMA_HELD` markers, recovered terminal traces and full ownership captures; six guarded full-flash reads surround the runs. The replay depends on the neighboring [accepted timeout artifact](../accele160-dma-timeout-20261017/README.md) for the exact prior channel state. The [subproject README](../../../rtems/accele160/dma_process_death/README.md) records the procedure, results and limits.

Run from the repository root:

```sh
python3 rtems/accele160/dma_process_death/verify_live.py artifacts/current/accele160-dma-process-death-20261017
python3 rtems/accele160/dma_process_death/test_verify_live.py artifacts/current/accele160-dma-process-death-20261017
```

All six firmware images match SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`. The reused upload image is `c2c2234300c5d5cd5caf1fa6f4b05d9df5a1d89cab515085ba1a029b93b9ab5f`.
