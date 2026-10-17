# First AcceleRAID 160 card-to-host DMA, 2026-10-17

`failed/` preserves the first attempt, which addressed `0xff001400` rather
than the Intel 80303's local DMA block at `0x00001400`. The descriptor was
never fetched; the card-side 30-tick poll reported `dead0005`, the host
payload stayed at its initial `5a` bytes, and the RTEMS worker did not
complete its terminal handoff. The host retained the coherent buffer,
command modules and card RAM grant. Read-only loader, ISR, owner, BSS and
host-buffer captures were saved before a whole-PC reboot. This is an
address-map failure, **not** a demonstrated stall or abort of a real DMA
transaction. No firmware was written and the old card stayed unbound.

`accepted/` contains the exact 19-page reuse image (SHA-256
`2e2858b30cc89799549eca7aa0626128b36d1529d5bea7a0b1a967ee3e84dcae`),
linked kernel/ELF/map/symbols, the first successful image (SHA-256
`f53ce81a5da832a8ec788816a02927834521af4e0cfcf37beb2cc60435dc1c2d`),
and the exact host pin module (SHA-256
`1ef0b6c44c8dceb2c1b820b61ac17a1d3096c6be87dc3978cf2dcb296fe89690`).
`accepted/source/run_dma-used.py` is the exact host runner for the two
reuse-image tests; the initial successful image's card source is also saved.
All captures were made on boot `3be73d3c-13ed-4365-9090-52031c3d6c1e`.

Three card-initiated **channel-0** transfers succeeded: initial HALT,
reuse HALT and reuse no-host expiry. Each moved exactly 256 bytes into a
fresh pinned coherent host window, matched all expected bytes, left the
remaining 3,840 payload bytes at `5a`, and left both 4 KiB guard pages
unchanged. Each completion took two card-side CSR/DAR/BCR polls. Channel 0
reported inactive, NDAR and BCR zero, and DCR `7` before host verification
and release. Channel 1 retained stock descriptor state; channel 2 remained
zero. HALT ended at tick 22 in 302.351/302.276 ms; no-host expiry ended at
tick 300 in 3,079.921 ms. These are end-to-end lease times, **not** pure DMA
latency or bandwidth measurements.

The first transfer's completed channel state was captured by a subsequent
read-only inventory. The reuse image admitted that exact prior state before
submitting a new descriptor, and the second reuse run was bound to the first
reuse capture. Eight guarded full 1 MiB flash reads in four pairs before and after
the successful transfers matched unchanged firmware SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
Page, stage, all 512 allocator-owner words, RTEMS worker, ISR stacks,
timer/vector and firmware callback restoration passed. The old DAC960PG
remained unbound. No firmware write was issued.

Replay the accepted captures and ten deliberate tamper cases:

```sh
python3 rtems/accele160/dma_transfer/verify_live.py artifacts/current/accele160-dma-transfer-attempt-20261017
python3 rtems/accele160/dma_transfer/test_verify_live.py artifacts/current/accele160-dma-transfer-attempt-20261017
```

This proves one bounded 256-byte transfer and successful HALT/no-host
**lease** drain. It does not prove cancellation of a DMA transaction that
is actually stalled or active at STOP. The host pin module retains resources
on uncertain completion; that negative path still needs a deliberate,
separate fault-injection experiment. See
[the implementation and limits](../../../rtems/accele160/dma_transfer/README.md).
