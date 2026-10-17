# AcceleRAID Doom variable startup stall localization

The 2026-10-17 diagnostic build preserved the same exact admitted Doom engine,
5043-request native WAD oracle, full paired stock-firmware reads, 8 MiB arena,
owner/guard checks and old-card isolation. It added a 16-word, host-readable
runtime trace at `0xc000fcc0`. The pre-run complete reads were the two
`i960-accele160-fps-20261017-post-{0,1}` captures on boot
`e933df02-43f6-43b9-87a3-c88f93cdd9d4`, both matching stock SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
No firmware write occurred and the old card remained unbound.

The host served 1401 oracle-matching WAD requests. At 35.059 seconds both
worker ISR counts were still rising (748 each), the owner fault word was zero,
and the engine was progressing. By 36.061 seconds both worker counts had
stopped at 760, `switch_fault` became `0x40`, and the engine entered WAD read
1402 but stopped before request publication. The timer continued at 100 Hz and
the Init ISR count continued rising. The `0x40` bit is set only by
`timer_isr.S:slot_bad`, when `_Thread_Executing` does not match any of the
three registered task owners. `engine_owner()` sees the fault and the callback
returned an error to Doom.
This explains why the stop position varies with host pacing. It is a
control/scheduling fault, not a bad WAD offset or checksum.

The 120-second no-progress guard saved the final page and trace, published
STOP, and left the callback/grant retained for whole-PC reset. The captured
`engine-trace.json`, `engine-stall.json`, `engine-stall-page.bin`,
`engine-latest-page.bin`, and `engine-reads.json` are the exact host outputs.
The first proposed fix kept both workers runnable until STOP or a finite
200000-tick deadline. **Its card run also failed** at 1400 oracle-matching
reads, with the same fault. A guarded snapshot of the still-retained image
showed `done=(0,0)`, `switch_stop=0`, worker loop counters below 14 million,
and `switch_active=(0,1,1)`. The workers had **not** exhausted their loops.
Both were parked in owned ISR dispatch continuations while Init slept, and
RTEMS selected its idle thread. That fourth context was missing from the
ISR's explicit owner table. `fixed-attempt0/` contains this correction's
exact trace, WAD receipts and fault page. The host published STOP and retained
the callback/grant for reset.

The next build added `_Thread_Idle` as a fourth explicit ISR owner with its
own 8 KiB stack, frame/lifetime checks, and drain condition. It increased the
RTEMS RAM image from 27 to 29 pages without changing the 8 MiB Doom arena or
firmware. **That run also failed** at 1400 oracle-matching reads. The idle
pointer was registered correctly. `idle-attempt0/` retains this run.

The third diagnostic build recorded the actual `slot_bad` value and interrupted
address. At the fault, its saved value was `1`, whereas all four task pointers
were valid `0xc075e...` values. Disassembly shows `1` was the active flag
loaded after the owner comparison, so this was **same-owner ISR reentry**, not
an unknown task. The interrupted address `0xc0714570` lies in RTEMS
`_Thread_Dispatch`, after it lowers the interrupt level while the earlier ISR
continuation has not yet unwound. The reentrant interrupt arrived on that
owner's still-active ISR stack. `unknown-attempt0/` holds the exact page and
BSS capture. The next candidate counts this narrow reentry and returns from
it without replacing the active save area or invoking dispatch again.
The first candidate with this behavior, `accepted-0`, passed the full bounded
32-frame run on boot `320d62df-163c-47b1-9921-22e28b39fff7`. Two same-boot,
guarded complete firmware reads preceded it; both matched the unchanged stock
SHA above with zero status, residual and guard changes. The host served 5,045
card WAD requests. The first 5,043 exactly matched the native startup oracle;
the last two were additional bounded reads during the frame sequence. All 32
frames, image/text/arena checks, full bank ownership checks, old-card isolation,
STOP and quiescence passed. Card presentation timing over 31 intervals was
847 ticks at 100 Hz, or **3.660 FPS**. Ten nested interrupts were counted
over 14,899 card ticks (~0.067%); `switch_fault` stayed zero. No new-card
browser delivery or input was tested, so this is **card-side render FPS** only.
`verify_accepted.py` replays the exact frame, timestamps, WAD prefix, owner
state, STOP and paired pre-run audit metadata. Full 1 MiB read data remains on
the test PC to avoid a redundant firmware blob in Git.

A normal reboot released that retained test module and grant. On the next
boot `19079ba3-6480-4c24-9e74-47d5e80cd571`, two guarded full 1 MiB reads
again matched unchanged stock firmware and served as preflight for an
**unchanged-image second run**. That run also served 5,045 WAD requests,
rendered all 32 frames, passed cleanup/STOP/full bank/owner checks and measured
the same **847 ticks / 3.660 card-side FPS**. It counted 11 nested events and
zero owner faults. The complete final framebuffer differs only in its timestamp
tail: the 64,000 pixels and 768-byte palette have identical SHA-256 across
both runs (`01c68ab3de900f6ecda08bf3c3fb0cb1f65adedea2771379acc8812929f7128c`
and `12bafa34214682ae20c2cb6f4e38f21575564de88c4599f3410661e9b7a5c6d3`).
`verify_accepted.py` checks both runs and this cross-run identity.

A normal reboot released the second retained run. On fresh boot
`d3cd3a69-fc5d-4be6-9278-e0942448a484`, two guarded complete READIMAGE reads
again matched the stock SHA with zero status, residual and guard changes.
The old card remained unbound. The compact metadata is in `accepted-1/post-0`
and `post-1`; full 1 MiB read data remains on the test PC at
`/home/mit/i960-accele160-fps-nested-20261017-final-post-{0,1}`. The first
run's post-reset pair also served as the second run's preflight, with matching
metadata copied to `accepted-0/post-{0,1}` for the replay. The interactive old-card
play/ping-pong harness is a separate port: this build has no keyboard input,
browser stream or new-card two-buffer host DMA ABI yet.

The working-tree `app.c` received one comment-only correction after both runs:
the workers' longer lease did not fix the stall. The accepted original source
is archived as `accepted-0/build/app.accepted.c` and matches SHA-256
`b94bd05a3a1f379d68c99b77158afe949b42e077b950486a201678eada56d0ea`.
The manifest source hash follows the corrected working-tree comment; executable
statements and the archived accepted kernel/image bytes are unchanged. A
rebuild comparison of that comment-only change is still open.
