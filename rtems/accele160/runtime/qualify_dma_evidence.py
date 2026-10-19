#!/usr/bin/env python3
"""Revalidate existing card DMA captures. Does not issue DMA or imply a new run."""
import subprocess,json,hashlib,argparse
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
cases=[('active-fault','accele160-active-dma-exceptions-20261018','fault-tested.tar.xz'),('active-nmi','accele160-active-dma-exceptions-20261018','nmi-tested.tar.xz'),('stalled-fault','accele160-stalled-dma-20261018','fault-tested.tar.xz'),('stalled-nmi','accele160-stalled-dma-20261018','nmi-tested.tar.xz'),('resume-fault','accele160-dma-resume-20261019','tested.tar.xz'),('resume-nmi','accele160-nmi-dma-resume-20261019','tested.tar.xz'),('refusal-fault','accele160-dma-refusal-20261019','tested.tar.xz'),('refusal-nmi','accele160-nmi-dma-refusal-20261019','tested.tar.xz')]
result=dict(kind='historical hardware captures replayed; no new DMA injection',cases=[])
for name,batch,archive in cases:
 path=root/'artifacts/current'/batch/archive
 r=json.loads(subprocess.check_output(['python3',str(root/'rtems/accele160/fault/verify_dma.py'),str(path)],text=True))
 recovery=json.loads((path.parent/'recovery.json').read_text())
 result['cases'].append(dict(name=name,archive=str(path.relative_to(root)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),replay=r,following_recovery=recovery))
 a.out.write_text(json.dumps(result,indent=2)+'\n')
 print(name,'passed',flush=True)
