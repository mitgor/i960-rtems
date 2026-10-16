> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# STOP in critical sections and omission deadlines — 2026-10-11

Twelve runs passed on the installed card: three fresh module/upload sessions for
each of four cases. STOP at dispatch depth 2/1 remained deferred until the outer
release; missing STOP reached the 128-tick deadline; missing RELEASE exhausted
its finite instruction-loop budget and returned the expected `0x4000` flag.
No unexpected context/guard faults. Every run drained its ISR continuations,
restored paired 512 KiB staging, execution/table/flash and MU state, and unloaded.
Original IPv6 Vader service returned HTTP 200 after restart. No reboot/flash writes.

| Case | Final ticks, three runs | STOP ticks (0 means absent) | Callback latency ms |
| --- | --- | --- | --- |
| 1 | 40,40,40 | 18,18,18 | 286.03–288.60 |
| 2 | 40,40,40 | 30,30,30 | 286.51–288.26 |
| 3 | 128,128,128 | 0,0,0 | 708.46–710.49 |
| 4 | 35,35,34 | 35,35,34 | 677.59–683.30 |

Cases 1/2: READY at 17/29, STOP at 18/30, inner release at 28, outer release and
controller wake at 40, wake depth zero. Twelve IRQs observed at each critical
level, 24 pending-switch observations, no owner/depth/nesting violations. B's
entries stayed at 8 through both levels; final A/B entries/returns were 32/8.
A runs its assembly sentinel probe after the critical section; B stays in its
sentinel loop throughout the critical hold.

Case 3: host writes no STOP; target reports no accepted token, event status 6
(`RTEMS_TIMEOUT`), 128 ticks, 64 entries/returns per worker, and zero fault flags.
Host sends RELEASE after DRAINED. Case 4: host writes STOP but no RELEASE;
release budget is zero and the only flag is `0x4000`. Host observes callback
completion and validates the expected response before allowing cleanup.

## Preserved evidence

- `live.tar.xz`: target ELF/bin/map/disassembly, objects/library/generated
  headers, exact generated host module sources and binary, twelve full raw
  report/upload/close sets, MU snapshots, pending-command logs, build/run logs
  and the remote sources used for the build.
- `source.tar.xz`: final local switch sources, build scripts, native/live tests,
  verifier and profile documentation.
- `acceptance.json`: decoded reports copied from the live archive.
- `native-tests.txt`: passing full `make -C rtems test`, including ASan/UBSan host
  omission models and expected-outcome cleanup gates.
- `verification.txt`: exact image identities, twelve raw reports, full cleanup,
  MU comparisons and 102 corrupted reports rejected. Original STOP1 and deferral
  archives were also reverified with the updated decoder.
- `http-restored.txt`: normalized HTTP response after production restart.

No visitor statistics or visitor IP logs are included. Artifact inventory and
SHA256SUMS cover these files.

Verify from repository root:

```sh
python3 rtems/switch/verify_cases_capture.py artifacts/irq-stop-cases-20261011/live.tar.xz
```

## Scope and remaining limits

[Implementation, wire layout and reproduction](../../rtems/switch/STOP-CASES.md).
This demonstrates individual message omissions with the host still observing
and completing cleanup. It does not test a vanished host, a stopped CPU,
permanent interrupt masking or safe cancellation of arbitrary code. The workers
still check a stop flag; the host hook still holds the existing session lock.
The 128-tick bound depends on delivered timer IRQs; the RELEASE bound is a finite
instruction loop, not a calibrated real-time deadline. Concurrent user control,
non-cooperative task containment, resident ownership and DMA remain future work.

Exact SHA-256 from the live archive:

```text
66c9499588a9e65d23640f80db7d8b130ff861d414a108b775545b3860e6364a  stopcases/kernel.bin
a8f8f16b9568453bc2eb7f32c4218a2445d207b186aadb57dead5088d9bf3b44  stopcases/kernel.elf
5626fb93ff27e12a19bd4a8c18f9e06fe8d8583146f824e44896e3b8a8cba8ad  stopcases-module/dac960rtems.ko
```
