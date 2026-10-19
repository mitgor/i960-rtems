from pathlib import Path
import re
import struct
from inventory import decode,REGISTERS
p=bytearray(4096);struct.pack_into('<56I',p,1024,0x31474e45,1,123,7,0,48,0,0,*REGISTERS)
assert not decode(p,123,7,0)['ownership_proven']
for i in range(8):
 b=bytearray(p);b[1024+i*4]^=1
 try:decode(b,123,7,0)
 except ValueError:pass
 else:raise AssertionError(i)
print('inventory decoder: schema/nonce/sequence/phase/count/reserved tampering rejected')

header=Path(__file__).with_name('inventory.h').read_text().split('={',1)[1].split('};',1)[0]
assert [int(x,16) for x in re.findall(r'0x([0-9a-f]+)u',header)]==REGISTERS
print('C and Python register ordering agree')
