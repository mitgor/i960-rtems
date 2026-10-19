# Idle-zone reclamation and cancellation boundary

The next available memory is the retired Doom zone at `c08ebbd0`, exactly
6,291,456 bytes, within the already qualified upper arena. This is reuse of owned
memory, not evidence that another stock-firmware range is safe. The existing
128 KiB heap and 384 KiB module partition retain their locations. RTEMS workspace
and task/interrupt stacks retain their previous sizes.

`ar_loan_attach` requires an exact live parent handle/size, one existing pin,
valid guards and a newer nonzero owner token. It adds a second parent pin and
initializes a guarded child arena inside the zone. The original Doom reservation
is never freed. The runtime host already excludes game restart after application
admission; the card additionally checks idle, engine-not-running and no zone
loan to Doom. These gates must remain together.

The child offers allocation, pin, unpin, free, owner cancellation and release.
Cancellation revokes new allocation/pin operations and marks every live child
cancelled. Existing references may complete/unpin. Free refuses outstanding
pins; loan return refuses every live child allocation, including unpinned ones.
Guard corruption poisons the loan and retains the parent. Owner tokens increase
across reattachment, preventing stale child handles from becoming valid with a
recreated arena. All operations require serialization outside IRQ context.

Wire operation 9 takes one LE word: 0 attaches, 1 advances the destructive
qualification, 2 returns the drained loan, 3 reports its phase. Qualification
allocates `6 MiB - 32` bytes, pins it twice, writes and verifies a position-dependent
pattern in at most 64 KiB per call, and cancels after the write pass. New access,
free, parent return and module close must refuse. Completion of just one pin
still cannot free the block. The second completion permits free, then parent
return. Exactly 192 successful steps reach phase 3. A failed test retains memory.
`qualify_loan.py` preserves every response and observed RPC latency.

This is a kernel heap API and qualification transport. The loaded module ABI
still has no import table through which applications can call it. It is not yet
an RTEMS workspace extension or a malloc replacement. Six MiB reclaimed does
not mean total physical ownership increased beyond the existing upper bank.

## Why unrestricted task cancellation is not claimed

The current module runs on Init, which also handles application RPC. A module
that never returns can block that channel. The console worker is independent,
but it does not prove that the module has stopped touching shared data. The
owned timer ISR explicitly maps four thread identities to four save areas
(`doom_dma/timer_isr.S`). Adding a fifth thread without changing that mapping
would enter the unknown-thread path. Deleting Init would also destroy the
supervisor and invalidate its retained execution context.

Cancellation of an owner is therefore revocation, not fabricated completion.
The two-reference proof exercises safe resource retention, not arbitrary task
termination. Trusted code can still corrupt memory or disable interrupts.

The next implementation gates are:

1. Give application execution its own RTEMS task and owned IRQ/terminal context;
   keep command reception and epoch/timeout ownership on a separate supervisor.
2. Publish requests/completions through bounded mailboxes with distinct invocation
   and task-generation identities. Prove all existing four contexts still work.
3. Track resource kind and owner: private allocation, shared reference, lock,
   DMA descriptor, and firmware continuation. Record acquisitions atomically with
   cancellation admission so no reference can arrive after revocation.
4. First test asynchronous suspension of an interrupt-enabled pure computation,
   retaining its stack, module and resources. Do not free on timeout alone.
5. Permit reclamation only after verified task/IRQ unwinding and all reference
   completions. Shared locks or outstanding DMA require a specific recovery
   action; uncertainty retains the whole dependency set until reboot.
6. Exercise nested RTEMS critical sections, two owners of one allocation, held
   locks, active/stalled DMA, fault/NMI and concurrent disconnect/STOP. Report
   each supported class explicitly instead of calling arbitrary deletion safe.

The separate hardware gate remains SXP/DMA stop/drain plus firmware allocation
and alias analysis before reclaiming stock ranges toward 10–12 MiB. Profile 19
observations do not satisfy it. Stock-firmware coexistence remains a future path.
