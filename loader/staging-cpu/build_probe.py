#!/usr/bin/env python3
"""Build sources for one fixed CPU CRC rehearsal, without accessing hardware."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import zlib

ROOT=Path(__file__).resolve().parents[2]
CANDIDATE_SHA='a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0'

def build(binary,out):
    candidate=(ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin').read_bytes()
    assert hashlib.sha256(candidate).hexdigest()==CANDIDATE_SHA
    crc=zlib.crc32(candidate)
    code=binary.read_bytes()
    assert hashlib.sha256(code).hexdigest()=='fb5c38ad5723deb7d4490963d9dc3b30313656e0c35ff10a6e75965ba8cb3a59'
    assert len(code)==128
    assert code[8:12] == bytes.fromhex('00c0f2c1')
    assert code[0x5c:0x60] == crc.to_bytes(4,'little')
    assert code[-4:] == bytes.fromhex('00500484')
    out.mkdir(parents=True,exist_ok=True)
    for name in ['dac960dump.c','Makefile','staging_pointer.h','ram_scratch.h','rom_exec.h','stage_data.h','stage_rehearsal.h']:
        shutil.copyfile(ROOT/'host/dump'/name,out/name)
    p=out/'rom_exec.h';s=p.read_text()
    s=s.replace('#define EXEC_REGION_SIZE 64u','#define EXEC_REGION_SIZE 128u')
    s=s.replace('#define EXEC_FLASH_SIZE 36u','#define EXEC_FLASH_SIZE 128u')
    s,n=re.subn(r'static const unsigned char exec_flash_code\[EXEC_FLASH_SIZE\] = \{.*?\};',
                'static const unsigned char exec_flash_code[EXEC_FLASH_SIZE] = {\n'+
                ','.join(f'0x{x:02x}' for x in code)+'\n};',s,flags=re.S)
    assert n==1
    s='/* CPU CRC probe variant: EXEC_FLASH names are inherited slot names.\n * Both code sites are RAM; second probe reads the staging alias, not flash. */\n'+s
    p.write_text(s)
    p=out/'stage_rehearsal.h';s=p.read_text();old='    rc = stage_read_pair(d, 2, stage_candidate_sha256, "candidate");'
    assert s.count(old)==1
    s=s.replace(old,old+'''\n    if (!rc) rc = run_rom_exec(d);
    if (d->pending || d->exec_dirty) goto done;''')
    p.write_text(s)
    p=out/'dac960dump.c';s=p.read_text().replace('#define WAIT_US 2000000u','#define WAIT_US 10000000u')
    s=s.replace('VERIFIED post-startup callx to mapped stock flash RET returned status=017f',
                'VERIFIED CPU CRC32 of full candidate through C1F2C000 equals 2012d01f; status=017f')
    s=s.replace('    if (strcmp(pci_name(pdev), bdf)) return -ENODEV;',
                '    if (strcmp(pci_name(pdev), bdf)) return -ENODEV;\n    if (!stage_check) return -EINVAL; /* fixed combined rehearsal only */')
    p.write_text(s)
    (out/'start.s').write_text((ROOT/'loader/staging-cpu/start.s').read_text().replace('EXPECTED_CRC',hex(crc)))
    shutil.copyfile(ROOT/'loader/staging-cpu/link.ld',out/'link.ld')
    print(f'Prepared fixed 128-byte CPU probe; candidate CRC32={crc:08x}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();build(a.binary,a.out)
