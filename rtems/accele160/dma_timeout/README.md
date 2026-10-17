# Host timeout while card DMA remains suspended

This follows the [short active-DMA suspend/resume proof](../dma_suspend/README.md). The card again starts a finite 13,000-descriptor channel-0 chain to an exactly admitted, pinned host buffer. On a valid STOP token while CSR says active, it clears CCR Channel Enable. It publishes `DMA_HELD` after two 10 ms ticks, holds the channel for 80 ticks, then automatically sets Channel Enable and requires normal completion. Both allocations remain owned throughout. This does not try an arbitrary PCI target or write flash.

The host observes `DMA_HELD`, checks the stock owner records and pinned-buffer status, crosses a 150 ms wait deadline while the card is still held, then tries the pin module's release operation. Release must return `EBUSY`; the pin, guards and grant must still be owned. It continues waiting instead of treating the host deadline as DMA completion. Once the finite chain drains, the usual full card, host, owner, staging, loader, RTEMS stack, timer/vector and firmware-continuation audits precede the real release. Any failed check leaves the pin, grant and command modules retained.

On boot `a248da87-1bb3-403e-97fc-837b307e1b0e`, two unchanged-image runs with fresh coherent buffers passed. STOP and suspension occurred at tick 21, the host's deadlines were 150.229 and 150.230 ms, premature release returned `EBUSY` (`errno 16`), card resume occurred at tick 101, and all 13,000 descriptors finished at tick 128. DAR/NDAR/BCR snapshots across the hold matched in each run; final CCR/CSR, NDAR and BCR were zero. End-to-end times including host audits were 1,359.654 and 1,361.785 ms. Four guarded full 1 MiB firmware reads in pre/post pairs matched SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`. The old DAC960PG stayed unbound and untouched.

The exact image SHA-256 is `c2c2234300c5d5cd5caf1fa6f4b05d9df5a1d89cab515085ba1a029b93b9ab5f`; kernel SHA-256 is `e1765ca3f4c5230f8fe1a1c4dc133c3b9550e5d2e6595f2069257b1835c2cc3d`. An independent rebuild was byte-identical. [Sources, binaries and all captures](../../../artifacts/current/accele160-dma-timeout-20261017/README.md) are archived. The offline replay depends on the preceding accepted suspend artifact to validate the exact same-boot channel state and rejects sixteen tampered captures:

```sh
python3 rtems/accele160/dma_timeout/verify_live.py artifacts/current/accele160-dma-timeout-20261017
python3 rtems/accele160/dma_timeout/test_verify_live.py artifacts/current/accele160-dma-timeout-20261017
```

This establishes **retention across a host wait timeout while DMA is deliberately suspended, then audited release after normal completion**. It does not establish how to recover a channel that remains active because of a real PCI fault, nor that a killed host process can reconstruct and safely release its resources. Those require separate gates. The [Intel 80303 Developer's Manual, §19.10.3 and §19.14.1](https://bitsavers.trailing-edge.com/components/intel/i960/273353-001_Intel_80303_IO_Processor_Developers_Manual_May2000.pdf) explicitly describes CCR disable as a suspend, not an abort.
