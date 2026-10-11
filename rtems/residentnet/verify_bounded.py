#!/usr/bin/env python3
"""Reuse the unchanged exclusive verifier for bounded residentnet bring-up."""
import argparse,importlib.util,json,tempfile
from pathlib import Path
h=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exclusive_verify',h.parent/'exclusive/verify.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('runs',type=Path,nargs='+');a=p.parse_args();r=a.root.resolve()
with tempfile.TemporaryDirectory() as d:
 root=Path(d);code=r/'residentnet'
 if not code.exists():code=r/'residentnet-v1-recovered'
 (root/'exclusive').symlink_to(code)
 for i,module in enumerate(r.glob('residentnet-module*')):(root/f'exclusive-module-{i}').symlink_to(module)
 result=[]
 for run in a.runs:
  report=m.verify(root,run);w=json.loads((run/'report.json').read_text())
  if w[150]==0x31484343:report['cache_probe']=dict(values=w[151:157],nmisr=w[157],atucr=w[158],dcache_status_or_reserved=w[159],completion_proven=False,ram_reclaimed=False)
  result.append(report)
 print(json.dumps(result,indent=2))
