# Exact slot validation and hashing

Card acceptance passed: ten sessions, 1,691 replies/full paired audits and ten
restorations. The selected `words` release reduces callback time 10.14% and kernel
time 4.00%; its tiny extra kernel gain over hash-only is within host variation.
Both candidates remain opt-in. HTTP is restored; exact results are in the ledger.

This is a target-only optimization of the accepted combined frame queue. The
original queue source and header remain the independent reference. The accepted
kernel module is reused byte-for-byte: paired targeted reads, full paired 512 KiB
audits on every request, deadlines and restoration policy are unchanged.

`--queue-slots byte` is the existing implementation. `hash` loads aligned alias-safe
words with byte prefixes/tails and performs the same four serial FNV-1a updates.
`words` additionally checks guard ranges with exact word equality and loads aligned
metadata words directly, falling back to explicit byte assembly when unaligned.
Endian conversion preserves the wire byte order. These are ordinary RAM helpers;
they do not read MMIO or beyond the requested ranges. Hashes never replace exact
comparisons. All epochs, generations, lengths, markers and guards are retained.

## Diagnostic profile

`--queue-diagnostic` adds opcode 5 only in explicitly selected diagnostic targets.
Its words are magic, op, epoch, occupied slot, repetition count, selector, zero,
zero, followed by 32 zero bytes. Count is 0–32. Selector 1 hashes the 4,864-byte
reply and compares its stored hash; selector 2 performs complete slot validation.
Every repetition checks its result. A compiler memory barrier prevents invariant
hoisting. Queue and renderer bytes remain unchanged. Invalid counts/selectors,
malformed requests and unoccupied/stale slots are rejected. The ordinary queue
validation still precedes the probe. No timer or interrupt is claimed.

Repeated callback measurements at 0, 1, 4, 8, 16 and 32 repetitions estimate slopes.
They include loop/check overhead and warmed data; subtracting hash from full
validation is an estimate, not a CPU-cycle accounting. Diagnostic targets are not
used for release performance comparisons, and release targets reject opcode 5.

## Tests and reproduction

```
make -C game/raycaster test-slotopt
python3 game/raycaster/build_target.py --work FRESH --sources ARCHIVES \
  --request-words --render-fast --frame-queue --queue-combined --queue-slots words
```

Each candidate passes the inherited combined/queue tests, 20,484 length/alignment
hash comparisons, 163,840 single-bit slot corruptions, metadata-offset checks,
protected-page tail reads, and diagnostic request mutations. Tests compare the
original renderer/model and complete queue/renderer bytes, not just status codes.
The stress suite alternates replacements with both slots occupied, stale/duplicate
requests, backpressure, eight epoch resets and CLOSE with both slots unacknowledged.

`run.py` selects request suites around the unchanged accepted live/replay sources.
Exact source assertions replace only model/case selection and reserve enough
random-epoch headroom for eight resets. Every transaction, full read, command
validation, snapshot, timing and CLOSE line remains intact. Live suite metadata
is saved independently; replay reads it and reconstructs every operation.

`batch.py` has baseline, candidates, release and selected-candidate stress phases.
It has no service stop, force-unload, reboot or automatic retry. Respect the shared
hardware lock and complete parallel card work before starting. Keep full audits
for all suites and restore production afterward.

See [the fifteen-step ledger](BATCH.md) and
[the evidence and performance report](../../../artifacts/slotopt-20261011/README.md).
