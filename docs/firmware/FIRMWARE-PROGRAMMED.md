# Patched firmware programmed and boot-validated — 2026-10-10

**The card now runs the patched stock firmware.** Its boot hook installed the
ROM-resident opcode `0x6F` handler at `FEFE001C`; two postboot calls returned
`017E`. Stock firmware 4.07-0-29 Enquiry2/profile checks passed before and after
those calls. The final validation probe was unloaded and the card remains
installed and driverless at `0000:37:09.1` (`1069:0010`).

This is a returning PING extension to stock firmware. At this milestone it did not provide a general host software loader. The later
[RAM software loader](../loader/SOFTWARE-LOADER.md) supplies returning program execution
without another flash patch. Hardware boot-mode straps remain unchanged.

## Programming result

The user explicitly requested programming and validation after reboot. The
previously tested one-shot module was SHA256-checked against its local archive:
`4a213850505f3d7a2408094da0a671628617700f3dba10960a5904ca0a7641a9`.
It performed the full stock/candidate preflight and CPU CRC check, restored the
stock command table and temporary code, and submitted **one** `2B/1` command
(transaction ID 84) with the boot-block flag zero.

The command completed with matching ID and success. The stock routine freed
staging; subsequent normal reads rebuilt it using the traced physical-flash
byte-copy path. Both complete 524,288-byte readbacks matched the candidate:

`a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`

The last 16 KiB boot block matches the original stock image exactly. The harness
reported `program-state=8`, `submitted=1 completed=1 verified=1`,
`experiment-result=0`, and zero pending/dirty flags. All programming captures
were copied locally and independently validated before reboot was requested.
No second programming attempt, rollback upload, or recovery test occurred.

## Reboot and validation

SSH and ping did not immediately return after the requested reboot. The user
was asked to inspect the PC and power-cycle it if needed, then reported it back.
The user did not specify whether a power cycle was performed; do not infer one.
Linux was reachable with a new boot ID:

- Before: `fb8bd36a-68b2-415d-9650-4d83fe6c2f48`
- After: `a9429ca4-0144-452d-8a80-7189608ce99b`

A dedicated postboot probe blocked all `0x21` uploads. It checked the stock
profile, pointer, runtime entry and callbacks; read the entire ROM image twice;
verified two reads of dispatch word `C001F9BC` equal `FEFE001C`; then invoked
`0x6F` twice. Both returned `017E`. Enquiry2 still matched the original profile,
and two more complete image reads matched the candidate. All 54 commands
completed with matched IDs, expected status and intact DMA guards.

This establishes that the patch survived reboot, the metadata hook installed
the new dispatch target, and the ROM handler executes after startup while the
stock command path remains responsive. It is not a RAID I/O or long-duration
stability test. The delayed return after reboot is recorded without attributing
its cause; stock-era reboot delays were also observed earlier.

## Artifacts and reproduction

Everything is local under
[artifacts/programmed-rom-20261010](../../artifacts/programmed-rom-20261010):

- `programming/`: six full images (stock, staged candidate, fresh flash, each
  paired), all transaction/RAM captures, kernel log, and worker completion state.
- `postboot/`: four populated full candidate-image captures, paired boot-installed
  table reads, two PING results, health checks and kernel log. The unused middle
  image slots remain zero-filled and are not evidence.
- `postboot-build/`: exact tested module and source. The programming module/source
  remains in `artifacts/one-shot-harness-20261010/build/`.
- `programming.tar`, `postboot.tar`, boot/final-state records and
  [validation.json](../../artifacts/programmed-rom-20261010/validation.json).

The inherited postboot filenames `stage-before-*` and `stage-restored-*` mean
before/after PING reads of the patched image; this probe never restored stock.
Remote copies remain in `/home/mit/i960-programmed-20261010/` and
`/home/mit/i960-postboot-20261010/`.

Offline validation:

```sh
python3 host/program/validate_programmed.py --postboot
python3 -m unittest discover -s host/program -p 'test_*.py' -v
```

`host/program/build_postboot.py --out <new-directory>` reproduces the tested
postboot module sources. Build on the Linux host and use `pointer_check=1
runtime_check=1 stage_check=1`; it reads the candidate and invokes the returning
PING only after full image/table checks. Its build reports one harmless unused
stock-hash constant warning inherited from the shared header.

**Current hardware is no longer stock.** Old stock-preimage staging/programming
rehearsals will reject it; do not edit their pinned hashes to bypass this. Keep
historical manifests unchanged as creation-time provenance. This report and the
new validation JSON record actual programming/boot success. Recovery remains
untested and was excluded by the user.

The subsequent software loader uses this installed hook and temporary RAM
code, preserving stock firmware behavior without a new flash candidate. BIO1,
bounded Tetris, persistent sessions and SSH terminal play are now validated;
see [CURRENT-FINDINGS.md](../../CURRENT-FINDINGS.md).
