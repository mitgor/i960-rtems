# DMA/SCSI ownership and callback-free monitor batch — 2026-10-11

The following 16 investigation, implementation and validation steps are complete;
exclusive hardware ownership remains intentionally denied.

1. Verified the current production close before taking the card.
2. Captured PCI topology without configuration writes.
3. Matched the vendor unpacked image to the installed firmware.
4. Byte-checked 73,608 disassembly rows and recorded 14 direct DMA-register leads.
5. Identified stock DMA0 start/completion and DMA1 start/wait/stop paths.
6. Identified the manufacturer's SCSI/cache ASIC families and missing contracts.
7. Implemented seven explicit target-owned proof requirements; idle never grants.
8. Added no-pending-command and epoch admission to the independent host channel.
9. Implemented bounded monitor entry on the owned ISR stack after ARM returns.
10. Preserved the original IRQ continuation, masks and DMA read-only snapshots.
11. Added RELEASE, expiry and HALT paths plus retention on uncertain completion.
12. Tested omission of RELEASE; preserved the initial failure without forced unload.
13. Consumed ENTER before PARKED to fix repeat entry; recovered after reboot and
    the user's physical intervention.
14. Found and corrected a historical compiler condition-code miscompilation in
    the diagnostic policy function; retained that build and its failed assertion.
15. Passed five final live sessions and offline replay, native sanitizer/gate
    tests and the complete RTEMS test target.
16. Restored IPv6 HTTP, verified original production OPEN and preserved artifacts.

## Failures are evidence too

The initial build left ENTER in IMR1 after expiry. A later IRQ could enter again
and replace EXPIRED with PARKED. The omitted-RELEASE ioctl timed out (Linux 110);
three read-only samples still showed ENTER/PARKED. Those samples do not measure
how many re-entries occurred. The host retained its module/allocation; an ordinary
unload did not remove it. No further firmware command was issued. The recovery
reboot did not return remotely until the user intervened. No flash was changed.

The consumption fix then completed all seven sideband exchanges, HALT and STOP,
but a report assertion rejected decision=0. Disassembly shows `cmpi` of the proof
mask followed by a condition-clobbering `cmpobne` of drift, then `testne`. Thus the
native test alone missed an i960 compiler error. Explicit volatile result stores
avoid this sequence. This erroneous diagnostic never enabled a transfer: there
is no transfer action in the target. The failed assertion's close restored RAM;
the now-unreferenced module was removed normally before rebuilding.

## Final results

Five sessions, ten firmware user callbacks (ARM and post-HALT diagnostic),
35 successful sideband operations, 20 monitor entries, five expiry returns,
ten denied transfer requests and five stale-epoch rejections. All reported
zero IRQ faults and zero sampled hardware drift. All six sampled DMA registers
were zero in these runs; that observation grants no ownership. Every close
verified restoration and unload. Offline replay rejected 125 modified reports.
The original and recovered boot IDs and raw evidence are retained.

The monitor is a bounded bare ISR experiment, not continuous callback-free
RTEMS execution. No disk workload, DMA transfer, SCSI reset, permanent handoff
or recovery mechanism was validated. See README for the actual remaining gates.

A final host review added immediate `ready=false` on uncertain control, so the
same open descriptor also rejects ordinary firmware writes. Native source guards
cover this admission rule; a fifth normal live session passed with module v5.
No second uncertain hardware failure was deliberately induced to test that flag.
