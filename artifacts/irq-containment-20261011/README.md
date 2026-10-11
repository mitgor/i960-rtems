# STOP-ignoring task containment — 2026-10-11

Three fresh `contain` sessions passed on the DAC960 at `192.168.2.75`.
[Implementation and limits](../../rtems/switch/CONTAINMENT.md).

The controller externally suspended two workers that never inspect STOP. Both
continued for four ticks after STOP, then stopped progressing. Their original
ISR frames remained live and their entire task/ISR stacks stayed unchanged over
10,000 checks. A distinct QUIESCED acknowledgement preceded callback return;
full RAM/MU restoration and ordinary module unload passed after each session.
No reboot or flash writes occurred. Production IPv6 HTTP was restored with 200.

| Run | STOP / containment ticks | A entries / returns | B entries / returns |
| --- | --- | --- | --- |
| 0 | 36 / 40 | 20 / 19 | 20 / 19 |
| 1 | 41 / 45 | 23 / 22 | 22 / 21 |
| 2 | 52 / 56 | 28 / 27 | 28 / 27 |

Each worker deliberately retains one continuation; this is not successful ISR
unwinding. Whole-instance disposal after return makes restoration possible.
The emergency loop ceiling remained unexhausted. Permanent interrupt masking,
scheduler corruption and resident task resource cancellation remain untested.

Contents:

- `live.tar.xz`: exact i960 build (binary, ELF, map, symbols, disassembly, core
  library and metadata), Linux driver sources/module, deployed sources, build/run
  logs and all three raw sessions. Each includes paired callback/close captures,
  trace, control records, image identities, MU snapshots and acceptance/cleanup
  reports. Also includes the pre-test production close and pinned RTEMS suspend
  implementation/state definitions used for the design audit.
- `source.tar.xz`: final local profile sources, host gate, native tests, verifier,
  build recipes and Markdown documentation. The live archive records sources as
  deployed; final documentation and the offline verifier were added afterward.
- `acceptance.json`: convenience copy of the three original decoded reports.
- `verification.txt`: original paired responses, exact image/module identities,
  full restoration/MU checks and ASan/UBSan C gate; 60 corrupted actual reports
  rejected by both C and Python.
- `native-tests.txt`: full passing RTEMS suite, including 91 corrupted synthetic
  containment reports rejected by both validators and generated cleanup-gate checks.
- `http-restored.txt`, `service-state.txt`: HTTP response and final production
  service state, with test module absent and unchanged boot ID.

Visitor statistics, visitor IP logs and active production traffic are excluded.

```sh
python3 rtems/switch/verify_contain_capture.py artifacts/irq-containment-20261011/live.tar.xz
make -C rtems test
```

Exact SHA256 identities:

```text
c159fd8a06fc7d1829a775a46039eb13b90e6a0e8102b2fb8cdc2723ea5f6548  contain/kernel.bin
6d7a1fe74522ddb7bbc1c5f9d48ed73025ed6056df142d755ef5a8b039f8a128  contain-module/dac960rtems.ko
```
