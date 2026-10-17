# AcceleRAID external-resume candidate and negative captures

`candidate/image/` holds the corrected, **not yet accepted** RAM image (`f0228b6a78a408b5d3624f5947b8fd30487a301abcda728e60a87cb74ae58ae6`). Its source and exact live scripts are in [the subproject](../../../rtems/accele160/dma_external_resume/README.md).

`negative/` preserves two useful outcomes from boot `a248da87-1bb3-403e-97fc-837b307e1b0e`:

1. `fallback-run/` and `negative/image/` record the original image (`28b679b9de196c0944603f0a66adc763bb7ac37f4a1635da42e6351a7a99008b`). The owner died at `DMA_HELD`; late recovery observed terminal HALTED, audited normal fallback completion at tick 248 after resume at tick 221, then released all resources. `negative/flash/` holds two pre- and two post-run complete stock-firmware reads, each SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
2. `preflight-rejection/` records the corrected image declining DMA because the supplied prior channel registers were stale. `no-active-page.bin` shows the bounded task fault before DMA, and the host retained its test allocations until reboot. No accepted DMA result comes from this attempt.

Do not promote either outcome as independent external-resume proof. The corrected candidate awaits a cold-boot inventory and matched run. See the subproject README for the exact remaining procedure and limits.

The negative captures can be checked independently with `python3 rtems/accele160/dma_external_resume/verify_negative.py artifacts/current/accele160-dma-external-resume-20261017`; `negative/replay.json` records the current result.
