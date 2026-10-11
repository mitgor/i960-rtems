#!/usr/bin/env python3
"""Separate validator, renderer and completion-observation effects."""
import argparse,gzip,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path);a=p.parse_args()
median=statistics.median
names=['base1','validate','fast1','poll1','poll2','fast2','base2']
result={}
for name in names:
 directory=a.captures/('live-'+name)
 phases=json.loads((directory/'phases.json').read_text())
 groups={}
 for label in ['render80','render10','snapshot64','snapshot4864']:
  rows=[r for r in phases if r['label']==label]
  groups[label]={k.replace('_ns','_ms'):median(r[k] for r in rows)/1e6 for k in ['execute_ns','audit_ns','kernel_ns','wall_ns','process_cpu_ns']}
 with gzip.open(directory/'commands.jsonl.gz','rt') as f:samples=[json.loads(line) for line in f]
 audit={}
 for phase,sample in zip(phases,samples):
  if phase['label']!='render80':continue
  for row in sample['commands']:
   if row['op']==0x20 and row['offset']<0x80000:
    audit.setdefault(row['count'],[]).append(row)
 groups['audit_reads_by_size']={n:dict(samples=len(rows),**{k+'_ms':median(r[k] for r in rows)/1e6 for k in ['wait','scan','total']}) for n,rows in audit.items()}
 result[name]=groups
pairs={'base':['base1','base2'],'validate':['validate'],'fast':['fast1','fast2'],'poll':['poll1','poll2']}
summary={}
for variant,runs in pairs.items():
 summary[variant]={label:{key:median(result[r][label][key] for r in runs) for key in result[runs[0]][label]} for label in ['render80','render10','snapshot64','snapshot4864']}
print(json.dumps(dict(runs=result,median_of_session_medians=summary,limits='Host intervals, not target cycles. One validator-only session; two sessions for the other variants. CPU time includes host validation and kernel work, excludes sleeping. All original paired read coverage and audit cadence retained.'),indent=2))
