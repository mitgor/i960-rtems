# AcceleRAID 160 RTEMS native-ROM prototype

This directory starts the native firmware path. It does **not** initialize the
80303 from reset yet: the original 64 KiB Mylex reset block still brings up
DRAM and PCI, finds selector 2, checks its trailer and loader checksum, copies
the 24 KiB loader to `0xc000a000`, and calls it. The replacement stage-two
loader copies a raw RTEMS diagnostic from flash to `0xc0010000`, checks FNV-1a,
and returns to the reset block. The reset block then branches to the RTEMS
entry in the modified trailer. The stock RAID application is never entered.
The accepted reset-block disassembly at `0xfeffcbb0..0xfeffcbd0` confirms
that it loads the stage-two entry from trailer word 1, passes the flash source
and DRAM destination in `g0/g1`, calls the loader, then returns trailer word 2
as the final runtime entry. This confirms the register handoff; it does not
prove the replacement image boots on hardware.

The first RTEMS payload deliberately does little: it switches to its own entry
stack, clears BSS, starts the RTEMS executive, schedules one worker for 64
iterations, and publishes a pass/fail record in the existing inbound RAM
aperture at `0xc0001f00`. It does not use DMA, SCSI, a UART, or a timer. Its
software-yield test is a first scheduler milestone, not the current Doom,
networking, or console runtime.

## Image layout and status

The offline packer accepts only the two SHA-pinned complete stock 1 MiB images
captured from the original card and the installed spare. It
preserves `0x00000..0x3ffff` (including the x86 option ROM) and
`0xc0000..0xfffff` (diagnostics, descriptor, reset block). In selector 2 it
replaces `0x41000..0x46fff` with the stage-two loader and puts a 16-byte
`RNT1` header followed by raw RTEMS bytes at `0x47000`. It updates only the
loader entry, RTEMS entry, loader checksum, and trailer checksum words in the
existing trailer. The old ZIP1 compressed stock application is removed.

The card-side report words, if the host PCI BAR is available, are:

| Local address | Meaning |
| --- | --- |
| `0xc0001f00` | stage-two entry marker `SGT2` |
| `0xc0001f04` | stage-two result `0x2000`, or error `0x1001..0x1003` |
| `0xc0001f08` | copied length, or computed FNV on digest failure |
| `0xc0001f0c` | expected/matching FNV |
| `0xc0001f10..1f18` | RTEMS worker count, Init yield count, done flag |
| `0xc0001f1c` | `PASS` / `FAIL` after scheduling |
| `0xc0001f20` | park/fatal code |
| `0xc0001f24` | `HST0` read-only host-startup sample marker |
| `0xc0001f28..1f38` | bridge PCI command, RAID PCI command, inbound doorbell, inbound status, inbound mask |
| `0xc0001f3c` | readiness flags: bit 0 bridge command bit 2, bit 1 RAID command bits 1–2, bit 2 boot doorbell bit 1 |
| `0xc0001f40` | opt-in `HST1` sequence: odd during an update, even when stable |
| `0xc0001f44..1f48` | opt-in inbound MU message 0/1, the posted mailbox pointer |
| `0xc0001f4c` | opt-in `HST1` marker |
| `0xc0001f50` | opt-in `MBX0` diagnostic ingress marker |
| `0xc0001f54..1f60` | ingress state, parsed command ID, output bus address, request FNV-1a |
| `0xc0001f64` | opt-in `RPL0` marker for local controller-info composition |
| `0xc0001f68..1f6c` | local reply state and FNV-1a; no host transfer is implied |
| `0xc0001f70..1f74` | opt-in `DMA1` marker and bounded emulator transfer/completion state |
| `0xc0001f78..1f80` | opt-in `REQ2`/`REQ3` marker, completed request count, last IOCTL |

These words have not been read from a cold-booted card. The current stock
firmware's host aperture is known; availability during this altered startup
must be proven rather than assumed.

The new `host_startup.c` observer reads only registers `0x1004`, `0x1204`,
`0x1320`, `0x1324`, and `0x1328`. It records a snapshot before RTEMS starts
and another at the scheduler result. The readiness bits describe the exact
conditions the stock firmware checks in the offline replay; they do not
perform initialization or answer a host mailbox. The observed MU status bit
`0x4` is deliberately separate from boot doorbell bit `0x2`.
An opt-in `ACCELE160_OBSERVE_HOST_EVENTS=1` build continues sampling after
RTEMS `PASS` instead of immediately parking. Its [offline QEMU result](../../../artifacts/current/accele160-offline-monitor-20261115/README.md)
captures the host PCI commands, ACK doorbell, and first mailbox status from
native i960 code. The normal build still parks. This monitor performs no
register writes or host DMA and is not a flash candidate.
The [second offline monitor](../../../artifacts/current/accele160-offline-monitor-v2-20261115/README.md)
adds the `HST1` sequence and mailbox pointer. `observe.py` accepts the older
nine- and sixteen-word formats and rejects an odd sequence in the newer
twenty- and twenty-five-word formats. Its two host reads must also match
before a record is accepted. The [opt-in ROM mailbox ingestion
image](../../../artifacts/current/accele160-offline-ingress-20261116/README.md)
adds a five-word `MBX0` report and reads only the exact offline ROM fixture
address. It parses the first host request without DMA output or completion.
The separate `ACCELE160_COMPOSE_CTLR_INFO=1` offline variant also reads its
own flash descriptor and product string, composes the observed 512-byte
reply in local RAM, and publishes `RPL0`. Its [bytewise emulator
gate](../../../artifacts/current/accele160-offline-reply-model-20261116/README.md)
passes, but it still does not issue DMA or complete the mailbox.
The further `ACCELE160_EMULATOR_DMA1_REPLY=1` build uses the captured
one-descriptor DMA1 shape and MU completion values. Its
[offline gate](../../../artifacts/current/accele160-offline-dma1-20261116/README.md)
checks all 512 output bytes and rejects malformed or out-of-scope requests.
The [simultaneous native/QEMU gate](../../../artifacts/current/accele160-native-qemu-handoff-20261116/README.md)
passed for the first request and showed the ROM submitting IOCTL `0x11`
next.
The further [two-reply image](../../../artifacts/current/accele160-native-ioctl11-20261116/README.md)
answers the captured `0x11` request with a 128-byte stock-replay fixture.
Its simultaneous QEMU gate shows the ROM advancing to `0x15`; the remaining
requests and physical startup are still untested.
The [three-reply image](../../../artifacts/current/accele160-native-ioctl15-20261116/README.md)
adds the captured 64-byte `0x15` reply. Its QEMU gate reaches the next
request, `0xd0`. The reply fields are repeatable under the saved synthetic
stock replay schedule, but remain unverified on hardware.
The [four-reply image](../../../artifacts/current/accele160-native-ioctld0-20261116/README.md)
adds `0xd0`; the coupled QEMU gate then reaches `0x2d`. The
[five-reply image](../../../artifacts/current/accele160-native-ioctl2d-20261116/README.md)
returns the first 512 bytes of its own XLYM descriptor for `0x2d`. Direct
emulator gates pass for valid and malformed fifth requests. Physical startup
remains untested, and this image is not cleared for flashing.

## Later offline mailbox and ring milestones

The [second ten-step batch](../../../docs/ACCELE160-NEXT-TEN-OFFLINE-STEPS-2.md) added opt-in native `SET_MEM_MBOX` (`0x8e`) setup, then memory-ring replies for controller info, health, and the first physical-device information request. The [first-ring gate](../../../artifacts/current/accele160-native-ring-offline-gate-20261116/README.md), [stock follow-up repeat](../../../artifacts/current/accele160-stock-followup-pair-20261116/receipt.json), and [strict native guest mirror trio](../../../artifacts/current/accele160-native-followup-mirror-pair-20261116/receipt.json) passed in the exploratory emulator/QEMU model. The guest registered a SCSI host and submitted two [further ring commands](../../../artifacts/current/accele160-native-next-boundary-20261116/README.md); `myrs` probe did not finish. The third batch is tracked in its [offline plan](../../../docs/ACCELE160-NEXT-TEN-OFFLINE-STEPS-3.md).

Each new handler is behind a separate build feature gate and packed against the second spare's own 1 MiB stock dump. The guest mirror copies only an observed native model reply after strict slot, DMA, status, doorbell and payload checks. None of these gates establish physical 80303 DMA, HP POST, or cold-boot behavior. The first spare's pre-beep failure remains unexplained; no current image is cleared for flashing.

## Host PCI identity and configuration-retry release (experiment, 2026-11-17)

The images described above never clear the 80303 Configuration Cycle Retry bit, EBCR local `0x1040` bit 2. If the board straps RETRY high, as Intel's default mode 3 and stock firmware's behaviour indicate, the host cannot complete a configuration cycle to such an image. Background and evidence: [experiment document](../../../docs/ACCELE160-EBCR-RELEASE-EXPERIMENT.md).

`ACCELE160_PCI_RELEASE=1` makes stage two call `accele160_pci_release()` from [pci_release.c](pci_release.c) immediately after the `SGT2` marker. It replays the stock runtime's ATU, bridge, interrupt-routing and messaging-unit stores for board model 32 and ends with EBCR = `0x48`. `ACCELE160_PCI_HIDE_OPTION_ROM=1` additionally writes ERLR = 0, stock's own no-ROM path, so the host does not run the x86 option ROM. Both are off by default; without them stage two is the unchanged 480-byte binary.

The routine writes an eight-word `PCI0` record at local `0xc0001ee0`, BAR offset `0x1ee0`:

| Word | Meaning |
| --- | --- |
| 0 | `PCI0` marker, written last |
| 1 | EBCR before any store: the board's reset value |
| 2 | EBCR readback after the release |
| 3 | bit 0 option ROM hidden, bit 1 `aa55` signature present |
| 4 | readback of `0x1200`: device and vendor ID |
| 5 | readback of `0x122c`: subsystem IDs |
| 6 | bridge command register before the sequence |
| 7 | number of register stores issued |

`observe.py` decodes it as `pci_release`. `test_pci_release.py` builds the routine for the host and checks it store for store against the saved stock trace; `emulator/config_retry_gate.py` checks a packed image in the interpreter. Offline results and images are in [the artifact directory](../../../artifacts/current/accele160-pci-release-20261117/README.md). Not tested on hardware.

## Build and verification

On the i960 build host, using a separate directory:

```sh
bash rtems/accele160/native_rom/build.sh \
  /home/mit/i960-rtems-20261011/bounded \
  /home/mit/i960/tools/bin \
  /home/mit/i960-native-rom-20261020/build
```

Then on the project machine:

```sh
python3 rtems/accele160/native_rom/pack.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin \
  artifacts/current/accele160-native-rom-20261020/build/stage2.bin \
  artifacts/current/accele160-native-rom-20261020/build/rtems.bin \
  /path/to/new-offline-prototype.bin
python3 -m unittest discover -s rtems/accele160/native_rom -p 'test_*.py'
```

The current cross-build produced a 480-byte loader and 15,840-byte RTEMS
diagnostic. Both linked ELF files have no remaining relocations. The exact
offline image and build maps are in
`artifacts/current/accele160-native-rom-20261020/`; the image SHA-256 is
`3f97745c76bd2d5e71a5ee143c9c9fec86bdb6a9d4a4b1202093eb944767909c`.
The spare-specific build from its own saved stock image is in
`artifacts/current/accele160-spare-rom-20261025/`, SHA-256
`6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd`.
The packer tests reject changed stock input, oversized payloads, and altered
loader/header/payload/trailer/reset bytes.
The observer's host-side C test can run locally without an i960 toolchain:

```sh
cc -std=c99 -Wall -Wextra -Werror -O2 \
  rtems/accele160/native_rom/host_startup.c \
  rtems/accele160/native_rom/test_host_startup.c \
  -o /tmp/accele160-host-startup-test
/tmp/accele160-host-startup-test
```

The updated `app.c` and `build.sh` were subsequently cross-built **locally**
with the archived Linux toolchain in an x86-64 Ubuntu container. The [offline
build record](../../../artifacts/current/accele160-offline-build-20261115/README.md)
has the new second-spare-specific `HST0` image, packer receipt, tests, and
emulator trace. The previously staged second-spare image remains byte for byte
unchanged. The new image is an offline diagnostic, not a flash candidate: it
still lacks host-visible PCI/MU startup and a mailbox response.
`test_stage2.c` compiles the actual copy/check routine under ASan/UBSan and
checks success, bounds, wrong header, wrong digest, and unchanged output on
digest failure.

```sh
cc -std=c99 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  rtems/accele160/native_rom/test_stage2.c -o /tmp/i960-native-rom-stage2-test
/tmp/i960-native-rom-stage2-test
```

`preflight.py` is a **read-only** gate for a future isolated spare. Given this
exact candidate and two full stock READIMAGE capture directories, it requires
the same boot ID and card identity, selector 9, 1 MiB, clean transfer and guard
status, and the pinned stock and candidate SHA-256 values. It writes a receipt
with `storeimage_issued=false` and `flashimage_issued=false`. Run it on the
test host only after identifying the spare and making two fresh full reads:

```sh
python3 rtems/accele160/native_rom/preflight.py \
  --candidate artifacts/current/accele160-native-rom-20261020/native-rom-prototype.bin \
  --read0 /path/to/spare/rawflash-0 --read1 /path/to/spare/rawflash-1 \
  --bdf PCI_BDF --out /path/to/spare/native-rom-preflight.json
```

This receipt verifies the saved captures; it is not a live card lock or a
flash authorization. The existing `stage_image.py` and `flash_image.py` are
pinned to a different image and card BDF, so they must not be used for this
candidate unchanged. A later spare-only stage/readback workflow must recheck
the live device, driver, command ownership, and flash identity immediately
before each operation.

`observe.py --bdf PCI_BDF --out receipt.json` is a read-only post-boot
observer. It checks the exact AcceleRAID PCI identity, 8 KiB BAR, and inbound
translation before reading the sixteen status words twice. It decodes the
`HST0` extension when present and remains compatible with the older nine-word
report. It does not bind or
unbind a driver or alter PCI configuration. A missing card or changed BAR map
is reported as a failure, not interpreted as an empty status record.

## Hardware boundary

**Do not flash the original card with this prototype.** The stock reset block's call/return and
raw-image assumptions have been checked against saved disassembly and the
offline trailer, but have not been exercised with this loader. The card may
reject the altered image or fail before the host BAR is reachable. The host
x86 option ROM is also still stock and may expect the RAID application.
There is no autonomous flash rollback proven for a valid-checksum image that
hangs. One matching spare was installed at `0000:37:04.1`, captured twice,
staged and independently read back, then experimentally programmed on
2026-10-25. The [spare test receipt](../../../artifacts/current/accele160-spare-rom-20261025/README.md)
records the exact image and command results. Its first cold start failed
before the user's normal POST beep. The [emulation gate](EMULATION.md) now
defines stock/candidate differential execution before any further flash.
The latest [offline ISP replay](../../../artifacts/current/accele160-isp-feature-status-20261025/README.md)
reaches an ISP BUS RESET only by using explicitly fabricated status output;
it still does not process the option ROM's controller-info mailbox request.
This does not change the no-flash decision.
An [offline no-option-ROM variant](../../../artifacts/current/accele160-romless-post-20261025/README.md)
changes only the x86 `55aa` signature byte at flash offset `0x30000`.
Experimental SeaBIOS/QEMU reaches a test boot sector with that variant,
whereas the valid option ROM waits inside controller BAR polling. The same
i960 RTEMS scheduler trace still passes. The physical PC BIOS and Linux
driver path have not been checked, and this image is not accepted by the
existing flash tool.
The [second spare's capture and staged variant](../../../artifacts/current/accele160-second-spare-20261026/README.md)
use its own descriptor and two matching full-flash reads. The exact no-ROM
image passes offline i960/QEMU replay and RAM stage/readback, with no flash
command issued. Its physical HP BIOS cold start is still untested.
Without a programmer, a failed test card may remain unusable until one is
available. A spare card protects service continuity; it does not restore a
bricked card.

The build on `192.168.2.80` was isolated under
`/home/mit/i960-native-rom-20261020/`. The existing live RTEMS/PCI owner was
not interrupted. SSH and the LAN route worked; no host routing was changed.
