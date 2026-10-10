"""Validate the exact fixed RAM scratch upload/readback/restore capture."""
import argparse
import json
import re
import struct
from pathlib import Path

PATTERN=bytes.fromhex('4939363052414d211032547698badcfe')


def validate(path):
    text=(path/'result.txt').read_text()
    records=re.findall(r'complete op=([0-9a-f]+) id=([0-9a-f]+) status=([0-9a-f]+) changed=\d+ guard-changed=(\d+)',text)
    expected=['1c','20','20','20','20','1c','20','20','20','20','20','20','1c',
              '20','20','21','20','20','21','20','20','1c']
    if len(records)!=22 or 'experiment-result=0 pending=0' not in text or 'scratch-dirty=0' not in text:
        raise ValueError('incomplete or unrestored experiment')
    for i,((op,tag,status,guard),want) in enumerate(zip(records,expected),1):
        if op!=want or int(tag,16)!=i or int(status,16) or int(guard):
            raise ValueError('bad completion/status/guard')
    uploads=re.findall(r'submit op=21 id=(\d+) len=(\d+) offset=([0-9a-f]+)',text)
    if uploads!=[('16','16','00080010'),('19','16','00080010')]:
        raise ValueError('unexpected upload range or count')
    pairs={}
    for name in ['scratch-before','scratch-test','scratch-restored']:
        a=(path/(name+'-a5.bin')).read_bytes();b=(path/(name+'-5a.bin')).read_bytes()
        if len(a)!=64 or a!=b:raise ValueError('invalid paired '+name+' read')
        pairs[name]=a
    before=pairs['scratch-before'];after=pairs['scratch-test'];restored=pairs['scratch-restored']
    if before[16:32]==PATTERN:raise ValueError('write did not create an observable change')
    if after!=before[:16]+PATTERN+before[32:]:raise ValueError('wrong payload or surrounding damage')
    if restored!=before:raise ValueError('restoration mismatch')
    if (path/'upload-test.bin').read_bytes()!=PATTERN or (path/'upload-restore.bin').read_bytes()!=before[16:32]:
        raise ValueError('wrong captured upload buffers')
    for name in ['enquiry-before.bin','enquiry-after.bin']:
        b=(path/name).read_bytes()
        if len(b)!=512 or b[4:7]!=bytes([4,7,29]):raise ValueError('wrong firmware enquiry')
    if (path/'read-a5.bin').read_bytes()!=(path/'read-5a.bin').read_bytes() or (path/'read-a5.bin').read_bytes()!=struct.pack('<I',0xc0f2c000):
        raise ValueError('wrong verified pointer')
    return dict(ram_write_verified=True,original_region_restored=True,surrounding_bytes_unchanged=True,
                local_address='0xc0fac010',length=16,commands=22,pending=False,scratch_dirty=False,
                flash_programmed=False,code_execution=False,recovery_entered=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);a=p.parse_args()
    try:print(json.dumps(validate(a.capture),indent=2))
    except (ValueError,OSError) as e:p.error(str(e))
