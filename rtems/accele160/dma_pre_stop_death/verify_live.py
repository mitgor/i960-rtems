#!/usr/bin/env python3
"""Replay two pre-STOP process deaths and bounded no-STOP expiry audits."""
import importlib.util,json,struct,sys
from pathlib import Path

spec=importlib.util.spec_from_file_location('process_death_verify',
    Path(__file__).resolve().parents[1]/'dma_process_death/verify_live.py')
pv=importlib.util.module_from_spec(spec);spec.loader.exec_module(pv)
tv=pv.tv
need,data,sha,fnv,words,js,fields=(tv.need,tv.data,tv.sha,tv.fnv,
                                  tv.words,tv.js,tv.fields)
PAGE=4096; PTR=0xc0710000; NONCE=0x161610d1
IMAGE='0477635a365a3ff40ca7b35759860884ec0aef7663ce70c72842c23dbe28427c'
KERNEL='3665b96dae43f0bf893923a53b05e9bd0b31a0bb04a2e476245ad0fc83b2533b'
PIN=tv.PIN
LAST=tv.LAST; SRC=tv.SRC

def run(path,image,boot,card,old,prior):
    pre=js(path/'preflight.json');death=js(path/'death-intent.json')
    observed=js(path/'death-observation.json');result=js(path/'result.json')
    p=path/'expiry'
    need(pre['boot_id']==death['boot_id']==observed['boot_id']==
         result['boot_id']==boot and
         pre['card']==result['card_after']==card and
         pre['old']==result['old_after']==old and
         pre['image_sha256']==death['image_sha256']==result['image_sha256']==
         IMAGE and pre['firmware_sha256']==result['firmware_sha256']==
         tv.iv.base.FIRMWARE and
         pre['fnv']==f'0x{fnv(image):08x}' and
         pre['prior_channel0']==[f'0x{x:08x}' for x in prior] and
         death['pid']==observed['pid']==result['killed_pid'] and
         observed['process_absent'] and
         result['process_absent_before_recovery'] and result['mode']=='expiry' and
         all(result[k] for k in ('full_audits','owner_restored',
                                  'page_restored','stage_restored')),
         'same-boot process death and audited recovery')
    before=data(path/'page-before.bin');reserved=data(path/'page-reserved.bin')
    owner=data(path/'owner-before.bin');owned=data(path/'owner-reserved.bin')
    need(all(len(x)==PAGE for x in (before,reserved,owner,owned)) and
         data(path/'page-restored.bin')==before and
         data(path/'owner-after.bin')[0x2a0:0xaa0]==owner[0x2a0:0xaa0] and
         len(data(path/'stage-before.bin'))==PAGE and
         words(reserved,0x820,4)==(0x4f4c4c41,0x16161041,PTR,0x80000) and
         words(reserved,0x840,4)==(0x56525352,PTR,0x80000,0x96016004),
         'grant/page/stage final restoration')
    first=(PTR-0xc0000000)//0x8000
    for i in range(256):
        bc,bo=words(owner,0x2a0+4*i,1)[0],words(owner,0x6a0+4*i,1)[0]
        rc,ro=words(owned,0x2a0+4*i,1)[0],words(owned,0x6a0+4*i,1)[0]
        need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo))
             and (not first<=i<first+16 or (bc,bo)==(0,0)),
             f'owner record {i}')
    for name in ('reserve','release'):
        st=fields(path/(name+'-status.txt'))
        need(all(st.get(k)==v for k,v in
                 (('done','1'),('status','0'),('residual','0'))),name+' command')
    receipts=js(p/'copy-receipts.json')
    need(len(receipts)==19,'copy count')
    for i,r in enumerate(receipts):
        b=image[i*PAGE:(i+1)*PAGE]
        need(r==dict(index=i,sha256=sha(b),fnv=f'0x{fnv(b):08x}'),
             f'copy receipt {i}')
    for name in ('copy','digest','ram-admit'):
        st=fields(p/(name+'-status.txt'))
        need(all(st.get(k)==v for k,v in
                 (('done','1'),('status','0'),('residual','0'))),name+' command')
    need(words(data(p/'digest-page.bin'),0x830,4)==
         (0x48534148,NONCE-0x60,19,fnv(image)) and
         words(data(p/'callback-returned-page.bin'),0xa40,5)==
         (0x3145534c,NONCE,1,0,0x59444152),
         'whole digest and callback return')
    active=data(p/'active-page.bin')
    page=data(p/'page-after.bin');stack=data(p/'irq-stack-after.bin')
    task_stack=data(p/'task-irq-stack-after.bin')
    trace=words(stack,3072,95)
    pin_before=fields(p/'dma-pin-before.txt')
    pin_active=death['pin_status']
    pin_after=fields(p/'dma-pin-after.txt')
    bus=int(pin_before['bus_addr'],16)
    need(death['active_page_sha256']==sha(active) and
         observed['premature_release_errno']==16 and
         observed['pin_status']['bus_addr']==pin_active['bus_addr'] and
         observed['pin_status']['armed']=='1' and
         observed['pin_status']['verified']=='0' and
         words(active,0xa40,3)==(0x3145534c,NONCE,1) and
         words(active,0xa4c,2)==(0,0x59535542) and
         words(data(p/'recovery-initial-page.bin'),0xa50,1)[0] in
             (0x59535542,0x45505845) and
         pin_active['bdf']==card['bdf'] and pin_active['armed']=='1' and
         pin_active['verified']=='0' and pin_active['released']=='0' and
         pin_active['guard_changes']=='0',
         'pre-STOP active checkpoint survived process death')
    need(page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+
         reserved[0x830:0xa00] and page[0xaa4:]==before[0xaa4:] and
         words(page,0xa00,8)==
         (0x314d4152,NONCE,PTR,0x80000,19,0,fnv(image),0) and
         words(page,0xa40,5)==
         (0x3145534c,NONCE,1,0,0x45505845) and
         words(page,0xa58,2)==(0,1) and
         words(page,0xa80,9)==
         (0x31414d44,NONCE,2048,0x314e4950,bus,
          prior[1],prior[3],prior[5],prior[7]) and
         data(p/'owner-after.bin')[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
         'terminal loader and owned grant')
    need(trace[0]==0x4b535452 and trace[1]==result['terminal_ticks']==300 and
         trace[2]==1 and trace[9:12]==(0,1,0x45505845) and
         trace[18:20]==(1,1) and trace[21]!=trace[36] and
         trace[23]<=trace[22]<trace[24] and
         trace[38]<=trace[37]<trace[39] and
         trace[33:35]==(1,1) and trace[41:44]==
         (0x45505845,0x0a010002,0x31414d44) and
         trace[68:73]==(2,0,0,0,0) and trace[73:76]==(LAST,0,0) and
         trace[77]==bus and trace[78:84]==
         (0xc0723000,SRC,LAST,13000,0,0) and
         all(x==0 for x in trace[84:95]) and
         result['stop_tick']==0 and result['resume_tick']==0 and
         result['channel0']==[f'0x{x:08x}' for x in trace[44:52]] and
         trace[44:52]==(0,LAST,0,bus+2048,0,SRC+2048,0,7) and
         trace[52:55]==(0,0xc0611320,0) and
         0xf0000000<=trace[55]<=0xfffffffc and trace[55]%4==0 and
         trace[56]==0 and trace[57] in (0xc060c6ec,PTR+0x80000) and
         trace[58:60]==(0,0x3f) and
         all(x==0 for x in trace[60:68]) and
         stack[:64]==b'\xa5'*64 and stack[-64:]==b'\xa5'*64 and
         task_stack[:64]==b'\xa5'*64 and task_stack[-64:]==b'\xa5'*64,
         'DMA/RTEMS/stock channel completion')
    need(pin_before['bdf']==pin_after['bdf']==card['bdf'] and
         pin_before['bus_addr']==pin_active['bus_addr']==pin_after['bus_addr'] and
         pin_before['armed']=='0' and pin_before['verified']=='0' and
         pin_after['armed']=='1' and pin_after['verified']=='1' and
         pin_after['guard_changes']=='0' and pin_after['payload_match']=='1' and
         data(p/'dma-data.bin')==tv.PATTERN,
         'pinned host payload and guards')
    return trace[44:52]

def verify(root):
    root=Path(root);acc=root/'accepted';live=acc/'live'
    prior_root=root.parent/'accele160-dma-process-death-20261017'
    pv.verify(prior_root)
    image=data(acc/'image/image.bin')
    need(len(image)==19*PAGE and sha(image)==IMAGE and
         sha(data(acc/'image/kernel.bin'))==KERNEL and
         sha(data(acc/'host/dma_pin.ko'))==PIN and
         data(acc/'source/start_and_die.py')==
         data(Path(__file__).with_name('start_and_die.py')) and
         data(acc/'source/recover.py')==
         data(Path(__file__).with_name('recover.py')),
         'exact image, module and sources')
    pre=js(live/'attempt-0/preflight.json')
    boot,card,old=pre['boot_id'],pre['card'],pre['old']
    need(card['bdf']=='0000:37:09.1' and card['driver']=='myrsread' and
         old['bdf']=='0000:37:04.1' and old['driver'] is None,
         'selected cards')
    for name in ('pre-flash-0','pre-flash-1','mid-flash-0',
                 'mid-flash-1','post-flash-0','post-flash-1'):
        tv.iv.base.audit(live/name,boot,card,old)
    ptrace=words(data(prior_root/'accepted/live/attempt-1/halt/irq-stack-after.bin'),3072,68)
    first=run(live/'attempt-0',image,boot,card,old,ptrace[44:52])
    second=run(live/'attempt-1',image,boot,card,old,first)
    need(first[1]==second[1]==LAST and first[5]==second[5]==SRC+2048,
         'two independent completed buffers')
    return dict(boot_id=boot,image_sha256=IMAGE,firmware_sha256=tv.iv.base.FIRMWARE,
                full_flash_reads=6,pre_stop_death_recoveries=2,
                terminal_ticks=[300,300],bytes_per_run=13000*2048)

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
