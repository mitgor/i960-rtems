# AcceleRAID 160: first real Doom frame gate

**First-frame gate passed on the third run:** 5,043 engine WAD reads matched
the native request trace, one real 320×200 Doom frame was read back in 16
checked pages, and engine-owned exit, all arena loans, executable text,
timer/STOP and old-card isolation passed. Engine entry to first frame took
123.54 seconds. The retained session was reset; two guarded complete post-reset flash reads passed on boot `c9773c0f-9b64-414b-8712-4d9e6bf1ae5e`. [Exact image, frame and evidence](../../../artifacts/current/accele160-doom-first-frame-20261017/README.md).
This is not sustained play or a measured FPS.

This builds on the [accepted full-WAD service](../doom_wad_service/README.md).
The card at `0000:37:09.1` admits the same pinned Doom engine into the
verified 8 MiB upper bank, then calls its owned entry once from an RTEMS
task. A guarded 6 MiB zone, checked 4 KiB WAD cache, 64 KiB framebuffer,
bounded read callbacks, STOP and timer ownership remain in force. The old
DAC960PG at `0000:37:04.1` must stay unbound. This is a RAM-only test; the
stock firmware callback and grant stay retained until whole-card reset.

`app.c` supplies the engine's allocation, file, clock, owner, wait, STOP and
frame-mark callbacks. The card publishes each exact WAD request; the host
provides the immutable file slice, and the card checks sequence, bounds,
length and FNV before and after copying. Any post-copy checksum failure
quarantines the card session. The first real frame, if reached, is copied into
the guarded frame allocation, read back in 16 checked pages, and must cause
the engine to leave through its owned 210 boundary. All engine loans must be
released and its executable text hash must remain unchanged before STOP.

The first two physical engine attempts **did not produce a game frame**.
The first monitor initially mishandled the uninitialized engine-report
sentinel, leaving the host absent for the first WAD request; its 500-tick
timeout worked. The corrected monitor then served 1,401 actual engine
requests, with the first 1,400 recorded requests matching the native trace,
but the engine made no further progress. After reset, an instrumented run
served 3,801 requests, all matching the native trace, then made no WAD or
frame progress for 120 seconds. Host STOP was published; Doom did not reach
a cooperative STOP point. Those runs were diagnostic failures. Exact
captures and post-reset audits are in
[the artifact](../../../artifacts/current/accele160-doom-first-frame-20261017/README.md).

The current source adds a read counter and a grant-owned interrupt sample
ring at `c0772000`. The ISR records the interrupted return address without
changing the hardware frame. The host saves the ring if WAD/frame progress
stalls for 120 seconds, then publishes STOP. If STOP cannot be handled, keep
the module and grant retained until whole-PC reset. Do not unload them.

Build against the pinned new-card RTEMS library and i960 toolchain:

```sh
rtems/accele160/doom_first_frame/build.sh \
  /home/mit/i960-accele160-rtems-20261017/accele160 \
  /home/mit/i960/tools/bin OUT_DIR
```

The runner requires explicit exact module, handler, firmware, image, WAD,
template, relocation and two same-boot guarded full-flash read paths. It
refuses a changed identity, wrong BDF, bound old card, active stock
descriptor, block device or stale owner. The current binary hashes in
`run_bridge.py` must match the exact rebuild; do not substitute a new binary
without updating and reviewing those gates. No firmware write is issued.

Next: add bounded repeated frames, input and host presentation. Keep the same native
WAD request oracle, ownership/arena/frame audits, and reset-only release.
