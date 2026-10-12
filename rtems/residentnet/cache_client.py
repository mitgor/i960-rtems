"""Physical cache bridge acceptance with exact host file and failure injection."""
import hashlib,json,time,zlib,struct
from pathlib import Path
from runtime_client import WadServer

def exercise(u,wad,root):
 root=Path(root);m=json.loads((root/'manifest.json').read_text());b=(root/'template.bin').read_bytes();server=WadServer(u,wad)
 assert hashlib.sha256(b).hexdigest()==m['sha256']
 u.command(15,expected=1);s=m['sections'][0]
 bad=bytearray(b);bad[0]^=1
 u.begin([(s['offset'],s['file_bytes'],s['memory_bytes'],s['flags'],zlib.crc32(bad))],m['entry']);u.write(0,bad);u.prepare();u.command(15,expected=2);u.command(5)
 u.begin([(s['offset'],s['file_bytes'],s['memory_bytes'],s['flags'],zlib.crc32(b))],m['entry']);u.command(15,expected=1);u.write(0,b);u.prepare();base=u.command(14)[5]
 data=server.data;directory=struct.unpack_from('<I',data,8)[0];oracle=2166136261
 for byte in data[:12]+data[499:1610]+data[directory:directory+512]+data[-37:]:oracle=((oracle^byte)*16777619)&0xffffffff
 rows=[];u.service=server.serve
 try:
  for mode in ('normal','crc','short','host-error','timeout','normal'):
   server.mode=mode;server.injected=False;start=time.monotonic();w=u.command(15,timeout=60);assert w[5]==(oracle if mode=='normal' else 3) and w[4]==3
   rows.append(dict(mode=mode,result=w[5],seconds=time.monotonic()-start))
 finally:u.service=None
 report=[u.command(12,i)[5] for i in range(8)];assert report[5:7]==[0,0]
 u.command(5)
 result=dict(manifest=m,wad_sha256=server.sha,base=0xc02d0040+base,oracle=oracle,runs=rows,requests=server.records,report=report)
 (u.out/'cache-results.json').write_text(json.dumps(result,indent=2)+'\n');(u.out/'cache-template.bin').write_bytes(b)
