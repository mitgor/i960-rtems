"""One-shot actual Doom startup, bounded first-frame acceptance."""
import errno,hashlib,json,struct,time,zlib
from pathlib import Path
from owned_client import Control
from batch_client import BatchServer

def exercise(u,root,wad):
 root=Path(root);m=json.loads((root/'manifest.json').read_text());blob=(root/'template.bin').read_bytes();meta=(root/'relocations.bin').read_bytes()
 assert hashlib.sha256(blob).hexdigest()==m['template_sha256'] and hashlib.sha256(meta).hexdigest()==m['metadata_sha256']
 u.journal_namespace='engine-';server=BatchServer(u,wad);rows=[]
 from checkpoint_client import Checkpoints
 checkpoints=Checkpoints(u,barriers=bool(m['startup'].get('checkpoint_barriers'))) if m['startup'].get('checkpoints_sha256') else None
 def load(b,metadata):
  parts=[b[s['offset']:s['offset']+s['file_bytes']] for s in m['sections']]+[metadata]
  geometry=[(s['offset'],s['file_bytes'],s['memory_bytes'],s['flags']) for s in m['sections']]+[(m['metadata_offset'],len(meta),len(meta),2)]
  u.begin([(*s,zlib.crc32(p)) for s,p in zip(geometry,parts)],m['entry'])
  for i,p in enumerate(parts):
   if p:u.write(i,p)
  u.prepare()
 try:
  u.command(18,expected=1)
  # Correct segment CRCs do not authorize altered executable or recipe bytes.
  bad=bytearray(blob);bad[0]^=1;load(bad,meta);u.command(18,expected=2,timeout=60);u.command(5)
  bad=bytearray(meta);bad[0]^=1;load(blob,bad);u.command(18,expected=2,timeout=60);u.command(5)
  for stopped in (False,True,False):
   load(blob,meta);base=u.command(14)[5];ctl=Control(u,False);server.mode="stop" if stopped else "normal";server.injected=False;first=len(server.records)
   def serve():
    if checkpoints:checkpoints.pump()
    return server.serve()
   u.service=serve;start=time.monotonic()
   try:w=u.command(18,timeout=1860)
   finally:u.service=None
   if checkpoints:checkpoints.pump(True)
   assert w[2]==0 and w[4]==0
   # Preserve a cleanly returned engine error/deadline report before rejecting
   # it as an unexpected outcome; never turn that report into acceptance.
   result=[u.command(19,i)[5] for i in range(12)];final=ctl.query();ctl.request(final[1],errno.ESTALE)
   with (u.out/'startup-attempts.jsonl').open('a') as f:f.write(json.dumps(dict(stop=stopped,seconds=time.monotonic()-start,value=w[5],result=result,control=list(final)))+'\n')
   assert w[5]==(0x454e4702 if stopped else 0x454e4700)
   assert result[:3]==[0x454e4750,2,6291456] and result[5:7]==([0,0] if stopped else [m['startup'].get('frame_count',1),1]) and result[9:]==[2 if stopped else 0,1,210 if stopped else 213] and not final[2]
   if not stopped:assert result[3:5]==[m['startup']['frame_fnv'],m['startup']['palette_fnv']]
   if m['startup'].get('visible'):
    from frame_client import capture_frames
    capture_frames(u,root,0 if stopped else 1 if not rows else 2)
   assert server.injected==stopped
   if stopped:assert server.stop_generation==final[1]
   rows.append(dict(stop=stopped,base=0xc02d0040+base,seconds=time.monotonic()-start,result=result,value=w[5],control=list(final),requests=server.records[first:]))
   (u.out/'startup-progress.json').write_text(json.dumps(rows,indent=2)+'\n')
  result=dict(manifest=m,wad_sha256=server.sha,requests=server.records,runs=rows,diagnostic_only=False,startup=True)
  (u.out/'engine-results.json').write_text(json.dumps(result,indent=2)+'\n');(u.out/'engine-template.bin').write_bytes(blob);(u.out/'engine-relocations.bin').write_bytes(meta)
 finally:u.journal_namespace='';u.service=None
