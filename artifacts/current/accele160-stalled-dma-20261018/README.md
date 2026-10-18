# Accele160 suspended-DMA timeout tests

**Both suspension/timeout tests and reset recovery passed; normal prompt restored.**
Final live boot `a320a74a-d22e-4bdc-83f9-ef2649e30e2f`, session `20261018T221116Z`. The original
qualified profile-5 kernel remains at verified idle after 64 frames, 5,045 WAD
reads and 529 external console exchanges without errors. Use Linux
`~/rtems-console` or Mac repo `./rtems-console`. Gateway 8088 is also restored.
Do not reset this live owner merely to finish documentation.

Qualification started 2026-10-18 and continued after midnight on 2026-10-19
(Europe/Berlin); archive/session names retain their starting-date/UTC convention.
See [implementation and limits](../../../rtems/accele160/fault/STALLED-DMA.md).

The test deliberately suspends an established DMA0 transfer using documented
CCR.CE=0. It does not fabricate a software busy flag, disable the entire PCI
bus master, target unmapped host memory, or construct an endless chain. This
is a controlled hardware suspension, not an unresponsive-PCI-target test.

## Evidence

- `restored-live.tar.xz`, `restored-replay.json`: exact original profile-5
  bundle and final session, both guarded firmware reads, all 64 DMA frames,
  console raw wires/client results, and three owned-state captures.
  Kernel `55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`.
  529 external exchanges passed; maximum sampled card reply was 2411.833 ms,
  not a new deadline guarantee. Replay using `verify_runtime.py --live`.
- `recovery.json` links both terminal tests to the next boot's paired firmware
  reads. Individual terminal replay does not claim later evidence by itself.
  All requested reboots returned without physical intervention.
- `restored-prompt.txt`, `restored-services.txt`: live prompt, idle game,
  returned workspace loan and active owner/gateway.

- `previous-final.tar.xz`: prior normal profile-5 session's clean STOP.
- `prepared-fault.tar.xz`: exact mode-8 candidate, sources and build products.
- `fault-tested.tar.xz`, `fault-replay.json`, `fault-hardware-state.json`:
  real `faulte` after DMA0 suspension, boot
  `b65eae66-cf12-4424-992e-ec9c89e1cdae`, session `20261018T220405Z`.
  Kernel `943795e0d427e9d4eea2897d06e968748ad741110b1fd70f1dab1a5a958f498e`.
  Entry CCR=0, CSR=0x400, NDAR=c0821020, BCR=65032. All 10000000
  observation polls expired with that same incomplete state. The host observed
  the terminal report 2.494 s after its trigger (not a hard latency guarantee).
  No completion marker, all guards intact, unchanged source/chain/owner checks,
  stable partial payload and untouched second target. STOP and module removal
  did not release resources. The runner exited cleanly; the separate
  `run/post-owner-exit.json` audit still found `done=0 released=0`, retained
  pins and byte-identical host buffers.
- `prepared-nmi.tar.xz`: exact separately built mode-9 NMI candidate.
- `nmi-tested.tar.xz`, `nmi-replay.json`, `nmi-hardware-state.json`: real
  doorbell NMI, boot `a5ca1694-68f9-4c56-883c-e6a33a5ba5c1`, session
  `20261018T220805Z`. Kernel
  `b218b15b054c87475c86dcf39f53b6a7cbcaae936ebda9abd504a0a3b332e52d`.
  Vector 248 entered with CCR=0, CSR=0x400, NDAR=c0821020 and BCR=65040.
  All 10000000 polls expired at the same outstanding state. Host terminal
  observation was 2.495 s after trigger. All integrity/retention checks passed,
  including after owner exit. Its fresh firmware pair closes fault recovery.
- `entry-and-loop-audit.json`: both exact disassemblies show the entry CSR
  capture and bounded loop loading CSR every iteration, up to 10000000 polls.
- `native-tests.txt`, `native-tests-linux.txt`: policy/card/host negative tests;
  Linux additionally runs the actual diagnostic's enabled and suspended paths
  with simulated MMIO, including timeout, errors, and descriptor geometry.

Replay immutable captures with:

```
python3 rtems/accele160/fault/verify_dma.py ARCHIVE
```

The 64 MiB figure describes the configured finite chain, not completed traffic.
An exhausted poll bound never becomes a drain receipt. Fingerprints cover the
whole source/descriptor list; independent host reads cover visible odd pages.
The PCI aperture cannot directly expose intervening even pages.

Unresponsive targets, indefinite PCI retry, blocked MMIO reads, arbitrary
engine failure, resume/abort, memory reclamation without reboot and broader
SCSI/cache exclusion remain open. The bound counts completed MMIO polls;
it is not a hard wall-clock guarantee if the bus itself fails to respond.
The unrelated existing artifact symlink under `accele160-flat-20261018` is
unchanged. Checksums and replay cover this batch, not a new whole-tree audit.
