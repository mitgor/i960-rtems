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
    a = p.parse_args()
    work = a.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    shutil.copytree(a.sources.resolve(), work / 'sources')
    project = work / 'project/rtems'
    shutil.copytree(ROOT / 'rtems', project, ignore=shutil.ignore_patterns('__pycache__', '._*'))
    profile = project / 'session'
    shutil.copyfile(HERE / 'rtems/app.c', profile / 'app.c')
    for name in ('ray.c', 'ray.h', 'trig.h'):
        shutil.copyfile(HERE / name, profile / name)
    subprocess.run([sys.executable, str(project / 'build.py'), '--work', str(work),
                    '--profile', 'session', '--cross', a.cross], check=True)
    sources = {}
    for path in sorted(profile.iterdir()):
        if path.is_file() and not path.name.startswith('.'):
            sources[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (work / 'session/raycaster-build.json').write_text(json.dumps(dict(
        application='raycaster', execution='bounded RTEMS session',
        hardware_tested=False, source_sha256=sources), indent=2) + '\n')


if __name__ == '__main__':
    main()
