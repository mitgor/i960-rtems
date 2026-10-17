# AcceleRAID 160 finite-chain STOP evidence, 2026-10-17

`accepted/` holds the exact 19-page RAM-only image, linked kernel/ELF/map/symbols, independently pinned host `dma_pin.ko`, exact card and host sources, six guarded full-flash reads, the fresh read-only DMA inventory, and both complete active-STOP runs. All accepted captures are from boot `a248da87-dfb9-48e1-981a-6a09094fa3bc` on new card `0000:37:09.1`; old card `0000:37:04.1` stayed unbound. The same exact image ran twice with a fresh pinned host target each time. STOP was seen while DMA was active at tick 21, and the 13,000-descriptor, 26,624,000-byte chain completed at tick 48 before host pin or 512 KiB stock RAM grant release. Full flash matched SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd` in all six reads. The accepted image is SHA-256 `5ae10f3c8a16ee67b1f56053473e0627bbf55d5ce6df7143ba55abcf848bc2f4`; independent rebuild was byte-identical.

`negative/` keeps concise diagnostic captures and exact image bytes for three earlier runs. `attempt-0` wrote 3,328,000 bytes successfully but observed STOP only after DMA completion. `attempt-1` never submitted DMA: the host encoded prior DCR `7` while channel 0's fresh-boot DCR was zero, and the card returned `dead0002`. `attempt-2` completed 26,624,000 bytes, but the card did not observe STOP while active because the DMA polling loop had no D-cache invalidation before reading the host-written sideband. Each strict failure retained host/card resources until reboot; no release or post-run full-flash audit is claimed for them. The negative image binaries are preserved; the accepted source is the corrected version.

The full independent replay checks image and host-module hashes, all six flash audits, the fresh read-only channel inventory, every 19-page copy receipt and card digest, both host payloads and guards, STOP ordering, final DMA registers, worker/ISR stacks, stock owner records, loader/staging restoration and prior-state binding. Ten deliberate capture alterations are rejected:

```sh
python3 rtems/accele160/dma_chain_stop/verify_live.py artifacts/current/accele160-dma-chain-stop-20261017
python3 rtems/accele160/dma_chain_stop/test_verify_live.py artifacts/current/accele160-dma-chain-stop-20261017
```

The accepted run is a normally completing finite DMA chain with STOP observed during transfer. It does **not** establish safe cancellation of a genuinely stalled active channel. See [implementation and limits](../../../rtems/accele160/dma_chain_stop/README.md).
