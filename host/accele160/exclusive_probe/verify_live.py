#!/usr/bin/env python3
"""Offline replay of the bounded AcceleRAID upper-page exclusive probe."""
import hashlib
import json
import struct
import sys
from pathlib import Path

IMAGE = '9eab93599a513fbd38776567134c1d80838bb893df147053284be2dfd7b8950b'
KERNEL = 'c30ffdd3ee1a8e13b840a36f94d6f0d863a6b80fc8947295a66c8b5692b9f450'
FLASH = '1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'


def check(ok, name):
    if not ok:
        raise ValueError(name)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def verify(root, prior):
    live = root / 'live-0'
    result = read_json(live / 'result.json')
    pre = read_json(live / 'preflight.json')
    check(sha((root / 'build/image.bin').read_bytes()) == IMAGE and
          sha((root / 'build/kernel.bin').read_bytes()) == KERNEL and
          pre['image_sha256'] == result['image_sha256'] == IMAGE and
          pre['kernel_sha256'] == KERNEL and
          pre['firmware_sha256'] == result['firmware_sha256'] == FLASH and
          pre['boot_id'] == result['boot_id'], 'exact same-boot inputs')
    check(result['full_audits'] and result['owner_restored'] and
          result['page_restored'] and result['stage_restored'] and
          result['card_after']['bdf'] == '0000:37:09.1' and
          result['card_after']['driver'] == 'myrsread' and
          result['old_after']['bdf'] == '0000:37:04.1' and
          result['old_after']['driver'] is None, 'final audits')
    for folder in (prior / 'post-survey-0', prior / 'post-survey-1',
                   root / 'post-0', root / 'post-1'):
        request = read_json(folder / 'request.json')
        read = read_json(folder / 'result.json')
        status = dict(x.split('=', 1) for x in
                      (folder / 'status.txt').read_text().split())
        check(request['boot_id'] == pre['boot_id'] and
              request['selector'] == 9 and request['length'] == 1048576 and
              request['card']['bdf'] == '0000:37:09.1' and
              read['bytes'] == 1048576 and read['sha256'] == FLASH and
              read['old_after']['driver'] is None and
              all(status.get(k) == v for k, v in
                  (('done', '1'), ('status', '0'), ('residual', '0'),
                   ('guard_changes', '0'))), 'full flash ' + str(folder))
    before = (live / 'upper-before.bin').read_bytes()
    check(before == bytes(4096), 'upper preimage')
    check((live / 'owner-before.bin').read_bytes()[0x2a0:0xaa0] ==
          (live / 'owner-after.bin').read_bytes()[0x2a0:0xaa0] and
          (live / 'page-before.bin').read_bytes() ==
          (live / 'page-restored.bin').read_bytes(),
          'allocator and loader restoration')
    check([r['mode'] for r in result['runs']] == ['stop', 'timeout'],
          'both control paths')
    for mode, run in zip(('stop', 'timeout'), result['runs']):
        page = (live / mode / 'page-after.bin').read_bytes()
        upper = (live / mode / 'upper-after.bin').read_bytes()
        probe = struct.unpack_from('<8I', page, 0xa80)
        check(probe == (0x314c4358, 0xc0f01000, 0, 0x76efddc5,
                        4, 0x76efddc5, 0, 0) and upper == before,
              'exclusive probe/restoration ' + mode)
        check(run['firmware_sp'] == run['restored_sp'] == '0xc0002100' and
              run['entry_sp'] == '0xc071ffc0' and run['task_done'] == 1 and
              run['polls'] <= 2000000 and
              (run['stale_pending'] is True if mode == 'stop' else
               run['polls'] == 2000000), 'RTEMS lease ' + mode)
    return {'bounded_exclusive_page': 'accepted', 'full_flash_reads': 4,
            'old_card': 'unbound', 'persistent_exclusive_ownership': False}


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        'artifacts/current/accele160-exclusive-probe-20261017')
    prior = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        'artifacts/current/accele160-doom-arena-20261017')
    print(json.dumps(verify(root, prior), indent=2))
