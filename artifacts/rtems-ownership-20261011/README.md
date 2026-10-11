# Resident ownership / cancellation batch — 2026-10-11

[Implementation and contract](../../rtems/ownership/README.md) ·
[16-step ledger and results](../../rtems/ownership/BATCH.md)

Five normal sessions completed 1,209 callbacks, 62 rollback/handoffs, five normal
commits, 67 clean owner restarts and five owner/waiter quarantines. Each session
restored the full 512 KiB original image and unloaded. An additional three-callback
session deliberately closed with a real mutex owner and blocked waiter; the host
retained resources and refused ordinary unload. All 1,212 original reports match
the exact native policy and pass the C report gate. Damaged copies are rejected.

- `live.tar.xz`: exact target build (binary, ELF, disassembly, symbols, map,
  objects, RTEMS headers/library and metadata), generated Linux module source
  and binary, build log, 48-callback smoke run, three 371-callback sessions,
  premature-close test, original raw paired captures and gzip traces, before
  boot ID, pre-test production close, and audited RTEMS semaphore/restart sources.
- `recovery.tar.xz`: same target/module binaries, after boot ID, post-reboot
  48-callback run with separate final-step log and full close, fresh production
  request/preflight/open. The running service's traffic and visitor logs are
  excluded. Production binaries remain in their earlier system-info artifacts.
- `verification.json`, `recovery-verification.json`: exact binary identities,
  native C policy replay under ASan/UBSan, C report gate and damaged-copy tests,
  saved response/audit checks, normal-close or retained-close verification.
- `native-tests.txt`: complete offline regression suite with ownership tests.
- `policy-final-tests.txt`: additional final wrap-exhaustion and repeated-cancel
  checks; these only extend native tests, not target code.
- `service-state.txt`, `http-restored.txt`, `production-verification.txt`: changed
  boot, fresh production preflight and paired original OPEN snapshot, active
  autonet, test module absent, and IPv6 HTTP 200 from the Mac.
- `source.tar.xz`: final ownership source, tests, verifiers, build registration,
  step ledger and project documentation. Existing loader/session dependencies
  are in the repository; starting Git revision was `c532865`.

The initial sessions do not have a separate final-step diagnostic log: closing
resets that log. Their terminal reports and full restoration remain intact. The
post-reboot session saves that log before close and verifies its ordering.
Preflight staging files are allocated slots; the OPEN files contain the actual
paired original snapshot. Neither detail is treated as missing card evidence.

The reference/ticket tests model software ownership, not DMA completion.
Quarantine keeps the unresolved lock and dependent objects; final disposal ends
the entire private bounded instance after callback return. This is not yet
asynchronous cancellation inside a permanently resident OS. No forced unloads,
flash writes or physical recovery tests were performed. The intentional retained
failure was saved and verified before reboot.

Reproduce verification from repository root, using empty scratch directories:

```sh
mkdir -p /tmp/i960-ownership-verify /tmp/i960-ownership-recovery
tar -xJf artifacts/rtems-ownership-20261011/live.tar.xz -C /tmp/i960-ownership-verify
tar -xJf artifacts/rtems-ownership-20261011/recovery.tar.xz -C /tmp/i960-ownership-recovery
python3 rtems/ownership/verify.py --root /tmp/i960-ownership-verify /tmp/i960-ownership-verify/ownership-smoke/run-0 /tmp/i960-ownership-verify/ownership-live1/run-0 /tmp/i960-ownership-verify/ownership-live1/run-1 /tmp/i960-ownership-verify/ownership-live1/run-2 /tmp/i960-ownership-verify/ownership-refusal
python3 rtems/ownership/verify.py --root /tmp/i960-ownership-recovery /tmp/i960-ownership-recovery/ownership-recovery/run-0
python3 rtems/ownership/verify_recovery.py /tmp/i960-ownership-verify /tmp/i960-ownership-recovery artifacts/rtems-ownership-20261011
make -C rtems test
python3 host/audit/artifacts.py --check-git
```

Exact target/module identities (same in all sessions):

```text
e8c799a02d12ba38a0722b58303c1b9e1a0e186bcf2a464c5d86f9836447ebba  ownership/kernel.bin (224356 bytes)
e92fa8f973227ba5a9b862fc6910a0ec060c74046c41fe9e58a54eac5abd36b4  ownership-module/dac960rtems.ko
```
