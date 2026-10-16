> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Automatic containment batch — 2026-10-11

[Step ledger](../../rtems/switch/AUTOMATIC-SEQUENCE.md) and
[implementation/findings](../../rtems/switch/CONTAINMENT-BATCH.md).

- `critical.tar.xz`: `containcases` target build, first and final Linux module,
  six initial and six final raw sessions, build/run logs, pre-test production
  close. Final module moves the 1024-byte decode array off the kernel stack.
  Each group has three STOP-at-depth-2 and three STOP-at-depth-1 sessions.
- `critical-verification.txt`, `initial-verification.txt`: original paired
  bytes, exact images, C validation under ASan/UBSan, full RAM/MU restoration
  and unload. Each six-run group rejects 240 corrupted actual reports.
- `failure-1.tar.xz`: omitted STOP with final-user-fd close.
- `failure-2.tar.xz`: omitted RELEASE after QUIESCED with driver unbind.
- `failure-3.tar.xz`: invalid local report marker after callback completion,
  with original paired captures preserved and final-user-fd close.
- `failure-*-verification.txt`: exact images, retention state, no post-injection
  transactions/cleanup and refused ordinary unload. For case 3 the original
  paired response is independently validated; only the local decode was damaged.
- `boot-1.txt` through `boot-4.txt`: start and three recovery boots; the first
  three match request identities in their respective failure archives.
- `acceptance.json`: convenience copy of all original decoded reports/retention snapshots.
- `native-tests.txt`: full native suite, including 40 additional critical-report
  rejections and 18 unsafe-retention snapshots (in addition to existing tests).
- `source.tar.xz`: final generators, target sources, tests, verifier and docs.
- `recovery.tar.xz`, `recovery-verification.txt`: final fresh production
  preflight/open with paired original staging and boot identity checks.
- `service-state.txt`, `http-restored.txt`: final production service and HTTP check.

Failure archives include the exact original `contain` target, the same pinned
failure-test module, raw preflight/open/retained diagnostics and acceptance JSON.
In failure 3, debugfs exposes a 512 KiB allocation but the recorded read span is
only 471,136 bytes. Verification uses that populated prefix; the unused tail is
not presented as captured card RAM. Raw bytes are preserved.

Retained diagnostics do not establish successful restoration of those failed
sessions. Evidence is saved before each reboot; no forced unload or flash writes
are performed. Visitor logs and active production traffic are excluded.

```sh
python3 rtems/switch/verify_contain_capture.py artifacts/irq-containment-batch-20261011/critical.tar.xz --critical
python3 rtems/switch/verify_contain_capture.py artifacts/irq-containment-batch-20261011/critical.tar.xz --critical --initial
python3 rtems/switch/verify_contain_failures.py artifacts/irq-containment-batch-20261011/failure-1.tar.xz --mode 1
python3 rtems/switch/verify_contain_failures.py artifacts/irq-containment-batch-20261011/failure-2.tar.xz --mode 2
python3 rtems/switch/verify_contain_failures.py artifacts/irq-containment-batch-20261011/failure-3.tar.xz --mode 3
```

Exact SHA256 identities:

```text
e4d6e955e1146616a4602ca29a6fd157dc33385fda940fd920a40e0c2bf5228b  containcases/kernel.bin
9d2a39d3be4890b970a228a0c631da2396eca899ab673619fd75dead6edf334f  containcases-module/dac960rtems.ko (initial)
022a3f616fa4936b8a0972c520a6abe5a216045153829b935c76cc4cafa16144  containcases-module-v2/dac960rtems.ko (final)
c159fd8a06fc7d1829a775a46039eb13b90e6a0e8102b2fb8cdc2723ea5f6548  contain/kernel.bin
f4f8470720c246e7f82c5a77644498fcd40e1ecd99d36b6bd01a81e0660315b9  containfail-module/dac960rtems.ko
```
