#!/usr/bin/env python3
"""Summarize measured word-ioctl latency by the last captured status phase.

This is observational, not a matched benchmark or a bound. Pages are separate
captures; a shutdown transition can occur between them. Every word is included.
"""
import argparse,json,statistics
from pathlib import Path

def summarize(events):
 buckets={k:[] for k in ('active','draining','parked','unknown')}
 phase='unknown';groups=0;i=0
 while i<len(events):
  e=events[i]
  if e.get('op')!=7:i+=1;continue
  page=e['arg'];rows=events[i+1:i+65]
  assert len(rows)==64 and all(r.get('op')==5 and r['arg']==n for n,r in enumerate(rows))
  if page==0:
   w=[r['words'][2] for r in rows]
   phase='parked' if w[2]==2 else 'draining' if w[3] else 'active'
  buckets[phase].extend(r['ns']/1e6 for r in rows)
  groups+=1;i+=65
 def stats(v):
  if not v:return None
  v=sorted(v)
  return dict(samples=len(v),median_ms=statistics.median(v),p95_ms=v[int(.95*(len(v)-1))],p99_ms=v[int(.99*(len(v)-1))],maximum_ms=v[-1])
 all_words=[x for v in buckets.values() for x in v]
 assert len(all_words)==sum(e.get('op')==5 for e in events)
 return dict(snapshot_pages=groups,all_words=stats(all_words),by_last_status={k:stats(v) for k,v in buckets.items()})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args()
 print(json.dumps(summarize(json.loads((a.run/'controls.json').read_text())),indent=2))
