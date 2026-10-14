#!/usr/bin/env python3
"""Recorded ioctl costs, distinct from wall time including sleep/logging/CRC."""
import json,statistics,struct,sys
from pathlib import Path
w=Path(sys.argv[1]);groups={}
for filename in ('frame-dma-journal.jsonl','frame-journal.jsonl'):
 for line in (w/filename).read_text().splitlines():
  r=json.loads(line);op=struct.unpack_from('<I',bytes.fromhex(r['request']))[0]
  kind='dma-'+str(op) if filename.startswith('frame-dma') else 'mailbox-'+str(op)
  if 'errno' in r:kind+='-errno-'+str(r['errno'])
  groups.setdefault(kind,[]).append(r['ns']/1e6)
print(json.dumps({k:dict(count=len(v),total_ms=sum(v),mean_ms=statistics.mean(v),min_ms=min(v),max_ms=max(v)) for k,v in groups.items()},indent=2))
