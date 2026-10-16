# Input-consumption trace and default exact divide

Make the previously qualified exact divide default for private playable engines
and the public play builder; retain `--no-fast-fixed-div` for the original.
Non-play compile/inventory builds keep the original by default.

Optional `--input-trace` records bounded key dequeue, pre-menu responder and
post-menu responder events with sequence, next display generation, gametic,
maketic, key/down and menu state. Per-frame versioned trailer has 16 event slots,
explicit cumulative overflow and strict padding. Overflow fails replay; no
silent loss. It cannot share the trailer with FixedDiv profiling. It changes
neither input scheduling nor ownership. Host submissions record timestamps and
observed frame, including unsuccessful queue submissions.

A/B/B/A: default exact divide without trace versus the same build with trace;
520 frames/run, fixed low detail, full paired audits and ownership checks,
held-slot stall, held STOP, heap drain and all replay/tamper tests. Measure
100–499 with no outlier removal, compare all images and native first 52 frames.
Match successful host input submissions to every dequeue and responder event;
report actual consuming frame/tic and compare repetitions. Historical captures
without this trace cannot retrospectively prove the old menu discrepancy's cause.
No claims of diagnosing that particular run without evidence.
Save exact captures/binaries locally before reboot and restore public IPv6 HTTP.
