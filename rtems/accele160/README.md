# Bounded RTEMS gate on the AcceleRAID 160

The 2026-10-17 [physical acceptance](../../artifacts/current/accele160-rtems-20261017/README.md) runs a newly linked RTEMS 4.6.6 image from the card's stock-owned 512 KiB grant. This is a **normally returning, one-shot software-clock profile**. RTEMS creates a worker, advances ten synchronous `rtems_clock_tick()` calls, observes that the worker wakes at tick five, writes an eight-word report, and returns to the stock command completion path. The host releases the grant only after the result and owner state pass. Hardware timer/interrupt ownership, asynchronous STOP, networking, persistence and Doom remain separate gates.

`rtems/build.py --profile accele160` compiles the same pinned RTEMS core as the old-board bounded profile, but uses this board's own [entry](start.S), [linker map](link.ld), [application](app.c), and minimal [libc](libc.c)/[context switch](context.S). It does not load a DAC960PG binary. The entry saves/restores the firmware PC, `g8..g15`, PFP and SP on normal return; interrupt level remains 31. The report is at `c000f800`, outside the owned image but inside the fixed loader page. The host saves and restores the entire page.

The [manifest tool](manifest.py) rejects an entry/BSS outside the uploaded image or an image crossing the last staging page. The accepted flat image is 57,972 bytes (23,300 bytes of text/data plus 34,672 bytes of BSS and tail), padded to 15 pages / 61,440 bytes. It occupies `c0710000..c071efff`; BSS ends at `c071e270`. The stock allocation is `c0710000..c078ffff`, with `c078f000` held as the final staging page, leaving 112 payload pages unused. The full [manifest](../../artifacts/current/accele160-rtems-20261017/image/manifest.json) pins the SHA-256 and FNV.

The separate [operation-9 handler](../../host/accele160/rtems_gate/handler.S) preserves ops 1–8 and adds only a fixed 15-page RTEMS admission. It checks the exact owner/address/size, nonce, page count, embedded whole-image FNV and embedded first 80 bytes, invalidates D/I caches, calls only the fixed grant base, then validates normal return and every report word. FNV is a transfer-integrity check, not a cryptographic signature; the trusted host also pins exact SHA-256 for the payload, firmware and command modules. A rejected or pending command retains resources for inspection. No host pointer or DMA descriptor comes from the mailbox.

To reproduce the archived build on the test PC with the pinned `sources/` and cross-tools, use an isolated work directory containing `project/rtems` and run:

```sh
python3 project/rtems/build.py --work "$PWD" --profile accele160
python3 project/rtems/accele160/manifest.py accele160/kernel.bin accele160/kernel.symbols image
```

The exact binary and build metadata are in the acceptance artifact. The physical harness is [run_rtems.py](../../host/accele160/rtems_gate/run_rtems.py); read its pinned preflight and the artifact README before running. It requires two same-boot full guarded flash reads and exact BDF `0000:37:09.1`, and it refuses a bound old card. It uploads one page at a time through the odd-page aperture, checks each card copy, checks a whole-image digest, tests bad hash/count rejection, runs RTEMS, then restores staging, loader and all 512 allocator metadata words. Do not force-unload a retained companion if a command is pending or a result is uncertain.

The subsequent [read-only hardware inventory](../../artifacts/current/accele160-inventory-20261017/README.md)
passed three fixed operation-10 calls with full flash, owner and loader-page
audits. Timer 0 was active; timer 1 had zero count/reload, no pending interrupt
and its interrupt masked. The mode registers were intentionally not read because
reading them clears terminal-count status. This observation does not transfer
timer/vector/stack ownership to RTEMS.

The following [operation-11 sideband gate](../../artifacts/current/accele160-stop-20261017/README.md)
passed a real concurrent host STOP while the stock direct-command mutex was
held. Wrong STOP remained pending; exact nonce/epoch STOP returned ACK and
status 0 in a 21.9 ms host-observed cycle. An absent STOP returned status 2
at the card's fixed deadline after 10.26 s. Two postboot and one post-call
full flash reads, complete loader-page restoration and all 512 owner words
passed. It proves a separately writable control word and bounded callback,
not STOP of an arbitrary RTEMS task or an interrupt/DMA drain.

The [operation-12 vector/mode result](../../artifacts/current/accele160-vector-20261017/README.md)
observed cached vector 18 `0xaaaaaaaa` and cached vector 130
`0xc0000418`. The guarded timer-1 mode read returned `0`, with count,
reload, pending, mask and mapping unchanged. Operation-11 STOP still passed
on the new image, and six full flash audits matched. The cached sentinel
means a blank ROM entry cannot be treated as a free vector.

The [operation-13 reusable RAM gate](../../artifacts/current/accele160-ram-admit-20261017/README.md)
now accepts a reviewed, returning image from the same grant. Two different
one-page binaries ran without another flash, six bad manifests were rejected,
four postboot/postcall full reads matched, and the previous STOP and fixed
RTEMS operations passed again. This makes small RAM-only code experiments
repeatable. It does not yet enforce a finite lease, own an independent task
stack or stop a nonreturning task.

A following [RAM-only owned-stack/STOP probe](../../artifacts/current/accele160-lease-20261017/README.md)
ran a worker on the grant's second page. Its firmware SP restored exactly;
a valid host STOP returned ACK in 23.4 ms, and a missing STOP exited a
fixed poll budget after 1.04 s. An invalid direct read of the even code
page was caught and the completed grant was safely released; the accepted
run uses card digests for that page and PCI readback for the odd stack page.
The same firmware passed its post-call full read. This is cooperative code,
not RTEMS task STOP or an independently enforced deadline.

The old-card loader/RTEMS comparison and the reason for repeated new-card
flash cycles are in [bring-up differences](OLD-NEW-DIFFERENCES.md).
Host-backed IPv4/IPv6 and web service follow later; Doom also requires a
separately owned multi-megabyte arena and frame transport.

The [RTEMS task lease](lease/README.md) now completes that first task-level
gate without another flash write. A worker task running in the 16-page
owned image acknowledged valid STOP in 48.829 ms after a stale token stayed
pending; the no-host path exited after 2,000,000 polls in 1.503 s. RTEMS
deleted the worker and returned through the restored firmware context.
Full pre/post flash, owner, loader-page, stage and stack audits passed;
the [card evidence](../../artifacts/current/accele160-rtems-lease-20261017/README.md)
replays offline. Next is a guarded, short timer/vector/interrupt-stack
experiment with complete state restoration and a card-side deadline. This
task STOP remains cooperative and cannot recover an arbitrary hung task.

The next [bounded timer gate](timer/README.md) also passed without another
firmware write. A three-page RAM image borrowed timer 1 and cached vector
18, received 8 fixed interrupts twice, then tested stale/valid STOP after
13 and 201 interrupts. ISR C code ran on an owned second page while the
hardware frame stayed on an owned entry-stack page. The longer host sample
was 1,253.04 interrupts/s at reload 10,000. Three pre/post inventories,
four guarded full flash reads and complete page/owner restoration passed;
[exact evidence](../../artifacts/current/accele160-timer-20261017/README.md)
replays offline. This is bare interrupt handling; the next gate is a bounded
RTEMS tick/worker wakeup using that timer with STOP and exact restoration.

The [combined RTEMS/timer gate](autoclock/README.md) is now accepted in two
repeated bounded batches without another flash write. Timer 1 woke the worker
at tick 5 and continued through 52 ticks during each CPU-bound no-host run;
STOP, finite exit, exact state restoration, six full flash reads and
independent vector/timer inventories passed. The initial false guard and
interrupt-priority experiments are preserved in its artifact. This is not yet
unrestricted task preemption or a resident service on the new board.

The following [bounded preemption gate](preempt/README.md) has now passed twice
on the new card without another firmware write. It uses three separate owned
8 KiB ISR continuations, time-slices two CPU-bound RTEMS workers from timer 1,
and drains both on valid STOP or a 120-tick deadline. The observed STOP and
no-host paths made 8 and 120 handoffs respectively, with exact timer/vector,
firmware-context, loader-page, stage and owner restoration. Six full flash
reads and independent post-run inventories passed. The [exact evidence](../../artifacts/current/accele160-preempt-20261017/README.md)
replays and rejects four tamper cases. It proves bounded preemption while
interrupts stay enabled; an independently enforceable resident lease and
memory/DMA ownership remain to be built before networking or Doom.

The following [STOP-ignoring containment gate](contain/README.md) also passed
twice without another firmware write. Two CPU-bound RTEMS workers ignored the
host sideband; a priority-1 controller observed four more ticks of progress
then suspended them externally. The workers' original ISR continuations
remained live until the whole one-shot instance returned to firmware. STOP
completed at 14 ticks and the no-host lease expired at 124 ticks; four full
flash reads and independent stock-state inventories passed. The [exact card
evidence](../../artifacts/current/accele160-contain-20261017/README.md)
replays offline. This tests containment of interrupt-enabled workers, not an
independent hardware watchdog or callback-free resident runtime.

The next [callback-free handoff gate](handoff/README.md) passed a RAM-only
expiry/HALT batch. Operation 13 returned in about 10.6 ms while an owned
timer-1 ISR remained active. The host's subsequent ENTER was consumed in a
stock-firmware frame; no-host expiry ended at 300 ticks in 3.048 seconds,
while valid HALT ended at four ticks in 88.5 ms after a wrong token remained
pending. Both paths restored processor priority, timer/vector/map/mask,
firmware stack, loader page, stage and all allocator records. Four same-boot
full flash reads and independent pre/post inventories passed. The [exact
evidence](../../artifacts/current/accele160-handoff-20261017/README.md)
replays offline and rejects four tamper cases. This is a bare finite monitor,
not resident RTEMS or a watchdog for permanently masked interrupts; RAM and
DMA ownership plus task quiescence remain the next gates for services.

The following [callback-free RTEMS timer gate](residentclock/README.md)
early-initialized RTEMS 4.6.6 under the same finite lease. An RTEMS one-shot
timer callback fired at tick 20 after the firmware call returned and after
host ENTER. Valid HALT ended at tick 21 / 286.276 ms and no-host expiry at
tick 300 / 3,076.707 ms. Four full same-boot flash reads, independent
pre/post inventories and complete owner/page/stage restoration passed; the
[exact evidence](../../artifacts/current/accele160-residentclock-20261017/README.md)
replays with five tamper rejections. This is still **not a resident RTEMS
task**: task multitasking never began. Task handoff and quiescence, explicit
RAM/DMA ownership and a recovery boundary remain before network or Doom.

The subsequent [resident-task gate](residenttask/README.md) crossed the
task boundary. Its retained stock-firmware ISR started one RTEMS task after
operation 13 returned. The task made progress on its RTEMS workspace stack,
received hardware timer interrupts, ignored stale STOP and ended on exact
HALT at tick 22 or finite expiry at tick 300. Shutdown returned to the
retained ISR, which restored the borrowed timer/vector/map/mask and original
firmware priority before returning to stock code. Two unchanged-image
batches, six complete flash reads and three independent inventories passed;
the [exact captures](../../artifacts/current/accele160-residenttask-20261017/README.md)
replay with seven tamper rejections. This is one bounded task with
whole-instance disposal. Explicit DMA ownership, multi-task/service drain
and a deadline independent of working interrupts remain future gates.
