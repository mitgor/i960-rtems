# Critical-section containment and refusal after completion

This is the implementation record for the [15-step automatic sequence](AUTOMATIC-SEQUENCE.md).
The separate `containcases` target combines externally suspended workers with
the previously measured bounded nested dispatch-critical sections. Production
`autonet` remains on its existing bounded implementation.

## Critical sections: measured results

Six final sessions passed, three per depth, with the exact same target binary.
An initial six sessions also passed and are retained separately in the archive.
The extended 1024-byte report caused a Linux 1048-byte stack-frame warning in
the first module. The final generator allocates its temporary decoding array
with `kmalloc` and frees it before authorizing cleanup. Allocation failure
returns ENOMEM with `stop_clean` still false. All six cases were rerun with this
change; the stack-frame warning is absent in the final module build.

| Selected depth | READY | STOP | Controller wake | Outer enable returns | Containment |
| --- | --- | --- | --- | --- | --- |
| 2 | tick 17 | tick 18 | tick 40 | tick 41 | tick 44 |
| 1 | tick 29 | tick 30 | tick 40 | tick 41 | tick 44 |

All rows held across all three final repetitions. Each critical depth had 12
IRQ observations, giving 24 pending-switch observations. Task B stayed at eight
entries until outer release. The controller never ran while dispatch was
locked. Task A's outer enable remained suspended until tick 41 as the controller
and B ran. The controller then allowed four ticks of STOP-ignoring work before
externally suspending both tasks and restoring the timer.

A initializes its progress budget before entering the critical test and reaches
its assembly leaf only after outer release; its initial one-million budget is
not a measurement of earlier assembly iterations. B is already in its leaf.
Both budgets decrease during the controller's four-tick grace interval, then
stay unchanged through 10,000 checks. A retains 34 entries / 33 returns, B
10 / 9. Both live frames and complete task/ISR areas remain intact. All faults
are zero, and paired full RAM/MU restoration and ordinary unload pass.

`contain_cases_report.h` checks the critical report in addition to the unchanged
quarantine invariants. READY must identify the selected depth; STOP must fall
inside that depth's interval; controller execution must wait for tick 40;
containment must occur at tick 44. Its report is the 944-byte containment record
followed by the existing 80-byte critical-section record. A different pinned
module prevents accepting this layout as the earlier ordinary containment test.
The concurrent host sends STOP immediately after READY instead of applying the
ordinary 120–200 ms delay.

## Failure injections

`build_contain_failures.py` composes the unchanged containment transport with
the existing lifetime stamps and retention snapshot. The older generator defaults
remain unchanged. `fail_control` selects one of three host-only injections:

1. Omit STOP after READY while the sole user fd is closed. Control/write return
   ETIMEDOUT, and completion remains pending in software.
2. Omit RELEASE after QUIESCED while sysfs unbind is in progress. This tests
   retention despite a quiescence token: callback completion has not yet been
   accepted, so the token alone cannot authorize cleanup.
3. Complete the real control handshake and callback, read the paired original
   response, then invalidate only the local decoded containment marker before
   the normal cleanup gate. The raw capture and target memory remain unchanged.
   The ioctl succeeds but write must return ENODATA. Pending and runner-uncertain
   are cleared, while dirty memory and an unclean STOP must still force retention.

The harness closes the sole user fd with live syscalls (cases 1/3), or starts
unbind while the operations are active (case 2). It snapshots state after the
syscalls finish and after ordinary unload is refused. It never calls normal
restoration or forces an unload following an injected failure. Each failing
session requires evidence collection and a fresh reboot before the next one.

The omitted-STOP case does not establish successful target containment: neither
a valid QUIESCED report nor a validated callback response is obtained. The
one-million-iteration worker ceiling and 128-tick event deadline are separate
bounds; no claim is made about which target escape ran without a valid report.
These tests exercise software uncertainty on responsive hardware, not physical
PCI loss, permanent interrupt masking or arbitrary kernel corruption.

## Reproduce

Stop production and independently verify its complete close first. Use fresh
output/module directories. Do not start a second test on a pinned failure state.

```sh
python3 project/rtems/build.py --work . --profile containcases
python3 project/rtems/switch/build_contain_cases.py \
  --payload containcases/kernel.bin --out containcases-module-v2
make -C /lib/modules/$(uname -r)/build M=$PWD/containcases-module-v2 modules
sudo python3 project/rtems/switch/live_contain_cases.py \
  --payload containcases/kernel.bin --module containcases-module-v2/dac960rtems.ko \
  --reader control-prototype/read_mu --output containcases-live2

python3 project/rtems/switch/build_contain_failures.py \
  --payload contain/kernel.bin --out containfail-module
make -C /lib/modules/$(uname -r)/build M=$PWD/containfail-module modules
sudo python3 project/rtems/switch/live_contain_failures.py \
  --payload contain/kernel.bin --module containfail-module/dac960rtems.ko \
  --mode 1 --output containfail-1
# Copy and verify evidence locally, then reboot. Repeat for modes 2 and 3,
# with a fresh boot and output directory for each.
```

The failure module pins the earlier `contain/kernel.bin` tested in the original
containment milestone; the critical-section cases use their own new target.
Do not substitute an image rebuilt from later shared source without regenerating
its pinned module and revalidating it.

## Live retention results

Omitted STOP/final close and omitted RELEASE/unbind both returned ETIMEDOUT
from ioctl and write. Pending, execution dirty, staging dirty and runner uncertain
remained 1; STOP clean remained 0. DMA/BAR pointers, experiment lifetime and a
module reference remained retained. No free/unmap/region-release stamps fired,
no firmware submissions followed the injection, and ordinary `rmmod` was refused.
The state remained identical after the refusal. The unbind test additionally
removed the driver's public binding while retaining its private resources.
Both captures were copied locally and independently verified before reboot.


The invalid-report/final-close case also passed. Control ioctl returned success;
write returned ENODATA (61). Pending and runner-uncertain became 0, control-done
became 1, and the completed-step count became 1. Execution/staging dirty remained
1, STOP clean stayed 0, and module/DMA/BAR retention remained intact. Ordinary
unload was refused and the post-refusal snapshot was identical. No firmware
command followed the local corruption marker. Original paired bytes still pass
the unchanged containment decoder, including the matching nonce. This proves
the dirty/unclean gate retains resources independently of the pending flag.

| Injection | ioctl / write | Pending / runner uncertain | Dirty exec / stage | STOP clean | Pinned / DMA / BAR |
| --- | --- | --- | --- | --- | --- |
| Omitted STOP, final close | ETIMEDOUT / ETIMEDOUT | 1 / 1 | 1 / 1 | 0 | 1 / 1 / 1 |
| Omitted RELEASE, unbind | ETIMEDOUT / ETIMEDOUT | 1 / 1 | 1 / 1 | 0 | 1 / 1 / 1 |
| Invalid local report, final close | success / ENODATA | 0 / 0 | 1 / 1 | 0 | 1 / 1 / 1 |

Each failure intentionally retained resources until reboot. It is not a clean
in-session recovery. All three archives were saved and verified before their
respective reboots; no force-unload or flash programming was used.

## Validation and remaining work

The full RTEMS native suite passes. New native cases reject 40 damaged critical
reports and 18 unsafe retention snapshots. Each six-run critical archive rejects
240 damaged actual reports through both the Python decoder and exact C host gate
under ASan/UBSan. The original three-run containment archive still passes the
updated verifier. All failure archives match their target/prepared-image/module
hashes and preserve unmodified evidence. Final sources and exact binaries are in
[the artifact bundle](../../artifacts/irq-containment-batch-20261011/README.md).

The next design gate is resource ownership for resident execution: which tasks
may hold shared locks or own I/O, what the supervisor can revoke, and how hardware
quiescence is independently acknowledged before reclaiming memory. The present
contract discards an entire one-shot instance and cannot safely cancel an arbitrary
task inside a persistent shared runtime. Permanent interrupt masking, unbounded
critical sections and arbitrary memory corruption remain outside the tested
contract. Keep production network code on its existing bounded autonet profile;
these results do not yet authorize a resident takeover or direct NIC DMA.


### Failure-capture extent

The rejected-report branch returns before the usual success path narrows the
debugfs payload blob length. Its raw files therefore expose the 512 KiB capture
allocation, while the command log proves only the 471,136-byte response prefix
was read for step 1. The unused tail is not a live card-memory measurement.
The first offline verification incorrectly compared that tail with original
RAM and rejected it; the verifier now uses the recorded populated prefix and
original bytes outside that audit range, exactly as the bounded response check
requires. The paired prefixes and original decoded report pass. Raw files are
unchanged. No additional hardware transaction was issued to fill the unused tail,
and reboot was deferred until corrected verification passed.


## Final recovery

All three recovery reboots completed. Four distinct boot IDs are preserved and
matched to each failing request. After the last reboot the test module and driver
binding were absent. Production's fresh firmware preflight passed, both original
staging reads matched the pinned ROM hash, and the IPv6 Vader/system-info page
returned HTTP/1.0 200 OK. Production is again running with `dac960auto`; no test
module remains loaded. These are reboot recovery checks, not in-session cleanup
of the intentionally retained failure states.
