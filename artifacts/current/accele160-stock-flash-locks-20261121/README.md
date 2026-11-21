# All-block Intel flash lock probe, prepared offline

The first live Intel-ID probe on 2026-11-21 read the master lock and only
blocks 4 through 11. Intel's
[28F008S3 datasheet](https://datasheet4u.com/pdf/1183856/28F008S3.pdf)
defines each block lock code at identifier-mode address `block_base + 2`.
This revised payload checks all sixteen 64 KiB blocks. Bit `n` of report
word 17 corresponds to block `n`, including the stock boot block and the
currently blank block 13.

`flash-id.bin` is 356 bytes, linked at `0xc000f900`, SHA-256
`f2d1352e01e7d69f9277623bb8d89047970df27312330121cb4b9b89f4809623`.
Its flash command writes are `FF`, `90`, `FF`; it has no erase, program, or
lock-configuration command. The stock-RAM launcher pins this hash, the tested
`ping_probe.ko` hash, the exact stock flash SHA-256, and the previous live boot
ID `9f2952ee-924f-4d27-af7e-83598ae24ba5` so it refuses another call on
that boot. It requires two new same-boot full stock reads and a manually
confirmed cold power cycle before touching the volatile dispatch word.

Offline validation: the payload's C logic passed the S3 model tests with
locks set on blocks 0, 6 and 15; the i960 build passed its entry, fallback,
and size checks. The live card has **not** run this revised payload. After a
successful call, the launcher restores the dispatch word and loader page; a
full READIMAGE should then confirm flash remains stock. If the command is
pending, the RAM hook must remain in place until a cold reset.
