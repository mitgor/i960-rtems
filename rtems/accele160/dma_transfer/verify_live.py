#!/usr/bin/env python3
"""Independent replay of the first AcceleRAID channel-0 card-to-host DMA."""
import importlib.util,json,struct,sys
from pathlib import Path

spec=importlib.util.spec_from_file_location('inventory_verify',Path(__file__).resolve().parents[1]/'dma_inventory_corrected/verify_live.py')
iv=importlib.util.module_from_spec(spec);spec.loader.exec_module(iv)
need,data,sha,fnv,words,js,fields=(iv.need,iv.data,iv.sha,iv.fnv,iv.words,iv.js,iv.fields)
FIRMWARE=iv.base.FIRMWARE
FIRST='f53ce81a5da832a8ec788816a02927834521af4e0cfcf37beb2cc60435dc1c2d'
REUSE='2e2858b30cc89799549eca7aa0626128b36d1529d5bea7a0b1a967ee3e84dcae'
KERNEL='178a25169a2dee0360ec48574a54d381f1af5af51cd6d0e5cf7c5619e36320eb'
PIN='1ef0b6c44c8dceb2c1b820b61ac17a1d3096c6be87dc3978cf2dcb296fe89690'
PTR=0xc0710000; PAGE=4096; PAGES=19; NONCE=0x161610d1
PATTERN=bytes(i^0xa6 for i in range(256))+b'\x5a'*(PAGE-256)

def check_owner(path):
    before=data(path/'owner-before.bin');owned=data(path/'owner-reserved.bin')
    after=data(path/'owner-after.bin')
    need(len(before)==len(owned)==len(after)==PAGE and
         before[0x2a0:0xaa0]==after[0x2a0:0xaa0],'final owner restoration')
    first=(PTR-0xc0000000)//0x8000
    for i in range(256):
        bc,bo=words(before,0x2a0+4*i,1)[0],words(before,0x6a0+4*i,1)[0]
        rc,ro=words(owned,0x2a0+4*i,1)[0],words(owned,0x6a0+4*i,1)[0]
        need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo)) and
             (not first<=i<first+16 or (bc,bo)==(0,0)),f'owner {i}')
    return before

def transfer(path,image,mode,boot,card,old,prior=None):
    pre=js(path/'preflight.json');res=js(path/'result.json')
    image_hash=FIRST if prior is None else REUSE
    need(pre['boot_id']==res['boot_id']==boot and pre['card']==res['card_after']==card and
         pre['old']==res['old_after']==old and
         pre['image_sha256']==res['image_sha256']==image_hash and
         pre['firmware_sha256']==res['firmware_sha256']==FIRMWARE and
         pre['fnv']==f'0x{fnv(image):08x}' and
         all(res[k] for k in ('full_audits','owner_restored','page_restored','stage_restored')) and
         len(res['runs'])==1 and res['runs'][0]['mode']==mode,'transfer identity')
    if prior is not None:
        need(pre['prior_channel0']==[f'0x{x:08x}' for x in prior], 'prior channel binding')
    else:need('prior_channel0' not in pre,'unexpected prior state')
    before=data(path/'page-before.bin');reserved=data(path/'page-reserved.bin')
    need(len(before)==len(reserved)==PAGE and data(path/'page-restored.bin')==before and
         len(data(path/'stage-before.bin'))==PAGE and
         words(reserved,0x820,4)==(0x4f4c4c41,0x16161041,PTR,0x80000) and
         words(reserved,0x840,4)==(0x56525352,PTR,0x80000,0x96016004),
         'grant/page/stage capture')
    check_owner(path)
    for n in ('reserve','release'):
        f=fields(path/(n+'-status.txt'))
        need(f.get('done')=='1' and f.get('status')=='0' and f.get('residual')=='0',n+' command')
    p=path/mode;run=res['runs'][0]
    receipts=js(p/'copy-receipts.json')
    need(len(receipts)==PAGES,'copy count')
    for i,r in enumerate(receipts):
        b=image[i*PAGE:(i+1)*PAGE]
        need(r==dict(index=i,sha256=sha(b),fnv=f'0x{fnv(b):08x}'),f'copy receipt {i}')
    for n in ('copy','digest','ram-admit'):
        f=fields(p/(n+'-status.txt'))
        need(f.get('done')=='1' and f.get('status')=='0' and f.get('residual')=='0',n+' callback')
    need(words(data(p/'digest-page.bin'),0x830,4)==
         (0x48534148,0x16161071,PAGES,fnv(image)),'whole card digest')
    armed=data(p/'callback-returned-page.bin')
    need(words(armed,0xa40,5)==(0x3145534c,NONCE,1,0,0x59444152),
         'firmware callback returned')
    page=data(p/'page-after.bin');stack=data(p/'irq-stack-after.bin')
    task_stack=data(p/'task-irq-stack-after.bin');trace=words(stack,3072,80)
    terminal=0x544c4148 if mode=='halt' else 0x45505845
    need(page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+reserved[0x830:0xa00] and
         words(page,0xa00,8)==(0x314d4152,NONCE,PTR,0x80000,PAGES,0,fnv(image),0) and
         words(page,0xa40,3)==(0x3145534c,NONCE,1) and
         words(page,0xa50,1)==(terminal,) and
         words(page,0xa58,2)==(0,1) and
         page[0xaa4 if prior else 0xa94:]==before[0xaa4 if prior else 0xa94:] and
         trace[0]==0x4b535452 and trace[1]==run['ticks'] and trace[2]==1 and
         trace[9:12]==(0,1,terminal) and trace[18:20]==(1,1) and
         trace[21]!=trace[36] and trace[23]<=trace[22]<trace[24] and
         trace[38]<=trace[37]<trace[39] and trace[33:35]==(1,1) and
         trace[41]==terminal and trace[42]==0x0a010002 and
         trace[43]==0x31414d44 and
         stack[:64]==b'\xa5'*64 and stack[-64:]==b'\xa5'*64 and
         task_stack[:64]==b'\xa5'*64 and task_stack[-64:]==b'\xa5'*64,
         'returned task/ISR/sideband')
    if mode=='halt':
        need(words(data(p/'stale-page.bin'),0xa4c,2)==(0xdeadbeef,0x59444152) and
             words(data(p/'task-stale-page.bin'),0xa4c,2)==(0xdeadbeef,0x49544341) and
             run['stale_pending'] is True and 20<=trace[1]<300,'HALT/stale token')
    else:need(300<=trace[1]<=302,'finite no-host expiry')
    pin_before=fields(p/'dma-pin-before.txt');pin_after=fields(p/'dma-pin-after.txt')
    bus=int(pin_before['bus_addr'],16);desc=trace[78];src=trace[79]
    need(pin_before['bdf']==card['bdf'] and pin_before['length']=='256' and
         pin_before['armed']=='0' and pin_before['verified']=='0' and
         pin_before['guard_changes']=='0' and pin_before['payload_match']=='0' and
         pin_after['bdf']==pin_before['bdf'] and
         pin_after['length']==pin_before['length'] and
         pin_after['bus_addr']==pin_before['bus_addr'] and
         pin_after['armed']=='1' and pin_after['verified']=='1' and
         pin_after['guard_changes']=='0' and pin_after['payload_match']=='1' and
         data(p/'dma-data.bin')==PATTERN and
         words(page,0xa80,5)==(0x31414d44,NONCE,256,0x314e4950,bus) and
         (prior is None or words(page,0xa94,4)==(prior[1],prior[3],prior[5],7)),
         'pinned host target/payload/guards')
    need(trace[68:73]==(2,0,0,0,0) and trace[73:76]==(desc,0,0) and
         trace[76]==run['dma_polls']>0 and trace[77]==bus and
         run['dma_bus']==f'0x{bus:08x}' and PTR<=desc<PTR+15*PAGE and
         desc%32==0 and PTR<=src<PTR+15*PAGE and
         trace[44:52]==(0,desc,0,bus+256,0,src+256,0,7) and
         trace[52:55]==(0,0xc0611320,0) and
         trace[56:60]==(0,0xc060c6ec,0,0x3f) and
         all(x==0 for x in trace[60:68]),'channel-0 completed, other channels')
    need(data(p/'owner-after.bin')[0x2a0:0xaa0]==
         data(path/'owner-reserved.bin')[0x2a0:0xaa0],
         'owner stable through DMA')
    return trace[44:52],before

def verify(root):
    root=Path(root);acc=root/'accepted';live=acc/'live'
    image=data(acc/'image/image.bin');first_image=data(acc/'image/first-transfer-image.bin')
    need(len(image)==len(first_image)==PAGES*PAGE and sha(image)==REUSE and
         sha(first_image)==FIRST and sha(data(acc/'image/kernel.bin'))==KERNEL and
         sha(data(acc/'host/dma_pin.ko'))==PIN,'exact binaries')
    pre=js(live/'accept-halt-corrected/preflight.json');boot=pre['boot_id']
    card,old=pre['card'],pre['old']
    need(card['bdf']=='0000:37:09.1' and card['driver']=='myrsread' and
         old['bdf']=='0000:37:04.1' and old['driver'] is None,'card selection')
    for name in ('pre-flash-0','pre-flash-1','post-halt-flash-0','post-halt-flash-1',
                 'post-reuse-halt-flash-0','post-reuse-halt-flash-1',
                 'post-reuse-expiry-flash-0','post-reuse-expiry-flash-1'):
        iv.base.audit(live/name,boot,card,old)
    first,before=transfer(live/'accept-halt-corrected',first_image,'halt',boot,card,old)
    obs=live/'postdma-inventory';obs_result=js(obs/'result.json')
    need(obs_result['boot_id']==boot and obs_result['owner_restored'] and
         obs_result['page_restored'] and obs_result['stage_restored'] and
         data(obs/'page-before.bin')==before and
         data(obs/'page-restored.bin')==before,'post-DMA inventory restore')
    for mode in ('halt','expiry'):
        t=words(data(obs/mode/'irq-stack-after.bin'),3072,68)
        need(t[43]==0x31414d44 and t[44:52]==first and t[9:11]==(0,1),
             'post-DMA channel state')
    a,before2=transfer(live/'accept-reuse-halt',image,'halt',boot,card,old,first)
    need(before2==before,'HALT loader baseline')
    b,before3=transfer(live/'accept-reuse-expiry',image,'expiry',boot,card,old,a)
    need(before3==before,'expiry loader baseline')
    return {'boot_id':boot,'firmware_sha256':FIRMWARE,'reuse_image_sha256':REUSE,
            'full_flash_reads':8,'card_to_host_bytes':256,
            'modes':['initial-halt','reuse-halt','reuse-expiry'],
            'dma_polls':[js(live/n/'result.json')['runs'][0]['dma_polls']
                         for n in ('accept-halt-corrected','accept-reuse-halt','accept-reuse-expiry')]}

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
