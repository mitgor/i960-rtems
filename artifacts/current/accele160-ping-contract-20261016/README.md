# AcceleRAID 160 bounded PING admission and stock `0x8f` test

2026-10-16. This batch develops the first **no-DMA** command contract for the
new AcceleRAID 160, still running stock 6.00-05 firmware. The old DAC960PG must
remain unbound. This is not an upload/call or a firmware patch.

## Native admission model

[`ping_protocol.c`](../../../host/accele160/helper/ping_protocol.c) accepts
exactly a 64-byte DAC960 V2 mailbox with main opcode `0x20`, control `0x40`
(`no_autosense`), IOCTL subcommand `0x8f`, zero DMA size/count/sense pointer,
zero SGE records, version 1, PING operation 1, signature `I960`, and a nonzero
32-bit nonce. Command ID is assigned by the host driver. The candidate request
puts version, operation, signature and nonce in common mailbox bytes 22–31.
The stock firmware only proves that it reads byte 21; transport and future
helper handling of bytes 22–31 require a live test. The signature is an
admission marker, not cryptographic authentication.

The native model builds an exact packet and rejects malformed envelopes; the
test compares it to an independently written 64-byte fixture, mutates all 58
non-ID/non-nonce bytes, and checks null/short/zero-nonce inputs. It ran with
AddressSanitizer and UndefinedBehaviorSanitizer:

```sh
cc -std=c11 -O2 -Wall -Wextra -Werror -pedantic \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  host/accele160/helper/ping_protocol.c \
  host/accele160/helper/test_ping_protocol.c -o /tmp/ar160-ping-protocol-test
/tmp/ar160-ping-protocol-test
```

## One-shot stock observation

[`build.py`](../../../host/accele160/helper/build.py) requires the exact pinned
Linux v6.8 `myrs.c`/`myrs.h` hashes and generates an isolated `myrs8f` module
restricted to PCI BDF `0000:37:09.1` and identity `1069:0050/1069:0054`.
The extension submits one stock `0x8f` command with zero DMA fields, under the
driver's direct-command mutex. A worker pins the module and command block until
completion. A timeout never cancels, reuses or unloads it. The
[`probe_stock.py`](../../../host/accele160/helper/probe_stock.py) harness checks
both card bindings, no disks, no retained reader, exact 64-byte mailbox, and
completed nonzero status before releasing the pin.

The module compiled successfully for Linux `6.8.0-138-generic` in the isolated
remote workspace `/home/mit/i960-ar160-8f-20261016`. Its SHA-256 is
`553028a8a22819b43d441e8b8af33ed0ade92e458f2b5a4369878a7637b483a0`.
The first load after unbinding stock `myrs` failed controller mailbox
reinitialization (`status 2`), before any `0x8f` command. This card has shown
the same second-initialization failure in previous work. A temporary `myrs`
blacklist let `myrs8f` initialize the new card first after a fresh boot. The
old card remained unbound. The one-shot [capture](stock-8f.json) records boot
ID `cf1ad15a-0e2f-4e19-ae9b-3041ced1877f`, driver `myrs8f` on `37:09.1`,
and the exact 64-byte request. Host observation took **50.3 ms**; completion
had host-visible status **2**, residual **0**. This is an unsupported/error
completion, not acceptance of a new PING handler. The harness verified the
mailbox, identity, ownership and completion, then cleared its pinned worker.

The temporary `/etc/modprobe.d/i960-accele160-8f-temporary.conf` was removed
and `update-initramfs -u` completed. `/etc/modprobe.d/blacklist-myrb.conf`
was preserved. `myrs8f` was unloaded only after its worker completed and
released; **both cards are now unbound**, SSH is healthy. No firmware write,
controller reset, or command to the old card occurred. The machine needed a
physical power cycle after the reboot; do not assume unattended recovery.

To replay the native model, run the sanitizer command above. To regenerate the
module, use the exact pinned Linux v6.8 `myrs.c`/`myrs.h` inputs in
[`sources.json`](../../../host/accele160/readimage/sources.json), then run
`python3 host/accele160/helper/build.py MYRS_C MYRS_H EMPTY_OUTPUT_DIR` and
build that directory against the host kernel. The Python generator refuses
source hash drift. Repeating the card test requires a fresh boot with stock
`myrs` prevented from binding the new card first; the prior same-boot unbind /
rebind attempt failed before command submission. The exact tested module hash
above and JSON capture are sufficient to identify this run; the generated
module is not retained as a second binary artifact.

## What this does and does not establish

The stock dispatcher’s zero-size DMA preparation returns without copying, and
the unsupported path stores internal status `0x104` at command offset `+0x56`
before calling the normal completion routine. The live host status is `2`;
its relationship to internal `0x104` has not been independently traced through
every mapping stage. This test validates stock command transport and cleanup.
It does not prove that a future helper’s reserved bytes survive transport, that
the erased loader space is owned executable memory, or that a modified image
can boot and recover. The next bounded step is an offline helper/dispatcher
patch and full-image structural verification; a flash test requires its own
recovery and rollback decision.
