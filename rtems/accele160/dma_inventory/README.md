# AcceleRAID 160 DMA-register inventory under the finite RTEMS lease

**Invalid DMA address mapping, discovered in the following transfer test.**
This exact historical image read `0xff001400..0xff0014ff`. Intel's 80303
peripheral map places the DMA controller at i960 local
`0x00001400..0x000014ff`. The four all-zero snapshots below therefore
describe the wrong address range and **do not show idle DMA channels**.
Keep the binaries and captures to reproduce the mistake and the valid
RTEMS/flash/owner checks. Use the corrected inventory source in
[`../dma_inventory_corrected`](../dma_inventory_corrected/README.md)
for any new card measurement. Do not run this historical image to select
a channel.

This is a RAM-only, read-only gate after the accepted two-task
[post-return RTEMS lease](../residentworkers/README.md). It adds a terminal
snapshot intended for three Intel 80303 DMA channels to that same
supervisor/worker protocol. No DMA register is written and no DMA transfer
is started. The image reads eight offsets at bases `ff001400`,
`ff001440`, and `ff001480`, which are the wrong addresses. It excludes CSR:
its interrupt flags are read-clear in the
[Intel 80303 manual, section 19.14.2](https://bitsavers.trailing-edge.com/components/intel/i960/273353-001_Intel_80303_IO_Processor_Developers_Manual_May2000.pdf).
The 24 words are appended to the existing ISR trace, with marker `DMA1` at
trace word 43. They are read before the retained ISR returns to stock code.

Two unchanged-image batches ran on the new card `0000:37:09.1`. Each batch
exercised exact HALT and no-host expiry. All four snapshots showed
zero in every sampled wrong-address word; each HALT ended at tick 22 and each expiry
at tick 300. The IRQ, worker-drain, vector/timer restoration, page, stage,
and all 512 allocator-owner checks passed. Six same-boot guarded full 1 MiB
flash reads matched the unchanged firmware. The old card `0000:37:04.1`
remained unbound. There was no firmware write. Exact image, card captures,
offline replay, and 13 tamper cases are in
[the artifact](../../../artifacts/current/accele160-dma-inventory-20261017/README.md).

The all-zero snapshot has no DMA meaning because of the address error.
CSR was not sampled. Before enabling a channel, the
next gate needs a pinned coherent host buffer with a 32-bit DMA address, a
card-owned aligned descriptor inside the allocator grant, exact channel
preflight including a carefully controlled CSR read, and a bounded
completion/error path. Intel's section 19.14.1 says clearing CCR enable
suspends rather than aborts a transfer; timeout handling must retain the
host buffer and grant until inactivity and drain are proven. Only a
successful bounded transfer plus STOP and no-host tests can establish DMA
ownership for a network or Doom service.

Build and replay:

```sh
bash rtems/accele160/dma_inventory/build.sh \
  /home/mit/i960-rtems-20261011/bounded /home/mit/i960/tools/bin OUT_DIR
python3 rtems/accele160/dma_inventory/verify_live.py \
  artifacts/current/accele160-dma-inventory-20261017
python3 rtems/accele160/dma_inventory/test_verify_live.py \
  artifacts/current/accele160-dma-inventory-20261017
```

The image SHA-256 is
`1603b2ea798c7e3e4b625673cff60d253f76ee61af30c0e209a9855c8ce4dc14`;
whole-image FNV is `7395d88c`. The runner pins the exact stock firmware,
handler, modules, image, BDFs and paired full reads. On any uncertain
completion it retains the allocator grant and one-shot modules.
