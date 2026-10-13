"""Bounded immutable card-frame retrieval and independent byte-for-byte replay."""
import errno,hashlib,json,struct,zlib
from pathlib import Path
TOTAL=131072

def png(frame):
 assert len(frame)==65536 and not any(frame[64768:]);pal=frame[64000:64768]
 raw=b''.join(b'\0'+b''.join(pal[x*3:x*3+3] for x in frame[y*320:(y+1)*320]) for y in range(200))
 def chunk(tag,b):return struct.pack('!I',len(b))+tag+b+struct.pack('!I',zlib.crc32(tag+b))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',320,200,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')

def publish(out,g,raw):
 out=Path(out);out.mkdir(exist_ok=True)
 rows=[]
 for i in range(2):
  f=raw[i*65536:(i+1)*65536];name=f'card-{g}-{i}.png';(out/name).write_bytes(png(f));rows.append(dict(name=name,frame=i,generation=g,sha256=hashlib.sha256(f).hexdigest()))
 manifest=dict(width=320,height=200,source='i960 card readback; exact native comparison passed',frames=rows)
 tmp=out/'frames.tmp';tmp.write_text(json.dumps(manifest));tmp.replace(out/'frames.json')
 (out/'index.html').write_text('''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Doom on i960 — bounded frames</title>
<style>body{background:#101217;color:#eee;font:16px system-ui;max-width:960px;margin:32px auto;padding:0 20px}img{width:100%;height:auto;image-rendering:pixelated;background:#000}button{padding:12px;margin:12px 8px 12px 0}p{color:#c8cbd2}</style>
<h1>Doom on the Mylex i960</h1><p>Two bounded demo frames, rendered on the card. The opening wipe is skipped. This is a verified capture, not interactive gameplay.</p>
<img id="screen" width="640" height="400" alt="Captured Doom frame"><div><button id="prev">Previous frame</button><button id="next">Next frame</button><button id="refresh">Refresh capture</button></div><p id="status">Loading capture…</p><code id="hash"></code>
<script>let data,index=0;function show(){const f=data.frames[index];screen.src=f.name;document.getElementById('status').textContent=`Frame ${index+1} of ${data.frames.length} · capture ${f.generation} · 320 × 200 · ${data.source}`;document.getElementById('hash').textContent='Frame + palette + padding SHA256: '+f.sha256;}async function load(){data=await(await fetch('frames.json',{cache:'no-store'})).json();index=0;show();}document.getElementById('prev').onclick=()=>{index=(index+data.frames.length-1)%data.frames.length;show()};document.getElementById('next').onclick=()=>{index=(index+1)%data.frames.length;show()};document.getElementById('refresh').onclick=load;load().catch(e=>document.getElementById('status').textContent=e.message);</script>'''.replace('screen.src=f.name',"document.getElementById('screen').src=f.name"))

def capture_frames(u,build,g):
 expected=(Path(build)/'visible-frames.bin').read_bytes();assert len(expected)==TOTAL
 def reject(g,off,error):
  try:u.io(9,struct.pack('<2I',g,off));raise AssertionError('invalid frame request accepted')
  except OSError as e:assert e.errno==error
 if not g:reject(1,0,errno.ESTALE);return
 reject(g+9,0,errno.ESTALE);reject(g,TOTAL,errno.EINVAL)
 raw=b''.join(u.io(9,struct.pack('<2I',g,off)) for off in range(0,TOTAL,1024))
 assert raw==expected and u.io(9,struct.pack('<2I',g,0))==raw[:1024]
 (u.out/f'visible-{g}.bin').write_bytes(raw);publish(u.out/'browser',g,raw)

def verify_frames(capture,build):
 capture=Path(capture);build=Path(build);m=json.loads((build/'manifest.json').read_text());want=(build/'visible-frames.bin').read_bytes()
 assert len(want)==TOTAL and hashlib.sha256(want).hexdigest()==m['startup']['frames_sha256']
 rows=[json.loads(x) for x in (capture/'engine-frame-journal.jsonl').read_text().splitlines()];expected=[]
 for g in (1,0,2):
  if not g:expected.append((1,0,errno.ESTALE));continue
  expected.extend([(g+9,0,errno.ESTALE),(g,TOTAL,errno.EINVAL)])
  expected.extend((g,off,0) for off in range(0,TOTAL,1024));expected.append((g,0,0))
 assert len(rows)==len(expected);epochs=set();ns=[]
 for row,(g,off,error) in zip(rows,expected):
  q=bytes.fromhex(row['request']);assert len(q)==1056;h=struct.unpack_from('<8I',q);assert h[0]==9 and h[1] and h[2:]==(8,0,0,0,0,0);epochs.add(h[1]);assert struct.unpack_from('<2I',q,32)==(g,off) and not any(q[40:])
  if error:assert row['errno']==error and 'response' not in row;continue
  assert 'errno' not in row;s=bytes.fromhex(row['response']);assert len(s)==1056 and struct.unpack_from('<8I',s)==(9,h[1],1024,1,0,0,0,0) and s[32:]==want[off:off+1024];ns.append(row['ns'])
 assert len(epochs)==1
 owned=json.loads((capture/'engine-owned-journal.jsonl').read_text().splitlines()[0]);assert epochs=={struct.unpack_from('<I',bytes.fromhex(owned['request']),4)[0]}
 for g in (1,2):
  assert (capture/f'visible-{g}.bin').read_bytes()==want
  for i in range(2):assert (capture/'browser'/f'card-{g}-{i}.png').read_bytes()==png(want[i*65536:(i+1)*65536])
 result=dict(accepted=True,bytes_per_capture=TOTAL,captures=2,full_native_bytes_match=True,successful_reads=len(ns),refusals=5,readback_seconds=sum(ns)/1e9,mean_ioctl_ms=sum(ns)/len(ns)/1e6,frames_sha256=hashlib.sha256(want).hexdigest())
 return result
