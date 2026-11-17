# AcceleRAID 160 remote return: read-only baseline

Prepared offline 2026-11-16. This is the first visit after the first spare's native image stopped the HP Z400 before its beep. The known booting setup is the original AcceleRAID 160 in Slot 5 and the **unmodified second spare** in Slot 6. The first, failed spare stays out of the PC. This runbook collects evidence; it does not bind a driver, enable an expansion ROM, write PCI configuration, issue a controller command in its default path, or program flash.

## 1. Before remote commands

Confirm and photograph the card labels and slots. Record whether the PC beeps and boots, HP BIOS version, `Slot 6 Option ROM Download`, both Mylex boot BIOS settings, and `SATA RAID Option ROM Download`. Keep the settings unchanged during this baseline. Stop if the installed cards or boot behavior differ from the known setup. The expected Linux functions are second spare RAID `0000:37:04.1` and original RAID `0000:37:09.1`; both previously identified as `1069:0050`, subsystem `1069:0054`.

## 2. Inventory only

From the project root on the remote host, choose a **new** output directory:

```sh
python3 host/accele160/offline_return/collect.py \
  --output /path/to/new-accele160-stock-baseline
python3 host/accele160/offline_return/review_inventory.py \
  --capture /path/to/new-accele160-stock-baseline \
  --output /path/to/new-accele160-stock-baseline-review.json
```

Save both directories/files and the BIOS/card photos together. The collector records PCI identities, driver and storage state, up to 256 bytes of config per function, resource tables and ROM BAR metadata, `lspci`, `dmesg`, boot ID and BIOS version where readable. It does **not** enable or read the expansion ROM, or touch BAR0. The review's `PASS` means those captured files are internally consistent, full `lspci` succeeded, and the two RAID identities match; it does not prove the HP executed or skipped an option ROM during POST, and it does not authorize READIMAGE. If the review says `REVIEW_REQUIRED`, inspect its findings before any further measurement.

## 2a. EBCR on the stock bridge function (read-only)

Added 2026-11-17 by the [configuration-retry experiment](../../../docs/ACCELE160-EBCR-RELEASE-EXPERIMENT.md). The 80303's Extended Bridge Control Register is at PCI configuration offset `0x40` of the bridge function. Its bit 2, Configuration Cycle Retry, makes the card answer every host configuration cycle with Retry until firmware clears it. Stock firmware writes `0x48` there; the native image that stopped the PC never wrote it.

Run the collector as **root** so the bridge-function captures reach offset `0x40`; a non-root sysfs read stops at 64 bytes. `review_inventory.py` then reports an `ebcr` entry for `0000:37:04.0` and `0000:37:09.0` and sets `ebcr_measured_on_both_bridges`. The expected raw value is `0x0048`, possibly with the pin-dependent bits 8–11 set. A manual equivalent is:

```sh
sudo setpci -s 37:04.0 40.w
sudo setpci -s 37:09.0 40.w
```

Both are configuration-space reads and change nothing. On a running stock card bit 2 is necessarily clear, since Linux could not otherwise have enumerated it; the review flags a set bit as a contradiction of the register model. This measurement confirms the register location and stock's value. It does not show the reset strap, which only a native image's `PCI0` record or a bus trace can.

## 3. Optional two guarded stock reads

This is a separate operation after the inventory. Run it only if the previously reviewed `myrsread.ko` is already bound solely to the Slot 6 spare, `read_bdf=0000:37:04.1`, the original is unbound, neither card exposes storage, and the exact pinned `rawreader.ko` is available. The wrapper and underlying reader check identities, module hashes, selector 9, 1 MiB length, idle descriptor, status/residual/guard changes, peer selection and DMA release. They do not bind a driver for you.

```sh
sudo python3 host/accele160/offline_return/collect.py \
  --output /path/to/new-accele160-stock-reads \
  --execute-flash-reads \
  --reader-module /path/to/reviewed/rawreader.ko
```

The two full reads must independently match second-spare stock SHA-256 `0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943` and produce `flash-read-verification.json` with `gate=PASS`. READIMAGE is a controller command despite leaving flash contents unchanged. On an unexpected card/driver identity, storage device, module hash, nonzero status/residual/guard changes, pending request, hash mismatch, or absent verification receipt, **stop and preserve the full capture**. The reader intentionally leaves a pending/failed DMA allocation pinned for diagnosis; do not unload or retry it automatically.

## 4. Separate physical discriminator

The first failed spare's chip should be read twice with the external programmer while the card is out of the PC and unpowered. Save both 1 MiB dumps, chip marking/orientation, programmer voltage/model, and hashes. The expected failed-image SHA-256 is `6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd`. This repeat can check programmer read stability; it does not by itself identify the pre-beep cause. The [programmer recovery guide](../../../docs/hardware/ACCELE160-EXTERNAL-PROGRAMMER-RECOVERY.md) keeps the first spare's own stock recovery image separate from the second spare's image.

The default collector deliberately does not read live MU registers. A previously used `mmio_snapshot.c` helper can map BAR0 read-only, but the read side effects of the specific physical MU registers in this host and driver state have not been established. PCI configuration and ROM resource state are captured now; MU/POST bus measurements require a separately reviewed, narrow plan or suitable passive instrumentation. A Linux expansion-ROM decode flag is not evidence that HP executed the ROM during POST.

The first decision after this visit is whether the stock baseline and repeat reads match. If they do, the unresolved physical question remains where the failed image diverges during HP POST or i960 startup. Do not infer that the offline QEMU/Linux gate predicts a cold boot, and do not flash a spare as part of this runbook.
