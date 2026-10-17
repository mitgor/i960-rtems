# AcceleRAID 160 Doom arena admission: rejected safely

On boot `ed14ddb9-6cf2-4dbc-8645-1383eda72c2d`, new card `0000:37:09.1`
was bound to exact `myrsread` and idle (`state=0 status=0 residual=0`). The old
DAC960PG `0000:37:04.1` was unbound. No DMA or RAM-command test module remained.
The read-only [upper-bank survey](../../../host/accele160/doom_arena/survey_upper.sh)
held the global card lock, remapped only PIATVR, read thirteen upper-bank 4 KiB
pages twice via BAR0's translated **odd page**, restored PIATVR to `c0000000`
after every page, and rechecked the idle descriptor. All sampled pages were
zero and stable. The two allocator metadata rounds were identical over all
512 count/owner words; two subsequent guarded 1 MiB firmware reads matched
SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
The complete duplicate flash bytes are already archived elsewhere and were
omitted here; read request/result/status evidence is retained.

The live stock allocator still has 2,785,280 free bytes split across two pools;
its largest contiguous free run is only **1,540,096 bytes**. Its 256 blocks map
only `c0000000..c07fffff`. It offers no owner tag for the proposed
`c0800000..c0ffffff` 8 MiB Doom arena. The current exact firmware image also
contains aligned upper-bank address literals at flash offsets `0x3039c`,
`0x30558`, `0x35b40`, `0x412ec` and `0xf407c` (addresses `c08e0000`,
`c08b0000`, `c0855000`, `c0811000`). A literal alone does not prove active
use, but rules out treating this bank as obviously unused. Zero reads cannot
prove DRAM presence, absence of aliasing, or ownership.

The [assessment](assessment.json) therefore **rejects 8 MiB admission**. No
upper-bank data write, firmware flash write, RTEMS upload or Doom launch was
attempted. The live card remains bound and idle; the old card remains unbound.
Replay with `python3 host/accele160/doom_arena/assess.py`. Changing one sampled
page or one flash-result hash makes replay reject the capture.

The next physical gate is a RAM-only operation-13 callback on its owned
512 KiB entry stack, with the stock CPU path suspended while that callback
runs. Before any upper-bank write, it must mask interrupts, prove both DMA
channels inactive and no stock disk work, snapshot an upper 4 KiB page plus
lower-bank comparison pages, and set a finite host/card deadline. Then it may
write a small sentinel, check for aliasing, restore every saved byte, and
verify both banks and DMA/firmware state before normal return. This establishes
only a **temporary alias probe**. Persistent Doom needs a further exclusive
handoff that prevents stock firmware from reclaiming upper-bank cache while
RTEMS runs. After that, test a complete
8 MiB pattern with per-page hashes, internal guards, STOP and timeout cleanup,
post-test owner/page/firmware/DMA audits. If ownership or drain is uncertain,
retain the allocation and do not write or release it. The current 512 KiB grant
and channel-0 finite-transfer recovery do not imply that handoff.
