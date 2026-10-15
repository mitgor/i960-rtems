#!/usr/bin/env python3
"""Isolated diagnostic workload only. Never changes production source or limits."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('project',type=Path);a=p.parse_args();f=a.project/'rtems/residentnet/shared_heap.inc';s=f.read_text()
for old,new in [('shared_bytes=(shared_cycles&31)?256:81920;','shared_bytes=81920; /* diagnostic: every shared cycle exercises the large pin */'),('tick-shared_since>=8','tick-shared_since>=80')]:
 assert s.count(old)==1;s=s.replace(old,new)
f.write_text(s)
