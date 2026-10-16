> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Exclusive RTEMS takeover — preserved evidence

[Contract](../../rtems/exclusive/README.md), [30-iteration ledger](../../rtems/exclusive/BATCH.md),
[research and remaining ownership gates](../../rtems/exclusive/RESEARCH.md).

| Archive | Preserved experiment |
|---|---|
| `exclusive-v1.tar.xz` | Three bare monitor sessions: inventory, inactive DMA disable, bus-master/grant isolation; exact target/module and sources |
| `exclusive-v2.tar.xz` | Four bounded RTEMS sessions: 8 ticks baseline, DMA-disabled, isolated; 100 ticks isolated |
| `exclusive-v3-cap.tar.xz` | 100-tick regression and one-way resident 1,200-tick deadline; exact ELF/bin/disassembly/module/source and retained close |
| `exclusive-v4-stop.tar.xz` | Fresh-boot 100-tick regression and resident host STOP at tick 581; consumed-request host acknowledgement correction |
| `exclusive-production.tar.xz` | Actual pre-test production close and post-reboot original-RAM preflight/OPEN, production identity and launcher |

Extract each experiment archive into a separate directory: they intentionally
contain different versions at the same `exclusive/` pathname. v3 and v4 use the
same target binary; v4 changes host acknowledgement admission. The source
snapshots reflect their build/run time; final replay scripts and documentation
are in the repository.

Nine bounded sessions restored RAM and unloaded. Two resident sessions retained
memory/module by design; both had completed the original ARM firmware callback
before takeover. Independent frozen snapshots proved RTEMS progress, interrupt
frame drain and parked-state stability. They are not full post-resident RAM dumps.
No firmware readback command was sent after resident entry.

All archived runs replay with `rtems/exclusive/verify.py --root ROOT ROOT/RUN...`.
The `evidence/replay-v*.json` summaries preserve the actual checks; the two
resident reports reject 38 selected corrupted snapshot variants. The native
admission matrix covers 512 cases, plus generated-source retention guards.
The full RTEMS native suite passed. Raw captures retain their original formatting.

## Recovery and production

- Initial experiment boot: `3c5b99fb-e6a3-4bab-8df2-fdd16e43b1d9`.
- After deadline run: ordinary `systemctl reboot` did not return promptly over
  SSH; the user subsequently restored access. Fresh boot
  `f4e3a34e-fc67-4fac-a631-447cf99b29cd` passed the original-RAM and bounded tests.
- After STOP run: `systemctl reboot --force` returned over SSH without another
  physical-access request. New boot `926ae76c-6a22-45fb-bd0c-e2cf93556afc` had the
  test module absent and card unbound.
- Production `autonet` was restored at `http-after-exclusive`. Original RAM,
  service state and external IPv6 HTTP 200 were verified. This is one successful
  forced reboot, not proof of reliable unattended recovery.

`verify_production.py EXTRACTED_PRODUCTION evidence/` replays those checks.
Live visitor statistics are excluded. No flash, disk, guessed SCSI MMIO, LBACR
or bus reset writes were performed. The installed stock-preserving flash patch
was not changed. The cooperative RTEMS/stock-firmware path remains available.
