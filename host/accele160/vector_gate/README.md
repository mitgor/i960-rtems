# AcceleRAID 160 cached-vector and timer-mode gate

Operation 12 extends the accepted operation-11 handler by a single bounded
observation. Intel's 80303 Developer's Manual, Table 8-7, maps cached
vector 18 to internal data RAM `0x04` and vector 130 to `0x20`. The handler
reads those words twice. It also samples timer-1 reload/count, IPND, IMSK
and IMAP2. Only if two sets of checks show zero reload/count, no pending
timer-1 interrupt, the timer-1 mask clear, and timer-1 mapping field zero
does it read TMR1 mode at `ff000318`. Reading that register clears its
terminal-count status by hardware design; the report preserves the value
seen on that first read. No timer/vector/mask/cache register is written.

The 3,868-byte [handler](handler.S) fits the retained 4 KiB code slot and
has no relocations. Its last 244 bytes occupy `c000f000..c000f0f3`, so
the host saves that exact code prefix plus the erased remainder of the
`f000..ffff` page. The report is separate at `c000f980..c000f9c7`.
The first physical harness preflight assumed the whole page was erased and
stopped before loading a command module. The corrected [harness](run_vector.py)
pins the linked handler SHA-256 and checks the exact 244-byte prefix before
running. It restores the full page and PCI aperture after completion and
compares all 512 allocator count/owner records. The one-shot Linux
companion is [vector_command.c](vector_command.c). Do not force-unload it if
the callback has not returned.

The [accepted card result](../../../artifacts/current/accele160-vector-20261017/README.md)
is: cached vector 18 `0xaaaaaaaa`, cached vector 130 `0xc0000418`, and
timer-1 mode `0x00000000` after all guards passed. Timer-1 pending,
mask, mapping, reload and count were unchanged before/after. This does
not grant vector 18 or timer 1: the vector-18 cache contains a sentinel,
not the zero ROM word, and the timer-1 mapping field is still zero.
The existing operation-11 STOP was also retested on this firmware, including
wrong-token and no-host deadline cases. Six complete flash reads, owner/page
restoration, and [offline replay](verify_live.py) passed. The latter rejected
three altered captures. The exact candidate SHA-256 is
`93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094`.

The isolated remote workspace is `/home/mit/i960-accele160-vector-20261017`.
For a fresh run, require two same-boot guarded full-flash reads of the exact
candidate, unbound old DAC960PG and idle stock descriptor, then pass the
linked `handler.bin`, module, candidate and both read directories to
`run_vector.py`. Follow with another full read and independent replay.
See [old/new bring-up differences](../../../rtems/accele160/OLD-NEW-DIFFERENCES.md)
for why this one-shot experiment used another flash cycle and how a reusable
RAM admission layer will eliminate that for subsequent probes.
