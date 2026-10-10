"""Validate the fixed, read-only C0120000 observation; occupancy is not ownership."""
import argparse
import json
import re
import struct
from pathlib import Path


def validate(path):
    log = (path / 'result.txt').read_text()
    records = re.findall(
        r'complete op=([0-9a-f]+) id=([0-9a-f]+) status=([0-9a-f]+) '
        r'changed=\d+ guard-changed=(\d+)', log)
    expected = ['1c', '20', '20', '20', '20', '1c', '20', '20',
                '20', '20', '20', '20', '1c', '20', '20']
    if len(records) != len(expected) or 'experiment-result=0 pending=0' not in log:
        raise ValueError('incomplete fixed observation')
    if 'OBSERVED hook-site local=c0120000 length=64' not in log:
        raise ValueError('wrong observation mode')
    for i, ((op, tag, status, guard), want) in enumerate(zip(records, expected), 1):
        if op != want or int(tag, 16) != i or int(status, 16) or int(guard):
            raise ValueError('bad completion/status/guard')
    submits = re.findall(r'submit op=20 id=(\d+) len=(\d+) offset=([0-9a-f]+)', log)
    if submits[-2:] != [('14', '64', 'ff1f4000'), ('15', '64', 'ff1f4000')]:
        raise ValueError('unexpected hook read address or length')
    for name, size in [('read', 4), ('control', 512), ('code', 16),
                       ('globals', 8), ('board', 512), ('dram-hook', 64)]:
        a = (path / f'{name}-a5.bin').read_bytes()
        b = (path / f'{name}-5a.bin').read_bytes()
        if len(a) != size or a != b:
            raise ValueError('bad paired ' + name)
        if name == 'dram-hook': hook = a
        if name == 'read' and a != struct.pack('<I', 0xc0f2c000):
            raise ValueError('wrong staging pointer')
        if name == 'code' and a != bytes.fromhex('061e805c5c2700090030f082985d0ac0'):
            raise ValueError('wrong stock entry')
        if name == 'globals' and a != struct.pack('<II', 0xc0110780, 0xc1000000):
            raise ValueError('wrong runtime globals')
        if name == 'board':
            for offset, value in {8: 0x80000, 12: 0xfef80000,
                                  0xe0: 0xc004ce90, 0xe4: 0xc004ced0,
                                  0xec: 0xc004cf80, 0x124: 0x739,
                                  0x128: 0xec0000}.items():
                if struct.unpack_from('<I', a, offset)[0] != value:
                    raise ValueError('wrong board geometry or callback')
    for name in ['enquiry-before.bin', 'enquiry-after.bin']:
        b = (path / name).read_bytes()
        if len(b) != 512 or b[4:7] != bytes([4, 7, 29]):
            raise ValueError('wrong firmware profile')
    return dict(dram_hook_observed=True, address='0xc0120000', bytes=64,
                zero_bytes=hook.count(0), nonzero_bytes=64 - hook.count(0),
                commands=15, pending=False, exclusive_ownership_proven=False,
                code_execution=False, flash_programming=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    try: print(json.dumps(validate(args.capture), indent=2))
    except (OSError, ValueError) as error: parser.error(str(error))
