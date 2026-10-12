#!/usr/bin/env python3
"""Generate a small trusted identity, not an embedded engine or relocation list."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('packed',type=Path);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
m=json.loads((a.packed/'manifest.json').read_text());b=(a.packed/'template.bin').read_bytes();assert m['linker_match'] and not m['admitted'] and hashlib.sha256(b).hexdigest()==m['template_sha256']
assert len(m['sections'])==3 and [s['name'] for s in m['sections']]==['.text','.data','.bss']
rows=subprocess.check_output([a.cross+'nm',str(a.build/'doom-platform.o')],text=True).splitlines();result=next(int(r.split()[0],16) for r in rows if r.split()[-1]=='_doom_engine_result')+m['sections'][2]['offset'];assert result+48<=m['memory_bytes']
sites=m['relocations'];assert sites==sorted(set(sites));meta=b''.join(struct.pack('<I',x) for x in sites);off=(m['memory_bytes']+15)&~15
for x in sites:assert x%4==0 and x+4<=len(b) and struct.unpack_from('<I',b,x)[0]<=m['memory_bytes']
m.update(result=result,metadata_offset=off,metadata_bytes=len(meta),metadata_sha256=hashlib.sha256(meta).hexdigest(),text_sha256=hashlib.sha256(b[:m['sections'][0]['file_bytes']]).hexdigest(),admission_bytes=off+len(meta))
(a.out/'template.bin').write_bytes(b);(a.out/'relocations.bin').write_bytes(meta);(a.out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
h='';names={'ENTRY':m['entry'],'FILE':len(b),'SPAN':m['memory_bytes'],'RESULT':result,'META':off,'SITES':len(sites),'TEXT':m['sections'][0]['file_bytes']}
for k,v in names.items():h+=f'#define ENGINE_{k} {v}u\n'
for k,v in [('image',m['template_sha256']),('metadata',m['metadata_sha256']),('text',m['text_sha256'])]:h+='static const unsigned char engine_'+k+'_sha[32]={'+','.join(str(x) for x in bytes.fromhex(v))+'};\n'
h+='static const unsigned engine_geometry[4][4]={'+','.join('{'+','.join(str(s[k]) for k in ('offset','file_bytes','memory_bytes','flags'))+'}' for s in m['sections'])+',{'+f'{off},{len(meta)},{len(meta)},2'+'}};\n'
(a.out/'engine_identity.h').write_text(h);print(json.dumps({k:v for k,v in m.items() if k not in ('relocations','sections')},indent=2))
