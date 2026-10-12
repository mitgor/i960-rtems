#!/usr/bin/env python3
"""Replay exact scalar/BIO staging checks from the archived core rehearsals."""
from pathlib import Path
import argparse,hashlib,json,struct,sys,tarfile,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'host/loadrun'))
import buffer_io,loadrun
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
rows={};results=[]
with tarfile.open(a.archive) as t,tempfile.TemporaryDirectory() as temp:
 for m in t.getmembers():
  if m.isfile():rows[m.name]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
 for folder,payload,expected in [('live','target-first',0xb791f3dd),('live-data','target-data',0xe4f1e4e1),('live-final','target',0xe4f1e4e1)]:
  d=Path(temp)/folder;d.mkdir()
  for m in t.getmembers():
   if m.isfile() and m.name.startswith(folder+'/'):
    dest=Path(temp)/m.name
    if not dest.resolve().is_relative_to(d.resolve()):raise ValueError('unsafe archive member')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(t.extractfile(m).read())
  data=buffer_io.prepare(t.extractfile(payload+'/test.bin').read(),b'',8192,1,0)
  value=loadrun.verify(d,data);response=(d/'response.bin').read_bytes();words=struct.unpack_from('<5I',response)
  if words!=(0x31474553,0,expected,4,3728) or value or any(response[20:]):raise ValueError('unexpected test response')
  build=json.loads(t.extractfile(payload+'/build.json').read())
  if build['sha256']!=rows[payload+'/test.bin']:raise ValueError('binary hash mismatch')
  results.append(dict(capture=folder,return_value=value,computed_result=hex(words[2]),prepare_steps=words[3],arena_bytes=words[4],payload_sha256=build['sha256']))
 final=json.loads(t.extractfile('target/build.json').read())
 for name,h in final['sources'].items():
  if hashlib.sha256((Path(__file__).resolve().parent.parent/name).read_bytes()).hexdigest()!=h:raise ValueError('final source mismatch: '+name)
(a.output/'archive-members.json').write_text(json.dumps(rows,indent=2)+'\n')
(a.output/'replay.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: three actual-card captures, returned execution values, full RAM restoration, final source hashes; '+str(len(rows))+' archived files')
