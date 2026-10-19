import struct
from qlogic_pause import decode
w=[0]*1024
w[320:340]=[0x31494350,1,23,1,0,0,0x10014,0x10014,5,0,0x10161077,6,0x1000006,1,0xfff00000,0,0,0,0,0]
w[352:374]=[0x314d5251,1,23,1,0,0,0xc0600d00,14,0x8bf00000,0,0,0xc0600df0,256,0xc0604df0,128,0xc0601730,0xc0605370,37,22|(22<<16),0,0,578]
w[384:404]=[0x31504351,1,23,1,0,0,12,0]+[0,2,37,22,0,2]*2
w[416:441]=[0x31535051,1,23,1,0,0,1,1,0x44,6,0,0x20,3,0,3,2,0x44,6,0,0,2,37,22,42,42]
pack=lambda v:struct.pack('<1024I',*v)
r=decode(pack(w),23,1,0)
assert r['one_shot'] and r['chip_writes']==2 and not r['hardware_drained'] and not r['ownership_proven']
for i in list(range(416,428))+[429,431]+list(range(432,439))+list(range(441,464)):
 t=w.copy();t[i]^=1
 try:decode(pack(t),23,1,0)
 except ValueError:pass
 else:raise AssertionError(i)
for i in (428,430):
 for n in (0,10001):
  t=w.copy();t[i]=n
  try:decode(pack(t),23,1,0)
  except ValueError:pass
  else:raise AssertionError((i,n))
for i in (323,355,387,419):w[i]=3
for i in (324,356,388,420):w[i]=1
assert decode(pack(w),23,3,1)['origin_sequence']==1
print('pause decoder: sequence/phase, bounds, transition, restored queues and reserved tampering rejected; later retained report accepted')
