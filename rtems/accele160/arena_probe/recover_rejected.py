#!/usr/bin/env python3
"""Release only the completed, read-only upper-bank rejection (status 2)."""
import fcntl
import hashlib
import mmap
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'host/accele160/lease_probe'))
from run_lease import BDF, OLD, PAGE, DEVICE, DEBUG, need, status, release, command
sys.path.insert(0, str(ROOT/'rtems/transport'))
from card_select import select

IMAGE = '25bdc7df178a14dc39ec2a277e972fea7eb53df4ee5e2d897e4d5982da3279d9'


def main():
    root = Path(sys.argv[1])
    build = root.parent/'build/image.bin'
    need(hashlib.sha256(build.read_bytes()).hexdigest() == IMAGE, 'wrong image')
    lock = open('/run/lock/i960-loadrun.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state = status('ram-admit')
    need(state.get('started') == '1' and state.get('done') == '1' and
         state.get('status') == '2' and state.get('residual') == '0' and
         state.get('released') == '0', 'not the completed rejected admission')
    need(status('release').get('started') == '0', 'release already started')
    need(select(BDF, 'accele160', driver='myrsread')['bdf'] == BDF and
         select(OLD, 'dac960pg')['driver'] is None, 'card selection')
    before = (root/'page-before.bin').read_bytes()
    reserved = (root/'page-reserved.bin').read_bytes()
    owned = (root/'owner-reserved.bin').read_bytes()
    rejected = (root/'stop/ready-page.bin').read_bytes()
    need(len(before) == len(reserved) == len(owned) == len(rejected) == PAGE,
         'snapshot lengths')
    need(struct.unpack_from('<16I', rejected, 0xb00) ==
         (0x314b4e42, 2, 1, 0x800000) + (0,)*12 and
         struct.unpack_from('<I', rejected, 0xa7c)[0] == 0xf0071001,
         'not the no-write bank gate')
    cfg = (DEVICE/'config').open('r+b', buffering=0)
    res = (DEVICE/'resource0').open('r+b', buffering=0)
    bar = mmap.mmap(res.fileno(), 2*PAGE)
    cfg.seek(0x44)
    original = struct.unpack('<I', cfg.read(4))[0]
    need(original == 0xc0000000, 'PIATVR changed')

    def translate(addr):
        cfg.seek(0x44)
        cfg.write(struct.pack('<I', addr))
        cfg.seek(0x44)
        need(struct.unpack('<I', cfg.read(4))[0] == addr, 'PIATVR readback')

    def snap(addr):
        translate(addr)
        return bytes(bar[PAGE:2*PAGE])

    def write(addr, off, value):
        translate(addr)
        bar[PAGE+off:PAGE+off+len(value)] = value
        need(bytes(bar[PAGE+off:PAGE+off+len(value)]) == value,
             'PCI writeback')

    ptr = struct.unpack_from('<I', reserved, 0x828)[0]
    need(ptr == 0xc0710000 and snap(0xc000e000) == rejected and
         snap(0xc0384000)[0x2a0:0xaa0] == owned[0x2a0:0xaa0] and
         snap(ptr+0x7e000) == (root/'stage-before.bin').read_bytes() and
         snap(0xc0f00000) == (root/'upper-before.bin').read_bytes() and
         snap(0xc0010000) == (root/'stock-before.bin').read_bytes(),
         'completed call differs from saved page/owner/stage/DRAM')
    indices = [1+32*i for i in range(64)] + [2047]
    samples = b''.join(snap(0xc0800000+i*PAGE-PAGE) for i in indices)
    need(samples == (root/'samples-before.bin').read_bytes(),
         'upper-bank samples changed')
    (root/'samples-rejected.bin').write_bytes(samples)
    try:
        for lo, hi in ((0xa00,0xa20),(0xa20,0xa3c),(0xa40,0xa60),
                       (0xa60,0xa80),(0xa80,0xaa0),(0xb00,0xb40)):
            write(0xc000e000, lo, before[lo:hi])
        need(snap(0xc000e000) ==
             reserved[:0x820] + before[0x820:0x830] + reserved[0x830:],
             'loader page restoration under grant')
        translate(original)
        release('ram-admit', 'admit')
        write(0xc000e000, 0x820, b'\xa5'*16)
        translate(original)
        command('release', root)
        end = snap(0xc000e000)
        need(struct.unpack_from('<4I', end, 0x820) ==
             (0x45455246,0x16161051,ptr,0x80000), 'grant release')
        need(snap(0xc0384000)[0x2a0:0xaa0] ==
             (root/'owner-before.bin').read_bytes()[0x2a0:0xaa0],
             'all 512 owner/count words restored')
        write(0xc000e000, 0x820, before[0x820:0x830])
        need(snap(0xc000e000) == before, 'final loader page')
        translate(original)
        release('release', 'release')
        subprocess.run(['rmmod','copy_command'], check=True)
        subprocess.run(['rmmod','digest_command'], check=True)
        (root/'host-recovery.txt').write_text(
            'Read-only bank rejection; exact page, grant, stage, sampled DRAM '
            'and owner restored after completed status-2 admission.\n')
    finally:
        translate(original)
        bar.close()
        res.close()
        cfg.close()


if __name__ == '__main__':
    main()
