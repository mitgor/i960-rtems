# Finite two-task RTEMS lease after AcceleRAID firmware return

**RAM-only card acceptance, 2026-10-17.** This extends the
[single-task handoff](../residenttask/README.md) with a separate RTEMS worker
and supervisor. Operation 13 returns to stock firmware before the host sends
ENTER. At hardware tick 20, an RTEMS timer callback fires in a retained
firmware interrupt; `rtems_initialize_executive_late()` starts Init. Init
creates a worker, records both task identities and stack bounds, then
suspends. The worker remains runnable, polls the exact nonce/epoch HALT and
the 300-tick deadline, and receives timer interrupts on an owned second ISR
stack. When it finishes, it resumes Init without allowing preemption,
suspends itself, and only then may Init shut down the RTEMS instance. The
retained firmware ISR disables/drains timer 1, restores the cached vector,
mapping, mask and priority, and returns to stock firmware. Grant release is
permitted only after that return and all page, stage and owner checks.

Two unchanged-image acceptance batches passed:

| Batch | HALT / no-host time | Ticks | Worker timer IRQs | Worker progress |
| --- | ---: | ---: | ---: | ---: |
| `accept-0` | 301.425 / 3,080.969 ms | 22 / 300 | 2 / 280 | 15,873 / 1,952,935 |
| `accept-1` | 304.246 / 3,079.843 ms | 22 / 300 | 2 / 280 | 16,129 / 1,952,937 |

Both wrong-token checks stayed pending. Task identities, separate RTEMS
stacks, worker suspension, two ISR stack guards, timer counts, firmware frame,
zero ISR faults and restoration flag 1 passed. Six full guarded 1 MiB flash
reads on the same boot matched unchanged operation-13 firmware SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
Independent pre/mid/post inventories found the original timer/vector state.
The loader page, staging source and all 512 allocator count/owner words
restored. Old DAC960PG `0000:37:04.1` remained unbound; no firmware was
written. [Exact binaries and captures](../../../artifacts/current/accele160-residentworkers-20261017/README.md)
replay offline and reject ten altered-evidence cases.

Build with the pinned RTEMS 4.6.6 core and i960 toolchain:

```sh
bash rtems/accele160/residentworkers/build.sh \
  /home/mit/i960-rtems-20261011/bounded \
  /home/mit/i960/tools/bin OUT_DIR
```

The 19-page `image.bin` SHA-256 is
`890ca49efdd1ea2228ae305ca3b78402cbd4104cc407f34a05d268123bd8544f`;
whole-image FNV is `a2cdcd12`. The pinned [host runner](run_residentworkers.py)
requires exact BDF, binaries and modules, paired full flash reads, all 19
copy receipts, odd-page samples, card-side whole-image digest, both finite
paths and full owner/page/stage restoration. It retains the grant on any
uncertain completion. [Offline replay](verify_live.py) checks the captures
and [tamper tests](test_verify_live.py) reject flash, owner, ISR, token,
callback and both task-record changes.

An earlier sleep-based two-task trial did **not** reach a terminal state.
Its callback had returned and ACTIVE was visible, but HALT remained pending
after six seconds; two later sideband, ISR and owner snapshots were identical.
The runner correctly retained the grant and modules. After a new boot cleared
those resources, the corrected image replaced tick sleeps with a direct
supervisor-suspend / worker-resume-and-suspend handoff. The idle-thread
dispatch path is the likely cause of that hang; the saved snapshots do not
prove the precise point of failure. Compact diagnostics are archived; the
obsolete trial binary is omitted. No flash write occurred in either trial.

This proves finite **two-task ownership and worker drain** after the stock
firmware callback returns. It does not prove general resident task preemption:
the worker runs with RTEMS task preemption disabled, although hardware timer
interrupts continue. RTEMS shutdown still disposes the whole instance; its
owned memory must not be reused until the retained ISR has returned. There
is no DMA owner or independent watchdog for permanently masked interrupts
or corrupt scheduler state. The next gate is a bounded DMA transaction with
an explicit host-buffer owner, completion/timeout state and drain before
grant release; only then should network or Doom service work be admitted.
