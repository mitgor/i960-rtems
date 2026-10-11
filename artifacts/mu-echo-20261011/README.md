# Masked MU echo — 2026-10-11

A single tagged word passed from Linux through IMR1 to the timer ISR and back
through OMR1. The successful retry took **11.023913 ms**. Firmware session
sequence stayed **1 → 1**: one initial STEP armed the timer, then the echo used
only the driver's MMIO ioctl. Normal firmware STOP was still required afterward.

The successful run verified timer/vector/mask restoration, full borrowed RAM
restoration, module unload, zero IMR1/OMR1, unchanged IIMR/OIMR, and restored
message-1 pending bits. No flash writes or recovery testing occurred.

## Captures

- `success.tar.xz`: exact target image/ELF/build, pinned Linux module and generated
  source, `mu-echo2` raw frames/snapshots/acceptance/restoration, source snapshot.
- `success.log`, `build-success.log`: complete retry output and build log.
- `failed-first.tar.xz`: original build/module/source and `mu-echo1` captures.
- `failed-first.log`, `build-first.log`: first attempt output/build.
- `native-tests.txt`, `offline-tests.log`: simulated register tests and repository
  RTEMS offline suite. These are separate from live hardware evidence.

The first echo succeeded in 6.156639 ms, but cleanup failed: the target attempted
an OISR write locally. Intel 80960RP manual 272736-002 §17.7.9/table 17-13 makes
OISR read-only from the local side; the PCI host must acknowledge it. The native
mock initially modeled this incorrectly. The target restored the message words
but OISR bit 1 remained set. STOP reported error 2; RAM/module were retained
rather than forcibly released. An authorized host reboot cleared the session.
The corrected test models local OISR writes as ignored. The corrected target
clears IISR, returns an ownership marker after stopping, and Linux clears only
OISR bit 1 after validating STOP, zero words and the expected masks.

The production `autonet` image/module were preserved. The original Vader HTTP
and visitor-statistics service was restarted after the successful retry.

## Scope

This proves bounded one-word transport on this card in an exclusively owned
experiment. It does not prove permanent firmware ownership, framed CTL1 traffic,
independent STOP, runaway-task interruption or unrestricted RTEMS preemption.
Next: implement a bounded framed adapter over the two message words with
sequence/epoch checks and an independent STOP handshake, first in simulation.
