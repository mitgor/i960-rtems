# Resident RTEMS application arena and segmented upload — 2026-10-12

Accepted final profile: `--resident-upload --owned-mib 12`, with all release
exclusive ownership flags. No flash change. Exact kernel SHA-256:
`e1ac22ddd47849ad54a73f6ced21455db91910e45f012218dffb770ac6a9ba85`.
Payload 432,400 bytes; second-stage code `c0f94000..c0f95910` (6,416 bytes).
The original immutable monitor still fits its 128 KiB window, with 1,088 bytes
left. Runtime BSS ends at `c0f894f0`, leaving 43,792 bytes before the loader.

## Accepted final run

`live-v4`, boot `ff3647b6-6a15-41e6-83be-a70f04008663`, used the v3 host module
with its explicit upper-code pre-takeover verification and the corrected Python
whole-snapshot scheduling gate. The target kernel was unchanged from v2.

- Four startup patterns over 12 MiB, with protected-code/high-tail comparisons.
- Guarded 8 MiB arena at `c02d0040..c0ad0040`, metadata in original runtime BSS.
- Resident uploads: 98,304 code bytes, 98,309 data bytes, 98,299 BSS bytes zeroed
  and checked. The image occupies a 327,680-byte span. Only the reviewed returning
  probe prefix executes; uploaded padding is CRC-verified, not arbitrary code run.
- A simultaneous contiguous 6,291,456-byte allocation was filled, checked and
  freed while the image remained pinned: 6,619,136 requested bytes live together.
- Copied instructions read `DATA` from the separate segment and returned
  `e4f1e4e1`. No firmware callback after the initial ARM; all uploads used PIO.
- 506 submitted command records (505 sequence numbers, including one deliberate
  replay rejection), stale epoch, overlap, wrong offset, duplicate write,
  incomplete prepare/run and partial-cancel tests.
- Ten concurrent dual-stack rounds: 140 client cases, 1,115 verified packets,
  30 retransmitted TCP segments; saturation reached 128 slots with 31 expected
  burst drops. Existing network timeouts were not increased.
- STOP parked at tick 7,907 (~79 seconds). Both workers/owned IRQ contexts drained;
  an intentionally partial upload was cancelled and the new arena proved empty.
  All 8,171 existing libc allocations and 585 shared objects retired.
- 135 protected pages, 4,347 page checks, zero protection errors. Complete final
  scan of the remaining 3,604,288-byte pattern reserve (901,072 words), plus the
  existing stack/workspace proofs.
- Observed IRQ maximum gap: 10.512 ms. Word-control ioctl maximum 9.954 ms,
  median 0.195 ms, across 4,544 reads. Upload ioctl maximum 388.109 ms includes
  contention with snapshots/networking. These are short-run measurements, not
  latency bounds or an endurance claim.

The resident module deliberately remains retained after final close, even after
successful park. The host was rebooted afterward to restore firmware ownership.
Production restoration is recorded in `production/` separately.

## Attempts retained

| Archive | Outcome |
| --- | --- |
| `failed-wire-layout.tar.xz` | Admission succeeded; manifest rejected before allocation. i960 C segment/manifest sizes were 32/272, wire sizes 20/172. Fixed by decoding 43 explicit words. |
| `successful.tar.xz` | First full sequential acceptance: uploaded/executed image, 6 MiB proof, six network rounds, partial-image STOP cleanup. Superseded by final concurrent acceptance. |
| `failed-concurrent.tar.xz` | Upload/probe completed but TCP timed out. Per-word diagnostic ioctls interleaved with uploads stretched snapshots and paused the relay. Word maximum 289.426 ms. No protection error was observed in captured diagnostics; no successful final-drain claim. |
| `final-concurrent.tar.xz` | Whole-snapshot exclusion gate corrected the host scheduling issue; all upload, concurrent network and shutdown tests passed. |

The compiler layout probe is saved as `layout-probe.c/.s`. The first native test
also exposed a 64-bit host pointer truncation in the guard helper; using unsigned
long preserved native pointers without changing the 32-bit i960 ABI.
The replay tool explicitly interprets Linux ESTALE (116), independent of the
replay computer's errno numbering.

## Evidence and reproduction

Each archive contains exact target binaries/ELF/map/disassembly/build metadata,
generated module and source, raw captures and relevant source snapshot. Member
hash manifests cover all regular files. `target-source-manifest.json` matches
175 repository C/header/assembly/link files to the final capture snapshot.
Readable summary, layout, control latency and independently replayed network and
upload reports are alongside the archives. Source archives exclude visitor logs.

`verify_upload.py` reconstructs both files, checks CRC32 and content hashes,
then replays the captured mailbox submissions through the actual C implementation
under ASan/UBSan. It checks returned states, results, handles and allocation
counters, and confirms partial-image cleanup after STOP. `verify.py` separately
checks firmware identity, prepared image, bootstrap bytes, one-callback behavior,
RAM/IRQ lifetimes, networking, and retained-close behavior. Both passed locally.

Native tests cover allocator/image failures, padded C layouts, protected-page
mutation, bootstrap response verification, and the actual snapshot/client gate.
After capture, the host prepare-loop bound was enlarged from 2,000 to 8,224 steps
and tested with a maximum-length mock, so the helper can cover a full 8 MiB arena.
The card used far fewer steps; full-capacity image upload remains untested.

Remote workspace: `/home/mit/i960-resident-upload-20261012`. Final run:

```sh
sudo -n python3 project/rtems/residentnet/live.py \
  --payload residentnet/kernel.bin --module residentnet-module-v3/dac960auto.ko \
  --output live-v4 --secondary-reset --fault-owner --extra-ram --general-heap \
  --heap-shared --queue-reclaim --owned-mib 12 --resident-upload \
  --upload-concurrent --ticks 60000 --rounds 10 --round-interval 4 --parallel --burst
```

Extract `final-concurrent.tar.xz` into an empty directory, then use repository tools:

```sh
python3 rtems/residentnet/verify.py --root /path/to/extracted /path/to/extracted/live-v4
python3 rtems/residentnet/verify_upload.py /path/to/extracted/live-v4 --output /tmp/upload-replay.json
```

The [ownership/transport contract](../../rtems/residentnet/UPLOAD.md) records limits
and next steps. Libc still uses the existing 171,824-byte heap. Arbitrary application
task launch, imports/relocations, Doom and longer concurrent endurance remain.
Checksum quarantine and protected-page fault injection passed native tests; they
were not deliberately injected into the live card in this batch.
