# Finite RTEMS task after the AcceleRAID 160 firmware callback

**Accepted RAM-only on the new card, 2026-10-17.** This 19-page image
extends the [post-return RTEMS timer](../residentclock/README.md) to one
RTEMS 4.6.6 task. Operation 13 returns to stock firmware while timer 1
retains a finite lease. After the host writes ENTER, the RTEMS timer callback
fires at tick 20 in a stock-firmware interrupt frame. That interrupt keeps
its continuation on owned ISR slot 0 while `rtems_initialize_executive_late()`
starts the Init task. The task uses the RTEMS workspace stack and a separate
owned ISR slot 1. It polls the nonce/epoch sideband, ignores an invalid STOP,
and ends on exact HALT or the 300-tick deadline. It masks interrupts and
calls `rtems_shutdown_executive()`, returning to the retained firmware ISR.
That ISR disables and drains timer 1, restores the vector/mapping/mask and
processor priority, then returns to stock firmware.

The two unchanged-image STOP/expiry batches passed:

| Batch | Firmware call return | Valid HALT | No-host expiry | Task timer IRQs |
| --- | ---: | ---: | ---: | ---: |
| `accept-0` | 41.425 / 41.442 ms | tick 22, 301.436 ms | tick 300, 3,078.362 ms | 2 / 280 |
| `accept-1` | 41.468 / 41.457 ms | tick 22, 301.353 ms | tick 300, 3,079.001 ms | 2 / 280 |

The first return time in each cell corresponds to HALT, the second to
expiry. Both wrong-token checks stayed pending until valid HALT. Task
progress, task identity and stack bounds, both ISR stack guards, nesting and
dispatch levels, and the stock-firmware frame were checked. Timer/vector,
firmware SP, priority, loader page, staging page and all 512 allocator records
restored after each path. Six complete same-boot flash reads and three
independent stock-state inventories passed. Old DAC960PG `0000:37:04.1`
remained unbound; no firmware was written. [Exact binaries and live
evidence](../../../artifacts/current/accele160-residenttask-20261017/README.md)
replay offline and reject seven altered captures.

Build with the pinned host RTEMS 4.6.6 core and i960 toolchain:

```sh
bash rtems/accele160/residenttask/build.sh \
  /home/mit/i960-rtems-20261011/bounded \
  /home/mit/i960/tools/bin OUT_DIR
```

The accepted 19-page `image.bin` SHA-256 is
`9574e08a321d8374b1ecb3d55a667ae098536634e51decf69174b7f8de4f7f5a`;
whole-image FNV is `090cb17f`. The unchanged operation-13 firmware SHA-256
is `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
The [host runner](run_residenttask.py) pins the BDF, binaries and modules;
requires paired full flash reads, exact stock preflight, every page copy
receipt, odd-page readback, whole-image digest, both finite paths, and full
owner/page/stage restoration. It retains a grant on uncertainty.

Two diagnostic calls reached a clean task HALT before the host checker
released them. The first tried to read ISR slot 1 from an even grant page;
BAR0 mirrored the adjacent entry page. The image moved slot 1 to odd page
17, with an unused gap at page 16. The second checker then interpreted the
new task-progress diagnostic word as the old ENTER count, even though the
trace retained the correct count. Both completed calls were inspected and
recovered under exact saved page, stage and owner checks. The accepted
runner uses the odd ISR page and checks the progress word against its trace.

This proves a **single bounded RTEMS task** can run after the firmware call
returns, with hardware ticks, sideband HALT, finite expiry and whole-instance
return to firmware. Its task context remains in the owned workspace after
shutdown but is never resumed; the host releases the grant only after RTEMS
returns to the retained ISR, timer 1 is quiet and both ISR continuations have
drained. This is not an independent hardware watchdog: permanently masked
interrupts or corrupted RTEMS scheduling could defeat the deadline. It does
not yet own DMA, run network services or Doom, or prove multi-task resident
preemption. The next gate is explicit DMA ownership and STOP/expiry drain for
all tasks and in-flight transfers before a service uses the grant.
