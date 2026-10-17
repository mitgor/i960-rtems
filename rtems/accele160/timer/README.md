# Bounded timer-1 and owned ISR-stack gate — AcceleRAID 160

This is a **RAM-only hardware experiment**, admitted by the accepted
operation-13 firmware. It does not run RTEMS. Its purpose is to prove that the
new card can borrow timer 1 and a cached vector briefly, receive interrupts
on owned RAM, then restore every borrowed register before returning to stock
firmware. The [live evidence](../../../artifacts/current/accele160-timer-20261017/README.md)
passed on 2026-10-17 without a firmware write.

The fresh operation-10/12 preflight found timer-1 reload/count/mode and
pending bit zero, IMSK `0x10c7`, ICON `0x6000`, IMAP2 `0x00080000`, cached
vector 18 `0xaaaaaaaa`, and cached vector F2 `0xe0000ff0`. F2 is a live
firmware pointer and is never changed. The RAM image refuses any drift in
these values, IMAP0/1, cached vector 130, or other exact stock guards before
arming. A guarded read of timer-1 mode is made only after zero count/reload,
pending clear and mask clear because the mode read clears terminal-count
status. The mapping field for timer 1 is temporarily set to vector 18, and
the sentinel there is saved and restored.

The image has three 4 KiB pages: code/data, an ISR C-stack page, and an
entry/hardware-frame stack page. The ISR preserves all 16 global registers,
the writable TC modes, and the original hardware frame; its C call uses the
second owned page. Normal entry preserves firmware PC/PFP/SP and `g8..g15`.
The test masks stock sources briefly, arms timer 1 at reload/count 10,000,
then lowers CPU priority. A fixed-poll bound, exact STOP token, or tick goal
ends the run. Cleanup raises priority, masks/disables the timer, clears its
pending bit, restores vector/map/reload/count/mask and checks them. This is
the same narrow interrupt-frame ownership model as the old-board ISR work;
it does not claim arbitrary nested preemption or an uncooperative-task
recovery mechanism.

The exact 12,288-byte [image](image.bin) has SHA-256
`09064cdb91661727a6c10ab93a5f149998fb9d9ca6b4e95e071f905be1cc8038`
and whole-image FNV `0x917f3e48`. It rebuilt byte-for-byte with the pinned
i960 GCC/binutils:

```sh
bash rtems/accele160/timer/build.sh /home/mit/i960/tools/bin /home/mit/i960-accele160-rtlease-20261017/timer-rebuild
```

`run_preflight.py` repeats the unchanged operation-10/12 reads with current
firmware and full paired flash audits. `run_timer.py` pins the image, firmware,
handler, card BDF and one-shot modules. It uploads all three pages under one
stock grant, checks every card-side copy digest and the whole-image digest,
runs the fixed-tick and STOP modes, checks owner/stack/page/command status,
restores the loader/staging pages and releases the grant. Uncertain completion
retains resources for inspection; never force-unload a pending callback.
The longer `--stop-after-ticks 200` call supplies a host-observed frequency
sample. After each batch, run operation-10/12 again and take a full guarded
flash read. The accepted capture contains two active batches and both post
inventories.

Offline replay and four negative mutations:

```sh
python3 rtems/accele160/timer/verify_live.py artifacts/current/accele160-timer-20261017
python3 rtems/accele160/timer/test_verify_live.py artifacts/current/accele160-timer-20261017
```

The next code change is to feed this proven timer ISR into bounded RTEMS
`rtems_clock_tick()` handling, with STOP quiescing the worker and then the
interrupt source before return. A resident service still needs a stronger
watchdog/lease contract, firmware-time accounting and owned networking RAM.
