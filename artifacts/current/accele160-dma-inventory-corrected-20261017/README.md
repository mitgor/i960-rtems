# Corrected AcceleRAID 160 DMA-register inventory, 2026-10-17

The RAM-only image reads the Intel 80303 DMA registers at local
`0x00001400`, `0x00001440` and `0x00001480`. It does not read CSR's
read-clear event flags or write any DMA register. The earlier
[wrong-address capture](../accele160-dma-inventory-20261017/README.md)
used `0xff001400` and is invalid as DMA evidence.

Two unchanged-image HALT/expiry batches passed on boot
`3be73d3c-13ed-4365-9090-52031c3d6c1e`. Channel 0 and channel 2 had
zero in all eight sampled words; channel 1 held a stock descriptor at
`c0611320`, DCR `3f` and moving PCI address, consistent with stock-firmware
use. This is a candidate-channel observation, not exclusive ownership.
HALT ended at tick 22; expiry at tick 300. Six guarded full 1 MiB flash
reads matched SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
All worker/ISR, owner/page/stage and timer/vector restoration checks passed.
The old card remained unbound; no firmware was written.

`image/` contains exact ELF, kernel, map, symbols and 19-page image SHA-256
`07df039f173490bac8db523f667a8bbfd276c3d4f5e4f9a8834b754ab145e711`.
`live/` contains all paired flash and acceptance captures. Replay and
13 tamper cases:

```sh
python3 rtems/accele160/dma_inventory_corrected/verify_live.py artifacts/current/accele160-dma-inventory-corrected-20261017
python3 rtems/accele160/dma_inventory_corrected/test_verify_live.py artifacts/current/accele160-dma-inventory-corrected-20261017
```

Source and channel-ownership limits are in
[the corrected gate](../../../rtems/accele160/dma_inventory_corrected/README.md).
