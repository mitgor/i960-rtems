#!/usr/bin/env python3
"""Validate the independent checkpoint wire log; compare scalar host evidence.
This can diagnose an incomplete startup, never promote it to acceptance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
MAGIC=0x31504344
STAGES={1:'owned entry',2:'doomgeneric_Create',3:'Create returned',10:'level setup',11:'blockmap loaded',12:'vertices loaded',13:'sectors loaded',14:'sides loaded',15:'lines loaded',16:'subsectors loaded',17:'nodes loaded',18:'segs loaded',19:'reject loaded',20:'things loaded',21:'side texture fingerprint',22:'level setup done',25:'texture table built',26:'texture lookup done',30:'precache entry',32:'texture present fingerprint',34:'precache patch',36:'precache done',37:'player position/angle',38:'player viewz/extralight',40:'view position/angle',41:'view cos/sin/z',42:'BSP rendered',43:'planes rendered',44:'masked rendered',50:'DrawFrame entered',51:'frame hashes',60:'exit requested',61:'owned exit returned',62:'cleanup finished',99:'composite texture',100:'lookup texture',101:'patch selected',102:'lookup finished'}
STAGES.update({27:'sector height fingerprint',63:'player spawn subsector/sector/input z',64:'player spawn z/floor/ceiling',65:'player spawn x/y/sector floor',66:'player mapthing',67:'initial viewheight/viewz/delta',70:'height entry z/floor/ceiling',71:'height entry viewheight/delta/bob',72:'height ground/cheats/state',73:'height bob/momx/momy',74:'airborne height result/z/viewheight',75:'ground height viewheight/bob/z',76:'height result/ceiling/delta',80:'display entry',81:'player render returned',82:'HUD finished',83:'background finished',84:'border finished',85:'menu begin',86:'menu finished',87:'network update finished',88:'wipe endscreen begin',89:'wipe endscreen finished',90:'wipe clock wait begin',91:'wipe clock wait finished',92:'screen wipe begin',93:'screen wipe finished',94:'wipe no-blit finished',95:'wipe menu finished',96:'video finish dimensions',97:'video copy scaling/offsets',98:'video copy finished'})

def describe(w,wad=None):
 result=dict(stage=STAGES[w[3]],words=list(w))
 if wad is not None:
  assert hashlib.sha256(wad).hexdigest()=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
  n,d=struct.unpack_from('<2I',wad,4);lumps=[struct.unpack_from('<II8s',wad,d+16*i) for i in range(n)]
  if w[3] in (34,101) and w[4]<len(lumps):
   off,size,name=lumps[w[4]];result.update(lump=name.rstrip(b'\0').decode(),directory_matches=(off,size)==tuple(w[5:7]))
  if w[3] in (99,100,102):
   names=[]
   for key in (b'TEXTURE1',b'TEXTURE2'):
    found=[l for l in lumps if l[2].rstrip(b'\0')==key]
    if not found:continue
    off,_,_=found[-1];count=struct.unpack_from('<I',wad,off)[0]
    for i in range(count):
     p=off+struct.unpack_from('<I',wad,off+4+4*i)[0];names.append(wad[p:p+8].rstrip(b'\0').decode())
   if w[4]<len(names):result['texture']=names[w[4]]
 if w[3] in (38,41):
  z=w[4] if w[3]==38 else w[6];result['view_height_map_units']=(z if z<0x80000000 else z-0x100000000)/65536
 if w[3] in (37,40):result['position_and_angle']=dict(x=(w[4] if w[4]<0x80000000 else w[4]-0x100000000)/65536,y=(w[5] if w[5]<0x80000000 else w[5]-0x100000000)/65536,degrees=w[6]*360/4294967296)
 fixed_fields={64:('z','floorz','ceilingz'),65:('x','y','sector_floor'),67:('viewheight','viewz','delta'),70:('z','floorz','ceilingz'),71:('viewheight','delta','bob'),73:('bob','momx','momy'),74:('viewz','z','viewheight'),75:('viewheight','bob','z'),76:('viewz','ceilingz','delta')}
 if w[3] in fixed_fields:result['fixed_16_16']={k:(v if v<0x80000000 else v-0x100000000)/65536 for k,v in zip(fixed_fields[w[3]],w[4:7])}
 if w[3]==63:result['spawn_selection']=dict(subsector=w[4],sector=w[5],input_z_hex=hex(w[6]))
 return result

def check(capture,build,wad=None):
 m=json.loads((build/'manifest.json').read_text());raw=(build/'startup-checkpoints.bin').read_bytes();assert hashlib.sha256(raw).hexdigest()==m['startup']['checkpoints_sha256'];oracle=list(struct.iter_unpack('<8I',raw));rows=[];epoch=None;uncertain=None
 lines=(capture/'engine-checkpoint-journal.jsonl').read_text().splitlines()
 for i,line in enumerate(lines):
  e=json.loads(line);q=bytes.fromhex(e['request']);assert len(q)==1056
  h=struct.unpack_from('<8I',q);assert h[0]==7 and 0<h[1]<=65535 and h[2:]==(4,0,0,0,0,0)
  index=struct.unpack_from('<I',q,32)[0];assert index==len(rows)+1 and index<=512 and not any(q[36:])
  if epoch is None:epoch=h[1]
  assert h[1]==epoch
  if 'errno' in e:
   assert i==len(lines)-1 and e['errno'] in (16,110);uncertain=e['errno'];continue
  s=bytes.fromhex(e['response']);assert len(s)==1056 and struct.unpack_from('<8I',s)==(7,epoch,32,1,0,0,0,0) and not any(s[64:])
  w=struct.unpack_from('<8I',s,32);assert w[0]==MAGIC
  if not w[1]:assert w[2]==len(rows) and not any(w[3:]);continue
  assert w[1]==index and w[2]>0 and w[3] in STAGES;rows.append(w)
 assert rows==[tuple(json.loads(l)) for l in (capture/'startup-checkpoints.jsonl').read_text().splitlines()]
 groups={}
 for w in rows:groups.setdefault(w[2],[]).append(w)
 assert list(groups)==list(range(4,4+len(groups))) and len(groups)<=3
 comparisons=[]
 for gen,observed in groups.items():
  # Each fresh image starts at stage 1; generation is intentionally different.
  assert observed[0][3:]==(1,0,0,0,0)
  idx=next((i for i,(a,b) in enumerate(zip(observed,oracle)) if a[3:]!=b[3:]),min(len(observed),len(oracle)))
  def desc(w):return describe(w,wad)
  comparisons.append(dict(generation=gen,records=len(observed),matching_prefix=idx,first_difference=None if idx==len(observed) else dict(card=desc(observed[idx]),host=desc(oracle[idx]) if idx<len(oracle) else None),last=desc(observed[-1])))
 return dict(accepted=False,diagnostic_only=True,validated_records=len(rows),oracle_records=len(oracle),epoch=epoch,uncertain_errno=uncertain,comparisons=comparisons)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--wad',type=Path);a=p.parse_args();r=check(a.capture,a.build,a.wad.read_bytes() if a.wad else None);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
