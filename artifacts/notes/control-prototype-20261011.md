> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Interrupt audit and control protocol evidence — 2026-10-11

Source/audit: `rtems/control/`; roadmap: `RTEMS-PREEMPTION-DMA-PLAN.md`.

- `config-build.txt`: explicit read-only PCI configuration inventory on the
  DAC960PG, followed by service state `active`. No BAR/MMIO accesses or writes.
- `control.o`, `control.dis`: protocol core cross-compiled with the established
  `/home/mit/i960/tools/bin/i960-coff-gcc -mrp -O2 -ffreestanding -fno-builtin`.
  This is a relocatable object, not a runnable or installed card payload.
- `tests.txt`: five native test groups, including 10,000 malformed frames and
  stale/torn/duplicate/STOP failure scenarios.
- `native-demo.json`: separate host/target processes over a shared-memory mapping;
  PING echo, advancing heartbeat and acknowledged STOP. Native simulated quiesce
  and ordering hooks, not real DMA/interrupt shutdown.

The running web service was not restarted or modified. Physical independent
control remains gated on a reserved host-visible slot and demonstrated interrupt/
cache/lifetime ownership. No claim is made that this demo preempts a live i960 task.
