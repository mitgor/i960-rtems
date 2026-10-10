#!/usr/bin/env python3
"""Offline RTEMS trace, RAM restoration, workspace guard and stack audit."""
import argparse,gzip,hashlib,json,struct
from pathlib import Path
from run import verify_close
import wire

def symbols(path):
 result={}
 for line in path.read_text().splitlines():
  words=line.split()
  if len(words)==3:
   try:result[words[2]]=int(words[0],16)-0xc0f2c000
   except ValueError:pass
 return result

def validate(folder,code,symbol_file=None):
 verify_close(folder/'close');original=(folder/'open/stage-before-a5.bin').read_bytes()
 meta=json.loads((folder/'request.json').read_text());assert hashlib.sha256(code).hexdigest()==meta['payload_sha256']
 image=wire.prepare(code);assert hashlib.sha256(image).hexdigest()==meta['image_sha256']
 entries=[];tick_ms=0;mode=None
 with gzip.open(folder/'trace.bin.gz','rb') as f:
  while prefix:=f.read(12):
   assert len(prefix)==12
   ns,n=struct.unpack('<QI',prefix);assert ns>0 and 16<=n<=4096
   incoming=f.read(n);assert len(incoming)==n
   size=struct.unpack('<I',f.read(4))[0];assert size<=8192
   reply=f.read(size);assert len(reply)==size
   magic,op,ms,packet_length=struct.unpack_from('<4I',incoming)
   assert magic==0x314d5452 and ms<=1000 and n==16+packet_length
   count=len(entries)+1;tick_ms+=ms
   assert struct.unpack_from('<4I',reply)==(magic,count,count,tick_ms//10)
   if len(reply)>=48 and struct.unpack_from('<I',reply,16)[0]==24:
    mode='network';length=struct.unpack_from('<I',reply,44)[0]&0x7fffffff;assert len(reply)==48+length
   else:
    mode='echo';assert reply[20:]==incoming[16:] and struct.unpack_from('<I',reply,16)[0]==packet_length
   entries.append((incoming,reply))
 summary=json.loads((folder/'summary.json').read_text());assert summary['steps']==len(entries) and summary['restored'] and summary['unloaded'] and not summary['driver_bound']
 table=symbols(symbol_file) if symbol_file else {};stack_high=[0,0,0];audits=0
 for p in sorted(folder.glob('audit-*.bin.gz')):
  index=int(p.name.split('-')[1].split('.')[0]);assert 1<=index<=len(entries)
  incoming,reply=entries[index-1];block=wire.block(incoming,index)
  before=image[:wire.bio.OFFSET]+block+original[wire.bio.IMAGE_SIZE:]
  after=gzip.decompress(p.read_bytes());assert len(after) in (wire.bio.IMAGE_SIZE,524288)
  assert wire.response(before,after+original[len(after):])==(0,reply);audits+=1
  if '_guarded_stacks' in table:
   count=struct.unpack_from('<I',after,table['_stack_count'])[0];assert count==3
   sizes=struct.unpack_from('<3I',after,table['_stack_sizes']);assert sizes==(2048,8192,4096)
   for i,size in enumerate(sizes):
    data=after[table['_guarded_stacks']+i*8320:table['_guarded_stacks']+(i+1)*8320]
    assert data[:16]==b'\xa5'*16 and data[16+size:]==b'\xa5'*(8320-16-size)
    used=size
    while used and data[16+used-1]==0xa5:used-=1
    stack_high[i]=max(stack_high[i],used)
 return dict(valid=True,mode=mode,steps=len(entries),milliseconds_supplied=tick_ms,ram_audits=audits,stack_used_lower_bounds=stack_high if table else None,restored=True,unloaded=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--payload',type=Path,required=True);p.add_argument('--symbols',type=Path);a=p.parse_args();print(json.dumps(validate(a.folder,a.payload.read_bytes(),a.symbols),indent=2))
