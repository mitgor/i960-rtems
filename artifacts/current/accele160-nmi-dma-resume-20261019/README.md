# Accele160 P3f: controlled DMA resume through real NMI

Profile 11 extends the fault-path resume diagnostic to a real host-doorbell NMI.
The owner verifies the MU aliases and issues one PCI doorbell bit-31 write after
arming. The core requires vector 248, the exact injected source, its subsequent
mask/acknowledgement, and all existing timeout/ownership checks before setting
DMA0 CE. The host independently compares PCI MU registers to the core snapshot.

No flash programming, descriptor reload, additional DMA target, IISR write,
module force-unload, PCI unbind or resource reclamation is involved. Successful
DMA still leaves the firmware callback pending and allocations retained until
reset. Normal profile 5 remains the service baseline.

## Artifacts

- `prepared.tar.xz`: final diagnostic bundle with exact source, kernel and inputs.
- `build.txt`: initial kernel build and manifest. `final-bundle-validation.txt`
  records the refreshed host validator/manifest and native tests before launch;
  the kernel did not change during that refresh.
- `native-tests*.txt`: local validation and actual diagnostic C under simulated
  Linux MMIO, covering both resume profiles, refused gates and second timeout.
- `previous-modes-replay.json`: profiles 6–10 replay with the extended verifier.
- `resume-disassembly.txt`, `entry-and-loop-audit.json`: compiled NMI gates,
  single CE write and bounded poll loop. Complete disassembly is in the bundle.
- `previous-final.tar.xz`: prior normal session `20261019T031433Z` clean shutdown;
  its final STOP/retention checks are in `previous-final-replay.json`. Full live
  replay for that session is in `accele160-dma-resume-20261019`.

[Implementation and record layout](../../../rtems/accele160/fault/DMA-RESUME.md).
This is recovery of a deliberately suspended healthy finite chain. It does not
establish recovery from arbitrary NMIs, unresponsive PCI targets, endless retries,
blocked MMIO, task restart, DMA abort, release without reset, or complete exclusion
of stock SCSI/cache engines. Poll bounds count completed MMIO reads.

## Hardware results

The profile-11 test passed in session `20261019T033138Z`, boot
`e7e02beb-daea-49ca-9ece-9bf750840741`, under
`/home/mit/i960-nmi-dma-resume-20261019`. Diagnostic kernel SHA-256:
`85f1c7a85de27d91ebbf36f2c5b3c2ebed4441dc475d762f3f91380b5f69da87`.
The exact Accele160 BDF is `0000:37:09.1`; both firmware reads match
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

Actual NMI vector 248 entered with NISR 0x100, IISR 0xb, IDR 0x80000000 and
IIMR 0x73. After mask/acknowledgement the core and independent host PCI reads
agreed: IISR 3, IDR 0, IIMR 0x7b. No other MU bit changed in these snapshots.

The deliberate suspension remained CSR=0x400, CCR=0, DAR=0xc0821000,
NDAR=0xc0821020, BCR=65032, DCR=7 through all 10000000 timeout polls. After
one CE resume, 1843607 further polls reached CSR=0, CCR=1, final DAR=0xc0829000,
NDAR/BCR=0, DCR=7. Trigger-to-record time was about 3.226 s, not a hard deadline.
The old timeout and new completion are separate immutable record fields.

The host received the complete 64 KiB pattern and 32-byte final marker after
the configured 64 MiB repeated-source chain. This proves final delivery, not an
independent byte counter for every repeat. The second target stayed untouched.
Source/chain fingerprints, visible odd pages, peer registers, owned stack guards,
host destination guards and allocator ownership all passed. STOP, denied ordinary
module unload and owner-process exit left `done=0 released=0 submitted=1`, pinned
buffers, and byte-identical host contents. No memory was released before reset.

`tested.tar.xz` contains the exact bundle, raw captures and post-owner-exit audit;
`tested-replay.json` and `hardware-state.json` summarize the accepted evidence.
Replay from repository root:

```sh
python3 rtems/accele160/fault/verify_dma.py artifacts/current/accele160-nmi-dma-resume-20261019/tested.tar.xz
```

## Recovery and restored service

Both resets returned without physical intervention. `recovery.json` links the
diagnostic boot to normal session `20261019T033558Z`, boot `cfb5e186-651a-4666-bb83-a8e52779a87a`,
with a fresh pair of matching complete firmware reads. Normal kernel SHA-256:
`55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`.
The original bundle remains `/home/mit/i960-owned-runtime-20261018/bundle`.

Restoration passed 64 frames, 5045 WAD reads, 709 external console exchanges
with zero errors and three owned-state samples. Maximum recorded console reply
latency was 2466.754 ms. `restored-live.tar.xz` includes the exact normal bundle,
session and `restored-console.json`; `restored-replay.json` verifies them.
The prompt is left at verified idle with no zone loan. Gateway 8088 is active
and responds HTTP 200; see `restored-prompt.txt` and `restored-services.txt`.

```sh
python3 rtems/accele160/fault/verify_runtime.py --live artifacts/current/accele160-nmi-dma-resume-20261019/restored-live.tar.xz
```

Use `./rtems-console` in the project on the Mac, or `~/rtems-console` on Linux.
The next bounded test is hardware refusal of a deliberately invalid resume gate,
keeping CE clear and all outstanding DMA resources retained until reset.
