#!/usr/bin/env python3
"""Install the optional gateway around an existing accepted Linux launcher.

Copy this directory and the pinned pure-Python wheel first. Never changes the
owner's pinned bundle, card image or modules. Keeps the original wrapper intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import zipfile


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--wrapper',type=Path,required=True)
    p.add_argument('--wheel',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();source=root/'source';vendor=root/'vendor'
    expected=(source/'requirements.txt').read_text().strip().split('sha256:')[1]
    if hashlib.sha256(a.wheel.read_bytes()).hexdigest()!=expected:raise ValueError('wheel hash')
    vendor.mkdir(exist_ok=True)
    with zipfile.ZipFile(a.wheel) as wheel:wheel.extractall(vendor)
    backup=root/'owner-launcher'
    if not backup.exists():
        if 'source/launcher.py' in a.wrapper.read_text():raise ValueError('refuse recursive launcher backup')
        shutil.copy2(a.wrapper,backup)
    files={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest()
        for d in (source,vendor) for f in sorted(d.rglob('*'))
        if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
    files['owner-launcher']=hashlib.sha256(backup.read_bytes()).hexdigest()
    (root/'gateway-manifest.json').write_text(json.dumps(files,indent=2)+'\n')
    command=['/usr/bin/python3',str(source/'launcher.py'),'--gateway-root',str(root),'--owner-launcher',str(backup)]
    a.wrapper.write_text('#!/bin/sh\nexec '+shlex.join(command)+' "$@"\n')
    a.wrapper.chmod(0o755)
    print('Gateway installed; original card launcher saved at',backup)


if __name__=='__main__':main()
