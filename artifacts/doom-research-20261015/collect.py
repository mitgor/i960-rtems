#!/usr/bin/env python3
"""Record research source pins and inspect the already accepted math object.

Usage: python3 artifacts/doom-research-20261015/collect.py --repos DIRECTORY
DIRECTORY contains shallow clones named as below; this script makes no network
or hardware calls. It only reads sources and writes research evidence here.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPOS = {
    'RealDOOM': ('sqpat/RealDOOM', ['README.md', 'math.asm', 'r_col24.asm', 'r_span24.asm', 'r_bsp24.asm']),
    'FastDoom': ('viti95/FastDoom', ['README.txt', 'FASTDOOM/r_bsp.c', 'FASTDOOM/lineahKN.asm']),
    'rp2040-doom': ('kilograham/rp2040-doom', ['README.md', 'src/pd_render.cpp', 'src/m_fixed.c']),
    'GBADoom': ('doomhack/GBADoom', ['README.md', 'include/m_fixed.h', 'source/m_recip.c', 'source/st_stuff.c']),
    'nRF52840Doom': ('next-hack/nRF52840Doom', ['NRF52840Doom/Doom/include/m_fixed.h']),
    'd32xr': ('viciious/d32xr', ['README.md', 'r_cache.c', 'r_phase2.c', 'r_phase7.c', 'sh2_fixed.s']),
}


def digest(b):
    return hashlib.sha256(b).hexdigest()


def math_evidence():
    archive = ROOT / 'artifacts/doom-pingpong-20261015/build-evidence-v1.tar.gz'
    raw = archive.read_bytes()
    assert digest(raw) == '3e47178822b57a6b6c6a89b28d2003e7c3537c20720dbf4857c03af730121503'
    member = 'build/engine-cross/i960/m_fixed.o'
    with tarfile.open(fileobj=io.BytesIO(raw)) as t:
        blob = t.extractfile(member).read()
    e = struct.unpack_from('<16sHHIIIIIHHHHHH', blob)
    assert e[0][:7] == b'\x7fELF\x01\x01\x01' and e[2] == 19
    sections = [struct.unpack_from('<IIIIIIIIII', blob, e[6] + i * e[11]) for i in range(e[12])]
    def section_bytes(s):
        return blob[s[4]:s[4] + s[5]]
    names = section_bytes(sections[e[13]])
    def name_at(strings, offset):
        return strings[offset:].split(b'\0', 1)[0].decode()
    symbols, text, relocs = {}, None, []
    for index, section in enumerate(sections):
        if name_at(names, section[0]) == '.text':
            text = section_bytes(section)
        if section[1] == 2:
            strings = section_bytes(sections[section[6]])
            entries = []
            for off in range(section[4], section[4] + section[5], section[9]):
                n, value, size, info, other, shndx = struct.unpack_from('<IIIBBH', blob, off)
                entries.append(dict(name=name_at(strings, n), value=value, section=shndx))
            symbols[index] = entries
    for section in sections:
        if section[1] == 9:
            for off in range(section[4], section[4] + section[5], section[9]):
                address, info = struct.unpack_from('<II', blob, off)
                relocs.append(dict(offset=address, symbol=symbols[section[6]][info >> 8]['name'], type=info & 255))
    assert text is not None
    word = struct.unpack_from('<I', text, 0x18)[0]
    assert ((word >> 24) << 4 | ((word >> 7) & 15)) == 0x670
    assert any(r['symbol'] == '___divdi3' and r['offset'] >= 0x50 for r in relocs)
    return dict(archive_sha256=digest(raw), member=member, object_sha256=digest(blob),
                text_bytes=len(text), fixedmul_emul_offset='0x18', fixedmul_emul_word=hex(word),
                undefined=[s['name'] for entries in symbols.values() for s in entries if s['name'] and s['section'] == 0],
                relocations=relocs, interpretation='Accepted archived object: FixedMul already uses emul; FixedDiv references general 64-bit division. Not a current live timing measurement.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repos', type=Path, required=True)
    a = p.parse_args()
    sources = {}
    for folder, (repo, files) in REPOS.items():
        path = a.repos / folder
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path, text=True).strip()
        status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=path, text=True)
        assert not status, f'dirty research source {folder}'
        sources[folder] = dict(repo='https://github.com/' + repo, commit=revision,
                               files={f: dict(sha256=digest((path / f).read_bytes()),
                                              url=f'https://github.com/{repo}/blob/{revision}/{f}') for f in files})
    scenarios = []
    for fraction, speed in [(0.1, 2), (0.2, 2), (0.3, 2), (0.4, 2), (0.2, 3), (0.8, 2)]:
        gain = 1 / (1 - fraction + fraction / speed)
        scenarios.append(dict(assumed_frame_fraction=fraction, assumed_local_speedup=speed,
                              whole_frame_speedup=gain, fps_gain_percent=100*(gain-1)))
    result = dict(research_date='2026-10-15', sources=sources, math_object=math_evidence(),
                  illustrative_amdahl_scenarios_not_predictions=scenarios,
                  hardware_accessed=False, new_target_speedups_measured=False)
    (HERE / 'evidence.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'{len(sources)} clean source repositories pinned; accepted math-object assertions passed; no hardware access')


if __name__ == '__main__':
    main()
