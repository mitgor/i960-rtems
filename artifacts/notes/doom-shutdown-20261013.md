> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Shared-heap shutdown and native replay — 2026-10-13

Physical and offline acceptance passed. This follows the two matching Doom first frames and
failed global STOP in [the ACK batch](../doom-sidefix-ack-20261013/README.md).

## Reproduced shutdown race

The old worker loop lets one task cancel/release shared references while its peer
is still finishing a work iteration. The deterministic freestanding 32-bit test
uses the actual RTEMS allocator and shared-heap code: task 0 publishes phase 1,
task 1 enters acquire, and a simulated preemption drains task 0 immediately before
task 1 takes the heap lock. Task 0 was the sole owner, so the buffer is freed.
Task 1's expected acquire refuses and `SHCHECK` aborts with heap error 10, equal
allocation/free counts and zero live bytes. This matches the card's terminal
signature; its old capture did not identify the exact failing SHCHECK line.

`worker_stop.h` tracks both workers leaving their work loops. A worker may begin
heap cancellation only after both arrive. Waiting keeps it runnable with timer
interrupts enabled, so it does not introduce an unregistered idle IRQ owner.
Control polling continues. Ten seconds or 100,000,000 polls terminates a stuck
wait; existing task/IRQ drains, ownership, guards and final scans remain required.
Arrival is published while interrupts are masked on this single-CPU target.

The same preemption with the barrier defers cancellation until both iterations
finish and drains with valid allocator metadata, zero live bytes and matching
created/retired shared handles. The test also checks elapsed, wraparound and
stalled-clock limits. The full 20,000-step allocator/shared-ownership regression
passes separately; it is not replaced by this small race test.

## Native replay diagnosis

A retained debug replay localizes the abort to `doom_shared_peer_step` acquiring
its audit mutex, during the rapid repeated PREPARE sequence. The native producer
had no modeled PIO delay and repeatedly reacquired the mutex within the peer's
unchanged two-tick wait bound. Adding a one-millisecond host transport delay after
each completed command, outside target locks, removes that abort. Target mutex
limits and physical test timing are unchanged.

This exposed a second issue in the remote analysis workspace: a stale
`engine_replay.py` omitted `I960_DOOM_CHECKPOINTS`, so the checkpoint-log allocation
was missing and a relocation address differed by 17,200 bytes. The current Git
helper already contains that flag. Synchronizing the read-only helper restores
that allocation model; no target firmware change is involved.

`verify_upload.py --native-work NEW_DIRECTORY` preserves generated source, input,
expected replies, binary and failure output for reproducible diagnosis.
`--commands-only` validates completed command evidence and the native model, but
always reports diagnostic-only, no physical final drain. Full acceptance still
uses the default parked-state check. Actual Doom ISA execution remains checked
against its separate native oracle and card checkpoints; it is not executed by
this host upload-state-machine model.

## Candidate and physical run

Workspace `/home/mit/i960-doom-shutdown-20261013`, boot
`f1aa723f-2de3-44bc-8841-c48f888d6bbf`, live supervisor PID 38092.
Kernel SHA256 `35fc3d80e5cd8a69d23cd90532e0afbc1827a91306fb2209c716b33e8bbd77eb`;
module SHA256 `cc55ffb901aa572a6110b898cc923172c82f54919fa42a79a3bdc44592477b91`.
The Doom engine/admission are unchanged from the comparison-workaround archive.
The kernel RAM audit passes without a new memory grant. Both worker arrival flags
are private BSS; no wire ABI or application callback changes are required.

The prior capture now passes all **7,832 native command replies** in diagnostic
mode (`native-command-replay.json`). Its physical shutdown failure remains a
failure. The new 75-round physical batch passes the default full verifier,
parked upload query, all paired audits, reference checkpoints and mutation tests.
The public relay was stopped cleanly and its module unloaded before launch.
The test reservation was held through capture verification; restoration is
complete as recorded below.

The paced replay also passes all 7,832 replies on macOS with ASan/UBSan
(`native-command-replay-macos.json`). Its generated sources, input, expected
replies, executable and output are in `native-macos.tar.gz`. The physical capture
being replayed remains the prior failed-shutdown batch; these diagnostic reports
must not be used to overwrite that verdict.

## Reproduction and acceptance boundary

From the isolated remote workspace, the small race and existing allocator suite
use the actual RTEMS 4.6.6 allocator sources:

```sh
python3 project/rtems/residentnet/test_general_heap.py --rtems rtems-4.6.6 --out stop-before --shared --queue-reclaim --shutdown-race before
python3 project/rtems/residentnet/test_general_heap.py --rtems rtems-4.6.6 --out stop-after --shared --queue-reclaim --shutdown-race after
python3 project/rtems/residentnet/test_general_heap.py --rtems rtems-4.6.6 --out heap-regression --shared --queue-reclaim --iterations 10000
```

The first command succeeds only when it reproduces the old assertion; that is a
regression-test success, not an accepted target shutdown. The second succeeds
only with both workers quiescent before cancellation and a valid empty heap.

The unchanged full card recipe is in [live.sh](live.sh). Its postprocessing is in
[postrun.sh](postrun.sh): network and full paired-memory replay, default upload
replay including the physical parked query, independently rebuilt native
upload model, comparison with the independently generated native checkpoints,
and startup-evidence mutation rejection. The native
command-only diagnosis above cannot substitute for any of these gates.

The bounded barrier applies to the two resident shared-heap workers on this
single-core target. It does not provide arbitrary task cancellation or SMP
synchronization. Native tests cover both timeout conditions; the long card run
exercises ordinary cooperative arrival, not a deliberately wedged worker.

The unchanged Doom build is in
[`doom-sidefix-20261013/build-evidence.tar.gz`](../doom-sidefix-20261013/build-evidence.tar.gz),
SHA256 `8b5a2b9401bb750e66f6fa2211463ab243dd9f6aa937ee1402526255951cfece`.
The new card archive also contains the exact six admitted engine files under
`residentnet/entry/engine`, including the reference checkpoint stream. Engine
template SHA256 is `faa5a9a1712a8089c6fe62e240a20a3da789d24f5205888f99ea169a2cb5731f`;
reference checkpoint SHA256 is
`e6060504b89dc297306603abd076d015ee13493662eb2d4e8f6b80a06cf8c526`.

## Physical result

The 75-round run completed in 4,491.260 seconds with **626 full snapshot/RAM
pairs**. Global STOP reached parked state at tick **444,562**; both worker-done
flags, balanced interrupt lifetimes, guards and final ownership scans passed.
The default network verifier accepts the capture: **306,981 allocations freed**,
**10,209 shared handles created and retired**, no large-workload allocation
refusals, and 444 unlocked-copy preemptions for each worker. Its 24 snapshot
corruption checks are rejected as expected.

Doom startup / partial-transfer STOP / startup completed in **1,522.551 /
25.922 / 1,514.546 seconds**. There are **403 checkpoint records** (199 + 5 + 199)
and **50 successful ACKs**. These remain initial wipe frames, not gameplay or
rendering FPS. No change to the engine, memory grant, mutex timeout, checkpoint
protocol or physical audit coverage was needed for this batch.

## Accepted replay and archive

Default full `verify_upload.py` passes **7,832 command replies / 21,515 upload
PIO records**, with `commands_only=false`, `native_cleanup_modeled=false` and
`stop_cancelled_partial_image=true`. Both first frames have pixel FNV
**4000963876** and palette FNV **1611003811**. The exact WAD proof covers **9,496
requests / 55,300 fragments**. All **24 startup evidence mutations** are rejected,
including frame/palette/cleanup, WAD fragments and checkpoint ACK corruption.

`checkpoint-comparison.json` is intentionally a diagnostic report rather than
an acceptance authority. Its two normal generations each match all 199 native
records. Its STOP generation differs from the normal oracle at the requested
exit, as expected; the complete engine verifier separately validates that STOP
and cleanup. Use the full network and upload reports together for acceptance.

`card-evidence.tar.gz` SHA256:
`30d1b9f186321548637801f1ec30699ecd07b2b00148dd896981d997e7346b44`.
The local copy matches the remote checksum. It contains exact project sources,
kernel/module and admitted engine binaries, all live captures, build/RAM reports,
the old assertion reproduction and corrected race test, allocator stress,
unpaced/stale/paced native diagnostic builds, and the successful full replays.
The standalone JSON reports beside this README are convenient copies from it.

This is the accepted bounded N3 startup/STOP/repeat/global-drain baseline. The
previous failed batch remains failed. Visible scene progression, framebuffer
readback, browser delivery, general compiler repair and interactive performance
are subsequent work. Reboot was requested only after the complete archive was
copied and hash-checked locally. SSH initially remained unavailable and the user
was asked to power-cycle if stuck; it subsequently returned on a new boot.
Whether a physical power-cycle occurred was not observed.

## Public service restored

Boot `c76b2f32-a14d-4c03-952f-cbfa6b254cb9` had no bound card driver or competing
relay. The unchanged production relay now owns the card: supervisor **4358**,
Python **4359**, output directory
`/home/mit/i960-rtems-web-20261011/http-after-doom-shutdown-20261013`.
Mac IPv6 curl receives **HTTP/1.0 200 OK** and the Darth Vader / RTEMS system-info
page at `http://[2a02:8106:40:9000:f662:19ee:dbad:1f1e]:8080/`; outbound IPv6 fetch
of example.com also passes. Headers, body and their metadata are saved beside
this README. This is a Mac-to-host check, not a new external-network reachability
claim. Visitor statistics continue in their existing host directory and are not
copied into Git. Test reservation released; stop the relay cleanly before future
exclusive hardware work.
