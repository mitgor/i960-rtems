# AcceleRAID 160: bounded host-backed Doom WAD service

This is the next physical gate after the [Doom image bridge](../doom_bridge/README.md).
The retained operation-13 RTEMS image runs on **new card** `0000:37:09.1`.
The old DAC960PG at `0000:37:04.1` stays unbound. The image admits and
relocates the same exact Doom engine but deliberately does **not** call its
entry. This test establishes bounded, card-requested, read-only access to the
entire 28,795,076-byte Freedoom 1 WAD, with exact cache readback.

`app.c` owns a 4,096-byte guarded cache allocation and a sequence-numbered
request/reply record at `c000fc00`. The card publishes request sequence last;
the host writes file bytes and offset, length, FNV, status before publishing
the reply sequence. The card rejects zero, oversized or out-of-file requests,
stale sequences, changed offset/length, bad FNV, host status and a 500-tick
timeout. The tested bad-FNV, stale-reply and timeout refusals leave the cache
unchanged. A post-copy verification failure would currently leave uncertain
cache contents and requires a stronger restore/quarantine path before Doom
uses this as its production file callback. STOP during a pending read
returns a bounded refusal and drains the RTEMS workers and timer into
reboot-only quiescence. The host can request a full 4,096-byte cache readback
after each operation. This is a protocol and cache test, **not** a libc
`read()` adapter or actual Doom startup.

Earlier bridge sessions left Doom allocations in upper DRAM across a reset.
The first runner attempt, `live-0` on the remote PC, refused at read-only
host preflight page 33 before loading modules or issuing a card command. The
accepted version captures two stable 1,024-page host-readable surveys, then
the card saves each of 2,048 marker preimages and each complete page into
grant scratch during a reversible marker, alias, pattern/read/restore proof.
The full preimage hash must match after restoration; a failed restore
quarantines the retained callback. This makes the claim independent of prior
RAM contents. The guarded allocator still excludes the first and last
64 KiB of the upper bank; the stock callback and RAM grant remain pending
until card reset. Do not unload `admit_command` or free the grant while held.

Build against the pinned AcceleRAID RTEMS build and i960 toolchain:

```sh
rtems/accele160/doom_wad_service/build.sh RTEMS_BUILD TOOLCHAIN_BIN OUT_DIR
```

The exact physical run used
`/home/mit/i960-accele160-doomwad-20261017/project` on the Linux PC and
`run_bridge.py` with exact handler, candidate firmware, five command
modules, two same-boot full-flash reads, Doom template/relocations and the
pinned `freedoom1.wad`. See the script's required arguments. It refuses an
unexpected BDF, driver, image hash, WAD hash, handler/firmware hash, live
command module, block device, active descriptor or changed grant owner.
No firmware write is issued. All live acceptance records and exact build
files are in [the artifact](../../../artifacts/current/accele160-doom-wad-service-20261017/README.md).

Offline replay and capture-mutation tests:

```sh
python3 rtems/accele160/doom_wad_service/verify_live.py
python3 rtems/accele160/doom_wad_service/test_verify_live.py
```

Next: connect this WAD request service to the admitted Doom engine's
file/cache ABI, put a bounded engine call in an owned RTEMS task, and obtain
the first **real** Doom frame through the already tested outbound path.
Keep the 8 MiB manifest, full bank/flash audits, old-card isolation, STOP,
and reboot-only release. This image is intentionally a one-shot test and has
no independent watchdog if the host stalls after ownership.
