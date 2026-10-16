# Framed MU control and independent bounded STOP

The `muctl` profile implements CTL1 over IMR1/OMR1 and passed on the real card.
[Live evidence](../../artifacts/notes/mu-framed-20261011.md).
Production `autonet` and the earlier one-word `mu` experiment remain separate.

## Wire and ownership

One CTL1 request/response is 64 bytes each. The driver writes IMR1 and polls
OMR1; the timer ISR receives/sends 16-bit fragments. All frame storage is in the
uploaded image's private RAM. No BAR RAM, queue port or ATU mapping is borrowed.
Both message interrupts remain masked. Only message-1 pending bits are cleared.

| IMR1 word | OMR1 acknowledgement | Meaning |
| --- | --- | --- |
| C0gggggg | 3Fgggggg | Begin next transport generation (1 through FFFFFF) |
| A0iihhhh | 5Fiihhhh | Request halfword ii, ordered 0 through 31 |
| B0ii0000 | 4Fiihhhh | Fetch response halfword ii |
| D0000000 | 2F000000 | Halt timer after STOP and the last response halfword |

Each 32-bit CTL1 word is split low halfword first. Beginning a generation clears
partial request storage. Repeated unchanged tokens have no second effect; the
reply remains visible. A complete identical CTL1 sequence retry returns the
cached response. A changed duplicate is refused. The existing CTL1 checksum,
epoch, sequence and reserved-word checks run only after all 32 fragments arrive.
The epoch comes from the initial arm request and is random per acceptance run.
This is stale-message detection, not authentication or a security boundary.

Successful STATUS and STOP responses put the RTEMS tick counter in `value`.
PING echoes its argument. CTL1 heartbeat counts control ISR ticks until STOP.
Bad epoch/checksum frames do not consume a valid sequence. A retry is explicit;
the driver does not replay a timed-out exchange. After an exchange error it
refuses further ioctls, retaining the normal validated close path.

The private ioctl is `0xc0904d02`, 36 uint32 words: request[16], response[16],
transport generation assigned by the driver, halt flag, and firmware sequence
before/after. The session mutex serializes the entire transaction. Each fragment
has at most 100 polling pauses of 1–1.5 ms plus scheduling delay; a frame uses 65
fragments. The target has an absolute 3,000-delivered-tick budget (nominally 30 s),
then stops task dispatch and the timer. This watchdog does not run when interrupts
are masked. Timing is experimental and not a real-time wall-clock guarantee.

## STOP and lifetime

1. CTL_STOP runs in the bounded timer handler before RTEMS dispatch. It sets the
   task-dispatch gate; it never resumes a task to ask it to stop. The monitor
   keeps polling to deliver the response and subsequent STATUS/retry requests.
2. Final HALT disables/restores the borrowed timer through `stop_timer()` and
   publishes its acknowledgement. The current ISR still has to return.
3. **HALT is not permission to free code, stacks or DMA memory.** Driver close
   still performs the original firmware STOP transaction, validates timer/vector
   restoration, restores message words, acknowledges OISR from Linux, verifies
   all borrowed RAM, and only then unloads. The stock callback also establishes
   that the preceding interrupt continuation returned. Uncertainty retains memory.

This proves independent control and STOP for the current bounded background
profile. It does not prove STOP can interrupt a non-yielding level-31 task,
a firmware callback that never returns, or an arbitrarily suspended ISR.
The control timer has priority 30; current RTEMS task execution masks it.
No unrestricted preemption, new interrupt stack, network DMA or NIC peer DMA
is enabled by this change.

## Reproduction

Run offline tests with `python3 rtems/control/test_framed.py` or `make -C rtems test`.
The simulator shares the exact target/host loops and models local OISR as read-only.
It covers frame roundtrip, exact/changed retries, checksum/epoch/sequence rejection,
fragment order, STOP/status/HALT, timeout, mask changes and the watchdog.

In the established build workspace:

```sh
python3 project/rtems/build.py --work . --profile muctl
python3 project/rtems/control/build_framed_transport.py \
  --payload muctl/kernel.bin --out muctl-module
make -C /lib/modules/$(uname -r)/build M="$PWD/muctl-module" modules
# Stop the production relay and verify full restoration/unload first.
sudo python3 project/rtems/control/live_framed.py --payload muctl/kernel.bin \
  --module muctl-module/dac960auto.ko --reader control-prototype/read_mu \
  --output muctl-live
```

Use a fresh output directory and fresh module load for each experiment. Keep the
original production binaries and restart the service after verified cleanup.
The acceptance test records every ioctl buffer, parsed response, firmware sequence,
MU snapshot and full close captures. It deliberately does not run a runaway task.

Next: design and validate an owned interrupt stack and full asynchronous context
preservation. Keep the current task priority policy until that work establishes
safe nested lifetime/return rules. Then test CPU-bound preemption and independent
STOP under that load; only that can close the stronger P1/P2 control gate.
