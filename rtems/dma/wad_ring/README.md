# Pipelined WAD request/completion ring

This is an **opt-in bounded experiment**, selected by `--wad-ring` together with
`--pipeline --pipeline-test --wad-dma --pingpong --debug-audits`.
The older mailbox and 4 KiB bulk paths remain available. Longer interactive
qualification and adaptive read-ahead remain future work.

## Layout and ownership

The driver retains two 40 KiB coherent host allocations. Each contains:

| Offset | Bytes | Owner / purpose |
| --- | ---: | --- |
| 0 | 4096 | Lower guard, initialized by driver |
| 4096 | 64 | Card-owned request |
| 4160 | 64 | Host-owned response |
| 4224 | 64 | Card-owned completion |
| 4288 | 32768 | Host payload, immutable until completion |
| 37056 | 3904 | Upper guard |

Sixteen little-endian words describe a record: magic, generation, slot, offset,
length, immutable file size, complemented generation, committed generation, and
eight zero reserved words. Requests, responses and completions use distinct
magic values. The epoch is checked by every host ioctl; mappings and card
registration belong to that one retained resident session. Generation zero and
wrap are forbidden. No userspace-selected bus/card address is accepted.

The card publishes up to two 32 KiB requests before consuming either response.
The host fills both from its immutable WAD snapshot. Payload and response stores
precede a DMA write barrier and the response commit store. The card's first
response fetch may straddle that publication, so after observing the committed
generation it rereads the now-immutable complete record before validation.

Card request/completion records use a separate final four-byte DMA for the
commit word. Each DMA has a finite descriptor and a bounded completion wait;
there is no circular hardware chain or unrestricted bus mastering. A completion
is published only after payload DMA has quiesced, full guards pass, and the
owning task has copied the valid bytes. A host slot cannot be reused until its
previous generation's completion matches its frozen response. The final two
completions are captured explicitly at STOP, even without subsequent reuse.

WAD and framebuffer traffic share DMA1. The same engine task drains a pending
frame before entering the WAD routine. No interrupt handler prepares a DMA,
scans guards, copies WAD bytes, or waits for hardware.

The card borrows both the cache's output allocation and its guarded staging
allocation. Full guard scans remain before and after **every** DMA operation;
word scans compare every byte, not a sample. Descriptor geometry, all descriptor
words, ownership, the DMA error/idle/descriptor/count registers, bus-master
cleanup and the isolation contract are checked. Full paired system/RAM audits
remain unchanged. Completion records attest these target checks; the ring does
not export a separate raw register report for every small control DMA.

STOP/host timeout can return only with hardware quiescent and card loans
returned. A timed-out partially served ring is retired instead of silently
retrying a generation. An uncertain hardware completion retains the card loans
and quarantines the session. Host mappings always remain pinned until reboot,
including STOP/errors. Never force-unload them.

## Read-ahead and ABI

The engine cache recognizes the opt-in `max_read=65536` batch API and requests
aligned 64 KiB windows, truncated at EOF. Its cache retains one such window in
128 independently tagged 512-byte lines, plus a 64 KiB bounce buffer. Each
window becomes one or two ring requests. The private ring read implementation
requires these exact aligned cache fills; it is not a general arbitrary-offset
64 KiB read service for other applications.

Legacy 512-byte/4 KiB API modes retain their 32-line, 16 KiB data cache and
existing no-read-ahead behavior. Metadata arrays have capacity for 128 lines.
The admitted engine supports both modes; a matched comparison changes only
whether the host enables the ring before engine startup.

Read-ahead trades fewer waits for more bytes. It must be measured for both cold
startup and warm level restart. In this scene it improves startup after word
optimization but increases warm-restart time; it therefore remains opt-in.
No WAD payload CRC is computed. Bounds/guards do not detect arbitrary in-bounds
byte corruption. Offline replay checks every submitted byte against the pinned
WAD; acceptance also compares frames/palettes with an independent native oracle.

## Host interface and evidence

Ioctl `0xc0204d0b` copies exactly 32,800 bytes: eight header words followed by
32 KiB payload. Header: operation, epoch, slot, generation, offset, length,
WAD bytes, zero. Operations:

1. Register the two driver-owned mappings once; no user address is accepted.
2. Read a committed request and the previous completion from host RAM.
3. Supply exact request bytes; zero padding is mandatory; publish response last.
4. Capture and validate the final request/response/completion triple.

Only registration uses mailbox commands (0x77 indices 6/7). Steady request,
response and completion operations use coherent host RAM. Every successful
exchange is journaled. Pending polls are counted/timed separately in the word
candidate, without writing a 64 KiB hex journal line per unsuccessful poll.

Run `test_target.py`, `test_host.py`, `test_client.py`, `test_cache.py` and
`test_protection.py` (the protection test needs Linux host32). They exercise the
actual implementations with ASan/UBSan and fault injection. The last test
mutates every protected page in the 146-page build.

For a physical capture, run the unchanged `residentnet/verify.py` and
`residentnet/verify_play_pipeline.py`, then this directory's `verify.py --wad
FILE`. All three are required: ring replay does not replace the system audit or
frame/STOP validation. Compare the first 52 controlled frames against native
output, preserving the four known pixel differences rather than ignoring them.

Exact binaries, sources, measurements, full captures and restoration status:
[dated evidence](../../../artifacts/wad-ring-20261015/README.md).
