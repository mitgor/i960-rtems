#!/usr/bin/env python3
"""Replay exact archived build/capture; WAD stays separately pinned by SHA-256."""
import argparse,hashlib,json,statistics,subprocess,tarfile,tempfile,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--wad',type=Path,required=True);a=p.parse_args();b=Path(__file__).resolve().parent
out=Path(tempfile.mkdtemp(prefix='doom-columns-replay-'))
for name in ('build-evidence.tar.gz','card-evidence.tar.gz'):
 with tarfile.open(b/name) as t:t.extractall(out,filter='data')
r=out/'project';c=out/'live'
for name,args in [('system',['rtems/residentnet/verify.py','--root',str(out/'build'),str(c)]),('frames',['rtems/residentnet/verify_play_pipeline.py',str(c)]),('wad',['rtems/dma/verify_wad.py',str(c),'--wad',str(a.wad.resolve())])]:
 run=subprocess.run(['python3',str(r/args[0]),*args[1:]],capture_output=True,text=True,check=True);(b/f'local-{name}.json').write_text(run.stdout)
run=subprocess.run(['python3',str(b/'analyze.py'),str(c),'--native',str(out/'native-frames')],capture_output=True,text=True,check=True);(b/'local-measurements.json').write_text(run.stdout)
for g in range(17,41):assert (c/f'play-0-{g}.bin').read_bytes()[:64768]==(out/'prior-low'/f'play-0-{g}.bin').read_bytes()[:64768], g
rows=[json.loads(x) for x in (b/'http-observations.jsonl').read_text().splitlines()]
for row in rows:assert hashlib.sha256((c/('play-'+row['frame']+'.bin')).read_bytes()).hexdigest()==row['payload_sha256']
(b/'http-verification.json').write_text(json.dumps(dict(observed_frames=len(rows),generations=[x['frame'] for x in rows],all_payload_hashes_match=True,mean_fetch_ms=statistics.mean(x['fetch_seconds'] for x in rows)*1000),indent=2)+'\n')
sys.path.insert(0,str(r/'rtems/residentnet'));from frame_client import png
for g,name in [(12,'baseline'),(28,'c'),(40,'assembly')]:
 raw=(c/f'play-0-{g}.bin').read_bytes()
 # Image export uses only pixels/palette; raw captured timing trailer is retained.
 (b/f'card-{name}.png').write_bytes(png(raw[:64768]+bytes(768)))
print('PASS local system/frame/WAD/HTTP replay; extracted evidence:',out)
