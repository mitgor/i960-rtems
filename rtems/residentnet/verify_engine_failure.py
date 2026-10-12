#!/usr/bin/env python3
"""Inspect the failed batch without promoting it to engine/STOP acceptance."""
import argparse,json,struct,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from packet_log import read_packets
from validate_packets import validate
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.capture
w=json.loads((root/'snapshots.json').read_text())[-1]['words'];assert w[0]==0x31525845 and w[2:5]==[1,0,0] and w[11]==64
raw=bytearray(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,101))
def add(frame):assert 20<=len(frame)<=1500;raw.extend(struct.pack('<4I',0,0,len(frame),len(frame))+frame)
counts=[0,0]
for e in read_packets(root):
 q=bytes.fromhex(e['request']);r=bytes.fromhex(e['response']);qh=struct.unpack_from('<8I',q);h=struct.unpack_from('<8I',r);assert h[0:2]==qh[0:2] and h[3:]==(1,0,0,0,0) and len(q)==len(r)==1568
 if e['op']==1:assert h[2]==qh[2] and q[32:32+h[2]]==r[32:32+h[2]];add(q[32:32+h[2]]);counts[0]+=1
 else:
  assert e['op']==2;counts[1]+=1;blob=r[32:32+h[2]];i=0
  while i<len(blob):n=struct.unpack_from('<I',blob,i)[0];i+=4;add(blob[i:i+n]);i+=n
  assert i==len(blob)
assert counts==w[60:62]
with tempfile.TemporaryDirectory() as d:
 f=Path(d)/'prefix.pcap';f.write_bytes(raw);result=validate(f)
progress=json.loads((root/'network-progress.json').read_text());rounds=1+max(x['round'] for x in progress);assert rounds==6
for family in (4,6):
 flows=[x for x in result['streams'] if x['sport']==9600 and (6 if ':' in x['src'] else 4)==family];assert len(flows)==rounds and all(x['bytes']==4096 for x in flows)
result.update(physical_shutdown_accepted=False,engine_entries=0,network_rounds=rounds,interrupt_drain_fault_bit=w[11],fault_observed_tick=w[5],failed_io_errno=71)
a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS: failed-batch prefix network bytes; interrupt/drain bit 64 documented, no engine/STOP acceptance')
