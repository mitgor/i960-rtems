> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Asynchronous ownership / containment — 2026-10-11

[Contract and implementation](../../rtems/ownirq/README.md) ·
[16-step ledger, results and development finding](../../rtems/ownirq/BATCH.md)

Ten fixed-target asynchronous sessions passed with full RAM/MU restoration and
ordinary unload: five owner checkpoint/rollback/handoff sessions and five
owner/waiter quarantine sessions. In all cases unrelated preempted work continued.
One intentional outstanding-lease report and one initial padded-struct report
were rejected after real control/callback completion, retaining resources until
reboot. Both recoveries passed. The related persistent wire-copy fix passed a
separate 48-callback hardware regression. Production IPv6 HTTP is restored.

| Mode | STOP | Controller | Lease / retirement | Quarantine | End |
|---|---|---|---|---|---|
| 1: nested depth 2, clean | 18 | 40 | 44 / 44 | — | 50 |
| 2: depth 1, clean | 30 | 40 | 44 / 44 | — | 50 |
| 3: ordinary quarantine | 17 | 17 | 21 / — | 21 | 25 |
| 4: nested quarantine | 18 | 40 | 44 / — | 44 | 48 |
| 5: lease deliberately retained | 17 | 17 | — | 21 | 25 |

- `initial.tar.xz`: original target build and `ownirq-module-v2`, source snapshot,
  original rejected mode-1 run, retention/unload log, boot 1, and pre-test
  production close. The i960 ABI copied 48 bytes into an eleven-word wire slot,
  zeroing diagnostic word 51. The host gate correctly rejected it. The archive
  preserves the original bytes and binary; it is not relabeled a successful run.
- `live.tar.xz`: corrected target build (binary, ELF, map, disassembly, symbols,
  objects, headers, library, metadata), generated `ownirq-module-v3` source/binary,
  build log, fixed smoke run, eight-run matrix, outstanding-lease refusal, boot 2,
  and pinned RTEMS mutex/suspension sources. It was saved and verified before reboot.
- `recovery.tar.xz`: unchanged ownirq target/module and post-reboot mode-4 run;
  corrected persistent ownership build, pinned `ownership-module-wire44`, build
  log and 48-callback regression; boot 3; fresh production request/preflight/open.
- `initial-verification.json`: original paired bytes, binary identities, refusal,
  plus offline diagnosis changing only word 51 in a temporary copy. Original
  report remains rejected. No repaired report authorizes hardware cleanup.
- `live-verification.json`, `recovery-verification.json`: exact-image checks,
  real C report gate under ASan/UBSan, 308 damaged actual report rejections,
  control records, immutable bytes, full normal RAM/MU restoration or retention.
- `ownership-wire-verification.json`: 48 original reports replayed through the
  native ownership policy and host gate, paired captures and full restoration.
- `native-tests.txt`, `ownership-wire-tests.txt`: full native suite and policy tests.
- `production-verification.txt`, `service-state.txt`, `http-restored.txt`: three
  distinct boots matched to requests, fresh preflight, pinned original OPEN
  snapshots, active autonet, test module absent, IPv6 HTTP 200 from the Mac.
- `source.tar.xz`: final new profile, verifiers/tests, related ownership fix,
  build registration and documentation. Inherited switch/transport dependencies
  are tracked in the repository; starting revision was `c67d529`.

QUIESCED is execution state, not a software-reference/DMA completion. Mode 5
preserves a real blocked mutex dependency and a software lease; no physical DMA
engine is exercised. The instance is one-shot and borrowed, not a resident BSP.
Failure blobs expose a 512 KiB allocation; verification uses the recorded populated
471,136-byte prefix and original bytes beyond it. Production preflight exports
allocated slots; its OPEN captures contain the actual original snapshot. Raw
captures are unchanged. Visitor logs and live traffic are excluded. No flash
writes or forced unloads occurred.

Reproduce from repository root using empty scratch directories:

```sh
mkdir -p /tmp/i960-ownirq-initial /tmp/i960-ownirq-live /tmp/i960-ownirq-recovery
tar -xJf artifacts/rtems-ownirq-20261011/initial.tar.xz -C /tmp/i960-ownirq-initial
tar -xJf artifacts/rtems-ownirq-20261011/live.tar.xz -C /tmp/i960-ownirq-live
tar -xJf artifacts/rtems-ownirq-20261011/recovery.tar.xz -C /tmp/i960-ownirq-recovery
python3 rtems/ownirq/verify.py --root /tmp/i960-ownirq-initial --module ownirq-module-v2 --initial /tmp/i960-ownirq-initial/ownirq-smoke/run-0
python3 rtems/ownirq/verify.py --root /tmp/i960-ownirq-live /tmp/i960-ownirq-live/ownirq-smoke-fixed/run-0 /tmp/i960-ownirq-live/ownirq-live/run-* /tmp/i960-ownirq-live/ownirq-refusal
python3 rtems/ownirq/verify.py --root /tmp/i960-ownirq-recovery /tmp/i960-ownirq-recovery/ownirq-recovery/run-0
python3 rtems/ownership/verify.py --root /tmp/i960-ownirq-recovery --module ownership-module-wire44 /tmp/i960-ownirq-recovery/ownership-wire44-live/run-0
python3 rtems/ownirq/verify_recovery.py /tmp/i960-ownirq-initial /tmp/i960-ownirq-live /tmp/i960-ownirq-recovery artifacts/rtems-ownirq-20261011
make -C rtems test
python3 host/audit/artifacts.py --check-git
```

SHA256 identities:

```text
b5e3c1c1439676e661d751afc7187a5e7b31c728475b14e835fceb7f2c6be6c8  initial ownirq/kernel.bin
07a56581aa02642e3601c781520196a46586b7892541cb5badac0ff4ea7b67a0  fixed ownirq/kernel.bin
f2428ebf4d7b9d5274f363b1e397ddb9e14060fceba440f4f3d6b7f8cfd69ed9  ownirq-module-v3/dac960rtems.ko
bbb33f69a73cdab7d93fec28ff48f9e6daf8126a2b2272a409bbac4fb8e44e27  ownership/kernel.bin (wire44)
f557d755ca2b077e0df7c8a12877f33b97638ef1c00248a5dcd77ffa9748c1da  ownership-module-wire44/dac960rtems.ko
```
