# AcceleRAID 160 cached-vector and timer-1 mode acceptance

Status, 2026-10-17: **bounded operation 12 passed on the card**. The live
cached vector-18 word is `0xaaaaaaaa`, not the zero value in the stock ROM
interrupt table. Cached vector 130 is `0xc0000418`, matching the ROM timer-0
entry. Under two sets of idle/masked timer-1 guards, the first TMR1 mode
read returned `0x00000000`; it was disabled and its terminal-count flag was
clear. IPND `0`, IMSK `0x10c7`, IMAP2 `0x00080000`, timer-1 reload `0`,
and timer-1 count `0` were unchanged before and after. The mode read can
clear terminal-count status by design, so this result is an observation
under guarded conditions, not a generic non-destructive register read.
Neither timer/vector/interrupt-stack ownership nor an RTEMS clock is proved.

The [source and procedure](../../../host/accele160/vector_gate/README.md)
preserve fixed operations 1–11. The linked 3,868-byte
[handler](build/handler.bin) has SHA-256
`dd4d51c24ef1debcbc1dc4830c0761696be94849082965146445f38e2662c52f`
and no relocations. The [1 MiB candidate](candidate.bin) has SHA-256
`93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094`.
The [offline audit](../../../host/accele160/vector_gate/audit.py) found
3,277 changed bytes confined to the retained loader cave and two checksum
words; the decompressed runtime, boot block and loader return hook were
unchanged. Five one-byte input mutations were rejected. The exact Linux
command module SHA-256 is
`a4309b14e1a5cb36558b1bb96c267f251e9974603beffbddc4ee2188f931a280`;
the [ELF, module, build header and relocation output](build/) are saved.

The [preflash full read](live/preflash-read/result.json) matched the prior
STOP-gate image SHA-256
`ef5635d38bf397ff13fa1140ef6265de0b300c70ad8b157c17427013a1d2abb5`.
[STOREIMAGE](live/stage/result.json) and an [independent full staged
readback](live/staged-readback/result.json) matched the candidate with zero
status, residual and DMA-guard changes. [FLASHIMAGE](live/flash/result.json)
completed with status/residual zero in 36.90 s. The host boot ID changed
from `76a93df2-6deb-4cea-a704-c9ae152a5f5f` to
`d88a2742-e903-4513-94a1-13e534b5e2cd`. Two independent
[postboot](live/persistent-0/result.json) [full reads](live/persistent-1/result.json)
matched the candidate byte for byte, with zero guard changes.

The [first host preflight](live/vector-preflight-failed/) stopped before
loading the one-shot command module. It had assumed an all-`0xff` saved
`f000..ffff` page, but the new handler extends 244 bytes into its start.
Those bytes exactly matched the pinned linked handler tail and the
remaining page was erased. The corrected harness required that exact
preimage. The [single op-12 card call](live/vector-run/result.json) then
returned status/residual `0/0` and the report above. It restored the full
page and PIATVR, and all 512 allocator count/owner records matched.
Stock-active bytes `0xaa0..0xaa1` of the owner page changed outside those
records, as in previous gates. A [post-call full flash read](live/postcall-flash/result.json)
again matched the candidate.

Because the handler grew, the accepted [operation-11 STOP](live/stop-compat/result.json)
was repeated on this exact firmware. Stale STOP stayed pending; valid STOP
returned ACK/status 0 in a 21.6 ms host-observed cycle; absent STOP returned
stock status 2 after 10.26 s. Both calls restored the page and owner
records, and a [sixth full flash read](live/postcompat-flash/result.json)
still matched the candidate. The [final host state](live/final-state.txt)
shows PIATVR `c0000000`, idle stock descriptor, only new-card `myrsread`
bound, old DAC960PG `37:04.1` unbound and no test companion retained.

[Independent replay](../../../host/accele160/vector_gate/verify_live.py)
validated all six complete reads, stage/flash receipts, exact report,
bounded page/owner state and STOP compatibility. It rejected mutations to
the cached vector report, a byte outside the report, and an owner word.
The internal vector-address mapping and TMR1 read-clear semantics come from
the [Intel 80303 I/O Processor Developer's Manual](https://bitsavers.trailing-edge.com/components/intel/i960/273353-001_Intel_80303_IO_Processor_Developers_Manual_May2000.pdf),
Table 8-7 and section 18.1.1.1. A `0xaaaaaaaa` cached vector is not an
owned interrupt handler; future timer work must reserve an unused mapping,
install an owned vector and stack, and restore the original cache word and
all borrowed registers after STOP and drain.
