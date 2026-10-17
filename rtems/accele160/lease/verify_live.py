#!/usr/bin/env python3
"""Offline replay of the accepted AcceleRAID RTEMS lease card captures."""
import hashlib,json,struct,sys
from pathlib import Path

FIRMWARE='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
IMAGE='0eb6e4591739dbf8c46363b74f0c645dd990b5cc139461ac6eb2635ad329263f'
KERNEL='e44d1ddab2892623cc6bb876b37ada1bc13d5b9c5aaa28515a825bcb3ebca41e'
NONCE=0x161610d1
PTR=0xc0710000
PAGES=16
PAGE=4096
def require(ok,label):
    if not ok:raise ValueError(label)
def sha(data):return hashlib.sha256(data).hexdigest()
def words(data,off,count):return struct.unpack_from('<'+str(count)+'I',data,off)
def status(path):return dict(x.split('=',1) for x in path.read_text().split())
def read(path):return path.read_bytes()
def fnv(data):
    h=0x811c9dc5
    for b in data:h=((h^b)*0x01000193)&0xffffffff
    return h

def verify(root):
    root=Path(root)
    source=Path(__file__).resolve().parent
    image=read(source/'image.bin')
    kernel=read(source/'kernel.bin')
    require(len(image)==len(kernel)==PAGES*PAGE and
            sha(image)==IMAGE and sha(kernel)==KERNEL and
            image[:15*PAGE]==kernel[:15*PAGE] and
            image[15*PAGE:]==b'\xa5'*PAGE,'image identity/layout')
    digest=fnv(image)
    require(digest==0x8622b536,'image FNV')
    accepted=root/'accept-3'
    pre=json.loads((accepted/'preflight.json').read_text())
    result=json.loads((accepted/'result.json').read_text())
    boot=pre['boot_id']
    require(pre['image_sha256']==IMAGE and pre['kernel_sha256']==KERNEL and
            pre['firmware_sha256']==FIRMWARE and
            pre['fnv']==f'0x{digest:08x}' and
            result['boot_id']==boot and result['image_sha256']==IMAGE and
            result['firmware_sha256']==FIRMWARE and
            result['owner_restored'] and result['page_restored'] and
            result['stage_restored'] and result['full_audits'],
            'preflight/result identity')
    card,old=pre['card'],pre['old']
    require(card['bdf']=='0000:37:09.1' and card['driver']=='myrsread' and
            old['bdf']=='0000:37:04.1' and old['driver'] is None and
            result['card_after']==card and result['old_after']==old,
            'card ownership')
    for p in (root/'accept-1/postcall-flash',
              root/'accept-2/postcall-flash',
              accepted/'postcall-flash'):
        request=json.loads((p/'request.json').read_text())
        receipt=json.loads((p/'result.json').read_text())
        audit=status(p/'status.txt')
        data=read(p/'data.bin')
        require(request['boot_id']==boot and request['selector']==9 and
                request['length']==len(data)==1048576 and
                receipt['sha256']==sha(data)==FIRMWARE and
                receipt['card_after']==card and receipt['old_after']==old and
                all(audit.get(k)=='0' for k in
                    ('status','residual','guard_changes')),
                f'full flash audit {p}')
    before=read(accepted/'page-before.bin')
    reserved=read(accepted/'page-reserved.bin')
    restored=read(accepted/'page-restored.bin')
    owner=read(accepted/'owner-before.bin')
    owned=read(accepted/'owner-reserved.bin')
    require(len(before)==len(reserved)==len(restored)==PAGE and
            restored==before and
            read(accepted/'owner-after.bin')[0x2a0:0xaa0]==owner[0x2a0:0xaa0] and
            words(reserved,0x820,4)==(0x4f4c4c41,0x16161041,PTR,0x80000) and
            words(reserved,0x840,4)==(0x56525352,PTR,0x80000,0x96016004),
            'loader/owner restoration')
    first=(PTR-0xc0000000)//0x8000
    for i in range(256):
        bc,bo=words(owner,0x2a0+4*i,1)[0],words(owner,0x6a0+4*i,1)[0]
        rc,ro=words(owned,0x2a0+4*i,1)[0],words(owned,0x6a0+4*i,1)[0]
        require((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo))
                and (not first<=i<first+16 or (bc,bo)==(0,0)),
                f'owner record {i}')
    require(len(read(accepted/'stage-before.bin'))==PAGE,'stage length')
    for index,mode in enumerate(('stop','timeout')):
        p=accepted/mode
        entry=result['runs'][index]
        require(entry['mode']==mode and entry['task_done']==1 and
                entry['elapsed_ms']>0,'mode result')
        receipts=json.loads((p/'copy-receipts.json').read_text())
        require(len(receipts)==PAGES,'copy count')
        for i,r in enumerate(receipts):
            data=image[i*PAGE:(i+1)*PAGE]
            require(r==dict(index=i,sha256=sha(data),fnv=f'0x{fnv(data):08x}'),
                    f'copy page {i}')
        for command_name in ('copy','digest','ram-admit'):
            s=status(p/(command_name+'-status.txt'))
            require(s.get('done')=='1' and s.get('status')=='0' and
                    s.get('residual')=='0',f'{command_name} status')
        digest_page=read(p/'digest-page.bin')
        require(words(digest_page,0x830,4)==
                (0x48534148,0x16161071,PAGES,digest),'card digest')
        ready=read(p/'ready-page.bin')
        require(words(ready,0xa40,3)==(0x3145534c,NONCE,1) and
                words(ready,0xa50,1)==(0x59444152,), 'READY')
        page=read(p/'page-after.bin')
        require(len(page)==PAGE and
                page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+reserved[0x830:0xa00]
                and page[0xa80:]==before[0xa80:],'loader bounds')
        flag=0x504f5453 if mode=='stop' else 0x454d4954
        require(words(page,0xa00,8)==
                (0x314d4152,NONCE,PTR,0x80000,PAGES,0,digest,0) and
                words(page,0xa20,7)==
                (0x314e5552,NONCE,0x31454e4f,PTR,PAGES,digest,flag),
                'admission report')
        side=words(page,0xa40,8)
        if mode=='stop':
            require(entry['stale_pending'] is True and
                    words(read(p/'stale-page.bin'),0xa4c,1)==(0xdeadbeef,) and
                    side==(0x3145534c,NONCE,1,0x504f5453,0x59444152,
                           0x214b4341,NONCE,1),'stale/valid STOP')
        else:
            require(side==(0x3145534c,NONCE,1,0,0x454d4954)+
                    (0xa5a5a5a5,)*3,'finite timeout')
        fw,sentinel,entry_sp,restored_sp,worker_sp,polls,seen,done=words(page,0xa60,8)
        stack=read(p/'entry-stack-after.bin')
        require(fw==restored_sp==0xc0002100 and sentinel==0xa5a5a5a5 and
                PTR+15*PAGE<=entry_sp<PTR+16*PAGE and
                PTR<=worker_sp<PTR+15*PAGE and
                polls==(2000000 if mode=='timeout' else entry['polls']) and
                seen==(1 if mode=='stop' else 0) and done==1 and
                stack[:256]==b'\xa5'*256 and
                sum(x!=y for x,y in zip(stack,image[15*PAGE:]))==
                entry['stack_changed_bytes'] and
                entry['firmware_sp']==f'0x{fw:08x}' and
                entry['entry_sp']==f'0x{entry_sp:08x}' and
                entry['restored_sp']==f'0x{restored_sp:08x}' and
                entry['worker_sp']==f'0x{worker_sp:08x}',
                'RTEMS task/stack telemetry')
        require(read(p/'owner-after.bin')[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
                'owner during execution')
    return {'stop_ms':result['runs'][0]['elapsed_ms'],
            'timeout_ms':result['runs'][1]['elapsed_ms'],
            'firmware_sha256':FIRMWARE,'image_sha256':IMAGE,
            'full_flash_reads':3,'modes':2}

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
