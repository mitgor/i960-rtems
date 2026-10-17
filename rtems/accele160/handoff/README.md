# Callback-free timer handoff (AcceleRAID 160)

**Accepted on the new card, 2026-10-17.** This three-page RAM-only image
returns from operation 13 while retaining a finite timer-1/vector-18 monitor.
The host sends ENTER only after the firmware callback has completed. The ISR
confirms an interrupt frame in stock firmware, then accepts a valid HALT or
expires at 300 hardware ticks. The accepted no-host expiry took 3,048.106 ms;
the callback had returned after 10.573 ms. Valid HALT took 88.471 ms and four
ticks, with callback return at 10.595 ms. A wrong token stayed pending.

Both paths logged zero ISR faults and restored the borrowed timer, cached
vector, mapping, mask, firmware stack and saved processor priority. Four full
flash reads and independent stock-state inventories bracketed the accepted
batch. The loader page, stage and all 512 allocator records restored. No
firmware was written and the old DAC960PG stayed unbound. The [exact image,
captures and offline replay](../../../artifacts/current/accele160-handoff-20261017/README.md)
are retained.

The entry switches to an owned stack, arms the timer under exact stock-state
guards, and returns at processor priority 0. The ISR has a separate owned
stack and saves the globals and trace controls. On HALT or expiry it masks and
disables timer 1, clears its pending bit, restores the saved vector/mapping/
mask and timer words, then restores the original priority in the interrupted
firmware frame. [Intel's i960 Jx manual,
§11.5](https://www.manualslib.com/manual/522595/Intel-I960-Jx.html?page=333)
places the saved process controls at `FP-16`; its [interrupt-return
description](https://www.manualslib.com/manual/522595/Intel-I960-Jx.html?page=205)
shows `ret` restoring that word. The accepted trace recorded priority-0
control word `0x2002` at ENTER and restored firmware word `0x62002` at exit.

The host runner pins the new-card BDF, stock firmware, operation-13 handler,
command modules and image SHA-256. It requires two same-boot complete flash
reads, exact stock timer/vector preflight, odd-page readback and a card-side
whole-image digest. It retains the grant on uncertain completion. The
[offline verifier](verify_live.py) rechecks image identity, both sideband
paths, bounded ISR stack, context/priority restoration, complete page and
owner restoration, four full flash reads and two independent inventories;
[tamper checks](test_verify_live.py) reject altered flash, owner, ISR fault
and stale-token evidence.

Four diagnostic runs preceded acceptance. The first returned at the stock
priority and saw no timer tick after callback completion. The second used an
overstrict entry-priority guard and returned status 2 before arming. The third
used a zero `modpc` mask, so the intended priority-0 transition did not
occur. The fourth reached ENTER and exact 300-tick expiry, but the host wait
was only 2.5 seconds and a separate host predicate mistook the saved process
controls for an instruction address. Its completed call was recovered under
exact page, owner and stage guards. The corrected host wait and predicate
passed the full expiry/HALT batch. The earlier raw captures remain in the
artifact for diagnosis; they are not alternate accepted images.

This is a bare callback-free monitor, **not a resident RTEMS service or an
independent watchdog**. Expiry requires continuing hardware interrupts; code
that masks them indefinitely can defeat it. It has not admitted RTEMS tasks,
network traffic, Doom, or DMA after callback return. A next resident gate
must put a bounded RTEMS control task under this lease, establish explicit
RAM and DMA ownership and prove quiescence before releasing either resource.
