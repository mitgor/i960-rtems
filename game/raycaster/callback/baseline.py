#!/usr/bin/env python3
"""Recompute the pre-change cost attribution from preserved upload captures."""
import gzip,io,json,statistics,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];ART=ROOT/'artifacts/upload-20261011'
med=statistics.median
results={}
with tarfile.open(ART/'live.tar.gz') as archive:
 for name in ['fast1','fast2']:
  def read(suffix):
   matches=[n for n in archive.getnames() if n.lstrip('./')=='live-'+name+'/'+suffix]
   assert len(matches)==1
   return archive.extractfile(matches[0]).read()
  phases=json.loads(read('phases.json'))
  commands=[json.loads(line) for line in gzip.decompress(read('commands.jsonl.gz')).splitlines()]
  assert len(commands)==len(phases)==421
  selected=[(p,c) for p,c in zip(phases,commands) if p['label']=='render80']
  groups={};waits=[];scans=[];totals=[]
  for phase,sample in selected:
   assert phase['sequence']==sample['sequence']
   reads=[r for r in sample['commands'] if r['op']==0x20 and r['offset']<0x80000]
   assert sum(r['count'] for r in reads)==2*phase['audit_bytes']
   waits.append(sum(r['wait'] for r in reads));scans.append(sum(r['scan'] for r in reads));totals.append(sum(r['total'] for r in reads))
   for r in reads:groups.setdefault(r['count'],[]).append(r['wait'])
  snap={label:med(p['execute_ns'] for p in phases if p['label']==label)/1e6 for label in ['render80','render10','snapshot64','snapshot4864']}
  results[name]=dict(callback_ms=snap,audit_ms=med(p['audit_ns'] for p,c in selected)/1e6,audit_command_wait_ms=med(waits)/1e6,audit_scan_ms=med(scans)/1e6,audit_command_total_ms=med(totals)/1e6,read_wait_by_bytes={k:dict(samples=len(v),median_ms=med(v)/1e6,min_ms=min(v)/1e6,max_ms=max(v)/1e6) for k,v in groups.items()})
print(json.dumps(dict(source='artifacts/upload-20261011/live.tar.gz',runs=results,interpretation='Read wait includes firmware, DMA and host polling; byte-size dependence alone does not establish raw PCI bandwidth. Snapshot64 still includes target request validation, RTEMS semaphore dispatch, runner/cache work and firmware completion. New candidates have no card measurements until the pending matrix runs.'),indent=2))
