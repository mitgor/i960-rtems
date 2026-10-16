# Card system information on the IPv6 Vader page

2026-10-11: the running `autonet` page includes runtime uptime, RTEMS/lwIP
versions, CPU model, memory configuration, HTTP response/connection counts and
card-interface RX/TX/drop counters. Darth Vader and the IPv6 endpoint remain.
Refresh the page to update the snapshot; no background browser polling is added.

Uptime is RTEMS tick count / 100, from the existing nominal 100 Hz hardware timer.
It resets when the uploaded runtime is reloaded, not when Linux starts. The
32-bit tick counter wraps after about 497 days. HTTP and packet counters are also
32-bit. Configured capacities are explicitly distinguished from free memory.

CPU clock frequency is not measured by this implementation. The approximately
33.333 MHz value is the previously measured timer bus, not an asserted CPU clock.
CPU utilization/load average and card temperature are unavailable: this runtime
has neither idle-time accounting nor a known temperature-sensor interface. No
Linux-host CPU/load/temperature values are presented as card measurements.
Networking still passes through the host relay; these are card IP counters,
not physical NIC statistics. The separate preemption experiments are not the
production web runtime.

## Implementation and verification

`http.c` formats a fresh response into a fixed 4096-byte buffer and queues it
with `TCP_WRITE_FLAG_COPY`. The network loop is serialized, so a later response
can safely reuse the buffer. Overflow produces a bounded HTTP 500 response.
`system_info.h` needs no allocation, printf or floating point. The current page
is about 2.9 KiB, below the existing 4800-byte TCP send buffer. There is no new
BIO ABI, host request, sensor-register read or flash write.

Native ASan/UBSan tests cover maximum numeric values, uptime conversion and
sentinel-filled small-buffer truncation. Existing network tests and the full
RTEMS suite pass. On-card acceptance passed 24 HTTP requests, including split
headers, invalid POST and oversized headers. Separate public IPv6 requests
observed uptime rise from 5 to 40 seconds and HTTP page responses from 1 to 24,
with increasing RX/TX and zero drops. Full close/RAM restoration and module
unload passed, followed by a production restart with the new image.

`serve-autonomous.sh` now defaults to `autonet-module-system-info/dac960auto.ko`.
The module is pinned to the exact uploaded image. Both payload and module can
be overridden with `I960_AUTONOMOUS_PAYLOAD` and `I960_AUTONOMOUS_MODULE`; they
must match. The previous image remains at `autonet-vader-before-system-info/`
on the established host, with its old `autonet-module-vader/` module, for rollback.

[Preserved binaries, checks and response samples](../../artifacts/notes/rtems-system-info-20261011.md).
