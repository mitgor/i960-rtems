# Live RAM dispatch and post-startup flash fetch — 2026-10-10

**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


Latest (2026-10-10): [programming preflight and live CPU verification](PROGRAMMING-PREFLIGHT.md)
passed. The CPU read all 512 KiB of the candidate through programmer alias
C1F2C000 with explicit cache invalidation and matched CRC32 2012D01F. All 105
commands completed cleanly; original staging/table/code restored, probe unloaded.
The descriptor policy and bytewise post-program flash-readback route are now
documented. Next implement the one-shot programming state machine and its
failure tests. No flash programming or recovery test occurred. Exact evidence
is in `artifacts/programming-preflight-20261010/` from the repository root.


## Result

Two hardware questions are now answered on the installed DAC960PG running
4.07-0-29:

1. A host-uploaded replacement for opcode `0x6F`'s table word at `C001F9BC`
   became visible to the i960. The card executed a RAM handler, returning
   distinctive status `017E`, then another handler returning `017F`.
2. After normal startup, the card fetched and returned from a stock `RET`
   instruction in its flash image at **`FEFB022C`**. The RAM callback that made
   that `callx` returned status `017F`. The command table and both temporary RAM
   sites were restored, and stock opcode `0x6F` again returned `0104`.

This establishes a practical path for a patched ROM handler, but the **new
`FEFE001C` handler itself has not been flashed or executed**. The offline
candidate remains `flash_ready: false`. No flash erase, program command,
firmware update or recovery check was performed.

## Evidence and address correction

The exact [successful run](artifacts/romfetch-live-20261010/attempt5/result.txt)
shows statuses `017E → 017F → 0104`, `experiment-result=0`, `pending=0`,
`exec-dirty=0`, and no DMA guard changes. The paired binary captures confirm
the table values `C0FAC100 → C0FAC180 → C001FE98`; both 64-byte RAM regions
match their originals after restoration. The probe module was unloaded and the
card is driverless. The [validator](host/dump/validate_rom_fetch.py) checks
these claims and the earlier controls; its
[report](artifacts/romfetch-live-20261010/validation.json) passed.

The previous disassembly labeled the main-firmware component as though it
began at `FEFC8000`. Its bytes actually occupy offset `0x30000` of this
512 KiB software image, physically corresponding to `FEFB0000` in the
`FEF80000–FEFFFFFF` window. The stock `RET` at image offset `0x3022C` is
therefore at `FEFB022C`, **not** `FEFC822C`. The earlier `callx FEFC8208`
targeted unrelated bytes and timed out. That failed run does not show that
post-startup flash fetch is disabled.

The [read-only flash-map capture](artifacts/romfetch-live-20261010/flash-map3/result.txt)
confirms the address translation. At `FEFB0200`, `FEFC8200`, and `FEFE0000`,
all 48 captured 32-bit words have the saved image byte from the corresponding
offset in the low lane and the target address in the upper three lanes. Each
window matched across A5/5A paired reads. This is consistent with the card's
8-bit flash bus; a 32-bit DMA word is **not** four consecutive ROM bytes.
The source image has `00 00 00 0A` (`RET`) at `FEFB022C`, and the target-built
RAM callback calls that exact address after `icctl 2,0,g0`. The successful
post-call status provides the instruction-fetch evidence; the data reads
alone would not.

## Probe sequence

| Artifact | Purpose and result |
| --- | --- |
| [Attempt 1](artifacts/romfetch-live-20261010/attempt1/result.txt) | First table rewrite executed RAM status `017E`; later dispatches used a stale cached pointer. Pinned module; reboot cleared state. |
| [Attempt 2](artifacts/romfetch-live-20261010/attempt2/result-from-dmesg.txt) | RAM control with `dcctl` returned `017E`; the callback calling the incorrectly addressed `FEFC8208` timed out. DMA/module retained; reboot cleared state. The dynamic debugfs blobs in the raw tar were archived at zero length; use the saved kernel-log transcript. |
| [Attempt 3](artifacts/romfetch-live-20261010/attempt3/result.txt) | RAM-only `icctl` control returned `017F`; stock dispatch and RAM bytes restored. |
| [Attempt 4](artifacts/romfetch-live-20261010/attempt4/result.txt) | RAM `callx` to a RAM `RET` returned `017F`; stock dispatch and RAM bytes restored. |
| [Flash mapping](artifacts/romfetch-live-20261010/flash-map3/result.txt) | Paired read-only windows established the 8-bit flash-bus low-lane pattern and physical image offset. The first flash-map attempt read only four bytes; the second had a short debugfs allocation for its last window, corrected in this final run. |
| [Attempt 5](artifacts/romfetch-live-20261010/attempt5/result.txt) | RAM callback `callx FEFB022C` fetched stock flash `RET`, returned `017F`, and restored all modified RAM. |

The fixed harness is [host/dump/dac960dump.c](host/dump/dac960dump.c), with
exact byte arrays and address allowlists in
[host/dump/rom_exec.h](host/dump/rom_exec.h). Target sources and binaries are
in [loader/romfetch/](loader/romfetch/). Exact module/source snapshots for
attempts 1–5 and the read-only mapping runs are under
[`artifacts/romfetch-live-20261010/`](artifacts/romfetch-live-20261010/).
Twenty-six host Python tests pass; each Linux module built with `W=1`.

## Remaining work before testing the patched ROM

The result supports the feasibility of executing `FEFE001C` after startup,
and the low-lane read at `FEFE0000` matches the zero-filled stock slot.
It does not prove that the proposed 48-byte patch was programmed or that its
boot-time table installation works. The offline
[three-write staging plan](artifacts/romhook-20261010/stage-plan/stage-plan.json)
pins 56 upload bytes at offsets `0x60000` (48-byte hook), `0x67F68`
(entry word), and `0x67FDC` (checksum word). Applying only those bytes to the
exact stock snapshot reconstructs the candidate. The [no-program live staging rehearsal](STAGING-REHEARSAL.md) subsequently
passed: paired full images matched stock, candidate and restored-stock hashes.
All 74 commands completed cleanly and the module was unloaded. Next resolve
CPU cache visibility in the programming path and finalize the matching Fujitsu
updater/descriptor procedure before programming. A later
programmed-image test must independently read back exact flash bytes and
exercise opcode `0x6F` from the new handler. The `2B/1` route erases the
lower 496 KiB, including that
handler's sector; update-time behavior must be accounted for. Recovery
testing remains explicitly outside this work.
