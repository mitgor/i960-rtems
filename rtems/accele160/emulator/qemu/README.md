# AcceleRAID 160 PCI option-ROM probe

## Archived stock/candidate comparison

`compare_coupled.py` compares the saved QEMU ROM/PCI/BAR/mailbox observations
and i960 bridge checkpoints without starting QEMU or accessing a card. For
the existing five-second Mylex option-ROM replay:

```sh
python3 rtems/accele160/emulator/qemu/compare_coupled.py \
  --stock-rom artifacts/current/accele160-rom-mailbox-20261025/stock.json \
  --candidate-rom artifacts/current/accele160-rom-mailbox-20261025/candidate.json \
  --stock-emu artifacts/current/accele160-rom-mailbox-20261025/stock-emu.log \
  --candidate-emu artifacts/current/accele160-rom-mailbox-20261025/candidate-emu.log
```

The saved result is
[stock-candidate-comparison.json](../../../../artifacts/current/accele160-rom-mailbox-20261025/stock-candidate-comparison.json).
Both images produce the same observed PCI configuration, BAR prefix, x86 ROM
blocks, and mailbox bytes. The i960 checkpoints differ: stock has advanced
past the host ACK into its next stage, while the native candidate has parked
after its RTEMS report. The BAR trace is capped, the stock command has not
completed, and the report's gate remains `INCONCLUSIVE`. This is an observed
checkpoint difference, not a proven first causal divergence or a physical
BIOS result.

This is an **offline host-side probe**, built against QEMU 6.2.0. It presents
the two PCI functions measured on the working original card: an Intel
`8086:2962` bridge at function 0 and a Mylex `1069:0050` RAID device at
function 1. The RAID function has subsystem `1069:0054`, revision `02`,
storage class `0104`, an 8 KiB prefetchable BAR0, and the unmodified x86
option ROM extracted from a saved flash image. It logs PCI configuration and
BAR0 accesses. BAR0 starts at
zero unless an explicit 8192-byte `aperture-file` is supplied; reads and writes
only affect that local buffer. With `bridge-socket`, the upper BAR page
(`0x1000..0x1fff`) reads and writes the running i960 emulator's RAM at
`PIATVR + BAR offset`. PCI configuration register `0x44` starts at
`0xc0000000` and remaps that page. The emulator serves requests after its
bounded boot run; concurrent execution is not modeled. With the bridge, the
DAC960 LP IDB register can fetch and forward one 64-byte hardware mailbox
from guest RAM via PCI DMA. It deliberately stays pending: there is no
controller command handler, completion, IRQ, or timing model.
An explicit `--explore-rom-ioctls` mode in `run_pci_rom.py` fabricates
zero-filled replies to four observed ROM IOCTLs (`0x01`, `0x11`, `0xd0`,
`0x2d`) with bounded DMA, mailbox status, and outbound doorbell handshake.
The stock x86 option ROM then returns to SeaBIOS, which reaches a test boot
sector and boots Alpine Linux to a login prompt in a 512 MiB guest. These
replies are **not** stock i960 firmware behavior. See the
[synthetic handoff run](../../../../artifacts/current/accele160-synthetic-handoff-20261115/README.md).
With a live socket, PCI command writes to function 0 and function 1 are
mirrored into the i960 model's local `0x1004` and `0x1204` command words.
The coupled [readiness test](test_pci_commands.py) proves that these host
writes release stock firmware's first wait. The `myrs` LP initialization
write of ACK-status (`0x02`) at BAR0+`0x20` is now provisionally forwarded to
i960 inbound doorbell bit 1; the coupled test shows this releases stock's
next wait. The mapping and later initialization remain incomplete; see the
[LP run record](../../../../artifacts/current/accele160-lp-init-20261025/README.md).

The source archive used for the tested build was the official
[QEMU 6.2.0 release](https://download.qemu.org/qemu-6.2.0.tar.xz), SHA-256
`68e15d8e45ac56326e0b9a4afa8b49a3dfe8aba3488221d098c84698bca65b45`.
The same patched source also builds on Apple Silicon macOS with Homebrew
Meson, Ninja, GLib and pixman. Configure with `--enable-fdt` in place of the
Linux-specific dependency setup below. The working local build is at
`/Users/mit/Library/Caches/i960/qemu-6.2.0/build/qemu-system-x86_64`; see
[the Mac run record](../../../../artifacts/current/accele160-local-mac-emulation-20261115/README.md).
On the Linux x86-64 test host, the local build used `libglib2.0-dev`,
`libpixman-1-dev`, `libfdt-dev`, Meson and Ninja. From this directory:

```sh
python3 install_probe.py /path/to/qemu-6.2.0
cd /path/to/qemu-6.2.0
./configure --target-list=x86_64-softmmu --disable-werror --disable-docs \
  --disable-gtk --disable-sdl --disable-vnc --disable-spice --disable-tools \
  --disable-user --disable-linux-user --disable-bsd-user
ninja -C build -j4 qemu-system-x86_64
```

With the custom QEMU binary and saved 1 MiB flash images:

```sh
python3 test_pci_bar.py --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64
python3 test_pci_commands.py \
  --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64 \
  --emulator /path/to/accele160-emu --image /path/to/spare-stock.bin
python3 test_pci_commands.py \
  --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64 \
  --emulator /path/to/accele160-emu --image /path/to/spare-stock.bin \
  --ack-status
python3 test_option_rom_coupled.py \
  --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64 \
  --emulator /path/to/accele160-emu --image /path/to/spare-stock.bin
python3 test_pci_bar.py --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64 \
  --aperture-file /path/to/controller-snapshot-8192.bin
python3 run_pci_rom.py /path/to/spare-stock.bin \
  --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64 \
  --aperture-file /path/to/stock-controller-snapshot-8192.bin
python3 run_pci_rom.py /path/to/failed-spare-candidate.bin \
  --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64 \
  --aperture-file /path/to/candidate-controller-snapshot-8192.bin
python3 test_live_bridge.py \
  --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64 \
  --emulator /path/to/accele160-emu \
  --image /path/to/spare-stock.bin --cycles 60000000 \
  --expected-report 00000000
python3 test_live_bridge.py \
  --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64 \
  --emulator /path/to/accele160-emu \
  --image /path/to/exact-failed-spare-candidate.bin --cycles 3000000 \
  --expected-report 32544753
python3 test_mailbox_submit.py \
  --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64 \
  --emulator /path/to/accele160-emu \
  --image /path/to/spare-stock.bin --cycles 60000000
python3 test_mailbox_submit.py \
  --qemu /path/to/qemu-6.2.0/build/qemu-system-x86_64 \
  --emulator /path/to/accele160-emu \
  --image /path/to/exact-failed-spare-candidate.bin --cycles 3000000
```

The [run record](../../../../artifacts/current/accele160-qemu-pci-probe-20261025/README.md)
contains the measured live PCI configuration and the two QEMU results. The
QEMU tests execute the actual PCI option-ROM entry and exercise the probe's
BAR0 read/write path. The final runs used static 8 KiB snapshots of simulated
controller RAM at `0xc0000000`, captured with the i960 runner's
`--dump-aperture=PATH` option. That BAR mapping is an exploratory hypothesis,
and the snapshot cannot reflect concurrent controller writes. The tests do
not reproduce the HP Z400 BIOS or the card's pre-POST failure. The stock and
candidate ROM bytes are identical. Standard SeaBIOS made no BAR0 or extended
configuration access in the bounded run, so the different snapshots did not
affect its trace. The original test mistakenly identified the VGA ROM's
`0xc0003` entry as Mylex's. The corrected probe locates Mylex at `0xcb000`:
its legacy callback receives zero from SeaBIOS, rejects the mismatched PCI
BDF, and returns. An [isolated BIOS variant and coupled replay](../../../../artifacts/current/accele160-bcv-gate-20261025/README.md)
now pass BDF `0x29` to that callback. Both exact spare images then make five
BAR writes; stock advances after the resulting doorbell, while the candidate
remains at its RTEMS park. This is an emulator experiment, not a physical
POST result.
The optional `--step-on-ack` switch runs one million i960 instructions when
the x86 ROM posts ACK-status, before the ROM continues. In that bounded
experiment stock reaches its next stage and the candidate stays parked;
neither image causes another ROM BAR access in the initial two-second window.
In a five-second run, both ROMs subsequently submit the same LP mailbox and
poll for completion. The [ROM mailbox run](../../../../artifacts/current/accele160-rom-mailbox-20261025/README.md)
records the DMA request and a further stock interpreter step. The model does
not yet complete the request.

The [live bridge run](../../../../artifacts/current/accele160-qemu-live-bridge-20261025/README.md)
verifies QEMU RAM reads/writes and PIATVR page remapping against both saved
spare images. The [LP mailbox submission run](../../../../artifacts/current/accele160-qemu-mailbox-20261025/README.md)
also performs the first `myrs` initialization transaction's host-side steps:
write a 64-byte `SET_MEM_MBOX` request into guest RAM, program the hardware
mailbox pointer, and ring the LP IDB. QEMU fetches the exact bytes by PCI DMA
and forwards them to the interpreter-side trace. It does not complete them.
The card's device ID `0x0050` selects the DAC960 LP driver path in Linux:
IDB is at BAR0 `0x20`, ODB at `0x2c`, and the hardware mailbox pointer at
`0x10`. The next step is to make stock firmware consume that request, produce
the status mailbox, and compare its completion with a physical stock capture.
The actual x86 option ROM's later request is different: it sends DAC960 V2
`GET_CTLR_INFO` (`0x20`/`0x01`) for 512 bytes. The
[captured ROM transaction](../../../../artifacts/current/accele160-rom-mailbox-20261025/README.md)
contains its exact 64-byte hardware mailbox. Even with the
[bounded ISP configuration probes](../../../../artifacts/current/accele160-isp-config-20261025/README.md)
and timer interrupt delivery, stock had not reached the MU receiver or
completed this request. Those probes are sequential and exploratory.

The later [forced-vector replay](../../../../artifacts/current/accele160-isp-bus-reset-20261115/README.md)
does reach the stock MU receiver after synthetic absent-device responses. It
backs the exact 64-byte ROM mailbox at the posted host address; the stock
helper copies it into local RAM in four 16-byte loads. The queued command has
now produced an offline 512-byte DMA1 output and outbound MU message under a
bounded descriptor model. That was the state of the sequential replay. The
later opt-in `test_preboot_card.py --explore-live-firmware` run starts the
stock i960 interpreter first, then connects QEMU while the x86 ROM executes.
QEMU copies the stock DMA output into guest RAM and exposes the stock MU
completion and doorbell. With the patched SeaBIOS in
`artifacts/current/accele160-bcv-gate-20261025/bios.bin`, the ROM completes
five observed IOCTLs (`01`, `11`, `15`, `d0`, `2d`) and reaches the ISO boot
prompt. `--boot-enter-on-prompt` sends Enter when the guest serial port prints
`boot:`. A 256 MiB Alpine guest subsequently starts the Linux kernel and
reaches `localhost login:`. The ISP scan responses and interrupt source
injection remain diagnostics. The corrected PC priority layout now lets the
stock mapped vectors enter through the normal CPU priority gate, but the
80303 external interrupt router and normal controller startup remain
unverified.
An additional bridge-only router experiment maps the modeled inbound MU
doorbell through stock IMAP1/IMSK to XINT7 and completes the same five ROM
IOCTLs. ISP interrupt routing remains unresolved: stock PIRSR sends INTA
upstream, while probing enabled inputs 1 and 2 does not consume channel 0's
synthetic status entry. Disassembly now shows the stock vector `0x42` handler
uses `(IPND & IMSK & channel_mask)` before calling the channel callback.
The channel mask is `0x1`; routed input 2 sets IPND bit `0x4`, so it cannot
service that response. The dated run record has the installed handler bytes,
disassembly, and probe transcript. The physical QLogic interrupt connection
and the source of this routing mismatch still need measurement.
An explicit offline PIRSR-bit-0 counterfactual (`test_preboot_card.py
--route-isp-pirsr-bit0`) routes all 15 synthetic ISP responses through
XINT0, then completes the stock x86 ROM's five IOCTLs and boots an Alpine
guest to login. Stock firmware itself writes PIRSR `0x0e`; this replay
overrides it to `0x0f` solely to isolate the routing dependency. The dated
record contains both the rejected stock route and this control.
With `--model-isp-no-device-queue`, a guarded offline queue model checks
the stock type-4/type-9 INQUIRY pairs and posts 15 hypothesized INCOMPLETE
statuses. One routed XINT0 interrupt then lets stock firmware drain them.
This mode removes per-response writes from the Python harness, but still
uses a synthetic absent-device result and the explicit PIRSR override.
The full run completes the stock ROM's five IOCTLs and reaches an Alpine
`localhost login:` prompt with one routed ISP interrupt for the 15-entry
response batch. The dated record contains the queue-model trace and ROM
output.
The opt-in `--auto-isp-no-device-queue` harness mode also removes explicit
`N` and `E 0` bridge calls: the emulator posts the guarded queue batch and
routes the interrupt on the next step after the counterfactual PIRSR change.
Its preboot trace reaches the same 15-entry consumer and MU-ready state.
Its full QEMU replay also reached Alpine login with all five stock ROM
mailboxes completed. The first full-run harness assertion expected direct
vector log lines, which routed interrupts do not emit; the saved guest,
ROM, and i960 traces passed post-run validation. The corrected harness
exited successfully on a shorter ROM replay. See the dated run record.
Disassembly of the stock setup now shows that its board-state value `0x20`
selects PIRSR `0x0e` and clears routing for channel 0. An opt-in control
posted the same 15 synthetic responses under that stock setting and ran
400 million more i960 instructions without an ISP interrupt; the stock
response consumer stayed at zero despite timer interrupts. The dated record
contains the disassembly and trace. The real card's QLogic interrupt wiring
and board-state field still need read-only measurement.
The stock board-state field is now traced to a firmware write that maps the
low five bits of the `0xe0400000` selector: the emulator's exploratory
selector 11 becomes kind `0x20`. The automatic ISP queue model now posts
responses independently of PIRSR and routes the pending interrupt only when
PIRSR allows it. Under stock `0x0e`, 15 responses remain pending after a
400-million-instruction control; the explicit `0x0f` counterfactual drains
them and completes the five-ROM-mailbox short replay. The dated record has
the source disassembly and both controls.
