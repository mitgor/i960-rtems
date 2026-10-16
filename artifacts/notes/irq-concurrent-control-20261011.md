> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Concurrent host-control milestone — 2026-10-11

Three live sessions passed with the unchanged `mustop` target and a new exact-
image-pinned concurrent host module. The callback transaction and STOP ioctl ran
in different host threads sharing an open file. Two competing STOP callers
produced one hardware exchange; stale and late requests were rejected.

| Run | STOP/drain tick | A/B IRQ entries (all returned) | Callback latency ms | Duplicate errno |
| --- | --- | --- | --- | --- |
| 1 | 36 | 18/18 | 268.09 | 114 |
| 2 | 41 | 21/20 | 291.34 | 114 |
| 3 | 51 | 26/25 | 339.06 | 114 |

All context/guard fault words were zero. Each run recorded a pending callback
at READY, no hardware completion at DRAINED, and a window close/join before
normal completion processing. Closing an extra descriptor alias did not stop
the active calls. Full 512 KiB paired RAM, execution/table/flash and MU state
restoration passed, followed by module unload. HTTP 200 from the IPv6 Vader
service confirmed the restored production service. No reboot or flash writes.

## Contents

- `live.tar.xz`: reused target build, generated concurrent module source/binary,
  build/run logs, three complete raw reports and upload/close captures, identity
  hashes, MU snapshots, kernel control logs and host concurrency observations.
- `source.tar.xz`: final switch-profile sources, concurrent driver generator,
  exact ioctl header, native/live tests, verifier and documentation.
- `acceptance.json`: decoded target reports copied from the live archive.
- `native-tests.txt`: native threaded ASan/UBSan tests of the exact ioctl body
  and generated join/image-pin/resource-retention assertions.
- `full-suite.txt`: passing full RTEMS suite.
- `verification.txt`: exact payload/prepared-image/module hashes, raw reports,
  concurrent control evidence, MU/full cleanup checks and 42 corrupt reports
  rejected.
- `http-restored.txt`: normalized HTTP response after restarting production.

Visitor statistics and visitor IP logs are excluded.

[API, lock order, lifetime contract and reproduction](../../rtems/switch/CONCURRENT.md).
The live descriptor-close test was an extra alias, not forced final release or
hot-unplug. Task cancellation remains cooperative; physical device removal,
permanent interrupt masking, full host disappearance, CTL1 framing and resident
ownership remain outside this result. Next: broader lifecycle/failure tests and
non-cooperative task containment.

```sh
python3 rtems/switch/verify_concurrent_capture.py artifacts/irq-concurrent-control-20261011/live.tar.xz
```

```text
3bf5d5e4c0fe0b7ef5af58d25510ad77e3cbfa9f18d2d31a414807e875a2029d  mustop/kernel.bin
842169706878b66ecdc970138077c45e4a576696f1e2dc8c8117d4c41a9a17ab  concurrent-module/dac960rtems.ko
```
