# AcceleRAID 160 Doom bridge, 2026-10-17

This is a **physical card test of memory allocation, exact Doom image admission,
and bidirectional PCI sideband transport**. It is not Doom execution or a
gameplay frame. Card `0000:37:09.1` was the only target; the old DAC960PG
`0000:37:04.1` remained unbound. No firmware write was issued. The accepted
stock firmware SHA-256 was
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

The previous reboot-only test left its deterministic DRAM pattern visible on
the next Linux boot. The original zero-only host preflight rejected it before
issuing any command. A read-only BAR0 survey found 1,022 of 1,024 odd pages
still matched that exact pattern; page 1 was zero and page 3 held other stock
data. The revised card preflight saved the first 16 pages and the two known
diagnostic pages in the owned grant. It required every other page, including
every even page the host cannot access, to match the exact prior pattern.
It then repeated simultaneous 2,048-page markers, lower-bank alias guard,
full fill/read/restore, preimage hash and idle-DMA checks before claiming the
bank. The full-bank report has error zero, 2,048 pages checked, zero marker
or page errors, matching lower/code hashes and restored-bank hash `853984e9`.
The cold-boot footprint is *not* presumed zero or generally available.

RTEMS claimed all 8 MiB while stock operation 13 stayed pending, but the
guarded allocator deliberately uses `c0810000..c0feffff`, excluding the
stock-touched first and last 64 KiB. It pinned three handles:

| Handle | Address | Size | Purpose |
| --- | --- | ---: | --- |
| `0x101` | `c0810010` | 900,000 bytes | Doom image/admission storage |
| `0x102` | `c08ebbd0` | 6,291,456 bytes | Doom zone candidate |
| `0x103` | `c0eebbf0` | 65,536 bytes | Frame candidate |

All guard checks passed after each bridge command. The 27-page RTEMS image
SHA-256 is `6b625a81c60a084c1cf3d0ba61d1dcbaa7dac23832333a3fa0eaeb8a03f80863`.
The host made 232 sequenced card requests. Admission before upload was
rejected, followed by 212 checked 4 KiB-or-smaller chunks totaling 867,792
bytes. The card verified the 431,864-byte Doom template, 53,472-byte ordered
relocation table, 369,376-byte text hash, zero BSS, and all 13,368
relocation sites; it relocated the image to `c0810010` and reported entry
`c0866dd0`. This is **image admission only**: the entry was not invoked.

The input path rejected a deliberately changed WAD header, then accepted the
exact 512-byte `IWAD` header from Freedoom 1 (first-512 SHA-256
`93bd1ddcfc43fbf233207876f5cfcbaef4cf4e64a1093efa47be9517d93214bd`).
The full WAD was not transferred. The card generated a deterministic 320×200
indexed diagnostic frame and served 16 separately checked 4 KiB pages through
the outbound sideband. The independent host calculation matched all 65,536
bytes; frame SHA-256 is
`e03906cd8ca54a10c475bc22af6e5a2a913db433900be52dcd641c05768bba7c`.
The captured [PNG image](live-1/persist/frame.png) and original
[PGM bytes](live-1/persist/frame.pgm) can be viewed directly.
The saved `wad-header.bin` was reconstructed from that frame, matched the
pinned SHA-256, and then compared byte for byte with the original WAD header
on the remote PC. The full source WAD remains in the remote test workspace.
This is a transport diagnostic, not a Doom-rendered picture.

STOP drained the workers and timer at tick 7,380, published `QUIE`, and left
the callback and grant retained. The old card remained unbound. The Linux
host-side runner had two recoverable mistakes after the card was live: an
assertion pinned the old zero-bank restore hash, and a later log write used an
uninitialized local variable. `resume_bridge.py` and `finish_bridge.py`
continued the *same* retained session without reuploading or touching the
old card. The resulting card evidence passed. The test PC did not immediately
return after `reboot -f`; a fresh boot subsequently released the retained
session. On boot `994bfdd8-8664-4516-86a8-36d6555d6a78`, the command
modules were gone, PIATVR was `c0000000`, `myrsread` bound to the new card,
its stock descriptor was idle, and the old card remained unbound. Two
complete guarded post-reset READIMAGE transfers had zero status, residual
and guard changes and SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
Never unload the pending operation-13 module or free its grant while the
card is retained.

`inputs/` holds exact Doom template, relocation table, identity header and
512-byte WAD header; `build/` holds the exact card image, kernel and symbols;
`live-1/` holds the full preflight, upload receipts, frame and STOP captures.
The two guarded full-flash reads used for same-boot preflight remain on the
remote PC in `i960-accele160-persistent-20261017/post-reset-{0,1}`; their
metadata and exact firmware identity are pinned by `run_bridge.py`. The
two new post-reset full reads remain in
`i960-accele160-doombridge-20261017/post-reset-{0,1}`; compact metadata is
saved here without duplicating both 1 MiB `data.bin` files in git. The
failed zero-only host preflight is `live-0/` remotely and changed no card RAM.

Replay and three frame/receipt/STOP tamper rejections pass offline:

```sh
python3 rtems/accele160/doom_bridge/verify_live.py
python3 rtems/accele160/doom_bridge/test_verify_live.py
```

Fresh-boot flash/driver acceptance passed. The next work is a new-card Doom
runtime ABI and a full-WAD service. The bridge deliberately does not call
the admitted Doom entry. It also has no independent watchdog if the host
stalls after claiming the bank, so keep it a one-shot, reboot-only test.
