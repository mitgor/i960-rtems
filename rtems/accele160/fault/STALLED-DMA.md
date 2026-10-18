# Accele160 suspended-DMA timeout qualification

Profiles 8 and 9 extend the isolated finite-chain diagnostic with a deliberate
hardware suspension, followed by real `faulte` or a host-doorbell NMI. Normal
profile 5 is unchanged. These profiles use the same owned source/descriptors,
guarded pinned host targets, exact-card admission and reset-only lifetime as
[the active-DMA tests](ACTIVE-DMA.md).

The suspension uses Intel 80303 manual 273353-001 section 19.14.1: clearing
DMA0 CCR.Channel Enable suspends internal-bus transfers at the earliest
opportunity. The PCI side may still empty/fill its queue, and queued data stays
valid. This is **not abort, completion, or permission to free memory**. No bus
master bit, other DMA channel, unknown PCI target, or circular chain is used.

After observing CSR.Channel Active, the test clears only DMA0 CCR.CE and waits
for 4096 matching descriptor/next-descriptor/byte-count observations, within
100000 iterations. Acceptance requires active/error-free CSR, disabled CCR,
nonzero remaining bytes, and a nonfinal descriptor. It then enters the owned
fault/NMI path. The terminal path runs its actual existing 10000000-poll bound.
The report must show precisely that exhausted bound and the same outstanding
hardware state at entry and afterward. DONE publishes diagnostic evidence;
it never completes the pending firmware command. The channel stays disabled,
the CPU parks, and source/descriptors/destinations remain owned until reset.

Host acceptance checks both stack guards, peer DMA registers, allocator owner
table, source/descriptor fingerprints and independently visible odd pages.
A partial host payload must be an exact source prefix followed by untouched
initialization bytes. Neither completion marker may be present; the unused
host target must be unchanged. Two samples a second apart must be identical.
STOP must not change the terminal record; buffer-module removal must fail,
with the admission still `done=0 released=0` and guards unchanged.

Words 195–203 record the suspension: established flag, CSR, CCR, current
and next descriptor, byte count, DCR, settling iterations and stable iterations.
The existing 208-word record has room; no new RAM reservation is introduced.
The original words 175–194 retain entry/timeout/source/chain evidence.

Replay with `python3 rtems/accele160/fault/verify_dma.py ARCHIVE`. Native tests
cover the actual diagnostic's suspended path and timeout, plus rejection of
forged completion, progress, errors, corrupt payloads, markers and guards.
Hardware findings and reset recovery are recorded in the artifact batch.

This qualifies a deliberate per-channel hardware suspension. It does not
reproduce an unresponsive PCI target, indefinite PCI retry, failed internal
bus access, or an arbitrary damaged engine. The bound is a count of completed
MMIO polls, not a hard wall-clock deadline when the bus itself stops responding.
No resume, abort, or memory reclamation without reboot is claimed. Broader
stock SCSI/cache exclusion remains separate work.
