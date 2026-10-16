> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Doom runtime entry / bounded WAD service — 2026-10-12

Implementation and acceptance record for the next step after shared arena
ownership. [ABI/lifetime contract](../../game/doom/runtime/entry/README.md).
No Doom engine has yet executed on the card.

Target SHA-256:
`6a20abc1606422b212e5b0d6e81a64c6b7b8bfe783728480847418246edac346`.
Reviewed application: 736 bytes, SHA-256
`31a69d63bf26dfb44bb6de5246490908be3fd27d3f162ec387e1f76b25692ed1`.
No unresolved probe imports; identical bytes linked at 0 and `0x100000`.
Protected upper code is 21,280 bytes; BSS ends at `c0f8b940`, leaving 34,496 bytes
before that code. No memory boundary or admission check was enlarged.

## Accepted card run

**Physical acceptance and independent replay passed** in `live2` on the second
boot. `accepted-evidence.tar.gz` preserves exact source, target/module binaries,
probe build/disassembly, full paired audits, packet/upload/WAD journals and raw
STOP evidence. The pinned WAD is 28,795,076 bytes, SHA-256
`7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d`.

- Real i960 code entered through the versioned table, allocated/freed through
  the shared arena, read the clock, and fetched header/directory/tail bytes.
  Both normal runs returned **2710325741** (the independent FNV oracle).
- **Ten read requests, nine replies**: six valid chunks accepted; CRC and short
  non-EOF payloads rejected; one explicit host error; one deliberately withheld
  response cancelled. Successful reads resumed afterward. Final report had
  **zero loans and an idle mailbox**. EOF, past-EOF, wrong file, excessive length
  and a destination outside the owning namespace were exercised by the probe.
- Normal entries took **8.016 s** and **2.491 s**; injected CRC/short/host-error
  entries took 1.088/1.023/0.335 s; the withheld reply returned after **5.121 s**.
  These are end-to-end measurements with audits/scheduling, not disk throughput.
  Twenty WAD queries totalled 5,086.509 ms; nine submissions totalled 1,712.891 ms.
  A bounded WAD cache and transport profiling are still needed for Doom startup.
- **Six dual-stack rounds / 782 replayed packets**, burst saturation and
  deliberate loss passed. Full snapshot replay rejected **24 mutations**.
  Maximum observed IRQ gap was **10.841 ms**. At **tick 11,672**, both workers
  and IRQ contexts drained and the arena/image/retained allocations were reclaimed.
- Native upload replay checked **539 commands / 1,420 upload ioctls**, plus the
  separate WAD stream, through actual C code. Eight runtime capture mutations
  were rejected. Existing shared-arena captures still replay with the new heap.
- ASan/UBSan, shared-owner ThreadSanitizer, host gate tests and the complete RTEMS
  offline suite passed. Native tests also cover stale loan tokens, token
  exhaustion, wrong-owner refusal and STOP during an outstanding read.

A final API review added an early refusal for NULL-pointer/zero-token loan
returns, preventing a NULL argument from being mistaken for an empty metadata
slot. That invalid-input guard is verified by native sanitizers after the card
run; the archive retains the exact physically tested source/binary. Valid read
loan paths are unchanged. This final guard has not had a separate physical run.

No flash write, forced unload, second firmware callback, new task or wider RAM
claim was used. The exclusive run requires reboot; production restoration is
recorded separately below.

## First attempt

`failed-tail-reply.tar.gz` contains the exact first target, module, source and
full available captures. The uploaded probe requested and received WAD header
and directory replies. Submission of its third (tail) reply returned EAGAIN.
The capture froze a live REQUEST but does not record the mailbox's later state
at refusal; expiration amid audit/poll scheduling is the working explanation,
not an independently recovered terminal error code. RTEMS was still active at
the failure snapshot (tick 10,728, no reported fault). The driver retained the
exclusive resources. This is failed evidence, not physical acceptance.

The host now holds the reentrant audit gate around each WAD query/reply pair
and avoids redundant UPL1 status polling while a WAD request remains pending.
It still performs every full paired snapshot, retains session/epoch checks,
does not retry uncertain writes, and uses the unchanged 500-tick target deadline.
New journal timestamps allow finer host scheduling analysis. The second attempt
uses the exact same target and kernel module after a reboot.

## Reproduction

Remote root: `/home/mit/i960-runtime-entry-20261012`. Build flags:

```
--profile residentnet --secondary-reset --fault-owner --extra-ram
--general-heap --heap-shared --queue-reclaim --owned-mib 12
--resident-upload --doom-heap --doom-shared --doom-runtime
```

Create a fresh module directory with `residentnet/build_transport.py`, build
against the running Linux kernel, and audit the RAM layout. For live.py omit
`--profile`; add `--upload-concurrent --ticks 18000 --rounds 6
--round-interval 2 --burst --parallel --drop-data --wad /path/freedoom1.wad`.
Check actual hardware ownership first. Never unload retained exclusive resources;
reboot after the batch and restore the cooperative public HTTP service.

The immutable WAD is `freedoom1.wad` from the already tracked
`artifacts/doom-m1-20261011/freedoom-0.13.0.zip`; it is not duplicated here.
The host logs file identity, offset, request mode and exact response packets.
Read the native/offline logs here. Replay a completed capture with:

```
python3 rtems/residentnet/verify.py --root EXTRACTED EXTRACTED/live2
python3 rtems/residentnet/verify_upload.py EXTRACTED/live2 --doom-heap --doom-shared --doom-runtime --wad WAD --output replay.json
python3 rtems/residentnet/test_runtime_evidence.py EXTRACTED/live2 --wad WAD --output tamper.json
```

The WAD verifier independently checks file identity, actual bytes, exact injected
failures, EOF length, reply ordering, report and FNV oracle, then executes the
captured reply stream through the real C runtime/probe/allocator/upload core.
Native replay represents the i960 function table with native pointer widths;
real i960 execution is established separately by the card capture. Native tests
cover STOP during a read; the live batch covers timeout recovery and final STOP.

## Production restoration

The final reboot returned as boot `c87aafb1-a3cf-48eb-aa06-0e7a154f33c9`.
The original cooperative IPv6 RTEMS/Vader/system-info service is restored as
PID **2247**, verified independently from the Mac with **HTTP 200**. See
`production-restore.json`, `service-status.txt` and `http-headers.txt`.
Visitor statistics remain on the host and were not archived. The Doom probe is
not a public game session; the public page continues to serve the original app.
