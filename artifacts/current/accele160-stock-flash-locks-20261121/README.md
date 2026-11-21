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
and size checks.

On the next cold boot `e56a1655-ee74-45d3-b844-07d66b52640b`, the sole
Slot 5 card passed first bind and two fresh full selector-9 stock reads.
The revised RAM probe completed once and reported Intel `89/A6`, master lock
`0`, and **all sixteen block lock bits clear** (`all_block_locks=0`). The
launcher restored the volatile dispatch word and loader page, then a third
full READIMAGE again matched stock SHA-256
`0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`.
No FLASHIMAGE, erase, program, or lock-configuration command was issued.
The full `live/` captures are local and not included in Git.

The next test cannot reuse this boot for another `0x8f` call: i960 cache
visibility after restoring a RAM hook is unproven. If a command remains
pending in a future run, leave the hook intact until a cold reset.
