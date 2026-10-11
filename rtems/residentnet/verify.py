#!/usr/bin/env python3
"""Independent replay: pinned image/module, one ARM, snapshot and packet evidence."""
import argparse,gzip,hashlib,json,struct,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import ROM_SHA,verify_close
from validate_packets import validate
import wire

def snapshot_gate(w,epoch):
 assert len(w)==64 and w[0]==0x31525845 and w[1]>0 and w[2] in (1,2)
 assert w[4]==w[11]==w[52]==0 and w[36:42]==[0]*6 and w[42:46]==[2,18,514,81916]
 assert w[54]==w[55] and w[56]==epoch and w[63]==1
 for i in (12,14):assert 0<=w[i]-w[i+1]<=1
 if w[2]==2:assert w[3] in (1,2) and w[8:10]==[1,1] and w[12]==w[13]>0 and w[14]==w[15]>0 and w[53]==0
 else:assert w[3]==0 and w[8:10]==[0,0] and w[53]==0x2000

def verify(root,out):
 identity=json.loads((out/'request.json').read_text());code=(root/'residentnet/kernel.bin').read_bytes()
 assert hashlib.sha256(code).hexdigest()==identity['payload_sha256'] and hashlib.sha256(wire.prepare(code)).hexdigest()==identity['image_sha256']
 assert any(hashlib.sha256(p.read_bytes()).hexdigest()==identity['module_sha256'] for p in root.glob('residentnet-module*/dac960auto.ko'))
 original=(out/'open/stage-before-a5.bin').read_bytes();assert hashlib.sha256(original).hexdigest()==ROM_SHA and original==(out/'open/stage-before-5a.bin').read_bytes()
 raw=gzip.decompress((out/'trace.bin.gz').read_bytes());ns,n=struct.unpack_from('<QI',raw);assert ns>0 and n==16
 req=raw[12:28];n=struct.unpack_from('<I',raw,28)[0];assert n==640 and len(raw)==32+n
 arm=struct.unpack('<4I',req);assert arm[:2]==(0x31415452,1) and arm[3]&255==2;epoch=arm[2]
 audit=gzip.decompress((out/'audit-000001.bin.gz').read_bytes());before=wire.prepare(code)[:wire.bio.OFFSET]+wire.block(req,1)+original[wire.bio.IMAGE_SIZE:]
 assert wire.response(before,audit+original[len(audit):])==(0,raw[32:])
 groups=[];cur=None;events=json.loads((out/'controls.json').read_text())
 for e in events:
  if 'words' not in e:continue
  w=e['words'];assert w[3]==1 and w[6:]==[0,0] and not w[4]&1
  tag={4:0x8b000000,5:0x92000000|(e['arg']<<16),6:0x94000000,7:0x95000000}[e['op']];assert w[5]==tag|epoch
  if e['op']==7:
   if cur is not None:assert len(cur)==64;groups.append(cur)
   cur=[]
  elif e['op']==5:assert e['arg']==len(cur);cur.append(w[2])
 assert len(cur)==64;groups.append(cur);assert groups==[s['words'] for s in json.loads((out/'snapshots.json').read_text())]
 for w in groups:snapshot_gate(w,epoch)
 for a,b in zip(groups,groups[1:]):assert b[1]>a[1] and all(b[i]>=a[i] for i in (5,6,7,60,61,62))
 assert groups[-1][2]==2 and groups[-1][4:36]==groups[-2][4:36] and groups[-1][6]>0 and groups[-1][7]>0
 assert groups[-1][62]-groups[-2][62]==2
 if groups[-1][3]==2:assert groups[-1][5]==arm[3]>>8
 errors=[e['errno'] for e in events if 'errno' in e]
 assert sorted(x for x in errors if x!=11)==[16,22,22,108,116] and errors.count(11)>=1
 assert 'errno=5' in (out/'write-denied.txt').read_text()
 log=(out/'last-control.txt').read_text();assert 'submit op=' not in log[log.index('MONITOR enter'):]
 assert 'SESSION FAILED: retained DMA/module; reboot required' in (out/'retained-close/result.txt').read_text()
 assert json.loads((out/'cleanup.json').read_text())['interface_present'] is False
 # Reconstruct raw-IP PCAP from successful bulk ioctls. Check every checksum and
 # reassemble both directions of TCP echo independently of the live assertions.
 pcap=bytearray(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,101));counts=[0,0];latencies=[]
 def add(frame):
  assert 20<=len(frame)<=1500;pcap.extend(struct.pack('<4I',0,0,len(frame),len(frame))+frame)
 for e in json.loads((out/'packets.json').read_text()):
  a=bytes.fromhex(e['request']);b=bytes.fromhex(e['response']);assert len(a)==len(b)==1568 and e['ns']>0
  aw=struct.unpack_from('<8I',a);bw=struct.unpack_from('<8I',b);assert aw[0]==bw[0]==e['op'] and aw[1]==bw[1]==epoch and aw[3:]==(0,)*5
  assert bw[3]==1 and not bw[4]&1 and bw[5:]==(0,0,0)
  if e['op']==1:
   assert aw[2]==bw[2] and a[32:32+aw[2]]==b[32:32+bw[2]];add(a[32:32+aw[2]]);counts[0]+=1
  else:
   assert e['op']==2 and aw[2]==0 and 0<bw[2]<=1536;blob=b[32:32+bw[2]];offset=0
   while offset<len(blob):
    n=struct.unpack_from('<I',blob,offset)[0];offset+=4;frame=blob[offset:offset+n];offset+=n;assert len(frame)==n;add(frame)
   assert offset==len(blob);counts[1]+=1
  latencies.append(e['ns']/1e6)
 assert counts==groups[-1][60:62]
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'packets.pcap';path.write_bytes(pcap);packets=validate(path)
 results=json.loads((out/'network-results.json').read_text());rounds=1+max(v.get('round',0) for v in results);assert 1<=rounds<=20 and len(results) in (12*rounds,14*rounds)
 for iteration in range(rounds):
  for family in (2,10):
   r=[v for v in results if v['family']==family and v.get('round',0)==iteration]
   assert len([v for v in r if v['protocol']=='udp']) in (4,5)
   ts=[v for v in r if v['protocol']=='tcp'];assert len(ts)==1
   t=ts[0];assert t['bytes']==4096 and t['sha256']==hashlib.sha256(bytes(i%251 for i in range(4096))).hexdigest()
   hs=[v for v in r if v['protocol']=='http'];assert len(hs)==1 and 'HTTP/1.0 200 OK' in hs[0]['response']

 bad=0
 for i in (0,2,4,11,36,37,38,39,40,41,42,43,44,45,52,53,54,56,63):
  w=groups[-1].copy();w[i]=0 if w[i] else 1
  try:snapshot_gate(w,epoch)
  except AssertionError:bad+=1
  else:raise AssertionError(('corruption accepted',i))
 return dict(run=out.name,boot=identity['boot_id'],ticks=groups[-1][5],stop_reason=groups[-1][3],ioctls=counts,cache_observations=groups[-1][57:60],cache_completion_proven=False,broader_ram_owned=False,rounds=rounds,snapshot_corruptions_rejected=bad,bulk_latency_ms=dict(min=min(latencies),max=max(latencies),mean=sum(latencies)/len(latencies)),packets=packets)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('run',type=Path);a=p.parse_args();print(json.dumps(verify(a.root,a.run),indent=2))
