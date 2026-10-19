# Accele160 diagnostic resume refusal

Profile 12 tests the refusal side of the existing controlled-resume gate. It
uses the same finite source, descriptor chain, guarded pinned host targets and
real `faulte` entry as profile 10. Only diagnostic evidence is corrupted; no
DMA address, source byte, descriptor, stack guard or hardware register is
corrupted. Normal service remains the original profile-5 bundle.

After deliberate DMA0 CE suspension and the first 10000000-poll timeout, the
handler saves the correct expected source fingerprint, flips its low bit in
the diagnostic record, and invokes the actual resume gate. The expected result
is attempt state 1 (refused) without reaching the live-enable write. It restores
the expected fingerprint and invokes the same gate again. The latched attempt
must refuse that corrected retry too. Neither invocation clears the latch.

A second independent 10000000-poll observer then records the outstanding hardware
state. Acceptance requires CSR=0x400, CCR=0 and exactly the original DAR/NDAR/BCR/
DCR after both timeouts, unchanged source/chain fingerprints, peer registers,
stack guards and exception ownership. Resume completion fields must stay zero.
Host validation requires a stable partial source prefix, no completion marker,
an untouched second target, unchanged allocator ownership, denied module unload
and matching retained buffers after owner-process exit. STOP must not convert
the parked handler into completion. All resources remain owned until reset.

The record grows to 240 words within its existing 4 KiB allocation. Existing
profiles retain their field meanings; older archives remain readable.

| Words | Meaning |
| --- | --- |
| 224–225 | Original and deliberately invalid expected source fingerprint |
| 226–227 | Attempt state after initial refusal and corrected retry |
| 228 | Second observer poll count |
| 229–234 | Second observer CSR, CCR, DAR, NDAR, BCR, DCR |
| 235–236 | Source and descriptor fingerprints after second timeout |
| 237–238 | Unchanged peer registers and valid owned stacks/vectors |

The original expected fingerprint at word 204 is restored before the second
call; the deliberately invalid value stays in word 225. Original timeout and
suspension fields remain intact. Words 208–223 must be `(1, 0, …, 0)`.

Native tests execute this actual C path with simulated MMIO and reject forged
refusal, retry, timeout, completion and ownership evidence. Hardware results,
binaries and reset recovery belong to the associated artifact batch.

This qualifies a deliberate evidence mismatch and a latched retry through the
fault path. It does not establish arbitrary corruption recovery, NMI-path gate
refusal, DMA abort, release without reset or a wall-clock deadline on a blocked
bus. Both bounds count completed MMIO reads.
