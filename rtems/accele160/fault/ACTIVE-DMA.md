# Accele160 fault/NMI containment with active DMA

Profiles 6 (real `faulte`) and 7 (host-doorbell NMI) are isolated diagnostic
profiles. Profile 5 remains the normal prompt/runtime configuration. Never
load a diagnostic into an existing retained session: reset first, then use
fresh paired guarded firmware reads and the normal exact-card admission gate.

The diagnostic runs before Doom image admission. It uses an aligned interior
of the existing 900000-byte image allocation: 65536 immutable pattern bytes,
followed by 1025 aligned 32-byte descriptors. The first 1024 descriptors repeat
that source into the same existing guarded, coherent host target. The last
writes a 32-byte marker. This is a finite 64 MiB chain, not a circular list.
The other host target is left untouched. Both targets and all card allocations
retain their existing reboot-only lifetime. No new PCI target is accepted.

The card first validates DMA configuration and all three idle channels. It
waits a bounded number of polls for Channel Active before injecting `faulte`
or publishing the doorbell arm acknowledgement. The NMI uses the same sole
host mapping, MU alias checks, and single IDR bit-31 write as profile 4.
The entry captures DMA0 CSR, CCR, NDAR and BCR immediately after the terminal
latch, before the C snapshot. Acceptance requires CSR bit 10 at **entry** and
no DMA error bits. A software pending flag or CCR enable alone is insufficient.

Intel 80303 developer's manual 273353-001, section 19.14.2, defines CSR bit 10
as active DMA transfers. CSR includes read-clear flags and is core-only;
this diagnostic owns those reads explicitly. The host must not snapshot the
MMIO page or attempt to read CSR through a translated PCI aperture.

After masking CPU interrupts/timer and switching to the terminal stack, the
handler saves its normal fault/NMI record and observes at most 10,000,000 CSR
polls. It records completion or timeout without disabling DMA, restoring stock
handlers, returning to firmware, or releasing anything. DONE means the terminal
record is published, **not** that the firmware command completed. Timeout and
errors still lead to a retained terminal park. Acceptance requires the final
marker descriptor, zero BCR/NDAR, inactive/error-free CSR, intact host guards,
unchanged source/chain, and an untouched second target. Full post-drain FNVs cover source and chain;
independent host comparisons cover every visible odd page. The existing PCI
aperture cannot directly read the intervening even pages. The complete host
DMA payload is checked byte-for-byte. The test then proves
STOP cannot turn that park into completion and ordinary module removal is
refused. Reset is the only supported recovery.

Record words 176–179 hold the entry hardware sample; 180–185 identify the
chain/source/target/count/start CSR/marker; 175 counts final observation polls;
186–191 hold final CSR/CCR/CDAR/NDAR/BCR/DCR; 192–194 hold full source/chain
FNVs and the peer-channel register check. Both stack guards are rechecked
after the bounded observation and hashing. The record remains within its
existing reserved page. The assembly build must receive ACCELE_TERMINAL_TEST;
otherwise its conditional entry sample would silently be absent.

Replay evidence with `python3 rtems/accele160/fault/verify_dma.py ARCHIVE`.
The replay validates raw records, exact bundle hashes and entry symbols,
source/descriptors, guarded host payloads, denied release, retained command,
and paired firmware reads. Hardware qualification and recovery results are
recorded in the corresponding artifact batch README. Native tests alone do
not establish DMA containment.

This does not establish aborting a stalled DMA engine, reclamation after a
fault, exclusion of stock SCSI/cache activity, or resuming an interrupted task.
Profiles 6/7 do not exercise the hardware timeout branch. The later
[profiles 8/9](STALLED-DMA.md) test deliberate hardware suspension; arbitrary
stalled-engine failure remains unqualified. A later transfer completion never authorizes
resource reuse by itself.
