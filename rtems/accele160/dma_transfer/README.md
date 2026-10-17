# Bounded AcceleRAID 160 card-to-host DMA

After the [corrected read-only inventory](../dma_inventory_corrected/README.md)
showed channel 0 idle during the finite RTEMS lease and channel 1 carrying
stock-firmware state, this RAM-only image submitted one 32-byte-aligned
80303 channel-0 descriptor. It wrote a fixed 256-byte pattern from the
card's owned grant to a fresh, guarded, coherent host buffer supplied by
[`dma_pin`](../../../host/accele160/dma_gate/README.md). The card checked
CCR/NDAR/BCR and the exact previous completed descriptor state before
reading CSR's read-clear flags, then wrote NDAR and enabled channel 0.
Completion required the descriptor to be fetched, BCR/NDAR zero, inactive
CSR, no error flags and disabled CCR. The host independently checked the
entire payload page, both guard pages, card trace and allocator/page/stage
restoration before releasing either side.

The first attempt used the **wrong** `0xff001400` address range, never
reached the DMA engine and left a retained grant and host buffer. Its
[exact failure capture](../../../artifacts/current/accele160-dma-transfer-attempt-20261017/README.md)
was saved before a recovery reboot. The corrected register base is local
`0x00001400`, per the Intel 80303 Developer's Manual, Appendix C. Preserve
this distinction when adapting the experiment to another i960 card.

The corrected first transfer and two unchanged reuse-image runs passed on
the card. All three delivered the exact 256 bytes in two card-side polls.
The reuse image bound its preflight to the prior completed channel-0 state,
which remains in read-only DAR/PADR/LADR/DCR registers even after CCR is
disabled. HALT passed twice at tick 22 and no-host expiry passed at tick
300; full paired flash, stock-channel, owner/page/stage and timer/vector
checks passed. Ten offline tamper cases reject changed flash, owner, host
payload/guards, DMA state, prior state, stale token and worker evidence.
See [exact sources, binaries and captures](../../../artifacts/current/accele160-dma-transfer-attempt-20261017/README.md).

The 30-tick DMA poll is bounded, but a failed or uncertain transfer retains
the host module and card grant; clearing CCR enable is only suspension, not
cancellation. The failed wrong-address test exercised that conservative host
retention, not a real in-flight DMA timeout. Before using DMA for networking
or Doom frames, test a deliberately stalled transfer and prove STOP/expiry
cannot free either allocation until the channel is inactive and its queues
are drained. The current completed-transfer result is a small, direct
card-to-host proof, not a throughput benchmark or a persistent service.
