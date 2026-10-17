# AcceleRAID 160 reboot-only RTEMS ownership

**2026-10-17 acceptance update:** The [full-bank evidence](../../artifacts/current/accele160-fullbank-20261017/README.md)
now proves all 2,048 pages in `c0800000..c0ffffff` distinct and writable under
an exclusive callback. The two firmware-populated pages were saved/restored in
the finite proof. A separate image claimed all 8 MiB, kept operation 13
pending, ran an independent timer heartbeat, and quiesced on STOP without
returning to stock. Its post-reset guarded flash checks passed after a fresh
power cycle; software-only reboot did not bring the PC back. Doom's new-board
allocator and transport remain open. The historical gates
below explain how this result was reached. [Current implementation](ARENA.md).

The intended deployment no longer needs RAID service while RTEMS runs. The
stock firmware remains the bootloader and RAM-upload entry point. After a
validated image enters, RTEMS may keep the i960, timer, interrupt stack and
host transport until card reset. Returning to stock firmware is **not** part
of that deployment. This policy is different from the accepted finite tests:
all current operation-13 images return, restore borrowed bytes and release
the stock 512 KiB grant.

## Physical evidence already accepted

* The [read-only arena survey](../../artifacts/current/accele160-doom-arena-20261017/README.md)
  measured a 1,540,096-byte maximum stock-free run and observed upper-bank
  firmware literals. Its zero pages gave no ownership.
* The [upper-page probe](../../artifacts/current/accele160-exclusive-probe-20261017/README.md)
  changed/restored four words at `c0f01080` in a priority-31 callback while
  CCR, NDAR and BCR of all three DMA channels were idle. STOP and expiry
  returned with identical full 4 KiB host snapshots.
* The [occupied-page probe](../../artifacts/current/accele160-occupied-probe-20261017/README.md)
  also changed/restored four words at `c0011080`, a nonzero page in stock's
  expanded runtime. Both paths passed full page, owner, stage, stack, and
  paired guarded flash audits. The old DAC960PG stayed unbound.
* The [combined timer/DRAM gate](../../artifacts/current/accele160-exclusive-timer-20261017/README.md)
  held both changed pages through two-worker RTEMS hardware-timer preemption.
  Host full-page captures observed the patterns after READY and more ticks;
  STOP/120-tick expiry restored pages, timer/vector/mask, firmware stack and
  allocator. Four complete guarded flash reads matched current firmware.

These show that **selected bytes can be borrowed while stock execution is
paused**. They do not show that the upper bank is an unaliased 8 MiB extent,
that firmware will leave it alone after operation 13 returns, or that a
never-returning RTEMS image can safely reclaim its own active loader path.

## Exclusive handoff contract

1. Boot stock firmware, identify exact new-card BDF `0000:37:09.1`, boot ID,
   firmware hash and `myrsread read_bdf`. Require old card `0000:37:04.1`
   unbound, no block devices, idle stock descriptor, and two complete guarded
   same-boot flash reads. Reserve the 512 KiB loader grant through the
   existing owner-tagged operation; validate every uploaded page and the
   whole image before calling it.
2. Enter on an owned stack at interrupt priority 31. Snapshot processor,
   timer/vector/mask, Messaging Unit, allocator, loader page and all three
   DMA channels. Refuse takeover if any descriptor or transfer is active.
   Stop stock interrupt sources; install only reviewed RTEMS sources and
   independent bounded host sideband. Do not resume the stock command loop.
3. Keep the live entry, ISR, RTEMS workspace, control page, any host-pinned
   descriptor, and all code/data required for STOP or crash reporting outside
   memory being reclaimed. The tested `c0011000` page is within stock's
   expanded image; its reversible write does **not** license overwriting
   `c0010000..c00b77ab` wholesale. With reboot-only exit, other stock-only
   state may be reclaimed only after an explicit liveness map proves it is
   unreachable from the active entry, interrupts, DMA and host transport.
4. Before admitting an 8 MiB arena, prove the chosen extent is real and
   unaliased across the full range. Save data required by the active path,
   perform bounded walking/address-distinctness patterns, and compare all
   relevant guard regions. Check all DMA channels and controller/host state
   throughout. A four-word page probe or zero scan is insufficient.
5. RTEMS must own its scheduler, timer, interrupt stacks, DMA descriptors,
   WAD input and framebuffer output. Host WAD/frame communication must use a
   sideband that works while the stock direct-command mutex is held; normal
   `myrsread` commands cannot be assumed available. Pins and grants remain
   held while the card can access them. A stalled DMA channel blocks unpin
   and release.
6. STOP is an orderly RTEMS shutdown request with a bounded acknowledgement
   and drain of tasks/IRQs/DMA. If the image has overwritten any stock state,
   completion must **not** return through the old firmware callback or free
   the grant. Reset/power-cycle is the recovery boundary. A host process
   dying while the card runs cannot authorize reuse; an independent observer
   retains pinned memory until it proves quiescence or the card resets.

## Next acceptance gates

1. **Finite CPU/timer/DRAM gate accepted:** the combined image checks three
   DMA channels idle, masks stock interrupt sources, runs two RTEMS workers
   with timer preemption, and restores both borrowed pages and exact stock
   timer/vector/priority after STOP or finite timeout. This still depends
   on a functioning RTEMS scheduler; it is not an independent watchdog or
   retained reboot-only image. DMA transfer ownership remains a separate
   gate; the [external-resume test](dma_external_resume/README.md) covered a
   finite transaction, not a never-draining one.
2. **Accepted:** all 2,048 upper-bank pages passed simultaneous address
   markers and complete page patterns with the two populated pages saved and
   restored. STOP/timeout and post-test flash audits passed. The reboot-only
   claim was checked through every BAR-readable odd page.
3. **Prototype accepted; service work open:** a retained RTEMS image kept the
   callback and grant while it owned all 8 MiB, then drained on STOP without
   returning to stock. A fresh power cycle restored stock and passed two full
   flash reads. A general host supervisor, owner-death handling for this mode,
   pinned WAD/frame DMA transport and Doom image admission still need work.

**Current decision:** exclusive reboot-only ownership is the target mode;
RAID service will not run concurrently. The card is presently back in stock
firmware after the power-cycle reset. Doom on this board remains gated by
new-board allocation, image admission and sideband WAD/frame delivery.
