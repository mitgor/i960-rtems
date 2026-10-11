#!/usr/bin/env python3
"""Compare full-history rewrite with one full-record append, without card access."""
import argparse,json,statistics,tempfile,time
from pathlib import Path
from packet_log import append_packet
p=argparse.ArgumentParser();p.add_argument('packets',type=Path);a=p.parse_args()
records=json.loads(a.packets.read_text());rows=[]
with tempfile.TemporaryDirectory() as tmp:
 out=Path(tmp)
 for count in sorted({min(len(records),n) for n in (100,500,1000,len(records))}):
  rewrite=[];append=[]
  for _ in range(10):
   start=time.perf_counter_ns();(out/'rewrite.json').write_text(json.dumps(records[:count])+'\n');rewrite.append((time.perf_counter_ns()-start)/1e6)
   start=time.perf_counter_ns();append_packet(out,records[count-1]);append.append((time.perf_counter_ns()-start)/1e6)
  rows.append(dict(records=count,bytes=(out/'rewrite.json').stat().st_size,rewrite_mean_ms=statistics.mean(rewrite),rewrite_max_ms=max(rewrite),append_mean_ms=statistics.mean(append),append_max_ms=max(append)))
print(json.dumps(dict(card_access=False,samples_per_size=10,measurements=rows),indent=2))
