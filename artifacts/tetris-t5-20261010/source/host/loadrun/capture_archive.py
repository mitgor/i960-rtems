#!/usr/bin/env python3
"""Lossless capture archives. Full-image blobs are XORed with a pinned baseline."""
import argparse,hashlib,json
from pathlib import Path
import zipfile

def sha(data):return hashlib.sha256(data).hexdigest()
def xor(data,base):
    return (int.from_bytes(data,'little')^int.from_bytes(base,'little')).to_bytes(len(base),'little')
def pack(folder,archive,base):
    if archive.exists():raise ValueError('archive already exists')
    manifest=dict(version=1,baseline_sha256=sha(base),files={})
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(folder.iterdir()):
            if not p.is_file():raise ValueError('unexpected subdirectory')
            data=p.read_bytes();mode='xor' if len(data)==len(base) else 'raw'
            manifest['files'][p.name]=dict(size=len(data),sha256=sha(data),encoding=mode)
            z.writestr('data/'+p.name,xor(data,base) if mode=='xor' else data)
        z.writestr('manifest.json',json.dumps(manifest,sort_keys=True))
    restored=read(archive,base)
    for name,data in restored.items():
        if data!=(folder/name).read_bytes():raise ValueError('round-trip mismatch')
    return manifest

def read(archive,base):
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read('manifest.json'))
        if manifest['version']!=1 or manifest['baseline_sha256']!=sha(base):raise ValueError('wrong baseline/version')
        result={}
        for name,meta in manifest['files'].items():
            if Path(name).name!=name or name in ('.','..'):raise ValueError('unsafe filename')
            data=z.read('data/'+name)
            if meta['encoding']=='xor':
                if len(data)!=len(base):raise ValueError('invalid XOR size')
                data=xor(data,base)
            elif meta['encoding']!='raw':raise ValueError('unknown encoding')
            if len(data)!=meta['size'] or sha(data)!=meta['sha256']:raise ValueError('capture hash mismatch')
            result[name]=data
        return result

def unpack(archive,folder,base):
    files=read(archive,base);folder.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():(folder/name).write_bytes(data)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path);p.add_argument('--baseline',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();unpack(a.archive,a.output,a.baseline.read_bytes())
