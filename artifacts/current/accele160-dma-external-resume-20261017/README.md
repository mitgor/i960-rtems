# AcceleRAID independent DMA resume: accepted and negative captures

`candidate/image/` holds the accepted RAM image (`f0228b6a78a408b5d3624f5947b8fd30487a301abcda728e60a87cb74ae58ae6`). Its source and exact live scripts are in [the subproject](../../../rtems/accele160/dma_external_resume/README.md).

`negative/` preserves two useful outcomes from boot `a248da87-1bb3-403e-97fc-837b307e1b0e`:

1. `fallback-run/` and `negative/image/` record the original image (`28b679b9de196c0944603f0a66adc763bb7ac37f4a1635da42e6351a7a99008b`). The owner died at `DMA_HELD`; late recovery observed terminal HALTED, audited normal fallback completion at tick 248 after resume at tick 221, then released all resources. `negative/flash/` holds two pre- and two post-run complete stock-firmware reads, each SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
2. `preflight-rejection/` records the corrected image declining DMA because the supplied prior channel registers were stale. `no-active-page.bin` shows the bounded task fault before DMA, and the host retained its test allocations until reboot. No accepted DMA result comes from this attempt.

Neither negative outcome proves independent external resume. The subsequent `accepted/attempt-2/` capture does: the host starter died at held DMA, independent recovery wrote RESUME, and the card recorded stop tick 21, resume tick 101, terminal tick 300 and reason 1. Premature pin release returned `EBUSY`; complete payload, guards, DMA, owner/page/stage and RTEMS audits passed; the resources were released. `accepted/fresh-inventory/` is the same-boot channel baseline. `accepted/pre-after-reboot-{0,1}/` and `accepted/post-live-{0,1}/` contain full-read request/result/status records, all reporting the exact stock 1 MiB SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`. The four identical 1 MiB `data.bin` copies were omitted here because the stock image is already archived; the capture retains each read's identity, size, status, hash and guard result. The old card stayed unbound.

The earlier unbound-driver diagnosis was an operator error: the `myrsread` module was inserted without mandatory `read_bdf=0000:37:09.1`. Reloading with this parameter bound the new card immediately. A PCI PM reset was attempted while unbound, but it does not prove a hardware fault. The full power cycle supplied a fresh baseline; it was not shown to be required for binding.

The negative captures can be checked independently with `python3 rtems/accele160/dma_external_resume/verify_negative.py artifacts/current/accele160-dma-external-resume-20261017`; `negative/replay.json` records the current result.

Replay the accepted capture with `python3 rtems/accele160/dma_external_resume/verify_accepted.py artifacts/current/accele160-dma-external-resume-20261017`. Two local tamper checks, changing the recorded resume reason and one DMA payload byte, were rejected.
