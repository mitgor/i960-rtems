# Exclusive exception ownership — 2026-10-11

This is an opt-in, reboot-only extension of held secondary reset. Compile with
`--profile residentnet --secondary-reset --fault-owner`. Default and cooperative
profiles keep their previous behavior. No flash changes are made.

## Architecture and boundaries

Intel 272736-002 sections 8.2.3, 9.3–9.5 and 11.4.2 describe the cached NMI
vector, two-word fault entries, hardware records and PRCB. The existing live
PRCB is `feffd4d0`, pointing to fault table `c0000800`. We replace the 32
entries with local-call handlers and zero reserved words; we do not relocate
the PRCB. Cached NMI vector address zero and the interrupt-stack register also
become owned. Each is read back. The handlers do not return to stock firmware.

The terminal entry records the hardware frame and transfers C execution to a
separate 4 KiB guarded area. It masks hardware interrupts, stops scheduling,
and serves only snapshot/read/STOP acknowledgements through the existing
message channel. STOP acknowledges an already terminal state; it does not
release reset, restart tasks or free resources. A second exception during
terminal handling parks without calling C again. This is containment, not
fault recovery or continuation. A destroyed current stack can prevent the
processor from delivering a fault before our handler gains control; the new
stack does not remove that architectural limitation.

The owned-exception profile uses 68 packet slots, reserving space for its new
stack and record within the existing allocation. Other resident builds retain
72 slots. A queue-capacity reduction is explicitly recorded, not presented as
an increase in usable RAM. `RNT4` distinguishes this layout; snapshot bit 2
rechecks vector/table/stack ownership and guards.

## Physical evidence so far

The first image passed a 100-tick bounded probe, 33 firmware callbacks, exact
restoration and module unload. Its resident test deliberately executed `faulte`
after 100 timer ticks. The terminal capture contains type/subtype `00050001`,
IP `c0f2e930`, stable diagnostics, held SCSI reset, intact guards and no firmware
callback after ARM. The paired captures, pinned image/module and host control
transactions pass independent replay. Resources were retained at close.

## Real NMI test

Intel section 17.7.5 provides a separate mechanism from software interrupt
posting: an external PCI agent sets inbound-doorbell bit 31. The dedicated
`--fault-test 3` image unmasks IIMR bit 3 only after ownership/reset validation.
Its image-pinned module exposes one guarded ioctl; no normal module includes
that trigger. The actual test captured hardware vector 248, doorbell
`80000000`, mask `1f3`, and status bit 3. The handler restored mask `1fb`,
cleared the doorbell NMI latch and kept a stable terminal record. Native tests
cover refusal predicates, repeated injection and copy-out uncertainty.

The revised order installs exception ownership before reset, after phase-2
isolation. It passed synthetic entry, real constraint fault and physical NMI
sessions. No stock handler ran after those tested transitions.

## RAM investigation

`--extra-ram` additionally requires exception ownership and secondary reset.
It admits only this board and the fixed cache-data interval `c0200000..c0240000`.
The surviving monitor, RTEMS state and stacks stay inside the old allocation;
the parked firmware frame and low tables remain untouched. All fault entries
and NMI routing point to owned handlers. Hardware interrupts are limited to
our timer, and the pinned ROM interrupt table has no pending software interrupts.
This profile issues no software interrupt posts or system calls. i960 DMA is
idle/disabled, bus mastering denied and the secondary device held in reset;
the board's identified cache path is synchronous CPU XOR, not a running
independent cache engine.

Before granting the queue, the code flushes register frames, saves/disables
D-cache state, and checks four address-dependent patterns across 65,536 words.
Each pass verifies neighboring 64-byte ranges, the low 1.25 MiB firmware-memory
checksum and the immutable upload checksum. It invalidates/re-enables D-cache
according to saved state. The actual card passed this twice before final
network testing. Hashes supplement the fixed-range pattern/alias checks; they
are not an exhaustive proof against every possible alias or hardware fault.

The only new consumer is a 128 × 1,500-byte packet queue at `c0200040`.
Both ends of the tested region and the immediate queue end have guards.
Existing queued packets migrate before worker execution. The internal queue
stays reserved. Runtime validation checks queue pointer/capacity/index bounds,
RAM proof status, guards, exception ownership and held reset. A failed probe
enters terminal containment with its report; it never enables external storage.
Snapshot `RNT5`, words 48–51, and status bit 3 describe this limited grant.
The old `ram_reclaim()` and offline `ram_transfer.h` remain closed; this does
not extend the general RTEMS heap or authorize any other firmware memory.

See [batch artifacts](../../artifacts/notes/rtems-fault-ownership-20261011.md).
Manual source: https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF

## Reproduce and replay

Use a fresh exclusive session and the image-pinned module. Stop the cooperative
service normally before opening the card. Never force-unload a retained module.
A host reboot/power-cycle remains the exit from exclusive execution.

```sh
python3 rtems/build.py --work WORK --profile residentnet --secondary-reset --fault-owner --extra-ram
python3 rtems/residentnet/build_transport.py --out MODULE --payload WORK/residentnet/kernel.bin
make -C MODULE
sudo python3 rtems/residentnet/live.py --payload WORK/residentnet/kernel.bin --module MODULE/dac960auto.ko --output RUN --secondary-reset --fault-owner --extra-ram --ticks 24000 --rounds 6 --round-interval 20 --parallel --burst --drop-data --deadline
```

For exception experiments, add `--fault-test 1` (real constraint), `2`
(synthetic entry), or `3` (hardware doorbell NMI), rebuild the pinned module,
and use `live_fault.py --kind 1`, `3`, or `2` respectively. Each requires a
separate boot. Do not infer kind 2 from a synthetic test. `verify_fault.py`
checks hardware vector/source evidence for kind 2.

Extract each archive into its own root, and symlink `residentnet` to the archived
`scsi-drain/residentnet`. Use `verify_fault.py --root ROOT ROOT/RUN`, or
`verify.py` for the network capture. `verify_bounded.py` checks the bounded
restoration capture. `ram_audit.py ROOT/residentnet` checks linked storage; its
candidate-range description is deliberately not itself a live RAM grant.

Final network acceptance passed: 24,000 ticks, six concurrent IPv4/IPv6
rounds spaced 20 seconds apart, 160-packet saturation with 129 unique echoes
and 31 counted drops, deliberate TCP loss recovery, and drained IRQ contexts
at the deadline. The final bounded probe restored and unloaded after 33
callbacks. The normal network module has no NMI-test entry point.
