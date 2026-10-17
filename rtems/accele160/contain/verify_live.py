#!/usr/bin/env python3
"""Offline replay for AcceleRAID 160 bounded STOP-ignoring RTEMS containment acceptance."""
import hashlib,importlib.util,json,struct,sys
from pathlib import Path
_baseline=Path(__file__).resolve().parents[1]/'preempt/verify_live.py'
_spec=importlib.util.spec_from_file_location('preempt_verify_live',_baseline)
base=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
helpers=base.base

IMAGE='42e97872951539f5cb4c7418c466364919007d0d35a2dbf81dbf014d58e3ffde'
KERNEL='4ae72fd5aab5fc5f167bed6bcf60f62352d15549034844300735c906bb5b024e'
FNV=0xa61ea90b
PAGE=4096;PAGES=27;PTR=0xc0710000;NONCE=0x161610d1
need=base.need; data=base.data;sha=base.sha;words=base.words;js=base.js;fields=base.fields

def acceptance(path,image,boot,card,old):
    pre=js(path/'preflight.json');result=js(path/'result.json')
    need(pre['boot_id']==result['boot_id']==boot and
         pre['card']==result['card_after']==card and
         pre['old']==result['old_after']==old and
         pre['image_sha256']==result['image_sha256']==IMAGE and
         pre['kernel_sha256']==KERNEL and pre['fnv']==f'0x{FNV:08x}' and
         pre['firmware_sha256']==result['firmware_sha256']==helpers.FIRMWARE and
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
            need(r==dict(index=i,sha256=sha(page),fnv=f'0x{helpers.fnv(page):08x}'),
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
        fw,preflight,entry_sp,restored,ticks,active,handoffs,cleanup=words(page,0xa60,8)
        trace=words(data(p/'irq-stack-after.bin'),0,32)
        need(fw==restored==0xc0002100 and preflight==0 and
             PTR+26*PAGE<=entry_sp<PTR+27*PAGE and active==3 and
             ticks==trace[1]==entry['ticks'] and handoffs==trace[2]==entry['handoffs'] and
             ticks>=10 and handoffs>=2 and trace[3]>0 and cleanup==trace[31]==1 and
             trace[0]==0x324e5443 and
             trace[6]>trace[4]>0 and trace[7]>trace[5]>0 and
             trace[8]==trace[6] and trace[9]==trace[7] and
             trace[11]==trace[12]+1 and trace[13]==trace[14]+1 and
             trace[15:21]==(1,1,2,2,1,1) and
             PTR<=trace[21]<PTR+20*PAGE and PTR<=trace[22]<PTR+20*PAGE and
             trace[23]==trace[24]==0x12 and trace[25]==10000 and
             all(trace[i] for i in range(26,30)) and trace[30]==0 and
             data(p/'worker0-irq-stack-after.bin')[-64:]==b'\xa5'*64 and
             data(p/'worker1-irq-stack-after.bin')[-64:]==b'\xa5'*64 and
             data(p/'owner-after.bin')[0x2a0:0xaa0]==owned[0x2a0:0xaa0] and
             sha(data(p/'entry-stack-after.bin'))==entry['entry_stack_pci_sample_sha256'] and
             entry['worker_trace']==[f'0x{x:08x}' for x in trace],
             f'containment/stack/restore {path.name}/{mode}')
        if mode=='timeout':need(ticks==124 and trace[10]==60,f'finite deadline {mode}')
    return before

def verify(root):
    root=Path(root);live=root/'live';image=data(root/'image/image.bin')
    kernel=data(root/'image/kernel.bin')
    need(len(image)==len(kernel)==PAGES*PAGE and sha(image)==IMAGE and
         sha(kernel)==KERNEL and image[:20*PAGE]==kernel[:20*PAGE] and
         image[20*PAGE:]==b'\xa5'*(7*PAGE) and helpers.fnv(image)==FNV,
         'accepted binary')
    pre=js(live/'attempt-0/preflight.json');boot=pre['boot_id']
    card,old=pre['card'],pre['old']
    need(card['bdf']=='0000:37:09.1' and card['driver']=='myrsread' and
         old['bdf']=='0000:37:04.1' and old['driver'] is None,'card ownership')
    for name in ('after-attempt0-flash-0','after-attempt0-flash-1',
                 'after-accept1-flash-0','after-accept1-flash-1'):
        helpers.audit(live/name,boot,card,old)
    baseline=acceptance(live/'attempt-0',image,boot,card,old)
    helpers.inventory(live/'preflight-0',boot,card,old,baseline)
    acceptance(live/'accept-1',image,boot,card,old)
    helpers.inventory(live/'post-attempt0',boot,card,old,baseline)
    helpers.inventory(live/'post-accept1',boot,card,old,baseline)
    return dict(boot_id=boot,image_sha256=IMAGE,firmware_sha256=helpers.FIRMWARE,
                batches=2,modes_per_batch=2,full_flash_reads=4,
                timeout_ticks=[js(live/('attempt-0' if i==0 else 'accept-1')/'result.json')['runs'][1]['ticks']
                               for i in (0,1)])

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
