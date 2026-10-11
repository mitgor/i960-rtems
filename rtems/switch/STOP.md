# One-shot independent MU STOP during an active callback

**Follow-up:** nested critical-section STOP and both individual omission deadlines
now pass on hardware (three runs each). See [STOP cases](STOP-CASES.md) for the
new profile, expected timeout flag and exact limits. Earlier next-step statements
below describe the original STOP1 milestone.

2026-10-11: `mustop` passed three runs on the installed DAC960. This is a separate
bounded experiment compiled from `switch/app.c` with `I960_STOP_TEST`. Existing
production, `switch`, `defer`, and CTL1 control profiles remain separate.

## Exact contract

Input is three little-endian words: magic `31505453`, nonzero 16-bit nonce,
host delay in milliseconds (120–200). The nonce rejects stale tokens; it is not
authentication. Only IMR1/OMR1 and message-1 pending bits are touched. Both message
interrupts remain masked; timer F2 polls IMR1. No BAR RAM or new DMA is borrowed.

| Direction | Token | Meaning |
| --- | --- | --- |
| Card → host | `71000000 \| nonce` | READY, published at timer tick 8 |
| Host → card | `72000000 \| nonce` | STOP, accepted once by timer ISR |
| Card → host | `73000000 \| nonce` | DRAINED: both workers and ISR continuations finished, guards checked, timer restored |
| Host → card | `74000000 \| nonce` | RELEASE, permitting MU cleanup and callback return |

The host waits for READY then delays as requested. Its command completion
doorbell must remain clear before STOP and while waiting for DRAINED. It sends
RELEASE only after DRAINED. It does not acknowledge a firmware completion early.

STOP sets the existing worker stop flag and sends an RTEMS event to the waiting
controller inside ISR/dispatch accounting. Scheduling happens after that
accounting unwinds. The controller lowers its priority, allowing both stop-aware
workers to resume and drain their interrupt contexts, finish register checks and
suspend. Only then does it restore the timer, check task/ISR guards and publish
DRAINED. RELEASE is polled at priority 31 with a finite loop budget. Target clears
message words and local IISR; host acknowledges OISR after callback completion,
paired payload verification and the target's MU-restoration marker.

No time advances after the timer is restored: matching stop/drained ticks prove
no further delivered timer ticks, not zero elapsed shutdown time.

## Host lifetime and bounds

`build_stop_transport.py` derives the standard `dac960rtems` transport and pins
its prepared payload SHA-256. A hook runs only for the actual execution command
(slot 41) after submission and before waiting for firmware completion. It keeps
the existing session lock throughout: there is no second ioctl, background host
thread, unlocked BAR access or change to remove/close serialization.

Once this hook starts, close refuses restoration until MU cleanup has succeeded.
Any exchange error retains the pending transaction/resources under the existing
module pinning rules. A clean normal report is not permission to skip full RAM
restoration. The target controller has a 128-delivered-tick event deadline;
workers and RELEASE polling also have finite instruction-loop budgets. Host
READY/DRAINED polls allow 800 sleeps each. These bounds are experimental, not
hard wall-clock guarantees, and a masked interrupt can prevent tick progress.

The missing-STOP event deadline and missing-RELEASE path have not been fault-
injected on hardware. Native ASan/UBSan tests cover target ownership refusal,
stale/duplicate stop tokens, event notification, release timeout and host
mask drift, premature firmware completion, nonce mismatch and both poll timeouts.
A mock does not establish hardware recovery from those failures.

## Evidence

| Host delay after READY | STOP tick | A entries/returns | B entries/returns |
| --- | --- | --- | --- |
| 120 ms | 34 | 17/17 | 17/17 |
| 150 ms | 41 | 21/21 | 20/20 |
| 200 ms | 52 | 26/26 | 26/26 |

All runs: both ISR lifetimes live at STOP, ISR nesting/dispatch accounting 1/1
at observation, zero context faults, successful controller event (not timeout),
DRAINED at the same tick, and nonzero RELEASE loop budget. Host firmware sequence
was 1 and pending at READY and DRAINED. Paired 512 KiB staging restoration, timer,
MU words/masks/pending-bit restoration and module unload passed. Callback latency
was 257.20–348.19 ms including host delay and verification. The IPv6 Vader page
returned HTTP 200 after restarting original production binaries. No reboot/flash.

The 816-byte result starts with the unchanged 736-byte switch report and appends
20 uint32 words named and checked in `live_stop.decode_stop()`.

## Reproduce

With production stopped and its full close captures verified:

```sh
python3 project/rtems/build.py --work . --profile mustop
python3 project/rtems/switch/build_stop_transport.py --payload mustop/kernel.bin --out mustop-module
make -C /lib/modules/$(uname -r)/build M=$PWD/mustop-module modules
sudo python3 project/rtems/switch/live_stop.py --payload mustop/kernel.bin \
  --module mustop-module/dac960rtems.ko --reader control-prototype/read_mu \
  --output mustop-live1
```

Offline, from repository root:

```sh
make -C rtems test
python3 rtems/switch/verify_stop_capture.py artifacts/irq-mu-stop-20261011/live.tar.xz
```

The verifier also rejects 42 deliberately damaged report fields. The original
build attempt referenced `rtems_task_self`, unavailable in this historical build;
the final code uses the executing controller's existing object ID. Both build
logs are preserved. No failed image was loaded.

## Remaining limitations

STOP1 is not CTL1: no framed status/retry service is claimed. Workers check a
stop flag; arbitrary non-cooperating task termination is unproven. STOP during
nested dispatch deferral is also not exercised by this profile. General interrupt
nesting, resident firmware takeover, disk I/O and network DMA remain outside scope.
Next combine STOP with critical-section deferral and controlled deadline tests,
then design concurrent user control and non-cooperative task containment.
