#!/usr/bin/env python3
"""Reproduce a conservative, version-pinned firmware ownership inventory.

Matches are leads, not whole-program alias analysis or evidence that holes are free.
Checks every disassembly byte against its source before using an instruction.
"""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/vendor-fujitsu/4.07-0-29'
SHA='21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195'
TARGETS={0x1310:'IMR0',0x1314:'IMR1',0x1318:'OMR0',0x131c:'OMR1',0x1320:'IDR',0x1324:'IISR',0x1328:'IIMR',0x132c:'ODR',0x1330:'OISR',0x1334:'OIMR',0x1350:'MUCR',0x1380:'IAR'}
ANCHORS=[('imr0-diagnostic',0xc0039ca0,0xc0039ce8),('mailbox-init-mask',0xc004b790,0xc004b81c),('mailbox-command',0xc004b880,0xc004b934),('mailbox-completion',0xc004b940,0xc004b9e0),('doorbell-dispatch',0xc004b9f0,0xc004baac),('handler-records',0xc004ed10,0xc004ed7c),('mu-isr',0xc004ef20,0xc004ef94),('bootstrap-clear',0xfefc813c,0xfefc81c0),('bootstrap-handler-records',0xfefcb540,0xfefcb5f4),('fault-record-read',0xfefcbba0,0xfefcbc20)]

def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 blob=(BASE/'unpacked.bin').read_bytes();assert hashlib.sha256(blob).hexdigest()==SHA
 actual=(ROOT/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/firmware-unpacked.bin').read_bytes();assert actual==blob
 rows=[];sources=[]
 for binary,dis,base,end in [('unpacked.bin','unpacked.dis',0xc0010000,0xc0010000+len(blob)),('Fgj40729.img.raw','bootstrap.dis',0xfefc8000,0xfefcf000)]:
  data=(BASE/binary).read_bytes();text=(BASE/dis).read_text();sources.append(dict(binary=str((BASE/binary).relative_to(ROOT)),sha256=hashlib.sha256(data).hexdigest(),range=[hex(base),hex(end)]))
  for line in text.splitlines():
   m=re.match(r'^([0-9a-f]{8}):\s*((?:[0-9a-f]{2} ){3}[0-9a-f]{2})\s*(.*)$',line)
   if not m:continue
   address=int(m[1],16)
   if not base<=address<end:continue
   raw=bytes.fromhex(m[2]);assert data[address-base:address-base+4]==raw,(dis,line)
   rows.append((address,m[3],line))
 hits=[]
 for address,asm,line in rows:
  if not re.match(r'(lda|ld|st|ldob|stob|ldos|stos|ldl|stl|ldt|stt|ldq|stq)\s',asm):continue
  for literal in re.findall(r'0x([0-9a-f]+)',asm):
   value=int(literal,16)
   if value in TARGETS or 0xc0000000<=value<0xc0002000:
    hits.append(dict(pc=hex(address),value=hex(value),register=TARGETS.get(value),assembly=asm))
 raw_hits={}
 for value,name in TARGETS.items():
  raw_hits[name]=[hex(0xc0010000+i) for i in range(0,len(blob)-3,4) if struct.unpack_from('<I',blob,i)[0]==value]
 for name,start,end in ANCHORS:
  selected=[line for address,asm,line in rows if start<=address<end]
  assert selected,name
  (a.out/(name+'.txt')).write_text('\n'.join(selected)+'\n')
 report=dict(version='4.07-0-29',matches_live_dump_unpacked=True,sources=sources,direct_operand_leads=hits,aligned_literal_leads=raw_hits,ownership_proven=False,limitations=['linear disassembly includes data; annotations need context','computed addresses and indirect references are not exhausted','no matches does not mean unowned','bootstrap excludes compressed region at FEF CF000 and above'])
 (a.out/'references.json').write_text(json.dumps(report,indent=2)+'\n')
 print(f'Byte-checked {len(rows)} disassembly rows; {len(hits)} direct leads; {len(ANCHORS)} annotated-region extracts. No free-space claim.')
if __name__=='__main__':main()
