# Final-close and driver-removal fault tests

2026-10-11: the final test module passed six hardware runs, three final-user-fd
closes and three sysfs driver unbinds during active callback/control syscalls.
The target is the unchanged, previously pinned `mustop` image. No reboot or
flash programming was required. [Evidence](../../artifacts/irq-lifecycle-20261011/README.md).

## What was injected

**Final user descriptor close:** a worker enters the callback through raw
`write(fd, request)`. Another worker enters the STOP ioctl on that same fd.
The test waits for the kernel's control-entry stamp, then closes the sole user
fd while both syscalls remain active. There is no spare dup alias. `/proc/self/fd`
confirms the descriptor disappeared; kernel syscall references still own the
file. Final `release` does not run until the control ioctl and callback write
finish. It then acquires the session mutex, restores RAM/MU state, and leaves
captures accessible through the driver's remaining device reference.

**Driver removal:** with both syscalls active, a third host thread writes the
PCI address to `/sys/bus/pci/drivers/dac960rtems/unbind`. Remove enters and blocks
on the session mutex. The controller exchange and callback finish first. Remove
then acquires the mutex, closes/restores the session, marks it removed and
unmaps the BAR. The still-open file keeps the experiment object alive. An ioctl
on that descriptor returns EAGAIN without BAR access; a read returns EIO. The
test captures all immutable evidence, closes that descriptor, observes final
object-release entry and disappearance of debugfs, and unloads the module.

This is logical Linux driver removal with a powered, responsive card. Physical
hot-unplug, surprise power loss and PCI bus faults were not tested.

## Measured ordering

Every row below is the same in all three corresponding final runs. Numbers
are atomic event-order stamps, not milliseconds.

| Event | Final-close runs | Unbind runs |
| --- | --- | --- |
| Write transaction enters under session mutex | 1 | 1 |
| Control ioctl claims window | 2 | 2 |
| Remove enters | — | 3 |
| Control ioctl reaches unlock/return | 3 | 4 |
| Writer closes and joins control window | 4 | 5 |
| Writer reaches session unlock/return | 5 | 6 |
| Remove acquires session mutex | — | 7 |
| Final release enters / acquires session mutex | 6 / 7 | 12 / 13, after unbind |
| Close starts / confirms clean restoration | 8 / 9 | 8 / 9 |
| Removed flag / BAR unmapped | — | 10 / 11 |
| Final object-release entry | after later module unload | 14 |

The instrumentation stamps function boundaries; the unlock/free immediately
following a stamp is not itself a timestamped instruction. The tests also verify
blocked futures, driver symlink disappearance, late-operation refusal, debugfs
removal and successful module unload rather than relying on stamps alone.
In the unbind case, final release does not run a second hardware cleanup:
the close stamps remain 8/9 after the last fd closes.

Target STOP/drain ticks were 51 for all final-close runs, and 52/51/51 for the
unbind runs. Each report has zero context/guard faults, both ISR continuations
drained, matching entry/return counts, preserved register sentinels and a
successful RELEASE handshake. Paired full 512 KiB staging restoration and the
execution/table/flash comparisons all passed, as did MU word/mask/pending-bit
restoration. Production IPv6 HTTP returned 200 after restart.

## Test instrumentation and the discovered diagnostic defect

`build_lifecycle_transport.py` derives the pinned concurrent driver. It adds a
read-only `lifecycle[16]` module parameter with atomic event-order stamps. It
preserves the session → control lock order and existing resource-retention gates.
For removal evidence, debugfs capture destruction moves from `remove` to the
final `session_free`; capture storage stays alive with the experiment's kref.
The BAR and DMA teardown retain their existing placement after session cleanup.
This diagnostic retention is specific to the test module.

The first instrumented run passed final close. The first unbind then exposed a
log-publication defect: `session_close()` appended its successful record, but
remove did not update the exported debugfs blob length. The verifier correctly
rejected that truncated `result.txt`. Event stamps and the kernel log showed
restoration had completed. Raw paired captures were independently rechecked in
a temporary copy with the separately saved kernel close line; the original
truncated file was preserved. The already-unbound module unloaded normally.

The final test module calls `session_log_end(d)` after removal cleanup and before
marking the object removed. All six reruns then passed using the unmodified
raw exported logs. `initial.tar.xz` retains the failed capture, v2 module, kernel
close line and recovery-verification note. `live.tar.xz` contains the final v3
module and six complete passing captures. Initial attempts are not counted
among those six passes. This was a diagnostic export failure, not evidence of
incomplete card restoration.

## Event array layout

Indices 0–13 are: write entry, control claim, remove entry, release entry,
control-window join, write finish, remove-lock acquisition, close start,
clean-close completion, removed flag, BAR unmap, release-lock acquisition,
final object-release entry, and control unlock/return. Indices 14–15 are unused.
Each used slot has one writer per tested lifecycle; this is an experiment trace,
not a general-purpose event log for repeated operations.

## Reproduce

Stop production and verify its complete close capture first. Use a fresh output
directory because the generator deliberately refuses an existing directory.

```sh
python3 project/rtems/switch/build_lifecycle_transport.py \
  --payload mustop/kernel.bin --out lifecycle-module
make -C /lib/modules/$(uname -r)/build M=$PWD/lifecycle-module modules
sudo python3 project/rtems/switch/live_lifecycle.py --payload mustop/kernel.bin \
  --module lifecycle-module/dac960rtems.ko --reader control-prototype/read_mu \
  --output lifecycle-live
```

From repository root, offline:

```sh
make -C rtems test
python3 rtems/switch/verify_lifecycle_capture.py artifacts/irq-lifecycle-20261011/live.tar.xz
```

The native ordering tests reject 13 early cleanup/join violations and check
capture retention, log publication and conservative failure-retention hooks in
the generated module. The archive verifier checks exact target/prepared-image/
module identities, ordering, original paired response bytes, complete close
captures and MU snapshots for all six final runs.

## Remaining limits

This establishes successful STOP/RELEASE concurrent with final user-fd close
and orderly driver unbind. Failed/stalled control exchanges during removal,
process termination with no completing control thread, physical disappearance,
and arbitrary non-cooperative task containment remain separate tests. The task
loops still check a stop flag. No resident firmware takeover, disk-I/O guarantee
or new DMA networking is implied. The next useful gate is controlled failure
of the concurrent exchange during teardown, retaining resources on uncertainty,
before choosing a safe policy for tasks that ignore STOP.
