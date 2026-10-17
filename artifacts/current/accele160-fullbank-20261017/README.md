# AcceleRAID 160 upper-bank and reboot-only acceptance, 2026-10-17

Card `0000:37:09.1`, boot `ed14ddb9-6cf2-4dbc-8645-1383eda72c2d`;
old DAC960PG `0000:37:04.1` unbound. The stock operation-13 firmware SHA-256
was `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
All tests used a separately owned 512 KiB upload grant, exact per-page copy
receipts, a whole-image card digest, and two guarded same-boot full-flash
preflight reads. No firmware write was issued in this batch.

| Stage | Exact image SHA-256 | Card result |
| --- | --- | --- |
| Zero-only `arena` | `25bdc7df178a14dc39ec2a277e972fea7eb53df4ee5e2d897e4d5982da3279d9` | Rejected before upper write; completed command/grant recovered |
| Read-only `census` | `b329045e3a1d54516ee0a75c3cf978b45353a3458cc8848da5163be16dae5558` | Two nonzero pages, 53 words; STOP/timeout passed |
| Saved `pages` | `7facfbc4fd92fa4e03a454f00a90fd612a628900ad92f469995021b4bcec90ac` | Exact 4 KiB copies of both populated pages; sources untouched |
| Reversible `fullbank` | `ba5c265aa24d524362be0c23b42ceb74df2daead340ef11af3ebb9dfba85a1e1` | All 2,048 pages distinct; complete 8 MiB pattern/read/restore on STOP and timeout |
| Reboot-only `persistent` | `752215d534c8c4d5998f5cdb8edb1d03929905dc480cc54bd110e47fa6f21304` | Held all 8 MiB patterned with stock callback pending; 1,024 odd pages checked; timer heartbeat and quiescent STOP passed |

The zero-only rejection was a useful negative gate. A card-side complete
word census found only `c0ffa000` and `c0ffe000` populated. Their combined 53
nonzero words were identical on STOP and timeout. The first page SHA-256 is
`01f91f4c8c3cbc6f5b34104d1877cc51ca1e69048c223ed724daceacfb89f096`;
the second is `50ec5e43497cf521b443ee749dccdc529e228e88edbf9b4b5082a31aa5541420`.
The separate host odd-page survey found all 1,024 accessible odd pages zero.

The reversible full-bank test saved the two populated pages in owned grant
scratch, checked their exact FNV values, then marked all 2,048 pages at once.
Every marker read back distinctly. Its lower-bank guard hash was stable
before, during and after those writes. Each page then passed a 1,024-word
write/read/restore cycle. The card's final upper-bank word hash was
`fefecffb`, identical on both runs. STOP took 9,292.873 ms; the no-host
120-tick expiry took 10,364.055 ms, including the roughly nine-second bank
proof. Full owner, loader, stage, scratch, stock page, interrupt context and
timer restoration passed. Two complete guarded post-test reads matched the
firmware SHA above, with zero residual and zero guard changes.

The persistent run first repeated the full-bank gate, then overwrote the
upper 8 MiB with deterministic per-page patterns and **did not return through
firmware**. The card reported full-bank word hash `833aedc5`; the host
compared all 1,024 BAR-readable odd pages byte for byte and recorded their
combined SHA-256 as `25ed66dcdbcb353e62d74bb90b880a0b4563b1332977451f0246c6802cabe300`.
The independent timer heartbeat advanced from tick 6 to 262 while the
operation-13 module still reported `started=1 done=0 released=0`. Exact STOP
drained the two workers and timer and entered `QUIE` with the same pending
command. A separate host process subsequently read the unchanged `QUIE` and
STOP-ACK records. This is intentionally a **reboot-only** state; do not
release its grant or unload its pending module.

The PC did not return after `reboot -f`; a physical power cycle brought it back. On new boot `a11703ca-57d6-4fc9-bc69-ed0581332d78`, the retained module was gone, PIATVR was `c0000000`, the stock descriptor idle, and the old card still unbound. Two complete guarded post-reset flash reads in `persistent/post-reset-{0,1}` matched the exact firmware, with status/residual/guard changes zero. This validates the power-cycle release boundary; it does not show that software-only reboot can clear a retained card session.

The local `build/` copies are exact binaries and symbols; `live-0/` contains
card pages, statuses, owner tables and reports. Flash metadata is retained
without duplicating each 1 MiB `data.bin` in git; the full guarded reads remain
in `/home/mit/i960-accele160-{arena,census,pages,fullbank,persistent}-20261017/`
on the test PC. Exact source and safety boundaries are in
[`rtems/accele160/ARENA.md`](../../../rtems/accele160/ARENA.md).
All five source trees were rebuilt with the pinned remote i960 toolchain after
the tests; each `kernel.bin` and `image.bin` SHA-256 matched its captured build.

Offline replay validates the exact images, each stage's paired full-flash
metadata, bank census and page copies, reversible restore reports, retained
STOP/heartbeat report and the changed boot ID with matching post-reset flash.
Four altered image/flash/bank/STOP captures are rejected:

```sh
python3 rtems/accele160/arena_full/verify_live.py
python3 rtems/accele160/arena_full/test_verify_live.py
```
