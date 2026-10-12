# Shared task ownership of the resident arena

The opt-in `--doom-shared --doom-heap --resident-upload` profile lets the two
existing, registered RTEMS workers use the **same** admitted 8 MiB arena. It
adds no memory grant and does not replace the 171,824-byte system libc heap.

## Ownership contract

A priority-inheriting RTEMS binary semaphore serializes arena metadata. Worker
1 owns the loader and the namespaced Doom libc context; worker 0 owns a separate
`doom_heap` context over the same arena. Allocation records are private to each
context. There is one arena, one set of 128 generation slots, and one mutex.
The two contexts do not increase arena capacity or its slot limit.

The adapter admits only the registered thread identity for its context. ISR,
dispatch-disabled, wrong-task and recursive entry are refused. A denied call
must not change even the allocator diagnostic word. Normal lock acquisition
has a two-tick wait budget; a timeout does not steal the mutex, drop a pin, or
infer that another task completed. The runtime treats unexpected test-operation
failure as terminal containment. There is no automatic retry of an uncertain
copy and no arbitrary task deletion.

Every loader operation which accesses allocator metadata uses that mutex.
Startup initialization precedes task execution; final image/arena teardown is
single-controller work after the existing task and IRQ drain proof. Bounded
loader write/CRC chunks still retain full validation. The reviewed RUN probe
has its existing fixed code gate. Its pinned BSS check and reviewed instruction
execution stay outside the mutex; only the state transitions acquire it. This
is not permission to run arbitrary programs or release their live image pin.

The resident profile still treats entry to its idle task as fatal. Do not block
both workers simultaneously: idle has no admitted task-owned IRQ context. The
timeout proof keeps its holder runnable while the waiter blocks. General
application/WAD blocking must preserve a runnable control worker or first add
and validate idle-context ownership; this change does not silently expand that
registry.

The mutex does **not** mask interrupts across bulk operations. The heap pins
source/destination records before releasing the mutex for 1 KiB copy/clear
chunks. Other contexts may operate on different allocations. This does not
make a raw pointer safe to free from another context: cross-context pointer
transfer needs a separate explicit lease API. Neither namespace can free the
other namespace's allocation.

STOP prevents further worker iterations; busy calls finish or report failure
while keeping uncertain pins. The controller gains final-drain authority only
after both workers are done, both owned IRQ continuations are drained, stack
checks pass, and ISR/dispatch nesting is zero. It uses nonblocking acquisition
for final reclamation. A stale worker cannot enter after this transition.

## Opt-in proof

Command 8 starts worker 0's zeroed 64 KiB allocation, verifies it, and fills a
pattern. It deliberately holds the mutex for five ticks while remaining runnable so worker
1 can prove its two-tick timeout without stealing ownership. Recursive entry
is tested separately. Worker 1 then exercises its 6 MiB zone, resizing, OOM,
overflow and string duplication. Worker 0 resizes its buffer to 96 KiB and
checks the preserved data. Both retain patterned allocations (96 KiB + 64 KiB)
until the final STOP drain, alongside the incomplete loader image.

During the run worker 0 repeatedly validates the shared arena, checks 1 KiB of
its buffer outside the mutex, and attempts forbidden operations in worker 1's
namespace. A successful command 8 still returns `444c4942`.

Shared-only command 9 reads a frozen ten-word diagnostic snapshot; index 0
refreshes it. Words are magic `53484152`, proof phase (4 = complete), peer
checks, wrong-task rejection rounds, peer/owner mutex entries, maximum observed
successful wait ticks, maximum observed hold ticks, expected timeout count,
and recursive rejection count. The intentional five-tick hold is included;
this diagnostic is not a measurement of normal allocator latency or a
worst-case guarantee. Full ordinary upload replies remain unchanged.

The semaphore/mutex/thread-queue routines join the existing protected upper
loader code section. Linker bounds and the RAM audit still exclude BSS and
both guard regions; the protected-page checks include all relocated code.

## Verification and remaining work

`rtems/residentnet/test_doom_shared.py` exercises the actual target ownership
code with two native threads, a recursive mutex, ASan/UBSan and optionally
`SANITIZERS=thread`. It checks wrong-task/ISR admission, recursion, timeout,
concurrent namespaces, retained buffers, join-before-drain and stale-task refusal.
The normal heap tests retain STOP-during-copy, pin, corruption and OOM coverage.

`verify_upload.py --doom-heap --doom-shared` independently reconstructs and CRC
checks uploaded files, then replays commands with both native owners and exact
allocation/handle transitions. Asynchronous command-9 counter values are
validated separately against their captured report; ordinary replies remain
byte-for-byte checked (apart from the expected native base address). Network,
reserve, guard, task and IRQ audits are unchanged.

[Physical acceptance and exact artifacts](../../../artifacts/doom-shared-20261012/README.md)
record the tested build and results. This establishes a task ownership gate,
not a playable Doom port: a real application entry ABI, remaining libc/compiler
helpers, bounded WAD service and framebuffer/input integration are still needed.
