# Callback and audit profiling

This experiment keeps `../ray.c` unchanged as the native and historical target
oracle. Build isolated candidates with `../build_target.py --request-words`
and add `--render-fast` for the renderer changes. Existing profiles/defaults
remain unchanged.

The request validator checks exactly the original fields and byte ranges, using
aligned alias-safe 32-bit equality for uniform padding, guards and the unused
output area. Byte prefixes and tails cover all alignments and input lengths;
there are no wider accesses across the end of a range. Header serialization and
all bounds checks remain explicit little endian.

The renderer uses the same serial FNV-1a recurrence, loading four bytes per word
in their original order. This hash is application output, not a replacement for
any host validation. Clipped sky/wall/floor runs avoid classifying each pixel
again. DDA traversal, divisions, collision, frame publication, copied output,
budgets and protocol are unchanged.

`build_transport.py --out DIR` reproduces the accepted quiet transport;
`--poll20` changes only ODB completion polling from 50 to 20 microseconds.
Linux polling sleeps may exceed those nominal values. The two-second deadline,
IDB polling, stale completion refusal, tags, DMA barriers, exact guard counts,
paired snapshots, immutable-byte validation and full audit every 32 requests
are unchanged. This experiment trades more completion observations for less
sleeping; it is not a raw PCI transfer optimization. `--coarse` omits detailed
command logging for a later release measurement.

Tests:

```
python3 game/raycaster/callback/test.py
python3 game/raycaster/callback/test_transport.py
python3 game/raycaster/upload/test.py
make -C game/raycaster test-transfer
make -C game/raycaster test
```

The differential test compares 20,000 requests (including rejected requests)
against the unchanged C renderer, under ASan/UBSan. The validator test checks
396,288 individual bit corruptions, all 4,097 input lengths at four alignments,
and exact uniform-range endpoints. The transport test requires the complete
generated sources to differ in only the ODB polling literal and experiment
metadata; existing fault tests cover the unchanged transaction logic.

See [the evidence ledger](../../../artifacts/callback-20261011/README.md) for
current card acceptance status; compiling a candidate does not establish a speedup.

`batch.py` is a fail-stop, seven-session baseline/validator/renderer/polling
matrix. It assumes a prepared isolated workspace, an available card and stopped
HTTP service; it never stops services, retries callbacks or forces an unload.
`compare.py` separates each contribution, records process CPU time as well as
wall time, and groups individual audit read waits by byte count. The ordinary
471,136-byte snapshot is still read twice; every 32nd request and CLOSE check
the full 524,288-byte allocation twice. All replies use the unchanged oracle.

Card acceptance: eight sessions, 3,368 replies, 104 periodic full audits and eight
restorations passed. Recommended combination: `--request-words --render-fast`
with the coarse 50 us module, 19.35 ms full-frame kernel median. `--poll20` remains
an optional tested tradeoff: about 0.27 ms less audit time but 17.2% more host CPU.
`release.py` runs the additional coarse 50 us acceptance session after the matrix.
`verify.py` replays all preserved results, including exact generated sources.
