# Accele160 diagnostic DMA resume after timeout

Profiles 10/11 extend the suspended-DMA exception diagnostic with a single controlled
resume of its existing finite chain. These are isolated diagnostics, not a runtime
fault recovery policy. Normal profile 5 and suspended profiles 8/9 retain their
behavior. Sources, descriptors, guarded host destinations and the pending
firmware callback remain owned until reset, including after successful DMA.

Intel 80303 manual 273353-001, section 19.14.1, documents that setting CCR.Channel
Enable after suspension resumes the current transfer with its queued data.
Each profile sets only that bit in DMA0 CCR. It does not set Chain Resume, reload
NDAR, alter PCI bus-master configuration, or access another channel.

The diagnostic first builds the same finite 1024 × 64 KiB chain and marker,
records fingerprints, observes active DMA, clears CE, and establishes 4096
stable samples. Real `faulte` (10) or host-doorbell NMI (11) enters the owned handler and exhausts the existing
10000000-poll observer. The original timeout fields remain immutable thereafter.

A one-shot gate checks exception identity, claim, context-switch state, both owned
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
| 221–223 | Profile 11: post-acknowledgement IISR, IDR and IIMR before CE resume |

Native tests execute the actual C diagnostic with simulated MMIO, covering gate
refusals, a latched retry, second timeout and successful completion. Host negative
tests reject altered timeout, completion, fingerprints and guards. Hardware
captures and reset recovery belong in the associated artifact batch.

This does not prove arbitrary fault recovery, arbitrary NMI recovery, task restart,
abort, safe memory reclamation, or tolerance of an unresponsive PCI target.
Both bounds count completed MMIO reads, not wall-clock time if the bus hangs.


## Profile 11: NMI-specific resume gate

The owner verifies the MU host/core register aliases, then issues exactly one
PCI doorbell bit-31 write after the card arms the test. It does not invoke the
handler directly. The owned handler captures the real vector 248 and NMI source,
masks the injected doorbell, and acknowledges only its IDR bit 31. The timeout
observer runs before the one-shot resume gate.

In addition to all shared checks, resume requires exception kind 2/code 0x7d004,
vector 248, the test armed, NISR exactly 0x100, the original IISR bit 3/IDR bit 31
set, and the original mask bit clear. The recorded post-ack IISR must equal the
original with only bit 3 cleared; IDR must equal the original with only bit 31
cleared; IIMR must equal the original with only bit 3 set. A mismatch refuses CE.
These checks follow manual 273353-001 sections 16.4.2 and 16.8.3–16.8.5: masking
does not clear status, and clearing IDR bit 31 clears the NMI doorbell status.
No IISR write or general NMI source clear is introduced.
After terminal publication, the host independently reads the PCI MU aliases
and requires equality with the core acknowledgement snapshot (`mu-after.json`).

Native tests reject incorrect vector, source, arm state, acknowledgement and
mask, in addition to the shared gate and bounded observer cases. Hardware results
and recovery are recorded in the NMI resume artifact batch. The normal service
continues to use the previously qualified profile-5 bundle.
