#!/usr/bin/env python3
"""Check bounded browser delivery against an already verified card capture."""
import argparse,hashlib,json,statistics,time,urllib.request
from pathlib import Path
from frame_client import png
p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();samples=[]
def get(name):
 t=time.monotonic_ns()
 with urllib.request.urlopen(urllib.request.Request(a.url.rstrip('/')+'/'+name,headers={'Cache-Control':'no-cache'}),timeout=10) as r:
  assert r.status==200;b=r.read()
 samples.append(dict(path=name,bytes=len(b),ms=(time.monotonic_ns()-t)/1e6));return b
page=get('index.html');assert b'Previous frame' in page and b'Next frame' in page and b'not interactive gameplay' in page
m=json.loads(get('frames.json'));assert m['width']==320 and m['height']==200 and len(m['frames'])==2
for i,row in enumerate(m['frames']):
 g=row['generation'];assert g in (1,2) and row['frame']==i and row['name']==f'card-{g}-{i}.png'
 raw=(a.capture/f'visible-{g}.bin').read_bytes();assert len(raw)==131072;frame=raw[i*65536:(i+1)*65536]
 assert hashlib.sha256(frame).hexdigest()==row['sha256'];expected=png(frame)
 for _ in range(5):assert get(row['name'])==expected
images=[s['ms'] for s in samples if s['path'].endswith('.png')]
a.output.write_text(json.dumps(dict(accepted=True,url=a.url,capture_generation=m['frames'][0]['generation'],full_png_bytes_match=True,samples=samples,mean_image_ms=statistics.mean(images),max_image_ms=max(images),rendering_fps_claim=False),indent=2)+'\n')
print('PASS HTTP page, manifest and 10 exact PNG responses; timings measure HTTP delivery, not card rendering')
