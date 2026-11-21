# Slot 5 diagnostic FLASHIMAGE retry, one attempt

On cold boot `17eaaa61-eb0d-42f0-936e-7d75e29a6da6`, the sole Slot 5
AcceleRAID 160 passed first bind. Two independent selector-9 full flash reads
matched its stock SHA-256
`0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`.

A separate unsupported IOCTL `0x8f` sense probe completed with host status 2,
`sense_len=14`, and sense suffix `81/04` (internal `0x104`). Its module was
released. A further full READIMAGE still matched stock.

The card then accepted STOREIMAGE of the exact card-specific experimental
writer candidate, SHA-256
`50a4d7da197fa2beb2b9f7836f2c06237822ef03c0aee2b9034f2e2a0c79ca64`.
An independent staged READIMAGE matched it byte for byte. The one-attempt
gate accepted the prior all-sixteen-block lock proof, the same-boot sense
proof, the two fresh stock reads, and the stage/readback receipts.

**One FLASHIMAGE was issued.** It completed with host status 2, residual 0,
`sense_len=14`, and sense `7000090000000007000000008016`. The suffix
`80/16` identifies the stock firmware's internal writer-failure status 22.
The host displayed `elapsed_ms=0` (whole kernel jiffies); this is not a
sub-millisecond measurement. The wrapper retained `flash_image.ko` for
inspection and did not retry. A persistent one-attempt marker was written
before the command. The PCI endpoint and stock descriptor still responded.
The PC was then told to power off.

After a cold power cycle, the PC beeped and booted Linux with this same sole
Slot 5 card. On boot `941d7063-c96b-41a7-950e-7c01f0fb49bd`, the read-only
driver first bind passed. Two independent full selector-9 READIMAGE captures
completed with status 0, residual 0, and unchanged DMA guards. Both have SHA-256
`0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`
and compare byte for byte with the pre-attempt stock capture. **No flash byte
was persistently changed.** The card remains stock and responds normally.

Full `live/` and `post-cold-941d/` captures and kernel logs are retained
locally outside Git. No further FLASHIMAGE should be issued on this card
without a new measured cause and a reviewed plan.
