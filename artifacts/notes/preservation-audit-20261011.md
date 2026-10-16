> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Final remote preservation audit — 2026-10-11

This audit closes the gap between the locally collected work and Git. It is
read-only with respect to the card: no firmware command, module load, reboot,
flash write or interruption of a terminal session was performed.

## Scope and accounting

`remote-files.json` inventories 7,859 regular project files beneath
`/home/mit/i960*` by path, size and SHA256. Python caches and the compiler
installation/source trees were excluded from this first scan. The compiler
installation and the two source packages actually used are separately preserved
in [../toolchain-20261011/](../toolchain-20261011/README.md). This is not a backup
of the user's home directory, OS or personal configuration.

- `covered-files.json`: 7,553 files already represented by identical content in
  the workspace or in a local tar archive. `::` separates archive from member.
  The map records the first matching copy, not necessarily the preferred entry
  point. T3's inner ZIP captures remain losslessly encoded; use its decoder.
- `excluded-files.json`: 259 unique compiler/kernel intermediates (`.o`, `.cmd`,
  `.mod`, generated `.mod.c`, module symbol/order lists). Exact tested `.ko`
  modules and the source/build recipes are preserved; duplicate build debris
  adds no execution evidence.
- `copied-files.json`: 41 previously missing files, 593,748 bytes, copied under
  `recovered/` with their relative remote paths and individually hash-verified.
- `active-session-files.json`: six unique files observed while a new terminal
  session was live. These hashes are point-in-time observations, not a coherent
  completed snapshot. That session subsequently finished and is archived below.

The recovered files include early source revisions and host tools, original
Tetris and probe ELF files, runtime runner/demo ELF files and linker maps, and
T2 emulator build/trace logs. **Recovered historical sources are not the current
implementation.** Source lives under root `host/`, `loader/` and `game/`. Old
probes may assume stock firmware or invalid historical memory layouts; do not
run them merely because their binaries are available. The old compiler smoke
build and obsolete load-control binaries are retained as historical evidence.

## Additional completed terminal session

During the scan, PID 17974 was running the existing launcher with output
`/home/mit/i960-tetris-t4/sessions/20261011-000116/`. It was left untouched,
then observed to have exited before collection of the completed session.

`terminal-session-20261011-000116.tar.xz` preserves all its files, including
preflight, OPEN/CLOSE captures and gzip request/response trace.
`terminal-session-summary.json` is the client result;
`terminal-session-validation.json` is an independent native C replay and paired
full-restoration check. All 2,224 frames matched. The run lasted 111.387 seconds,
quit normally, restored RAM and unloaded. Median call was 42.34 ms; no simulation
ticks or input actions were dropped. This was a separately observed session,
not another scripted test launched by this audit; operator identity/input
provenance is not inferred from the trace.

`final-host-state.txt` records the unchanged boot ID, no DAC960 module in lsmod,
and no bound controller driver after completion. There was no new flash dump;
installed-ROM identity still refers to the earlier programming/postboot evidence.

To replay independently on macOS, from the repository root:

```sh
mkdir /tmp/i960-audit-session
# Use a new empty destination.
tar -xJf artifacts/preservation-audit-20261011/terminal-session-20261011-000116.tar.xz -C /tmp/i960-audit-session
cc -shared -fPIC -DTETRIS_CORE_ONLY -Igame game/tetris.c -o /tmp/i960-audit-native.dylib
PYTHONPATH=host/session:host/loadrun python3 host/session/validate_terminal.py /tmp/i960-audit-session/20261011-000116 --library /tmp/i960-audit-native.dylib
```

## Verification and remaining limits

The saved `i960-preserve-*-tests.txt` reports record reruns of programming tests
(5), loader tests (4), terminal tests (5), and session ASan/UBSan simulation
(292 command-boundary faults plus stale/malformed requests and six corruptions).
They are offline tests; hardware evidence is preserved separately.

[CURRENT-FINDINGS.md](../../CURRENT-FINDINGS.md) consolidates the current state
and gaps: recovery, DRAM timing decode, RAID I/O, preemption and RTEMS/networking
remain unproved or unimplemented. Historical source snapshots and their claims
are preserved unchanged; current documentation points to later results.

All curated files are covered by `../SHA256SUMS` and `../artifact-inventory.json`.
`python3 host/audit/artifacts.py --check-git` checks the bytes and inclusion in
the Git index. This audit prepares a local Git commit; it does not push anywhere.

Git whitespace checks pass for maintained sources and documentation. Historical
artifact snapshots and generated disassemblies retain original trailing spaces
and blank lines; they are intentionally not normalized, to preserve their hashes.
The installed toolchain archive was verified against all 119 regular-file and
symlink entries, and both source packages match their remote SHA256 values.
