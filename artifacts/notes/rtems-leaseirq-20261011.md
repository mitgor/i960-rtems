> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Continuous execution lease evidence — 2026-10-11

[Contract and ownership table](../../rtems/leaseirq/README.md) ·
[Sixteen-step ledger and results](../../rtems/leaseirq/BATCH.md)

Nine sessions passed **23 callbacks and 13 continuous execution leases** with
full normal restoration/unload. This includes a 60-second uninterrupted run,
a 24,000-tick administrative-cap run lasting about 115 seconds, renewal and
no-grant expiry, one host-silent second, and a persistent quarantined two-lock
chain while an independent task kept running. All 40,111 hardware checks reported
zero drift. Production IPv6 HTTP was restored on the same Linux boot.

- `live.tar.xz`: exact target binary/ELF/map/disassembly/symbols, library, headers
  and build metadata; generated v2/v3 host-module sources/binaries; original
  requests, control transcripts, paired captures, compressed traces and reports
  for all sessions; verified pre-test production close and fresh production
  request/preflight/open. Object intermediates omitted. Individual archive bytes
  were hash-compared before removing redundant loose copies.
- `source.tar.xz`: new profile, policy/model/gate tests, live harness, offline
  replay, build registration and documentation. Inherited dependencies remain
  tracked in Git. Starting revision: `22b314a`.
- `evidence/replay.json`: all 23 original replies checked with the actual C gate,
  exact payload/module identities, persistent state/chain invariants, control
  timing and normal restoration. **1,610** damaged actual reports rejected.
- `evidence/native-tests.txt`: full RTEMS native suite. `final-native-lease.txt`
  covers the final host builder; 192 modeled transitions plus cap/wrap/deadline
  cases and 29 new hardware-proof mutations under ASan/UBSan.
- Original build/test logs include the initial pre-hardware compile failure.
  The missing generated declaration and output-length constant were corrected
  before the first live run. v3 preserves the status observation before RELEASE
  instead of overwriting it with a later read; its fresh live regression passed.
- Service/HTTP/production-verification evidence confirms autonet owns the card,
  the test module is absent, original paired OPEN bytes match the known ROM SHA,
  and the Mac received the Vader page with HTTP 200. No visitor logs exported.

The long run saw 12,502 lease ticks and 291 renewals; the cap run stopped at
exactly 24,000 lease ticks despite 559 renewals. Expiry stops at 512 ticks since
the last grant/renewal. First-command logs preserve the outstanding firmware
callback with no new stock submission or early completion inside the lease.
These are parked-firmware execution leases, not DMA/SCSI takeover. No flash
writes, forced unloads, reboot or direct DMA-engine programming occurred. Existing loader DMA remained
part of normal upload/readback/restoration.

```sh
mkdir -p /tmp/i960-leaseirq-replay
tar -xJf artifacts/rtems-leaseirq-20261011/live.tar.xz -C /tmp/i960-leaseirq-replay
cp -R artifacts/rtems-leaseirq-20261011/evidence /tmp/i960-leaseirq-replay/
python3 rtems/leaseirq/verify.py --root /tmp/i960-leaseirq-replay \
 /tmp/i960-leaseirq-replay/leaseirq-smoke/smoke \
 /tmp/i960-leaseirq-replay/leaseirq-matrix/*/ \
 /tmp/i960-leaseirq-replay/leaseirq-cap/cap \
 /tmp/i960-leaseirq-replay/leaseirq-final/smoke
python3 rtems/leaseirq/verify_production.py /tmp/i960-leaseirq-replay
make -C rtems test
python3 host/audit/artifacts.py --tracked-only --check-git
```

Original ROM SHA256:
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
Exact target/module hashes are preserved per session and checked by replay.
The explicit tracked-only inventory scope leaves concurrent application artifacts
outside this batch until their owner stages them.
