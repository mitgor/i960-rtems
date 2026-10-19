# Accele160 P3e: deliberate DMA suspension, timeout, then controlled resume

The profile-10 test on 2026-10-19 passed on Accele160 `0000:37:09.1`.
No flash was written. The diagnostic session was `20261019T030941Z`, boot
`1f283763-10b6-4aeb-834f-08292362efbd`, under
`/home/mit/i960-dma-resume-20261019`.

Diagnostic kernel SHA-256:
`e9cb1c8233d319b1b553c351bef8d0e55eb4f4408fa38ea9579770b3399daa86`.
Both pre-test firmware reads match
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

The owned fault handler received real `faulte` while DMA0 was deliberately
suspended. It exhausted 10000000 CSR polls with CSR `0x400`, CCR 0, DAR
`0xc0821000`, NDAR `0xc0821020`, BCR 65040 and DCR 7. That original timeout
record remained unchanged. The one-shot gate then set CCR.CE; the finite chain
completed after 1843705 further polls, with CSR 0, CCR 1, final DAR
`0xc0829000`, NDAR/BCR 0 and DCR 7. Host trigger-to-report time was about
3.217 seconds, not a guaranteed hardware deadline.

All source/chain fingerprints, independently visible odd pages, peer registers,
stack guards and allocator ownership checks passed. The guarded host target
contained the complete 64 KiB pattern and final 32-byte marker after the
configured 64 MiB finite chain. The second target stayed untouched. The payload
proves final delivery, not an independent byte counter for every repeated copy.
STOP and denied ordinary module unload preserved the terminal record. After the
host owner exited, buffers still matched byte-for-byte, pins remained retained,
and admission remained `done=0 released=0 submitted=1`.

## Files and replay

- `prepared.tar.xz`: exact diagnostic bundle, including source and binaries.
- `tested.tar.xz`: exact bundle plus paired firmware reads, raw terminal records,
  destination buffers, visible source/descriptor pages, retention evidence and
  post-owner-exit audit.
- `tested-replay.json`, `hardware-state.json`: accepted evidence and registers.
- `native-tests*.txt`: local tests and Linux execution of actual diagnostic C
  with simulated MMIO (including gate refusal and second timeout).
- `previous-modes-replay.json`: profiles 6–9 still pass the current verifier.
- `resume-disassembly.txt`, `entry-and-loop-audit.json`: compiled CE-write and
  finite observer inspection; complete disassembly is in both bundles.
- `previous-final.tar.xz`: previous normal owner's clean shutdown capture.
  `previous-final-replay.json` validates only final STOP/retention evidence;
  its earlier full normal replay is in `accele160-stalled-dma-20261018`.

Replay from repository root:

```sh
python3 rtems/accele160/fault/verify_dma.py artifacts/current/accele160-dma-resume-20261019/tested.tar.xz
```

See [design](../../../rtems/accele160/fault/DMA-RESUME.md). This is one
controlled fault-path resume of a deliberately suspended, healthy DMA engine.
It does not establish NMI-path resume, arbitrary fault/PCI retry recovery,
wall-clock timeout on a blocked bus, task restart, abort or reclamation without
reset. Normal profile 5 remains the service baseline.

## Reset recovery and restored prompt

The reset returned without physical assistance. Normal session `20261019T031433Z`
on boot `f191f6f8-c1ae-4ce3-aee1-9e02024cf6ba` passed two fresh firmware reads,
64 captured frames, 5045 WAD reads and 685 external console exchanges with
zero errors. Maximum recorded card console reply latency was 2809.846 ms.
`restored-live.tar.xz` contains the original qualified profile-5 bundle,
this session and `restored-console.json`. `restored-replay.json` validates it;
`recovery.json` links the diagnostic boot to the fresh firmware pair.
`restored-prompt.txt` and `restored-services.txt` show verified idle, no zone
loan, the working prompt and active streaming gateway. Run:

```sh
python3 rtems/accele160/fault/verify_runtime.py --live artifacts/current/accele160-dma-resume-20261019/restored-live.tar.xz
```

Use `./rtems-console` in the project on the Mac, or `~/rtems-console` on the
Linux host. The service remains running; this archive captures a live session.
