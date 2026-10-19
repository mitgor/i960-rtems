#!/usr/bin/env python3
"""Replay profile-14 runtime and its non-status engine/firmware-RAM observations."""
import hashlib,json,struct,sys,tarfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'fault'))
from verify_runtime import verify
from inventory import decode
from firmware_audit import audit

def replay(path):
    result=verify(path,live=True)
    with tarfile.open(path) as t:files={m.name:t.extractfile(m).read() for m in t if m.isfile()}
    manifest=json.loads(files['bundle/project/rtems/accele160/doom_dma/persistent-manifest.json'])
    if manifest['terminal_test'] not in (14,15):raise ValueError('expected profile 14/15')
    expected={'inventory.h','inventory.py'}
    if manifest['terminal_test']==15:expected.update(('qlogic_config.h','qlogic_config.py'))
    if set(manifest['engine_inventory_sources'])!=expected:raise ValueError('inventory source set')
    for name,digest in manifest['engine_inventory_sources'].items():
        if hashlib.sha256(files['bundle/project/rtems/accele160/ownership/'+name]).hexdigest()!=digest:raise ValueError('inventory source identity')
    firmware=audit(files['bundle/inputs/candidate.bin'])
    samples=[]
    for name in sorted(files):
        if '/run/owned-' not in name or not name.endswith('.bin'):continue
        page=files[name];w=struct.unpack_from('<240I',page)
        row=decode(page,w[17],w[166],w[171])
        if manifest['terminal_test']==15:
            from qlogic_config import decode as config_decode
            row['qlogic']=config_decode(page,w[17],w[166],w[171])
        row.update(member=name,sequence=w[166],ticks=w[167]);samples.append(row)
    samples.sort(key=lambda s:s['sequence'])
    if len(samples)!=3:raise ValueError('expected ready/frame32/idle samples')
    result.update(profile=manifest['terminal_test'],engine_samples=samples,firmware_dependencies=firmware,
        memory_reclaimed=False,engines_disabled=False,scsi_config_independently_read=manifest['terminal_test']==15)
    return result
if __name__=='__main__':print(json.dumps(replay(sys.argv[1]),indent=2))
