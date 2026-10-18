#!/usr/bin/env python3
"""Verify the frozen candidate and native evidence; no physical acceptance claim."""
import hashlib,json,tarfile
from pathlib import Path
here=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
for line in (here/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split();assert sha((here/name).read_bytes())==digest,name
state=json.loads((here/'status.json').read_text())
assert state['physical_restart_acceptance'] is False
assert not state['installed_bundle_changed'] and not state['flash_written']
with tarfile.open(here/'candidate.tar.xz') as archive:
    def read(name):return archive.extractfile(name).read()
    inventory_bytes=read('bundle-candidate/bundle.json')
    assert sha(inventory_bytes)==state['bundle_manifest_sha256']
    inventory=json.loads(inventory_bytes)
    available=set(archive.getnames());checked=0
    for name,digest in inventory['files'].items():
        member='bundle-candidate/'+name
        if member in available:assert sha(read(member))==digest,name;checked+=1
    manifest=state['manifest'];src='bundle-candidate/project/rtems/accele160/doom_dma/'
    assert sha(read(src+'app.c'))==manifest['source_sha256']
    assert sha(read('bundle-candidate/kernel/kernel.bin'))==manifest['kernel_sha256']
    assert sha(read('bundle-candidate/kernel/image.bin'))==manifest['image_sha256']
    build=json.loads(read('bundle-candidate/kernel/build.json'))
    assert build['persistent'] and build['reusable'] and build['private_cache_map']
    for name in ('rearm-policy.log','browser.log','dma.log'):
        text=read(name).decode();assert 'passed' in text or 'verified' in text
    assert 'OK' in read('launcher.log').decode()
print(f'Frozen reusable candidate: {checked} archived bundle files and native logs verified; see verify_card.py for the subsequent physical acceptance')
