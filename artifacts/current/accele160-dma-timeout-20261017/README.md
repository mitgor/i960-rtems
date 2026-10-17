# Accepted AcceleRAID 160 host-timeout DMA evidence

`accepted/source/` holds exact test and replay sources, `accepted/image/` the i960 ELF/kernel/upload image, `accepted/host/dma_pin.ko` the pinned host module, `accepted/live/` two runs and four guarded full-flash reads, and `accepted/prior/attempt-1/` the copied exact preceding channel state used for admission. The offline replay checks that copy against the [previous accepted suspend artifact](../accele160-dma-suspend-20261017/README.md). The [subproject README](../../../rtems/accele160/dma_timeout/README.md) gives the test boundary and measured results.

Run from the repository root:

```sh
python3 rtems/accele160/dma_timeout/verify_live.py artifacts/current/accele160-dma-timeout-20261017
python3 rtems/accele160/dma_timeout/test_verify_live.py artifacts/current/accele160-dma-timeout-20261017
```

The upload image SHA-256 is `c2c2234300c5d5cd5caf1fa6f4b05d9df5a1d89cab515085ba1a029b93b9ab5f`. All four firmware snapshots match `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
