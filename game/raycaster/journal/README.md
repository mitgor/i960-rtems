# Bounded metadata journal

The browser queue supports `--queue-metadata journal` (opt-in) and `rewrite`
(the accepted default until journal card testing is complete). This changes only host evidence metadata; card binaries, paired full
512 KiB audits, slot checks, command validation and native frame comparison stay
unchanged. Native backend behavior is unaffected.

Each request appends and flushes its intent before execution, then appends a result
only after every audit passes. Records use canonical JSON, consecutive ordinals,
a SHA-256 chain and strict intent/result alternation. The bound is 8,193 requests
and 16 KiB per record. The completion seal is written only after successful card
CLOSE, closed audit streams and one-time compatibility exports. Any uncertain
request or metadata write error stops the session; it is never retried.

Replay requires a complete seal, matching exports, all original full snapshots,
command/profile checks, native oracle and verified restoration. Missing, partial,
reordered, duplicated or trailing records fail. A valid prefix is not a completed
session. The chain detects corruption; it is not authentication. Flush is not
`fsync`: this format does not promise durability across power loss.

`metadata-timing.jsonl` measures intent, command archive and result writes
separately. It is diagnostic, not a substitute for audit evidence.

Run `make -C game/raycaster test-journal`. `benchmark.py CAPTURE` runs rewrite /
journal / journal / rewrite against an existing capture without touching hardware.
`replay_test.py` converts a temporary copy of an accepted capture and exercises
full replay plus corruption rejection; that conversion is explicitly offline.
Live validation status and measurements are in
[the evidence directory](../../../artifacts/journal-20261011/README.md).
