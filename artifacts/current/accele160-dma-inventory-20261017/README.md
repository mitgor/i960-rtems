# Read-only 80303 DMA inventory, 2026-10-17

**Superseded as DMA evidence.** The captured image read `0xff001400`-based
addresses, whereas the Intel 80303's DMA registers are at local
`0x00001400..0x000014ff`. Its all-zero values cannot establish channel
state. Preserve this artifact as a reproducible failed address-map
assumption; the RTEMS lease, flash, loader and allocator checks still stand.

`image/` contains the exact 19-page RAM-only RTEMS image, linked kernel,
ELF, map and symbols. `live/accept-{0,1}` contains two complete HALT/expiry
acceptance batches: per-page copy receipts, whole-image card digest,
returned firmware callback, ISR/task/worker trace, three-channel DMA
snapshot, guarded stacks, owner/page/stage restoration and command status.
`live/{pre,mid,post}-flash-{0,1}` contains six full guarded 1 MiB READIMAGE
audits on boot `7f7e351e-dc82-4bef-bb1e-ceeb8dae827a`; each SHA-256 is
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
No flash write or DMA-register write was issued. The old DAC960PG was
unbound throughout.

All four terminal snapshots reported zero for the *wrong* address range.
CSR was intentionally omitted because its event bits are read-clear. HALT completed at tick 22 in
305.121/304.755 ms; expiry at tick 300 in 3079.100/3080.361 ms.
Restoration flag was 1 and fault word 0 in all four paths.

Replay independently from the repository root:

```sh
python3 rtems/accele160/dma_inventory/verify_live.py artifacts/current/accele160-dma-inventory-20261017
python3 rtems/accele160/dma_inventory/test_verify_live.py artifacts/current/accele160-dma-inventory-20261017
```

The verifier checks image and firmware identities, all six complete flash
reads, 76 per-page receipts, four card-side digests, complete owner/page/stage
restoration, both task/ISR continuations and the DMA words in the raw stack
against the saved results. The tamper test rejects 13 edits, including a
DMA marker and channel word. The source and limits are in
[the DMA inventory gate](../../../rtems/accele160/dma_inventory/README.md).
