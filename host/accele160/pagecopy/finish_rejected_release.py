#!/usr/bin/env python3
"""Finish a fully completed rejected-copy release after exact state checks."""
import mmap
from pathlib import Path
import struct

cap = Path('/home/mit/i960-accele160-pagecopy-20261016/pagecopy-bad-index')
base = Path('/sys/bus/pci/devices/0000:37:09.1')
dbg = Path('/sys/kernel/debug')
def fields(name):
    return dict(x.split('=', 1) for x in (dbg/f'accele-{name}/status').read_text().split())
def need(ok, why):
    if not ok: raise RuntimeError(why)
need(fields('copy')['status'] == '2' and fields('copy')['released'] == '1', 'copy state')
need(fields('release')['done'] == '1' and fields('release')['status'] == '0' and fields('release')['residual'] == '0', 'release state')
with (base/'config').open('r+b',buffering=0) as cfg, (base/'resource0').open('r+b',buffering=0) as res:
    bar=mmap.mmap(res.fileno(),8192)
    cfg.seek(0x44); original=struct.unpack('<I',cfg.read(4))[0]
    need(original==0xc0000000,'PIATVR state')
    def snap(addr):
        cfg.seek(0x44);cfg.write(struct.pack('<I',addr))
        cfg.seek(0x44);need(struct.unpack('<I',cfg.read(4))[0]==addr,'PIATVR readback')
        return bytes(bar[4096:8192])
    try:
        before=(cap/'page-before.bin').read_bytes()
        page=snap(0xc000e000)
        need(page[0x820:0x828]==b'FREEQ\x10\x16\x16','release result')
        need(struct.unpack_from('<I',page,0x828)[0]==0xc0710000,'released pointer')
        expected=bytearray(before);expected[0x820:0x830]=page[0x820:0x830]
        need(page==expected,'page differs outside result')
        table=snap(0xc0384000); old=(cap/'table-before.bin').read_bytes()
        need(table[0x2a0:0xaa0]==old[0x2a0:0xaa0],'metadata restoration')
        stage=snap(0xc078e000)
        need(stage==(cap/'staging-before.bin').read_bytes(),'staging restoration')
        snap(0xc000e000);bar[4096+0x820:4096+0x830]=before[0x820:0x830]
        need(snap(0xc000e000)==before,'page restoration')
    finally:
        cfg.seek(0x44);cfg.write(struct.pack('<I',original));bar.close()
(dbg/'accele-release/release').write_text('release\n')
need(fields('release')['released']=='1','release companion')
print('bad-index cleanup passed; grant freed; owner/page/staging restored')
