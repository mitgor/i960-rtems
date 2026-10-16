> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Remote preservation audit — 2026-10-10

Compared remote project files by SHA-256 with this working tree, including
uncommitted files. Scope: `/home/mit/i960-analysis.7jVBmy`, `fwpkg`, `fwpkg_prl`,
`biosA`, `scratch`, `i960/host`, `i960/game`, `i960/t`, and `i960/toolchain.sh`.
`remote-files.json` lists the 295 files examined; `copied-files.json` identifies
20 additional artifacts copied and checked against the remote SHA-256 hashes.
This is a project audit, not a backup of the user's home directory.

## Additional files preserved

- `control/result.txt`: initial Enquiry2-only control log. Its response bytes are
  already present in the existing Enquiry2 captures (same hash).
- `acquisition-module/dac960dump.ko`: exact successful acquisition module,
  built for Ubuntu kernel 6.8.0-138-generic. Its source matches the local
  `host/dump/dac960dump.c`. Keep for provenance; rebuild for a different kernel.
- `historical-scripts/`: eight exploratory decoding and symbol-search scripts.
  **These are historical experiments, not supported tools.** `gf_decode.py` is
  XOR-only and incomplete; `symparse.py` uses the incorrect name-before-address
  assumption, superseded by `host/dump/vendor_symbols.py`. `gfmake.py` retains
  the ten-byte trailer in raw outputs. The correct individual decoder is already
  archived as `vendor-fujitsu/4.07-0-39/decoded/globalflash_decode.py`.
- `bios/b.asm`: alternate BIOS disassembly. The associated ROM already matches
  `artifacts/dac960pg-x86-bios.rom` exactly.
- `loader-build/`: exact i960 loader and hello binaries, ELF files, maps and hello
  disassembly from the remote target build. The loader disassembly already exists
  in `artifacts/analysis/loader-target.dis`. These are software-build evidence;
  hello's internal-RAM execution address is invalid on hardware (see loader docs).
- `historical-sources/dac960probe.c`: old remote probe revision, retained without
  replacing the corrected working source. Do not use as the current probe.
- `toolchain/smoke-test.c`: small compiler code-generation example.

## Already preserved or not useful to duplicate

Both original Fujitsu packages, correctly decoded firmware and boot blocks, all
snapshot captures and successful acquisition logs, the collector, and primary
firmware/flasher disassemblies were already present by content hash. The remote
toolchain build script also matches a local file. Sources for the current dump
harness and loader match the local working tree.

The remaining differences include kernel build intermediates, host executables,
compiler smoke-test objects, and failed XOR/bit-reversal firmware transforms.
These can be regenerated or are superseded failed outputs; the audit manifest
preserves their hashes without treating them as valid firmware. Python caches
were omitted. Compiler installations and large build trees are not vendored here.

No hardware commands, module loading, reboot, or flash writes were performed
for this audit. Files are available for Git, but no commit or push was made.

The installed GCC 3.3.6 and binutils 2.27 source trees were compared with every
regular file in their saved upstream tarballs: no original source files had been
modified. No unique compiler patches were found to preserve. Installed versions
reported GCC 3.3.6 and GNU objdump 2.27.
