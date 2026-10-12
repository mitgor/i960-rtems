#!/usr/bin/env python3
"""Offline ELF32/i960 rebase experiment, not an admitted card loader.
Only import-free ELF REL objects with canonical .text/.data/.bss and retained
R_960_32 records are accepted. Relocation metadata must come from a trusted build.
"""
import struct
MAX=8*1048576

def rebase(raw,destination,entry_name="_relocated_entry"):
 assert raw[:7]==b'\x7fELF\x01\x01\x01' and len(raw)>=52
 h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw);_,kind,machine,version,entry,ph,sh,flags,eh,pe,pn,se,sn,strings=h
 assert kind==1 and machine==19 and version==1 and eh==52 and se==40 and 0<sn<=256 and strings<sn
 assert sh<=len(raw) and sn*40<=len(raw)-sh
 sections=[struct.unpack_from('<10I',raw,sh+i*40) for i in range(sn)]
 def contents(s):
  assert s[4]<=len(raw) and s[5]<=len(raw)-s[4];return raw[s[4]:s[4]+s[5]]
 names=contents(sections[strings])
 def name(s):
  assert s[0]<len(names);end=names.find(b'\0',s[0]);assert end>=0;return names[s[0]:end].decode('ascii')
 allocated=[i for i,s in enumerate(sections) if s[2]&2 and s[5]]
 assert 0<len(allocated)<=3
 for i in allocated:
  s=sections[i];assert (name(s),s[1],s[2]) in (('.text',1,6),('.data',1,3),('.bss',8,3));assert s[3]%4==0 and s[5]<=MAX
 assert len(set(name(sections[i]) for i in allocated))==len(allocated)
 ordered=sorted(allocated,key=lambda i:('.text','.data','.bss').index(name(sections[i])))
 placement={};end=0
 for i in ordered:
  s=sections[i];assert s[3]==0 and s[8]<=16
  end=(end+15)&~15;placement[i]=end;end+=s[5]
 assert end<=MAX and destination%16==0 and 0<=destination<=0x100000000-end
 base=0;file_end=max(placement[i]+sections[i][5] for i in allocated if sections[i][1]!=8)
 image=bytearray(file_end)
 for i in allocated:
  s=sections[i]
  if s[1]!=8:image[placement[i]:placement[i]+s[5]]=contents(s)
 symtabs={};entry=None
 for i,s in enumerate(sections):
  if s[1]==2:
   assert s[9]==16 and s[5]%16==0
   symbols=[struct.unpack_from('<IIIBBH',contents(s),j) for j in range(0,s[5],16)]
   assert all(j==0 or sym[5]!=0 for j,sym in enumerate(symbols)), 'unresolved symbol'
   symtabs[i]=symbols
   assert s[6]<sn;strings_blob=contents(sections[s[6]])
   for sym in symbols:
    assert sym[0]<len(strings_blob);finish=strings_blob.find(b'\0',sym[0]);assert finish>=0
    if strings_blob[sym[0]:finish].decode('ascii')==entry_name:
     assert entry is None and sym[5] in allocated and name(sections[sym[5]])=='.text' and sym[1]<sections[sym[5]][5]
     entry=destination+placement[sym[5]]+sym[1]
 assert entry is not None, 'entry symbol missing'

 offsets=[];rel_sections=0
 for s in sections:
  if s[1] not in (4,9) or s[7] not in allocated:continue
  assert s[1]==9 and s[9]==8 and s[5]%8==0 and s[6] in symtabs
  target=sections[s[7]];assert target[1]!=8;rel_sections+=1
  blob=contents(s)
  for j in range(0,len(blob),8):
   address,info=struct.unpack_from('<II',blob,j);index=info>>8;typ=info&255
   assert typ==2 and index<len(symtabs[s[6]]), 'unsupported relocation'
   symbol=symtabs[s[6]][index];assert symbol[5] in allocated, 'external/absolute relocation'
   assert address%4==0 and address+4<=target[5]
   offset=placement[s[7]]+address;assert offset not in offsets, 'duplicate relocation'
   addend=struct.unpack_from('<I',image,offset)[0]
   assert symbol[1]<=sections[symbol[5]][5]
   value=(destination+placement[symbol[5]]+symbol[1]+addend)&0xffffffff
   assert destination<=value<=destination+end, 'out-of-image addend'
   struct.pack_into('<I',image,offset,value);offsets.append(offset)
 assert rel_sections and offsets, 'retained relocations required'
 return bytes(image),dict(link_base=base,base=destination,entry=entry,memory_bytes=end-base,file_bytes=len(image),relocations=sorted(offsets),sections=[dict(name=name(sections[i]),offset=placement[i],file_bytes=sections[i][5] if sections[i][1]!=8 else 0,memory_bytes=sections[i][5],flags=1 if sections[i][2]&4 else 2) for i in ordered])
