# Accele160 diagnostic DMA resume after timeout

Profile 10 extends the suspended-DMA fault diagnostic with a single controlled
resume of its existing finite chain. It is an isolated diagnostic, not a runtime
fault recovery policy. Normal profile 5 and suspended profiles 8/9 retain their
behavior. Sources, descriptors, guarded host destinations and the pending
firmware callback remain owned until reset, including after successful DMA.

Intel 80303 manual 273353-001, section 19.14.1, documents that setting CCR.Channel
Enable after suspension resumes the current transfer with its queued data.
Profile 10 sets only that bit in DMA0 CCR. It does not set Chain Resume, reload
NDAR, alter PCI bus-master configuration, or access another channel.

The diagnostic first builds the same finite 1024 × 64 KiB chain and marker,
records fingerprints, observes active DMA, clears CE, and establishes 4096
stable samples. Real `faulte` enters the owned handler and exhausts the existing
10000000-poll observer. The original timeout fields remain immutable thereafter.

A one-shot gate checks fault identity, claim, context-switch state, both owned
stack guards and exception ownership, timeout count, suspended descriptor/count,
source and chain fingerprints, and unchanged peer registers. It then checks the
live DMA0 registers against the timeout record. Any mismatch refuses the write;
the attempt latch prevents retry. Passing the gate sets CE and observes a second
10000000-poll bound. No path synthesizes firmware completion or releases memory.

Completion requires inactive/error-free CSR, enabled CCR, the final descriptor,
zero NDAR/BCR, DCR 7, intact fingerprints, unchanged peers and valid ownership.
The host independently requires the complete payload and final marker in slot 0,
untouched slot 1, intact destination guards, visible source/descriptor pages,
unchanged allocator owner table, denied module unload, and unchanged retained
buffers after the owner exits. A second timeout or error is a failed diagnostic,
with resources retained for reset; it is never reported as successful recovery.

The report uses 224 words in the existing 4 KiB record page:

| Words | Meaning |
| --- | --- |
| 175–203 | Original entry, suspension and exhausted timeout evidence |
| 204–205 | Source and descriptor fingerprints before initial DMA |
| 208 | Attempt: 1 refused, 2 enabled but not qualified, 3 qualified completion |
| 209 | CSR immediately before resume |
| 210 | Resume observer iterations |
| 211–216 | Resume CSR, CCR, DAR, NDAR, BCR, DCR |
| 217–218 | Source and descriptor fingerprints after resume observation |
| 219–220 | Unchanged peer registers and valid stack/exception ownership |

Native tests execute the actual C diagnostic with simulated MMIO, covering gate
refusals, a latched retry, second timeout and successful completion. Host negative
tests reject altered timeout, completion, fingerprints and guards. Hardware
captures and reset recovery belong in the associated artifact batch.

This does not prove arbitrary fault recovery, an NMI resume path, task restart,
abort, safe memory reclamation, or tolerance of an unresponsive PCI target.
Both bounds count completed MMIO reads, not wall-clock time if the bus hangs.
