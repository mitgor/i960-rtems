#!/usr/bin/env python3
"""Actual Python producer layout, ordered commit and fail-before-write bounds."""
import struct
from key_fifo import OFFSET,guard,snapshot,submit,configure,pending
page=bytearray(4096);writes=[]
def write(addr,off,data):
    assert addr==0xc000e000
    writes.append((off,bytes(data)));page[off:off+len(data)]=data
def reset():
    page[:]=bytes(4096);writes.clear()
    struct.pack_into('<16I',page,OFFSET,0x3146424b,0x161610e1,1,16,0,0,0,1,0,0,0,0,0,0,1,~0x3146424b&0xffffffff)
    struct.pack_into('<16I',page,OFFSET+80*4,*(guard(i) for i in range(16)))
reset();assert submit(write,0,0,1,'fifo',list(range(16)))==16
assert writes[-1][0]==OFFSET+16 and writes[-2][0]==0xd28
assert len(writes)==18 and pending(page,16,1,'fifo')==16
for i in range(16):assert struct.unpack_from('<4I',page,OFFSET+64+i*16)==(i+1,1,i,~(i+1)&0xffffffff)
count=len(writes)
for args in ((16,0,1,'fifo',[1]),(16,16,1,'fifo',[512]),(0xfffffffd,0xfffffffd,1,'fifo',[1])):
    try:submit(write,*args);raise AssertionError('invalid publication')
    except ValueError:pass
    assert len(writes)==count
try:configure(page,write,16,1,'mailbox');raise AssertionError('nonempty mode switch')
except ValueError:pass
struct.pack_into('<I',page,OFFSET+5*4,16)
configure(page,write,16,1,'mailbox')
assert submit(write,16,16,1,'mailbox',[448])==17
assert writes[-3][0]==0xd2c and snapshot(page,17,1,'mailbox')[4:6]==(17,16)
reset();submit(write,0,0,1,'fifo',[448]);struct.pack_into('<I',page,OFFSET+64+4,0)
try:pending(page,1,1,'fifo');raise AssertionError('stale run')
except ValueError:pass
print('PASS production producer: exact ring layout, descriptors-before-tail, full/invalid/wrap refusal, quiescent mode change and stale descriptor audit')
