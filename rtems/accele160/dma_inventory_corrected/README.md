# Corrected Intel 80303 DMA register inventory

This RAM-only image repeats the finite post-return RTEMS supervisor/worker
lease while reading **local** `0x00001400`, `0x00001440` and `0x00001480`
DMA register blocks. These are the addresses in the Intel 80303 Developer's
Manual, Appendix C, Tables C-18/C-19. The earlier
[`dma_inventory`](../dma_inventory/README.md) image used `0xff001400`
and its all-zero words were not valid DMA-channel evidence.

Two unchanged-image batches passed on the card. At each HALT and no-host
terminal snapshot, channel 0 and channel 2 were all zero in CCR, DAR, NDAR,
PADR, PUADR, LADR, BCR and DCR. Channel 1 held a stock descriptor at
`c0611320` and DCR `3f`; its PCI address changed between batches. Thus
channel 1 was **not** selected for experimentation. CSR was deliberately
omitted because its event bits are read-clear. No DMA register was written.
Six guarded full flash reads and complete RTEMS, timer/vector,
owner/page/stage audits passed, with 13 tamper rejections. See the
[exact evidence](../../../artifacts/current/accele160-dma-inventory-corrected-20261017/README.md).

This identifies channel 0 as an idle candidate during the finite RTEMS
lease, not as permanently exclusive. The following
[bounded transfer gate](../dma_transfer/README.md) rechecked CCR, DAR,
NDAR, BCR and CSR at admission, then used a card-owned descriptor and pinned
host buffer. Its three successful transfers provide the actual completion
and drain evidence. The stock card's channel 1 must remain untouched.
