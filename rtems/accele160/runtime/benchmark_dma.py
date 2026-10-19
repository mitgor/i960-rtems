#!/usr/bin/env python3
"""Matched packet reply transport trials; explicit byte-exact diagnostic first.
Stop the TUN relay before this raw packet test: it must not steal replies.
No retries or automatic fallback after uncertain completion.
"""
import argparse,json,struct,socket,time,statistics,subprocess,os
from pathlib import Path
from client import Client
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--rounds',type=int,default=40);a=p.parse_args()
if not 10<=a.rounds<=500:raise SystemExit('rounds 10..500')
assert subprocess.run(['systemctl','is-active','--quiet','i960-rtems-ip']).returncode!=0,'stop relay first'
c=Client();rows=[]
def checksum(b):
 if len(b)%2:b+=b'\0'
 n=sum(struct.unpack('!%dH'%(len(b)//2),b))
 while n>>16:n=(n&65535)+(n>>16)
 return (~n)&65535
def packet(payload):
 src=socket.inet_aton('10.196.0.1');dst=socket.inet_aton('10.196.0.2')
 h=struct.pack('!BBHHHBBH4s4s',0x45,0,28+len(payload),1,0,64,17,0,src,dst)
 return h[:10]+struct.pack('!H',checksum(h))+h[12:]+struct.pack('!HHHH',12346,9601,8+len(payload),0)+payload
def cpu():
 out={}
 for unit in ('i960-doom','i960-combined'):
  pid=int(subprocess.check_output(['systemctl','show','-p','MainPID','--value',unit],text=True))
  fields=Path('/proc/%d/stat'%pid).read_text().rsplit(')',1)[1].split()
  out[unit]=dict(pid=pid,ticks=int(fields[11])+int(fields[12]))
 return out
def one(mode,n,i):
 payload=struct.pack('<I',i)+bytes((j^i)&255 for j in range(n-4));t=time.monotonic()
 r=c.call(5,packet(payload),transport=mode);ms=(time.monotonic()-t)*1000
 b=bytes.fromhex(r['data']);assert len(b)>=32
 length=struct.unpack_from('<I',b)[0];ip=b[4:];assert length==len(ip)==28+n and ip[0]==0x45 and ip[9]==17 and checksum(ip[:20])==0
 assert ip[12:20]==socket.inet_aton('10.196.0.2')+socket.inet_aton('10.196.0.1')
 assert struct.unpack_from('!HHH',ip,20)==(9601,12346,n+8) and ip[28:]==payload
 assert r['transport']==('pio' if mode=='pio' else 'dma')
 rows.append(dict(mode=mode,payload_bytes=n,nonce=i,ms=ms,owner_ms=r['latency_ms'],reply_bytes=len(b)))
for i in range(32):one('dma-check',(64,256,1024,1400)[i%4],i)
before=cpu();started=time.monotonic()
for i in range(a.rounds):
 for n in (64,256,1024,1400):
  for mode in (('pio','dma') if i%2==0 else ('dma','pio')):one(mode,n,32+i)
  a.out.write_text(json.dumps(dict(rows=rows,in_progress=True),indent=2)+'\n')
after=cpu();elapsed=time.monotonic()-started
summary={}
for n in (64,256,1024,1400):
 summary[str(n)]={mode:dict(median_ms=statistics.median(r['ms'] for r in rows if r['mode']==mode and r['payload_bytes']==n),max_ms=max(r['ms'] for r in rows if r['mode']==mode and r['payload_bytes']==n)) for mode in ('pio','dma')}
query=c.call(7,transport='dma-check');assert not struct.unpack('<6I',bytes.fromhex(query['data']))[2]
out=dict(rows=rows,summary=summary,cpu_before=before,cpu_after=after,clock_ticks=os.sysconf('SC_CLK_TCK'),elapsed_s=elapsed,final=query,paired_checks=33)
a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(summary,indent=2))
