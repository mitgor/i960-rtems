#!/usr/bin/env python3
"""Verify narrow source/flag scope and tie the scalar proof to the real engine."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=a.root
probe=r/'branch-probe';m=json.loads((probe/'build.json').read_text());assert m['expanded'] and m['candidate_function_exact']
rows=[]
for target,folder in [('host32','engine-host'),('i960','engine-cross')]:
 b=json.loads((r/folder/target/'build.json').read_text());assert b['point_side_o0'] and not b['failures'] and '-Os' in b['flags'] and '-O0' not in b['flags']
 split=[c for c in b['commands'] if '-O0' in c];assert len(split)==1 and Path(split[0][split[0].index('-c')+1]).name=='r_point_side.c'
 src=r/folder/'doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric'
 body=(src/'r_point_side.c').read_text();body=body[body.index('int\nR_PointOnSide\n'):].strip()
 original=(probe/'point.c').read_text();original=original[original.index('int\nR_PointOnSide\n'):].strip()
 assert body==original and 'int\nR_PointOnSide\n' not in (src/'r_main.c').read_text()
 rows.append(dict(target=target,only_o0_file='r_point_side.c',unchanged_function_sha256=hashlib.sha256(body.encode()).hexdigest()))
a_text=(probe/'candidate-text.bin').read_bytes();b_text=(probe/'unoptimized-text.bin').read_bytes();assert a_text==b_text
admission=json.loads((r/'admission/manifest.json').read_text());assert admission['startup']['checkpoint_barriers']==1 and admission['admission_bytes']<=900000
kernel=json.loads((r/'residentnet/build.json').read_text());assert '-DI960_DOOM_CHECKPOINT_BARRIERS' in kernel['flags']
result=dict(physical_doom_acceptance=False,compilation_scope=rows,exact_candidate_probe_text_bytes=len(a_text),candidate_probe_text_sha256=hashlib.sha256(a_text).hexdigest(),admission_bytes=admission['admission_bytes'],checkpoint_barriers=True)
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
