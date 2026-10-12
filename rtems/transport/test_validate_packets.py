#!/usr/bin/env python3
"""TCP port reuse must preserve per-connection gaps and overlap checks."""
import socket,struct,tempfile
from pathlib import Path
from validate_packets import checksum,validate

def packet(reverse,seq,flags,body=b'',ack=0):
 src,dst=(socket.inet_aton(x) for x in (('10.196.0.2','10.196.0.1') if reverse else ('10.196.0.1','10.196.0.2')))
 tcp=bytearray(struct.pack('!HHIIBBHHH',*( (9600,40000) if reverse else (40000,9600)),seq,ack,0x50,flags,8192,0,0)+body)
 struct.pack_into('!H',tcp,16,checksum(src+dst+struct.pack('!BBH',0,6,len(tcp))+tcp))
 ip=bytearray(struct.pack('!BBHHHBBH4s4s',0x45,0,20+len(tcp),0,0,64,6,0,src,dst));struct.pack_into('!H',ip,10,checksum(ip))
 return bytes(ip+tcp)

def connection(a,b,body=b'abcd',close=True):
 rows=[packet(False,a,2),packet(True,b,18,ack=a+1),packet(False,a+1,16,body),packet(True,b+1,16,body)]
 if close:rows += [packet(False,a+1+len(body),17),packet(True,b+1+len(body),17)]
 return rows

def run(rows):
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp)/'packets.pcap';raw=struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,101)
  p.write_bytes(raw+b''.join(struct.pack('<4I',0,0,len(r),len(r))+r for r in rows));return validate(p)
rows=connection(100,200)+connection(1000,2000,b'efgh')
r=run(rows);assert len(r['streams'])==4 and {s['connection'] for s in r['streams']}=={1,2}
assert run(connection(100,200)[:4]+[packet(False,101,16,b'abcd')]+connection(100,200)[4:])['retransmitted_segments']==1
cases={
 'gap':connection(100,200)+[packet(False,1000,2),packet(True,2000,18,ack=1001),packet(False,1001,16,b'ab'),packet(False,1004,16,b'd')],
 'overlap':connection(100,200)[:4]+[packet(False,102,16,b'XX')],
 'unclosed_reuse':connection(100,200,close=False)+connection(1000,2000),
 'echo_mismatch':connection(100,200)+[packet(False,1000,2),packet(True,2000,18,ack=1001),packet(False,1001,16,b'abcd'),packet(True,2001,16,b'abce')],
 'wrong_syn_ack':[packet(False,100,2),packet(True,200,18,ack=999)]}
for name,rows in cases.items():
 try:run(rows)
 except AssertionError:pass
 else:raise AssertionError('accepted '+name)
print('PASS: closed TCP tuple reuse, duplicate segments; gaps, conflicting overlap, unclosed reuse, mismatched echo/SYN-ACK rejected')
