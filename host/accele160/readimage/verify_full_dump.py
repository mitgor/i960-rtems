#!/usr/bin/env python3
"""Offline verification of the full selector-9 flash capture and EZAssist overrun."""
import argparse,gzip,hashlib,json,struct,subprocess,tempfile,zlib
from pathlib import Path

def unpack(blob):
 sig,ver,flag,method,t,date,crc,cs,us,n,x=struct.unpack_from('<IHHHHHIIIHH',blob)
 if sig!=0x04034b50 or method!=6 or not 0<n<128 or 30+n+x+cs>len(blob):raise ValueError('invalid embedded ZIP bounds')
 local=blob[:30+n+x+cs];name=blob[30:30+n]
 central=struct.pack('<IHHHHHHIIIHHHHHII',0x02014b50,20,ver,flag,method,t,date,crc,cs,us,n,0,0,0,0,0,0)+name
 end=struct.pack('<IHHHHIIH',0x06054b50,0,0,1,1,len(central),len(local),0)
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp)/'image.zip';p.write_bytes(local+central+end)
  data=subprocess.run(['unzip','-p',str(p),name.decode()],capture_output=True,check=True,timeout=30).stdout
 if len(data)!=us or zlib.crc32(data)!=crc:raise ValueError('embedded ZIP CRC/size mismatch')
 return data,dict(name=name.decode(),compressed_bytes=cs,expanded_bytes=us,crc32=f'{crc:08x}',crc_passed=True,sha256=hashlib.sha256(data).hexdigest())

def verify(p,baseline):
 a=(p/'rawflash-0/data.bin').read_bytes();b=(p/'rawflash-1/data.bin').read_bytes()
 if len(a)!=1048576 or a!=b:raise ValueError('full flash pair mismatch')
 for i in (0,1):
  fields=dict(x.split('=') for x in (p/f'rawflash-{i}/status.txt').read_text().split())
  if any(fields.get(k)!=v for k,v in dict(done='1',status='0',residual='0',selector='9',length='1048576',guard_changes='0').items()):raise ValueError('unaccepted raw flash completion')
 matches={}
 for name,off in [('boot',0xf0000),('firmware',0x40000),('bios',0x30000)]:
  ref=(baseline/f'{name}-full-0/data.bin').read_bytes()
  if a[off:off+len(ref)]!=ref:raise ValueError('component mismatch: '+name)
  matches[name]=dict(offset=hex(off),bytes=len(ref),sha256=hashlib.sha256(ref).hexdigest())
 for name,off,path in [('descriptor',0xe0000,baseline/'descriptor-0.bin'),('diagnostics',0xc0000,p/'guarded-diagnostics-0/data.bin')]:
  ref=path.read_bytes()
  if a[off:off+len(ref)]!=ref:raise ValueError('region mismatch: '+name)
  matches[name]=dict(offset=hex(off),bytes=len(ref),sha256=hashlib.sha256(ref).hexdigest())
 ez,ezcheck=unpack(a[:0x30000]);_,fwcheck=unpack(a[0x47000:0xc0000])
 capture=p/'retained-ezassist/allocation-0.bin.gz'
 owned=gzip.decompress(capture.read_bytes()) if capture.exists() else (p/'retained-ezassist/allocation-0.bin').read_bytes()
 pre=65536;requested=164576;tail=1048576
 if len(owned)!=pre+requested+tail:raise ValueError('retained allocation length')
 if owned[pre:pre+len(ez)]!=ez:raise ValueError('overrun does not equal expanded EZAssist')
 if any(x!=0xa5 for x in owned[:pre]+owned[pre+len(ez):]):raise ValueError('unexpected writes outside expanded image')
 changed=sum(v!=0xa5 for v in owned[pre+requested:])
 return dict(bytes=len(a),sha256=hashlib.sha256(a).hexdigest(),paired_equal=True,zero_residual=True,guards_unchanged=True,complete_flash_address_range=True,independent_external_programmer_verification=False,region_matches=matches,firmware_zip=fwcheck,ezassist_zip=ezcheck,overrun=dict(requested=requested,actual_expanded=len(ez),bytes_beyond_request=len(ez)-requested,changed_guard_bytes=changed,exact_match_to_decompressed_flash=True,prefix_and_remaining_tail_unchanged=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('baseline',type=Path);a=p.parse_args();print(json.dumps(verify(a.capture,a.baseline),indent=2))
