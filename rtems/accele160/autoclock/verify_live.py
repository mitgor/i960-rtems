#!/usr/bin/env python3
"""Offline replay of the accepted AcceleRAID 160 RTEMS hardware-clock gate."""
import hashlib,json,struct,sys
from pathlib import Path

FIRMWARE='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
IMAGE='d7234b9309e5e435456ddd50905787b4ddbab4e7fd9e0ea18d5094ca09a39db5'
KERNEL='b592bc5a711e6847cc208cc9753e9b672940d17d0c2c2e7c9c3f328f3e695150'
NONCE=0x161610d1
PTR=0xc0710000
PAGES=17
PAGE=4096
def need(ok,label):
    if not ok:raise ValueError(label)
def data(p):return p.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def words(b,off,n):return struct.unpack_from('<'+str(n)+'I',b,off)
def fields(p):return dict(x.split('=',1) for x in p.read_text().split())
def js(p):return json.loads(p.read_text())
def fnv(b):
    h=0x811c9dc5
    for x in b:h=((h^x)*0x01000193)&0xffffffff
    return h
def audit(path,boot,card,old):
    req=js(path/'request.json');result=js(path/'result.json')
    state=fields(path/'status.txt');b=data(path/'data.bin')
    need(req['boot_id']==boot and req['selector']==9 and
         req['length']==len(b)==1048576 and
         sha(b)==result['sha256']==FIRMWARE and
         result['card_after']==card and result['old_after']==old and
         all(state.get(k)=='0' for k in ('status','residual','guard_changes')),
         f'full flash audit {path.name}')
def inventory(path,boot,card,old,reference=None):
    pre=js(path/'preflight.json');result=js(path/'result.json')
    need(pre['boot_id']==result['boot_id']==boot and
         pre['card']==result['card_after']==card and
         pre['old']==result['old_after']==old and
         pre['firmware_sha256']==FIRMWARE and
         result['owner_restored'] and result['page_restored'],
         f'inventory identity {path.name}')
    obs=result['observations']
    regs=obs['inventory']['registers']
    fixed={'0xff000310':'0x00000000','0xff000314':'0x00000000',
           '0xff008500':'0x00000000','0xff008504':'0x000010c7',
           '0xff008510':'0x00006000','0xff008520':'0x00004444',
           '0xff008524':'0x00006754','0xff008528':'0x00080000',
           '0x0000003c':'0xe0000ff0'}
    need(all(regs.get(k)==v for k,v in fixed.items()) and
         obs['inventory']['live_prcb_matches_stock_ibr'] and
         obs['vector']['cached_vector18']=='0xaaaaaaaa' and
         obs['vector']['cached_vector130']=='0xc0000418' and
         obs['vector']['mode']=='0x00000000' and
         all(obs['vector'][phase].get(k)==v for phase in ('pre','post')
             for k,v in {'ipnd':'0x00000000','imsk':'0x000010c7',
                         'imap2':'0x00080000','trr1':'0x00000000',
                         'tcr1':'0x00000000'}.items()),
         f'borrowed state {path.name}')
    if reference is not None:
        need(data(path/'page-before.bin')==reference,
             f'loader page after {path.name}')
    for name in ('inventory','vector'):
        state=fields(path/(name+'-status.txt'))
        need(state.get('done')=='1' and state.get('status')=='0' and
             state.get('residual')=='0',f'{name} status {path.name}')
    return data(path/'page-before.bin')
def acceptance(path,image,digest,boot,card,old):
    pre=js(path/'preflight.json');result=js(path/'result.json')
    need(pre['boot_id']==result['boot_id']==boot and
         pre['card']==result['card_after']==card and
         pre['old']==result['old_after']==old and
         pre['image_sha256']==result['image_sha256']==IMAGE and
         pre['kernel_sha256']==KERNEL and
         pre['fnv']==f'0x{digest:08x}' and
         pre['firmware_sha256']==result['firmware_sha256']==FIRMWARE and
         all(result[k] for k in ('full_audits','owner_restored',
                                 'page_restored','stage_restored')),
         f'acceptance identity {path.name}')
    before=data(path/'page-before.bin');reserved=data(path/'page-reserved.bin')
    owner=data(path/'owner-before.bin');owned=data(path/'owner-reserved.bin')
    need(len(before)==len(reserved)==len(owner)==len(owned)==PAGE and
         data(path/'page-restored.bin')==before and
         words(reserved,0x820,4)==(0x4f4c4c41,0x16161041,PTR,0x80000) and
         words(reserved,0x840,4)==(0x56525352,PTR,0x80000,0x96016004) and
         data(path/'owner-after.bin')[0x2a0:0xaa0]==owner[0x2a0:0xaa0] and
         len(data(path/'stage-before.bin'))==PAGE,
         f'grant/page restoration {path.name}')
    first=(PTR-0xc0000000)//0x8000
    for i in range(256):
        bc,bo=words(owner,0x2a0+i*4,1)[0],words(owner,0x6a0+i*4,1)[0]
        rc,ro=words(owned,0x2a0+i*4,1)[0],words(owned,0x6a0+i*4,1)[0]
        need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo))
             and (not first<=i<first+16 or (bc,bo)==(0,0)),
             f'owner record {i} {path.name}')
    for index,mode in enumerate(('stop','timeout')):
        p=path/mode;entry=result['runs'][index]
        need(entry['mode']==mode and entry['elapsed_ms']>0,
             f'mode result {path.name}/{mode}')
        receipts=js(p/'copy-receipts.json')
        need(len(receipts)==PAGES,f'copy count {mode}')
        for i,r in enumerate(receipts):
            page=image[i*PAGE:(i+1)*PAGE]
            need(r==dict(index=i,sha256=sha(page),fnv=f'0x{fnv(page):08x}'),
                 f'copy page {i} {path.name}/{mode}')
        for name in ('copy','digest','ram-admit'):
            s=fields(p/(name+'-status.txt'))
            need(s.get('done')=='1' and s.get('status')=='0' and
                 s.get('residual')=='0',f'{name} {path.name}/{mode}')
        need(words(data(p/'digest-page.bin'),0x830,4)==
             (0x48534148,0x16161071,PAGES,digest),f'digest {mode}')
        ready=data(p/'ready-page.bin')
        need(words(ready,0xa40,3)==(0x3145534c,NONCE,1) and
             words(ready,0xa50,1)==(0x59444152,),f'READY {mode}')
        page=data(p/'page-after.bin')
        need(len(page)==PAGE and
             page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+reserved[0x830:0xa00]
             and page[0xa80:]==before[0xa80:],f'report bounds {mode}')
        flag=0x504f5453 if mode=='stop' else 0x454d4954
        need(words(page,0xa00,8)==
             (0x314d4152,NONCE,PTR,0x80000,PAGES,0,digest,0) and
             words(page,0xa20,7)==
             (0x314e5552,NONCE,0x31454e4f,PTR,PAGES,digest,flag),
             f'admission report {mode}')
        side=words(page,0xa40,8)
        if mode=='stop':
            need(entry['stale_pending'] is True and
                 words(data(p/'stale-page.bin'),0xa4c,1)==(0xdeadbeef,) and
                 side==(0x3145534c,NONCE,1,0x504f5453,0x59444152,
                        0x214b4341,NONCE,1),f'STOP {path.name}')
        else:
            need(side==(0x3145534c,NONCE,1,0,0x454d4954)+
                 (0xa5a5a5a5,)*3,f'finite timeout {path.name}')
        fw,preflight,entry_sp,restored,ticks,irq_sp,wake,cleanup=words(page,0xa60,8)
        stack=data(p/'irq-stack-after.bin');trace=words(stack,0,11)
        need(fw==restored==0xc0002100 and preflight==0 and
             PTR+16*PAGE<=entry_sp<PTR+17*PAGE and
             PTR+15*PAGE+192<=irq_sp<PTR+16*PAGE and
             ticks>=wake>=5 and cleanup==1 and
             trace[0]==0x444b4c43 and
             trace[1]&0x1f0000==0 and trace[2]&0x1f0000==0 and
             trace[3]==0x2000 and trace[5]==125000 and
             trace[7]<=ticks and PTR<=trace[9]<PTR+15*PAGE and
             trace[10]==0x00180000 and stack[44:64]==b'\xa5'*20 and
             sum(x!=y for x,y in zip(stack,image[15*PAGE:]))==
             entry['irq_stack_changed_bytes'] and
             len(data(p/'entry-stack-after.bin'))==PAGE and
             sha(data(p/'entry-stack-after.bin'))==
             entry['entry_stack_pci_sample_sha256'] and
             data(p/'owner-after.bin')[0x2a0:0xaa0]==owned[0x2a0:0xaa0] and
             entry['ticks']==ticks and entry['wake_tick']==wake and
             entry['cleanup']==cleanup and
             entry['worker_trace']==[f'0x{x:08x}' for x in trace],
             f'RTEMS clock/stack/restore {path.name}/{mode}')
        if mode=='timeout':
            need(ticks>=20 and trace[8]==500000,
                 f'sustained clock {path.name}')
    return before
def verify(root):
    root=Path(root);live=root/'live';accepted=root/'candidate-7'
    image=data(accepted/'image.bin');kernel=data(accepted/'kernel.bin')
    need(len(image)==len(kernel)==PAGES*PAGE and
         sha(image)==IMAGE and sha(kernel)==KERNEL and
         image[:15*PAGE]==kernel[:15*PAGE] and
         image[15*PAGE:]==b'\xa5'*(2*PAGE),'accepted binary')
    digest=fnv(image);need(digest==0x7b154664,'whole-image FNV')
    pre=js(live/'accept-7/preflight.json');boot=pre['boot_id']
    card,old=pre['card'],pre['old']
    need(card['bdf']=='0000:37:09.1' and card['driver']=='myrsread' and
         old['bdf']=='0000:37:04.1' and old['driver'] is None,
         'exact card ownership')
    for name in ('boot2-after-accept6-flash-0','boot2-after-accept6-flash-1',
                 'boot2-after-accept7-flash-0','boot2-after-accept7-flash-1',
                 'boot2-after-repeat-flash-0','boot2-after-repeat-flash-1'):
        audit(live/name,boot,card,old)
    first=inventory(live/'boot2-post-accept6',boot,card,old)
    before=acceptance(live/'accept-7',image,digest,boot,card,old)
    need(before==first,'precall loader page')
    inventory(live/'boot2-post-accept7',boot,card,old,before)
    repeat=acceptance(live/'accept-7-repeat',image,digest,boot,card,old)
    need(repeat==before,'repeat loader page')
    inventory(live/'boot2-post-repeat',boot,card,old,before)
    return {'boot_id':boot,'image_sha256':IMAGE,'firmware_sha256':FIRMWARE,
            'batches':2,'modes_per_batch':2,'full_flash_reads':6,
            'sustained_ticks':[js(live/(name+'/result.json'))['runs'][1]['ticks']
                               for name in ('accept-7','accept-7-repeat')]}

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
