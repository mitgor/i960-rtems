# AcceleRAID 160 bounded Doom FPS gate, 2026-10-17

This is the first attempt to measure sustained, card-side Doom frame rate on
the 100 MHz AcceleRAID. The admitted engine and WAD are the exact first-frame
build; only the RTEMS test kernel changes. It records card timer ticks for 32
consecutive `stage=100` frames, then exits through the owned 210 boundary.
The planned FPS calculation excludes startup: 31 intervals divided by elapsed
card timer seconds. It does not measure browser delivery or DMA throughput.

`attempt-0` **did not reach a frame or produce FPS**. Two guarded 1 MiB stock
firmware reads passed before the run on boot
`c9773c0f-9b64-414b-8712-4d9e6bf1ae5e`. The RTEMS image passed its
preflight, full bank proof, exact upload, WAD rejection tests, and Doom entry.
The host served 1,301 engine WAD reads. All 1,301 offset/length pairs match
the prefix of the pinned 5,043-record native oracle. The last request was
offset 27,465,216, length 4,096; the card-reported read count was 1,302,
with 1,301 completed. After 120 seconds without a new WAD request or frame,
the host saved the page, published STOP and exited with the callback and grant
retained. The captured interrupt sample page was all `ff`, so it cannot locate
the stalled instruction. Do not interpret it as a stack or CPU trace.

`reboot -f` cleared the retained test session and Linux returned on boot
`fce8114f-3192-4bff-a284-8dee1879a189`. Both cards were unbound. The first
manual load of preserved `myrsread.ko` omitted its required `read_bdf=` module
parameter, so it did not probe the new card. This was a host setup error;
the earlier conclusion that a cold power cycle was required was premature.
After the next boot the exact driver loaded with
`read_bdf=0000:37:09.1`, bound only the AcceleRAID, and showed an idle stock
descriptor. No firmware write was issued, and the old card stayed unbound.

`attempt-1` passed two new same-boot guarded complete firmware reads on boot
`a56d1a84-e029-4a7f-9c8d-99db434403bf`, then served 4,809 WAD reads
matching the native oracle prefix exactly. The engine entered read 4,810 but
did not publish its request or a frame. The host saved the state and published
STOP after 120 seconds with no progress. The corrected BAR0 read of the
interrupt sample page still returned all `ff`; it is unusable, not evidence
of the interrupted PC. The card callback and grant remained retained until
`reboot -f`.

`attempt-2` started on the following boot after the exact driver bound and
two fresh complete firmware reads passed. It stopped after 79 exact native
WAD reads, with no next request or frame for 120 seconds. Its read-entered
and read-completed counters were both 79. The different stopping positions
show that one fixed WAD offset is not the sole trigger. STOP was published;
the callback and grant again remained retained until whole-PC reset.
**No 32-frame run has completed, so no new-card FPS has been measured.**

Linux returned on boot `e933df02-43f6-43b9-87a3-c88f93cdd9d4`. The exact
driver bound only the new card, the stock descriptor was idle, and two
independent guarded 1 MiB READIMAGE transfers had zero status, residual and
guard changes. Both matched unchanged stock firmware SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
Their compact metadata is in `post-reset-{0,1}/`; full data remains on the PC.

`attempt-0/build/` contains the exact 32-frame kernel/image and symbols.
Each `attempt-*/persist/` contains its WAD sequence, no-progress report and
available captured pages. The executable source and pinned hashes are in
[`rtems/accele160/doom_first_frame`](../../../rtems/accele160/doom_first_frame/README.md).
The pre-run full reads remain on the test PC in the `pre-`, `preb-` and `prec-`
directories; their full data is omitted here because each matched the unchanged stock firmware SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

After a successful 32-frame baseline, the exact quality-preserving renderer
options can be rebuilt for the new card and measured in matched runs. Flat
planes, half-height, and low-detail modes stay disabled for normal quality.
