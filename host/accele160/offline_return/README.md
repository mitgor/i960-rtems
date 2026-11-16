# Read-only return-to-hardware collector

`collect.py` prepares a timestamped directory supplied by the operator. By default it captures host inventory only: boot ID, kernel version, `/sys` PCI IDs/driver/storage state for both AcceleRAID cards and both Intel bridge functions, up to the first 256 bytes of each PCI config space (including current command and expansion-ROM BAR decode bits when readable), each PCI resource table (including the expansion-ROM resource row), `lspci`, `dmesg`, and BIOS version where the host permits. It writes `inventory.json` and `flash-read-plan.json`. It never changes PCI configuration, enables the expansion ROM, binds a driver, maps BAR0, stages an image, or programs flash. An unavailable tool or permission-limited command is recorded in its output file instead of silently treated as evidence.

Run the inventory on the remote **only after** confirming the known booting setup: original card in Slot 5 and stock second spare in Slot 6. Choose a new output path; existing paths are refused:

```sh
python3 host/accele160/offline_return/collect.py --output /path/to/new-capture
python3 host/accele160/offline_return/review_inventory.py \
  --capture /path/to/new-capture --output /path/to/new-capture-review.json
```

The separate review checks four PCI functions, both RAID identities, exposed storage, and the saved config/resource hashes. `PASS` is a clean inventory only; it does not approve READIMAGE or flashing. A missing boot ID, file, or changed identity yields `REVIEW_REQUIRED`. The [operator runbook](RUNBOOK.md) gives the visit order and stopping conditions.

Record the HP F10 `Slot 6 Option ROM Download` setting, both Mylex boot BIOS settings, and SATA RAID option ROM setting separately in a photo or notes. Linux's PCI ROM decode flag does not prove what HP F10 did during POST.

## Optional guarded full-flash reads

This mode is **not** part of the default inventory. It invokes the previously used `read_spare.py` twice, each time using the pinned `rawreader.ko`, fixed selector 9 and one MiB length. The underlying reader checks the module and reviewed driver SHA-256 hashes, original-card unbound state, spare-only `myrsread` binding, `read_bdf`, idle descriptor state, no exposed storage, read status/residual/guard changes, and post-read card selection before releasing DMA. The collector additionally checks the PCI identities and binding before the first read; verifies each `data.bin` against its `result.json` and `status.txt`; requires both hashes to equal the known second-spare stock SHA-256 `0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943`; and records a passing two-read receipt only then.

Execute this only if the same reviewed modules and BDF-limited driver are available on the remote and the stock inventory matches. `read_spare.py` requires its pinned driver module at `/home/mit/i960-dma-refusal-20261019/bundle/inputs/myrsread.ko`; the collector cannot adapt it to a new driver build.

```sh
sudo python3 host/accele160/offline_return/collect.py \
  --output /path/to/new-capture-with-reads \
  --execute-flash-reads \
  --reader-module /path/to/reviewed/rawreader.ko
```

The read path issues READIMAGE to the spare, so it is read-only with respect to flash contents but still changes transient controller/module state. If the underlying reader reports a pending/failed request or changed guard, it deliberately leaves its module and DMA allocation pinned for diagnosis. The collector stops immediately and does **not** attempt automatic unload/retry. Preserve the entire output directory and inspect the state before any next action. No first-spare programmer operation is performed by this script.

Local checks: `python3 -m unittest discover -s host/accele160/offline_return -p 'test_*.py' -q` tests the target and readback gates. A dry run with fake `/sys` confirmed inventory mode creates no flash-read directories. The live optional mode has **not** been executed by this new wrapper.

The collector does not read live MU BAR registers. The existing `mmio_snapshot.c` helper has a read-only mapping mode, but the side effects of each relevant physical register read in this host/driver state have not been established. The runbook records MU capture as a later separately reviewed measurement; PCI config and ROM-resource metadata are available in the default inventory without a BAR access.

The separate [image verifier](verify_recovery_images.py) audits the saved first-spare stock recovery copy, its failed-image programmer read, the second spare's two stock captures, and the current five-reply second-spare candidate. It only reads local files; see the [external-programmer checklist](../../../docs/hardware/ACCELE160-EXTERNAL-PROGRAMMER-RECOVERY.md).
