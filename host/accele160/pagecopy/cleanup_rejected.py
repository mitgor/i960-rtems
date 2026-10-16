#!/usr/bin/env python3
"""Resume an interrupted rejected-copy session only after exact-state checks."""
import argparse
import mmap
from pathlib import Path
import struct

BDF = Path('/sys/bus/pci/devices/0000:37:09.1')
DBG = Path('/sys/kernel/debug')
PAGE = 4096


def fields(name):
    return dict(s.split('=', 1) for s in (DBG / f'accele-{name}/status').read_text().split())


def require(condition, label):
    if not condition:
        raise RuntimeError(label)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('capture', type=Path)
    a = parser.parse_args()
    data = lambda name: (a.capture / name).read_bytes()
    with (BDF / 'config').open('r+b', buffering=0) as cfg, (BDF / 'resource0').open('r+b', buffering=0) as resource:
        bar = mmap.mmap(resource.fileno(), PAGE * 2)
        original = struct.unpack('<I', (cfg.seek(0x44), cfg.read(4))[1])[0]
        require(original == 0xc0000000, 'unexpected PIATVR')
        def translate(addr):
            cfg.seek(0x44); cfg.write(struct.pack('<I', addr))
            cfg.seek(0x44); require(struct.unpack('<I', cfg.read(4))[0] == addr, 'PIATVR readback')
        def snap(addr):
            translate(addr)
            return bytes(bar[PAGE:2*PAGE])
        def put(addr, off, buf):
            translate(addr)
            bar[PAGE+off:PAGE+off+len(buf)] = buf
            require(bytes(bar[PAGE+off:PAGE+off+len(buf)]) == buf, 'write readback')
        try:
            require(fields('reserve')['released'] == '1', 'reserve not released')
            require(fields('copy')['status'] == '2' and fields('copy')['released'] == '0', 'copy state')
            require(fields('release')['started'] == '0', 'release already started')
            before, reserved = data('page-before.bin'), data('page-reserved.bin')
            grant = struct.unpack_from('<I', reserved, 0x828)[0]
            require(grant == 0xc0710000, 'unexpected grant')
            current = snap(0xc000e000)
            rejected = data('page-rejected.bin')
            require(current[:0x820] == rejected[:0x820] and current[0x830:0x860] == rejected[0x830:0x860] and current[0x870:] == rejected[0x870:], 'rejected page drift outside controls')
            require(current[0x820:0x830] in (rejected[0x820:0x830], before[0x820:0x830]) and current[0x860:0x870] in (rejected[0x860:0x870], before[0x860:0x870]), 'unexpected control state')
            require(snap(grant + 0x7e000) == data('staging-pattern.bin'), 'staging drift')
            require(snap(0xc0384000)[0x2a0:0xaa0] == data('table-reserved.bin')[0x2a0:0xaa0], 'grant drift')
            put(0xc000e000, 0x860, before[0x860:0x870])
            put(0xc000e000, 0x820, before[0x820:0x830])
            expected = bytearray(reserved); expected[0x820:0x830] = before[0x820:0x830]
            require(snap(0xc000e000) == expected, 'page restoration mismatch')
            put(grant + 0x7e000, 0, data('staging-before.bin'))
            require(snap(grant + 0x7e000) == data('staging-before.bin'), 'stage restore mismatch')
            require(snap(0xc0384000)[0x2a0:0xaa0] == data('table-reserved.bin')[0x2a0:0xaa0], 'metadata changed')
            translate(original)
            (DBG / 'accele-copy/release').write_text('release\n')
            require(fields('copy')['released'] == '1', 'copy companion not released')
            put(0xc000e000, 0x820, bytes([0xa5])*16)
            translate(original)
            (DBG / 'accele-release/start').write_text('probe\n')
            require(fields('release')['done'] == '1' and fields('release')['status'] == '0', 'release failed')
            page_after = snap(0xc000e000)
            require(page_after[0x820:0x828] == b'FREEQ\x10\x16\x16', 'release result')
            require(snap(0xc0384000)[0x2a0:0xaa0] == data('table-before.bin')[0x2a0:0xaa0], 'metadata not restored')
            put(0xc000e000, 0x820, before[0x820:0x830])
            require(snap(0xc000e000) == before, 'loader page not restored')
            translate(original)
            (DBG / 'accele-release/release').write_text('release\n')
            require(fields('release')['released'] == '1', 'release companion not released')
            print('rejected_session_cleanup=passed grant=c0710000 metadata_restored=1 page_restored=1 PIATVR=c0000000')
        finally:
            translate(original)
            bar.close()


if __name__ == '__main__':
    main()
