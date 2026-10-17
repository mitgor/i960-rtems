# AcceleRAID 160 bounded RTEMS timer preemption

**Accepted on the new card, 2026-10-17.** This RAM-only operation-13 image extends the [hardware-clock proof](../autoclock/README.md) to two CPU-bound, equal-priority RTEMS workers. The owned timer-1 ISR advances the RTEMS clock and calls `_Thread_Dispatch()` from its per-task continuation when a switch is due. Neither worker voluntarily yields during its bounded loop. A priority-1 controller sleeps between ticks, checks the sideband STOP word, and sets a finite 120-tick deadline. The exact valid STOP token, or that deadline, quiesces both workers. Both must resume and drain their ISR continuations before the borrowed timer/vector and stock firmware context are restored. No firmware write was made.

The 27-page image is inside the card's existing 512 KiB stock-owned grant: 20 pages for code/data/BSS, three separate 8 KiB ISR areas (controller and two workers), and one entry/hardware-frame page. The ISR selects its save area from `_Thread_Executing`, rejects an unknown/reentrant owner, saves all globals and writable TC state, checks the hardware frame against the task's RTEMS stack, and verifies PC/AC/vector equality when that continuation returns. The workers' observed hardware vector is `0x12`; their ISR C stack pointers were `c0726180` and `c0728180`. The controller had no interrupt continuation in these runs, so its ISR SP is zero. The 64-byte area guards and the RTEMS nesting/dispatch-disable levels were checked after all continuations drained. The 112-byte report is placed in odd grant page 21, which the host PCI aperture can read reliably; even grant pages are not used for host readback validation.

Two complete STOP/no-host batches passed on boot ID `2fef3a5a-8027-4067-9d7e-2a8f8f6c6b84`:

| Batch | Valid STOP | No-host deadline | Handoffs | ISR continuations |
| --- | ---: | ---: | ---: | --- |
| `accept-0` | 145.027 ms, 8 ticks | 1,257.979 ms, 120 ticks | 8 / 120 | workers 4/4 and 60/60 entries/returns |
| `accept-1` | 144.826 ms, 8 ticks | 1,257.571 ms, 120 ticks | 8 / 120 | workers 4/4 and 60/60 entries/returns |

In each STOP case a wrong token remained pending and only the exact nonce/epoch token produced ACK. The `two_live` count was 7 in STOP and 119 in the no-host path, demonstrating suspended ISR continuations on both worker stacks. All 27 page-copy receipts, whole-image digest, admission report, owner records, loader page and staging source passed each path. Firmware SP was `c0002100` before and after, and cached vector 18 restored to `0xaaaaaaaa`. Six complete guarded 1 MiB flash reads matched SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`, with status/residual/guard changes zero. Independent timer/vector inventories after both batches matched stock. `myrsread` remains bound to new card `0000:37:09.1`; old DAC960PG `0000:37:04.1` remains unbound and untouched. No one-shot command module remains loaded.

The first physical run also performed eight handoffs and restored state, but its **host checker** attempted to read a report from even grant page 20. It rejected the returned call, retained resources, and then the exact saved page/grant/stage/owner recovery procedure released it. Two full firmware reads passed. Moving the trace to odd page 21 produced the repeated accepted result. This diagnostic is retained under `live/attempt-0` without its obsolete binary.

The accepted `image.bin` SHA-256 is `514dfc5b1c8ea1a2ef114ad421f88a12f015a7669dea8af70981dfead107405f`, `kernel.bin` SHA-256 `3f211bf02b85e911836259cd7f83be27b4ffb0c4e93d2aa1c80d89e669bd4f7f`, whole-image FNV `0x91f3da52`. The exact binaries, map, source snapshot and card evidence are [archived here](../../../artifacts/current/accele160-preempt-20261017/README.md). Rebuild with `build.sh RTEMS_BUILD_DIR TOOLCHAIN_BIN OUT_DIR`, using the pinned RTEMS build and toolchain described in [the task lease](../lease/README.md). The physical [runner](run_preempt.py) checks exact SHA pins, BDF ownership, two same-boot full flash reads, 27 page copies, digest, STOP/deadline, complete page/owner/stage restoration and stack telemetry. Do not force-unload a pending operation-13 command; [recovery](../autoclock/recover_finished.py) is limited to an already returned, exact-byte-matched call.

Offline replay and four tamper cases:

```sh
python3 rtems/accele160/preempt/verify_live.py artifacts/current/accele160-preempt-20261017
python3 rtems/accele160/preempt/test_verify_live.py artifacts/current/accele160-preempt-20261017
```

This proves **bounded RTEMS timer-driven preemption of two interrupt-enabled CPU-bound tasks** on the new card. STOP is handled by a higher-priority RTEMS controller task after a tick; it cannot regain control if code masks interrupts indefinitely or corrupts scheduler state. It is not a resident RTEMS service, a noncooperating-task containment mechanism, network stack, DMA path or Doom port. The next gate is a finite resident lease with an independently enforceable quiescence boundary and memory/DMA ownership suitable for services; retain the old card runtime separately.
