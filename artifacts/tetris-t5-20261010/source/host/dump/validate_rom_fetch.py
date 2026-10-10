#!/usr/bin/env python3
"""Validate the fixed RAM-dispatch and 8-bit flash-bus captures offline."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'artifacts/romfetch-live-20261010'
ROM = ROOT / 'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin'


def check_run(number, second_binary):
    path = BASE / f'attempt{number}'
    result = (path / 'result.txt').read_text()
    statuses = re.findall(r'complete op=6f id=[0-9a-f]+ status=([0-9a-f]{4})', result)
    assert statuses == ['017e', '017f', '0104'], (number, statuses)
    assert 'experiment-result=0 pending=0' in result
    assert 'exec-dirty=0' in result
    assert 'guard-changed=0' in result
    assert 'guard-changed=1' not in result
    for prefix, expected in [('exec-table-ram', bytes.fromhex('00c1fac0')),
                             ('exec-table-flash', bytes.fromhex('80c1fac0')),
                             ('exec-table-restored', bytes.fromhex('98fe01c0'))]:
        a = (path / f'{prefix}-a5.bin').read_bytes()
        assert a == (path / f'{prefix}-5a.bin').read_bytes() == expected
    for stem, code in [('ram', (ROOT/'loader/romfetch/ram-status.bin').read_bytes()),
                       ('flash', (ROOT/f'loader/romfetch/{second_binary}').read_bytes())]:
        before = (path / f'exec-{stem}-before-a5.bin').read_bytes()
        after = (path / f'exec-{stem}-after-a5.bin').read_bytes()
        restored = (path / f'exec-{stem}-restored-a5.bin').read_bytes()
        assert len(before) == len(after) == len(restored) == 64
        assert before == (path / f'exec-{stem}-before-5a.bin').read_bytes()
        assert after == (path / f'exec-{stem}-after-5a.bin').read_bytes()
        assert restored == (path / f'exec-{stem}-restored-5a.bin').read_bytes()
        assert after == code + before[len(code):]
        assert restored == before
    return {'attempt': number, 'statuses': statuses, 'restored': True,
            'result_sha256': hashlib.sha256((path/'result.txt').read_bytes()).hexdigest()}


def main():
    rom = ROM.read_bytes()
    assert len(rom) == 0x80000
    mapping = {}
    for addr in (0xfefb0200, 0xfefc8200, 0xfefe0000):
        name = f'{addr:08x}'
        path = BASE / 'flash-map3'
        a = (path/f'{name}-a5.bin').read_bytes()
        assert len(a) == 64 and a == (path/f'{name}-5a.bin').read_bytes()
        for i in range(0, 64, 4):
            observed = int.from_bytes(a[i:i+4], 'little')
            expected = ((addr+i) & 0xffffff00) | rom[addr+i-0xfef80000]
            assert observed == expected, (name, i, observed, expected)
        mapping[name] = {'words_checked': 16, 'paired': True}
    assert rom[0x3022c:0x30230] == bytes.fromhex('0000000a')
    assert bytes.fromhex('003000862c02fbfe') in (ROOT/'loader/romfetch/flash-ret-probe.bin').read_bytes()
    runs = [check_run(3, 'icctl-control.bin'),
            check_run(4, 'ram-call-control.bin'),
            check_run(5, 'flash-ret-probe.bin')]
    output = {'flash_mapping': mapping, 'runs': runs,
              'attempt2_timeout': 'uncertain completion: timeout' in
              (BASE/'attempt2/result-from-dmesg.txt').read_text()}
    assert output['attempt2_timeout']
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
