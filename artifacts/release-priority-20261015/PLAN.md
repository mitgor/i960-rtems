# Release priority and private-memory experiment

Declared before the long measurement blocks completed (2026-10-15).

- Two 520-frame runs using the identical accepted kernel, engine, module, WAD,
  low-detail mode, CRC/FNV policy, scripted restart inputs and full-audit cadence.
- After the existing frame-60–66 restart, measure blocks 100–199, 200–299,
  300–399 and 400–499. Run one assigns baseline/priority/priority/baseline;
  run two reverses that order. Every interval remains in its block. No new inputs
  are injected during the measured blocks.
- Baseline uses four-word audit gate holds and publishes HTTP state after release.
  Priority gives pending releases precedence, uses one-word audit holds, and
  publishes the validated immutable host copy before waiting for release.
  Both still read every word and pump packets/sleep once per four audit words.
- Record gate wait, ioctl duration (including any kernel-mutex wait), audit holds,
  completion observation, browser publication, host delivery and card publication.
  Report host FPS and card publication FPS together to expose queue phase.
- Existing paired mailbox reads, initial three-second two-slot stall, complete
  guards/markers, held-frame STOP and heap/IRQ drain remain mandatory. First 52
  frames are compared with the native oracle; longer captures are cross-compared.
- Only after the unchanged-engine comparison, consider selective `-O2` builds of
  private Newlib memcpy/memset. Everything else stays `-Os`. No libc replacement,
  MMIO widening, allocator ownership change or checksum/audit removal. Test actual
  source paths with ASan/UBSan, inspect target assembly and run the full native
  engine before physical admission. Any memory candidate is measured separately.
- No speedup is promised. Preserve failed evidence. Do not force-unload retained
  mappings; copy/hash/replay evidence before normal reboot and restore public HTTP.
