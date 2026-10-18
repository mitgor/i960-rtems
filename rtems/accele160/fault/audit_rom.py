#!/usr/bin/env python3
"""Inspect pinned firmware PRCB; never infer live vector ownership from ROM."""
import hashlib,json,struct,tarfile
from pathlib import Path
root=Path(__file__).resolve().parents[3]
archive=root/'artifacts/current/accele160-service-20261018/followup.tar.xz'
with tarfile.open(archive) as t:b=t.extractfile('bundle/inputs/candidate.bin').read()
sha=hashlib.sha256(b).hexdigest()
assert sha=='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
prcb=struct.unpack_from('<8I',b,0xfdd20)
assert prcb[0]==0xc0000800 and prcb[4]==0xfeffd910 and prcb[7]==0xc0001000
print(json.dumps(dict(firmware_sha256=sha,prcb='0xfeffdd20',prcb_words=[hex(x) for x in prcb],
    fault_table='RAM: needs live capture',nmi='cached: needs live capture',
    source_archive=str(archive.relative_to(root)),hardware_ownership_proven=False),indent=2))
