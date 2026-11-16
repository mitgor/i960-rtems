# PCI configuration-retry release: offline artifacts, 2026-11-17

Produced by [reproduce.sh](reproduce.sh) on the `experiment/accele160-ebcr-release` branch. Context, evidence and limits are in the [experiment document](../../../docs/ACCELE160-EBCR-RELEASE-EXPERIMENT.md). Offline only: no card, PCI device or flash was accessed. **No image here is cleared for flashing.**

## Images

Each 1 MiB image keeps its base card's reset block, descriptor, diagnostics and x86 option ROM bytes; only the selector-2 loader, payload and trailer words differ from stock.

| File | Base stock capture | Stage two | SHA-256 |
| --- | --- | --- | --- |
| `native-passive-pci-release-second-spare.bin` | second spare `0ca0f4b6…` | release, ROM hidden | `9b69e9ca285090bf8159895cedd2947588ef1ea2534683bf4c883ae98c404648` |
| `native-passive-pci-release-first-spare.bin` | first spare `fadd2b0f…` | release, ROM hidden | `9b1f0ce3340b531880e21bbab9760b1c66e3595f105bf22eeae6385a6ca20753` |
| `native-service-pci-release-hidden-rom-second-spare.bin` | second spare | release, ROM hidden | `6b10ffcc0514e293e301a224026f4b060dba4583de658d6f5d56e4769e5aabe7` |
| `native-service-pci-release-second-spare.bin` | second spare | release, ROM kept | `0d90fa59e9fa57734d449d23c16f215448ac70906403fb4eecd8643fed3b3329` |
| `control-passive-no-release-second-spare.bin` | second spare | unchanged 480-byte loader | `bd0c204c5f12b049a78258dc3db1c6a049d458504ff1ed61bfb0c20043f01a97` |

The control image is byte-identical to `native-passive-marker-second-spare.bin` from the 2026-11-16 diagnostic package. Each image has a `*.pack-receipt.json` from `pack.py`. The first-spare image exists because that card already holds a non-booting image and must go through the external programmer anyway. Never write an image to a card other than its base.

`build/` holds the cross-build inputs for each variant (`stage2.bin`, `rtems.bin`, maps, symbols), the build script run inside the container, and its log. Stage two with the release is 1,536 bytes, SHA-256 `e80a068f…d5df` with the ROM hidden and `a2d991fc…0f75` with it kept. The RTEMS payloads are unchanged from the 2026-11-16 builds: passive `5aeb7a4b…08a4`, service `2f31a155…73b9`.

## Receipts

| File | Content |
| --- | --- |
| `stock-pci-reg-writes.json` | Every stock store into the bridge, ATU and messaging-unit blocks, in order, with the state at release. Test fixture for `test_pci_release.py`. |
| `failed-first-spare-pci-reg-writes.json` | The same run for the image that froze the HP Z400: zero stores, retry never released. |
| `config-retry-gate.json` | Interpreter gate: stock reference, two must-hang references, three candidates. `PASS`. |
| `config-retry-gate-first-spare.json` | The same gate for the first-spare image against that card's stock. `PASS`. |
| `config-retry-gate-negative.json` | Non-releasing images offered as candidates. `FAIL`, as intended. |
| `config-retry-post.json` | Coupled QEMU/SeaBIOS run: four images reach the boot sector, four stall on the first configuration read. `PASS`. |
| `regression/` | Existing gates re-run: direct service gate for the old and both new service images, readiness-negative, and the coupled Debian guest run for the new service image with the ROM kept. |
| `unit-tests.txt` | Output of the release and return-kit unit tests. |
| `image-sha256.txt`, `emulator-sha256.txt`, `qemu-build/binary-sha256.txt` | Hashes of the images and of the binaries that produced the receipts. |

Every gate receipt carries `physical_boot_tested: false` and `safe_to_flash: false`.

## Model assumptions behind every receipt

- EBCR resets to `0x000c`: Configuration Cycle Retry set, as in Intel initialization mode 3. The board's RETRY strap has not been measured.
- The interpreter uses the exploratory board selector 11 and modeled zero reset values for registers stock reads before writing.
- The host is SeaBIOS under QEMU with a patched card model, not the HP 786G3 BIOS. A bounded retry count stands in for an indefinite host retry.
- The QEMU card presents a fixed PCI identity; it does not yet take the identity the i960 programmed.

## Scripts

- [reproduce.sh](reproduce.sh) regenerates everything into a new directory; see its header for the environment variables.
- [link-main-checkout-artifacts.sh](link-main-checkout-artifacts.sh) links the saved artifacts that are untracked in the main checkout into this worktree and hides the links from git. The older gates and tests need them.

## The private QEMU binary

The modified `accele160.c` was compiled on its own with the flags from the existing QEMU 6.2.0 build tree's `compile_commands.json`, then linked with that tree's link line with only the object and output paths replaced. The existing tree was read, not written. `qemu-build/link-command.txt` is the exact link command; `qemu-build/binary-sha256.txt` lists the new binary first and the unmodified one second. QEMU looks for firmware next to its binary, so either pass `QEMU_DATA=<existing build>/pc-bios` to the scripts or link that directory beside the new binary. A normal alternative is `install_probe.py` into a separate QEMU 6.2.0 source tree and a full build.
