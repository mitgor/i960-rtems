# Why the AcceleRAID bring-up has used more flash writes

The DAC960PG and AcceleRAID 160 both run i960 code, but their stock firmware,
command handlers, RAM maps, host drivers and interrupt controllers are
different. The old card now has a reusable programmed loader and a mature
RAM-only RTEMS path. Host software can upload a new RTEMS application or Doom
image into an owned arena and use the installed transport without flashing
for every run. This was earned during the old card's own bring-up; it was not
provided by the original RAID firmware.

On the AcceleRAID, the first stock `0x8f` hook had no generally admitted RAM
program. We patched a small retained handler to establish narrow operations:
RAM staging, allocation/ownership, page copy, digest and exact entry, one
fixed RTEMS image, observational register inventory, and a bounded sideband
STOP gate. Each newly admitted operation changed the handler, so it required
an audited 1 MiB candidate, staged readback, one flash command, reboot and
two complete persistent reads. The RTEMS task and test payloads themselves
were uploaded to RAM. The resulting extra flash cycles reflect this
one-operation-at-a-time bring-up policy, not a requirement of the 100 MHz
processor or RTEMS.

The new card's accepted RTEMS test is smaller in scope. It uses a stock-owned
512 KiB grant and a fixed 57,972-byte RTEMS image. Its worker wakes after
five synchronous software ticks and returns through the stock command.
The old card has an 8 MiB Doom-capable arena, resident and preemptible RTEMS
profiles, an autonomous clock, host-backed networking and browser output.
Those old-board binaries and board support cannot simply be copied to the
AcceleRAID; the i960 family is shared, but the hardware contract differs.

The intended way to stop repeated flashing is a single reusable, bounded
RAM admission layer on the AcceleRAID. The host would upload a manifest and
segments into an independently checked grant, verify exact address/length,
entry, BSS, stack and whole-image digest, then run the image with a finite
lease and the independently writable STOP word. It must preserve the stock
driver's command/complete ownership and page/allocator audits. The current
operation-8 leaf and operation-9 RTEMS call prove pieces of this, but both
pin exact payloads; operation 11 proves only a bounded callback STOP.
Changing to a generic admission should be one separately audited firmware
revision, followed by RAM-only vector/timer probes and RTEMS experiments.

The first reusable revision, [operation 13](../../host/accele160/ram_admit/README.md),
was [accepted on card](../../artifacts/current/accele160-ram-admit-20261017/README.md)
on 2026-10-17. It admits one contiguous 1–127-page trusted-host image with
an aligned entry, whole-image FNV and pinned host SHA-256. It preserves
operations 1–12 and uses the existing stock-owned grant. Two different RAM
probes ran through the same firmware, so future reviewed returning programs
no longer need a flash revision. This first contract does **not** yet
implement segmented loading, a separate BSS/stack contract, a finite
execution lease or task-aware STOP. Those are still required before it can
replace the old board's resident RTEMS loader.

The accepted 2026-10-17 operation-12 experiment is one final fixed observational
probe before that consolidation. It reads the internal cached vector words
at `0x04` and `0x20` and reads timer-1 mode only when two sets of count,
reload, pending, mask and mapping checks pass. The timer mode read clears
terminal-count status by hardware design, so even this probe is not purely
non-destructive if that status was set. In the accepted run it was clear;
mode was 0, cached vector 18 was `0xaaaaaaaa`, and the full audits passed.
That sentinel and timer-1's undefined mapping are reasons to require an
explicit vector/stack ownership proof before a timer write.
