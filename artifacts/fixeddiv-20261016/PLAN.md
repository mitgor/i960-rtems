# FixedDiv experiment, declared before hardware measurement

Compare the latest fixed-column low-detail baseline plus call-site timing with
the same build plus exact bounded unsigned `ediv`. A/B/B/A, 520 frames each,
frames 100–499 timing window, full paired audits and unchanged ownership checks.
Both builds carry identical per-call profiling and bounded differential tests;
FPS is for instrumented builds, not a claim about uninstrumented speed.
Every call site reports count and timer-0 elapsed ticks. Includes timer read,
call overhead, interrupts and preemption; not pure task CPU cycles. Timer is
nominally 4,166,700 Hz. A back-to-back read calibration is reported separately.
No approximate division. Preserve original INT_MIN behavior via legacy fallback;
INT_MIN/zero is undefined in the original and deliberately not executed.
Candidate is opt-in. Full all-run pixel/palette comparison remains strict.

Intel Rx developer manual describes unsigned ediv and remainder/quotient ordering:
https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF
