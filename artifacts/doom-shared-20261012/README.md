# Doom shared-arena task ownership — 2026-10-12

**Physical acceptance passed on the corrected build.** The two existing RTEMS
workers share one 8 MiB arena through one priority-inheriting task mutex, with
separate allocation namespaces. System libc remains on its established heap.
[Contract and reproduction](../../game/doom/runtime/SHARED-ARENA.md).

## Accepted run

Remote workspace: `/home/mit/i960-doom-shared-final-20261012`.
Payload SHA-256:
`c51468ac463d33183ff45a82d17e7595ae83b927f18ea1b64ce42d197ba32f91`.

- Command 8 verified the 6 MiB zeroed zone, resize/OOM preservation, overflow,
  strdup, and the other worker's 64 → 96 KiB resize. Its end-to-end duration was
  **15.551757493 seconds**, including scheduling and host transport.
- At the frozen diagnostic snapshot: **3,305 peer buffer/arena checks**, 3,305
  wrong-task rejection rounds (gate plus malloc/calloc/free attempts per round),
  **6,617 peer / 514 owner mutex entries**, one expected timeout, and one
  recursive rejection. Counters can continue after this snapshot.
- Maximum observed successful lock wait: **2 ticks**. Maximum observed hold:
  **5 ticks**, deliberately induced by the timeout test. Nominal ticks are
  10 ms. These are observations, not a wall-clock scheduling guarantee or
  normal allocator critical-section benchmark.
- Both workers retained patterned allocations, **98,304 + 65,536 bytes**, until
  STOP. The incomplete image also stayed pinned. At **tick 9,342**, both task
  and owned IRQ contexts drained, the complete retained buffers were checked,
  both allocation namespaces and the partial image were reclaimed, and the
  arena was proved empty. Outer guards, reserve and protected-code checks passed.
- **Six dual-stack network rounds**, **804 replayed packets**, burst saturation
  and deliberate TCP loss passed. The independent verifier rejected **24**
  corrupted snapshots. Maximum observed IRQ gap: **10.797 ms**.
- Upload replay checked **517 commands / 1,412 PIO ioctls**, exact ordinary
  replies and allocation handles, both file CRCs and bytes, **98,299 BSS bytes**,
  returning-probe result, and STOP cancellation. Asynchronous diagnostic values
  were separately validated against their captured report. Linux and Mac replay
  passed; **seven new capture mutations** were rejected.
- Existing system-heap stress retired **8,822 allocations and 578 shared
  objects**. These counters belong to the old system heap, not the Doom arena.
- Protected upper code: **17,168 bytes**; BSS ends at `c0f8a660`, leaving
  **39,328 bytes** before that code. No linker bound or RAM grant was enlarged.
- The refreshed allocation-integrated Doom relocatable object is **631,176
  bytes** (311,024 text, 69,888 data, 250,264 BSS), with **53 unresolved imports**.
  This is not a loadable or running Doom image.

## Failed attempt and fixes

`failed-idle-attempt.tar.gz` preserves the first build, complete available
captures, source, module and both placement failures. Initial links exceeded
128 KiB of main code. Semaphore/mutex/thread-queue routines were placed in the
existing protected upper section, whose full placement/hash checks still apply.

The first physical run ended with `ESHUTDOWN` during command 8. Its timeout
proof slept the lock holder while the waiter could also block. Code inspection
shows that this can reach this profile's deliberately fatal `idle_error` task;
idle has no registered IRQ owner. The first harness did not capture a terminal
snapshot, so the exact fatal code was not recovered. The corrected test keeps
the holder runnable, interrupts enabled, for five ticks. That exact test passed
on the second physical run. Do not interpret this as general idle-context support.

Review also found that a denied heap call wrote the diagnostic word before
acquiring ownership. Denied callers now leave all metadata untouched, including
overflow/null-input paths. The native threaded proof and real card repeatedly
exercise wrong-owner calls. The probe's long BSS check and reviewed execution
also moved outside the mutex, relying on the existing live image pin; metadata
state transitions remain locked. These changes are in the accepted image.

The native test initially modeled a nonrecursive mutex while RTEMS uses a
recursive binary semaphore. This produced an artificial long recursive-refusal
wait. Its backend now models RTEMS recursion and verifies the adapter refuses
nested ownership without losing the outer lock. ASan/UBSan, ThreadSanitizer,
allocator tests and the complete RTEMS offline suite pass.

No flash write, forced module unload, second firmware callback, or unregistered
application task was used. The failed session and accepted exclusive session
both required reboot. The final reboot returned; the original cooperative public IPv6 RTEMS/Vader
service was restored as PID 5764 and independently returned **HTTP 200** from
the Mac. See `http-headers.txt`, `service-status.txt` and `production-restore.json`.
Visitor statistics remained on the host and were not copied into git.

## Files and reproduction

- `accepted-evidence.tar.gz`: exact target/driver sources, binaries, map/symbols,
  disassembly/build recipes, full raw captures, network and upload replay,
  plus the updated i960 Doom object and symbol inventory.
- `failed-idle-attempt.tar.gz`: preserved failed attempt, never acceptance evidence.
- `card-shared.json`, `card-libc.json`, `summary.json`, `ram-audit.json`:
  small extracts from the accepted archive.
- Native/offline test logs, Mac full/upload replay, and capture tamper results.
- `prior-upload-replay.json`: old accepted single-owner capture still passes the
  changed core and verifier. Its numbers describe the old run.

Build/live flags:

```
--profile residentnet --secondary-reset --fault-owner --extra-ram
--general-heap --heap-shared --queue-reclaim --owned-mib 12
--resident-upload --doom-heap --doom-shared
```

For `live.py`, omit `--profile`; add `--upload-concurrent --ticks 18000
--rounds 6 --round-interval 2 --burst --parallel --drop-data`. Build in an isolated
workspace and create a fresh module output directory. Check the actual card
owner first. Never unload an exclusive retained module; reboot after testing.

Offline, extract the accepted archive into a fresh directory, then run:

```sh
python3 rtems/residentnet/verify.py --root /path/to/extracted /path/to/extracted/live
python3 rtems/residentnet/verify_upload.py /path/to/extracted/live --doom-heap --doom-shared --output /tmp/upload-replay.json
python3 rtems/residentnet/test_shared_evidence.py /path/to/extracted/live --output /tmp/tamper-results.json
python3 rtems/residentnet/test_doom_shared.py
SANITIZERS=thread python3 rtems/residentnet/test_doom_shared.py
```

Next: define a versioned application entry/runtime ABI and implement remaining
libc/compiler and bounded WAD services. Preserve a runnable control worker when
Doom blocks, or first implement and validate idle-task interrupt ownership.
Raw cross-task pointer transfer, arbitrary task launch and general all-task
blocking remain outside this acceptance.
