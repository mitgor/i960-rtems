# Runtime software loader evidence

Collected 2026-10-10, Europe/Berlin. See ../../SOFTWARE-LOADER.md.

- `target/`: exact i960 runner/demo/mix raw binaries and disassemblies.
- `module/`: generated kernel-module sources and exact Linux 6.8.0-138-generic
  `dac960loadrun.ko` used for all three runs.
- `source/`: source snapshot of host and target loader implementation.
- `run-fibonacci-10/`: first direct insmod execution, return 55; metadata was
  recorded after collection. All debugfs captures were copied before unload.
- `run-fibonacci-20/`: CLI execution, return 6765.
- `run-mix/`: CLI replacement with different software, return 0x8c2f3b20.
- `native-tests.txt`: ASan/UBSan transaction fault injection, bounds/clean gates,
  and independent validation of all three live capture sets.
- `legacy-loader-tests.txt`: existing loader regression suite.
- `final-host-state.txt`: final kernel/build/boot identity; the collection
  command also successfully checked module absent and card driverless.

All three runs share one boot ID and each completed 110 commands. Module unload
succeeded each time. `stage-candidate-*` files are uploaded RAM overlays, not
flashable firmware. No flash writes occurred. Historical `exec-flash-*` names
refer to the RAM call gate here. Full-image captures are staging RAM; they do
not replace the physical flash readback evidence in programmed-rom-20261010.

Files are intended for Git along with the rest of the archaeological evidence.
The repository-wide SHA256SUMS and artifact-inventory.json include this folder.
