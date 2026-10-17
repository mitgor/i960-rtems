# AcceleRAID 160 bounded worker-independent containment

**Accepted on the new card, 2026-10-17.** This RAM-only operation-13 image extends the [two-worker preemption proof](../preempt/README.md). Both equal-priority workers run CPU-bound loops that do not read STOP, yield or call RTEMS. Timer 1 continues to time-slice them. The priority-1 controller reads the independently writable host sideband, rejects a wrong token, and imposes a finite 120-tick lease when no valid STOP arrives. On either exit path it records both progress counters, waits four more ticks to prove they continue despite STOP, and externally suspends each worker with `rtems_task_suspend()`.

This is **whole-instance disposal**, not individual task cancellation. Each suspended worker keeps its original hardware frame and one live, task-owned ISR continuation. Neither worker is resumed, deleted, unwound or described as drained. The timer is then masked and drained, and its cached vector, mapping, count, reload and mask restore before the controller returns through the stock firmware callback. The host may release the 512 KiB grant only after the callback has returned and all admission, page, stage and owner audits pass. No firmware write was made.

The image has 20 pages of code/data/BSS, three separate 8 KiB ISR areas (controller plus two workers) and one entry page, all inside the stock-owned 512 KiB grant. It records task identity, RTEMS `STATES_SUSPENDED` state and count 1, the unchanged original frame PC/AC/vector (`0x12`), 64-byte ISR-area guards, worker and ISR-area checksums before/after containment, zero ISR/dispatch nesting, and 10,000 unchanged progress/scheduler observations. It reports both retained active flags as 1, and each worker's ISR entries equal returns plus one. The report is written to odd grant page 21 for reliable PCI readback.

Two full STOP/no-host batches passed on boot ID `2fef3a5a-8027-4067-9d7e-2a8f8f6c6b84`:

| Batch | Valid STOP | No-host lease expiry | Worker continuations |
| --- | ---: | ---: | --- |
| `attempt-0` | 259.192 ms, 14 ticks/handoffs | 1,360.380 ms, 124 ticks/handoffs | 7/6 entries/returns at STOP; 62/61 at expiry |
| `accept-1` | 259.134 ms, 14 ticks/handoffs | 1,357.654 ms, 124 ticks/handoffs | 7/6 entries/returns at STOP; 62/61 at expiry |

A stale STOP token remained pending. Each worker advanced by tens of thousands of iterations during the four-tick post-STOP window, then made no progress during 10,000 checks after external suspension. Both task states were `2` (`STATES_SUSPENDED`) with suspend count 1, and worker/ISR checksums remained unchanged. The controller returned to firmware with SP `c0002100` restored. Four complete guarded 1 MiB post-batch flash reads matched SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`; two independent post-batch timer/vector inventories matched stock. The loader page, staging source and every allocator count/owner record restored. The old DAC960PG `0000:37:04.1` stayed unbound and untouched; the new card `0000:37:09.1` remains bound to `myrsread`, with no one-shot command module loaded.

The accepted image SHA-256 is `42e97872951539f5cb4c7418c466364919007d0d35a2dbf81dbf014d58e3ffde`, kernel SHA-256 `4ae72fd5aab5fc5f167bed6bcf60f62352d15549034844300735c906bb5b024e`, and whole-image FNV `0xa61ea90b`. [Exact binaries, source snapshot and live evidence](../../../artifacts/current/accele160-contain-20261017/README.md) are archived. Rebuild with `build.sh RTEMS_BUILD_DIR TOOLCHAIN_BIN OUT_DIR`, using the pinned RTEMS core and toolchain described in [the task lease](../lease/README.md). The physical [runner](run_contain.py) pins all identities, requires two same-boot full flash reads, validates per-page copies and the card digest, tests STOP and lease expiry, checks retained contexts and full restoration, and leaves resources in place on any uncertain result. Never force-unload a pending operation-13 module.

```sh
python3 rtems/accele160/contain/verify_live.py artifacts/current/accele160-contain-20261017
python3 rtems/accele160/contain/test_verify_live.py artifacts/current/accele160-contain-20261017
```

The replay checks the exact binary, four complete flash reads, page copies, digest, STOP/expiry reports, retained ISR frames, worker progress and stock inventories. Four tamper tests alter image, flash, STOP and owner evidence and must be rejected.

**Scope:** This proves STOP of workers that ignore the control word but leave interrupts enabled and the RTEMS scheduler intact. The lease deadline is enforced by an RTEMS controller task, not an independent hardware watchdog. Permanently masked interrupts, unbounded critical sections, broken scheduler state, resource/lock cleanup and active DMA are not contained. The firmware callback remains parked for each finite run; this is not a callback-free resident service. The next gate is a bounded callback-free supervisor or a separate hardware-enforced recovery mechanism, plus explicit RAM/DMA ownership and quiescence before networking or Doom on this card.
