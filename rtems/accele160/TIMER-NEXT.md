# Next AcceleRAID clock and STOP gates

The accepted 2026-10-17 RTEMS image proves scheduling through synchronous `rtems_clock_tick()` calls only. Its fixed operation-9 admission and one-shot callback cannot run an arbitrary replacement image. Hardware timer/interrupt ownership and host STOP require another exact payload and a separately audited flash candidate. Keep the current image as the known-good rollback point.

A [reproducible stock-ROM literal scan](../../artifacts/current/accele160-rtems-20261017/timer-static.json) found no aligned direct `0xff000310` (timer-1 reload), `0xff000318` (timer-1 mode), `0xff008510` (interrupt configuration) or `0xff008528` (interrupt map 2) words in the expanded runtime or copied loader. It found one `0xff000314` (candidate timer-1 count) word and several pending/mask words. This narrow negative result is **not** a free-timer claim: the firmware may calculate register addresses, use a base register, or touch them via another processor or device path. The addresses come from the existing DAC960PG i960Rx timer experiment and need new-board confirmation against the [Intel 80303 developer's manual](https://www.bitsavers.org/components/intel/i960/80303/273353-001_Intel_80303_IO_Processor_Developers_Manual_May2000.pdf). That older profile is an implementation reference, not evidence that the AcceleRAID has the same vector table, clock rate, mask or pending state.

The next read-only image should save a bounded register/PRCB/vector inventory into its owned report, without changing timer, interrupt or cache controls. Verify the manual's read side effects first: the older profile explicitly avoided reading timer mode until count, reload, pending and mask were known idle, because a mode read clears terminal-count state. Pin exact new-card BDF, firmware and payload identities, repeat snapshots, compare all owner and flash audits, and restore the loader page. A zero register is observation, not ownership.

On 2026-10-17 the first observational gate was built as a fixed firmware
operation 10, preserving accepted operations 1–9. The [Intel 80303 manual](https://bitsavers.trailing-edge.com/components/intel/i960/273353-001_Intel_80303_IO_Processor_Developers_Manual_May2000.pdf)
confirms the TMRx read-clear side effect (18.1.1.1) and timer count/reload
addresses (18.1.2–18.1.3); the [i960 Jx manual](https://bitsavers.trailing-edge.com/components/intel/i960/272483-001_Intel_i960_Jx_Microprocessor_Users_Manual_Sep94.pdf)
identifies the PRCB, ISP and SSP registers. The fixed command reads only the
documented non-mode registers and stock-ROM PRCB words; it writes a bounded
report to the saved loader page and does not allocate grant memory. The
[candidate and current status](../../artifacts/current/accele160-inventory-20261017/README.md)
are recorded separately. Three live operation-10 calls returned normally;
two postboot and one post-call complete flash reads matched the candidate,
and all 512 allocator records plus the loader page restored. Timer-1
reload/count were `0/0`, pending was zero, and timer-1 was masked. Timer-0
count moved. The timer mode registers were deliberately not read, so this is
still an observation, not a timer-1 ownership grant. Two bytes at owner-page
offsets `0xaa0..0xaa1` changed with stock activity outside the allocator's
`0x2a0..0xa9f` count/owner arrays; the first host checker stopped there,
captured and restored the completed command, then two fresh runs passed with
the exact metadata boundary.

The [ROM/vector replay](../../artifacts/current/accele160-inventory-20261017/vector-static.json)
shows the live mapping field for timer 1 is zero (undefined vector 2), while
timer 0 maps to vector 130. Stock ROM vector 18 is blank, but ICON `0x6000`
enables vector caching and the live cached word at `0x04` is still unknown.
An external source is mapped to a zero ROM entry too, so the ROM alone is
not an ownership map. Before any timer write, capture that cached word and
the timer-1 mode read-clear state under a deliberately bounded command; do
not read the mode casually or treat a blank ROM word as a free vector.

After a stable inventory, qualify a short timer-1 experiment under a fresh exact image: refuse non-idle timer/vector/mask state, save every borrowed word, use an owned interrupt stack and complete context preservation, run a fixed small number of ticks, disable the source, drain the interrupt, restore original registers and verify them before RTEMS returns. Retain the grant and command on any uncertain completion; reboot recovery is required for an unreturned handler. Measure the actual clock against host time before choosing RTEMS tick frequency.

Independent STOP needs a control path that can operate while the command callback is pending. The current command companion serializes a single `dcmd_mutex` operation, so another normal mailbox command cannot be assumed to interrupt it. On 2026-10-17 the [operation-11 sideband proof](../../artifacts/current/accele160-stop-20261017/README.md) did this through the saved loader page: exact nonce/epoch admission, stale-token rejection, a card-visible READY and ACK, and a finite no-host deadline. The host wrote the STOP word while the direct command was pending. Exact STOP returned status 0 in a 21.9 ms host-observed cycle; no STOP returned stock status 2 after 10.26 s. Two full postboot reads and a post-call full read matched firmware, the loader page and PCI aperture restored, and all 512 owner records matched. This is a bounded callback proof, not RTEMS task quiescence, a physical DMA drain or an IRQ-context cancellation guarantee.

The next timer experiment should first read the live cached-vector word and deliberately qualify timer-1 mode's read-clear behavior. It can then borrow a vector only after proving its original state and installing an owned interrupt stack. Route a valid sideband STOP to task quiescence, disable and drain the timer, restore all saved registers/table/stack state, and verify the original host-visible page and owner records. Keep a card-side deadline and retain resources on uncertain completion. Do not infer a free vector from a blank stock-ROM entry: ICON enables live vector caching, and an active external source already has a blank ROM entry.

Only after timer + independent STOP restoration passes should the new-board network relay and web server be ported. Doom additionally needs a separately owned multi-megabyte arena; the 512 KiB grant does not satisfy its memory contract.
