# Concurrent host control during a firmware callback

**2026-10-11 follow-up:** [STOP-ignoring worker containment](CONTAINMENT.md) passed
three card sessions: external suspension, retained live ISR stacks, restored
timer and full cleanup after callback return. This is one-shot instance disposal,
not permanent-interrupt-mask recovery or resident resource-safe cancellation.
Earlier next-step statements below describe their historical checkpoints.

**2026-10-11 follow-up:** [failed-control teardown tests](FAILED-TEARDOWN.md) now pass
on the card for omitted STOP/final close and omitted RELEASE/unbind. Pending
resources remain pinned; unload is refused and recovery requires reboot. This
covers synthetic control failure, not physical disappearance or non-cooperative
task containment. Earlier next-step statements below are historical.

**Follow-up:** final user-descriptor close and orderly driver-unbind fault tests
now pass on the card, three runs each. See [lifecycle tests](LIFECYCLE.md) for
ordering evidence, the diagnostic fix and remaining failure-path limits.

2026-10-11: three live sessions passed using the previously proven `mustop`
target image and a new, image-pinned `concurrent-module/dac960rtems.ko`.
A Python worker blocks in the callback's write/read transaction while a separate
host thread invokes the control ioctl on a duplicated descriptor of the same
open session. STOP is no longer injected by the execution-command wait hook.

## Interface

Private ioctl `0xc0204d03` uses eight uint32 words (32 bytes). Input: operation
0 for STATUS or 1 for STOP, nonce, then six zero words. Output:

| Word | Meaning |
| --- | --- |
| 0–1 | operation and nonce |
| 2 | firmware sequence captured when the control window opened |
| 3–4 | completion doorbell and OMR1 at initial ioctl observation |
| 5–6 | completion doorbell and DRAINED token before RELEASE (STOP only) |
| 7 | STOP handshake complete |

The ioctl is available on the already-open session file, including dup/fork
aliases. A second independent open still obeys exclusive session ownership.
Outside the active execution window it returns EAGAIN without accessing BAR.
Wrong nonce returns ESTALE; malformed operation/reserved words return EINVAL;
a second STOP after one has claimed the window returns EALREADY (or EAGAIN
if completion has already closed it). A timed-out/failed control exchange is
not replayed. Copy-out failure after successful RELEASE does not undo the
hardware operation; the window remains claimed.

STOP waits for READY, uses the request's bounded 120–200 ms experimental delay,
sends STOP, waits for DRAINED with the hardware completion bit still clear,
and sends RELEASE. STATUS is a snapshot; it is serialized behind an active
STOP exchange and is not a continuously available telemetry channel. This API
retains the experimental STOP1 tokens, not CTL1 framing or a resident monitor.

## Lock and lifetime contract

The write transaction retains `session_lock`, protecting ordinary read/write,
close and driver removal. After posting the actual execution command (slot 41),
it opens `control_window` under a new `control_lock`, copying nonce and firmware
sequence into control-owned fields. It then waits for firmware completion
without holding `control_lock`.

The ioctl takes only `control_lock`. It never acquires `session_lock`. The
one-way lock order is therefore session → control. On completion **or timeout**,
the writer takes `control_lock`, closes the window and waits for any active
ioctl to finish before logging completion, consuming the completion mailbox,
reading back output or starting cleanup. If the ioctl failed, or no handshake
completed, the writer retains the pending transaction and the existing module/
DMA resources. It does not infer cleanup permission from a timeout.

The ioctl and writer retain kernel file references; `.owner` retains the module
and the open session's kref retains the experiment object. Closing a dup alias
does not trigger final release while those references exist. Remove waits on
`session_lock`; when it can unmap the BAR, the window has already been closed
and joined. Late ioctls inspect only the retained object and return EAGAIN.
The shared debug log is touched by the ioctl only inside the window, while the
writer is polling; the writer joins it before touching the log again.

Physical hot-unplug, live driver unbind and final-descriptor close while both
syscalls are in progress were not fault-injected. The live close test closes
an extra alias while the original/active syscall references remain. Native
threaded tests exercise the exact ioctl body with the session mutex held by a
writer, stale/late/duplicate rejection, early-completion failure, copy-out
failure after RELEASE, and window joining. This is narrower than a kernel
lockdep/KCSAN proof of every lifecycle interleaving.

## Hardware results

Three sessions used delay values 120, 150 and 200 ms. Each observed:

- A STATUS ioctl with firmware sequence 1, READY token and no completion bit,
  while the callback worker's future was still pending.
- Wrong-epoch STOP rejected before any message write.
- Two overlapping STOP callers: exactly one STOP/DRAINED/RELEASE exchange in
  the kernel log; the competing call rejected.
- A dup alias closed during the exchange without ending the running callback.
- DRAINED received while firmware completion remained absent, then window
  closure/join before normal callback completion handling.
- Zero target context/guard faults; both owned ISR continuations drained.
- Full paired staging/execution/table/flash and MU restoration, module unload,
  and rejection of a late control request after callback completion.

No target firmware changes, reboot or flash writes were needed. The original
IPv6 Vader service was restored and fetched with HTTP 200. The target tasks
still cooperate by checking a stop flag; this does not provide forced arbitrary
task cancellation or recovery from permanent interrupt masking.

## Reproduction and evidence

Stop the production service and verify its close capture first. In the established
remote workspace:

```sh
python3 project/rtems/switch/build_concurrent_transport.py \
  --payload mustop/kernel.bin --out concurrent-module
make -C /lib/modules/$(uname -r)/build M=$PWD/concurrent-module modules
sudo python3 project/rtems/switch/live_concurrent.py --payload mustop/kernel.bin \
  --module concurrent-module/dac960rtems.ko --reader control-prototype/read_mu \
  --output concurrent-live1
```

Offline from repository root:

```sh
python3 rtems/switch/test_concurrent.py
python3 rtems/switch/verify_concurrent_capture.py artifacts/irq-concurrent-control-20261011/live.tar.xz
```

[Artifacts and exact results](../../artifacts/notes/irq-concurrent-control-20261011.md).
The next gate is broader lifecycle/failure testing of this API and an explicit
containment policy for non-cooperative tasks before resident ownership or DMA.
