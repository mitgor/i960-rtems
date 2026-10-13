#!/usr/bin/env python3
"""Independent pinned-WAD player-spawn geometry reference (not ISA execution)."""
import argparse,hashlib,json,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('wad',type=Path);p.add_argument('--map',default='E1M6');p.add_argument('--compiled-axis-cc',action='store_true',help='Model the captured r_main.o compare/branch/test ordering; not ISA execution');p.add_argument('--output',type=Path,required=True);a=p.parse_args();data=a.wad.read_bytes()
assert hashlib.sha256(data).hexdigest()=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
n,d=struct.unpack_from('<2I',data,4);directory=[struct.unpack_from('<II8s',data,d+16*i) for i in range(n)];base=next(i for i,l in enumerate(directory) if l[2].rstrip(b'\0').decode()==a.map)
def lump(relative,name):
 off,size,key=directory[base+relative];assert key.rstrip(b'\0').decode()==name and off+size<=len(data);return data[off:off+size]
things=list(struct.iter_unpack('<5h',lump(1,'THINGS')));player=next(t for t in things if t[3]==1);x,y=player[0]*65536,player[1]*65536
lines=list(struct.iter_unpack('<7H',lump(2,'LINEDEFS')));sides=lump(3,'SIDEDEFS');segs=list(struct.iter_unpack('<6H',lump(5,'SEGS')));subs=list(struct.iter_unpack('<2H',lump(6,'SSECTORS')));nodes=list(struct.iter_unpack('<12h2H',lump(7,'NODES')));sectors=lump(8,'SECTORS');assert len(sectors)%26==len(sides)%30==0
heights=[struct.unpack_from('<2h',sectors,i) for i in range(0,len(sectors),26)]
def signed(v):return (v+0x80000000)%0x100000000-0x80000000
def mul(a,b):return signed((a*b)>>16)
route=[];index=len(nodes)-1
while not index&0x8000:
 assert len(route)<=len(nodes) and 0<=index<len(nodes)
 node=nodes[index];nx,ny,ndx,ndy=[v*65536 for v in node[:4]];detail={}
 if not ndx:
  side=(int(nx>x) if x<=nx else int(ndy<0)) if a.compiled_axis_cc else (int(ndy>0) if x<=nx else int(ndy<0));kind='vertical'
 elif not ndy:
  side=(int(ndx<0) if y<=ny else 0) if a.compiled_axis_cc else (int(ndx<0) if y<=ny else int(ndx>0));kind='horizontal'
 else:
  dx,dy=signed(x-nx),signed(y-ny)
  if (ndy^ndx^dx^dy)&0x80000000:side=int(bool((ndy^dx)&0x80000000));kind='sign shortcut'
  else:
   left,right=mul(ndy>>16,dx),mul(dy,ndx>>16);side=int(right>=left);kind='fixed multiply';detail=dict(left=left,right=right,dx=dx,dy=dy)
 child=node[12+side];route.append(dict(node=index,partition=list(node[:4]),branch=kind,side=side,child=child,**detail));index=child
sub=index&0x7fff;num,first=subs[sub];assert num>0;seg=segs[first];line=lines[seg[3]];side=line[5+seg[4]];sector=struct.unpack_from('<H',sides,side*30+28)[0];floor,ceiling=heights[sector]
h=2166136261
for pair in heights:
 for value in pair:
  for b in struct.pack('<I',(value*65536)&0xffffffff):h=((h^b)*16777619)&0xffffffff
out=dict(diagnostic_only=True,not_card_execution=True,compiled_axis_cc=a.compiled_axis_cc,map=a.map,map_lump_index=base,player_mapthing=list(player),sector_height_fingerprint=h,sector_count=len(heights),route=route,subsector=sub,first_seg=first,linedef=seg[3],sidedef=side,sector=sector,floor=floor,ceiling=ceiling,stationary_view_height=min(floor+41,ceiling-4))
a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='route'},indent=2))
