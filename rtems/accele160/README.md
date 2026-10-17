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
