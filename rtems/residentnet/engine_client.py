"""One-shot full-engine-linked owned preflight, exact build only."""
import errno,hashlib,json,struct,time,zlib
from pathlib import Path
from owned_client import Control
from runtime_client import WadServer

def exercise(u,root,wad):
 root=Path(root);m=json.loads((root/'manifest.json').read_text());blob=(root/'template.bin').read_bytes();meta=(root/'relocations.bin').read_bytes()
 if m.get('startup'):
  from startup_client import exercise as startup
  return startup(u,root,wad)
 assert hashlib.sha256(blob).hexdigest()==m['template_sha256'] and hashlib.sha256(meta).hexdigest()==m['metadata_sha256']
 u.journal_namespace='engine-';server=WadServer(u,wad);rows=[]
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
   load(blob,meta);base=u.command(14)[5];ctl=Control(u,stopped)
   def serve():
    waiting=server.serve();ctl.serve();return waiting
   u.service=serve;start=time.monotonic()
   try:w=u.command(18,timeout=60)
   finally:u.service=None
   assert w[2]==0 and w[4]==0 and w[5]==(0x454e4702 if stopped else 0x454e4700)
   result=[u.command(19,i)[5] for i in range(12)];final=ctl.query();ctl.request(final[1],errno.ESTALE)
   assert result[:3]==[0x454e4750,1,6291456] and result[5]==1 and result[6]==int(not stopped) and result[9:]==[2 if stopped else 0,1,0] and not final[2]
   rows.append(dict(stop=stopped,base=0xc02d0040+base,seconds=time.monotonic()-start,result=result,value=w[5],control=list(final),requests=ctl.records))
  result=dict(manifest=m,wad_sha256=server.sha,requests=server.records,runs=rows,diagnostic_only=True)
  (u.out/'engine-results.json').write_text(json.dumps(result,indent=2)+'\n');(u.out/'engine-template.bin').write_bytes(blob);(u.out/'engine-relocations.bin').write_bytes(meta)
 finally:u.journal_namespace='';u.service=None
