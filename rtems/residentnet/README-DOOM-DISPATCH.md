# Dispatcher ownership and WAD service follow-up

The timer's registered-owner guard is intentional. A first-rejection record in
RAM diagnostics words 40–51 (engine profile only) distinguishes:

1. A timer on an unregistered executing task.
2. A timer while that published task already owns a live IRQ continuation.
3. Failure of the controller's final RAM/application drain.

`IJR1` records the first reason, published executing TCB, both active flags,
interrupt FP, saved PC/AC/vector, registered TCBs, and count. It never clears
`switch_fault`, changes an owner, or grants a saved pointer permission. Accepted
runs still require all these words zero. `verify_irq_rejection.py` checks a failed
capture against independently frozen stack/TCB bounds; seven tamper cases reject.

## The actual failure

The diagnostic caught reason 2 at tick 31,926: executing worker 0, active flags
`[1,0]`, but interrupt FP on worker 1's stack. The saved priority was 20.
Upstream RTEMS 4.6.6 `_Thread_Dispatch` publishes the heir before enabling
interrupts, then calls its extensions and context-switch routine on the outgoing
stack. That window is incompatible with this port's task-owned IRQ continuations.
The native test compiles the real upstream function and deterministically
interposes an IRQ in that window, reproducing the identity/stack mismatch.

`--dispatch-atomic` generates a build-local patched dispatcher. It keeps masking
from heir publication through physical context transfer. On later resumption,
it preserves the original local interrupt level instead of recapturing masked
31. It restores that level only after the executing identity and stack agree.
The test covers callers at levels 20 and 31, including transfer away and later
resumption. New task contexts in this proof start masked; no arbitrary task,
idle-owner, user-extension or FPU context admission is added. Existing ISR guards,
stack checks, continuation lifetime and STOP drain remain mandatory.

Original/patched hashes and the generated source are recorded in target build
metadata/artifacts. Upstream source files remain unchanged. Production's accepted
cooperative autonet image is not rebuilt by this opt-in profile.

## Host snapshots and WAD polling

Page-wide host exclusion could delay a WAD reply beyond the unchanged five-second
deadline. The monitor is frozen once and read in four-word serialized groups.
UPL, WAD, owned-control and network buffers are independent of that monitor
snapshot; they may run between groups. Only the main test thread freezes the
monitor. Every 64-word page and every paired audit is retained. The regression
test executes the actual host reader, checks complete consistent pages, and
shows the old page-wide lock starves service while the new groups do not.

`--wad-poll` lets the application worker service the existing PIO control mailbox
while waiting for a WAD response. It checks the registered runnable owner before
briefly masking control dispatch, restores prior PC and yields periodically.
It changes no wire ABI, read size, five-second deadline, CRC, EOF/padding,
sequence/epoch, exact destination loan, cancellation or cleanup requirement.
Native owned/STOP/WAD-loan tests and actual core replay exercise this path.

The two switches are explicit. The full on-card engine preflight batch requires
both switches, the 1 MiB initial proof reservation, all earlier regression
probes, modified-image refusals, normal / STOP / normal and final drain. It
passed at tick 100,085 with no rejection markers. This is the engine-linked
preflight; Doom itself has not initialized on the card.
