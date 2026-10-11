#!/usr/bin/env python3
"""Replay the same captured metadata through rewrite and journal paths (ABBA)."""
import argparse,json,statistics,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from journal.metadata import Metadata,read_metadata
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args()
requests=json.loads((a.capture/'browser-requests.json').read_text());rows=json.loads((a.capture/'phases.json').read_text())
assert len(requests)==len(rows)>100
reports=[]
for mode in ('rewrite','journal','journal','rewrite'):
 with tempfile.TemporaryDirectory(prefix='i960-metadata-bench-') as directory:
  out=Path(directory);m=Metadata(out,mode);reqs=[];phases=[];times=[]
  for request,row in zip(requests,rows):
   t=time.monotonic_ns();reqs.append(request);m.intent(request[0],bytes.fromhex(request[1]),reqs);mid=time.monotonic_ns()
   phases.append(row);m.result(row,phases);end=time.monotonic_ns();times.append(dict(sequence=len(reqs),intent_ns=mid-t,result_ns=end-mid))
  t=time.monotonic_ns();m.finish(reqs,phases,len(reqs));m.close();close_ns=time.monotonic_ns()-t
  (out/'queue-test.json').write_text(json.dumps(dict(metadata_format=mode+'-v1')))
  assert read_metadata(out)==(requests,rows)
  cost=lambda rs:statistics.mean((r['intent_ns']+r['result_ns'])/1e6 for r in rs)
  reports.append(dict(mode=mode,requests=len(reqs),mean_ms=cost(times),first50_ms=cost(times[:50]),last50_ms=cost(times[-50:]),close_ms=close_ns/1e6,samples=times))
print(json.dumps(reports,indent=2))
