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

Next: measure the new board's timer/vector/mask ownership without borrowing stock resources, add a bounded independently controlled STOP path, then host-backed IPv4/IPv6 and web service. Doom requires a separately owned multi-megabyte arena and frame transport.
