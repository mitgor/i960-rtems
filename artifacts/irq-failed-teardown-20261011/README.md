# Failed control during teardown — 2026-10-11

Two controlled hardware failures passed: mode 1 omitted STOP while the last
user fd was closed; mode 2 omitted RELEASE while the PCI driver was unbound.
Both tests used the same bounded `mustop` target and Linux test module.
[Implementation and limits](../../rtems/switch/FAILED-TEARDOWN.md).

In each case ioctl and write returned ETIMEDOUT. The transaction remained
pending, both RAM regions dirty, the runner uncertain, and STOP not clean.
DMA/BAR pointers remained present, the experiment was not freed, and the module
reference count stayed 1. There were no firmware submissions after injection.
Ordinary `rmmod` refused to unload the module; retained state was identical one
second later. The unbind case additionally proves retention after the driver
symlink disappears. Both failure captures show ODB=1: completion became visible
but was not consumed after the control error. This is software uncertainty on a
responsive card, not a physical bus timeout or a claim of indefinite CPU hang.

Files:

- `close.tar.xz`, `unbind.tar.xz`: exact target binary/build, generated test
  driver and `.ko`, build/run logs, scripts as deployed, raw preflight/open/
  retained debugfs captures, request identity, input and acceptance JSON.
- `close-verification.txt`, `unbind-verification.txt`: offline hash, ordering,
  retained-state and no-restore checks against those unmodified captures.
- `boot-before.txt`, `boot-between.txt`, `boot-after.txt`: separate boots before
  close, before unbind, and after unbind. Request records match the first two.
- `recovery.tar.xz`, `recovery-verification.txt`: successful pre-test production
  close and final fresh preflight/open captures; paired staging matches pinned ROM.
- `recovery-state.txt`: fresh-boot module/driver and service checks.
- `http-restored.txt`: response from the production IPv6 Vader/system-info page.
- `native-tests.txt`: successful full RTEMS native suite, including 16 rejected
  unsafe retention snapshots and generated no-free-before-retention checks.
- `source.tar.xz`: final switch sources, tests, verifier, transport runner,
  Makefile and current documentation.

The live harness intentionally never calls normal close/restoration after the
injected failure. `retained/` is not successful close evidence. Evidence was
copied locally before each reboot. No forced unload or flash programming was
performed. No visitor statistics or visitor-IP logs are included.

```sh
python3 rtems/switch/verify_failed_teardown.py artifacts/irq-failed-teardown-20261011/close.tar.xz --case close
python3 rtems/switch/verify_failed_teardown.py artifacts/irq-failed-teardown-20261011/unbind.tar.xz --case unbind
```

Exact SHA256 identities, shared by both runs:

```text
3bf5d5e4c0fe0b7ef5af58d25510ad77e3cbfa9f18d2d31a414807e875a2029d  mustop/kernel.bin
73c9d90f466035ecfa7616b0fec67d5a401c851705f491f34f8bf5be8d4f6963  prepared firmware image
48cc1008d72a6309bee324311aec264c08b1b242e89fb15ae88d1580395f406c  failed-teardown-module/dac960rtems.ko
```
