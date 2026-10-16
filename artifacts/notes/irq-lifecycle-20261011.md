> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Final-close and driver-unbind evidence — 2026-10-11

The final module passed six card runs: three final-user-fd closes and three
sysfs unbinds during active callback and STOP ioctl syscalls. Zero target
context/guard faults. Full paired RAM, execution/table/flash and MU restoration
passed; every module unloaded. IPv6 HTTP returned 200 after restart. No reboot
or flash programming. The target was the unchanged `mustop` image.

## Results

- Final-close runs: the sole user fd disappeared while both calls held kernel
  file references. Control exit → window join → write finish → final release
  → session restoration. STOP/drain at tick 51 in all three runs.
- Unbind runs: remove entered while control was active and blocked on the
  session mutex. Control exit → window join → write finish → remove acquired
  lock → restoration → removed flag → BAR unmap. STOP/drain ticks 52/51/51.
- After unbind, retained-fd ioctl/read returned EAGAIN/EIO. Closing that fd
  reached final object release without repeating hardware cleanup; debugfs
  disappeared and the module unloaded.

[Event order, implementation and limits](../../rtems/switch/LIFECYCLE.md).
The test covers orderly Linux driver removal on a powered card, not physical
hot-unplug. It uses completing STOP/RELEASE exchanges; failing control concurrent
with teardown, host disappearance and non-cooperative task containment remain open.

## Captures

- `live.tar.xz`: target build, final v3 module and generated sources, successful
  build/run logs, six raw reports, input blocks, exact image identities, complete
  paired close captures, MU snapshots and lifecycle stamps.
- `initial.tar.xz`: first instrumented v2 module and two initial hardware
  attempts. Final close passed; the initial unbind capture was rejected because
  remove failed to publish the updated log length. Its original truncated
  result, kernel close line, final event stamps and recovery verification remain
  preserved. These attempts are not counted among the final six passes.
- `source.tar.xz`: final local switch-profile sources, generators, tests,
  verifiers, Makefile and documentation.
- `acceptance.json`: summary copied from the six final captures.
- `native-tests.txt`: passing full RTEMS suite, including 13 negative lifecycle
  order checks and generated retention/log-publication assertions.
- `verification.txt`: final raw/paired reports, exact image hashes, lifetime
  ordering and complete restoration; independent recheck of the initial raw
  restoration with the separately saved kernel close line in a temporary copy.
- `http-restored.txt` and `service-state.txt`: production HTTP and service state.

The first unbind did restore the card: kernel log and complete raw comparisons
confirm that. The v3 fix publishes the debugfs log length after remove's cleanup.
The final six runs pass without substituting or augmenting any raw log. Capture
retention after unbind is test-only and lasts until the experiment's final kref.
No visitor statistics or visitor IP logs are included.

```sh
python3 rtems/switch/verify_lifecycle_capture.py artifacts/irq-lifecycle-20261011/live.tar.xz \
  --initial artifacts/irq-lifecycle-20261011/initial.tar.xz
```

Exact live-image SHA-256 values:

```text
3bf5d5e4c0fe0b7ef5af58d25510ad77e3cbfa9f18d2d31a414807e875a2029d  mustop/kernel.bin
742a15b3c7a91b8dedce7b3f804a3f1352355dc52ffd4467bbb79e96b0bb0a98  lifecycle-module-v3/dac960rtems.ko
```
