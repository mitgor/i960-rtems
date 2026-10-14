#!/usr/bin/env python3
"""Failed selector prefix only: no STOP/drain or performance acceptance claim."""
import hashlib,json,struct,subprocess,tarfile,tempfile
from pathlib import Path
out=Path(__file__).resolve().parent;r=Path(tempfile.mkdtemp(prefix='doom-selector-failed-'))
for name,sha in [('failed-selector-build.tar.gz','a9bfd475ad6eef1314824e0728e2d13d36eda50f4236ae4a4833b9e2de33d1ca'),('failed-selector-card.tar.gz','922aeb9daf3464c4a35a4dc5281ecfbdafa8c95bde89cbc29d481898a1cd2302')]:
 p=out/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
 with tarfile.open(p) as t:t.extractall(r,filter='data')
p=r/'project/rtems/residentnet/verify.py';s=p.read_text();s=s.replace("assert groups==[s['words'] for s in json.loads((out/'snapshots.json').read_text())]", "saved=[s['words'] for s in json.loads((out/'snapshots.json').read_text())];assert groups[:-1]==saved and groups[-1][1]>groups[-2][1];snapshot_gate(groups[-1],epoch,reset,owner,extra,heap);groups=groups[:-1];stops=stops[:-1]");s=s[:s.index(' assert groups[-1][2]==2')]+" return dict(full_audit_pairs=len(groups),additional_unpaired_monitor_pages=1,final_state=groups[-1][2],acceptance=False)\nprint(json.dumps(verify(Path(sys.argv[1]),Path(sys.argv[2]))))\n";p.with_name('verify_prefix.py').write_text(s)
x=subprocess.run(['python3',str(p.with_name('verify_prefix.py')),str(r/'build'),str(r/'compare')],capture_output=True,text=True);assert x.returncode==0,x.stderr
result=json.loads(x.stdout);d=r/'compare';raw=(d/'frame-dma-001.bin').read_bytes();assert len(raw)==73728 and raw[:4096]==raw[69632:]==b'\xa5'*4096;b=raw[4096:69632]
rows=[json.loads(s) for s in (d/'frame-journal.jsonl').read_text().splitlines()];assert len(rows)==65
assert b''.join(bytes.fromhex(row['response'])[32:] for row in rows[:64])==b
assert bytes.fromhex(rows[-1]['response'])[32:]==b[:1024]
n=(r/'native-frames/frame-1.bin').read_bytes();assert b[64000:64768]==n[64000:64768]
diff=sum(x!=y for x,y in zip(b[:64000],n[:64000]));assert diff==7
w=struct.unpack_from('<16I',b,64768);assert w[:4]==(0x31524650,1,1,2)
result.update(guarded_bytes=73728,paired_frame_equal=True,native_pixel_differences=diff,reported_mode=w[3],expected_mode=1,profile=list(w),stop_drain_proven=False)
(out/'failed-selector-prefix.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
