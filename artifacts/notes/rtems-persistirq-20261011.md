> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Persistent asynchronous RTEMS — 2026-10-11

[Contract](../../rtems/persistirq/README.md) ·
[Completed sixteen-step batch](../../rtems/persistirq/BATCH.md)

Five normal sessions passed **120 callbacks**, 29 clean rollback/handoffs, five
quarantined generations and 46 further interrupt-driven epochs of the independent
worker. A separate six-callback early-close test deliberately retained resources
after valid QUIESCED/callback completion; ordinary unload was refused. Evidence
was copied and replayed before reboot. Recovery passed a fresh session, full
restoration and production IPv6 HTTP 200 from the Mac.

- `live.tar.xz`: exact target binary/ELF/map/disassembly/symbols, RTEMS library and
  headers/build metadata; image-pinned generated host module/source; all six
  sessions' request identities, traces, paired captures, control records, reports,
  normal close or retained-close evidence; pre-test production close and fresh
  production request/preflight/open. Compiler object intermediates were omitted.
  Original files were hash-compared with the archive before deleting redundant
  local loose copies. Raw reports and HTTP responses are unchanged.
- `source.tar.xz`: new profile, native/live/offline tests, build integration and
  batch documentation. Inherited switch/transport/ownership dependencies are
  tracked in Git; starting revision is `6ec2c0d`.
- `evidence/replay-before-reboot.json`: 108 callbacks verified before reboot,
  including retained-close evidence.
- `evidence/replay-final.json`: all 126 callbacks verified against the real C
  host gate; 5,922 damaged actual reports rejected. Checks include stable task,
  stack and ledger identity; transitive quarantine invariants; clean handoff
  values; control handshakes; original paired captures and full restoration.
- `evidence/native-tests.txt`: full native suite, including 32,400 graph cases
  checked against independent reachability and 94 unsafe report mutations under
  ASan/UBSan.
- `evidence/persistirq-build-v2.log`, matrix/refusal logs: original build and test
  output. The final build fixed a volatile-pointer compile warning before the
  first card invocation; no rejected target runs occurred in this batch.
- Boot, service, HTTP and production-verification files prove the recovery boot
  differs from the test boot, production owns the card again, and the test module
  is absent. Live visitor statistics and traffic logs were not exported.

The retained module state was `[resident_open=1,pending=0,runner_uncertain=0,
exec_dirty=1,stage_dirty=1,dma_present=1,bar_present=1,stop_clean=1]`, refcount 1.
A repeated observation agreed; no card command or forced unload followed refusal.
These are software leases and two real RTEMS mutexes, not actual DMA completion.
The persistent instance is paused between callbacks with its timer restored.

Reproduce offline from repository root:

```sh
mkdir -p /tmp/i960-persistirq-replay
tar -xJf artifacts/rtems-persistirq-20261011/live.tar.xz -C /tmp/i960-persistirq-replay
python3 rtems/persistirq/verify.py --root /tmp/i960-persistirq-replay \
 /tmp/i960-persistirq-replay/persistirq-smoke/run-0 \
 /tmp/i960-persistirq-replay/persistirq-matrix/run-* \
 /tmp/i960-persistirq-replay/persistirq-early-close/run-0 \
 /tmp/i960-persistirq-replay/persistirq-recovery/run-0
cp -R artifacts/rtems-persistirq-20261011/evidence /tmp/i960-persistirq-replay/
python3 rtems/persistirq/verify_recovery.py /tmp/i960-persistirq-replay
make -C rtems test
python3 host/audit/artifacts.py --tracked-only --check-git
```

Known original ROM SHA256:
`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
Target and module SHA256 identities are pinned in each original `request.json`
and validated against the archived binaries. No flash was written.

The artifact audit supports explicit `--tracked-only` scope so unrelated files
being prepared by a parallel application task remain outside this batch. Stage
new batch artifacts before `--tracked-only --update`; the default still audits
all files. This batch leaves the concurrent CHIP-8 work untouched.
