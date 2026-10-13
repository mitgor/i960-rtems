#!/usr/bin/env python3
"""Replay complete scalar-loader captures; preserve deliberate semantic failures."""
import argparse,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'host/loadrun'))
from loadrun import verify
p=argparse.ArgumentParser();p.add_argument('probe',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();b=a.probe;m=json.loads((b/'build.json').read_text());recorded=json.loads((b/'physical-results.json').read_text());rows=[];boots=set();commands=0
module_sha=hashlib.sha256((b/'module/dac960loadrun.ko').read_bytes()).hexdigest()
assert m['exact_scheduled_function_bytes']==160 and m['expected_source_results']==[0,1,0,1,0,1,1,0,0]
for variant in ('scheduled','no-schedule','unoptimized'):
 payload=(b/(variant+'.bin')).read_bytes();sha=hashlib.sha256(payload).hexdigest()
 for i,expected in enumerate(m['expected_source_results']):
  c=b/(variant+'-case-'+str(i));q=json.loads((c/'request.json').read_text());boots.add(q['boot_id'])
  assert q['payload_sha256']==sha and q['module_sha256']==module_sha and q['argument']==i and q['entry']==0 and q['buffer_io'] is False
  assert (c/'payload.bin').read_bytes()==payload and (c/'unloaded.txt').read_text()=='clean module unload completed\n'
  value=verify(c,payload);log=(c/'result.txt').read_text();ids=[int(x) for x in re.findall(r'^submit op=[0-9a-f]+ id=(\d+) ',log,re.M)]
  assert ids==list(range(1,111));commands+=len(ids)
  rows.append(dict(variant=variant,case=i,expected_source=expected,actual=value,source_match=value==expected,full_loader_audit=True,clean_unload=True))
assert rows==recorded and len(boots)==1
failures={v:[r['case'] for r in rows if r['variant']==v and not r['source_match']] for v in ('scheduled','no-schedule','unoptimized')}
assert failures=={'scheduled':[0,5],'no-schedule':[0],'unoptimized':[]}
out=dict(diagnostic_only=True,doom_accepted=False,transactions=len(rows),firmware_commands=commands,full_paired_512KiB_staging_phases=len(rows)*3,all_restored_and_unloaded=True,boot_id=next(iter(boots)),semantic_failure_cases=failures,module_sha256=module_sha,rows=rows)
a.output.write_text(json.dumps(out,indent=2)+'\n');print('PASS 27 complete paired scalar transactions replayed; scheduled failures [0,5], no-schedule [0], unoptimized none; no Doom acceptance')
