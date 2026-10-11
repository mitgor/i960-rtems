# Two-task IRQ continuation switch — 2026-10-11

**Three live runs passed. No reboot, flash programming or recovery test.**
Production Vader/visitor HTTP was stopped with verified cleanup and restarted
using its existing `autonet` binaries afterward.

Each run:

- 32 hardware timer ticks and 32 IRQ-path scheduler handoffs (including the final
  controller wakeup); 31 observations with both ISR lifetime records live.
- Both tasks: 16 ISR entries, 16 returns, no live continuation at teardown.
- CPU-bound loops with distinct GPR sentinels and checked deep call chains.
  Both consumed about 228,000 iterations before observing STOP. No voluntary
  yield occurs in either assembly loop.
- PC before/after 00142002, TC before/after zero; globals and checked locals matched.
  No AC-branch, frame, stack guard, owner or nesting failures.
- Timer/vector/mask restoration, full borrowed RAM restoration and module unload.

| Owner | Task stack | Hardware frame | Owned ISR area |
| --- | --- | --- | --- |
| C0F568E8 | C0F5C2D0–C0F5E2D0 | C0F5CC70 | C0F60480–C0F62480 |
| C0F56A58 | C0F5E350–C0F60350 | C0F5ECF0 | C0F62480–C0F64480 |

Range ends are exclusive. These are addresses of this exact build, not a new
permanent firmware allocation. Host STEP latency was 247.28–248.65 ms.

`live.tar.xz` contains the exact target binary/ELF/disassembly/map, compiled module
and generated source, `switch-live1/run-0..2` raw reports and full captures, and
source snapshots. `build.log`, `live.log`, `offline-tests.log` and `http-check.txt`
preserve build, acceptance, regression and restored-service results. No visitor
IP statistics are included.

```sh
python3 rtems/switch/verify_capture.py artifacts/irq-switch-20261011/live.tar.xz
```

The verifier checks exact binary hashes, raw sentinel/lifetime reports and full
borrowed-RAM restoration for every run, rather than trusting saved success flags.
Native tests additionally reject reentry, owner/frame/AC mismatches, out-of-bounds
frames and release with a live continuation.

This is bounded asynchronous time-slicing, not a resident monitor. Host-independent
STOP during these CPU-bound loops, live critical-section deferral, general nesting,
NMI/trace faults and unrestricted network-task preemption remain open.
[Implementation and next work](../../rtems/switch/README.md).
