# AcceleRAID 160: PCI configuration-retry release experiment

Branch `experiment/accele160-ebcr-release`, written 2026-11-17. This is a parallel experiment. It lives in its own git worktree and changes nothing in the main checkout. Everything here is offline: no card, PCI device or flash was touched, and no image is cleared for flashing.

## Summary

The first spare, flashed with the native RTEMS image on 2026-10-25, stopped the HP Z400 before its POST beep. The flash contents were later proven byte-exact, and disabling the Slot 6 option ROM did not help. This experiment tests one explanation and builds the fix for it:

- **Hypothesis.** The 80303 on this board starts in Intel initialization mode 3, where the primary PCI interface answers every host configuration cycle with Retry until firmware clears one bit. Stock firmware clears it in its runtime. Every native image so far replaces that runtime and never clears it, so the host BIOS never gets a completed configuration cycle from the card. How the HP firmware reacts to that has not been observed; a freeze before the beep is consistent with it.
- **Result in the offline model.** With retry modeled, the exact image that froze the PC stalls the emulated host on its first configuration read. So do the two 2026-11-16 diagnostic images and the staged second-spare no-ROM image. Stock boots. New images that release retry at stage-two entry boot.
- **Not established.** The board's actual RETRY strap has not been measured. The hypothesis rests on Intel documentation plus stock firmware behaviour, and the model encodes it as an assumption. A physical confirmation is cheap and read-only; see [Physical confirmation](#physical-confirmation-and-next-test).

## Why this explanation

### Intel documentation

| Source | What it says |
| --- | --- |
| 80303 programming guide, order 273395-005, section 2, table 1 and section 2.3 | Mode 3 (`RST_MODE#` = 1, `RETRY` = 1) is the default: the core runs its initialization code while the primary PCI interface retries all configuration cycles. The core must clear the Configuration Cycle Retry bit in EBCR before the host can configure the device. |
| Same guide, section 4, `init_bridge()` | The sample writes EBCR last, with a comment that this lets the host BIOS start its configuration. `EBCR_ADDR` is `0x00001040`. |
| 80303 developer's manual, order 273353-001, table 14-46 | EBCR is at local `0x1040` and at PCI configuration offset `0x40` of the bridge function. Bit 2 is Configuration Cycle Retry, with its default taken from the RETRY pin at the rising edge of `P_RST#`. Bit 0 posting disable, bit 1 core processor reset, bit 3 upstream prefetchable memory enable (default 1), bit 5 reset internal bus, bit 6 secondary DAC medium decode enable. |
| Same manual, bridge initialization list, item 8 | The retry bit is cleared after the bridge registers are set, to let the host configure the bridge. |
| 80303 data sheet, order 273358-009, RETRY pin | If RETRY is high at primary reset, configuration cycles are retried until the bit is cleared in EBCR. |

The documents are on bitsavers under `components/intel/i960/` and `components/intel/i960/80303/`. They are not copied into the repository.

### Stock firmware 6.00-05

Addresses are runtime addresses in the expanded stock image; the disassembly is [stock-runtime-c004d000.dis](../artifacts/current/accele160-timer-interrupt-20261025/stock-runtime-c004d000.dis) in the main checkout.

| Where | What stock does |
| --- | --- |
| `c0051190` | Programs ATU identity: vendor `1069`, device `0050`, subsystem `1069:0054` for board model 32, class code, 8 KiB inbound window, expansion ROM window. It checks the `aa55` ROM signature and writes ERLR = 0 when the signature is missing. |
| `c00513f0` | Programs the secondary ATU. |
| `c0051560` | Programs the PCI-to-PCI bridge registers. |
| `c00516b0` | Scans the secondary bus ("ScanSPCI"). |
| `c0051b44` | Sets interrupt routing PIRSR = `0x0e`, private devices SISR = `0x3ff`, arbitration SACR = `0x1554`. |
| `c0052df4` | Writes EBCR = `0x48`: retry clear, bits 3 and 6 set. |
| `c004e450` | Directly afterwards masks the messaging unit: IISR, IIMR and OIMR = `0xffffffff`, message registers = 0. |
| `c0052e08` | Prints `BIOS Cfg Wait...`, loops until the host has set memory and bus-master enable on the ATU and bus-master enable on the bridge, then prints ` done `. |

The boot block's recovery monitor does the same in miniature: it sets its own IDs, writes EBCR = `0x08`, then prints `BootBlk_Wait4SystemCommand` (`feff0200`). The doorbell bit-3 handlers in both the boot block and the runtime write EBCR = `0x20`, which is the documented Reset Internal Bus bit.

On the normal boot path nothing before the runtime writes any bridge or ATU register. The interpreter trace shows the first such store at instruction 48,716,633, after runtime entry at 48,565,709. The boot block contains an ATU/P2P setup routine at `feffd530` that writes EBCR = `0x14`, but no caller was found and it does not run in the trace.

### The native images

`stage2.c`, `start.S` and `app.c` on main contain no store to `0x1040` or to any ATU identity register. `host_startup.c` only reads the PCI command registers and waits for bits that the host can set only after it has completed configuration cycles.

### Why the emulator never showed it

The i960 interpreter treated `0x1040` as plain memory, and the QEMU device answered every configuration read unconditionally. All earlier gates therefore ran with the host already able to configure the card.

### Cross-check against the real card

The saved live PCI dump of the working original card, [live-readonly-state.txt](../artifacts/current/accele160-startup-20261016/live-readonly-state.txt), holds the ATU function's configuration space. Every ATU value stock wrote in the interpreter trace matches that dump: subsystem `1069:0054`, PIALR `ffffe000`, PIATVR `c0000000`, SIABAR `fe000008`, SIALR `ff000000`, SIATVR `c0000000`, SOMWVR `fc000000`, ERLR `ffff8000`, ERTVR `fef30000`, ATUCR `00000106`, SATUCMD `0016`, PATUIMR and SATUIMR `000000fc`. The one difference is the ATU latency timer: stock writes `0x40` and the dump holds `0x20`, a field the host rewrites. This shows the stock routines above ran on real hardware and that the interpreter reproduces their values.

For the bridge function only the 64-byte header is saved, in [live-pci-identities.txt](../artifacts/current/accele160-qemu-multifunction-20261025/live-pci-identities.txt). It agrees with stock's cache line size `0x10` and with bridge control bit 9 (`0x0202` is stock's `0x0200` plus the host's SERR enable). Offsets `0x34`/`0x36` read `0x68`/`0`, so stock's stores to local `0x1034`/`0x1036` are not visible there; the table copies them anyway. EBCR at offset `0x40` is beyond that header and is not cross-checked.

An older note for the previous DAC960PG card, `docs/firmware/MODE0.md`, read EBCR `0x0018` on a running card and concluded that RETRY is strapped low. A read after boot cannot show the strap, because firmware has cleared the bit by then; that conclusion should not be carried over to this board.

## What this branch adds

### i960 interpreter (`rtems/accele160/emulator`)

| Addition | Purpose |
| --- | --- |
| `--trace-pci-registers` | Logs every store into the bridge (`0x1000`), ATU (`0x1200`) and messaging-unit (`0x1300`) blocks as `checkpoint pci-reg-write`, with instruction count, IP, origin, address, size and value. |
| `--model-config-retry` | Sets EBCR to the assumed mode-3 reset value `0x000c` after reset and reports when bit 2 is first cleared (`checkpoint config-retry released`) and a summary on every exit path. |
| Bridge socket query `Y` | Returns the retry state to the QEMU side: bit 0 modeled, bit 1 released, bits 16–31 current EBCR. |
| [pci_register_trace.py](../rtems/accele160/emulator/pci_register_trace.py) | Runs an image, saves the write list as JSON, and computes the register state at the moment of release. |
| [config_retry_gate.py](../rtems/accele160/emulator/config_retry_gate.py) | The offline gate described below. |

Both flags are opt-in. Without them the interpreter output is unchanged, and the existing direct service gate and readiness-negative test pass unmodified.

### QEMU card model (`rtems/accele160/emulator/qemu`)

`accele160.c` gains `model-config-retry=on` and `config-retry-limit=N`. While the i960 has not released retry, each host configuration access to either function advances the i960 by one million instructions and asks again. A host bridge that keeps re-issuing a retried cycle never completes it; here `N` attempts stand in for that, after which QEMU prints a `config-retry STALL` line and exits with status 66. [test_config_retry_post.py](../rtems/accele160/emulator/qemu/test_config_retry_post.py) boots SeaBIOS to a marker boot sector under this model.

The modified model needs its own QEMU binary. This run compiled only `accele160.c` and relinked against the objects of the existing QEMU 6.2.0 build tree, writing the result outside that tree; the exact link command is saved in the artifact directory.

### Native firmware (`rtems/accele160/native_rom`)

| File | Content |
| --- | --- |
| [pci_release.h](../rtems/accele160/native_rom/pci_release.h), [pci_release.c](../rtems/accele160/native_rom/pci_release.c) | `accele160_pci_release()`: a 56-entry table copied in order from the stock trace, ending with EBCR = `0x48`. It issues 55 stores with the option ROM hidden and 56 with it kept. |
| [stage2.c](../rtems/accele160/native_rom/stage2.c) | Calls the release as the first action after the `SGT2` marker when built with `ACCELE160_PCI_RELEASE`. |
| [build.sh](../rtems/accele160/native_rom/build.sh) | `ACCELE160_PCI_RELEASE=1` enables it; `ACCELE160_PCI_HIDE_OPTION_ROM=1` additionally writes ERLR = 0. |
| [observe.py](../rtems/accele160/native_rom/observe.py) | Decodes the new `PCI0` record through the host BAR after a boot. |
| [test_pci_release.py](../rtems/accele160/native_rom/test_pci_release.py) | Host unit tests against the stock trace. |

**Why stage two and not the stock-equivalent point in RTEMS.** Stage two is the first native code after the stock reset block. Releasing there means a bad payload digest, an RTEMS fault or a park can no longer hold the host in retry: the PC boots and the DRAM markers stay readable through the BAR. In the interpreter the release happens at instruction 1,355,953, against 49,602,106 for stock. The stage-two binary grows from 480 to 1,536 bytes; the loader window is 24 KiB.

**The `PCI0` record** is eight words at local `0xc0001ee0`, BAR offset `0x1ee0`: marker, EBCR before any write, EBCR after, flags (bit 0 ROM hidden, bit 1 ROM signature seen), ATU vendor/device readback, ATU subsystem readback, bridge command before, store count. `ebcr_before` will be the first physical observation of the board's reset strap.

**Differences from the stock sequence**, all deliberate:

| Difference | Reason |
| --- | --- |
| The secondary-bus scan is not run. In the trace it is 16 SOCCAR selects; with the interpreter's QLogic model enabled stock also sets the QLogic BAR to `fff00000` and its command register to `0116` through SOCCAR/SOCCDR. | The diagnostic does not use SCSI. PIRSR, SISR and SACR are still set to the stock values for this board, and the compared register state at release is the same with or without the QLogic model. |
| The seven messaging-unit stores run before the EBCR write, not after. | The release is then the last store, and the host never sees unmasked outbound interrupts. |
| SISR is written as an aligned 16-bit store. | Stock uses an unaligned 32-bit store at `0x1042`. Its upper half lands on PBISR, which is write-one-to-clear, so the zeros written there do nothing. |
| SDER is `0xfffe`, not stock's `0x0004`. | Stock's value sets Private Memory Space Enable and clears every bridge error interrupt mask (developer's manual, table 14-55). An error such as a master abort on the secondary bus then raises an NMI, which stock services. The native image installs no NMI handler, so the masks stay set; bit 2 is kept. The saved stock bridge header shows secondary status `0x2280`, Received Master Abort set, so such events do occur on this board. |
| ERLR = 0 when `ACCELE160_PCI_HIDE_OPTION_ROM` is set. | This is stock's own no-ROM path. The host then never runs the Mylex x86 ROM, which polls a controller that the passive image does not emulate. |
| Board-model-dependent values are constants. | The routine is for board model 32, subsystem `0x0054`, only. |
| BIUCR (`0x1640`) is not written. | Stock sets it to 3 just before the ATU routine (`c0051170`). Per the developer's manual, table 12-8, the two bits enable instruction prefetch and write merging; they do not affect what the host sees. |

## Results

All from [artifacts/current/accele160-pci-release-20261117](../artifacts/current/accele160-pci-release-20261117/README.md), produced by one script.

**Register trace.** Stock makes 65 bridge/ATU stores and releases at IP `c0052e00` with EBCR `0x0048`; seven messaging-unit stores follow. The failed first-spare image makes zero stores and ends with EBCR `0x000c`.

**Offline gate, interpreter only** ([config-retry-gate.json](../artifacts/current/accele160-pci-release-20261117/config-retry-gate.json)):

| Image | Retry released | Register state at release |
| --- | --- | --- |
| Second spare stock | yes, instruction 49,602,106 | reference |
| First-spare image that froze the HP Z400 | never | — |
| Passive diagnostic rebuilt without the flag | never | — |
| Passive diagnostic with release, ROM hidden | yes, instruction 1,355,953 | equals stock except SDER and ERLR/ERTVR |
| Service diagnostic with release, ROM hidden | yes, instruction 1,355,953 | equals stock except SDER and ERLR/ERTVR |
| Service diagnostic with release, ROM kept | yes, instruction 1,355,967 | equals stock except SDER |

The gate also checks that the release IP is inside stage two, that no bridge/ATU store follows it, that no store before it goes to a register stock never writes, that the messaging-unit masks equal stock's, that the `PCI0` record is complete, and that the RTEMS diagnostic still reaches `PASS`. A must-hang reference counts only if it reaches `PASS` without releasing. Offering the non-releasing images as candidates makes the gate fail, as intended.

The gate's window is 4,000,000 instructions with no host activity. Code that runs only after a host event is outside it, so a later re-assertion of retry or rewrite of ATU registers from such a handler would not be seen. The current images contain no such code.

**Host-side reproduction, interpreter coupled to QEMU/SeaBIOS** ([config-retry-post.json](../artifacts/current/accele160-pci-release-20261117/config-retry-post.json)), option ROM omitted in every run:

| Image | Host outcome |
| --- | --- |
| Second spare stock | retry released after 50 retried attempts; boot sector reached |
| Three release candidates | released after 2 attempts; boot sector reached |
| First-spare image that froze the HP Z400 | stall on the first configuration read of the bridge function; no configuration access completes |
| Passive diagnostic without the flag | stall |
| `native-service-marker-second-spare.bin` from 2026-11-16 | stall |
| `native-rom-second-spare-no-x86-rom.bin`, staged 2026-10-26 | stall |

**Counterfactual and fault gates.** With the model's RETRY strap set low,
EBCR starts at `0x0008`; the failed first-spare image and a no-release control
both let SeaBIOS reach the boot sector, with no firmware release write. This
shows the modeled stall depends on the unmeasured strap, rather than proving
the strap's physical state. Separately, changing only the stored RTEMS payload
digest in a temporary copy of the first-spare candidate makes stage two report
`0x1003`; early PCI release still lets the modeled host reach the boot sector.
The receipts are [low-strap](../artifacts/current/accele160-pci-release-20261117/config-retry-low-strap.json)
and [payload-fault](../artifacts/current/accele160-pci-release-20261117/config-retry-payload-fault.json).

Intel's [80303 initialization guide](https://www.bitsavers.org/components/intel/i960/80303/273395-005_80303_IO_Processor_Prog_Guide_and_Initialization_200104.pdf),
section 4.4, initializes the ATUs before the bridge and writes EBCR last to
allow host BIOS configuration. Its address definitions match the bridge-block
offsets used here, including EBCR `0x1040`, SISR `0x1042`, and SDER `0x105c`.
The guide does not validate the Mylex-specific values or the native routine's
earlier timing; those remain based on the stock trace and are not hardware
qualified.

**Regression.**

- The control build without the new flag is byte-identical to the existing `native-passive-marker-second-spare.bin`, SHA-256 `bd0c204c…01a97`; its stage two is the unchanged 480-byte `08d9866a…b0af`.
- The cross-built RTEMS payloads match the saved `passive-build-v1` and `service-build-v1` payloads exactly.
- The existing direct service gate gives the same result for the old service image and both new service images.
- The readiness-negative test passes on the new service image.
- The new service image with the ROM kept passes the existing coupled Debian guest gate with the same six ROM IOCTLs.
- The same guest gate with the retry model on and the host started after only 1,000 i960 instructions: the new service image releases after two retried attempts and passes; the 2026-11-16 service image stalls on the first configuration read.
- The 28 native-ROM tests and 5 return-kit tests pass.

One pre-existing problem was seen and left alone: `candidate_scheduler_gate.py` fails in the main checkout as well, because it expects a 9-word report line and the interpreter now prints 16 words.

## Images

Built from each card's own stock capture. None is tested on hardware; every pack receipt says `safe_to_flash: false`.

| Image | Base | SHA-256 |
| --- | --- | --- |
| `native-passive-pci-release-second-spare.bin` | second spare stock `0ca0f4b6…` | `a29ed071522e8f34b6e0d6d18b8e7c5a57d9f1ae149a60bedc1aad0d2b02d8b3` |
| `native-passive-pci-release-first-spare.bin` | first spare stock `fadd2b0f…` | `842dc04f866fb949a8531f8517eb2109c08aebbedbc19996e33e66a09fd79e17` |
| `native-service-pci-release-hidden-rom-second-spare.bin` | second spare stock | `07ba2e2d5223919c554439b87dc66ef4a5984a2e905196ba0b831b72e88e2057` |
| `native-service-pci-release-second-spare.bin` | second spare stock | `8edb06a4f3099c5213d26b0e3395250ca6818e44abe2abf62b968fe89ed0da17` |
| `control-passive-no-release-second-spare.bin` | second spare stock | `bd0c204c5f12b049a78258dc3db1c6a049d458504ff1ed61bfb0c20043f01a97` |

Passive images use `ACCELE160_EARLY_ENTRY_MARKER`, `ACCELE160_OBSERVE_HOST_EVENTS` and `ACCELE160_READ_ROM_MAILBOX`. Service images use the full flag list from `service-flags.env` of the 2026-11-16 package.

## Reproduce

From the root of this worktree:

```sh
sh artifacts/current/accele160-pci-release-20261117/link-main-checkout-artifacts.sh /path/to/main/checkout
QEMU=/path/to/qemu-system-x86_64-built-with-this-accele160.c \
BIOS=artifacts/current/accele160-bcv-gate-20261025/bios.bin \
FIRST_SPARE_STOCK=artifacts/current/accele160-spare-rom-20261025/rawflash-0/data.bin \
sh artifacts/current/accele160-pci-release-20261117/reproduce.sh /path/to/new/output
```

The first command links the saved artifacts that are untracked in the main checkout into this worktree; nothing is copied or committed. It hides the links through a self-ignoring `artifacts/current/.gitignore` that stays local to the worktree. The shared `.git/info/exclude` must not be used for this, because it would hide the same directories in the main checkout. Without `QEMU` and `BIOS` the script skips the coupled runs. The cross-build needs Docker with a linux/amd64 image that has bash and python3, and the archived toolchain cache described in the 2026-11-15 offline build record. The [artifact README](../artifacts/current/accele160-pci-release-20261117/README.md) lists what each step writes and how the private QEMU binary was built.

## How this relates to the main checkout

Much of the AcceleRAID native work is untracked on main. The branch therefore starts with one commit that copies those files unmodified, so the experiment can be read as a diff:

| Commit | Content |
| --- | --- |
| `a17db352` | Unmodified copy of `rtems/accele160/native_rom`, `rtems/accele160/emulator` (without `build/`), `host/accele160/offline_return`, the untracked `docs/ACCELE160-*.md` and `docs/hardware/ACCELE160-*.md`, and three saved inputs. |
| later commits | The experiment. |

To see exactly what the experiment changed:

```sh
git diff a17db352 experiment/accele160-ebcr-release --stat
```

To carry the source changes into the main checkout as uncommitted edits:

```sh
git diff a17db352 experiment/accele160-ebcr-release -- rtems host docs | git apply --3way
```

Files on main that changed after the snapshot will need a manual merge. The emulator and build changes are opt-in flags, so applying them does not alter existing gate results.

## Physical confirmation and next test

Ordered from cheapest. Steps 1 and 2 are read-only.

1. **Read EBCR on a stock card.** On the booted PC with the stock second spare in Slot 6:

   ```sh
   sudo setpci -s 37:04.0 40.w
   ```

   The expected value is `0048`, possibly with pin-dependent bits 8–11 set. This confirms that the register is where the analysis says and holds stock's value. It cannot show the reset strap, because retry must already be clear for Linux to see the card. The return kit now decodes this from its bridge-function capture when the collector runs as root; see the [runbook](../host/accele160/offline_return/RUNBOOK.md).
2. **Optional: POST-code card.** With the failed first spare installed, a port-80 display separates a stall in PCI enumeration from a stall in an option ROM. It needs no change to any card.
3. **Use the first spare for the retest.** It already holds a non-booting image and has to go through the external programmer in any case. Writing `native-passive-pci-release-first-spare.bin` to its chip tests the hypothesis in one programming cycle and leaves the stock second spare untouched. The stock recovery image `restore-first-spare-stock-1MiB.bin` stays the fallback. This is a separate decision; the existing decision gate in the POST failure audit still applies.
4. **Before that cold boot:** keep `myrs` blacklisted so Linux does not probe a card that enumerates as `1069:0050` but answers no commands. The HP Slot 6 option-ROM setting no longer matters for an image that hides the ROM, but record it.
5. **Expected if the hypothesis is right:** the PC beeps and boots; `lspci` shows `1069:0050` subsystem `1069:0054`; `observe.py --bdf <BDF>` reports stage two entered, RTEMS `PASS` and a `pci_release` record whose `ebcr_before` has bit 2 set.
6. **If the PC still stops before the beep,** the hypothesis is wrong or incomplete. Restore the first spare's stock image and record the POST code.

## Limits and open questions

- **The strap is inferred.** No measurement shows EBCR bit 2 set at reset on this board. If the board straps RETRY low, this experiment explains nothing, although the release code would still be harmless. `ebcr_before` in the `PCI0` record settles it at the first successful boot.
- **Bridge-block values are mostly unverified on hardware.** They come from the interpreter trace with the hypothetical board selector 11. The ATU values agree with a live dump; for the bridge function only the first 64 bytes are saved. Stock reaches its release in the model only with selector 11, so no other selector offers a competing set of values.
- **No NMI or fault handler.** The image masks the bridge and ATU error interrupts, but an NMI from another source would run whatever the boot block's interrupt table holds. The host would still boot; the diagnostic could stop updating its markers.
- **Stores wider than four bytes are not traced.** The interpreter flags one into the traced blocks and the trace tool then refuses the run. The current code has none.
- **Read-modify-write registers.** Stock derives a few values from registers it reads. The trace records what it wrote with modeled zero reset values. The bridge command register is handled as save/restore, as in stock.
- **SeaBIOS is not the HP BIOS.** The stall in the coupled run is the model's own bounded-retry exit, not an observed BIOS behaviour. It shows what follows if the host never gets a completed configuration cycle. It does not show how HP firmware 786G3 v03.15 behaves, and the QEMU device still presents a fixed PCI identity rather than the values the i960 programmed.
- **Early release changes timing.** The host can now configure the card and set its command bits before RTEMS starts. The passive image only observes this. Later service work should check that nothing depends on the old ordering.
- **No secondary-bus setup.** SATUCMD is enabled with the stock value while the QLogic chip is left unconfigured, which is the state stock passes through just before its scan. A long-lived image should either complete the scan or justify leaving it.
- **A second failure may hide behind this one.** Releasing retry makes the next failure observable rather than guaranteeing a boot. With the ROM kept, the HP BIOS would run the Mylex option ROM against the native service handlers, which is validated only in QEMU.

## Changed and added files

```
docs/ACCELE160-EBCR-RELEASE-EXPERIMENT.md            this document
docs/ACCELE160-OFFLINE-WORKPLAN.md                   pointer to this experiment
docs/hardware/ACCELE160-POST-FAILURE-AUDIT.md        new hypothesis row and discriminator
docs/hardware/ACCELE160-EMULATOR-ASSUMPTIONS.md      new ledger row
host/accele160/offline_return/review_inventory.py    EBCR decode
host/accele160/offline_return/test_collect.py        tests for it
host/accele160/offline_return/RUNBOOK.md             EBCR section
rtems/accele160/emulator/board_memory.h              retry model API
rtems/accele160/emulator/runner.cc                   flags, summary, bridge query Y
rtems/accele160/emulator/third_party/sim5/src/NativeCore.cc   trace and EBCR hooks
rtems/accele160/emulator/pci_register_trace.py       new
rtems/accele160/emulator/config_retry_gate.py        new
rtems/accele160/emulator/README.md                   new section
rtems/accele160/emulator/qemu/accele160.c            host-side retry model
rtems/accele160/emulator/qemu/test_config_retry_post.py   new
rtems/accele160/emulator/qemu/run_pci_rom.py, test_native_card.py   opt-in retry-model switch
rtems/accele160/native_rom/pci_release.c, pci_release.h   new
rtems/accele160/native_rom/stage2.c, build.sh        opt-in release
rtems/accele160/native_rom/observe.py, test_observe.py    PCI0 record
rtems/accele160/native_rom/test_pci_release.py, test_pci_release_driver.c   new
rtems/accele160/native_rom/README.md                 new section
artifacts/current/accele160-pci-release-20261117/    images, receipts, scripts
```
