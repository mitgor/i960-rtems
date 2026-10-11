# Resident resource ownership and safe cancellation

2026-10-11. This is a separate `ownership` RTEMS 4.6.6 profile: the same
RTEMS instance, task IDs, guarded stacks, mutex and ledger persist across bounded
host callbacks. It establishes resource rules before combining them with the
asynchronous containment experiments in `../switch/`. Production remains autonet.

## What owns what

The owner task holds a real priority-inheritance binary mutex and stages a
transactional update. The waiter blocks in the RTEMS mutex queue. A third task
uses independent state and can continue when that dependency is quarantined.
The supervisor controls admission and cancellation requests; it cannot unlock
the owner's mutex. The target has no timer, interrupt handler or device DMA in
this profile and executes at CPU interrupt level 31.

RTEMS 4.6.6's `semcreate.c` sets `only_owner_release` for priority-inheritance
mutexes. Plain FIFO/priority binary semaphores do not have that guarantee.
`coremutexsurrender.c` checks the releasing task before decrementing the nesting
count or handing the mutex to a waiter. The experiment deliberately calls
release from the supervisor and requires `RTEMS_NOT_OWNER_OF_RESOURCE` (23),
with holder, nesting count, owner resource count and waiter queue unchanged.
The original pinned source files accompany the artifacts.

The ledger contains an owner epoch, phase, committed/staged values, one software
reference, a monotonically increasing ticket, acknowledgements and counters.
This single-resource prototype has one owner and one dependent waiter; it is not
a general dependency-graph implementation. Task deletion and stack freeing are
forbidden. A clean retired owner may restart on its existing stack and task ID
only after the real mutex has no holder and the waiter has completed.

| State | Permitted transition | Required evidence |
|---|---|---|
| IDLE | BEGIN → HELD | Current epoch, actual owner acquires mutex |
| HELD | CANCEL → CANCEL | Stop admitting leases; retain mutex and staged state |
| CANCEL | Owner checkpoint → RETIRED | No external software reference; rollback then owner release |
| HELD | Owner commit → RETIRED | No reference; publish value then owner release |
| RETIRED | RESTART → IDLE | Owner suspended, resource count zero, mutex free, no pending waiter; advance epoch |
| CANCEL | QUARANTINE | Suspend owner and dependent waiter; keep mutex and their stacks intact |
| QUARANTINE | Complete outstanding reference | Exact epoch and ticket; no unlock/restart/resume |
| IDLE/RETIRED/QUARANTINE | FINALIZE | No external references; all workers suspended; callback returns |

Rollback/commit and the real mutex release run inside one dispatch-protected
section. The waiter can observe the committed value only after that section.
The supervisor waits for the owner's acknowledgement and for retirement before
allowing restart. Repeated cancellation is idempotent. Old epochs, wrong tickets
and duplicate completions cannot release a current reference. Neither epoch nor
ticket may wrap; exhaustion requires a new instance.

A reference here is a **software lease**, not evidence of physical DMA completion.
A real device integration must acquire references before submission and release
them only after a verified completion or reset/drain acknowledgement.

## Quarantine and final disposal

Quarantine preserves the unresolved transaction, owner mutex, blocked waiter,
RTEMS objects and task stacks. Stack hashes must remain unchanged across later
callbacks while the unrelated task advances. The quarantined tasks cannot be
restarted or resumed. This tests the retention policy for a refusing owner; it
does not inject an arbitrary-instruction runaway into this bounded profile.

Finalization is different from releasing that lock. It ends the entire private
RTEMS instance after all workers are suspended, software references are zero,
and execution returns to stock firmware. There are no live target timers, DMA
engines or external object users in this profile. Only then may the host restore
the saved RAM image. A quarantined object is never handed back to a surviving
client or allocator. A future resident system needs explicit reservation and
real external-I/O lifetime rules before using this terminal-disposal argument.

The host module pins the exact prepared target image. It marks ownership open
before a possible target entry. The decoded 64-word response gate checks the
sequence, epoch, actual mutex/task state, stack guards, dispatch/ISR depth and
terminal suspension. After valid finalization, further requests are rejected.
An early close keeps ownership open and refuses restoration even when the
firmware callback itself has finished and no command is pending. The ordinary
transport's pin path retains dirty workspace, DMA buffer, BAR mapping and module
reference until reboot. Never force-unload that failure state.

## Build and run

From a remote working directory with the pinned archives in `sources/`:

```sh
python3 project/rtems/build.py --work . --profile ownership
python3 project/rtems/ownership/build_transport.py --out ownership-module --payload ownership/kernel.bin
make -C /lib/modules/$(uname -r)/build M="$PWD/ownership-module" modules
sudo python3 project/rtems/ownership/live.py --payload ownership/kernel.bin --module ownership-module/dac960rtems.ko --output ownership-live --cycles 20 --runs 3
```

Stop the production service and verify its full close first. Use fresh output
directories. `live_refusal.py` intentionally leaves the session pinned; save its
captures before rebooting. It must never be followed by another test in that
boot. Ordinary runs always reach FINALIZE before closing their descriptor.

`python3 rtems/ownership/test_policy.py` is offline only. `verify.py` replays
recorded requests through the exact C policy under ASan/UBSan and checks actual
reports through the kernel's C acceptance predicate, including damaged copies.
It also verifies recorded binary identities, response traces, immutable bytes,
paired final captures, and full normal-close restoration. See the artifact
README for reproducible archive verification commands.

## Results and remaining work

See [the 16-step ledger](BATCH.md) and
[original builds and captures](../../artifacts/rtems-ownership-20261011/README.md).
The initial smoke run and three 20-cycle sessions passed, followed by a
premature-close retention test. A post-reboot run preserves the finalization
log separately because the transport resets that log during close; the earlier
original reports and successful cleanup remain independently verifiable.

Next, combine this exact ownership contract with the owned interrupt-stack
containment profile: hold a real mutex while interrupted, admit cancellation
through the independent channel, and defer the owner checkpoint until both the
critical-section and reference gates permit it. Start with a known dependency
pair and an unrelated task. Preserve quarantine on timeout. Then test multiple
resources and dependency closure, real host-buffer leases with completion
acknowledgements, and firmware RAM/interrupt/DMA reservation. Permanent interrupt
masking, corrupted scheduler state, memory isolation, unrestricted resident
preemption and physical DMA cancellation remain unproven.
