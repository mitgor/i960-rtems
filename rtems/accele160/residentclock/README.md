# Callback-free RTEMS timer gate on AcceleRAID 160

**Accepted RAM-only on the new card, 2026-10-17.** This 17-page image keeps
the [finite post-return timer lease](../handoff/README.md), initializes RTEMS
4.6.6 before returning from firmware operation 13, and lets the card's timer-1
ISR advance the RTEMS clock. An RTEMS one-shot timer callback fired at hardware
tick 20, after the firmware callback returned and after host ENTER was observed
in a stock-firmware interrupt frame. The ISR never dispatches an RTEMS task.

The no-host path expired at tick 300 in 3,076.707 ms; exact HALT ended at
tick 21 in 286.276 ms after a wrong token remained pending. Operation 13 had
returned at 31.067 and 31.127 ms respectively. Both paths logged zero ISR
faults, callback-after-ENTER flag 1, retained the ISR stack guards, restored
the original processor priority and timer/vector/map/mask, and fully restored
the loader page, staging source and all 512 allocator records. Four complete
same-boot flash reads and independent pre/post stock inventories passed. The
old DAC960PG stayed unbound; no firmware was written. [Exact build and live
captures](../../../artifacts/current/accele160-residentclock-20261017/README.md)
replay offline and reject five altered-evidence cases.

Build with the pinned i960 tools and RTEMS 4.6.6 core on the Linux host:

```sh
bash rtems/accele160/residentclock/build.sh \
  /home/mit/i960-rtems-20261011/bounded \
  /home/mit/i960/tools/bin OUT_DIR
```

The accepted `image.bin` SHA-256 is
`6e8e0d60bd6f4b8e48756ae6acbb50740dc1477d517b91da36da3df150d9fd25`;
whole-image FNV is `364f75fd`. The unchanged operation-13 firmware SHA-256
is `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
`run_residentclock.py` pins these and the command modules, requires two
complete same-boot flash reads, a stock timer/vector preflight, each upload
receipt, odd-page readback, card-side whole-image digest, bounded HALT and
expiry, exact quiescence and restoration. It retains an uncertain grant.

The first three trial calls returned status 2 before timer-1 was armed.
The first stopped at a mistaken expectation that RTEMS's early initialization
left dispatch-disable level zero. The next two reached `INVALID_ID` from
`rtems_timer_fire_after()`: the API configuration had allocated one semaphore
and zero timers. Each completed call was recovered only after exact page,
grant, owner and stage checks. The corrected image gives the timer manager one
object; these diagnostic attempts are not alternate accepted images.

This proves that an **RTEMS timer callback** can execute after the firmware
callback returns, under a finite hardware-timer lease. It does **not** prove a
resident RTEMS task, scheduler handoff, DMA ownership, an independent watchdog
or a long-lived network/Doom service. RTEMS is only early-initialized; task
multitasking is deliberately not started, and dispatch stays disabled in the
ISR. The next gate must transfer control to an owned RTEMS task after the
firmware return, then prove STOP/expiry quiesces every task, ISR continuation
and DMA operation before releasing RAM. A task that masks interrupts
indefinitely can still defeat the timer deadline.
