# AcceleRAID 160 full-WAD service, 2026-10-17

The new card at `0000:37:09.1` accepted a retained, RAM-only RTEMS image
that admits the exact Doom engine and serves bounded, card-requested reads
from the host's pinned Freedoom 1 WAD. **The engine entry was not invoked;
these are not gameplay frames.** The old DAC960PG `0000:37:04.1` remained
unbound. No firmware write occurred.

The first attempt (`live-0` on the remote PC) rejected the upper bank at a
read-only host preflight, before loading a command module, because previous
Doom allocations persisted across reset. The revised image captured and
restored actual preimages of all 2,048 upper-bank pages. Its simultaneous
marker, lower-bank alias, whole-page pattern/read/restore, code hash, DMA-idle
and preimage-hash checks passed. The bank report has error 0, all 2,048
pages tested, zero marker/page failures, matching lower and code hashes, and
restored preimage hash `11be3882`. Two read-only host surveys of the 1,024
host-visible odd pages agreed byte for byte (4 MiB per survey, SHA-256
`0ec3550226c137f2f656bed8c6afc5bf6376c47134a0c81480fb15f0830f5248`).

The card pinned a 900,000-byte image allocation at `c0810010`, a 6 MiB
zone candidate at `c08ebbd0`, a 64 KiB frame at `c0eebbf0`, and a guarded
4 KiB WAD cache. It admitted and relocated the same 867,792-byte Doom image
after 212 sequenced upload commands. The WAD header rejection/admission and
independently calculated diagnostic frame from the previous bridge passed
again. That frame is in `evidence/persist/frame.pgm`; its SHA-256 is
`e03906cd8ca54a10c475bc22af6e5a2a913db433900be52dcd641c05768bba7c`.

The new protocol made 42 card-owned WAD requests spanning the 28,795,076-byte
file. Thirty-eight valid reads passed, including directory, end-of-file,
unaligned and deterministic scattered offsets. After every non-STOP request,
the host read the complete 4 KiB cache back from card RAM and compared it
byte for byte to its model. Deliberately bad FNV, stale reply sequence and
five-second no-host timeout each refused without changing the cache; a later
valid read recovered. A fourth refusal was STOP during a pending read.
Zero-byte EOF was rejected before a card request was published. The card's
final counters were 38 accepted and 4 refused. Its timer heartbeat advanced
from 6 to 1,743 before quiescent STOP. Full arena guards, owner record and
old-card checks passed; the firmware callback and grant remained pinned for
reboot-only release.

`build/` contains the exact 27-page image (`2748538e4140de26b560a2d2aa2ecaeee4f2b34d90eb744e10f86d266a5f9125`),
kernel (`96142197a385e6b5f3a035050bface009c32a99bc8c164496f3726f4bd6b9aea`),
ELF/map/symbols. `evidence/` contains the exact compact preflight, owner,
control-page, WAD-request, frame and STOP captures. Exact source and replay
are in [doom_wad_service](../../../rtems/accele160/doom_wad_service/README.md).
The pinned WAD itself is left in the remote test workspace rather than
duplicated in git; its full SHA-256 is
`7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d`.
The exact Doom template, relocation table and WAD header are shared from
[the preceding bridge](../accele160-doom-bridge-20261017/README.md).

Offline replay passed, including rejection of three capture mutations:

```sh
python3 rtems/accele160/doom_wad_service/verify_live.py
python3 rtems/accele160/doom_wad_service/test_verify_live.py
```

Post-reset acceptance **passed** on boot
`a3e08f10-8177-4529-ba88-b62b6c2ccb9f`. The retained module was gone,
`myrsread` bound the new card, its stock descriptor was idle, PIATVR was
`c0000000`, and the old card remained unbound. Two independent, guarded
complete 1 MiB READIMAGE transfers had zero command status, residual and
guard changes. Both matched unchanged firmware SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
Their compact request/result/status records are in `post-reset-{0,1}/`; the
two identical full flash binaries remain on the remote PC and are omitted
from git. The complete same-boot pre-run reads were also verified by
`run_bridge.py`.
