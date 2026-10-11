#!/usr/bin/env python3
"""Replay baseline and lossless fast-archive sessions using their archived code."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);a=p.parse_args();art=a.artifacts.resolve()
assert __debug__,'verification requires Python without -O'
expected={'accepted/kernel.bin':'3c6f40e44f77f09f8fbed02722232d0651f4a4b7514ccb198fbaa4768dc44f4d','accepted/dac960rtems.ko':'3796b5cbeacb853d31c966defa0788fcd568886160725674f7d7011c77aef0fa'}
reports=[];profiles={}
with tempfile.TemporaryDirectory(prefix='i960-browser-replay-') as directory:
    for variant in ('baseline','fast'):
        root=Path(directory)/variant;root.mkdir()
        tag='fast-' if variant=='fast' else ''
        for name in (f'browser-{tag}builds.tar.gz',f'browser-{tag}live.tar.gz'):
            with tarfile.open(art/name) as archive:archive.extractall(root,filter='data')
        for entry in json.loads((art/(tag+'source-manifest.json')).read_text()):
            assert hashlib.sha256((root/entry['path']).read_bytes()).hexdigest()==entry['sha256']
        for name,digest in expected.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
        game=root/'game/raycaster'
        subprocess.run(['make','-C',str(game),'all'],check=True,stdout=subprocess.DEVNULL)
        def invoke(script,*args):
            return json.loads(subprocess.check_output([sys.executable,str(script),*map(str,args)],text=True))
        names=('live-browser','live-disconnect') if tag else ('live-browser','live-idle','live-limit','live-signal','live-disconnect')
        for name in names:
            capture=root/name
            report=invoke(game/'browserqueue/verify.py',capture,'--payload',root/'accepted/kernel.bin','--module',root/'accepted/dac960rtems.ko')
            assert report==json.loads((art/(tag+name+'-verified.json')).read_text())
            quiet=invoke(game/'upload/verify_quiet.py',capture)
            assert quiet==json.loads((art/(tag+name+'-quiet.json')).read_text())
            reports.append(report)
        profile=invoke(game/'browserqueue/profile.py',root/'live-browser',art/(tag+'card-browser'))
        assert profile==json.loads((art/(tag+'profile.json')).read_text())
        profiles[variant]=profile
    print(json.dumps(dict(sessions=len(reports),replies=sum(r['replies'] for r in reports),full_audits=sum(r['full_audits'] for r in reports),targeted_slots=sum(r['targeted_slots'] for r in reports),commands=sum(r['commands'] for r in reports),restored_sessions=sum(r['restored'] for r in reports),profiles=profiles),indent=2))
