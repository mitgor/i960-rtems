# AcceleRAID 160 callback-free timer handoff, 2026-10-17

**Accepted RAM-only on-card gate.** The exact three-page image SHA-256 is
`1f448cdf017d3410e03a493f45f7ad37a8e4f4f3268c05270e5bc7fe10952f2a`;
whole-image FNV is `e08fbc64`. Stock operation-13 firmware SHA-256 remains
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
No flash write was made. The new card was `0000:37:09.1` under `myrsread`;
the old `0000:37:04.1` stayed unbound.

The callback completed in 10.573 ms for expiry and 10.595 ms for HALT. The
host then sent ENTER through the loader-page sideband. The timer ISR recorded
a stock-firmware frame, not the owned callback stack. With no HALT, the monitor
expired at exactly 300 ticks in 3,048.106 ms. A wrong token stayed pending;
valid HALT stopped at four ticks in 88.471 ms. The owned ISR stack changed by
128 bytes in each mode, retained its end guards, and recorded zero faults.
Both paths reported restoration flag 1, firmware SP `c0002100`, timer vector
18, priority-0 process controls `00002002` at ENTER and saved firmware
controls `00062002` at exit.

The accepted `live/attempt-5` contains exact reports, copy receipts, card-side
whole-image digest, sideband snapshots, ISR trace/stack, allocator records,
loader page and stage restoration, and host timing. `live/pre-flash-{0,1}` and
`live/post-flash-{0,1}` are four complete 1 MiB guarded reads from the same
boot, each matching the firmware SHA above. Independent `live/preflight` and
`live/postflight` inventories show the stock timer-1 count/reload/mode zero,
pending bit clear, mask `10c7`, map `80000`, and cached vector 18
`aaaaaaaa`. The accepted source/build is in `image/`; rebuilding it with the
pinned remote i960 tools reproduced the same SHA-256.

Replay the captured acceptance from the repository root:

```sh
python3 rtems/accele160/handoff/verify_live.py artifacts/current/accele160-handoff-20261017
python3 rtems/accele160/handoff/test_verify_live.py artifacts/current/accele160-handoff-20261017
```

The replay passed. Four independent tamper cases altered a flash byte, an
allocator owner record, the ISR fault word, and the stale-token capture; all
were rejected. `live/attempt-0` through `live/attempt-4` are compact failure
captures. Attempts 3 and 4 reached valid 300-tick expiry, but the host first
used a too-short terminal wait and then mistook an i960 process-control word
for an instruction pointer. Each completed call was guardedly recovered, with
fresh full flash reads and stock inventories before continuing. The first
three attempts established the priority-mask correction; they are historical
captures, not alternate accepted binaries.

This proves a finite monitor after the firmware callback returns. It does not
run resident RTEMS, network services, Doom or DMA, and it is not a hardware
watchdog against code that masks interrupts indefinitely. The next physical
gate is a bounded resident RTEMS control task under this monitor, followed by
explicit RAM/DMA ownership and verified quiescence before resource release.
