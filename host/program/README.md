# DAC960PG one-shot programming harness

**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](../../FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


Implemented and tested in simulation and a live **RAM-only rehearsal**.
No flash programming has been performed with this harness. See
[ONE-SHOT-PROGRAMMING.md](../../ONE-SHOT-PROGRAMMING.md).

## Build and test

From the repository root:

```sh
python3 -m unittest discover -s host/program -p 'test_*.py' -v
python3 host/program/build.py --out /tmp/i960-program-new-build
```

The output directory must not exist. The generator builds on the pinned
128-byte CPU CRC callback and the existing fixed staging harness. Build the
result on the matching Linux machine with `make -C <output> W=1`.
`one_shot.h` is shared verbatim by the kernel transport and native fault tests.
The integration test also compiles the generated staging transaction verbatim,
substituting models for hardware, CPU execution and hashing.

## Default live mode: RAM rehearsal

Load the generated `dac960dump.ko` with `pointer_check=1 runtime_check=1
stage_check=1`. The default `program_enable=0` stages the candidate, verifies
full SHA256 plus CPU CRC, restores temporary code/table, passes through the
one-shot dry-run gate, and restores the complete original staging image.
Default BDF is `0000:37:09.1`; the device must already be driverless. The driver
does not unbind another driver. Confirm debugfs exists and inspect the result;
successful module insertion alone does not establish that a device was probed.

A successful rehearsal reports `program-state=2 ... submitted=0`,
`experiment-result=0 pending=0`, and all dirty flags zero. Copy debugfs files
with `cat` into ordinary files before tarring them. Unload only after checking
those results and preserving captures.

## Enabled programming mode

Programming requires both `program_enable=1` and `program_token` equal to the
full candidate SHA256:

`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`

The token is a deliberate activation guard, not a secret or authentication
credential. A missing/wrong token is rejected by module initialization before
PCI driver registration. Supplying a token with programming disabled is also
rejected. The module refuses missing preflight flags or mixed experiments.

**Enabled insertion starts the transaction automatically in a workqueue.**
There is no later “confirm” button. It performs the same RAM/CPU preflight,
restores stock dispatch and temporary code, retains the verified candidate,
then submits one fixed `2B/1` command with byte 3 zero. It never sends `0x22`,
changes the boot-block flag, accepts arbitrary mailbox bytes, or retries.

The enabled run pins the module, PCI device and resources until reboot,
including when preflight fails. This intentionally avoids releasing module
text from inside its worker and prevents unloading after an uncertain result.
Do not unbind it through sysfs. Nothing automatically reboots or resets the PC.
`worker-state` in `/sys/kernel/debug/dac960dump/` is 1 while running and 2 when
finished. State 2 means finished, not success. Follow kernel logs for progress;
the complete `result.txt` size is published at worker completion. Capture files
must not be treated as final while the worker is running.

Program completion has a 120-second observation deadline in the worker; normal
commands retain the CPU rehearsal's ten-second deadline. Deadline expiry stops
the sequence, retains resources and does not imply the device stopped erasing
or programming. A tag mismatch likewise leaves the completion unacknowledged.

After a matched successful programming completion, two complete `0x20` reads
must match the candidate SHA256 and the preserved boot block. On this pinned
firmware, programming frees staging and the next read repopulates it through
physical-flash byte loads; see PROGRAMMING-PREFLIGHT.md for the traced contract.
No RAM upload is permitted after the program doorbell, including on error.
The third pair of full images is named `flash-readback-*.bin` in enabled mode;
it is `stage-restored-*.bin` in default mode.

## State values

| Value | State | Meaning |
| --- | --- | --- |
| 0 | NEW | Programming gate not reached; inspect preflight result |
| 1 | REFUSED | No programming doorbell; pre-submit failure |
| 2 | DRY_RUN | Programming disabled; RAM rollback follows |
| 3 | READY | Internal pre-submission state |
| 4 | SUBMITTED | Programming doorbell has been rung once |
| 5 | UNCERTAIN | Timeout or unmatched completion; no retry/readback/rollback |
| 6 | PROGRAM_FAILED | Matched nonzero status; no retry/readback/rollback |
| 7 | READBACK_FAILED | Matched success but full readback did not validate |
| 8 | VERIFIED | Matched success and full fresh readback validated |

Only state 8 with `experiment-result=0` establishes this harness's programming
and readback success. Boot-hook execution still requires a subsequent reboot
and separate health/`0x6F` checks. Recovery testing remains excluded by request.

Archived rehearsal evidence can be revalidated offline with:

```sh
python3 host/program/validate_rehearsal.py
```
