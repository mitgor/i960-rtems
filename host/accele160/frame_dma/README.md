# Reboot-only AcceleRAID framebuffer DMA targets

This module allocates two 77,824-byte coherent guarded buffers on the explicitly
selected AcceleRAID 160 at `0000:37:09.1` (`1069:0050`, subsystem `1069:0054`).
It requires the existing exact-card `myrsread` driver and bus mastering. It
never programs a DMA channel or issues a firmware command.

Build with `make` against the test host kernel. Root-only debugfs files under
`/sys/kernel/debug/accele-frame-dma` expose status, full buffer captures and
32-byte completion markers. Payload starts at byte 4,096 and spans 65,536
bytes; marker starts at 69,632. Prefix and suffix remain A5. A full capture is
one bounded pread, followed by marker, hash and guard verification by the
owning runner. Reading debugfs does not itself establish immutable ownership.

The module takes permanent references to itself and the selected driver.
Normal unload is deliberately denied. The buffers remain pinned through
userspace death, STOP and uncertain hardware completion. Reset the whole PC
before reclaiming them; do not force-unload. This design trades reclamation
for an unambiguous lifetime during initial qualification. It is not a generic
DMA allocator or a drop-in replacement for the old-card pin module.

The card side lives in `rtems/accele160/doom_dma`. Its exact-generation ACK,
source drain, completion-marker and full-audit protocol is mandatory.
