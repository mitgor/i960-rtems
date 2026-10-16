#!/usr/bin/env python3
"""Generate a small trusted identity, not an embedded engine or relocation list."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('packed',type=Path);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--startup-requests',type=Path);p.add_argument('--startup-checkpoints',type=Path);p.add_argument('--checkpoint-barriers',action='store_true');p.add_argument('--startup-oracle',type=Path);p.add_argument('--play',action='store_true');p.add_argument('--dma-stress',action='store_true');p.add_argument('--pingpong',action='store_true');p.add_argument('--cross',required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
assert not a.checkpoint_barriers or (a.startup_oracle and a.startup_checkpoints)
m=json.loads((a.packed/'manifest.json').read_text());b=(a.packed/'template.bin').read_bytes();assert m['linker_match'] and not m['admitted'] and hashlib.sha256(b).hexdigest()==m['template_sha256']
assert len(m['sections'])==3 and [s['name'] for s in m['sections']]==['.text','.data','.bss']
rows=subprocess.check_output([a.cross+'nm',str(a.build/'doom-platform.o')],text=True).splitlines();result=next(int(r.split()[0],16) for r in rows if r.split()[-1]=='_doom_engine_result')+m['sections'][2]['offset'];assert result+48<=m['memory_bytes']
sites=m['relocations'];assert sites==sorted(set(sites));meta=b''.join(struct.pack('<I',x) for x in sites);off=(m['memory_bytes']+15)&~15
for x in sites:assert x%4==0 and x+4<=len(b) and struct.unpack_from('<I',b,x)[0]<=m['memory_bytes']
m.update(result=result,metadata_offset=off,metadata_bytes=len(meta),metadata_sha256=hashlib.sha256(meta).hexdigest(),text_sha256=hashlib.sha256(b[:m['sections'][0]['file_bytes']]).hexdigest(),admission_bytes=off+len(meta))
assert not a.dma_stress or (a.play and json.loads((a.build/'build.json').read_text()).get('dma_stress')==1)
if a.play:
 assert not a.startup_oracle and not a.checkpoint_barriers
 assert json.loads((a.build/'build.json').read_text()).get('play')
 m['startup']={'play':True,'checkpoint_api':True}
 frame_offset=next(int(r.split()[0],16) for r in rows if r.split()[-1]=='_doom_platform_frames')+m['sections'][2]['offset']
 assert frame_offset>=m['sections'][2]['offset'] and frame_offset+131072<=m['memory_bytes']
 assert m['admission_bytes']<=900000
 m['play_offset']=frame_offset
 for key in ('fast_point_side','input_trace','fixed_div_profile','fast_fixed_div','runtime_detail','fast_columns','fast_render','fast_memory','wad_profile','frame_profile','no_fnv','direct_frame','presentation_test','low_detail','detail_test','cpu_profile','column_test'):m[key]=bool(json.loads((a.build/'build.json').read_text()).get(key))
 m['double_buffer']=bool(json.loads((a.build/'build.json').read_text()).get('double_buffer'))
 if a.dma_stress:
  m['dma_stress']=1
  m['pingpong']=bool(json.loads((a.build/'build.json').read_text()).get('pingpong'))
if a.pingpong:
 assert a.play and m['double_buffer']
 m['pingpong']=True
if a.startup_oracle:
 oracle=json.loads(a.startup_oracle.read_text());assert oracle['exact_bytes_match'] and ((oracle.get('visible') and oracle['frame_count']==2 and oracle['frame']==1) or (not oracle.get('visible') and oracle['frame']==0 and oracle['gametic']==2))
 assert a.startup_requests
 trace=a.startup_requests.read_bytes();assert len(trace)==oracle.get('request_count',4747)*8
 oracle['requests_sha256']=hashlib.sha256(trace).hexdigest()
 (a.out/'startup-requests.bin').write_bytes(trace)
 if a.startup_checkpoints:
  cp=a.startup_checkpoints.read_bytes();assert cp and len(cp)%32==0
  (a.out/'startup-checkpoints.bin').write_bytes(cp);oracle['checkpoints_sha256']=hashlib.sha256(cp).hexdigest()
 if a.checkpoint_barriers:oracle['checkpoint_barriers']=1
 if oracle.get('visible'):
  frames=(a.startup_oracle.parent/'visible-frames.bin').read_bytes();assert len(frames)==131072 and hashlib.sha256(frames).hexdigest()==oracle['frames_sha256']
  frame_offset=next(int(r.split()[0],16) for r in rows if r.split()[-1]=='_doom_platform_frames')+m['sections'][2]['offset']
  assert frame_offset>=m['sections'][2]['offset'] and frame_offset+len(frames)<=m['memory_bytes']
  m['visible_offset']=frame_offset;(a.out/'visible-frames.bin').write_bytes(frames)
 m['startup']=oracle
 assert m['admission_bytes']<=900000, 'native startup reservation proof exceeded'
(a.out/'template.bin').write_bytes(b);(a.out/'relocations.bin').write_bytes(meta);(a.out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
h='';names={'ENTRY':m['entry'],'FILE':len(b),'SPAN':m['memory_bytes'],'RESULT':result,'META':off,'SITES':len(sites),'TEXT':m['sections'][0]['file_bytes']}
for k,v in names.items():h+=f'#define ENGINE_{k} {v}u\n'
for k,v in [('image',m['template_sha256']),('metadata',m['metadata_sha256']),('text',m['text_sha256'])]:h+='static const unsigned char engine_'+k+'_sha[32]={'+','.join(str(x) for x in bytes.fromhex(v))+'};\n'
h+='static const unsigned engine_geometry[4][4]={'+','.join('{'+','.join(str(s[k]) for k in ('offset','file_bytes','memory_bytes','flags'))+'}' for s in m['sections'])+',{'+f'{off},{len(meta)},{len(meta)},2'+'}};\n'
if a.play:h+='#define ENGINE_STARTUP 1\n#define ENGINE_PLAYABLE 1\n#define ENGINE_PLAY_OFFSET '+str(m['play_offset'])+'u\n'
# Renderer trailers remain in the engine; ping-pong uses completion-marker timing
# instead of the legacy per-frame DMA timing query ABI.
if m.get('frame_profile') and not m.get('pingpong'):h+='#define ENGINE_FRAME_PROFILE 1\n'
if m.get('cpu_profile'):h+='#define ENGINE_CPU_PROFILE 1\n'
if m.get('double_buffer'):h+='#define ENGINE_PLAY_DOUBLE 1\n'
if a.startup_oracle:h+='#define ENGINE_STARTUP 1\n#define ENGINE_FRAME '+str(oracle['frame_fnv'])+'u\n#define ENGINE_PALETTE '+str(oracle['palette_fnv'])+'u\n'
if m.get('startup',{}).get('visible'):
 h+='#define ENGINE_FRAME_COUNT 2u\n#define ENGINE_VISIBLE_OFFSET '+str(m['visible_offset'])+'u\n'
 h+='static const unsigned char engine_visible_sha[32]={'+','.join(str(x) for x in bytes.fromhex(oracle['frames_sha256']))+'};\n'
if m.get('pingpong'):assert a.play and m['double_buffer']
if m.get('pingpong'):h+='#define ENGINE_PINGPONG 1\n'
if a.dma_stress:h+='#define ENGINE_DMA_STRESS 1\n'
(a.out/'engine_identity.h').write_text(h);print(json.dumps({k:v for k,v in m.items() if k not in ('relocations','sections')},indent=2))
