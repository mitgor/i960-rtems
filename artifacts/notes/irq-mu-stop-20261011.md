> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Independent MU STOP with two live interrupt contexts — 2026-10-11

Three `mustop` hardware runs passed. The host sent STOP through IMR1 while
firmware command sequence 1 remained pending. At STOP, both task-owned ISR
continuations were live. Each worker then observed its stop flag, finished
register/deep-stack checks, and suspended. Both interrupt contexts drained;
the timer was restored before DRAINED acknowledgement. Host RELEASE permitted
MU cleanup and callback return. The host completion doorbell was checked clear
before STOP and before accepting DRAINED.

| Host delay after READY | STOP tick | A entries/returns | B entries/returns | Callback latency |
| --- | --- | --- | --- | --- |
| 120 ms | 34 | 17/17 | 17/17 | 257.20 ms |
| 150 ms | 41 | 21/21 | 20/20 | 293.14 ms |
| 200 ms | 52 | 26/26 | 26/26 | 348.19 ms |

All context/guard faults zero; controller wake was the STOP event, not the local
deadline. Full paired 512 KiB staging and execution/table/flash restoration,
MU words/masks/pending bits and module unload passed. The original IPv6 Vader
service returned HTTP 200 after restart. No reboot or flash programming occurred.

## Files

- `live.tar.xz`: ELF/bin/map/disassembly, generated headers/objects/library,
  generated module sources/binary, three raw reports and complete upload/close
  captures, MU snapshots, host pending-command logs, exact run identities,
  target/driver build logs and the remote source snapshot.
- `source.tar.xz`: final local build scripts, switch profiles, STOP1 native/live
  tests, offline verifier and documentation.
- `acceptance.json`: readable copy of all three decoded reports.
- `native-tests.txt`: passing full RTEMS suite, including ASan/UBSan STOP1 host
  and target simulations and generated exact-image/retention gates.
- `verification.txt`: raw reports, exact payload/prepared-image/module hashes,
  pending-command evidence, complete close and MU restoration, 42 deliberately
  corrupted report fields rejected.
- `http-restored.txt`: normalized production HTTP response after restart.

Visitor statistics and visitor IP logs are excluded. The artifact inventory
and SHA256SUMS cover these files. The initial build-only failure used an absent
historical `rtems_task_self` symbol; final source uses the controller object ID.
The initial error log is retained; no failed image was uploaded.

Verify from the repository root:

```sh
python3 rtems/switch/verify_stop_capture.py artifacts/irq-mu-stop-20261011/live.tar.xz
```

## Limits and next step

See [STOP1 implementation and contract](../../rtems/switch/STOP.md). This is a
one-shot host-driver hook under the existing session lock, not a concurrent user
ioctl or the earlier framed CTL1 protocol. The stop-aware workers do not yield
the CPU voluntarily but do cooperate in termination. Arbitrary non-cooperating
task cancellation, STOP inside nested critical sections, resident ownership,
network DMA and hardware fault-injection of missing-host deadlines remain open.
The native failure models do not substitute for those hardware tests.

Next combine STOP with nested dispatch deferral and bounded deadline tests,
then design concurrent control and non-cooperative task containment.

Exact SHA-256 from the live archive:

```text
3bf5d5e4c0fe0b7ef5af58d25510ad77e3cbfa9f18d2d31a414807e875a2029d  mustop/kernel.bin
771b90c73bda019dd242a7adb3ceb87ad148f2776bc97fc5e9a1e0f13d52b599  mustop/kernel.elf
f084a13c00400d62a27cb0de93a76c69d7cd007dfbf8e1d46f5775c71a6343b0  mustop-module/dac960rtems.ko
```
