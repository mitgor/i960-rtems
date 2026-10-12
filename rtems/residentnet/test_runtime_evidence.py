#!/usr/bin/env python3
"""Reject altered physical runtime captures before accepting their claims."""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--wad',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();results=[]
for case in ('payload','sequence','crc','missing_reply','identity','oracle','probe','report'):
 with tempfile.TemporaryDirectory() as tmp:
  t=Path(tmp)
  for f in a.capture.iterdir():
   if f.is_file():(t/f.name).symlink_to(f.resolve())
  def write(name,data):
   dest=t/name;dest.unlink();dest.write_bytes(data)
  if case in ('payload','sequence','crc','missing_reply'):
   rows=[json.loads(s) for s in (a.capture/'wad-journal.jsonl').read_text().splitlines()];i=next(i for i,r in enumerate(rows) if r['op']==4)
   if case=='missing_reply':rows.pop(i)
   else:
    r=rows[i];raw=bytearray.fromhex(r['request']);raw[{'payload':64,'sequence':36,'crc':56}[case]]^=1;r['request']=raw.hex()
   write('wad-journal.jsonl',('\n'.join(json.dumps(r) for r in rows)+'\n').encode())
  elif case=='probe':
   b=bytearray((a.capture/'runtime-probe.bin').read_bytes());b[0]^=1;write('runtime-probe.bin',b)
  else:
   r=json.loads((a.capture/'runtime-results.json').read_text())
   if case=='identity':r['wad_sha256']='0'*64
   elif case=='oracle':r['oracle']^=1
   else:r['report'][2]+=1
   write('runtime-results.json',(json.dumps(r)+'\n').encode())
  run=subprocess.run(['python3',str(Path(__file__).with_name('verify_upload.py')),str(t),'--doom-heap','--doom-shared','--doom-runtime','--wad',str(a.wad),'--entry',str(a.capture.parent/'residentnet/entry/runtime-probe.bin'),'--output',str(t/'replay.json')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  assert run.returncode,(case,'corrupt evidence accepted');results.append(dict(case=case,rejected=True))
a.output.write_text(json.dumps(results,indent=2)+'\n');print('PASS: eight runtime capture mutations rejected')
