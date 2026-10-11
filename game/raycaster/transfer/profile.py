#!/usr/bin/env python3
"""Reconcile complete per-command evidence with each measured transaction."""
import argparse,gzip,json,statistics
from collections import defaultdict
from pathlib import Path
from commands import FIELDS,parse
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args()
phases=json.loads((a.capture/'phases.json').read_text())
with gzip.open(a.capture/'commands.jsonl.gz','rt') as f:commands=[json.loads(line) for line in f]
assert len(commands)==len(phases)
table=(0xc001f9bc-0xc0f2c000)&0xffffffff
categories=lambda r: ('request_upload' if r['offset']==0x70000 else 'sentinel_upload' if r['offset']==0x80280 else 'table_upload') if r['op']==0x21 else 'callback' if r['op']==0x6f else 'table_read' if r['offset']==table else 'result_read' if r['offset']==0x80280 else 'audit_read'
groups=defaultdict(list);residual=[];counts=defaultdict(int)
for phase,sample in zip(phases,commands):
 assert sample['sequence']==phase['sequence']
 assert parse(sample['log'])==sample['commands']
 rows=sample['commands']
 expected=[(0x21,0x3060,0x70000)]
 if phase['sequence']==1:expected += [(0x21,4,table),(0x20,4,table),(0x20,4,table),(0x6f,0,0)]
 expected += [(0x21,16,0x80280),(0x21,4,table),(0x20,4,table),(0x20,4,table),(0x6f,0,0),(0x20,4,table),(0x20,4,table),(0x20,16,0x80280),(0x20,16,0x80280)]
 for repeat in range(2):
  expected += [(0x20,min(0xf000,phase['audit_bytes']-off),off) for off in range(0,phase['audit_bytes'],0xf000)]
 assert [(r['op'],r['count'],r['offset']) for r in rows]==expected
 assert sum(r['count'] for r in rows if r['op']==0x20 and r['offset']<0x80000)==2*phase['audit_bytes']
 if phase['sequence']>1:
  assert len(rows)==(28 if phase['sequence']%32==0 else 26)
  assert sum(r['op']==0x21 for r in rows)==3 and sum(r['op']==0x6f for r in rows)==1
 if phase['label']!='render80':continue
 by_kind=defaultdict(list)
 for r in rows:by_kind[categories(r)].append(r)
 for kind,values in by_kind.items():
  counts[kind]+=len(values)
  groups[kind].append({k:sum(r[k] for r in values) for k in FIELDS+('total',)})
 total=sum(r['total'] for r in rows)
 assert phase['kernel_ns']>=total
 residual.append(phase['kernel_ns']-total)
summary={kind:dict(frames=len(values),commands=counts[kind],**{k+'_ms':statistics.median(v[k] for v in values)/1e6 for k in FIELDS+('total',)}) for kind,values in groups.items()}
print(json.dumps(dict(verified_transactions=len(phases),commands=sum(len(s['commands']) for s in commands),render80=summary,median_unattributed_kernel_ms=statistics.median(residual)/1e6,limits='Host monotonic intervals. wait includes firmware execution and polling; logging is separate. Unattributed time includes CMDPROFILE logging, session validation and copying. Audits and command sequence unchanged.'),indent=2))
