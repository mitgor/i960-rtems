#!/usr/bin/env python3
"""Check two bounded stock slot-3 replays against observed controller info."""
import argparse
import json
import re
from pathlib import Path

EXPECTED_SHA = 'a3f72f98e18667d7c80eebac996b77f465bce5d5024a8b3ec3c70d2a285572f8'
MODEL = re.compile(
    r'stock next model event=3 slot3=0x([0-9a-f]{8}) '
    r'status3=([0-9a-f]{16}) output-sha256=([0-9a-f]{64}) '
    r'ring-cursor=0x([0-9a-f]{8}) .*?descriptor='
    r'([0-9a-f]{8}),([0-9a-f]{8}),([0-9a-f]{8}),'
    r'([0-9a-f]{8}),([0-9a-f]{8}),([0-9a-f]{8}) '
    r'outbound=0x([0-9a-f]{8}) no-guest-copy=1')
REQUEST = re.compile(r'ring followup event=3 slot=3 dma=0x([0-9a-f]{8}) '
                     r'hex=([0-9a-f]{128})')


def check(path):
    qemu = (path / 'qemu.log').read_text()
    requests = REQUEST.findall(qemu)
    models = MODEL.findall(qemu)
    assert len(requests) == len(models) == 1, path
    slot_dma, slot_hex = requests[0]
    slot = bytes.fromhex(slot_hex)
    assert slot[:8] == bytes.fromhex('01002050ec030000')
    assert slot[21] == 1 and slot[40:44] == bytes.fromhex('ec030000')
    output_dma = int.from_bytes(slot[32:40], 'little')
    (word0, status, sha, cursor, d0, d1, d2, d3, d4, d5, outbound) = models[0]
    assert word0 == '00000000' and status == '00000001ffffffec'
    assert sha == EXPECTED_SHA and outbound == '00000002'
    assert int(cursor, 16) == int(slot_dma, 16) + 64
    assert [d0, d1, d2, d3, d4, d5] == [
        '00000000', f'{output_dma:08x}', '00000000',
        'c060c300', '000003ec', '0000003f']
    assert 'stock next event=3 local-idb=0x00000010' in qemu
    return {'slot_dma': '0x' + slot_dma, 'output_dma': f'0x{output_dma:08x}',
            'output_sha256': sha, 'status_hex': '01000000ecffffff',
            'outbound': 2, 'guest_copy': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--first', type=Path, required=True)
    p.add_argument('--repeat', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    first, repeat = check(a.first), check(a.repeat)
    assert first['output_dma'] != repeat['output_dma']
    receipt = {'gate': 'PASS', 'first': first, 'repeat': repeat,
               'scope': 'stock i960 model slot 3 output/status/doorbell; no guest copy',
               'physical_card_tested': False, 'safe_to_flash': False}
    a.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('stock_next_event3=PASS')


if __name__ == '__main__':
    main()
