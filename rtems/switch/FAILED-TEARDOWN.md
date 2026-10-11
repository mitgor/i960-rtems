# Failed control during teardown

**2026-10-11 follow-up:** [STOP-ignoring worker containment](CONTAINMENT.md) passed
three card sessions: external suspension, retained live ISR stacks, restored
timer and full cleanup after callback return. This is one-shot instance disposal,
not permanent-interrupt-mask recovery or resident resource-safe cancellation.
Earlier next-step statements below describe their historical checkpoints.

2026-10-11: two hardware tests passed, one final-user-fd close with STOP omitted,
and one driver unbind with RELEASE omitted. Both deliberately leave the module
pinned and require reboot. No flash was programmed. See the
[evidence bundle](../../artifacts/irq-failed-teardown-20261011/README.md).

## Injection and scope

`build_failed_teardown.py` derives the lifecycle/concurrent driver and uses the
unchanged pinned `mustop` target. Read-only `fail_control=1` omits STOP after READY;
mode 2 sends STOP, observes DRAINED, then omits RELEASE. Each branch reports
`-ETIMEDOUT` through the existing control-error path. Invalid modes fail probe
before device access. A 200 ms delay in the inherited test control path lets
both syscalls enter before the harness closes the sole user fd or starts unbind.

These are synthetic host-control failures on a responsive, powered card, not
physical PCI timeouts. The target retains its finite event/release deadlines.
In both captures ODB eventually reads `00000001`: the completion bit became
visible, but the driver did not consume completion after control failure. The
result is deliberately conservative software uncertainty. We do not infer a
valid target response, restored memory, or a permanently stalled processor.

## Measured behavior

| Observation | Omitted STOP + final close | Omitted RELEASE + unbind |
| --- | --- | --- |
| Control ioctl / callback write errno | ETIMEDOUT / ETIMEDOUT | ETIMEDOUT / ETIMEDOUT |
| Pending, execution dirty, staging dirty, runner uncertain | all 1 | all 1 |
| STOP started / clean | 1 / 0 | 1 / 0 |
| Pinned / owned after final release | 1 / 0 | 1 / 0 |
| Removed / driver bound | 0 / yes | 1 / no |
| DMA pointer / BAR pointer retained | yes / yes | yes / yes |
| Module reference count | 1 | 1 |
| DMA free, BAR unmap, region release, object-free stamps | all zero | all zero |
| Successful restoration stamp / commands after injection | zero / none | zero / none |
| Ordinary `rmmod` | refused: module in use | refused: module in use |

The complete retention snapshots remain identical one second after the refused
unload. Debugfs evidence also remains accessible. These are instrumented driver
state and control-flow checks, supported by the actual unload refusal; we do not
probe freed memory or issue additional firmware commands to prove retention.

The event arrays are respectively:

```
[1,2,0,7,4,6,0,5,0,0,0,8,0,3,0,0]
[1,2,3,10,5,7,8,6,0,9,0,11,0,4,0,0]
```

Indices 0–13 retain the [lifecycle](LIFECYCLE.md) meanings. This derived module
uses 14 for DMA-free entry and 15 for PCI-region-release entry. Both stay zero.
The writer joins the control window before close is attempted; close refuses
restoration because STOP is not clean. Final release waits for the syscall
references. Unbind waits for the session mutex, marks removed, and leaves the
pending/dirty experiment intact. The base experiment/device and explicit module
references keep its state alive. No forced unload, rebind or manual restoration
is attempted after failure.

`retention[16]` records, in order: pending, execution dirty, staging dirty,
runner uncertain, STOP started, STOP clean, pinned, removed, owned, control
window, control done, negated control errno, DMA pointer present, BAR pointer
present, completed steps, injection mode. Snapshots hold the session mutex and
never dereference DMA or BAR memory. Read these after the operations have joined;
the parameter array is a diagnostic snapshot, not a general atomic telemetry API.

## Reproduce and verify

Stop the web service and verify its successful full close first. Use one case
per fresh boot. The harness deliberately does not call `Board.close()` after
failure: that would misrepresent retained captures as successful cleanup.

```sh
python3 project/rtems/switch/build_failed_teardown.py \
  --payload mustop/kernel.bin --out failed-teardown-module
make -C /lib/modules/$(uname -r)/build M=$PWD/failed-teardown-module modules
sudo python3 project/rtems/switch/live_failed_teardown.py \
  --payload mustop/kernel.bin --module failed-teardown-module/dac960rtems.ko \
  --mode 1 --output failed-close
# Copy evidence off the machine, reboot, verify a different boot ID and no module.
# Run mode 2 with --output failed-unbind, copy evidence, and reboot again.
```

`Board` now accepts optional module arguments, recorded in `request.json`;
existing callers keep their previous default. Native tests reject 16 damaged
retention snapshots and check generated injection/retention gates. Offline:

```sh
make -C rtems test
python3 rtems/switch/verify_failed_teardown.py \
  artifacts/irq-failed-teardown-20261011/close.tar.xz --case close
python3 rtems/switch/verify_failed_teardown.py \
  artifacts/irq-failed-teardown-20261011/unbind.tar.xz --case unbind
```

The verifiers match exact target, prepared-image and module hashes, errno,
ordering, retained state and logs. `retained/` contains failure diagnostics,
not paired successful close evidence. Recovery is separately established by
three distinct boot IDs, absence of the retained module, fresh board preflight,
paired original staging reads matching the pinned ROM, and restored IPv6 HTTP 200.

## Remaining work

The tested failure policy is to retain resources until reboot. This does not
establish in-session recovery, physical hot-unplug safety, indefinite callback
containment, arbitrary PCI faults, or shutdown of tasks that ignore STOP or keep
interrupts masked. The next preemption gate is a design for non-cooperative task
containment, with independently observable quiescence before memory reclamation.
Keep production HTTP on its existing bounded autonomous implementation.
