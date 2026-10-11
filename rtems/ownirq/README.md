# Asynchronous ownership and cancellation

The `ownirq` profile integrates the [ownership policy](../ownership/README.md)
with the [owned interrupt-stack containment path](../switch/CONTAINMENT.md).
It uses the same real RTEMS 4.6.6 priority-inheritance binary mutex, but the owner
and unrelated worker now execute at CPU priority 20 and are preempted by timer
F2. Each has its own 8 KiB IRQ area and lifetime record. A third task waits on
the mutex at priority 31 and never enables interrupts; it needs no IRQ slot.
The controller runs at RTEMS priority 1 and CPU priority 31. All three workers
have RTEMS priority 2; this test requires owner-only release but does not claim
new evidence of priority boosting (the earlier ownership profile covers that).

The independent host ioctl sends STOP while the firmware callback is still
running. READY identifies the selected critical interval, so STOP is immediate.
The timer records STOP and wakes the controller. It never releases a task's
mutex, completes its lease, or edits an original interrupted frame.

## Cancellation and dependencies

The owner starts a transaction, acquires the mutex and one software lease, then
starts the waiter. The waiter blocks in the real mutex queue. The owner and
unrelated task execute the deep-call assembly probe with register/condition-code
sentinels and a finite one-million-iteration emergency ceiling.

In clean modes, the controller requests cancellation only after it can safely
run outside dispatch-disabled sections. A private checkpoint flag permits the
owner's probe to return through its original ISR continuation. The task validates
the complete register roundtrip and drained IRQ lifetime, then polls its own
cancellation checkpoint. Retirement is deferred while its software reference is
outstanding. The controller observes that deferral, waits another two ticks,
and completes the exact generation/ticket. The owner rolls back and releases
its mutex inside one dispatch-protected section, acknowledges and suspends itself.
The waiter sees the old committed value, writes its own value, releases and
suspends. No supervisor unlock or forced stack unwind occurs.

In quarantine modes, the controller never grants the owner's checkpoint. It
observes four more ticks of progress despite STOP, then suspends the owner and
blocked waiter. The mutex, incomplete transaction, original interrupt frame and
both task stacks remain allocated. Restart/finish are rejected. The unrelated
worker continues for another four ticks using its own interrupt area. Owner task
and IRQ hashes, waiter stack hash and owner progress remain unchanged throughout.
Only then is the unrelated worker suspended and the borrowed timer restored.
Both workers' live ISR frames remain live in quarantine; they are not called
drained or modified to synthesize a return.

All modes also attempt a wrong ticket, an old generation and a non-owner unlock.
Successful-reference modes reject a duplicate completion. The real RTEMS release
returns `RTEMS_NOT_OWNER_OF_RESOURCE` (23) with the owner's lock intact.

## Test modes

| Mode | STOP window | Owner outcome | Reference at final report |
|---|---|---|---|
| 1 | Dispatch depth 2 | Owner checkpoint, rollback, waiter handoff | 0 |
| 2 | Dispatch depth 1 | Owner checkpoint, rollback, waiter handoff | 0 |
| 3 | Ordinary preempted execution | Owner + waiter quarantine | 0 |
| 4 | Dispatch depth 2 | Owner + waiter quarantine | 0 |
| 5 | Ordinary preempted execution | Owner + waiter quarantine | **1: host must retain** |

Modes 1/2/4 keep the nested critical section for 12 timer observations per depth.
IRQ delivery continues but dispatch waits for the outer enable. The blocked
waiter cannot observe the staged update. Quarantine after a critical section
also demonstrates that deferral and dependency preservation compose.

## Reclamation boundary

The target restores timer registers/vector/mask, verifies guards, task state,
frame ownership, zero dispatch/ISR nesting and 10,000 stable observations, then
sends **QUIESCED**. Host RELEASE allows the callback to return and MU state to be
restored. This is execution quiescence, not permission to free a leased resource.
The host's separate 256-word report gate checks ownership/reference state before
setting `stop_clean` or restoring any borrowed RAM.

Mode 5 intentionally returns a valid quiescence report with one unresolved
software reference. Its host gate returns ENODATA after the real callback has
completed, keeps `stop_clean=0`, and retains dirty RAM, DMA allocation, BAR mapping
and module reference even though pending/runner-uncertain are both zero. Ordinary
unload must fail. Save captures before reboot; never force-unload or retry on
that retained state. No actual DMA engine is active: the lease tests the lifetime
contract needed before a real external device may be added.

Normal disposal ends this entire one-shot borrowed RTEMS instance. The unrelated
task continues during the containment interval, not indefinitely after returning
to firmware. This does not add cancellation to the production webserver, reserve
firmware RAM/DMA/interrupt ownership, implement dependency closure for arbitrary
lock graphs, or recover from permanent interrupt masking/corrupted scheduler
state. There is no task memory isolation. Production remains bounded autonet.

## Build, run, verify

Use pinned sources and tools as for the existing RTEMS profiles. Stop production
and verify its full close first. Always use a new module/output directory:

```sh
python3 project/rtems/build.py --work . --profile ownirq
python3 project/rtems/ownirq/build_transport.py --out ownirq-module-new --payload ownirq/kernel.bin
make -C /lib/modules/$(uname -r)/build M="$PWD/ownirq-module-new" modules
sudo python3 project/rtems/ownirq/live.py --payload ownirq/kernel.bin --module ownirq-module-new/dac960rtems.ko --reader control-prototype/read_mu --output ownirq-new
# This next run deliberately retains resources and requires reboot afterward:
sudo python3 project/rtems/ownirq/live_refusal.py --payload ownirq/kernel.bin --module ownirq-module-new/dac960rtems.ko --output ownirq-refusal-new
```

`make -C rtems test` is offline. `test_gate.py` exercises the exact C acceptance
predicate under ASan/UBSan; `verify.py` checks saved binary identities, paired
responses, original control records, immutable guards, actual report rejection
mutations, full normal RAM/MU restoration or failure retention. It truncates
failure blobs to their recorded populated 471,136-byte span; the allocated tail
is not presented as a measurement. Raw captures are preserved.

See [the step ledger](BATCH.md) and
[builds, captures and measured results](../../artifacts/rtems-ownirq-20261011/README.md).
