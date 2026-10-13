# ROM-resident stock command hook

**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](../../docs/firmware/FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


Later live evidence is in [ROM-FETCH-LIVE.md](../../docs/loader/ROM-FETCH-LIVE.md): the
card fetched a stock flash `RET` after startup and executed a changed RAM
dispatch-table word. The new FEFE001C handler remains unflashed. The pinned
[three-write staging plan](../../artifacts/romhook-20261010/stage-plan/stage-plan.json)
reconstructs the offline candidate from the exact stock image; it performs
no hardware access. `stage_plan.py` and `test_stage_plan.py` define and test
the plan. The [live staging rehearsal](../../docs/loader/STAGING-REHEARSAL.md) passed with full
candidate and restored-stock verification. Programming CPU cache visibility
and updater integration remain to be resolved.

This is the step-3 successor to `loader/stockhook/`. The metadata entry at
`FEFE0000` patches the decompressed RAM command table word for opcode `0x6F`
to the `PING` handler at `FEFE001C`, then branches to the original stock entry
`C004A2E0`. The 20-byte handler writes status `0x017E` and tail-branches to
the stock completion function `C004BAD0`. It uses no private DRAM and does
not allocate or copy a handler at boot.

The whole 48-byte hook fits in the verified zero-filled flash padding inside
the pinned type-2 firmware component. `build_image.py` accepts only the exact
stock dump, unpacked program and inspected target binary; the result is a raw
offline image, not a vendor updater file. The archived original DRAM-backed
candidate remains in `loader/stockhook/` and `artifacts/stockhook-20261010/`.

Build on the SSH host with the archived i960 toolchain:

```sh
make CROSS=/home/mit/i960/tools/bin/i960-coff-
```

Rebuild the full image from the project root, using a new output path:

```sh
python3 loader/romhook/build_image.py \
  --stock artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin \
  --unpacked artifacts/vendor-fujitsu/4.07-0-29/unpacked.bin \
  --hook artifacts/romhook-20261010/romhook.bin \
  --out /tmp/romhook-rebuild.bin
python3 -B -m unittest discover -s loader/romhook -p 'test_*.py'
python3 -B loader/romhook/verify_layout.py \
  --stock artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin \
  --candidate artifacts/romhook-20261010/candidate-full-rom.bin \
  --hook artifacts/romhook-20261010/romhook.bin
```

See [ROM-HANDLER-STEP3.md](../../docs/loader/ROM-HANDLER-STEP3.md) for the storage decision
and remaining hardware gates. **Do not flash this raw image yet.**

Step 4 adds `package_update.py`, which wraps the exact candidate in the
matching Fujitsu type-2 MIMG after checking donor identity and complete
reconstruction. The wrapper is archived at
`artifacts/romhook-20261010/experimental-firmware.img`; it is also
`flash_ready: false`. See [ROM-HANDLER-STEP4.md](../../docs/loader/ROM-HANDLER-STEP4.md).
