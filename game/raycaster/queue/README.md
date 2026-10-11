# Bounded frame queue prototype

This is an opt-in cooperative RTEMS raycaster profile. It is **not** autonomous
rendering or an accepted replacement for immutable-memory auditing. Every request
retains two complete 512 KiB reads and all existing transport validation.
Read [the evidence ledger](../../../artifacts/framequeue-20261011/README.md) for
card acceptance and measurements.

## Memory and ownership

Two 5,120-byte slots occupy staging offsets `0x60000..0x627ff`, inside the existing
mutable grant. The target link must end at or before `0xc0f8c000`; the queue ends
at `0xc0f8e800`, before the upper workspace guard. No additional physical RAM is
claimed. The fixed queue is initialized explicitly by INIT, not by a presumed
zeroed firmware buffer. Opening saves the original allocation and closing restores
and verifies it completely, including queued frames that were never acknowledged.

Each slot contains 64 metadata bytes, the unchanged 4,864-byte RAY1 reply, and
192 tail guard bytes. Metadata is eight LE32 words: magic, epoch, generation,
length, READY marker, FNV-1a over the reply, complemented generation, and slot
index; bytes 32..63 are `a5`, and the tail is `5a`. Publication writes READY last.
FNV is only an additional corruption check: it never replaces exact paired reads,
full allocation audits, byte comparisons or native renderer comparison.

The target validates existing ready slots before handling another operation.
The host reads after the callback has returned through the existing runner/cache
maintenance. There is no concurrent producer during a read; the compiler ordering
barrier and READY marker alone are **not** an asynchronous cache/DMA protocol.
The host acknowledges only after paired targeted bytes equal both the native
frame and the complete audited snapshot. Slots stay immutable until that ACK.

The 64-byte request is eight LE32 words (magic, operation, epoch, slot, generation,
three reserved zeros) followed by a 32-byte RAY1 render request or zeros.
Operations: INIT=0, PUBLISH=1, ACK=2, QUERY=3. PUBLISH accepts exactly one bounded
80-column frame. INIT requires no occupied slot and a strictly newer nonzero
epoch; the host test starts each session with a random epoch. Generations advance
exactly once per successful publication, never wrap, and ACK must name the exact
occupied slot/generation/epoch. Invalid operations change neither queue nor
renderer state. Queue-full does not overwrite a frame. Query and application
errors return a bounded 64-byte descriptor, with the RIO transport still intact.

The response is 16 LE32 words: magic, version=1, application status, epoch,
ready mask, last generation, two slot generations, two lengths, echoed RIO
sequence, five reserved zeros. Status: 0 success, 1 malformed, 2 stale,
3 full/busy, 4 corrupted existing publication. A duplicate ACK is rejected.
There is no retry of an uncertain callback or DMA operation.

## Transport and audit contract

After callback return/self-disarm/result validation, the queue module reads the
64-byte descriptor twice, then each READY slot twice. It validates identities,
lengths, completion markers, guards and hashes. It then performs the **original
paired full allocation audit on every STEP**, including queue errors. Exact byte
comparison binds targeted reads back to that full snapshot. An uncertain read
completion prevents further DMA and retains the existing failure policy.
A known-complete targeted failure still performs the full audit before rejecting
the transaction. All fixed-address reads use the existing runtime read gate.

The baseline module also forces paired full allocation audits every STEP, so the
comparison does not reward the queue by weakening audit cadence. `RAYPROFILE`
retains the total transaction timing; `FQPROFILE` separately measures targeted
read/validation and full audit costs. Each full snapshot is archived, rather than
only every 32nd one. Baseline frames and steady queue frames use identical keys.

This first prototype uses separate PUBLISH and ACK callbacks. Report their
combined per-frame cost: a cheap targeted read does not establish higher FPS when
full auditing, per-slot hashing and ACK transactions are still present.

## Build, test and replay

```
make -C game/raycaster
python3 game/raycaster/queue/test.py
python3 game/raycaster/queue/test_transport.py
python3 game/raycaster/queue/build_target.py --work FRESH --sources ARCHIVES
python3 game/raycaster/queue/build_transport.py --out MODULE --queue
```

The target wrapper selects the accepted word validator and renderer. The module
retains quiet-upload safeguards and 50 us completion polling. These options do
not change existing defaults, production autonet or the resident-network track.
`batch.py` runs baseline/queue/queue/baseline in a prepared isolated workspace;
it never stops services, forces unload, reboots or retries. `live.py` requires
exclusive use of the existing lock. `verify.py` independently reconstructs all
responses, complete slot contents, full audit integrity and the exact command
sequence from archived evidence. Preserve the exact binaries and sources.

Native tests cover full-queue rejection, wrong/duplicate ACKs, newer-epoch reset,
generation exhaustion, insufficient output capacity, incomplete publication,
40,960 single-bit slot corruptions, every new read boundary with completed failure
and timeout, and 10,304 mismatches between targeted bytes and full audits.
The C queue is also compared to an independent Python ownership model and the
unchanged native renderer. Card tests close with one unacknowledged frame to
verify restoration without requiring application-level draining.
