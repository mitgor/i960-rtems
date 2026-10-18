#!/usr/bin/env python3
"""Package a prebuilt, admitted persistent engine and matching card kernel."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('project','kernel','admission','command-inputs','dma-module','stock-driver','rawreader','startup-oracle','wad','out'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    src=a.project/'rtems/accele160/doom_dma'
    manifest=json.loads((src/'persistent-manifest.json').read_text())
    engine=json.loads((a.admission/'manifest.json').read_text())
    if not manifest['persistent'] or manifest['frames']!=0 or not engine['persistent_play'] or engine['card_profile']!='accele160':
        p.error('requires admitted persistent AcceleRAID build')
    if a.out.exists():p.error('bundle destination already exists')
    a.out.mkdir(parents=True)
    for name in ('card_profiles','rtems/transport','host/accele160/lease_probe',
                 'host/accele160/readimage','rtems/accele160/doom_dma','game/doom/play/accele160'):
        shutil.copytree(a.project/name,a.out/'project'/name,
                        ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.o'))
    for name in ('kernel.bin','image.bin','kernel.elf','kernel.map','kernel.symbols','build.json'):
        target=a.out/'kernel'/name;target.parent.mkdir(exist_ok=True)
        shutil.copyfile(a.kernel/name,target)
    shutil.copytree(a.admission,a.out/'engine')
    inputs=a.out/'inputs';inputs.mkdir()
    for name in ('reserve_command.ko','release_command.ko','copy_command.ko',
                 'digest_command.ko','admit_command.ko','handler.bin','candidate.bin'):
        shutil.copyfile(a.command_inputs/name,inputs/name)
    for source,name in ((a.dma_module,'dma_frames.ko'),(a.stock_driver,'myrsread.ko'),(a.rawreader,'rawreader.ko'),
                        (a.startup_oracle,'native-requests.bin'),(a.wad,'freedoom1.wad')):
        shutil.copyfile(source,inputs/name)
    files={str(f.relative_to(a.out)):hashlib.sha256(f.read_bytes()).hexdigest()
           for f in sorted(a.out.rglob('*')) if f.is_file()}
    (a.out/'bundle.json').write_text(json.dumps(dict(schema=1,card_profile='accele160',
        bdf='0000:37:09.1',old_bdf='0000:37:04.1',files=files),indent=2)+'\n')
    print('Bundle ready:',a.out)


if __name__=='__main__':main()
