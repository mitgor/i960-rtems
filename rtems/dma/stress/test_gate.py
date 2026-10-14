#!/usr/bin/env python3
"""Use the existing real arena/admission test with a modeled stress STOP entry.
Requires a Linux 32-bit C/ASan toolchain, like the original admission test.
"""
import argparse,ast,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('admission',type=Path);a=p.parse_args();r=Path(__file__).resolve().parents[2]/'residentnet'
tree=ast.parse((r/'test_engine_gate.py').read_text());source=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='source' for t in n.targets))
source=source.replace('void doom_shared_yield(void){yields++;}', 'void doom_shared_yield(void){yields++;}\nvoid doom_shared_service(void){}')
begin=source.index('#ifdef ENGINE_STARTUP\n row[1]=2;');end=source.index('\n#endif',begin)+len('\n#endif')
source=source[:begin]+'''#ifndef ENGINE_DMA_STRESS
#error stress admission required
#endif
 memset(row,0,sizeof row);row[0]=0x454e4750;row[1]=3;row[2]=65536;row[5]=512;row[9]=2;row[10]=1;row[11]=210;
 if(mode==8)row[1]=2;if(mode==9)row[2]=6291456;if(mode==10)row[10]=0;
'''+source[end:]
source=source.replace('return mode==4?0x454e4702:0x454e4700;', 'return 0x454e4702;')
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp);(t/'test.c').write_text(source)
 subprocess.run(['gcc','-m32','-no-pie','-std=c11','-Os','-g','-fsanitize=address,undefined','-I'+str(r),'-I'+str(a.admission),str(t/'test.c'),str(r/'../../loader/digest/sha256.c'),str(r/'../../loader/segmented/image.c'),str(r/'../../loader/segmented/arena.c'),'-o',str(t/'test')],check=True)
 subprocess.run([str(t/'test'),str(a.admission/'template.bin'),str(a.admission/'relocations.bin')],check=True)
