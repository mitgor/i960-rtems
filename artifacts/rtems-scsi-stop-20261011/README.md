# SCSI stop, usable packet RAM and resident traffic — 2026-10-11

This batch qualifies the board's private **Symbios 53C895**, implements an
optional held-secondary-reset resident mode, and expands the packet queue to
72 MTU-sized slots inside the existing allocation. Physical RAM outside that
allocation remains denied because stock NMI/fault paths still need ownership.

See [the contract and remaining gates](../../rtems/residentnet/SCSI-STOP.md).
Reset is a forced stop/discard operation, not a graceful SCSI flush or proof of
disk-data consistency. No flash programming or SCSI commands are involved.

## Preserved evidence

- `residentnet-scsi-topology.tar.xz`: first 28-page diagnostic image/module,
  30-callback restored run, source snapshot and logs. Two earlier invocations
  failed before card access: module compilation had not finished, then another
  experiment held the session lock. Both logs are preserved.
- `residentnet-scsi-config.tar.xz`: 29-page image/module, 31-callback restored
  run and exact PCI configuration read evidence.
- `residentnet-scsi-reset.tar.xz`: first reset-enabled build, bounded bring-up,
  12,000-tick resident run, raw packets/control/snapshots and retained close.
- `residentnet-scsi-final.tar.xz`: final 72-slot reset build/module, 31-page
  bounded probe and 36,000-tick resident run with ten spaced dual-stack rounds.
- `scsi-production-restored.tar.xz`: cooperative production image/module,
  restored-service preflight/open captures and published endpoint metadata.
  The live stream is deliberately excluded; it was still being written.
- `evidence/topology/`: byte-checked firmware excerpts and corroborated live
  channel/PCI identity, plus the archived PRCB bytes and their source hash.
- `evidence/*native*.txt`, `evidence/native-tests.txt`: actual-C ASan/UBSan tests,
  384 DMA bit faults, 336 topology/identity bit faults, bounded reset failures,
  candidate RAM proof/boundary tests, queue operations and traffic scheduling.
- `evidence/reset-replay.json`: independent first-reset replay, including
  image/module hashes, one ARM callback, packet checksums/streams, queue burst,
  exact held-reset register state and retained close. No extra firmware callback.
- `evidence/prior-replay.json`: previous 64-slot capture still validates.

Archive target paths are `scsi-drain/residentnet/`. Make a `residentnet` symlink
to that directory in an extracted archive root for the existing replay tools.
Keep each build beside its matching module/capture; do not mix archives.

## Measured findings

Channel metadata and direct private PCI configuration agree on `1000:000c`,
revision 2, MMIO `88000000`, BAR `fff00000`, SCRIPT BAR `fff02000`, one secondary
channel and no primary channel. The configuration-address selector was restored.

The first physical held-reset run completed 12,000 timer ticks and three
concurrent dual-stack rounds spaced 30 seconds apart. It recovered from a
96-packet TX-withheld burst (65 replies, 31 counted drops) and intentional TCP
loss. Snapshot readbacks stayed at primary command 2, secondary command 0,
BCR `242`, SACR `13ffc`, zero i960 DMA words and zero NMISR. Both task interrupt
continuations drained at the deadline. The host reboot returned without physical
intervention on boot `300d8383-5715-4256-a68d-89306713406b`.

The final link map contains 108,000 packet bytes, up from 98,304: 72 × 1,500
instead of 64 × 1,536. It leaves 2,256 unused mutable bytes with all existing
workspace, task stacks, interrupt stacks and guards retained. Cooperative
network storage defaults are unchanged. The final bounded probe completed
100 ticks, 33 callbacks, exact restoration and module unload.

The final resident run reached exactly 36,000 ticks with ten concurrent
IPv4/IPv6 rounds spaced 30 seconds apart. Its saturated queue returned 73
unique echoes and counted 23 drops, with high-water 72. Deliberately dropped
TCP data recovered. Both task interrupt continuations drained at the autonomous
deadline; further network operations were rejected while resources remained
retained for reboot.

Live cached NMI is `c004e190`, the stock error handler that can reinitialize the
secondary interface. Live PRCB is `feffd4d0`; the RAM-only probe declined to
follow it and emitted sentinel fault entries. **Those sentinels are not fault
table contents.** The paired programmed-ROM captures resolve this PRCB's fault
table pointer to `c0000800`. Nothing has changed these asynchronous paths.

## Thirty-step ledger

These are investigation, implementation and verification steps, not thirty
reboots. Broader-RAM gating is an explicit result, not claimed completion.

1. Inspect workspace, running service, boot ID and existing card owner.
2. Preserve isolation from the separate frame-queue experiment and its recovery.
3. Trace the primary-bus Symbios initialization path.
4. Trace the secondary-bus Symbios path and channel structure layout.
5. Trace the alternative BusLogic path without assuming it matches this card.
6. Check Intel's secondary-reset contract and specification update.
7. Implement fixed channel-topology diagnostic pages.
8. Cross-build and run the 28-page bounded probe; restore/unload.
9. Implement a narrowly addressed PCI identity read with selector restoration.
10. Run and archive the 29-page bounded probe.
11. Corroborate one secondary 53C895 against metadata and PCI configuration.
12. Implement bounded held-reset sequencing and native failure tests.
13. Test actual identity-admission code against 336 bit mutations.
14. Add the opt-in reset build and resident-only irreversible transition.
15. Prove its unchanged bounded entry/return path on the card.
16. Run the first 12,000-tick held-reset resident test.
17. Exercise spaced concurrent IPv4/IPv6 traffic and TCP retransmission.
18. Fill/drain the queue and verify exact replies plus counted drops.
19. Copy/replay the exact build and reboot from held reset.
20. Inspect the live cached NMI vector and trace stock reinitialization.
21. Resolve the ROM PRCB from paired preserved firmware captures.
22. Implement/test an offline fixed-range RAM-transfer policy; keep live grant closed.
23. Expand useful queue storage to 72 MTU-sized slots within the grant.
24. Test actual queue wrap, full, backpressure and oversize paths at all layouts.
25. Verify the complete linked RAM map and remaining guard margin.
26. Run the final 31-page/100-tick bounded probe and verify restoration.
27. Run/replay the longer spaced resident network test with transaction journaling.
28. Archive before reboot, then restore/check cooperative public IPv6 HTTP.
29. Update findings, Claude instructions and the narrative with the remaining gates.
30. Verify artifact/index hashes and commit source, binaries and captures.

## Next hardware boundary

Install and validate exclusive NMI/fault containment before transferring firmware
cache data to RTEMS. Include a controlled fault test that cannot resume stock
SCSI initialization. Audit surviving monitor memory dependencies, then test one
fixed guarded range for capacity, aliasing and integrity. The current
`ram_transfer.h` describes those evidence requirements but is not called by
live code. Do not treat held reset, low software counters or this candidate
address as an external-memory grant.

## Recovery and production

The final held-reset reboot returned without physical intervention on boot
`1e938df7-c454-479f-8e64-8ec7f754831e`. The cooperative `i960-http6` service
was restarted with the existing visitor log. A request from the Mac returned
HTTP 200 and the 2,891-byte Darth Vader/status page at the published IPv6
address. The response headers/body are preserved in `evidence/http-after-scsi.*`.
The full native suite passed after the final verifier edits. Both physical
held-reset runs, all bounded probes and the prior capture pass independent replay.
