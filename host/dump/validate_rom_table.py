"""Validate the fixed live read of the stock opcode-0x6f dispatch word."""
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
        raise ValueError('incomplete fixed table observation')
    if 'VERIFIED stock opcode-6f table word local=c001f9bc value=c001fe98' not in log:
        raise ValueError('wrong table observation mode')
    for i, ((op, tag, status, guard), want) in enumerate(zip(records, expected), 1):
        if op != want or int(tag, 16) != i or int(status, 16) or int(guard):
            raise ValueError('bad completion/status/guard')
    submits = re.findall(r'submit op=20 id=(\d+) len=(\d+) offset=([0-9a-f]+)', log)
    if submits[-2:] != [('14', '4', 'ff0f39bc'), ('15', '4', 'ff0f39bc')]:
        raise ValueError('unexpected table read address or length')
    sizes = {'read': 4, 'control': 512, 'code': 16, 'globals': 8,
             'board': 512, 'rom-table': 4}
    for name, size in sizes.items():
        a = (path / f'{name}-a5.bin').read_bytes()
        b = (path / f'{name}-5a.bin').read_bytes()
        if len(a) != size or a != b:
            raise ValueError('bad paired ' + name)
        if name == 'rom-table' and a != struct.pack('<I', 0xc001fe98):
            raise ValueError('wrong stock table word')
        if name == 'read' and a != struct.pack('<I', 0xc0f2c000):
            raise ValueError('wrong staging pointer')
        if name == 'code' and a != bytes.fromhex('061e805c5c2700090030f082985d0ac0'):
            raise ValueError('wrong stock entry')
        if name == 'globals' and a != struct.pack('<II', 0xc0110780, 0xc1000000):
            raise ValueError('wrong runtime globals')
        if name == 'board':
            for offset, value in {8: 0x80000, 12: 0xfef80000,
                                  0xe0: 0xc004ce90, 0xe4: 0xc004ced0,
                                  0xec: 0xc004cf80}.items():
                if struct.unpack_from('<I', a, offset)[0] != value:
                    raise ValueError('wrong board callback or geometry')
    for name in ('enquiry-before.bin', 'enquiry-after.bin'):
        data = (path / name).read_bytes()
        if len(data) != 512 or data[4:7] != bytes((4, 7, 29)):
            raise ValueError('wrong firmware profile')
    return dict(stock_table_verified=True, address='0xc001f9bc',
                value='0xc001fe98', commands=15, pending=False,
                table_write_visibility_proven=False, rom_instruction_fetch_proven=False,
                code_execution=False, flash_programming=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.capture), indent=2))
    except (OSError, ValueError) as error:
        parser.error(str(error))
