# Hardware-interrupt RTEMS development

This directory contains the observational inventory, autonomous transport
builder and explicit hardware tests. The `irq` build profile in `../irq/`
contains a bounded hardware-timer/preemption experiment. `auto` compiles the
same core with `I960_BACKGROUND` to resume RTEMS from timer interrupts between
host requests. `autonet` adds the same interrupt runtime to the dual-stack networking and HTTP
profile. These remain separate from the cooperative `net` profile.

## Established hardware facts

On this board, the observational probe found PRCB `FEFFD4D0`, ROM interrupt
table `FEFFD0C0`, core interrupt mask `10C7`, ICON `6000`, and IMAP2 `00080000`.
Timer 0 reload was `171E8` and its count was changing. Timer 1 count/reload,
mask bit and pending bit were zero. All three on-chip DMA channels reported
zero control/status. These are observations, not a claim that every PCI/SCSI
engine is quiescent or that arbitrary DRAM is free.

The active vector cache matters: ICON bit 13 makes dedicated interrupt vectors
come from internal data RAM. Timer-1 vector `F2` can use cached slot `003C`
without writing the flash table. The probe saves/restores that slot and refuses
any IMAP configuration already using it. The bounded live test delivered eight
hardware ticks and eight timed task wakeups while a lower-priority task ran a
busy loop; the awakened task observed the busy loop advancing. Timer state,
vector and masks were restored before the callback returned, and the existing
loader verified RAM restoration and unloaded.

The inventory deliberately avoids TMR0/TMR1 reads: reading those mode registers
clears terminal-count status. The timer experiment reads TMR1 only after its
count/reload/mask/pending checks pass, and refuses a nonzero mode. This is a
mutating, explicitly invoked experiment, not a read-only inventory.

## Separate autonomous transport

The ordinary cooperative module must not load a background interrupt image.
`build_transport.py` generates `dac960auto`, pins the SHA256 of the exact
prepared target, and creates `/dev/i960-auto`. Protocol magic is `RTA1`;
operations are status (0), arm (1), and stop (2). `autonet` uses RTA1 with network operations 0–5 and STOP 6; generate its
module with `--network`. Cooperative networking retains its original protocol.

Private RTEMS state can change between paired DMA reads. Both immutable regions
and both BIO responses must agree and validate independently; private bytes are
not claimed to be a coherent simultaneous snapshot. Bounds/guard locations
remain unchanged. Before any restoration, final file release issues STOP and
validates that the timer is stopped, its pending bit is clear, the vector is
restored and original masks/mapping are back. Failure retains the image and
module. SIGKILL therefore cannot bypass the kernel-side stop requirement.

The native simulator exercises 344 command-failure/timeout boundaries for each
of the two autonomous variants (688 total), changing
private state and a rejected stop acknowledgement. It asserts that no image
restoration occurs while its simulated interrupt handler is live. These tests
are not proof of hardware interrupt/frame correctness.

Three failed trials are retained with their original binaries and logs: a
background mask that blocked firmware interrupts, an uninitialized `modpc`
operand that prevented STOP, and a generic session-ready guard that blocked
STOP after a completed application error. Each retained resources and required
a host reboot; none wrote flash. Corrections preserve stock interrupt masks,
initialize the processor-control operand and allow only verified STOP after a
completed error (never after pending/uncertain execution).

The corrected `auto` test delivered 2,009 ticks and task wakeups during 20 seconds
without host polling, approximately 100.024 Hz. `autonet` delivered 509 ticks in
five silent seconds, then passed dual-stack echoes, IPv6 Internet HTTP and a
60-second IPv6 stress test (554,528 bytes). The final build passed live SIGTERM,
SIGKILL and invalid-operation restoration/unload, and 24 HTTP request tests.
See the [dated report](../../artifacts/rtems-web-autonomous-20261011/README.md).

## Build and test

On a deployed source tree, build `rtems/build.py --profile irq` or `--profile auto` / `--profile autonet`
with the normal work directory and cross prefix. Build the autonomous module
with `build_transport.py --payload <auto/kernel.bin> --out <new-module-directory>`,
then compile that module against the running Linux kernel. `live_test.py` is an
explicit card test which arms RTEMS, leaves the host silent, checks progression,
and closes through the stop-before-restore protocol.

`build_inventory.sh <new-output-directory>` builds the observational BIO1 payload
and its scalar transport. The inventory response is magic `RAI1`, PC, 28
address/value pairs, PRCB pointer plus ten words, and interrupt-table pointer
plus 257 words. Its maximum response is 1308 bytes; request capacity 1400.

## Remaining limits

Background timer reload 41667 with divide-by-eight gives approximately 100 Hz
on the measured 33.333 MHz bus; the bounded IRQ experiment uses reload 20000. Nested-interrupt handling, arbitrary user-task
preemption, independent packet transport, general fault recovery and live
exclusive takeover are not established. The background entry resumes bounded
RTEMS work at priority 31 and returns to stock firmware. The bounded `irq`
profile separately proves a hardware interrupt can trigger a task switch.
An unrestricted autonomous BSP requires further work; avoid claiming one from
these narrower experiments.

Register semantics and cached-vector layout come from Intel's
[i960 Rx Developer's Manual, 272736-002](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF),
sections 8.4, 8.5.2.1, 19.1–19.3 and Appendix C. Preserve firmware timer 0.
