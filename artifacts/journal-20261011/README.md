# Metadata journal — host validation, card acceptance pending

Implemented 2026-10-11. Base commit `db5d4b2`. No card commands, flash writes,
reboots or production service changes were made by this batch. The parallel RTEMS
shared-heap task retained the hardware; do not interrupt it to run these tests.
`--queue-metadata rewrite` remains the default. Journal is opt-in.

## Measured results

Same 325-request metadata from the accepted gzip-1 browser capture, processed in
rewrite / journal / journal / rewrite order. Both paths produce exactly matching
requests and phases. These are metadata-only benchmarks, **not new live card runs
or measured browser FPS improvements**. Linux ran on 192.168.2.75 while parallel
work was active, so the precise timings include host scheduling variation.

| Host | Rewrite mean, two runs | Journal mean, two runs |
| --- | --- | --- |
| Linux | 5.020 / 5.153 ms | 0.129 / 0.095 ms |
| Mac | 0.820 / 0.748 ms | 0.0166 / 0.0169 ms |

Linux rewrite's last 50 requests cost 8.86 / 8.15 ms; journal cost 0.099 / 0.094 ms.
Journal final export/seal cost 9.72 / 9.55 ms once at CLOSE. The reduction is about
97.8% in average metadata cost; it does not remove card execution or full audits.
Raw per-request measurements are in `metadata-bench-{linux,mac}.json`.

Native regression results are in `native-tests.txt` and `native-tests-linux.txt`.
Six journal tests cover every byte-prefix truncation of a small valid journal,
chain/order errors, correctly rehashed invalid ordering, compatibility export
mismatch, rewrite/journal differential sessions, write failures before and after
execution, failed CLOSE, and pre-execution request bounds.

`offline-replay-tamper.json` records full replay of a **temporary converted copy**
of the prior accepted 325-request card capture. Original full snapshots, command
logs, native comparisons, payload hash and restoration checks remain in effect.
All 12 mutations reject, including missing/truncated/unsealed/broken-chain journal
and all eight previous audit corruption cases. This is replay evidence, not a
new physical capture. Original binaries and captures remain in
`artifacts/browserqueue-20261011/browser-fast-{builds,live}.tar.gz`.

## Continue physical acceptance

Isolated prepared workspace: `/home/mit/i960-journal-20261011-g5s8JT`.
Accepted unchanged images are `accepted/kernel.bin` and `accepted/dac960rtems.ko`.
Sources plus reference firmware inputs are installed; Linux native tests pass.

After the parallel task releases the card and its service restoration is verified:

1. Record current service/boot/card owner; stop production gracefully and verify
   CLOSE using the existing transport verifier. Preserve the existing lock.
2. Run the browser queue with `--queue-metadata rewrite`, then `journal`, then
   `journal`, then `rewrite`; reuse `browserqueue/browser_test.cjs`, identical
   binaries and full audits. Use separate output directories. Compare pacing
   classes separately and inspect `metadata-timing.jsonl`, including commands cost.
3. Run `browserqueue/lifecycle_test.py --backend card-queue --queue-metadata
   journal` for idle, limit, signal and disconnect, with accepted payload/module.
4. Replay each capture using `browserqueue/verify.py` and `upload/verify_quiet.py`;
   run `browserqueue/tamper_test.py` on a journal capture. Archive exact sources,
   binaries, captures and browser reports. Restore and check public IPv6 HTTP.
5. Only after acceptance consider changing the default. Report actual delivery
   measurements separately from the metadata microbenchmark.

The record chain detects corruption, not malicious rewriting. Flush is not fsync;
no power-loss durability claim is made. An interrupted or unsealed session is
never accepted, even if earlier audits passed. See the [format contract](../../game/raycaster/journal/README.md).
