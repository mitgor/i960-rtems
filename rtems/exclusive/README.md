# Exclusive RTEMS execution — experimental, reboot to leave

This profile implements **exclusive CPU execution with unused PCI engines
isolated**, after the setup firmware callback has returned. A resident mode never
resumes the parked firmware continuation. STOP or the target deadline drains the
two RTEMS worker interrupt frames and parks the processor. Reboot/power-cycle is
the exit path. The user explicitly authorized this mode on 2026-10-11.

This does not establish complete ownership of every board engine or arbitrary
DRAM. See [research and limits](RESEARCH.md), [30-iteration ledger](BATCH.md) and
[evidence](../../artifacts/rtems-exclusive-20261011/README.md).

## Results

Nine bounded sessions restored RAM and unloaded. Six of these ran real RTEMS
workers, totaling 324 hardware timer ticks. Two one-way resident sessions passed:

| Resident case | Timer ticks | Exit | Result |
|---|---:|---|---|
| Deadline | 1,200 | Local 12-second nominal deadline | Both workers drained; all 1,200 IRQ continuations returned; parked |
| Host STOP | 581 | Independent host control | All 581 IRQ continuations returned; parked |

Both resident sessions rejected firmware writes after entry, rejected malformed,
stale and repeated-entry controls, retained allocations on close, and reported
unchanged worker state in subsequent parked snapshots. Neither resumed firmware.
The first reboot did not return promptly over SSH; the user restored access.
The second, forced reboot returned over SSH and production IPv6 HTTP was restored.
Reboot recovery is therefore not a proven unattended recovery method.

## Two separate future paths

| Path | Execution and ownership contract |
|---|---|
| Exclusive (this directory) | Firmware initializes hardware; uploaded RTEMS takes the CPU, denies unused PCI bus mastering/grants and retains the original allocation. Reboot exits. |
| Cooperative/coexistence | Preserve `autonet`, `handoff`, `leaseirq`, `persistirq`, `ownirq` and their evidence. Reversible ownership contracts must preserve stock service and task/resource lifetime. |

The existing profiles are not removed or repurposed. Production HTTP remains on
`autonet`. Its host relay depends on firmware callbacks and cannot simply be
pointed at the resident profile. Resident networking needs a replacement data
transport before lwIP/HTTP can run in this mode.

## Hardware transition

ARM creates the RTEMS instance, installs the existing owned-stack timer entry,
and **returns**. The host waits for the completed callback before sideband entry.
The initial firmware IRQ frame remains parked on the owned monitor stack.

Phase 0 only observes; phase 1 writes zero to CCR0/1/2 after admitting six zero
DMA control/status words. Phase 2 also clears primary/secondary ATU command bit 2
and sets SACR external-master priorities to disabled. Readbacks are required.
Primary memory decode remains enabled so the independent host message channel
continues working. No descriptor, guessed SCSI register, flash, LBACR or bus reset
is written. Active/error DMA is refused; no abort/drain of active hardware is claimed.

A dedicated second ISR uses the existing two task-owned stacks and lifetime
checks. Two non-cooperating counting workers run with hardware time slicing.
The controller wakes on deadline or STOP, sets a stop flag, lets both workers
finish their suspended ISR continuations and validates stack guards/lifetimes.
Resident mode then masks interrupts and serves read-only status while parked.
It never calls `engine_release` or returns to stock firmware.

Bounded mode is a transition rehearsal: drain, restore engine controls, return
through the original monitor frame, HALT, diagnostic callback, verified STOP and
full RAM restoration. It remains available for regression testing.

## Host protocol and retention

Same eight-word ioctl `0xc0204d04`: action, epoch, argument, five zeros. Actions
0–3 retain the bounded monitor semantics. Added actions:

- 4: irreversible resident entry; response `8B:epoch`.
- 5: read word 0–63 of a frozen snapshot; value returned in word 2, response
  `92:index:epoch`.
- 6: STOP RTEMS workers (idempotent while parked), response `94:epoch`.
- 7: capture snapshot, response `95:epoch`.

Tokens include the 16-bit session epoch. The driver checks no pending firmware
command and sequence 1 before entering; marks resident **before** publishing the
request; disables ordinary writes; and retains memory on close even after a
successful STOP. Resident acknowledgements additionally require IMR1 consumed
(zero), so a previous identical reply cannot acknowledge an unconsumed request.
A read/copy failure cannot reverse the resident state. Uncertain operations
also disable the handle and retain resources. Never force-unload a retained run.

Snapshot v1 (64 words): magic `EXR1`, generation, state (1 running, 2 parked,
3 fatal quarantine), stop reason (1 host, 2 deadline), 32 RTEMS/lifetime words,
16 hardware words, runtime error, interrupt mask, actual/expected vector, epoch,
then seven zeros. Snapshot capture happens with interrupts masked; the host reads
that frozen copy. No firmware callback or DMA is used to fetch it.

## Reproduction

Requires the established remote toolchain, production cleanly stopped, and an
unbound card. `live.py` cleans up bounded runs; `resident.py` deliberately retains.

```sh
python3 project/rtems/build.py --work . --profile exclusive
python3 project/rtems/exclusive/build_transport.py --out exclusive-module --payload exclusive/kernel.bin
make -C /lib/modules/$(uname -r)/build M=$PWD/exclusive-module CC=gcc-12 modules
sudo python3 project/rtems/exclusive/live.py --payload exclusive/kernel.bin --module exclusive-module/dac960auto.ko --output NEW-BOUNDED --phase 2 --ticks 100
sudo python3 project/rtems/exclusive/resident.py --payload exclusive/kernel.bin --module exclusive-module/dac960auto.ko --output NEW-RESIDENT --ticks 6000 --stop-after 5
# Copy/verify captures before reboot. Power cycle may be necessary.
```

`--ticks` is 100 Hz nominal; the resident harness accepts 200–6000 ticks.
The application deliberately has a finite run limit and a stable parked state;
unlimited unattended execution is a future extension. Current workers honor
the controller's stop flag; this is not a new arbitrary-task cancellation proof.

Native gate tests: `python3 rtems/exclusive/test_native.py`. Extract each artifact
archive into its **own** directory and run `verify.py --root DIR DIR/RUN...`.
The verifier checks hashes, original RAM, raw ARM trace, no pending callback,
control replies, frozen snapshots, task IRQ drain and either restored or retained
close as appropriate. It is an offline verifier, not a runtime report gate.

## Next work

1. Establish the cache coprocessor completion contract and secondary in-flight
   transaction drain before broad memory reuse or active-I/O takeover.
2. Diagnose warm-reboot behavior and provide a reliable cold-reset route.
3. Add an owned resident host-memory ring transport with strict mapping lifetime;
   migrate console and lwIP only after bounded DMA pattern tests and drain proofs.
4. Extend duration, payload/task loading and resource containment in exclusive
   mode. Keep cooperative stock-service ownership research independently viable.
