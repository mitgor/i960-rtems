#!/usr/bin/env python3
"""Build the single reviewed reusable-RAM admission candidate from exact ROMs."""
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'helper'))
from audit_dispatch_rehearsal import analyze
from audit_late_ping import CAVE, LOADER_BASE, LOADER_RETURN

STOCK_SHA = '0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a'
CURRENT_SHA = '93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094'
OLD_HANDLER_SHA = 'dd4d51c24ef1debcbc1dc4830c0761696be94849082965146445f38e2662c52f'
HANDLER_SHA = '8d8c79c3b8c206608ef7221000991c0d75eb101ce06581fedc2a74522648ad34'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def make(stock, current, old_handler, handler):
    assert len(stock) == len(current) == 1048576
    for name, data, want in [('stock', stock, STOCK_SHA),
                             ('current', current, CURRENT_SHA),
                             ('old handler', old_handler, OLD_HANDLER_SHA),
                             ('handler', handler, HANDLER_SHA)]:
        if sha(data) != want:
            raise ValueError(f'{name} identity mismatch')
    if len(old_handler) != 3868 or len(handler) != 4324:
        raise ValueError('handler sizes')
    base = analyze(stock)
    previous = analyze(current)
    if previous['runtime'] != base['runtime'] or current[0xf0000:] != stock[0xf0000:]:
        raise ValueError('runtime or boot drift')
    loader = base['loader']
    offset = loader['flash_offset'] + CAVE - LOADER_BASE
    hook = loader['flash_offset'] + LOADER_RETURN - LOADER_BASE
    if (current[offset:offset+len(old_handler)] != old_handler or
        current[offset+len(old_handler):offset+len(handler)] !=
            b'\xff' * (len(handler)-len(old_handler))):
        raise ValueError('handler preimage or erased extension changed')
    if CAVE + len(handler) > 0xc000f800:
        raise ValueError('handler/report overlap')
    candidate = bytearray(current)
    candidate[offset:offset+len(handler)] = handler
    size = loader['size']
    checksum = sum(struct.unpack_from(f'<{size//4}I', candidate,
                                      loader['flash_offset'])) & 0xffffffff
    trailer = base['trailer_offset']
    struct.pack_into('<I', candidate, trailer+24, checksum)
    trailer_checksum = sum(struct.unpack_from('<31I',candidate,trailer)) & 0xffffffff
    struct.pack_into('<I', candidate, trailer+124, trailer_checksum)
    checked = analyze(candidate)
    changed = {i for i,(a,b) in enumerate(zip(current,candidate)) if a != b}
    allowed = (set(range(offset,offset+len(handler))) |
               set(range(trailer+24,trailer+28)) |
               set(range(trailer+124,trailer+128)))
    if (not changed <= allowed or checked['runtime'] != base['runtime'] or
        not checked['loader']['checksum_passed'] or
        not checked['trailer_checksum_passed'] or
        candidate[0xf0000:] != stock[0xf0000:] or
        candidate[hook:hook+4] != current[hook:hook+4]):
        raise ValueError('flash boundary/checksum audit')
    return bytes(candidate), dict(candidate_sha256=sha(candidate),
        handler_sha256=HANDLER_SHA, changed_bytes=len(changed),
        loader_checksum=f'0x{checksum:08x}',
        trailer_checksum=f'0x{trailer_checksum:08x}',
        runtime_unchanged=True, boot_block_unchanged=True)

if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    stock = root/'artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin'
    current = root/'artifacts/current/accele160-vector-20261017/candidate.bin'
    if not stock.exists():
        matches = list((root/'artifacts').rglob('stock*.bin'))
        raise SystemExit(f'provide exact stock image path; candidates: {matches[:4]}')
    image, report = make(stock.read_bytes(), current.read_bytes(),
                         (here.parent/'vector_gate/handler.bin').read_bytes(),
                         (here/'handler.bin').read_bytes())
    path = here/'candidate.bin'
    if path.exists(): raise FileExistsError(path)
    path.write_bytes(image)
    print(json.dumps(report, indent=2))
