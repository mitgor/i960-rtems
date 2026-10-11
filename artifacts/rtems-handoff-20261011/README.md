# DMA/SCSI ownership and callback-free monitor evidence

See [contract](../../rtems/handoff/README.md) and [batch](../../rtems/handoff/BATCH.md).
All experiments were RAM-only. No flash, SCSI-engine or DMA-engine programming.

- `initial.tar.xz`: original target, generated module v2, first failed live
  session, and original source snapshot. Omitted RELEASE timed out; module pinned.
- `handoff-v3-diagnostic.tar.xz`: consumed-ENTER target/module v3, successful
  sideband exchanges followed by diagnostic assertion failure, and build/run logs.
  Its `failed-close` nevertheless records verified STOP and full RAM restoration.
- `handoff-final.tar.xz`: final target ELF/bin/map/disassembly, build metadata,
  generated module v4 sources/binary, four complete passing sessions and logs.
- `handoff-guard-final.tar.xz`: final module v5 with immediate write lockout on
  uncertainty, fifth passing session and a source snapshot. Same target binary.
- `handoff-production-v4.tar.xz`: intermediate production restoration evidence.
- `handoff-production.tar.xz`: actual pre-test production close, intermediate clean close and final restored
  production preflight/OPEN/request identity, autonet build identity and launcher.
  Live visitor statistics are excluded.
- `firmware-audit/`: byte-checked matching-ROM DMA excerpts and limitations.
- `evidence/`: PCI topology, initial retained MU samples/refcount/error, recovery
  boot, native tests, final replay, production verification and IPv6 HTTP response.

Extract archives into separate scratch directories when comparing builds; they
intentionally contain the same `handoff/` pathname with different binaries.
Extract `handoff-final.tar.xz` and `handoff-guard-final.tar.xz` together and run:

```sh
python3 rtems/handoff/verify.py --root /path/to/extracted
```

Final replay validates five sessions, 20 entries, five expiries, ten denials,
125 rejected report mutations and full restoration. Source for the final build
is in `rtems/handoff/`; the v3 consumption change is `entry.h`, while its policy
is the original policy preserved in `initial.tar.xz`. Exact build hashes are in
per-session `request.json` and `build.json`. Redundant loose artifact copies were
byte-compared to their archives before removal; counts are recorded in evidence.

Old boot: `82403cf7-9150-4581-b032-e029c2dd6484`.
Recovered/final/production boot: `3c5b99fb-e6a3-4bab-8df2-fdd16e43b1d9`.
A clean close and HTTP reply are not disk-I/O, recovery or long-term stability tests.
