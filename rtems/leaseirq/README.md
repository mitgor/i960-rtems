# Continuous execution under a hardware lease

`leaseirq` runs preemptible RTEMS workers continuously inside a parked firmware
callback. Host grant, renewal and STOP use the independent MU control ioctl;
there are no returning host-driven execution epochs during an active lease.
The profile builds on `persistirq`'s owned IRQ stacks, full register preservation,
two-mutex dependency chain, persistent generations and terminal FINALIZE gate.

This is an **execution lease with firmware parked**, not unrestricted coexistence
with running stock firmware, full-board takeover, or DMA ownership. Each lease
has a 512-tick renewal deadline and a non-renewable 24,000-tick administrative cap.
At the observed approximately 208 Hz these are about 2.46 and 115.2 seconds.
The worker's old finite instruction budget now wraps; it exits only on its
checkpoint flag. The host no longer depends on a firmware STOP command.

## Explicit ownership contract

| Resource | Lease and evidence | Release / limitation |
|---|---|---|
| i960 execution | One outstanding callback, firmware continuation parked; driver session mutex held; no stock submissions during grant–QUIESCED | Return only after timer cleanup and independent RELEASE |
| RTEMS RAM | Existing guarded RIO reservation: code starts C0F2C000, private state C0F4C010–C0F9BFEF, upper guard C0F9BFF0 | Existing image snapshot/restore contract; no extra RAM or allocator claim |
| Timer 1 / cached F2 | Known idle start gate; vector 003C, reload/count 20000, map F80000, only core interrupt bit 2000 enabled | Stop and clear own pending bit; restore saved vector/mapping/mask before return |
| Firmware interrupt sources | Temporarily excluded by the tested core mask, including timer 0 delivery | Sources are not reprogrammed; accumulated pending work/time during the pause is a coexistence limit |
| MU message 1 | Driver-serialized IMR1/OMR1 protocol; IIMR=1FB and OIMR=FF checked on every tick | Exact cleanup after RELEASE and real callback completion |
| Host buffers / BAR / module | Existing kernel session ownership remains held throughout callback and control | Uncertain completion or missing terminal proof retains resources |
| Timer 0 | Firmware-owned; reload observed unchanged on every tick | No writes or mode-register reads; no claim of accurate stock time across a long pause |
| DMA / SCSI / PCI / NIC | **Not transferred**; no register writes, mapping changes or new descriptors | Existing idle-card experiment only; no storage traffic, physical DMA-drain or NIC-ownership proof |

The timer-register address/side-effect basis is the existing
[observational inventory](../autonomous/inventory.c) and
[hardware findings](../autonomous/README.md). The new read of timer-0 reload at
FF000300 is observational; TMR0 is never read. Existing timer helpers alone
perform timer-1 acquisition/restoration. Runtime checks also inspect ICON=6000,
the installed vector, timer-1 reload, both MU masks and timer-0 reload. A drift
sets a fault and prevents acceptance; it does not repair unknown hardware state.
These checks detect relevant changes in this experiment, not arbitrary malicious
privileged code or every asynchronous bus master.

The protocol acknowledgement documents the cooperative monitor/host handoff;
it is not evidence that stock firmware implemented a new reservation API.
The firmware continuation is still outstanding and must eventually return.

## Protocol and failure behavior

The BIO request remains `{0x31515250,generation,operation,argument}`. Async
operations 1 CLEAN, 2 QUARANTINE and 3 FOLLOW require argument zero. Synchronous
STATUS/COMPLETE/FINALIZE/ADMISSION retain the persistent profile's contract.
As in `persistirq`, an invalid asynchronous generation/state is not a recoverable
pre-entry admission error: it can return without READY and cause fail-closed
retention. General API use still needs host-side generation/phase admission.
One 352-word (1408-byte) report contains the old 320-word resource proof plus
32 lease/hardware words. The exact-image-pinned host gate validates both parts.

The same eight-word ioctl `0xc0204d03` supports these actions:

| Action | Transition |
|---|---|
| 0 STATUS | Read current sideband state; does not renew |
| 2 GRANT | READY 71xxxxxx → grant 61xxxxxx → acknowledged 62xxxxxx, using BIO sequence |
| 3 RENEW | Host monotonic 16-bit sequence in 63xxxxxx → matching 64xxxxxx |
| 1 STOP / release | STOP 72xxxxxx → QUIESCED 75xxxxxx → RELEASE 74xxxxxx |

The driver rejects stale epochs, renewal before grant, and duplicate grants
before writing hardware. Target renewal must be exactly the next sequence;
duplicate observations do not extend the deadline. Expiry wins over renewal at
the same tick. Renewals cannot extend the administrative cap. Host STATUS traffic
alone cannot keep the lease alive.

On expiry the controller cancels clean work or contains the known resource
chain, drains Other, restores the timer and publishes QUIESCED. The host may
acknowledge an already-quiesced expiry with RELEASE. This is proven when the host
continues observing the control channel. If the host disappears entirely, the
bounded RELEASE wait/failure path can retain the instance; an unplugged-host
recovery claim is not made. The callback wait is increased to 125 seconds only
for the explicitly leased callback; all other firmware command waits are
unchanged. A timeout is an error requiring retention, never an ownership grant.

The report preserves reason (1 host STOP, 2 renewal/grant expiry, 3 runtime cap),
grant/renew/stop ticks, renewal count, maximum gap, rejected tokens, tick-by-tick
hardware-check count, drift count, expected active mask/map/vector, saved vector,
timer reloads, RAM bounds and control masks. Follow leases preserve the original
A/B/C stacks and trapped IRQ continuation while Other continues. FINALIZE still
requires zero software references and proven suspension; it disposes of the
instance without force-unlocking the quarantined tasks.

## Build and reproduce

```sh
python3 rtems/build.py --work /path/to/work --profile leaseirq
python3 rtems/leaseirq/build_transport.py --out /path/to/new-module \
 --payload /path/to/work/leaseirq/kernel.bin
make -C /lib/modules/$(uname -r)/build M=/path/to/new-module CC=gcc-12 modules
python3 rtems/leaseirq/test_native.py
make -C rtems test
```

On the prepared host, stop the production service and verify the **current**
output directory's full close, then invoke `live.py --payload ... --module ...
--output NEW_DIRECTORY`. Add `--matrix --soak 60` for expiry, host-silent,
dependency and sustained tests; `--cap-only` exercises the full administrative
limit while renewing. Never load this image with the ordinary session module.

See [the batch ledger](BATCH.md) and
[archived binaries and captures](../../artifacts/rtems-leaseirq-20261011/README.md).

## Next ownership gates

1. Distinct long-lived monitor entry that does not keep a firmware command
   outstanding; requires a real firmware reservation or explicit takeover.
2. Inventory and quiesce **all** DMA/SCSI/watchdog users before claiming exclusive
   board ownership or extending memory. An idle sample is not a transfer.
3. Firmware-time accounting and pending interrupt handling across long pauses;
   test storage only under an explicit disposable-media scope.
4. Resident control disconnect/unbind/fault matrix and longer soak. This batch's
   expiry/release proof does not replace full disappearance/teardown testing.
5. Physical host-buffer DMA leases with verified completion before unmapping;
   then network queues. Linux retains NIC and routing ownership meanwhile.

Privileged loops that mask the timer, corrupt the monitor or its stacks remain
outside containment guarantees. Keep production on bounded `autonet`.
