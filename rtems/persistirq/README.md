# Persistent asynchronous epochs and dependency closure

`persistirq` keeps one RTEMS instance alive across host callbacks, including a
quarantined task's original interrupt continuation. Within an epoch, timer F2
preempts A and Other on their separate owned interrupt stacks. Between callbacks,
the timer/vector/masks are restored and RTEMS does not execute. Continuous
execution alongside the firmware is still a separate ownership problem.

## Resource contract

Four workers and two real priority-inheritance mutexes form a chain:

- A owns R0 and holds one software completion lease.
- B owns R1 and blocks on R0.
- C blocks on R1.
- Other has no edge to the chain.

The bounded graph computes transitive dependants. Freezing A closes admission to
A/B/C (mask 7), excluding Other. Adding A→R1 would close a cycle and is rejected
without mutation. Existing waiters may receive locks after a clean rollback;
new acquisitions by a cancelled task are refused. Both real mutexes reject the
controller's attempted release with RTEMS status 23. The graph is checked against
actual RTEMS states, holder IDs, nesting and resource counts.

Clean cancellation waits for A's IRQ return and lease completion, rolls back its
staged change, then permits B and C to take their locks and finish. All four
workers suspend; later clean epochs restart the same IDs/stacks only after live
IRQ frames and mutex ownership are absent. Generations and lease tickets prevent
stale completion from acting on a later epoch.

Quarantine keeps A's live IRQ frame, both mutexes and B/C wait relationships.
Four stack/IRQ hashes remain identical across firmware returns. Later epochs
restart only Other, which can repeatedly enter and leave its own IRQ stack.
Completing A's lease does **not** unlock or restart the quarantined chain.
FINALIZE ends the entire experiment once references are zero, every task is
suspended and the timer is restored. Host cleanup also requires proven callback
completion. This disposes of the instance; it does not recover its mutexes.

## Protocol

Each input is four little-endian uint32 words: magic `0x31515250`, resource
generation, operation, argument. BIO sequence is the independent MU nonce.
The first command must create an epoch. The output is 320 words (1280 bytes),
validated by the exact-image-pinned host module's `report.h`.

| Operation | Generation / argument | Result |
|---|---|---|
| 0 STATUS | current / 0 | State without clock advancement |
| 1 CLEAN | next / 0, 1 or 2 | Plain or nested-critical STOP, rollback and handoff |
| 2 QUARANTINE | next / 0, 1 or 2 | Freeze A/B/C, retain lease and IRQ frame |
| 3 FOLLOW | current / 0 | Run Other while A/B/C remain frozen |
| 4 COMPLETE | current / ticket | Release one software reference |
| 5 FINALIZE | current / 0 | Terminal proof; BUSY while references remain |
| 6 ADMISSION | current / 0 | STATE in quarantine; no restart mutation |

Statuses: OK=0, STALE=1, BUSY=2, STATE=3. Operations 1–3 require concurrent
READY/STOP/QUIESCED/RELEASE control through a second host thread. Synchronous
operations do not arm control. The live harness tests invalid generations with
synchronous commands: an invalid asynchronous request lacks READY and is not a
recoverable protocol operation in this prototype. Closing without FINALIZE
retains the image, BAR, DMA buffer and module even after a clean STOP. Do not
force unload or issue more card commands after that refusal; save evidence and
reboot.

The report includes stable IDs, stack/ledger addresses, graph edges, actual
mutex state, lifetime entry/return counters, full register probes, critical
section timing, generation/start counters and quarantine hashes. `ownership`
contains eleven serialized words: copy 44 bytes, never the padded i960 struct.

## Build and verification

```sh
python3 rtems/build.py --work /path/to/work --profile persistirq
python3 rtems/persistirq/build_transport.py --out /path/to/new-module \
  --payload /path/to/work/persistirq/kernel.bin
make -C /lib/modules/$(uname -r)/build M=/path/to/new-module CC=gcc-12 modules
python3 rtems/persistirq/test_native.py
make -C rtems test
```

On the prepared, unbound card host, with the production relay stopped and its
close verified, run `live.py --payload ... --module ... --output NEW_DIRECTORY`.
`--sessions 3 --clean 8 --follow 6` runs the main matrix. `--early-close` is an
intentional resource-retention test requiring a reboot afterwards.

`verify.py --root ARTIFACT_ROOT PATHS...` validates archived traces, paired
captures, image/module hashes, actual C acceptance logic, cross-callback
identity and quarantine invariants, restoration or retained-close evidence, and
47 damaged variants of every actual report. Native graph tests exhaust 32,400
combinations against independent reachability and use ASan/UBSan.

See [the completed batch](BATCH.md) and
[the archived evidence](../../artifacts/rtems-persistirq-20261011/README.md).

## Remaining work

1. Host admission state for all async operations, including recoverable rejection
   before entering the card; test stale sequences and concurrent duplicate calls.
2. Variable bounded graph capacity, multiple references per task, and dependency
   types beyond these two explicitly instrumented mutexes. Track queue/buffer
   ownership and completion provenance; do not equate a software lease with DMA.
3. Persistent-session timeout, unbind and failed-control fault matrix. Earlier
   one-shot fault coverage is useful but does not prove the new lifecycle.
4. A firmware reservation/takeover contract before leaving RTEMS interrupts armed
   between callbacks. Timer masks, shared RAM, commands, disk I/O and all DMA
   must have explicit ownership before unrestricted resident execution.

This profile is an experimental RAM-only test. Production remains `autonet`.
