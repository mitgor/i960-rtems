#!/usr/bin/env python3
"""Replay the two non-acceptance captures without promoting the candidate."""
import hashlib
import json
import struct
import sys
from pathlib import Path

FLASH = '1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
FIRST = '28b679b9de196c0944603f0a66adc763bb7ac37f4a1635da42e6351a7a99008b'
CANDIDATE = 'f0228b6a78a408b5d3624f5947b8fd30487a301abcda728e60a87cb74ae58ae6'

def check(ok, why):
    if not ok:
        raise ValueError(why)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fields(path):
    return dict(item.split('=', 1) for item in path.read_text().split())

def word(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

def main(root):
    neg = root / 'negative'
    flash_boots = set()
    for name in ('pre-flash-0', 'pre-flash-1',
                 'post-fallback-flash-0', 'post-fallback-flash-1'):
        directory = neg / 'flash' / name
        request = json.loads((directory / 'request.json').read_text())
        result = json.loads((directory / 'result.json').read_text())
        status = fields(directory / 'status.txt')
        flash_boots.add(request['boot_id'])
        check(request['selector'] == 9 and request['length'] == 1048576
              and request['card']['bdf'] == '0000:37:09.1'
              and result['card_after'] == request['card']
              and result['old_after']['driver'] is None
              and result['bytes'] == 1048576 and result['sha256'] == FLASH
              and sha(directory / 'data.bin') == FLASH
              and all(status.get(key) == value for key, value in
                      (('done', '1'), ('status', '0'), ('residual', '0'),
                       ('guard_changes', '0'))), name)
    check(sha(neg / 'image' / 'image.bin') == FIRST and
          sha(root / 'candidate' / 'image' / 'image.bin') == CANDIDATE,
          'exact RAM images')
    run = neg / 'fallback-run'
    pre = json.loads((run / 'preflight.json').read_text())
    death = json.loads((run / 'death-intent.json').read_text())
    observed = json.loads((run / 'death-observation.json').read_text())
    result = json.loads((run / 'result.json').read_text())
    check(flash_boots == {pre['boot_id']} and
          pre['boot_id'] == death['boot_id'] == observed['boot_id'] ==
          result['boot_id'] and pre['image_sha256'] == death['image_sha256'] ==
          result['image_sha256'] == FIRST and result['firmware_sha256'] == FLASH
          and death['pid'] == observed['pid'] == result['killed_pid']
          and observed['process_absent'] and
          observed['premature_release_errno'] == 16
          and result['mode'] == 'fallback' and
          result['terminal_ticks'] == 248 and result['stop_tick'] == 21
          and result['resume_tick'] == 221 and result['resume_reason'] == 2
          and all(result[key] for key in ('full_audits', 'owner_restored',
                                         'page_restored', 'stage_restored'))
          and result['card_after']['bdf'] == '0000:37:09.1'
          and result['old_after']['driver'] is None, 'fallback result')
    held = (run / 'halt' / 'held-page.bin').read_bytes()
    terminal = (run / 'halt' / 'page-after.bin').read_bytes()
    trace = struct.unpack_from('<96I',
            (run / 'halt' / 'irq-stack-after.bin').read_bytes(), 3072)
    check(death['held_page_sha256'] == hashlib.sha256(held).hexdigest()
          and word(held, 0xa4c) == 0x544c4148
          and word(held, 0xa50) == 0x444c4548
          and word(terminal, 0xa50) == 0x544c4148
          and trace[0] == 0x4b535452 and trace[1] == 248
          and trace[9:12] == (0, 1, 0x544c4148)
          and trace[68] == 2 and trace[82:86] == (1, 21, 21, 221)
          and trace[94:96] == (1, 2)
          and trace[44] == trace[46] == trace[48] == trace[50] == 0
          and trace[49] == 0xc0789800 and trace[51] == 7,
          'finite fallback and inactive DMA')
    pin = fields(run / 'halt' / 'dma-pin-after.txt')
    payload = (run / 'halt' / 'dma-data.bin').read_bytes()
    check(pin['armed'] == pin['verified'] == pin['payload_match'] == '1'
          and pin['guard_changes'] == '0' and len(payload) == 4096
          and payload[:256] == bytes(i ^ 0xa6 for i in range(256))
          and payload[256:] == b'\x5a' * 3840,
          'exact host payload and guards')
    failed = neg / 'preflight-rejection'
    fpre = json.loads((failed / 'preflight.json').read_text())
    page = (failed / 'halt' / 'no-active-page.bin').read_bytes()
    check(fpre['image_sha256'] == CANDIDATE
          and fpre['boot_id'] == pre['boot_id']
          and word(page, 0xa50) == 0x45505845
          and word(page, 0xa58) == 0x200000
          and not (failed / 'result.json').exists(),
          'candidate rejected before DMA acceptance')
    return dict(negative_fallback='audited', rejected_preflight='retained',
                full_flash_reads=4, external_resume_accepted=False)

if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(
        'artifacts/current/accele160-dma-external-resume-20261017')
    print(json.dumps(main(root), indent=2))
