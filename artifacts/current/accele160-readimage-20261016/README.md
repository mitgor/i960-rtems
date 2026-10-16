# AcceleRAID READIMAGE investigation — 2026-10-16

## Latest result

The subsequent fresh-boot test recovered matching pairs of the **512 KiB main
firmware, 64 KiB boot block and 28 KiB BIOS**. Main firmware decompression/CRC
passes. The whole 1 MiB flash is still incomplete; an additional image read was
followed by a confirmed host freeze. See [fresh-boot results and current handoff](fresh/README.md).
The sections below record the earlier investigation and failed live handoff.


## Result so far

**No complete stock flash dump. No READIMAGE command reached the card yet.**
The offline protocol is substantially better understood, but live driver handoff
failed before the descriptor probe. No flash programming command was sent. The
old DAC960PG at `0000:37:04.1` was never bound, reset individually, or accessed
through MMIO. The user subsequently authorized restarting the whole PC; that
restart necessarily affects both cards.

The preceding 28 KiB option-ROM capture remains the only accepted new-card dump.
This directory's Fujitsu package is a downloaded reference, **not a stock dump**.

## Recovered protocol

Source: [Fujitsu AR160 package](https://support.ts.fujitsu.com/globalflash/ScsiController/AR160/V7.02-0-00_6.21-40/zip_ar160_v7.02-0-00_6.21-40.exe).
It includes firmware 7.02-0-00, BIOS 6.21-40, and DACFL6 0.74. The installed
controller reported firmware 6.00-05. Release notes explicitly restrict upgrade
compatibility; none of these images was programmed or run on the controller.

The existing `host/globalflash_decode.py` decodes DACFL6 into an MZ executable.
Named routines and disassembly identify the READIMAGE wrapper at file offset
`0x939c` and its descriptor caller at `0xa98e` (call instruction `0xaa24`).
`analyze_vendor.py` validates the exact executable hash and 12 instruction
anchors, and confirms the direct far-call target from the MZ segment mapping.
This is not a general-purpose symbol parser or proof of all indirect callers.

| Mailbox bytes | Verified meaning in the utility |
| --- | --- |
| 2 | IOCTL command 0x20 |
| 4–7 | Transfer size |
| 8–15 | Sense buffer address |
| 16–17 | Argument word; descriptor caller passes zero; general meaning unknown |
| 20 | Sense length |
| 21 | READIMAGE subcommand 0x2d |
| 22–23 | Zero-extended selector; descriptor uses 0x0e |
| 32–39 | Destination DMA address |
| 40–47 | Destination length |

The verified caller requests 0x400 bytes and checks the first DWORD for
`0x4d594c58` (bytes `58 4c 59 4d`). It reads the **system flash descriptor**.
The wrapper zeros the remaining scatter/gather entries. The utility's `-r`
option writes image version information to `dacfl600.txt`; it is not a ROM
backup option. Names such as `makeEntireImageFile` must not be mistaken for
proof that arbitrary card flash can be read.

**Still unknown:** whether other selectors read persistent images or staging
RAM, how offsets/chunks are expressed, full flash size/layout on this board,
and compatibility of this command with running 6.00-05 firmware. No guessed
selector, MEMCOPY command, raw flash address or flash-write command was used.

## Narrow Linux probe

`host/accele160/readimage/build.py` generates `myrsread` from hash-pinned Linux
v6.8 `myrs.c`/`myrs.h`. Both originals are retained in `upstream-sources.tar.gz`.
The extension keeps the driver's normal queue/completion implementation and
adds only a fixed 1 KiB descriptor read and a cached-controller-info read.

- Requires `read_bdf=` and exact IDs `1069:0050 / 1069:0054` before detection.
- No old-PG match can pass that gate.
- Descriptor uses Linux controller-to-host/no-autosense flags instead of the
  DOS utility's autosense buffer. This adaptation is not yet hardware-validated.
- One command at a time, existing direct-command mutex, coherent DMA buffer.
- Worker waits for completion; userspace polls with a 10-second deadline.
- Pending work retains its DMA buffer and module reference. `clear` refuses a
  pending operation. This is **bounded observation, not command cancellation**.
- Driver bind/unbind sysfs attributes are suppressed on the experiment driver.
  Do not use PCI remove/rescan, force-unload, or free resources after timeout.
- Completion must be checked before buffer cleanup. Repeated exact bytes and
  descriptor structure are necessary before treating data as evidence.

The module compiled on Linux 6.8.0-138-generic. Python syntax validation and the
offline protocol-anchor check passed. The retained module is the exact attempted
build; it is not an accepted firmware-dump tool.

## Live handoff failure

Boot `164a6af9-4bc8-43f2-9eb0-805a0ce43f68` initially had new card bound to `myrs`,
old card unbound, and no new-card block disks. The first attempt unbound **only**
`0000:37:09.1`. Stock removal logged cache flush. Experimental driver detection
failed with `Failed to enable mailbox, status 2` and `Unable to Enable Memory
Mailbox Interface`. Upstream `DAC960_LP_hw_init` then invokes its controller
reset path. Thus this attempt was not reset-free, despite issuing no READIMAGE.

One subsequent experimental initialization and one stock-driver restoration
attempt both reported `Unknown Initialization Error FB`. No command job or DMA
buffer from the extension was created. The experimental module was unloaded;
both cards were unbound at that point. Exact kernel output is in
`live-attempt.txt`. The older NVIDIA boot warnings are unrelated, pre-existing.

The user authorized reboot. To avoid another live mailbox handoff,
`/etc/modprobe.d/i960-readimage-temporary.conf` was created with `blacklist myrs`,
and the current kernel initramfs was regenerated before `sudo reboot`.
The existing `myrb` blacklist/install rule was left unchanged. No experiment
module was installed for automatic loading. On return, verify identities and
that the new card is unbound before loading the explicit-BDF probe.

**Restore after testing:** remove only that temporary myrs blacklist, regenerate
the current initramfs, and restore stock binding via a fresh boot if live
reattachment repeats the mailbox failure. Never remove the old-card myrb rules.

## Reproduction / continuation

Offline:

```sh
python3 host/accele160/readimage/analyze_vendor.py artifacts/current/accele160-readimage-20261016/DACFL6-decoded.exe
python3 host/accele160/readimage/build.py /path/to/myrs.c /path/to/myrs.h /path/to/new-build
make -C /lib/modules/$(uname -r)/build M=/path/to/new-build modules
```

After a fresh boot with stock `myrs` prevented from binding, on Linux with the
repository layout copied intact:

```sh
sudo python3 host/accele160/readimage/probe_fresh.py --bdf 0000:37:09.1 --module /path/to/new-build/myrsread.ko --out /path/to/new-evidence
```

This probe only tries two descriptor reads; it does not dump full flash.
If initialization fails, stop and inspect logs rather than repeatedly binding.
If completion remains pending, retain the module and DMA storage. If descriptor
reads succeed, first decode and validate the flash layout, then corroborate the
actual image-read semantics before broadening the command or transfer length.

## Handoff status

The authorized reboot did not return SSH after several checks. Physical screen
inspection/power cycling was requested. Continue the fresh-boot test once Linux
is reachable. No descriptor or complete flash result is claimed.
