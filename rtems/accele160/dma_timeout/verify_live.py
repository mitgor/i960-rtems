#!/usr/bin/env python3
"""Replay two host-timeout DMA holds, release denial and full audits."""
import importlib.util, json, sys
from pathlib import Path

spec=importlib.util.spec_from_file_location(
    'inventory_verify',Path(__file__).resolve().parents[1]/
    'dma_inventory_corrected/verify_live.py')
iv=importlib.util.module_from_spec(spec);spec.loader.exec_module(iv)
prior_spec=importlib.util.spec_from_file_location(
    'suspend_verify',Path(__file__).resolve().parents[1]/
    'dma_suspend/verify_live.py')
sv=importlib.util.module_from_spec(prior_spec);prior_spec.loader.exec_module(sv)
need,data,sha,fnv,words,js,fields=(iv.need,iv.data,iv.sha,iv.fnv,
                                  iv.words,iv.js,iv.fields)
IMAGE='c2c2234300c5d5cd5caf1fa6f4b05d9df5a1d89cab515085ba1a029b93b9ab5f'
KERNEL='e1765ca3f4c5230f8fe1a1c4dc133c3b9550e5d2e6595f2069257b1835c2cc3d'
PIN='1ef0b6c44c8dceb2c1b820b61ac17a1d3096c6be87dc3978cf2dcb296fe89690'
PAGE=4096; PAGES=19; PTR=0xc0710000; NONCE=0x161610d1
FIRST=0xc0723000; LAST=FIRST+(13000-1)*32; SRC=0xc0789000
PATTERN=bytes(i^0xa6 for i in range(256))+b'\x5a'*(PAGE-256)

def verify_run(path,image,boot,card,old,prior):
    pre=js(path/'preflight.json');result=js(path/'result.json')
    run=result['runs'][0];p=path/'halt'
    need(pre['boot_id']==result['boot_id']==boot and
         pre['card']==result['card_after']==card and
         pre['old']==result['old_after']==old and
         pre['image_sha256']==result['image_sha256']==IMAGE and
         pre['firmware_sha256']==result['firmware_sha256']==iv.base.FIRMWARE and
         pre['fnv']==f'0x{fnv(image):08x}' and
         pre['prior_channel0']==[f'0x{x:08x}' for x in prior] and
         all(result[k] for k in ('full_audits','owner_restored',
                                  'page_restored','stage_restored')) and
         len(result['runs'])==1 and run['mode']=='halt',
         'run identity, full audits and prior channel')
    before=data(path/'page-before.bin');reserved=data(path/'page-reserved.bin')
    owner=data(path/'owner-before.bin');owned=data(path/'owner-reserved.bin')
    owner_after=data(path/'owner-after.bin')
    need(all(len(x)==PAGE for x in (before,reserved,owner,owned,owner_after)) and
         data(path/'page-restored.bin')==before and
         owner[0x2a0:0xaa0]==owner_after[0x2a0:0xaa0] and
         len(data(path/'stage-before.bin'))==PAGE and
         words(reserved,0x820,4)==(0x4f4c4c41,0x16161041,PTR,0x80000) and
         words(reserved,0x840,4)==(0x56525352,PTR,0x80000,0x96016004),
         'stock grant and final restoration')
    first_block=(PTR-0xc0000000)//0x8000
    for i in range(256):
        bc,bo=words(owner,0x2a0+i*4,1)[0],words(owner,0x6a0+i*4,1)[0]
        rc,ro=words(owned,0x2a0+i*4,1)[0],words(owned,0x6a0+i*4,1)[0]
        need((rc,ro)==((16,0x96016004) if first_block<=i<first_block+16
                       else (bc,bo)) and
             (not first_block<=i<first_block+16 or (bc,bo)==(0,0)),
             f'owner record {i}')
    for n in ('reserve','release'):
        st=fields(path/(n+'-status.txt'))
        need(all(st.get(k)==v for k,v in
                 (('done','1'),('status','0'),('residual','0'))),n+' command')
    receipts=js(p/'copy-receipts.json')
    need(len(receipts)==PAGES,'copy count')
    for i,r in enumerate(receipts):
        chunk=image[i*PAGE:(i+1)*PAGE]
        need(r==dict(index=i,sha256=sha(chunk),fnv=f'0x{fnv(chunk):08x}'),
             f'copy receipt {i}')
    for n in ('copy','digest','ram-admit'):
        st=fields(p/(n+'-status.txt'))
        need(all(st.get(k)==v for k,v in
                 (('done','1'),('status','0'),('residual','0'))),n+' command')
    need(words(data(p/'digest-page.bin'),0x830,4)==
         (0x48534148,0x16161071,PAGES,fnv(image)) and
         words(data(p/'callback-returned-page.bin'),0xa40,5)==
         (0x3145534c,NONCE,1,0,0x59444152),
         'digest and callback return')
    page=data(p/'page-after.bin');stack=data(p/'irq-stack-after.bin')
    task_stack=data(p/'task-irq-stack-after.bin');trace=words(stack,3072,95)
    pin_before=fields(p/'dma-pin-before.txt')
    pin_after=fields(p/'dma-pin-after.txt');bus=int(pin_before['bus_addr'],16)
    need(page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+
         reserved[0x830:0xa00] and
         page[0xaa4:]==before[0xaa4:] and
         words(page,0xa00,8)==
         (0x314d4152,NONCE,PTR,0x80000,PAGES,0,fnv(image),0) and
         words(page,0xa40,3)==(0x3145534c,NONCE,1) and
         words(page,0xa50,1)==(0x544c4148,) and
         words(page,0xa58,2)==(0,1) and
         words(page,0xa80,9)==
         (0x31414d44,NONCE,2048,0x314e4950,bus,
          prior[1],prior[3],prior[5],prior[7]) and
         data(p/'owner-after.bin')[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
         'loader sideband and in-run owner')
    need(trace[0]==0x4b535452 and trace[1]==run['ticks']==128 and
         trace[2]==1 and trace[9:12]==(0,1,0x544c4148) and
         trace[18:20]==(1,1) and trace[21]!=trace[36] and
         trace[23]<=trace[22]<trace[24] and
         trace[38]<=trace[37]<trace[39] and
         trace[33:35]==(1,1) and trace[41]==0x544c4148 and
         trace[42]==0x0a010002 and trace[43]==0x31414d44 and
         stack[:64]==b'\xa5'*64 and stack[-64:]==b'\xa5'*64 and
         task_stack[:64]==b'\xa5'*64 and task_stack[-64:]==b'\xa5'*64,
         'RTEMS task/ISR/stack restoration')
    need(pin_before['bdf']==card['bdf'] and pin_before['length']=='256' and
         pin_before['armed']=='0' and pin_before['verified']=='0' and
         pin_before['guard_changes']=='0' and
         pin_after['bdf']==pin_before['bdf'] and
         pin_after['bus_addr']==pin_before['bus_addr'] and
         pin_after['armed']=='1' and pin_after['verified']=='1' and
         pin_after['guard_changes']=='0' and pin_after['payload_match']=='1' and
         data(p/'dma-data.bin')==PATTERN,
         'pinned host payload and both guards')
    held=data(p/'held-page.bin');timed=data(p/'host-timeout-page.bin')
    held_owner=data(p/'held-owner.bin');held_pin=fields(p/'held-pin.txt')
    denial=js(p/'release-denied.json')
    need(words(held,0xa50,1)==words(timed,0xa50,1)==(0x444c4548,) and
         words(held,0xa4c,1)==words(timed,0xa4c,1)==(0x544c4148,) and
         held_owner[0x2a0:0xaa0]==owned[0x2a0:0xaa0] and
         held_pin['bdf']==card['bdf'] and
         held_pin['bus_addr']==pin_before['bus_addr'] and
         held_pin['armed']=='1' and held_pin['verified']=='0' and
         held_pin['released']=='0' and held_pin['guard_changes']=='0' and
         denial['errno']==run['premature_release_errno']==16 and
         150<=denial['deadline_ms']==run['host_timeout_ms']<500,
         'host timeout retained pin/grant and rejected release')
    need(trace[68:73]==(2,0,0,0,0) and
         trace[73:76]==(LAST,0,0) and
         trace[76]==run['dma_polls']>0 and trace[77]==bus and
         trace[78:84]==(FIRST,SRC,LAST,13000,1,21) and
         run['stop_seen_active']==1 and run['stop_seen_tick']==21 and
         trace[84:88]==(21,101,0,1) and trace[94]==1 and
         trace[88:91]==trace[91:94] and trace[88]!=LAST and
         run['suspend_tick']==21 and run['resume_tick']==101 and
         run['hold_dar']==f'0x{trace[88]:08x}' and
         run['hold_bcr']==trace[89] and
         run['hold_ndar']==f'0x{trace[90]:08x}' and
         trace[44:52]==(0,LAST,0,bus+2048,0,SRC+2048,0,7) and
         trace[52:55]==(0,0xc0611320,0) and
         trace[56:60]==(0,0xc060c6ec,0,0x3f) and
         all(x==0 for x in trace[60:68]),
         'STOP, stable suspend/resume and completed release')
    return trace[44:52],before

def verify(root):
    root=Path(root);acc=root/'accepted';live=acc/'live'
    image=data(acc/'image/image.bin')
    need(len(image)==PAGES*PAGE and sha(image)==IMAGE and
         sha(data(acc/'image/kernel.bin'))==KERNEL and
         sha(data(acc/'host/dma_pin.ko'))==PIN,'exact binaries')
    prior_root=root.parent/'accele160-dma-suspend-20261017'
    sv.verify(prior_root)
    src=prior_root/'accepted/live/attempt-1'
    dup=acc/'prior/attempt-1'
    files=sorted(p.relative_to(src) for p in src.rglob('*') if p.is_file())
    need(files==sorted(p.relative_to(dup) for p in dup.rglob('*') if p.is_file())
         and all(data(src/p)==data(dup/p) for p in files),
         'exact prior same-boot audited run')
    pre=js(live/'attempt-0/preflight.json')
    boot,card,old=pre['boot_id'],pre['card'],pre['old']
    need(card['bdf']=='0000:37:09.1' and card['driver']=='myrsread' and
         old['bdf']=='0000:37:04.1' and old['driver'] is None,'selected cards')
    for name in ('pre-flash-0','pre-flash-1','post-flash-0','post-flash-1'):
        iv.base.audit(live/name,boot,card,old)
    prior_trace=words(data(dup/'halt/irq-stack-after.bin'),3072,68)
    first,before=verify_run(live/'attempt-0',image,boot,card,old,prior_trace[44:52])
    second,before2=verify_run(live/'attempt-1',image,boot,card,old,first)
    need(before==before2 and first[1]==second[1]==LAST and
         first[5]==second[5]==SRC+2048,'loader/channel baseline')
    return dict(boot_id=boot,firmware_sha256=iv.base.FIRMWARE,
                image_sha256=IMAGE,full_flash_reads=4,
                accepted_timeout_recovery_runs=2,chain_descriptors=13000,
                bytes_per_run=13000*2048,stop_ticks=[21,21],
                suspend_ticks=[21,21],resume_ticks=[101,101],
                terminal_ticks=[128,128])

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
