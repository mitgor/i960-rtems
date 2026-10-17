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
`fce8114f-3192-4bff-a284-8dee1879a189`. Both cards were unbound. Loading
the exact preserved `myrsread.ko` after `raid_class` did not bind the new card;
an explicit bind was rejected. A full removal of power is needed before
another card run. No firmware write was issued, and the old card remained
unbound and untouched. The next run must start with fresh driver inventory and
two same-boot guarded full-flash reads.

`attempt-0/build/` contains the exact 32-frame kernel/image and symbols.
`attempt-0/persist/` contains the last page, WAD sequence, no-progress report
and unusable interrupt sample. The executable source and pinned hashes are in
[`rtems/accele160/doom_first_frame`](../../../rtems/accele160/doom_first_frame/README.md).
The two pre-run full reads remain on the test PC in
`/home/mit/i960-accele160-fps-20261017-pre-{0,1}`; their full data is omitted
here because both matched the unchanged stock firmware SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

After a successful 32-frame baseline, the exact quality-preserving renderer
options can be rebuilt for the new card and measured in matched runs. Flat
planes, half-height, and low-detail modes stay disabled for normal quality.
