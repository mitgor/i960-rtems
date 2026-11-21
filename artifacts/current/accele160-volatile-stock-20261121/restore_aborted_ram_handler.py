#!/usr/bin/env python3
"""Restore the blank stock loader page after an aborted, unexecuted RAM upload."""
import mmap
import os
from pathlib import Path
import struct

DEV = Path('/sys/bus/pci/devices/0000:37:09.1')
BASE, TABLE, LOADER = 0xc0000000, 0xc0023000, 0xc000e000


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def main():
    need(os.geteuid() == 0, 'root required')
    need((DEV / 'driver').resolve().name == 'myrsread', 'driver changed')
    host, = DEV.glob('host*/scsi_host/host*')
    need((host / 'stock_descriptor').read_text().strip() ==
         'state=0 status=0 residual=0', 'descriptor not idle')
    cfg = os.open(DEV / 'config', os.O_RDWR)
    barfd = os.open(DEV / 'resource0', os.O_RDWR | os.O_SYNC)
    bar = mmap.mmap(barfd, 8192, access=mmap.ACCESS_WRITE)
    def mapping(value):
        need(os.pwrite(cfg, struct.pack('<I', value), 0x44) == 4 and
             os.pread(cfg, 4, 0x44) == struct.pack('<I', value),
             'PIATVR mapping failed')
    try:
        need(os.pread(cfg, 4, 0) == bytes.fromhex('69105000'),
             'PCI identity changed')
        mapping(TABLE)
        need(struct.unpack_from('<I', bar, 4096 + 0x4fc)[0] == 0xc0023790,
             'stock dispatch was not restored')
        mapping(LOADER)
        bar[4096:8192] = b'\xff' * 4096
        need(bytes(bar[4096:8192]) == b'\xff' * 4096,
             'blank loader page restore failed')
    finally:
        mapping(BASE)
        bar.close()
        os.close(barfd)
        os.close(cfg)
    print('stock dispatch, loader RAM page, and PIATVR restored; no command sent')


if __name__ == '__main__':
    main()
