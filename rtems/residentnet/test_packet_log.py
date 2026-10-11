#!/usr/bin/env python3
"""Full record preservation and rejection of incomplete/conflicting journals."""
import json,tempfile
from pathlib import Path
from packet_log import append_packet,finish_packets,read_packets
with tempfile.TemporaryDirectory() as d:
 out=Path(d);records=[dict(op=1,ns=i+1,request=bytes([i])*1568,response=bytes([i])*1568) for i in range(32)]
 for r in records:r['request']=r['request'].hex();r['response']=r['response'].hex()
 for r in records:append_packet(out,r)
 assert not (out/'packets.json').exists()
 finish_packets(out,records);assert read_packets(out)==records
 journal=out/'packet-journal.jsonl';original=journal.read_text()
 for bad in (original[:-1],original.split('\n',1)[1],original+original.splitlines()[0]+'\n',original.replace('"ns": 1,','"ns": 0,',1)):
  journal.write_text(bad)
  try:read_packets(out)
  except (AssertionError,ValueError):pass
  else:raise AssertionError('damaged journal accepted')
 journal.unlink();assert read_packets(out)==records # historical arrays still replay
print('Packet journal: complete requests/replies, legacy replay, four damaged journals rejected')
