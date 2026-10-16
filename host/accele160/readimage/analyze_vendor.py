#!/usr/bin/env python3
"""Verify the exact offline READIMAGE evidence; never execute a vendor utility."""
import argparse,hashlib,json,struct
from pathlib import Path
def analyze(path):
 data=path.read_bytes()
 receipt=json.loads((Path(__file__).resolve().parents[3]/'artifacts/current/accele160-readimage-20261016/provenance.json').read_text())
 if hashlib.sha256(data).hexdigest()!=receipt['decoded_dacfl6_sha256']:raise ValueError('unknown vendor executable')
 anchors={0x939c:'c8580000',0x940d:'26c6470220',0x9459:'26c647152d',
          0x9461:'668b460e6626894720',0x946d:'668b460a6626894724',
          0x9479:'668b46126626894728',0x94c1:'8b461626894710',
          0x94c8:'8a4618b400c45ef026894716',0xa9f5:'c646f30e',
          0xaa0c:'666800040000',0xaa24:'9a3c212606',0xaa43:'6626813f584c594d'}
 for offset,h in anchors.items():
  if data[offset:offset+len(bytes.fromhex(h))]!=bytes.fromhex(h):raise ValueError(f'code anchor {offset:x} mismatch')
 hdr=struct.unpack_from('<H',data,8)[0]*16
 calls=[]
 for i in range(hdr,0x16000-5):
  if data[i]==0x9a:
   off,seg=struct.unpack_from('<HH',data,i+1)
   if hdr+seg*16+off==0x939c:calls.append(hex(i))
 if calls!=['0xaa24']:raise ValueError('unexpected direct far-call sites')
 return dict(hash=receipt['decoded_dacfl6_sha256'],verified_anchors=len(anchors),
  readimage_routine_file_offset='0x939c',direct_far_calls=calls,
  descriptor=dict(command=32,ioctl=45,selector_byte22=14,word16=0,size=1024,expected_prefix_hex='584c594d'),
  command_layout={'2':'0x20','4..7':'transfer length','8..15':'sense address',
   '16..17':'argument word (descriptor caller supplies zero)','20':'sense length','21':'0x2d',
   '22..23':'selector (zero-extended byte)','32..39':'DMA address','40..47':'DMA length'},
  limitations=['only descriptor call verified','no arbitrary-flash offset semantics established','vendor utility targets a newer package','not a card dump'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('exe',type=Path);a=p.parse_args();print(json.dumps(analyze(a.exe),indent=2))
