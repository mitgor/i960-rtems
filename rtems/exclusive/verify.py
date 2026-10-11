#!/usr/bin/env python3
"""Replay original exclusive-mode captures. No device/network access."""
import argparse,gzip,hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import verify_close,ROM_SHA
import wire

def snapshot_gate(w):
 assert len(w)==64 and w[0]==0x31525845 and w[1]>0 and w[2] in (1,2)
 assert w[4]==w[11]==w[52]==0 and w[36:42]==[0]*6 and w[42:46]==[2,18,514,81916]
 assert w[5]>0 and (w[6]>0 or w[7]>0) and w[54]==w[55] and w[56]>0 and not any(w[57:])
 for i in (12,14):assert 0<=w[i]-w[i+1]<=1
 if w[2]==2:assert w[6]>0 and w[7]>0 and w[3] in (1,2) and w[8:10]==[1,1] and w[12]==w[13]>0 and w[14]==w[15]>0 and w[53]==0
 else:assert w[3]==0 and w[8:10]==[0,0] and w[53]==0x2000

def verify(root,out):
 identity=json.loads((out/'request.json').read_text());code=(root/'exclusive/kernel.bin').read_bytes()
 modules=[p.read_bytes() for p in root.glob('exclusive-module-*/dac960auto.ko')];assert any(hashlib.sha256(x).hexdigest()==identity['module_sha256'] for x in modules)
 assert hashlib.sha256(code).hexdigest()==identity['payload_sha256'] and hashlib.sha256(wire.prepare(code)).hexdigest()==identity['image_sha256']
 original=(out/'open/stage-before-a5.bin').read_bytes();assert hashlib.sha256(original).hexdigest()==ROM_SHA and original==(out/'open/stage-before-5a.bin').read_bytes()
 raw=gzip.decompress((out/'trace.bin.gz').read_bytes());o=0;rows=[]
 while o<len(raw):
  ns,n=struct.unpack_from('<QI',raw,o);o+=12;req=raw[o:o+n];o+=n;n=struct.unpack_from('<I',raw,o)[0];o+=4;data=raw[o:o+n];o+=n;assert ns>0 and len(req)==16 and n in (512,640);rows.append((req,data))
 assert o==len(raw);arm=list(struct.unpack('<4I',rows[0][0]));assert arm[:2]==[0x31415452,1]
 epoch=arm[2];phase=arm[3]&255;limit=arm[3]>>8
 audit=gzip.decompress((out/'audit-000001.bin.gz').read_bytes());before=wire.prepare(code)[:wire.bio.OFFSET]+wire.block(rows[0][0],1)+original[wire.bio.IMAGE_SIZE:]
 assert wire.response(before,audit+original[len(audit):])==(0,rows[0][1])
 controls=json.loads((out/'controls.json').read_text());successful=[e for e in controls if 'words' in e]
 for e in successful:
  w=e['words'];assert w[3]==1 and w[6:]==[0,0] and not w[4]&1
 if (out/'snapshots.json').exists():
  assert len(rows)==1 and phase==2
  snapshots=json.loads((out/'snapshots.json').read_text());groups=[];cur=None
  for e in successful:
   if e['op']==7:
    if cur is not None:assert len(cur)==64;groups.append(cur)
    cur=[]
   elif e['op']==5:assert e['arg']==len(cur);cur.append(e['words'][2])
  assert len(cur)==64;groups.append(cur);assert groups==[s['words'] for s in snapshots]
  for s in snapshots:snapshot_gate(s['words']);assert s['words'][56]==epoch
  for prev,nxt in zip(groups,groups[1:]):assert nxt[1]>prev[1] and all(nxt[i]>=prev[i] for i in (5,6,7))
  assert groups[-1][2]==2 and groups[-1][4:36]==groups[-2][4:36]
  if groups[-1][3]==2:assert groups[-1][5]==limit
  assert sorted(e['errno'] for e in controls if 'errno' in e)==[16,22,116]
  assert 'errno=5' in (out/'write-denied.txt').read_text()
  log=(out/'last-control.txt').read_text();assert 'submit op=' not in log[log.index('MONITOR enter'):]
  assert 'SESSION FAILED: retained DMA/module; reboot required' in (out/'retained-close/result.txt').read_text()
  bad=0
  for index in (0,2,4,11,36,37,38,39,40,41,42,43,44,45,52,53,54,56,57):
   w=groups[-1].copy();w[index]=0 if w[index] else 1
   try:snapshot_gate(w)
   except AssertionError:bad+=1
   else:raise AssertionError(('corruption accepted',index))
  return dict(path=out.name,boot=identity['boot_id'],resident=True,ticks=groups[-1][5],reason=groups[-1][3],snapshots=len(groups),corruptions_rejected=bad,retained=True)
 if (out/'cache-pages.json').exists():
  pages=json.loads((out/'cache-pages.json').read_text());assert len(pages) in (4,6,7,14,15,28,29,31) and len(rows)==2+len(pages)
  for page,(req,data) in enumerate(rows[2:],1):
   assert struct.unpack('<4I',req)==(0x31415452,0,epoch,page)
   words=list(struct.unpack('<160I',data));assert words==pages[page-1] and words[150:152]==[0x32484343,page]
 else:assert len(rows)==2
 assert struct.unpack('<4I',rows[1][0])==(0x31415452,0,epoch,0)
 w=list(struct.unpack('<'+str(len(rows[1][1])//4)+'I',rows[1][1]));assert rows[1][1]==(out/'report.bin').read_bytes()
 assert w[7:9]==[0x10c7,0x80000] and w[9]==w[10] and not any(w[11:14]) and not w[14]&0x2000 and not w[15] and w[16:21]==[0x31464f48,4,1,0,0] and w[46]==w[48]==0
 assert w[64:67]==[0x31435845,phase,0] and w[68:84]==w[100:116]
 if phase==2:assert w[90]==w[74]&~4 and w[91]==w[75]&~4 and w[93]==w[77]|0x3ffc
 if limit:assert w[116]==w[123]==w[148]==0 and w[117]==limit and w[118]>0 and w[119]>0 and w[120:122]==[1,1] and w[124]==w[125]>0 and w[126]==w[127]>0
 verify_close(out/'close');assert 'AUTONOMOUS STOP verified before any RAM restoration' in (out/'close/result.txt').read_text()
 log=(out/'monitor-log.txt').read_text();assert 'submit op=' not in log[log.index('MONITOR enter'):]
 return dict(path=out.name,boot=identity['boot_id'],resident=False,phase=phase,ticks=limit,restored=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('paths',type=Path,nargs='+');a=p.parse_args();print(json.dumps([verify(a.root,x) for x in a.paths],indent=2))
if __name__=='__main__':main()
