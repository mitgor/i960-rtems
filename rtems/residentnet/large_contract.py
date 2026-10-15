"""RAM1 snapshot acceptance; no hardware access or memory grant."""
INITIAL_IMAGE='b382c02769a76c1ee1ecadbf14b90b6d9b845546a16b3f7e1e5f33e09e239301'
def validate_large(w,mib,parked=False,revision=None,transition=False):
 assert mib in (1,4,10,12)
 assert len(w)==64 and all(type(x) is int and 0<=x<=0xffffffff for x in w)
 size=mib*1048576;lo=0xc0240000;hi=lo+size
 assert w[:8]==[0x314d4152,lo,size,1,4,size,0,0]
 reserve=0xc0ad0080 if w[26]==3 else lo+0x90000
 assert w[8:15]==[lo+64,262144,lo+0x40080,65536,4,reserve,hi-64-reserve]
 assert w[15]>0 and w[16]==1 and not lo-65536<=w[17]<hi+65536
 assert 0xc0000010<=w[17]<0xc1000000 and not w[17]&15
 assert w[26] in (0,1,2,3)
 if revision is not None:assert w[26]==revision
 if w[26]>=1:
  assert w[19]==4 and w[20:24].count(65536)==3 and 0<w[20:24][0]<=65536
  assert all(0<n<=65536 for n in w[20:24])
  assert w[18] in (0,w[14]//4)
  complete=w[18]==w[14]//4
  if parked:assert complete
  if complete:assert (parked or transition) and min(w[24:26])>0
 if w[26]>=2:
  assert lo+64<=w[27]<=lo+64+262144-131072 and w[28]==131072
  assert w[29:31]==([131072,1] if complete else [0,0])
 if w[26]==3:
  assert mib in (10,12) and w[31:34]==[0xc02d0040,8388608,1]
  assert 134<=w[34]<=145 and w[35]>=w[34]*5 and w[36:38]==[0,0]
  assert w[38]==0xc0f94000 and w[38]<w[39]<=0xc0f9bff0 and w[39]%16==0
  assert w[40:]==[0]*24
 else:assert w[31:]==[0]*33

def validate_large_stacks(w):
 slots={0xc0280080+i*65664+16 for i in range(4)}
 for start in (16,26):
  if w[start]:
   assert 0xc0240040<=w[start]<0xc0280040
   assert w[start+1] in slots and w[start+2]==w[start+1]+65536
   if w[start+8]:assert w[start+1]+16<=w[start+3]<=w[start+2]-64 and not w[start+3]&15
  elif w[2]==2:raise AssertionError('parked worker never owned a stack')

 if w[16] and w[26]:assert w[16]!=w[26] and w[17]!=w[27]
