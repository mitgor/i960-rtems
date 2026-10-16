> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Owned interrupt execution stack — hardware evidence, 2026-10-11

**Both live tests passed, without reboot, flash programming or recovery tests.**
The original IPv6 Vader/visitor service was stopped with verified RAM restoration,
and restarted with its existing production image after the experiments.

## Isolated context stress (`irqctx-live1`)

Three runs delivered 42 interrupts each (126 total), with zero stack/frame faults
and zero probe failures. g0–g14 sentinels and g15 matched before/after, as did
PFP/SP and r4–r15. The bounded r3 counter completed; RIP is legitimately changed
by interrupt calls and was not treated as a constant register. Both 25-level
call chains unwound correctly. Compare/branch stress reported no AC error.
PC was 00142002 before and after; TC was zero before and after despite deliberately
toggling its mark-trace mode inside the ISR while hardware disabled tracing.

Owned allocation: C0F5E3A0–C0F62420 (end exclusive). Sampled C stack SP range:
C0F5E4E0–C0F5F120, reaching 3,264 bytes above the C-stack base. Hardware interrupt
frame: C0F5B0A0, retained on the interrupted RTEMS stack. Both guards stayed intact.
Each host STEP took 263.57–300.46 ms. Full borrowed RAM restored; module unloaded.

## Bounded background control (`muctx-live1`)

546 interrupts, zero frame/guard faults, no active handler after HALT. STATUS,
PING, exact retry, wrong-epoch rejection, checksum rejection, independent STOP,
STOP retry and later STATUS all passed. RTEMS stopped at tick 362 / control
heartbeat 363. Final timer HALT took 9.303409 ms. Firmware sequence remained
1 → 1 throughout all nine control ioctls. A separate firmware STEP afterward
collected stack diagnostics; it was not required to perform STOP/HALT.

Owned allocation: C0F5E4E0–C0F62560. Entry/leave SP sample C0F5E620; this sampling
does not measure the deepest framed-handler call. The sampled hardware frame
was C0002050 in the firmware stack, with saved PC=00062002, AC=00009002, vector F2.
Global ISP remained C0001000. Full timer/vector/mask, MU and borrowed RAM
restoration passed; the module unloaded.

## Files and verification

`live.tar.xz` contains both target binaries/ELFs/disassemblies/maps, both compiled
modules/generated source, raw register/CTL1 records, full open/close captures,
and source snapshots. `irqctx/source/` preserves the exact source of the first
successful build; the later header conditionalization omits unused stress
helpers from `muctx` without changing the `irqctx` code path.

The `*-build.log`, `*-live.log` and `offline-tests.log` preserve compiler output,
acceptance results and the complete existing RTEMS regression suite. `http-check.txt`
records HTTP verification after the production service restarted. No visitor IP
statistics are included.

```sh
python3 rtems/interrupt/verify_capture.py artifacts/owned-interrupt-stack-20261011/live.tar.xz
```

The verifier checks binary hashes, linked trampoline/allocation, raw sentinel and
control records, and full borrowed-RAM restoration. It does not merely trust a
saved `passed` flag.

## Scope

This owns the C ISR stack and tests complete return-context preservation along
the existing non-nested return path. The **hardware entry frame remains in
place** and must remain live. There is no movable asynchronous thread context,
arbitrary preemption, runaway level-31 task STOP, general nesting, NMI recovery
or breakpoint/trace-fault virtualization. [Implementation and next work](../../rtems/interrupt/README.md).
