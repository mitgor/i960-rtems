# New-card Doom memory admission gate

`survey_upper.sh` uses the existing read-only `mmio_snapshot.c` helper to
sample BAR0's translated odd pages under the global card lock. It checks the
exact AcceleRAID BDF, `myrsread` with explicit `read_bdf`, the idle stock
descriptor, absence of retained test modules, and the old card's unbound
state. It restores PIATVR after each sample and at exit. Run only on the
qualified 80303 AcceleRAID profile; a zero or stable snapshot confers no
memory ownership.

`assess.py` replays the captured pages, checks all 512 stock allocator
count/owner words between rounds, scans the exact firmware image for aligned
upper-bank literals and validates two post-survey full-flash read records. It
deliberately returns `admitted: false` while the proposed 8 MiB arena lies
outside the stock owner table. It does not issue a card command or a DRAM
write. The [physical evidence and next handoff](../../../artifacts/current/accele160-doom-arena-20261017/README.md)
describe the accepted read-only result.
