#!/usr/bin/env python3
"""Compile actual Doom/zone/API layout constants for both 32-bit ABIs."""
import argparse,json,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--doom',type=Path,required=True);p.add_argument('--newlib',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);r=Path(__file__).resolve().parent
names=['int','long','short','int64_t','mapthing_t','maplinedef_t','mapsidedef_t','mapvertex_t','mapsector_t','mapseg_t','mapnode_t','mapsubsector_t','ticcmd_t','vertex_t','side_t','seg_t','sector_t','line_t','mobj_t','memblock_t','memzone_t','struct doom_runtime_v1','struct doom_runtime_owned']
expressions=[];labels=[]
for name in names:
 for op in ('sizeof','__alignof__'):expressions.append(f'{op}({name})');labels.append(f'{op} {name}')
for name in ('allocate','release','ticks_ms','read'):
 expressions.append(f'offsetof(struct doom_runtime_v1,{name})');labels.append('API offset '+name)
for name in ('io','magic','owner','wait_ms','stopping'):
 expressions.append(f'offsetof(struct doom_runtime_owned,{name})');labels.append('owned offset '+name)
source=a.out/'layout.c';source.write_text('#include <stddef.h>\n#include <stdint.h>\n#include "doomdata.h"\n#include "r_defs.h"\n#include "d_ticcmd.h"\n#include "z_zone.c"\n#include "api.h"\nunsigned abi_sizes[]={'+','.join(expressions)+'};\n')
def constants(obj):
 b=obj.read_bytes();h=struct.unpack_from('<16sHHIIIIIHHHHHH',b);assert b[:7]==b'\x7fELF\x01\x01\x01';sections=[struct.unpack_from('<10I',b,h[6]+i*40) for i in range(h[12])]
 for s in sections:
  if s[1]!=2:continue
  t=sections[s[6]];strings=b[t[4]:t[4]+t[5]]
  for i in range(s[4],s[4]+s[5],16):
   off,value,size,info,other,index=struct.unpack_from('<IIIBBH',b,i)
   if strings[off:strings.find(b'\0',off)] in (b'abi_sizes',b'_abi_sizes'):
    section=sections[index];return list(struct.unpack_from('<'+str(len(labels))+'I',b,section[4]+value-section[3]))
 raise AssertionError('ABI constants missing')
rows={}
for name,cc,flags in [('host','gcc',['-m32','-D__SINGLE_THREAD__']),('i960-default',a.cross+'gcc',['-mrp']),('i960-private',a.cross+'gcc',['-mrp','-mold-align'])]:
 obj=a.out/(name+'.o');cmd=[cc,*flags,'-I'+str(a.doom),'-I'+str(r.parents[1]/'include'),'-I'+str(a.newlib/'newlib/libc/include'),'-I'+str(r.parent/'owned'),'-c',str(source),'-o',str(obj)];subprocess.run(cmd,check=True);rows[name]=dict(zip(labels,constants(obj)))
for label in labels:
 assert rows['host'][label]==rows['i960-private'][label],(label,rows['host'][label],rows['i960-private'][label])
for name in ('memblock_t','memzone_t'):assert rows['i960-private']['__alignof__ '+name]<=4 and rows['i960-private']['sizeof '+name]%4==0
for label in labels:
 if label.startswith(('API offset','owned offset')) or label in ('sizeof struct doom_runtime_v1','sizeof struct doom_runtime_owned'):assert rows['i960-default'][label]==rows['i960-private'][label]
assert rows['i960-default']['sizeof side_t']==32 and rows['i960-private']['sizeof side_t']==20
(a.out/'layout.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS actual Doom/zone layouts match host; runtime API sizes/offsets unchanged')
