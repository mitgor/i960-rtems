#!/usr/bin/env python3
"""Replay the exact AcceleRAID Doom bridge capture without touching hardware."""
import hashlib,json,struct,sys
from pathlib import Path

DEFAULT=Path(__file__).resolve().parents[3]/'artifacts/current/accele160-doom-bridge-20261017'
def sha(data):return hashlib.sha256(data).hexdigest()
def fnv(data):
    h=0x811c9dc5
    for b in data:h=((h^b)*0x01000193)&0xffffffff
    return h
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def words(data,offset,count):return struct.unpack_from('<%dI'%count,data,offset)
def verify(root=DEFAULT):
    inputs=root/'inputs';build=root/'build';live=root/'live-1';run=live/'persist'
    result=json.loads((live/'result.json').read_text())
    image=(build/'image.bin').read_bytes();kernel=(build/'kernel.bin').read_bytes()
    need(len(image)==27*4096 and sha(image)==result['image_sha256'] and
         sha(image)=='6b625a81c60a084c1cf3d0ba61d1dcbaa7dac23832333a3fa0eaeb8a03f80863' and
         sha(kernel)==result['kernel_sha256'] and fnv(image)==0x3a62a5d7,
         'RTEMS build identity')
    need(image[:20*4096]==kernel[:20*4096] and image[20*4096:]==b'\xa5'*(7*4096),
         'RTEMS image layout')
    template=(inputs/'template.bin').read_bytes();relocs=(inputs/'relocations.bin').read_bytes()
    wad=(inputs/'wad-header.bin').read_bytes()
    need(len(template)==431864 and sha(template)=='9f2472c900bb724e7a69b2490e083c4c633520e1d525623398db2e36f2c1e173' and
         sha(template[:369376])=='5f36a39f4b14a078690ed7003ed3bcd0e36904b2b573b2ef6946f8559cb33828',
         'Doom template/text')
    need(len(relocs)==53472 and sha(relocs)=='4a0408886fe0a840b866219b62c0c1d19c7b6b6dcbc61574155fe88f49ba1a94',
         'Doom relocations')
    sites=struct.unpack('<13368I',relocs)
    need(all(x%4==0 and x<=len(template)-4 and
             struct.unpack_from('<I',template,x)[0]<=814320 and
             (i==0 or sites[i-1]<x) for i,x in enumerate(sites)),
         'relocation bounds')
    need(len(wad)==512 and wad[:4]==b'IWAD' and
         sha(wad)=='93bd1ddcfc43fbf233207876f5cfcbaef4cf4e64a1093efa47be9517d93214bd',
         'Freedoom WAD header')
    ready=(run/'ready-page.bin').read_bytes();pre=(run/'prestop-page.bin').read_bytes()
    stop=(run/'quiescent-page.bin').read_bytes()
    bank=words(ready,0xb00,16);claim=words(ready,0xb40,16)
    need(bank[0:4]==(0x314b4e42,0,0x3734,0x800000) and
         bank[4]==bank[5]==bank[6] and bank[7:11]==(2048,0,2048,0) and
         bank[11]==0x853984e9 and bank[12:14]==(0,0) and bank[14]==bank[15],
         'full upper-bank reversible audit')
    need(claim[0:4]==(0x314d5241,2048,0x833aedc5,0) and
         claim[7:16]==(0xc0810010,0xc08ebbd0,0xc0eebbf0,
                       900000,6291456,65536,0x101,0x102,0x103),
         'guarded Doom arena admission')
    need(words(pre,0xb00,16)==bank and words(stop,0xb00,16)==bank,
         'bank audit retained')
    bridge=words(stop,0xb80,20)
    need(bridge[6:10]==(0x31475242,0x161610e1,232,0) and
         bridge[11:16]==(867792,1,1,claim[7]+355776,867792) and
         bridge[17]==1,'image/WAD/frame bridge status')
    stopped=words(stop,0xb40,16)
    need(stopped[4]>claim[4] and stopped[5:7]==(0x45495551,0) and
         words(stop,0xa54,1)==(0x214b4341,), 'heartbeat and STOP')
    pending=(run/'admit-pending-status.txt').read_text()
    need('started=1' in pending and 'done=0' in pending and 'released=0' in pending,
         'retained callback')
    receipts=json.loads((run/'bridge-receipts.json').read_text())
    need(len(receipts)==232 and [x['seq'] for x in receipts]==list(range(1,233)),
         'ordered command sequence')
    need((receipts[0]['op'],receipts[0]['status'])==(4,1),
         'premature admission rejection')
    admission=template+bytes(814320-len(template))+relocs
    for i,off in enumerate(range(0,len(admission),4096),1):
        r=receipts[i];n=min(4096,len(admission)-off)
        need((r['op'],r['offset'],r['n'],r['status'],r['value'])==
             (1,off,n,0,off+n),f'upload receipt {i}')
    need((receipts[213]['op'],receipts[213]['status'],receipts[213]['value'])==
         (4,0,1),'exact image admission receipt')
    need((receipts[214]['op'],receipts[214]['status'])==(2,7) and
         (receipts[215]['op'],receipts[215]['status'],receipts[215]['value'])==
         (2,0,struct.unpack_from('<I',wad,4)[0]),'WAD rejection/admission')
    frame=(run/'frame.bin').read_bytes()
    expected=bytes((((x>>3)^(y>>3)^wad[(x+y)&511])&255)
                   for y in range(200) for x in range(320))+bytes(1536)
    need(frame==expected and len(frame)==65536 and fnv(frame)==bridge[16] and
         sha(frame)==result['frame_sha256'],'diagnostic framebuffer oracle')
    for i,r in enumerate(receipts[216:]):
        need((r['op'],r['offset'],r['n'],r['status'],r['value'])==
             (3,i,4096,0,fnv(frame[i*4096:(i+1)*4096])),
             f'frame page {i}')
    need((run/'frame.pgm').read_bytes()==b'P5\n320 200\n255\n'+frame[:64000],
         'renderable frame')
    need(result['full_audits_before'] and result['release']=='reboot-only' and
         result['grant_retained'] and result['old']['driver'] is None,
         'ownership report')
    reset_boot=None
    for number in (0,1):
        folder=root/f'post-reset-{number}'
        req=json.loads((folder/'request.json').read_text())
        post=json.loads((folder/'result.json').read_text())
        status=dict(x.split('=',1) for x in (folder/'status.txt').read_text().split())
        if reset_boot is None:reset_boot=req['boot_id']
        need(req['boot_id']==reset_boot and reset_boot!=result['boot_id'] and
             req['card']['bdf']=='0000:37:09.1' and
             req['card']['driver']=='myrsread' and req['selector']==9 and
             req['length']==post['bytes']==1048576 and
             post['sha256']==result['firmware_sha256'] and
             post['card_after']==req['card'] and
             post['old_after']['driver'] is None and
             all(status[k]=='0' for k in ('status','residual','guard_changes')),
             f'post-reset full-flash audit {number}')
    return {'commands':len(receipts),'upload_bytes':len(admission),
            'frame_sha256':sha(frame),'bank_pages':bank[7],
            'quiescent_tick':stopped[4], 'reset_boot_id':reset_boot}
if __name__=='__main__':
    print(json.dumps(verify(Path(sys.argv[1]) if len(sys.argv)>1 else DEFAULT),indent=2))
