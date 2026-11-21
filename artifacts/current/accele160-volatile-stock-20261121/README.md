# Ram injection v1: stock-card RTEMS and Doom, 2026-11-21

The [firmware experiment names](../../../docs/hardware/ACCELE160-FIRMWARE-NAMES.md)
distinguish this flashless route from the persistent and native images.

Card `0000:37:09.1` (serial `10112504772`) booted Linux with its original
stock flash SHA-256
`0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`.
Two full guarded READIMAGE captures on boot
`941d7063-c96b-41a7-950e-7c01f0fb49bd` matched that SHA before this test.
No STOREIMAGE, FLASHIMAGE, erase, or program command was issued here.

The first installer prototype stopped before sending a command because it
mistakenly treated the host PCI window as exposing both even and odd 4 KiB
pages. The host restored the stock dispatch pointer, blank loader RAM page,
and PIATVR mapping; a subsequent read-only probe confirmed the same table
and blank-page hashes as before. No code from that prototype ran.

The corrected installer staged the previously accepted 4324-byte handler
(`8d8c79c3...48ad34`) and a 296-byte i960 copy stub
(`b5358912...21eedd`) only in host-visible RAM. The first stock `0x8f`
callback copied the hidden even-page portion and compared every word. The
second callback verified the complete handler's additive checksum, flushed
the instruction cache, and set the dispatch pointer from the i960 side.
Both returned stock unsupported status `2/0`, as expected. The handler then
answered a normal operation-1 ping with status/residual `0/0`. The loader
page bytes matched the exact staged layout, and PIATVR returned to default.
The handler remains volatile until a cold reset.

The exact prior 15-page, 61,440-byte RTEMS image was uploaded under the
handler. The card verified whole-image FNV `0x648486da`; the task returned
the expected result in 0.051 seconds. All 15 page copies, negative request
checks, allocator owner table, staging page, and loader page audits passed.

The separate volatile-stock Doom runner used the existing pinned persistent
RTEMS/Doom bundle and a 40-frame limit. It captured 40 DMA frames, paired the
first four with independent PIO, completed 5,083 successful and four expected
rejected WAD requests, and passed the per-game idle, frame, DMA, ownership,
and global STOP checks. The service exited successfully. Its final state is
the expected reboot-only quiescent RTEMS owner, with the grant retained.
The PCI card remained enumerated and the Linux host remained reachable.

The full local captures are `install-live/`, `rtems-live/`, and `doom-live/`.
Only the small result/status records need to be tracked in Git; the complete
frame and memory captures can remain local. A cold power cycle and two new
full READIMAGE captures are still needed to establish the post-run flash
identity. Until then, do not issue another card command or unload the retained
DMA/admission modules.
