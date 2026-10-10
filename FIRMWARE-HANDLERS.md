# Firmware handler analysis — 2026-10-10

**Current result:** [In-system recovery succeeded](SNAPSHOT-RECOVERY.md). A paired
512 KiB capture contains the exact 4.07-0-29 firmware and FWTCBBLK boot block,
plus the independently verified PCI BIOS. This supersedes older no-dump status
and the 256 KiB layout assumption below.

**Update:** [FIRMWARE-40729.md](FIRMWARE-40729.md) verifies the matching-version
reference supplied by the user. Its bootstrap and read/copy/DMA handler regions
are identical to 4.07-0-39. The reference-version gap is resolved for those paths;
installed-byte identity and staging/alias behavior remain unverified.


**The vendor reference firmware contains a flash-to-staging-buffer copy followed
by a host-readable image command.** This establishes a plausible software dump
path. It does not yet establish a valid dump of the installed card: the reference
is 4.07-0-39, the running card reports 4.07-0-29, and the current live staging
buffer has not validated as a flash image.

## Verified unpacking

The normalized 0x38000-byte firmware contains a standard ZIP archive at offset
0x7000, not a proprietary Huffman stream. The archive has one member, `ZIP1`,
using PKZIP method 6 (Implode): compressed length 167,576, output length 304,120,
CRC32 `31d5040e`. Info-ZIP `unzip -p` extracts it successfully. This is the ZIP
Implode format, distinct from PKWARE DCL/blast.

`host/dump/unpack_firmware.py` pins the input hash, verifies archive metadata,
extracts only ZIP1 to stdout via unzip, and checks output length, CRC32 and SHA-256.
It refuses to overwrite its output. The output hash is
`6d35598e082f72c83fcc6030e3b4788dfb6f7c334ada569f7e2a140a9195a3fe`.
The reproducible manifest is `artifacts/analysis/firmware-unpacked-manifest.json`.

Startup at flash address 0xFEFC8170 copies raw offsets 0x1000–0x6FFF to DRAM
0xC000A000–0xC000FFFF. It passes the archive at 0xFEFCF000 and destination
0xC0010000 to the decompressor, then jumps to 0xC004A2E0. Thus:

- Bootstrap runtime address = raw file offset + 0xC0009000 (within the copied area).
- Unpacked program runtime address = unpacked file offset + 0xC0010000.

The old linear flash-address disassembly mislabels absolute call destinations
inside relocated bootstrap code. Use these runtime bases when following calls.
Vendor binary and complete disassembly outputs remain on the SSH machine under
`/home/mit/i960-analysis.7jVBmy/`; they are not redistributed in this repository.

## Command dispatch recovered

At 0xC001F7B0, the dispatcher reads mailbox byte 0, masks bit 7, subtracts one,
checks the index, and indexes a table at 0xC001F804. The following entries are
read directly from the verified decompressed bytes:

| Opcode | Dispatch target | Subsequent path |
| --- | --- | --- |
| 0x1C | 0xC001FE6C | Enquiry2 |
| 0x20 | 0xC001FDB8 | schedules 0xC004CCB0, calls board callback +0xE0 |
| 0x21 | 0xC001FDC8 | schedules 0xC004CD00, calls board callback +0xE4 |
| 0x22 | 0xC001FDD8 | schedules programming path; not used |
| 0x2B | 0xC001FE90 | config subcommand dispatcher 0xC00207D0 |

For one initialization path, callback +0xE0 is 0xC004CE90 and +0xE4 is
0xC004CED0. The later bootstrap path at runtime 0xC000C9A0 (raw offset 0x39A0)
sets them to 0xC004D2C0 and 0xC004D2F0. Both pairs obtain the staging pointer
from the same helper at 0xC004D230.

The read handlers add mailbox offset +4 to the staging base, take the 16-bit
count at +2 and host bus address at +8, then invoke DMA helper 0xC004C010 with
control value 15. The write handlers use control value 14. Live 0x20/0x21
observations and vendor host dataflow independently agree with these directions.
These are image-buffer operations, not arbitrary CPU address reads.

## The flash-copy helper

The helper at 0xC004D230 has this observed flow (names below are our annotations):

```
if (staging_pointer != 0)
    return staging_pointer;

prepare_allocator();
staging_pointer = allocate(board.flash_size);
destination = staging_pointer | board.memory_alias;
source = board.flash_base;
for (i = 0; i < board.flash_size; i++)
    destination[i] = source[i];
return staging_pointer;
```

Relevant reference addresses:

- Staging pointer: 0xC0112A70.
- Board descriptor pointer: 0xC011E22C.
- Memory alias value: 0xC011E230.
- Board fields: +8 size, +0x0C source base, +0x10 flash-descriptor address.
- Copy loop: 0xC004D284–0xC004D2A8.

This is positive evidence of a flash-read mechanism, unlike merely finding
strings or guessing opcode names. It also explains why a previous upload can
contaminate subsequent reads: nonzero staging state bypasses the flash copy.
It does **not** explain all unidentified live bytes yet.

## Image-window correction

An earlier bootstrap routine at runtime 0xC000C600 configures size 0x80000,
base 0xFEF80000 and descriptor 0xFEFF9C00. However, the decompressor wrapper
finishes through runtime 0xC000C9A0, which sets size **0x40000**, base
**0xFEFC0000**, and descriptor zero, then installs the alternate callbacks.
The expected firmware entry relative to this latter image base is **0x8000**.
The bootstrap code is in the 4.07-0-39 reference; the live revision's final board
state still needs verification.

Our original kernel harness allowed offsets up to 0x80000 without evidence of a
per-board image size. It now limits offset+length to 0x40000. No read is validated
as flash solely because it falls inside that conservative bound.

## Descriptor operations and cleanup are not yet live procedures

The 0x2B dispatcher uses mailbox byte 2 minus one as its table index. Subcommand 2
jumps through board callback +0xD0; subcommand 3 schedules a path using +0xD4;
subcommand 13 uses +0xD8. Callback availability varies by initialization path.
The earlier configuration installs a descriptor reader at 0xC004D670, which can
read directly from flash when staging is absent and from staging otherwise.
The later configuration installs 0xC0050870 in these descriptor callback slots.
Consequently, the DOS flasher's descriptor-read path cannot be assumed to work
on every board configuration.

A routine at 0xC004D6D0 obtains/frees staging memory, clears the pointer and returns
status 0x104. Its `WrongFl` string and changing callback assignments make it an
error/cleanup path, not a verified standalone refresh command. We did not invoke
it by guessing a command. There is no established safe live “refresh from flash”
sequence in this work.

## Additional live checks and their limits

Two further paired 512-byte 0x20 reads ran through the existing constrained
transport, each with Enquiry2 before/after. All eight completions had matching
IDs, status zero, unchanged guards, and pending=0. Both pairs matched exactly.

| Offset | First 16 bytes | Interpretation |
| --- | --- | --- |
| 0x48000 | `a6 b2 6b f6 f5 88 66 8d 0d ea e8 0e dd 36 fb 8e` | Tested before finding the later 256 KiB override; outside that window, so not a valid flash-image probe. Do not repeat. |
| 0x8000 | `a7 7d 8f 98 9c 80 30 3c 0f 19 2e bf d8 18 2e 1b` | Inside the corrected window, but does not match the reference boot entry. Source identity remains unverified. |

A version difference alone is not an explanation for these bytes; neither is the
known first-512-byte staging overwrite sufficient to explain them. Possible
state/address-alias differences require evidence, not an assumed fix.
Captures and manifests are in `artifacts/firmware-handler-20261010/`.

Both modules were removed after completed transactions. Final state: module
absent, controller driverless, PCI command 0x0006, BAR0 0xEE000008. No reset,
program operation, staging upload, descriptor command or recovery-mode entry
was issued during this follow-up.

## Reproduction and next decision

```
python3 host/dump/unpack_firmware.py /path/to/firmware.raw /new/path/unpacked.bin
python3 -m unittest discover -s host/dump -p 'test_*.py'
```

The actual reference extraction passes size, CRC and hash validation. Four new
negative tests reject unsupported input, truncation, wrong CRC and a wrong output
with an internally matching CRC. All 14 dump-tool tests pass. The kernel module
with the reduced image-window bound builds with W=1 against the running kernel.

A useful next experiment is a **fresh-session 0x20 read before any 0x21**, but a
reset/reboot has not been performed or established as necessary. Before that,
obtain the exact 4.07-0-29 reference if possible and check its copy helper, alias
configuration and callback assignments against this analysis. If fresh reads
produce a valid boot entry, capture the established window twice and validate
its firmware, boot-block and IBR structure. The 256 KiB image window would still
not, by itself, establish complete coverage of a larger physical flash chip.

Do not clear arbitrary card memory, invoke ProgramImage, or provoke an unsupported
command merely to discard the current staging buffer. No valid installed-firmware
or complete physical-flash dump has been obtained yet.
