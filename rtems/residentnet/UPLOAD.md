# Resident segmented upload and application arena

**2026-10-12 shared-owner follow-up:** optional `--doom-shared --doom-heap`
adds one task mutex for loader and allocator metadata, and separate allocation
namespaces for the two existing workers. Command 9 exposes its frozen diagnostic
report. The physical shared proof, timeout/refusal checks and full STOP drain
passed; see [the ownership contract](../../game/doom/runtime/SHARED-ARENA.md).
Do not allow both workers to block: idle IRQ ownership remains unimplemented.
The single-worker description below remains the baseline without these flags.


**Doom allocation follow-up:** opt-in `--doom-heap` now tests a scoped libc
adapter on this same arena. [Contract](../../game/doom/runtime/README.md) and
[physical evidence](../../artifacts/doom-runtime-20261012/README.md). It adds UPL1
command 8; system malloc remains unchanged. The original accepted layout below
is historical; use the new image-specific map for this variant.

Opt-in `--resident-upload` integrates the guarded allocator and segmented image
core into exclusive RTEMS. It requires the release `--owned-mib 10` or `12`
profile, including secondary SCSI reset, owned faults, extra RAM, shared heap and
queue reclaim. Stock/cooperative profiles remain available. Exit is reboot-only;
there is no flash change, firmware callback after takeover, or resumed RAID/SCSI.

The accepted on-card tests and exact images are recorded in
[the artifact ledger](../../artifacts/rtems-resident-upload-20261012/README.md).
This is an application arena and resident loader, **not yet a replacement for
libc malloc or an arbitrary application task-launch ABI**. The existing libc
heap remains 171,824 bytes. The new arena supports pinned allocations and one
loaded image; the live allocation proof uses it directly in RTEMS task context.

## Ownership and bootstrap

Four address-dependent full-RAM passes still qualify the original 12 MiB grant
before RTEMS initializes. The new profile also fingerprints selected protected
pages before the passes and compares them after every pass:

- Original immutable code: `c0f2c000..c0f4c000`.
- Actual second-stage loader code, linked at `c0f94000`.
- `c0f9bff0..c1000000`: upper guard, frozen BIO response, saved staging tail,
  stock cache data/descriptors and top-of-DRAM warm marker.

These intervals are stable only after ARM returns and exclusive engine isolation
is established. Dynamic RTEMS BSS, task/IRQ stacks and the small queue/heap grants
remain excluded from immutable hashes and have their own ownership/guard checks.
This does not claim an inventory of every firmware allocation or graceful disk
flush. The engines are held/reset, stock execution never resumes, and the parked
firmware frame remains outside the destructive RAM grant.

The linker places loader/arena/image/protection text and constants in a separate
section in the original uploaded allocation. It is loaded and verified with the
initial image, not copied over running monitor code. Assertions keep it beyond
BSS and below the upper guard. The host's generated response validator checks
`c0f94000..c0f9bff0` against the original upload before takeover; that interval is
no longer treated as mutable in this profile. The separate loader section allows
larger uploaded applications without extending the original monitor code window.

| Interval | Ownership |
| --- | --- |
| `c0240040..c0280040` | Existing 256 KiB RTEMS workspace |
| `c0280080..c02c0280` | Existing four guarded stack slots |
| `c02d0000..c02d0040` | New arena lower guard |
| `c02d0040..c0ad0040` | New 8 MiB application arena |
| `c0ad0040..c0ad0080` | New arena upper guard |
| `c0ad0080..candidate_end-64` | Remaining immutable pattern reserve |
| `c0f4c010..c0f894f0` | Current runtime data/BSS, including allocator metadata |
| `c0f894f0..c0f94000` | Unallocated separation; not an application grant |
| `c0f94000..c0f95910` | Accepted second-stage code, 6,416 bytes |
| `c0f95910..c0f9bff0` | Unallocated code reservation, host-verified before takeover |

Addresses of runtime BSS and code end are image-specific; retain the linker
assertions and image audit when changing them. Do not infer ownership from unused
padding. `ram_audit.py` reports both code intervals and remaining BSS space.

Only this profile replaces the first 8 MiB plus 128 guard bytes of the old reserve
pattern contract. It does not disable reserve checking globally. Runtime checks
sample the remaining reserve and verify arena boundary guards. Worker 1 checks
one protected page per observed timer tick; the accepted image has 135 pages.
The whole protected set is checked again after both worker/IRQ contexts drain,
with control polls between pages. Sparse/background checks detect changes after
the fact, with the collision limitation of 32-bit FNV hashes. RX/RW labels and
redzones provide software policy, not an MMU or memory-safety sandbox.

RAM diagnostic revision 3 adds arena base/size/guard status at words 31–33 and
protected-page count/check count/error/address/code bounds at 34–39. Words 13–14
now describe only the remaining pattern reserve; the full final scan still checks
every word in that interval. `large_contract.py` validates the revised layout.

## Transport and execution

The host uses ioctl `0xc4204d06`, a 32-byte header followed by 1,024 bytes. Header:
operation (1 submit, 2 query), session epoch, request length, then five zero words.
Responses retain the established callback sequence, doorbell and uncertainty
checks. The same session mutex serializes upload, network and monitor access.
The concurrent host harness also excludes uploads for a whole diagnostic
snapshot, so a stream of upload ioctls cannot stretch each of its 64-word pages
and starve the network relay. This gate is shared with the upload client; it does
not hold the kernel lock across the complete upload or its preparation.
A 10-second PIO transaction deadline poisons the session on uncertain completion;
the client never retries an uncertain write. Reboot releases retained resources.

PIO tokens use the top byte for operation, next byte for word index and low
16 bits for the session epoch:

| Token | Operation |
| --- | --- |
| `70` | Begin mailbox, length 32..1024, multiple of four |
| `71` | Next sequential request word, index 0..255 |
| `72` | Publish the complete request to worker 1 |
| `74` | Freeze a 16-word result snapshot |
| `73` | Read one frozen result word |

Replies set bit `08000000`. ISR/control code only handles the mailbox and frozen
report. Worker 1 performs all allocation, CRC, BSS clearing and probe execution
with interrupts enabled. An occupied inbox refuses another request; network
worker 0 and the timer continue serving control. New submissions stop when STOP
is requested; status queries remain available while parked.

Each mailbox starts with eight little-endian u32 words: UPL1 (`314c5055`),
monotonically increasing request sequence, command, three arguments, two zeros.
Commands: 1 begin manifest; 2 write segment/index/length; 3 one prepare step;
4 execute the reviewed probe; 5 cancel; 6 arena validity; 7 six-MiB allocation proof.
Wire data chunks are at most **992 bytes** after the header. CRC/BSS prepare
steps are at most 1,024 bytes. CRC32 is corruption detection, not authentication.

A manifest is **43 explicit words**, independent of compiler struct layout:
ABI/count/entry followed by eight groups of offset/file bytes/memory bytes/flags/
CRC32. On GCC 3.3.6 for i960, the C segment occupies 32 bytes and manifest 272;
the wire equivalents are 20 and 172. Never memcpy wire bytes into those structs.
The first hardware attempt caught that mismatch by rejecting the request before
allocation. Native tests now repeat with deliberately padded structs.

The loader accepts relative segments in one pinned arena allocation. It validates
ranges, overflow, overlap, entry alignment, permissions and sequential writes.
Preparation rereads file CRCs, zeroes BSS, then synchronizes caches before READY.
At present RUN accepts only the five-word, returning, position-independent probe
that reads one word from the second segment and XORs it with `a5a5a5a5`.
The entire second segment's BSS is checked before the call. Extra uploaded code
bytes are verified and cached but are not executed by this probe. Arbitrary code
launch, relocations/imports and a runtime function table remain separate work.

STOP waits for worker and owned IRQ contexts to drain, then cancels any partial
image, releases its pin and proves the arena empty. Quarantined images or corrupt
metadata cannot be reclaimed; shutdown enters the existing terminal containment
path. Host final-close continues to retain the resident module until reboot.

## Reproduce

```sh
python3 rtems/build.py --work /path/to/work --profile residentnet \
  --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared \
  --queue-reclaim --owned-mib 12 --resident-upload
python3 rtems/residentnet/build_transport.py --out /path/to/module \
  --payload /path/to/work/residentnet/kernel.bin
make -C /path/to/module
```

On the known card, with the production owner stopped, use `live.py` with those
same feature flags, `--resident-upload --upload-concurrent`, explicit payload,
module/output paths, a bounded tick budget and network rounds. This is exclusive,
reboot-only use. Run `make -C rtems test` and `make -C loader test` offline first.
`verify.py` checks the full session; `verify_upload.py` reconstructs the uploaded
files and replays the request journal through the actual C core under sanitizers.

Next: libc/task ownership adapters, allocator latency at higher occupancy,
arbitrary owned application contexts, runtime imports/PIC or relocation policy,
and longer concurrent upload/network endurance. Doom and host-backed WAD I/O
still need their runtime work. No DMA or direct-NIC path is added here.

## Runtime entry and WAD service (2026-10-12)

The opt-in `--doom-runtime` extension is physically accepted on top of
`--doom-shared`. It uploads only the reviewed 736-byte probe, passes a versioned
runtime function table, and serves bounded reads from one immutable host WAD.
Commands 10–12 and separate WAD ioctl operations 3/4 are described in the
[ABI contract](../../game/doom/runtime/entry/README.md). All original upload,
full paired-audit and STOP/drain checks remain. The accepted timeout/error/
recovery run and the first refused tail reply are both preserved in
[the evidence archive](../../artifacts/doom-entry-20261012/README.md).
This does not yet load Doom or admit arbitrary application entry points.

## Accepted runtime proof extensions (2026-10-12)

Opt-in `--doom-runtime` now builds three closed reviewed application gates:
command 11 is the 736-byte PIC runtime/WAD probe; command 13 is the relocated
184-byte code/data/128-byte-BSS proof; command 15 is the 1,760-byte cache bridge.
Command 14 reports only the READY image's relative arena allocation offset.
None of these commands admits arbitrary engine code or accepts a host relocation
recipe. All ordinary segmented geometry/CRC/zero-fill/pin/cache checks remain.
Exact-byte whitelists and compiled trusted patch sites gate relocated execution;
post-entry code/data checks and template restoration precede completion.

[Physical cache and private-runtime evidence](../../artifacts/doom-platform-20261012/README.md)
records the six normal/error/timeout/recovery entries, full paired audits, actual
C replay and final task/IRQ drain. The host completion deadline is at most 60 s
for the seven-read cache probe; each kernel read still has its 500-tick deadline.
Invalid local deadlines refuse before publishing or consuming a sequence, and
uncertain writes are never retried. That input guard is native-tested after the
physical batch; all valid-command behavior is unchanged.

Use explicit complete Doom object suffixes in `link-upload.ld`. A leading
`*doom*.o` wildcard matches directory names too and can misplace ordinary kernel
code. The boundary assertion caught that failed offline build. Neutral versus
Doom-named path fixtures now produce the same layout without widening the window.
The link-complete private Newlib engine is a separate offline candidate and
requires its own owned entry/STOP, larger manifest and initialization acceptance.
