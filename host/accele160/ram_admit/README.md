# AcceleRAID reusable RAM admission, operation 13

This is the first reusable AcceleRAID 160 code-entry operation. The retained
handler preserves operations 1–12, including the fixed RTEMS image and
sideband STOP gate. Operation 13 accepts a **trusted host's** contiguous
1–127-page image in the stock-owned 512 KiB grant at `c0710000`, with the
last 4 KiB page reserved for upload staging. It validates the grant record,
manifest nonce/address/size/page count/aligned entry offset/flags and a
whole-image FNV before invalidating I-cache and calling the entry. A returned
payload must write the `RUN1`, nonce, `ONE1` report; the handler adds the
base, page count and digest. Two distinct 48-byte returning probes are the
initial RAM-only acceptance payloads. Future trusted payloads can be changed
without another firmware write once this operation passes its live tests.

The manifest lives at `c000fa00..fa1f`: `RAM1`, command nonce, grant base,
grant size, page count, entry offset, whole-page FNV, flags=0. The report
is `c000fa20..fa3b`: `RUN1`, nonce, `ONE1`, base, count, FNV, payload result.
The host must pin the complete payload SHA-256; FNV is only an accidental
corruption check. This operation is for reviewed, returning programs. It
cannot interrupt a hung payload or enforce a wall-clock lease, and it does
not yet admit segmented ELF, separate BSS or an owned task stack. A future
resident supervisor must handle those and route sideband STOP to task
quiescence before arbitrary long-running RTEMS programs are admitted.

The [source handler](handler.S) is 4,324 bytes, linked at `c000e1d8`; it
ends at `c000f2bc`, below the first record at `c000f800`. The initial
4 KiB linker limit from operation 12 was an audited conservative slot, not
the end of the erased stock loader cave. [The candidate audit](audit.py)
checks exact stock/current/handler identities, the old handler preimage,
erased extension, unchanged runtime/boot block, cave-only edits and both
loader checksums. Candidate SHA-256 is
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

On 2026-10-17, two same-boot complete reads matched the preceding accepted
vector image `93faf91f…`; `STOREIMAGE` staged the candidate and a complete
read returned exactly `1c4995ad…`. The one-shot `FLASHIMAGE` command then
completed status/residual `0/0` in 36.84 seconds. After the PC restarted,
two persistent full reads matched the candidate on a new boot. The two
distinct RAM-only probes each completed normally, in 20.94 and 20.66 ms
host-observed time. Six bad digest, entry and nonce manifests returned stock
status 2 without changing the report or owner records. The page, staging
source, PCI aperture and all 512 allocator count/owner records restored.
The older operation-11 STOP still passed: 21.5 ms for the exact STOP and
10.26 s for its no-host deadline. The fixed operation-9 RTEMS image also
passed under this handler: 15-page upload in 1.14 s, card digest, task
result and owner/page restoration. Two further complete reads after the
RAM and compatibility tests still matched. [The archived captures and
replay](../../../artifacts/current/accele160-ram-admit-20261017/README.md)
include four rejected tamper variants.

[The live harness](run_admit.py) requires two same-boot full persistent reads
of that exact candidate, the new card bound to `myrsread`, the old PG unbound,
and an idle descriptor. It reserves the grant; verifies all 512 count/owner
records; uploads and independently hashes both probes; tries bad digest,
out-of-range entry and wrong nonce; then runs both variants with report,
page and owner audits. It restores the staging and loader pages before
release. Never force-unload its command companion after an uncertain result.
Use the accepted evidence and exact binaries as the baseline for the next
RAM-only experiment. A returning code probe is the proven contract; do not
infer a finite runtime lease or task-aware STOP from it.
