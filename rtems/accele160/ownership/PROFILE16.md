# Profile 16: fixed QLogic software queue-state snapshot

This opt-in normal runtime keeps profile 14's engine inventory and adds **at most 18
fixed RAM reads**: three firmware identity/mapping guards, one exact context
pointer, and 14 context/accounting words. Profile 15 remains available for the
separate PCI identity probe. Profile 16 performs no new configuration cycles,
chip MMIO reads, status acknowledgements, queue writes or pointer traversal.
Normal profile 5 remains the service to restore after testing.

Before reading the context, the probe requires firmware `1077:1016`, selector
16, register mapping `8bf00000`, and context pointer `c03e5bc8 == c0600d00`.
Failure records a refusal and skips context reads. An arbitrary captured head,
tail or current-entry pointer is always data; it is never used as an address.
The fixed context comes from the pinned firmware analysis in
[profile 15](PROFILE15.md), not from a scan of RAM.

Words 352–383 in the existing 4 KiB report hold magic `QRM1`, schema 1, nonce,
sequence, phase, result, observed context pointer, count 14, 14 values and ten
reserved zeros. Results are 0 success, 1 metadata refusal, 2 pointer refusal.
The shared runtime acknowledgement is published after all reports. Host code
checks the envelope and rereads the immutable page. The extension fits without
changing the original report or the profile-14 inventory.

| Fixed addresses | Meaning established by the static trace |
| --- | --- |
| `c0600d28` | Context's chip mapping, observed only |
| `c0600d2c/30` | Pending software list head/tail |
| `c0600d34/38` | Request ring base/capacity |
| `c0600d3c/40` | Response ring base/capacity |
| `c0600d44/48` | Current request/response entry pointers |
| `c0600d4c` | Packed 16-bit request producer/cached consumer |
| `c0600d50` | Packed 16-bit response producer/consumer |
| `c0498280` | Packed channel accounting; lower half is channel-0 active exchanges |
| `c0498284` | Another initialized channel accounting word; semantics not established |
| `c049828c` | Mailbox-reported firmware resource count, not an active-work counter |

Each accounting read includes the neighboring channel halfword. The raw 32-bit
word is preserved; the decoder also reports the channel-0 low halves. It does
not assert that all three have the same semantics. Firmware submission
`c0070a80..90` increments `c0498280`; response processing `c006fa38..4c`
decrements it. Setup clears `c0498284`, but the traced code does not establish
its meaning. `c006d320..36c` issues mailbox command 31 and stores its returned
word at `c049828c`.

Layout, pointer bounds/alignment and index ranges are reported independently.
Unexpected values are retained as evidence rather than used as addresses. Even
matching software indices and zero active exchanges do not prove hardware
completion: the consumer may be cached, chip DMA may be in flight, and no engine
has been permanently excluded. These are sequential observations, not an atomic
cross-engine snapshot. The probe uses the existing runtime memory attributes;
it does not flush or invalidate caches from the concurrent worker. In particular,
software accounting and cached consumer values are not fresh chip-completion
evidence. No new memory may be reclaimed on this evidence alone.

Native tests execute the actual C whitelist, reject every metadata guard and
an unexpected context pointer, verify that no context read occurs after refusal,
and check report boundaries. Decoder tests cover stale envelopes, reserved-word
corruption and out-of-range pointers/indices. The owned-runtime test includes
profile 16; its preprocessed exception entry must match profile 5. Both new
sources are pinned by the exact inventory source set in the build manifest.

## Reproduction

Clone an accepted bundle and preserve its admission and pin modules. Build with
`ACCELE_TERMINAL=1 ACCELE_TERMINAL_TEST=16 ACCELE_SERVICE=1`, persistent/reusable
mode and the existing FIFO/engine settings. Refresh the manifest and bundle
hashes. Use the single-owner launcher on a fresh boot for 64 frames with 32
paired captures, run the external console acceptance client, and save the live
archive before clean STOP. Verify STOP and retained resources before rebooting.
Restore the immutable normal profile-5 bundle and verify paired firmware reads,
Doom/console acceptance and gateway recovery. See the artifact README commands.

## Next gate

Next, review access semantics and add a bounded read-only chip-state probe to
compare the real device consumer/producer with these cached software values.
It must preserve the known mapping, access widths and fault-retention path.
Only then use the observed queue layout to finish the board-specific stop contract:
identify all completion/accounting users, determine how to prevent new QLogic
DMA while retaining outstanding resources, and qualify a bounded failure path.
Any unresolved hardware state must retain firmware allocations and require a
reset. Preserve DMA0, primary ATU/MU and the working host transport. Keep the
stock-firmware coexistence option separate from exclusive isolation.

## Size correction from the first physical snapshot

The context reports **256 request entries and 128 response entries**, with the
previously traced 64-byte entry stride. This corrects profile 15's erroneous
128/64-entry static inference: request storage is `c0600df0..c0604def` (16 KiB),
response storage `c0604df0..c0606def` (8 KiB). Both remain reserved.

The test bundle is preserved unchanged, including its original analysis decoder
that tested the smaller hypothesis and reported `expected_layout=false`. The
card probe, read addresses, report format and acceptance envelope are unchanged.
The repository decoder now checks the measured sizes; native boundary tests
and replay of the actual raw capture validate this analysis correction. The
replay records both captured and corrected decoder hashes, and a copy of the
corrected decoder is archived. This is an offline interpretation correction,
not a second card run with a modified image.

## Physical acceptance and recovery

Kernel `660d5783b3c4fb597fcd41c9a3697d1d5bb636294cc7525064b15d778aa6b03f` on boot `f31b2a17-8809-4a88-b881-f03c297fe151`,
session `20261019T101018Z`, passed 64 frames, 5045 WAD reads and
709 external console exchanges without errors. Worst observed card reply
was 2879.710 ms, not a guaranteed bound. Owned vectors/ISP/guards,
report identities and stable-page rereads passed. Final STOP produced QUIE/ACK,
retained callback/pins and an identical fourth queue snapshot.

All four samples show context `c0600d00`, mapping `8bf00000`, pending head/tail
zero, request base/capacity `c0600df0/100`, response `c0604df0/80`, current pointers
`c0601730/c0605370`, request indices 37/0, response indices 22/22, and channel-0
accounting words 0/0/578. The ring pointers match producer/consumer positions
37 and 22 at 64-byte stride. Unequal cached request indices do not establish
37 outstanding requests; nor do the zero counters establish hardware drain.

Reset recovery on boot `9086e6f3-5eb2-424e-a210-d4dee54608dd` passed paired full firmware
reads and restored normal session `20261019T101634Z` with kernel
`55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`. It passed 64 frames, 5045 WAD reads and
709 external exchanges. Prompt idle/loan return and gateway HTTP 200 pass.
Leave this normal owner running. No physical intervention was required.

[Complete captures and replay commands](../../../artifacts/current/accele160-qlogic-queue-20261019/README.md).
