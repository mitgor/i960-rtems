# Step 4: update wrapper and live dispatch preflight — 2026-10-10

**Later evidence:** [ROM-FETCH-LIVE.md](ROM-FETCH-LIVE.md) proves the running
card used a changed `0x6F` table word and fetched a stock flash `RET` after
startup. Its address correction supersedes the FEFC8208 wrapper inference
below. The *new* FEFE001C handler is still unflashed and untested.

**Result:** the exact step-3 ROM-backed hook is now wrapped in a matching
Fujitsu type-2 MIMG for offline examination. A separate fixed, read-only SSH
probe verified the running card's opcode `0x6F` dispatch word. Neither result
establishes that the proposed ROM handler can execute after stock startup. The
candidate remains `flash_ready: false` and has not been installed.

## Offline package

`loader/romhook/package_update.py` reconstructs the exact pinned 512 KiB
candidate from the stock dump, verified decompressed program and 48-byte
target hook. It accepts only the exact archived Fujitsu 4.07-0-29 MIMG, checks
its header, trailer, declared length, component type and stock component
bytes, then replaces only its type-2 payload. Recombining the new payload
with the stock image outside `0x30000–0x67FFF` reproduces the candidate
byte-for-byte. The 512-byte header and ten-byte trailer are unchanged.

The resulting [experimental-firmware.img](artifacts/romhook-20261010/experimental-firmware.img)
is 229,898 bytes; SHA-256
`4c32da1011bcf182b08998a8a00148a665e957d3958593e76d81605a1e72dc2b`.
Its [manifest](artifacts/romhook-20261010/experimental-firmware.img.json)
records the exact inputs and leaves vendor acceptance, hardware validation,
recovery and flash readiness false. MIMG consistency does **not** validate
the updater's descriptor changes or the subsequent `2B/1` operation, which
erases and rewrites the lower 496 KiB. No updater or programming command ran.
The existing [recovery audit](artifacts/romhook-20261010/recovery-audit/audit.json)
also passed its **partial** header, type, declared-length, descriptor-length
and adapter-ID checks for this new package. It extracted the unchanged
10,752-byte stock recovery monitor; vendor acceptance remains unverified.

## Live table observation

The running card at `0000:37:09.1` was driverless and reported firmware
4.07-0-29. A new opt-in `rom_table_check=1` mode in `host/dump` required the
existing staging-pointer and runtime-profile checks, then allowed exactly
two four-byte opcode-`0x20` reads at local `C001F9BC` (wrapped staging offset
`FF0F39BC`). The A5 and 5A sentinel captures matched: `98 FE 01 C0`, or
`C001FE98`, the pinned stock unsupported-command handler. All 15 commands
completed with matched IDs, status zero and unchanged DMA guards. The
independent [validator](host/dump/validate_rom_table.py) passed; the
[capture](artifacts/romhook-step4-20261010/live/result.txt) and
[report](artifacts/romhook-step4-20261010/live-validation.json) are archived.
The probe was removed normally; the card is driverless again.

This establishes the live preimage and table address for the proposed patch.
It does not test writing that word, i960 cache visibility, dispatch to a
new target, or instruction fetch from `FEFE001C`. The stock bootstrap fetches
flash before normal startup, but the program later writes `8` to EBCR at
`C004E840`; post-startup flash **data** reads do not prove instruction fetch.
The matching program also contains three `callx` wrappers at
`C004CC88–C004CCA8` targeting boot-block addresses `FEFC8208`, `FEFC81C0`
and `FEFC81E0`. A scan found no direct call or embedded pointer to those
wrappers, so their presence alone does not establish that a running stock
card reaches a post-startup flash instruction fetch.

## Remaining gates

1. Prove a safe, restorable path to execute a controlled instruction from the
   firmware flash window after the EBCR write, or obtain equivalent hardware
   evidence. Do not infer it from the bootstrap's earlier execution.
2. Verify live visibility of a changed dispatch word without leaving a
   persistent modification. The read-only probe only established its stock
   value; no callback/table write was attempted.
3. Design the handler's behavior during the stock `2B/1` rewrite of the flash
   region containing it. Suspend the new opcode or arrange a stable copy
   before erasure, with a verified restoration route.
4. Verify recovery entry and restoration on hardware, including the serial
   path described in [SERIAL-RECOVERY-SETUP.md](SERIAL-RECOVERY-SETUP.md), and
   satisfy the independent backup gate in [REFLASH.md](REFLASH.md) before
   programming. Vendor acceptance and descriptor mutation remain untested.

The wrapped `0x21` upload offset may merit a separately reviewed RAM-write
experiment, but existing evidence does not make a live table rewrite or
arbitrary callback handoff safe. There was no RAM upload, custom execution,
reset, reboot, recovery transition or flash write in step 4.
