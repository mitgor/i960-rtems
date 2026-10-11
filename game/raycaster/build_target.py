#!/usr/bin/env python3
"""Build an isolated RTEMS session variant, without editing shared rtems/build.py.

Uses the repository's hash-checked RTEMS/newlib source archives. Never accesses
PCI, stops a service, loads a driver, or writes to the source-archive directory.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True, help='fresh build directory')
    p.add_argument('--sources', type=Path, required=True, help='existing source archive directory')
    p.add_argument('--cross', default='/home/mit/i960/tools/bin/i960-coff-')
    p.add_argument('--memory', choices=['byte', 'word'], default='word')
    p.add_argument('--memory-check', action='store_true', help='run 264 bounded reference-check batches before requests')
    p.add_argument('--request-words', action='store_true', help='exact aligned word request validation')
    p.add_argument('--render-fast', action='store_true', help='word-loaded FNV and clipped column runs')
    p.add_argument('--frame-queue', action='store_true', help='bounded two-slot queue prototype; requires queue audit transport')
    a = p.parse_args()
    if a.memory_check and a.memory != 'word':
        p.error('--memory-check requires --memory word')
    work = a.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    shutil.copytree(a.sources.resolve(), work / 'sources')
    project = work / 'project/rtems'
    shutil.copytree(ROOT / 'rtems', project, ignore=shutil.ignore_patterns('__pycache__', '._*'))
    profile = project / 'session'
    shutil.copyfile(HERE / 'rtems/app.c', profile / 'app.c')
    for name in ('ray.c', 'ray.h', 'trig.h'):
        shutil.copyfile(HERE / name, profile / name)
    from callback.optimize import request_words, render_fast, once
    if a.request_words:
        header = project / 'transport/buffer_io.h'
        header.write_text(request_words(header.read_text()))
    if a.render_fast:
        ray = profile / 'ray.c'
        ray.write_text(render_fast(ray.read_text()))
    if a.frame_queue:
        for name in ('queue.c', 'queue.h'):
            shutil.copyfile(HERE/'queue'/name, profile/name)
        app=profile/'app.c'
        text=once(app.read_text(),'#include "ray.h"', '#include "ray.h"\n#include "queue.h"\nstatic struct fq_state queue_state;')
        text=once(text,'rc=ray_request(guest,b+BIO_INPUT,bio_word(b+12),b+BIO_OUTPUT,bio_word(b+16));', 'rc=fq_request(&queue_state,guest,(unsigned char*)(0xc0f2c000u+FQ_OFFSET),b+BIO_INPUT,bio_word(b+12),b+BIO_OUTPUT,bio_word(b+16),bio_word(b+8));')
        text=once(text,'rc?0:(bio_word(b+BIO_INPUT+16)?RAY_REPLY:RAY_HEADER)', 'rc?0:FQ_REPLY')
        # Queue operations cannot enter the raycaster's benchmark adapter.
        text=once(text,'if(!rc && bio_word(b+BIO_INPUT+4)==3', 'if(0 && !rc && bio_word(b+BIO_INPUT+4)==3')
        text=once(text,'if(!bio_word(b+20) && bio_word(b+BIO_INPUT+4)==3', 'if(0 && !bio_word(b+20) && bio_word(b+BIO_INPUT+4)==3')
        app.write_text(text)
        link=profile/'link.ld';text=link.read_text()
        text=once(text,'ASSERT(. <= 0xc0f9bff0,', 'ASSERT(. <= 0xc0f8c000,')
        link.write_text(text)
    if a.memory == 'word':
        libc = profile / 'libc.c'
        original = libc.read_text()
        assert sum(line.startswith('void *memcpy(') for line in original.splitlines()) == 1
        assert sum(line.startswith('void *memset(') for line in original.splitlines()) == 1
        original = '\n'.join(line for line in original.splitlines()
                             if not line.startswith(('void *memcpy(', 'void *memset(')))
        # Keep remaining byte helpers unchanged; new definitions precede memmove.
        libc.write_text((ROOT / 'rtems/memory/word.c').read_text() + '\n' + original + '\n')
    if a.memory_check:
        for name in ('check.c', 'check.h'):
            shutil.copyfile(ROOT / 'rtems/memory' / name, profile / name)
        app = profile / 'app.c'
        source = app.read_text()
        source = '#include \"check.h\"\nstatic unsigned int memory_batch;\n' + source
        assert source.count('  job=1;\n') == 1
        source = source.replace('  job=1;\n',
            '  if(memory_batch<MEMORY_BATCHES){\n'
            '   if(memory_check_batch(memory_batch))bounded_fatal(0x60000+memory_batch);\n'
            '   memory_batch++;\n  }\n  job=1;\n')
        app.write_text(source)
    subprocess.run([sys.executable, str(project / 'build.py'), '--work', str(work),
                    '--profile', 'session', '--cross', a.cross], check=True)
    sources = {}
    for path in sorted(profile.iterdir()):
        if path.is_file() and not path.name.startswith('.'):
            sources[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    sources['buffer_io.h'] = hashlib.sha256((project/'transport/buffer_io.h').read_bytes()).hexdigest()
    (work / 'session/raycaster-build.json').write_text(json.dumps(dict(
        application='raycaster', frame_queue=a.frame_queue, request_words=a.request_words, render_fast=a.render_fast, memory=a.memory, memory_check_batches=264 if a.memory_check else 0, execution='bounded RTEMS session',
        hardware_tested=False, source_sha256=sources), indent=2) + '\n')


if __name__ == '__main__':
    main()
