#!/usr/bin/env python3
"""Offline replay for AcceleRAID 160 bounded timer-preemption acceptance."""
import hashlib,importlib.util,json,struct,sys
from pathlib import Path
_baseline=Path(__file__).resolve().parents[1]/'autoclock/verify_live.py'
_spec=importlib.util.spec_from_file_location('autoclock_verify_live',_baseline)
base=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

IMAGE='514dfc5b1c8ea1a2ef114ad421f88a12f015a7669dea8af70981dfead107405f'
KERNEL='3f211bf02b85e911836259cd7f83be27b4ffb0c4e93d2aa1c80d89e669bd4f7f'
FNV=0x91f3da52
PAGE=4096;PAGES=27;PTR=0xc0710000;NONCE=0x161610d1
need=base.need; data=base.data;sha=base.sha;words=base.words;js=base.js;fields=base.fields

def acceptance(path,image,boot,card,old):
    pre=js(path/'preflight.json');result=js(path/'result.json')
    need(pre['boot_id']==result['boot_id']==boot and
         pre['card']==result['card_after']==card and
         pre['old']==result['old_after']==old and
         pre['image_sha256']==result['image_sha256']==IMAGE and
         pre['kernel_sha256']==KERNEL and pre['fnv']==f'0x{FNV:08x}' and
         pre['firmware_sha256']==result['firmware_sha256']==base.FIRMWARE and
         all(result[k] for k in ('full_audits','owner_restored','page_restored','stage_restored')),
         f'acceptance identity {path.name}')
    before=data(path/'page-before.bin');reserved=data(path/'page-reserved.bin')
    owner=data(path/'owner-before.bin');owned=data(path/'owner-reserved.bin')
    need(data(path/'page-restored.bin')==before and
         words(reserved,0x820,4)==(0x4f4c4c41,0x16161041,PTR,0x80000) and
         words(reserved,0x840,4)==(0x56525352,PTR,0x80000,0x96016004) and
         data(path/'owner-after.bin')[0x2a0:0xaa0]==owner[0x2a0:0xaa0],
         f'grant/page restoration {path.name}')
    first=(PTR-0xc0000000)//0x8000
    for i in range(256):
        bc,bo=words(owner,0x2a0+4*i,1)[0],words(owner,0x6a0+4*i,1)[0]
        rc,ro=words(owned,0x2a0+4*i,1)[0],words(owned,0x6a0+4*i,1)[0]
        need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo)),
             f'owner record {i} {path.name}')
    for index,mode in enumerate(('stop','timeout')):
        p=path/mode;entry=result['runs'][index]
        need(entry['mode']==mode and entry['elapsed_ms']>0,f'mode {mode}')
        receipts=js(p/'copy-receipts.json')
        need(len(receipts)==PAGES,f'copy count {mode}')
        for i,r in enumerate(receipts):
            page=image[i*PAGE:(i+1)*PAGE]
            need(r==dict(index=i,sha256=sha(page),fnv=f'0x{base.fnv(page):08x}'),
                 f'copy receipt {i} {mode}')
        for name in ('copy','digest','ram-admit'):
            state=fields(p/(name+'-status.txt'))
            need(all(state.get(k)==v for k,v in (('done','1'),('status','0'),('residual','0'))),
                 f'{name} status {mode}')
        need(words(data(p/'digest-page.bin'),0x830,4)==
             (0x48534148,0x16161071,PAGES,FNV),f'digest {mode}')
        ready=data(p/'ready-page.bin')
        need(words(ready,0xa40,3)==(0x3145534c,NONCE,1) and
             words(ready,0xa50,1)==(0x59444152,),f'READY {mode}')
        page=data(p/'page-after.bin')
        need(page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+reserved[0x830:0xa00]
             and page[0xa80:]==before[0xa80:],f'report bounds {mode}')
        flag=0x504f5453 if mode=='stop' else 0x454d4954
        need(words(page,0xa00,8)==(0x314d4152,NONCE,PTR,0x80000,PAGES,0,FNV,0) and
             words(page,0xa20,7)==(0x314e5552,NONCE,0x31454e4f,PTR,PAGES,FNV,flag),
             f'admission report {mode}')
        side=words(page,0xa40,8)
        if mode=='stop':
            need(entry['stale_pending'] is True and
                 words(data(p/'stale-page.bin'),0xa4c,1)==(0xdeadbeef,) and
                 side==(0x3145534c,NONCE,1,flag,0x59444152,0x214b4341,NONCE,1),
                 f'STOP/ACK {mode}')
        else:
            need(side==(0x3145534c,NONCE,1,0,flag)+(0xa5a5a5a5,)*3,
                 f'finite timeout {mode}')
        fw,preflight,entry_sp,restored,ticks,irq_sp,handoffs,cleanup=words(page,0xa60,8)
        trace=words(data(p/'irq-stack-after.bin'),0,28)
        need(fw==restored==0xc0002100 and preflight==0 and
             PTR+26*PAGE<=entry_sp<PTR+27*PAGE and irq_sp==trace[13] and
             ticks==trace[1]==entry['ticks'] and handoffs==trace[2]==entry['handoffs'] and
             ticks>=6 and handoffs>=2 and trace[3]>0 and cleanup==trace[27]==1 and
             trace[0]==0x54504d45 and trace[7]==trace[8] and
             trace[9]==trace[10]>0 and trace[11]==trace[12]>0 and
             PTR+22*PAGE+192<=trace[14]<PTR+24*PAGE and
             PTR+24*PAGE+192<=trace[15]<PTR+26*PAGE and
             trace[17]==trace[18]==0x12 and
             trace[19:25]==(0x10c7,0x80000,0xaaaaaaaa,0,0,0) and
             trace[26]==0 and
             data(p/'worker0-irq-stack-after.bin')[-64:]==b'\xa5'*64 and
             data(p/'worker1-irq-stack-after.bin')[-64:]==b'\xa5'*64 and
             data(p/'owner-after.bin')[0x2a0:0xaa0]==owned[0x2a0:0xaa0] and
             sha(data(p/'entry-stack-after.bin'))==entry['entry_stack_pci_sample_sha256'] and
             entry['worker_trace']==[f'0x{x:08x}' for x in trace],
             f'preemption/stack/restore {path.name}/{mode}')
        if mode=='timeout':need(ticks==120 and trace[6]==60,f'finite deadline {mode}')
    return before

def verify(root):
    root=Path(root);live=root/'live';image=data(root/'image/image.bin')
    kernel=data(root/'image/kernel.bin')
    need(len(image)==len(kernel)==PAGES*PAGE and sha(image)==IMAGE and
         sha(kernel)==KERNEL and image[:20*PAGE]==kernel[:20*PAGE] and
         image[20*PAGE:]==b'\xa5'*(7*PAGE) and base.fnv(image)==FNV,
         'accepted binary')
    pre=js(live/'accept-0/preflight.json');boot=pre['boot_id']
    card,old=pre['card'],pre['old']
    need(card['bdf']=='0000:37:09.1' and card['driver']=='myrsread' and
         old['bdf']=='0000:37:04.1' and old['driver'] is None,'card ownership')
    for name in ('after-attempt0-flash-0','after-attempt0-flash-1',
                 'after-accept0-flash-0','after-accept0-flash-1',
                 'after-accept1-flash-0','after-accept1-flash-1'):
        base.audit(live/name,boot,card,old)
    baseline=acceptance(live/'accept-0',image,boot,card,old)
    acceptance(live/'accept-1',image,boot,card,old)
    base.inventory(live/'post-accept0',boot,card,old,baseline)
    base.inventory(live/'post-accept1',boot,card,old,baseline)
    return dict(boot_id=boot,image_sha256=IMAGE,firmware_sha256=base.FIRMWARE,
                batches=2,modes_per_batch=2,full_flash_reads=6,
                timeout_ticks=[js(live/f'accept-{i}/result.json')['runs'][1]['ticks']
                               for i in (0,1)])

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
