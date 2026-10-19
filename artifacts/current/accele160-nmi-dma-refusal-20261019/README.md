# Accele160 P3h: NMI source-evidence refusal and corrected retry

Profile 13 extends controlled resume refusal to the real host-doorbell NMI path.
After proper source acknowledgement and the first timeout it invalidates only
saved NISR evidence, invokes the real gate, restores the evidence, and retries
with the attempt latch intact. The actual MU acknowledgement, source bytes,
descriptors and hardware ownership are preserved.

## Artifacts

- `prepared.tar.xz`: exact diagnostic kernel, sources, inputs and manifest.
- `build.txt`, `native-tests*.txt`: build and native validation, including the
  actual NMI refusal C path with simulated MMIO and host evidence rejection.
- `previous-modes-replay.json`: previous diagnostic modes 6–12 still replay.
- `refusal-disassembly.txt`, `entry-and-loop-audit.json`: compiled saved-NISR
  flip/restore, acknowledgement gates, both calls and second bounded observer.
- `previous-final.tar.xz`: previous normal session `20261019T035012Z` clean
  shutdown; `previous-final-replay.json` checks final STOP/retention evidence.
  Its full live replay is in `accele160-dma-refusal-20261019`.

[Implementation and layout](../../../rtems/accele160/fault/DMA-REFUSAL.md#profile-13-nmi-source-evidence-refusal).
This is one invalid recorded NMI source and a latched retry, not an unknown
physical NMI source, arbitrary corruption, DMA abort or release without reset.
Both timeouts count completed MMIO reads; no wall-clock bound on a broken bus
is claimed. General stock SCSI/cache ownership remains a separate gap.

## Hardware result

Profile 13 passed in session `20261019T041205Z`, boot
`7028b527-0a73-4d75-bc67-8dbcd115fd73`, at BDF `0000:37:09.1`.
Kernel SHA-256: `7596eba4062c2c96a87b8e204a124b26cd9c14de1b20e57c731e700ed46a2e28`.
The two pre-test complete firmware reads match
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

Real NMI vector 248 and source 0x100 were acknowledged before the saved-source
injection. Recorded word 151 changed from 0x100 to zero, the actual resume gate
refused, and restoring 0x100 did not bypass the attempt latch. Both attempts
recorded 1. Core and independent PCI MU reads agree on the post-ack state:
IISR=3, IDR=0, IIMR=0x7b. Actual source acknowledgement was never corrupted.

Both 10000000-poll observers ended with CSR=0x400, CCR=0, DAR=0xc0821000,
NDAR=0xc0821020, BCR=65032, DCR=7. The 504-byte source prefix stayed stable;
the rest of the payload retained its initial bytes and no marker appeared.
The second target stayed untouched. Trigger-to-record time was about 4.988 s;
this is a measurement, not a bus-independent wall-clock guarantee.

Source and descriptor fingerprints, independently visible odd pages, stack and
host guards, peer registers and allocator ownership passed. STOP, denied ordinary
module unload and owner-process exit preserved the outstanding transfer and
host buffers. Admission remained `done=0 released=0 submitted=1`, with pins
retained. No flash writes, synthetic completion or resource release occurred.

`tested.tar.xz` contains the exact bundle, raw captures and post-owner-exit audit.
`tested-replay.json` and `hardware-state.json` summarize the evidence. The replay
reports reset recovery as false because that separate evidence follows the test.

```sh
python3 rtems/accele160/fault/verify_dma.py artifacts/current/accele160-nmi-dma-refusal-20261019/tested.tar.xz
```

## Recovery and normal prompt

The reset returned without physical intervention. `recovery.json` links the
NMI diagnostic to normal session `20261019T041732Z`, boot `bbefd6d3-016a-4c9e-8388-36a164e78fd4`,
and fresh paired complete firmware reads with the same expected hash.
Original normal kernel SHA-256 remains
`55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`,
from `/home/mit/i960-owned-runtime-20261018/bundle`.

Restoration passed 64 frames, 5045 WAD reads and 709 external console exchanges
with zero errors, plus the owned-state snapshots. Maximum observed console reply
latency was 2433.761 ms. `restored-live.tar.xz` contains that bundle, session and
`restored-console.json`; `restored-replay.json` verifies them. The prompt remains
at verified idle with its zone loan returned. Gateway 8088 returns HTTP 200;
see `restored-prompt.txt` and `restored-services.txt`.

```sh
python3 rtems/accele160/fault/verify_runtime.py --live artifacts/current/accele160-nmi-dma-refusal-20261019/restored-live.tar.xz
```

Use `./rtems-console` from the Mac project or `~/rtems-console` on Linux.
Next: consolidate P3 evidence and audit permanent stock SCSI/cache-engine
ownership before P4 general task ownership/cancellation. These controlled
resume/refusal cases do not close that separate hardware-ownership gate.
