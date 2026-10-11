# Combined ACK-and-PUBLISH

This opt-in bounded queue profile adds operation **4** to the existing 64-byte
request. It acknowledges and replaces **the same slot** in one callback. The
previous separate-operation target and transport defaults remain available.

Words 0..7 are magic, op=4, epoch, slot, new generation, acknowledged generation,
zero, zero. The remaining 32 bytes are the exact bounded RAY1 render request.
The epoch must match, the named slot must be occupied with the acknowledged
generation, and the new generation must equal last+1 without wrapping. Both
occupied slots are integrity-checked, and the complete render request is validated,
before any ownership, slot or renderer state changes. This works when both slots
are full, while preserving the other slot byte-for-byte. No cross-slot ACK is
implied. Duplicate combined requests are stale; they never render twice.

Publication reuses the original validated bounded renderer, fixed-length slot,
metadata/hash/guards and READY-last sequence. There is no separate ACK commit
before rendering. Input rejection preserves the previous publication and renderer
state. This is not rollback across a hardware failure or an unexpected renderer
failure after publication starts: such a transaction is uncertain and must not be
retried. Existing fail-stop retention/restoration rules apply. The host reads
only after callback return/cache maintenance; there is no asynchronous producer.

The host acknowledges a frame only after exact native comparison, paired targeted
reads, and the **complete paired 512 KiB audit**. The next request combines that
ACK with a new frame. Full audits still run on **every request**, including
application errors. Combining two operations reduces the number of callbacks and
audits per rendered frame, never the coverage or cadence per transaction. The
kernel module and all its validation are byte-identical to the accepted queue v2
module. No flash, RAM ownership, quiet-upload ordering or DMA policy is changed.

## Tests and comparison

```
make -C game/raycaster test-combined
python3 game/raycaster/build_target.py --work FRESH --sources ARCHIVES \
  --request-words --render-fast --frame-queue --queue-combined
```

`optimize.py` asserts each transformation matches the accepted queue source exactly
once. The old source remains unchanged for independent replay. Native tests compare
293 separate/combined requests against an independent ownership model and the
unchanged renderer, with identical 80-frame trajectories. All 512 request-bit
mutations agree; the 508 rejected mutations preserve queue, slot and renderer
bytes. Sanitizer tests cover invalid lengths/capacity, generation exhaustion and
5,120 corrupt publication bytes blocking replacement without mutation. Existing
queue/transport/generation/lifecycle tests remain mandatory.

`batch.py` runs separate / combined / combined / separate in an isolated workspace
with the existing exclusive hardware lock. The baseline is the accepted original
queue target and both variants use the exact same full-audit kernel module.
Measured baseline frames are ACK(previous)+PUBLISH(next); combined frames perform
both in one request. Each variant starts from identical reset and seed frames and
uses the same keys. Both finish with an unacknowledged frame so CLOSE must restore
without relying on a final application ACK. Extra combined error cases are outside
the steady timing set. `profile.py` uses paired sums before taking medians.

Card acceptance passed: 586 replies and paired full audits across four sessions,
with four clean restorations. Median kernel cost fell from 39.958 to 25.078 ms per
frame (37.24%); full audit cost per request remains about 11.6 ms. Public HTTP is
restored. The earlier single-frame renderer remains the default.

After exclusive ownership and an orderly production close, one prepared test is:

```
sudo python3 game/raycaster/queue/live.py --payload TARGET/session/kernel.bin \
  --module MODULE/dac960rtems.ko --output FRESH-CAPTURE --queue --pipeline combined
python3 game/raycaster/queue/verify.py FRESH-CAPTURE \
  --payload TARGET/session/kernel.bin --module MODULE/dac960rtems.ko
```

Use the queue v2 module with full audits; `--pipeline separate` is the measured
comparison against the original queue target. Restore production after testing.

Hardware results and exact binaries are recorded in
[the evidence ledger](../../../artifacts/ackpublish-20261011/README.md).
