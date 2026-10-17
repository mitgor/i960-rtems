# Bounded exclusive callback on the AcceleRAID 160

On boot `ed14ddb9-6cf2-4dbc-8645-1383eda72c2d`, the exact 16-page RAM
image SHA-256 `9eab93599a513fbd38776567134c1d80838bb893df147053284be2dfd7b8950b`
entered operation 13 twice. The current full firmware SHA-256 was
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
The new card was bound to exact `myrsread`, the old DAC960PG was unbound,
and stock reported an idle descriptor with no block devices.

Both callback entries ran at interrupt priority 31 on the owned stack while
stock command execution was suspended. The card checked CCR, NDAR and BCR
idle on **all three** DMA channels. It found `c0f01000` entirely zero, wrote
four distinct words at offset `0x80`, read all four back, restored them, and
rehashed the complete 4 KiB page. The report in each `page-after.bin` is
`XCL1, c0f01000, 0, 76efddc5, 4, 76efddc5, 0, 0`: idle DMA before/after,
matching page FNV before/after, four correct readbacks, status zero. Host BAR
snapshots `upper-before.bin` and both `upper-after.bin` are identical full
zero pages (SHA-256 `ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7`).

The STOP path ignored a stale token, accepted exact STOP and returned in
54.332 ms. The no-host path returned after exactly 2,000,000 polls in
1,508.141 ms. Firmware SP restored to `c0002100`; RTEMS worker and owned
entry stacks, loader page, staging and all 512 allocator count/owner words
passed the host audits before release. Two full guarded flash reads before
([prior arena capture](../accele160-doom-arena-20261017/README.md)) and two
after matched the same firmware hash. PIATVR returned to `c0000000`, stock
descriptor to idle, and no test module remained. No firmware flash write
occurred.

The exact build output is in `build/`; source and build script are in
[`rtems/accele160/exclusive_probe`](../../../rtems/accele160/exclusive_probe/README.md).
Replay with `python3 host/accele160/exclusive_probe/verify_live.py` from the
repository root. Altering a probe report or an upper-page byte rejects replay.

This is temporary, synchronous exclusivity of the CPU path and one restored
page. Stock firmware resumes afterward. It does **not** grant the upper 8 MiB
for a long-running RTEMS/Doom session, demonstrate alias freedom throughout
the bank, or cancel a never-draining DMA transaction.
