#!/usr/bin/env python3
import hashlib,json,subprocess
from pathlib import Path
root=Path('/home/mit/i960-span-four-20261016');result={}
for name in ('build','build-fast'):
 b=root/name;m=json.loads((b/'admission/manifest.json').read_text());e=b/'engine-cross/i960';opts=json.loads((e/'build.json').read_text())
 assert not m['wall_profile'] and not m['fast_walls'] and m['span_four']==(name=='build-fast')
 assert m['fast_fixed_div'] and not m['fixed_div_profile'] and not m['input_trace'] and not m['fast_point_side']
 for k in ('frame_profile','cpu_profile','wad_profile','low_detail','direct_frame','no_fnv','fast_columns','fast_render'):assert m[k]
 assert hashlib.sha256((e/'r_point_side.o').read_bytes()).hexdigest()=='beb7a66306aef9fa8a0cb4c0e18e81524b337c05f640897282c3f8bedcc6dd1b'
 assert hashlib.sha256((e/'fixed_divide.o').read_bytes()).hexdigest()=='c4e7e522441d9847d9c01b8ee9d33a6b39b5062a41833bc3bdc3c407ae5d30d4'
 cmd=next(c for c in opts['commands'] if c[-3].endswith('/r_segs.c'))
 assert '-O2' not in cmd
 assert m['memory_bytes']<=900000
 platform=json.loads((b/'platform-cross/build.json').read_text())
 assert platform['final_link_passed'] and not platform['undefined']
 for obj in ('r_draw',):
  (b/(obj+'.disassembly.txt')).write_text(subprocess.check_output(['/home/mit/i960/tools/bin/i960-coff-objdump','-Dr',str(e/(obj+'.o'))],text=True))
 result[name]=dict(memory_bytes=m['memory_bytes'],file_bytes=m['file_bytes'],span_four=m['span_four'])
a=root/'build/engine-cross/i960';b=root/'build-fast/engine-cross/i960'
changed=sorted(p.name for p in a.glob('*.o') if p.read_bytes()!=(b/p.name).read_bytes())
assert changed==['doom-engine.o','r_data.o','r_draw.o','w_wad.o'],changed
for name in ('r_draw','r_data','w_wad'):
 rel='engine-cross/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric/'+name+'.c'
 assert (root/'build'/rel).read_bytes()==(root/'build-fast'/rel).read_bytes()
assert (a/'r_draw.o').read_bytes()==Path('/home/mit/i960-walls-20261016/build-plain/engine-cross/i960/r_draw.o').read_bytes()
result['baseline_r_draw_matches_accepted_plain']=True
result['changed_objects']=changed
print(json.dumps(result,indent=2))
