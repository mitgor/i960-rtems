"""Validate the exact thirteen-command read-only runtime audit capture."""
import argparse
import json
import re
import struct
from pathlib import Path


def validate(path):
    text = (path/'result.txt').read_text()
    completions = re.findall(r'complete op=([0-9a-f]+) id=([0-9a-f]+) status=([0-9a-f]+) changed=\d+ guard-changed=(\d+)', text)
    expected = ['1c','20','20','20','20','1c','20','20','20','20','20','20','1c']
    if len(completions)!=13 or 'experiment-result=0 pending=0' not in text:
        raise ValueError('missing successful complete experiment')
    for i, ((op, tag, status, guard), want) in enumerate(zip(completions, expected), 1):
        if op!=want or int(tag,16)!=i or int(status,16) or int(guard):
            raise ValueError('invalid completion sequence/status/guard')
    reads={}
    for name,size in [('read',4),('control',512),('code',16),('globals',8),('board',512)]:
        a=(path/(name+'-a5.bin')).read_bytes(); b=(path/(name+'-5a.bin')).read_bytes()
        if len(a)!=size or a!=b: raise ValueError('invalid paired '+name+' read')
        reads[name]=a
    if reads['read']!=struct.pack('<I',0xc0f2c000): raise ValueError('wrong staging pointer')
    if reads['code']!=bytes.fromhex('061e805c5c2700090030f082985d0ac0'): raise ValueError('wrong code')
    if reads['globals']!=struct.pack('<II',0xc0110780,0xc1000000): raise ValueError('wrong board/alias')
    fields={hex(o):struct.unpack_from('<I',reads['board'],o)[0] for o in
            [8,12,16,0xcc,0xd0,0xd4,0xd8,0xdc,0xe0,0xe4,0xe8,0xec,0xf0,0xf4,0x124]}
    for offset,value in {8:0x80000,12:0xfef80000,16:0xfeff9c00,0xe0:0xc004ce90,
                         0xe4:0xc004ced0,0xe8:0xc004d6d0,0xec:0xc004cf80}.items():
        if fields[hex(offset)]!=value: raise ValueError('wrong board profile/callback')
    for name in ['enquiry-before.bin','enquiry-after.bin']:
        b=(path/name).read_bytes()
        if len(b)!=512 or b[4:7]!=bytes([4,7,29]): raise ValueError('wrong enquiry')
    return dict(runtime_reads_verified=True,commands=13,pending=False,
                staging_base='0xc0f2c000',board='0xc0110780',alias='0xc1000000',
                board_fields={o:hex(v) for o,v in fields.items()},
                ram_upload=False,code_execution=False,recovery_entry=False,flash_programming=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path)
    args=p.parse_args()
    try: print(json.dumps(validate(args.capture),indent=2))
    except (OSError,ValueError) as e: p.error(str(e))
