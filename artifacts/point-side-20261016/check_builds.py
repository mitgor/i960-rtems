#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('workspace',type=Path);a=p.parse_args();a.workspace=a.workspace.resolve();result={}
for name,fast in [('build',False),('build-fast',True)]:
 b=a.workspace/name;m=json.loads((b/'admission/manifest.json').read_text());engine=json.loads((b/'engine-cross/i960/build.json').read_text())
 assert m['fast_point_side']==fast and engine['fast_point_side']==fast
 assert m['fast_fixed_div'] and not m['fixed_div_profile'] and not m['input_trace']
 for key in ('frame_profile','cpu_profile','wad_profile','low_detail','direct_frame','no_fnv','fast_columns','fast_render'):assert m[key]
 side=hashlib.sha256((b/'engine-cross/i960/r_point_side.o').read_bytes()).hexdigest()
 assert side==('6c5e16fcd090c0c3ee00f0a90aa24d85844821b1366226141d340201c1795180' if fast else 'beb7a66306aef9fa8a0cb4c0e18e81524b337c05f640897282c3f8bedcc6dd1b')
 commands=[c for c in engine['commands'] if c[-3].endswith('r_point_side.c')]
 assert len(commands)==1 and ('-O0' in commands[0])!=fast
 divide=hashlib.sha256((b/'engine-cross/i960/fixed_divide.o').read_bytes()).hexdigest()
 assert divide=='c4e7e522441d9847d9c01b8ee9d33a6b39b5062a41833bc3bdc3c407ae5d30d4'
 result[name]=dict(fast_point_side=fast,point_side_sha256=side,divide_sha256=divide,memory_bytes=m['memory_bytes'],file_bytes=m['file_bytes'])
# Two unchanged assertion-bearing sources also embed the distinct absolute build paths.
old=a.workspace/'build/engine-cross/i960';new=a.workspace/'build-fast/engine-cross/i960'
changed=[p.name for p in old.glob('*.o') if p.read_bytes()!=(new/p.name).read_bytes()]
assert sorted(changed)==['doom-engine.o','r_data.o','r_point_side.o','w_wad.o'],changed
for name in ('r_data','w_wad'):
 left=a.workspace/'build/engine-cross/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric'/(name+'.c')
 right=a.workspace/'build-fast/engine-cross/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric'/(name+'.c')
 assert left.read_bytes()==right.read_bytes()
 assert str(left).encode() in (old/(name+'.o')).read_bytes()
 assert str(right).encode() in (new/(name+'.o')).read_bytes()
source=a.workspace/'build-fast/engine-cross/doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric/r_point_side.c'
assert source.read_bytes()==(a.workspace/'project/game/doom/point_side/point.c').read_bytes()
dis=subprocess.check_output(['/home/mit/i960/tools/bin/i960-coff-objdump','-dr',str(new/'r_point_side.o')],text=True)
lines=dis.splitlines();tests=[i for i,line in enumerate(lines) if '\ttestle\t' in line]
assert len(tests)==3 and all('\tcmpi\t' in lines[i-1] for i in tests)
assert '\tcall' not in dis
result['candidate_compare_pairs']=3
result['candidate_call_free']=True
result['changed_engine_objects']=changed
print(json.dumps(result,indent=2))
