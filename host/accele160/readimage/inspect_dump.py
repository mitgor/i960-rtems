#!/usr/bin/env python3
"""Inspect captured images offline; validate pairs and the main firmware ZIP CRC."""
import argparse,hashlib,json,struct,subprocess,tempfile,zlib
from pathlib import Path

def inspect(p):
 d=(p/'descriptor-0.bin').read_bytes()
 if len(d)!=1024 or d[:4]!=b'XLYM' or d!=(p/'descriptor-1.bin').read_bytes():raise ValueError('descriptor pair invalid')
 regions=[]
 for i in range(struct.unpack_from('<H',d,10)[0]):
  off=32+64*i
  address,size=struct.unpack_from('<II',d,off)
  regions.append(dict(selector=d[off+8],flash_offset=address,bytes=size))
 c=(p/'controller.bin').read_bytes()
 out=dict(regions=regions,cpu_mhz=struct.unpack_from('<H',c,272)[0],cpu_type=c[274],cpu_count=c[275],memory_mb=struct.unpack_from('<H',c,208)[0],cache_mb=struct.unpack_from('<H',c,210)[0],memory_mhz=struct.unpack_from('<H',c,220)[0],flash_mib=struct.unpack_from('<H',c,418)[0],images={})
 for name in ['boot','firmware','bios']:
  a=(p/(name+'-full-0')/'data.bin').read_bytes();b=(p/(name+'-full-1')/'data.bin').read_bytes()
  if a!=b:raise ValueError('image pair differs: '+name)
  for i in (0,1):
   status=(p/(name+'-full-'+str(i))/'status.txt').read_text()
   if not status.startswith('done=1 status=0 residual=0 '):raise ValueError('unsuccessful image completion: '+name)
  out['images'][name]=dict(bytes=len(a),sha256=hashlib.sha256(a).hexdigest(),paired_equal=True)
  if name=='bios':
   if a[:2]!=b'\x55\xaa' or a[2]*512!=len(a) or sum(a)%256:raise ValueError('BIOS checksum/length failure')
   out['images'][name]['rom_checksum_passed']=True
  if name=='boot':
   words=struct.unpack_from('<8I',a,len(a)-0xd0)
   out['images'][name]['ibr_words']=[hex(x) for x in words]
   out['images'][name]['entry_prcb_check_sum']=(words[4]+words[5]+words[6])&0xffffffff
  if name=='firmware':
   blob=a[0x7000:]
   sig,ver,flag,method,t,date,crc,cs,us,n,x=struct.unpack_from('<IHHHHHIIIHH',blob)
   if sig!=0x04034b50 or method!=6 or n!=4 or blob[30:34]!=b'ZIP1' or 30+n+x+cs>len(blob):raise ValueError('unexpected embedded ZIP')
   local=blob[:30+n+x+cs];filename=blob[30:30+n]
   central=struct.pack('<IHHHHHHIIIHHHHHII',0x02014b50,20,ver,flag,method,t,date,crc,cs,us,n,0,0,0,0,0,0)+filename
   end=struct.pack('<IHHHHIIH',0x06054b50,0,0,1,1,len(central),len(local),0)
   with tempfile.TemporaryDirectory() as tmp:
    z=Path(tmp)/'image.zip';z.write_bytes(local+central+end)
    data=subprocess.run(['unzip','-p',str(z),'ZIP1'],capture_output=True,check=True,timeout=30).stdout
   if len(data)!=us or zlib.crc32(data)!=crc:raise ValueError('embedded firmware CRC failure')
   out['images'][name]['embedded']=dict(compressed_bytes=cs,uncompressed_bytes=us,crc32=f'{crc:08x}',crc_passed=True,uncompressed_sha256=hashlib.sha256(data).hexdigest())
 out['complete_physical_flash_dump']=False
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();print(json.dumps(inspect(a.directory),indent=2))
