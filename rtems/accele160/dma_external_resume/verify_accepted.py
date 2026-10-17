#!/usr/bin/env python3
"""Offline replay of the accepted independent-resume capture."""
import hashlib
import json
import struct
import sys
from pathlib import Path

FLASH = '1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
IMAGE = 'f0228b6a78a408b5d3624f5947b8fd30487a301abcda728e60a87cb74ae58ae6'


def check(ok, name):
    if not ok:
        raise ValueError(name)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def fields(path):
    return dict(item.split('=', 1) for item in path.read_text().split())


def word(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def verify(root):
    accepted = root / 'accepted'
    run = accepted / 'attempt-2'
    halt = run / 'halt'
    pre, death, observed, result = (
        read_json(run / name) for name in
        ('preflight.json', 'death-intent.json', 'death-observation.json',
         'result.json'))
    check(sha((root / 'candidate/image/image.bin').read_bytes()) == IMAGE,
          'candidate image')
    check(pre['boot_id'] == death['boot_id'] == observed['boot_id'] ==
          result['boot_id'] and pre['image_sha256'] == death['image_sha256'] ==
          result['image_sha256'] == IMAGE and pre['firmware_sha256'] ==
          result['firmware_sha256'] == FLASH, 'same-boot exact inputs')
    check(death['pid'] == observed['pid'] == result['killed_pid'] and
          observed['process_absent'] and result['process_absent_before_recovery']
          and observed['premature_release_errno'] == 16,
          'dead original owner and denied premature release')
    check(result['mode'] == 'external-resume' and
          all(result[k] for k in ('full_audits', 'owner_restored',
                                  'page_restored', 'stage_restored')) and
          result['card_after']['bdf'] == '0000:37:09.1' and
          result['card_after']['driver'] == 'myrsread' and
          result['old_after']['bdf'] == '0000:37:04.1' and
          result['old_after']['driver'] is None, 'final ownership audit')
    for name in ('pre-after-reboot-0', 'pre-after-reboot-1',
                 'post-live-0', 'post-live-1'):
        directory = accepted / name
        request = read_json(directory / 'request.json')
        flash = read_json(directory / 'result.json')
        status = fields(directory / 'status.txt')
        check(request['boot_id'] == result['boot_id'] and
              request['selector'] == 9 and request['length'] == 1048576 and
              request['card']['bdf'] == '0000:37:09.1' and
              flash['bytes'] == 1048576 and flash['sha256'] == FLASH and
              all(status.get(k) == v for k, v in
                  (('done', '1'), ('status', '0'), ('residual', '0'),
                   ('guard_changes', '0'))), 'full-flash ' + name)
    held = (halt / 'held-page.bin').read_bytes()
    stable = (halt / 'recovery-held-page.bin').read_bytes()
    resumed = (halt / 'resume-written-page.bin').read_bytes()
    final = (halt / 'page-after.bin').read_bytes()
    check(death['held_page_sha256'] == sha(held) and
          word(held, 0xa50) == word(stable, 0xa50) == 0x444c4548 and
          word(held, 0xa4c) == word(stable, 0xa4c) == 0 and
          word(resumed, 0xa4c) == 0x4d555352 and
          word(final, 0xa50) == 0x45505845, 'held/resume/terminal pages')
    stack = (halt / 'irq-stack-after.bin').read_bytes()
    task_stack = (halt / 'task-irq-stack-after.bin').read_bytes()
    trace = struct.unpack_from('<96I', stack, 3072)
    check(trace[0] == 0x4b535452 and trace[1] == result['terminal_ticks'] == 300
          and trace[9:12] == (0, 1, 0x45505845) and
          trace[68:73] == (2, 0, 0, 0, 0) and
          trace[83] == trace[84] == result['stop_tick'] == 21 and
          trace[85] == result['resume_tick'] == 101 and
          trace[94:96] == (1, result['resume_reason']) == (1, 1) and
          80 <= trace[85] - trace[84] < 200 and
          result['channel0'] == [f'0x{x:08x}' for x in trace[44:52]] and
          stack[:64] == stack[-64:] == task_stack[:64] == task_stack[-64:] ==
          b'\xa5' * 64, 'timer/RTEMS/DMA trace and guards')
    pin = fields(halt / 'dma-pin-after.txt')
    payload = (halt / 'dma-data.bin').read_bytes()
    check(pin['armed'] == pin['verified'] == pin['payload_match'] == '1' and
          pin['guard_changes'] == '0' and
          payload == bytes(i ^ 0xa6 for i in range(256)) + b'\x5a' * 3840,
          'pinned host payload and guards')
    check((run / 'page-restored.bin').read_bytes() ==
          (run / 'page-before.bin').read_bytes() and
          (run / 'owner-after.bin').read_bytes()[0x2a0:0xaa0] ==
          (run / 'owner-before.bin').read_bytes()[0x2a0:0xaa0],
          'released loader page and allocator')
    return {'external_resume': 'accepted', 'flash_reads': 4,
            'stop_tick': trace[84], 'resume_tick': trace[85],
            'terminal_tick': trace[1]}


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(
        'artifacts/current/accele160-dma-external-resume-20261017')
    print(json.dumps(verify(root), indent=2))
