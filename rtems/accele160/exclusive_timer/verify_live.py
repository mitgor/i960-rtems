#!/usr/bin/env python3
"""Replay the bounded RTEMS timer + occupied/upper-page card capture."""
import hashlib
import json
import struct
import sys
from pathlib import Path

IMAGE = '126b26bbf76d8e7a782d2be4659fecab5664bb57726647a21803e7010fc73825'
KERNEL = '440673cae52c0e7a4c07f9cbba4e54111f977a28bd566f3b115313a02377032e'
FLASH = '1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
FNV = 0x63af0065
PAGE = 4096
PAGES = 27
PTR = 0xc0710000
NONCE = 0x161610d1


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fnv(data):
    h = 0x811c9dc5
    for b in data:
        h = ((h ^ b) * 0x01000193) & 0xffffffff
    return h


def js(path):
    return json.loads(path.read_text())


def data(path):
    return path.read_bytes()


def words(blob, offset, count):
    return struct.unpack_from('<' + str(count) + 'I', blob, offset)


def fields(path):
    return dict(x.split('=', 1) for x in path.read_text().split())


def flash_pair(path, boot):
    for number in (0, 1):
        directory = path / ('post-' + str(number))
        request = js(directory / 'request.json')
        result = js(directory / 'result.json')
        status = fields(directory / 'status.txt')
        need(request['boot_id'] == boot and request['selector'] == 9 and
             request['length'] == result['bytes'] == 1048576 and
             request['card']['bdf'] == '0000:37:09.1' and
             result['sha256'] == FLASH and
             result['old_after']['driver'] is None and
             all(status.get(k) == v for k, v in
                 (('done', '1'), ('status', '0'), ('residual', '0'),
                  ('guard_changes', '0'))), 'full guarded flash ' + str(directory))


def verify(root, previous):
    root, previous = Path(root), Path(previous)
    live = root / 'live-0'
    image = data(root / 'build/image.bin')
    kernel = data(root / 'build/kernel.bin')
    pre = js(live / 'preflight.json')
    result = js(live / 'result.json')
    boot = pre['boot_id']
    need(len(image) == len(kernel) == PAGES * PAGE and sha(image) == IMAGE and
         sha(kernel) == KERNEL and image[:20*PAGE] == kernel[:20*PAGE] and
         image[20*PAGE:] == b'\xa5' * (7*PAGE) and fnv(image) == FNV and
         pre['image_sha256'] == result['image_sha256'] == IMAGE and
         pre['kernel_sha256'] == KERNEL and
         pre['firmware_sha256'] == result['firmware_sha256'] == FLASH and
         result['boot_id'] == boot, 'exact image and boot')
    need(result['full_audits'] and result['owner_restored'] and
         result['page_restored'] and result['stage_restored'] and
         pre['card'] == result['card_after'] and
         pre['old'] == result['old_after'] and
         pre['card']['bdf'] == '0000:37:09.1' and
         pre['card']['driver'] == 'myrsread' and
         pre['old']['bdf'] == '0000:37:04.1' and
         pre['old']['driver'] is None, 'card and final owner')
    flash_pair(previous, boot)
    flash_pair(root, boot)
    before = data(live / 'page-before.bin')
    reserved = data(live / 'page-reserved.bin')
    owner = data(live / 'owner-before.bin')
    owned = data(live / 'owner-reserved.bin')
    upper = data(live / 'upper-before.bin')
    stock = data(live / 'stock-before.bin')
    need(len(before) == len(reserved) == len(owner) == len(owned) == PAGE and
         upper == bytes(PAGE) and len(stock) == PAGE and stock != bytes(PAGE)
         and data(live / 'page-restored.bin') == before and
         data(live / 'owner-after.bin')[0x2a0:0xaa0] == owner[0x2a0:0xaa0] and
         words(reserved, 0x820, 4) == (0x4f4c4c41, 0x16161041, PTR, 0x80000),
         'initial/final pages and grant')
    first = (PTR - 0xc0000000) // 0x8000
    for i in range(256):
        baseline = (words(owner, 0x2a0 + i*4, 1)[0],
                    words(owner, 0x6a0 + i*4, 1)[0])
        held = (words(owned, 0x2a0 + i*4, 1)[0],
                words(owned, 0x6a0 + i*4, 1)[0])
        need(held == ((16, 0x96016004) if first <= i < first+16 else baseline),
             'allocator record ' + str(i))
    need([r['mode'] for r in result['runs']] == ['stop', 'timeout'], 'control modes')
    upat = struct.pack('<4I', 0x314d5458, 0x89abcdef, 0x13579bdf, 0x554d5458)
    spat = struct.pack('<4I', 0x324d5458, 0xfedcba98, 0x2468ace0, 0x554d5458)
    for mode, run in zip(('stop', 'timeout'), result['runs']):
        directory = live / mode
        page = data(directory / 'page-after.bin')
        held_upper = data(directory / 'upper-held.bin')
        held_stock = data(directory / 'stock-held.bin')
        need(held_upper == upper[:0x80] + upat + upper[0x90:] and
             held_stock == stock[:0x80] + spat + stock[0x90:] and
             data(directory / 'upper-after.bin') == upper and
             data(directory / 'stock-after.bin') == stock and
             words(page, 0xa80, 8) ==
             (0x314d5458, 0, fnv(upper), fnv(stock), fnv(upper), fnv(stock), 0, 0),
             'held and restored full pages ' + mode)
        need(page[:0xa00] == reserved[:0x820] + before[0x820:0x830] +
             reserved[0x830:0xa00] and page[0xaa0:] == before[0xaa0:] and
             words(page, 0xa00, 8) ==
             (0x314d4152, NONCE, PTR, 0x80000, PAGES, 0, FNV, 0),
             'loader report bounds ' + mode)
        flag = 0x504f5453 if mode == 'stop' else 0x454d4954
        need(words(page, 0xa20, 7) ==
             (0x314e5552, NONCE, 0x31454e4f, PTR, PAGES, FNV, flag),
             'RTEMS report ' + mode)
        side = words(page, 0xa40, 8)
        if mode == 'stop':
            need(run['stale_pending'] is True and
                 words(data(directory / 'stale-page.bin'), 0xa4c, 1) ==
                 (0xdeadbeef,) and
                 side == (0x3145534c, NONCE, 1, flag, 0x59444152,
                          0x214b4341, NONCE, 1), 'STOP/ACK')
        else:
            need(side == (0x3145534c, NONCE, 1, 0, flag) +
                 (0xa5a5a5a5,) * 3, 'timeout')
        for command in ('copy', 'digest', 'ram-admit'):
            state = fields(directory / (command + '-status.txt'))
            need(all(state.get(k) == v for k, v in
                     (('done', '1'), ('status', '0'), ('residual', '0'))),
                 command + ' status ' + mode)
        receipts = js(directory / 'copy-receipts.json')
        need(len(receipts) == PAGES, 'page count ' + mode)
        for i, receipt in enumerate(receipts):
            chunk = image[i*PAGE:(i+1)*PAGE]
            need(receipt == dict(index=i, sha256=sha(chunk),
                                 fnv=f'0x{fnv(chunk):08x}'),
                 'copy receipt ' + str(i) + ' ' + mode)
        need(words(data(directory / 'digest-page.bin'), 0x830, 4) ==
             (0x48534148, 0x16161071, PAGES, FNV), 'whole image digest')
        fw, preflight, entry, restored, ticks, irq, handoffs, cleanup = words(
            page, 0xa60, 8)
        trace = words(data(directory / 'irq-stack-after.bin'), 0, 28)
        need(fw == restored == 0xc0002100 and preflight == 0 and
             PTR+26*PAGE <= entry < PTR+27*PAGE and
             ticks == trace[1] == run['ticks'] and
             handoffs == trace[2] == run['handoffs'] and
             trace[0] == 0x54504d45 and trace[3] > 0 and
             trace[7] == trace[8] and trace[9] == trace[10] > 0 and
             trace[11] == trace[12] > 0 and trace[17] == trace[18] == 0x12 and
             trace[19:25] == (0x10c7, 0x80000, 0xaaaaaaaa, 0, 0, 0) and
             trace[26] == 0 and cleanup == trace[27] == 1 and
             data(directory / 'owner-after.bin')[0x2a0:0xaa0] ==
             owned[0x2a0:0xaa0] and
             data(directory / 'worker0-irq-stack-after.bin')[-64:] == b'\xa5'*64 and
             data(directory / 'worker1-irq-stack-after.bin')[-64:] == b'\xa5'*64,
             'timer, ISR and owner drain ' + mode)
        if mode == 'timeout':
            need(ticks == handoffs == 120 and trace[6] == 60,
                 'finite timeout ticks')
    return dict(boot_id=boot, image_sha256=IMAGE, firmware_sha256=FLASH,
                modes=2, full_flash_reads=4, old_card='unbound',
                persistent_exclusive_ownership=False)


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        'artifacts/current/accele160-exclusive-timer-20261017')
    previous = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        'artifacts/current/accele160-occupied-probe-20261017')
    print(json.dumps(verify(root, previous), indent=2))
