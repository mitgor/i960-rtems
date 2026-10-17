# Accepted AcceleRAID 160 active-DMA suspend/resume evidence

`accepted/source/` is the exact test source and replay code; `accepted/image/` contains the i960 ELF, kernel binary, 19-page upload image, map and symbols; `accepted/host/dma_pin.ko` is the exact pinned host target module; `accepted/live/` contains fresh same-boot inventory, two unchanged-image runs (`attempt-0`, `attempt-1`) and four guarded full-flash reads. The test logic and interpretation are in [the subproject README](../../../rtems/accele160/dma_suspend/README.md).

Reproduce the offline acceptance and mutation checks from the repository root:

```sh
python3 rtems/accele160/dma_suspend/verify_live.py artifacts/current/accele160-dma-suspend-20261017
python3 rtems/accele160/dma_suspend/test_verify_live.py artifacts/current/accele160-dma-suspend-20261017
```

The image SHA-256 is `ba5b966c638937e85185095ff8415089101f626c71af20677e4bcbba44a8359b`; the exact pinned-host module SHA-256 is `1ef0b6c44c8dceb2c1b820b61ac17a1d3096c6be87dc3978cf2dcb296fe89690`. The four flash reads each hash to `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
