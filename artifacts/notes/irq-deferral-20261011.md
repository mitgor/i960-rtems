> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Nested RTEMS dispatch deferral — 2026-10-11

Three bounded runs on the DAC960 passed without reboot or flash programming.
The original `autonet` service was cleanly stopped for the experiment, restored,
and fetched from the Mac at its global IPv6 address with HTTP 200 and Vader.

Each run observed:

| Measurement | Result |
| --- | --- |
| Critical-section ticks at dispatch depth 2 / 1 | 4 / 4 |
| Pending dispatch / different-heir observations while disabled | 8 / 8 |
| Task B IRQ entries before outer release / on A's return | 0 / 1 |
| A resumes from outer enable | tick 9, dispatch depth 0 |
| Total ticks / IRQ-path handoffs / both ISR contexts live | 32 / 24 / 23 |
| A ISR entries / returns | 20 / 20 |
| B ISR entries / returns | 12 / 12 |
| Faults, dangling ISR ownership, active ISR slots at exit | all zero |
| Register patterns, PC/TC, AC branch check, stack guards | passed |
| Full 512 KiB staging, execution/table/flash checks, module unload | passed |

Host callback latency was 246.97–248.64 ms. The timer uses reload 20000;
this is tick-count evidence, not a calibrated RTEMS wall-clock rate. Direct
outer-enable dispatch is not counted among the 24 IRQ-path handoffs.

## Preserved files

- `live.tar.xz`: target ELF, binary, disassembly, map, object/archive files and
  generated headers; generated Linux module source and module; three complete
  upload/request/raw-response/close captures; build/live logs and source snapshot.
- `source.tar.xz`: local build script and switch-profile sources including the
  final offline verifier. Generated RTEMS headers and target build are in live.
- `acceptance.json`: readable copy of the three raw-report interpretations.
- `native-tests.txt`: full `make -C rtems test` run, passed.
- `verification.txt`: exact binary identity, raw report, full cleanup and
  45 negative acceptance checks. The previous switch archive also reverified.
- `http-restored.txt`: normalized HTTP response after restoring production.

No visitor statistics or visitor address logs are included.

## Reproduce verification

```sh
python3 rtems/switch/verify_capture.py --defer artifacts/irq-deferral-20261011/live.tar.xz
```

The verifier reconstructs the prepared image and checks its request hash,
checks kernel/module hashes, decodes each raw report, rejects corrupted deferral
fields, and verifies both full staging readbacks and the saved close evidence.
The artifact inventory/SHA256SUMS covers this directory.

## Scope and next gate

This establishes nested **scheduler dispatch** deferral while timer interrupts
continue. It does not exercise arbitrary nested interrupts, dynamically owned
ISR slots, independent MU STOP in this active callback, resident takeover, disk
I/O, or DMA networking. Production HTTP remains on the prior `autonet` binaries.
Next combine independent framed MU STOP with these owned task continuations;
retain a local deadline and drain everything before returning to firmware.

Exact SHA-256 values from the live archive:

```text
12d75b5bcb04b924038b5b602abbc5367e362afd6c08d08846768cfbc540d0a6  defer/kernel.bin
998f023270fb6637192a914c734df9668ca98873d284f6930bfff162c0558849  defer/kernel.elf
1e5d935c5a9261fab43cf07210864bc2dab2fdfd98aff290a5d6e8e1f3173f57  defer-module/dac960rtems.ko
```
