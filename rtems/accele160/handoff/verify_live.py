#!/usr/bin/env python3
"""Offline replay of AcceleRAID 160 callback-free timer handoff acceptance."""
import importlib.util,json,struct,sys
from pathlib import Path

baseline=Path(__file__).resolve().parents[1]/'autoclock/verify_live.py'
spec=importlib.util.spec_from_file_location('autoclock_verify_live',baseline)
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
need,data,sha,fnv,words,js,fields=(base.need,base.data,base.sha,base.fnv,
                                  base.words,base.js,base.fields)
IMAGE='1f448cdf017d3410e03a493f45f7ad37a8e4f4f3268c05270e5bc7fe10952f2a'
FNV=0xe08fbc64
PAGE=4096; PAGES=3; PTR=0xc0710000; NONCE=0x161610d1

def acceptance(path,image,boot,card,old):
    pre=js(path/'preflight.json');result=js(path/'result.json')
    need(pre['boot_id']==result['boot_id']==boot and
         pre['card']==result['card_after']==card and
         pre['old']==result['old_after']==old and
         pre['image_sha256']==result['image_sha256']==IMAGE and
         pre['firmware_sha256']==result['firmware_sha256']==base.FIRMWARE and
         pre['fnv']==f'0x{FNV:08x}' and
         all(result[k] for k in ('full_audits','owner_restored',
                                  'page_restored','stage_restored')),
         'accepted run identity')
    before=data(path/'page-before.bin');reserved=data(path/'page-reserved.bin')
    owner=data(path/'owner-before.bin');owned=data(path/'owner-reserved.bin')
    need(all(len(b)==PAGE for b in (before,reserved,owner,owned)) and
         data(path/'page-restored.bin')==before and
         words(reserved,0x820,4)==(0x4f4c4c41,0x16161041,PTR,0x80000) and
         words(reserved,0x840,4)==(0x56525352,PTR,0x80000,0x96016004) and
         data(path/'owner-after.bin')[0x2a0:0xaa0]==owner[0x2a0:0xaa0],
         'grant/page restore')
    first=(PTR-0xc0000000)//0x8000
    for i in range(256):
        bc,bo=words(owner,0x2a0+4*i,1)[0],words(owner,0x6a0+4*i,1)[0]
        rc,ro=words(owned,0x2a0+4*i,1)[0],words(owned,0x6a0+4*i,1)[0]
        need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo))
             and (not first<=i<first+16 or (bc,bo)==(0,0)),
             f'owner record {i}')
    need(fields(path/'reserve-status.txt')['status']=='0' and
         fields(path/'release-status.txt')['status']=='0',
         'grant command status')
    for index,mode in enumerate(('expiry','halt')):
        p=path/mode;entry=result['runs'][index]
        need(entry['mode']==mode and entry['elapsed_ms']>0 and
             entry['callback_ms']>0, f'run timing {mode}')
        receipts=js(p/'copy-receipts.json')
        need(len(receipts)==PAGES,f'copy count {mode}')
        for i,r in enumerate(receipts):
            b=image[i*PAGE:(i+1)*PAGE]
            need(r==dict(index=i,sha256=sha(b),fnv=f'0x{fnv(b):08x}'),
                 f'copy page {i} {mode}')
        for name in ('copy','digest','ram-admit'):
            st=fields(p/(name+'-status.txt'))
            need(all(st.get(k)==v for k,v in
                     (('done','1'),('status','0'),('residual','0'))),
                 f'{name} command {mode}')
        need(words(data(p/'digest-page.bin'),0x830,4)==
             (0x48534148,0x16161071,PAGES,FNV),f'whole digest {mode}')
        armed=data(p/'callback-returned-page.bin')
        need(words(armed,0xa40,5)==
             (0x3145534c,NONCE,1,0,0x59444152),
             f'callback returned armed {mode}')
        page=data(p/'page-after.bin');side=words(page,0xa40,8)
        terminal=0x45505845 if mode=='expiry' else 0x544c4148
        need(page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+
             reserved[0x830:0xa00] and page[0xa80:]==before[0xa80:] and
             words(page,0xa00,8)==
             (0x314d4152,NONCE,PTR,0x80000,PAGES,0,FNV,0) and
             words(page,0xa20,7)==
             (0x314e5552,NONCE,0x31454e4f,PTR,PAGES,FNV,0x4d524141) and
             side[:3]==(0x3145534c,NONCE,1) and side[4]==terminal and
             side[6:]==(0,1),f'report/sideband bounds {mode}')
        if mode=='halt':
            stale=data(p/'stale-page.bin')
            need(entry['stale_pending'] is True and
                 words(stale,0xa4c,2)==(0xdeadbeef,0x59444152) and
                 side[3]==0x544c4148,f'stale/valid HALT {mode}')
        fw,preflight,entry_sp,restored,ticks,irq_sp,entries,restore=words(page,0xa60,8)
        stack=data(p/'irq-stack-after.bin');trace=words(stack,3072,15)
        need(fw==restored==0xc0002100 and preflight==0 and
             PTR+2*PAGE<=entry_sp<PTR+3*PAGE and
             PTR+PAGE+192<=irq_sp<PTR+2*PAGE and
             ticks==trace[1]==entry['ticks'] and entries==trace[2]==1 and
             0<trace[3]<ticks and restore==trace[10]==1 and
             trace[0]==0x31464f48 and side[5]==trace[4] and
             0xc0000100<=trace[4]<PTR and
             (trace[5]&0x1f0000)==0 and trace[7]==0x12 and
             trace[8]==irq_sp and trace[9]==0 and trace[11]==terminal and
             trace[12]==((trace[14]&~0x1f0000)|(trace[13]&0x1f0000)) and
             stack[:64]==b'\xa5'*64 and stack[-64:]==b'\xa5'*64 and
             sum(x!=y for x,y in zip(stack,image[PAGE:2*PAGE]))==
             entry['stack_changed_bytes'] and
             data(p/'owner-after.bin')[0x2a0:0xaa0]==owned[0x2a0:0xaa0] and
             entry['firmware_sp']==f'0x{fw:08x}' and
             entry['restored_sp']==f'0x{restored:08x}' and
             entry['irq_sp']==f'0x{irq_sp:08x}' and
             entry['frame']==f'0x{trace[4]:08x}' and
             entry['frame_pc']==f'0x{trace[5]:08x}' and
             entry['frame_vector']==f'0x{trace[7]:08x}',
             f'ISR/context/restoration {mode}')
        if mode=='expiry':need(ticks==300,f'finite expiry {mode}')
        else:need(2<=ticks<300,f'bounded HALT {mode}')
    return before

def verify(root):
    root=Path(root);live=root/'live';image=data(root/'image/image.bin')
    need(len(image)==PAGES*PAGE and sha(image)==IMAGE and fnv(image)==FNV
         and image[PAGE:]==b'\xa5'*(2*PAGE),'accepted image')
    pre=js(live/'attempt-5/preflight.json');boot=pre['boot_id']
    card,old=pre['card'],pre['old']
    need(card['bdf']=='0000:37:09.1' and card['driver']=='myrsread' and
         old['bdf']=='0000:37:04.1' and old['driver'] is None,
         'old/new card selection')
    for name in ('pre-flash-0','pre-flash-1','post-flash-0','post-flash-1'):
        base.audit(live/name,boot,card,old)
    baseline=base.inventory(live/'preflight',boot,card,old)
    before=acceptance(live/'attempt-5',image,boot,card,old)
    need(before==baseline,'pre-run loader page')
    base.inventory(live/'postflight',boot,card,old,before)
    return dict(boot_id=boot,image_sha256=IMAGE,firmware_sha256=base.FIRMWARE,
                callback_free_modes=['expiry','halt'],full_flash_reads=4,
                ticks=[x['ticks'] for x in js(live/'attempt-5/result.json')['runs']])

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
