#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('workspace',type=Path);a=p.parse_args();result={}
for name,trace in [('build',False),('build-fast',True)]:
 b=a.workspace/name;m=json.loads((b/'admission/manifest.json').read_text())
 assert m['fast_fixed_div'] and not m['fixed_div_profile'] and bool(m['input_trace'])==trace
 for key in ('frame_profile','cpu_profile','wad_profile','low_detail','direct_frame','no_fnv'):assert m[key]
 side=hashlib.sha256((b/'engine-cross/i960/r_point_side.o').read_bytes()).hexdigest()
 assert side=='beb7a66306aef9fa8a0cb4c0e18e81524b337c05f640897282c3f8bedcc6dd1b'
 divide=hashlib.sha256((b/'engine-cross/i960/fixed_divide.o').read_bytes()).hexdigest()
 assert divide=='c4e7e522441d9847d9c01b8ee9d33a6b39b5062a41833bc3bdc3c407ae5d30d4'
 nm=subprocess.check_output(['/home/mit/i960/tools/bin/i960-coff-nm',str(b/'platform-cross/doom-platform.o')],text=True)
 for symbol in ('_doom_div_profile','_doom_div_check','_doom_div_record'):assert symbol not in nm
 assert ('_doom_input_event' in nm)==trace
 result[name]=dict(input_trace=trace,fast_fixed_div=True,point_side_sha256=side,divide_sha256=divide,memory_bytes=m['memory_bytes'],file_bytes=m['file_bytes'])
print(json.dumps(result,indent=2))
