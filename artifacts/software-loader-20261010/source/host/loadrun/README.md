# Linux runtime loader

See [SOFTWARE-LOADER.md](../../SOFTWARE-LOADER.md) for live results, build/run
commands and limits. This profile requires the installed patched ROM, exact
board/staging state and an idle driverless card at `0000:37:09.1`.

- `build.py` derives a separate `dac960loadrun` kernel module from the guarded
  dump transport, replaces its experiment with `transaction.h`, embeds the
  pinned runner, and rejects base-source drift at required replacement sites.
- `policy.h` bounds uploads and entry points; payloads come from Linux
  `request_firmware`, held until safe cleanup.
- `loadrun.py` validates inputs, serializes its own runs, checks ownership,
  installs a content-addressed payload, inserts the module, saves debugfs
  captures, unloads only after clean state and independently verifies evidence.
- `test_transaction.c` tests the actual transaction against a fault-injecting
  firmware model. It does not simulate i960 instruction execution.

Run `python3 host/loadrun/test_loadrun.py` from the repository root. No hardware
is touched by generation or tests. Do not run other raw probes concurrently;
the CLI lock cannot protect against independent direct PCI access.

The module retains historical capture filenames: `stage-candidate-*` contains
the RAM payload overlay, **not a flash candidate**; `exec-flash-*` captures the
RAM runner; `dram-hook-*` is the paired 16-byte result, with little-endian return
value then marker `0x52554e31`; `upload-test/restore.bin` saves original result
RAM. `result.txt` is the full transaction log. Never pass these RAM-overlay
images to the flash programmer.
