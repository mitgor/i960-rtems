#!/usr/bin/env python3
"""Resume a held finite DMA after owner death, then audit before release."""
import argparse,errno,fcntl,json,mmap,struct,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/lease_probe'))
from run_lease import (BDF,OLD,PAGE,DEVICE,DEBUG,FIRMWARE,HANDLER,MODULES,
                       NONCE,need,sha,fields,fnv,status,command,release,verify_read)
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

IMAGE='28b679b9de196c0944603f0a66adc763bb7ac37f4a1635da42e6351a7a99008b'
PIN='1ef0b6c44c8dceb2c1b820b61ac17a1d3096c6be87dc3978cf2dcb296fe89690'
PIN_DEBUG=Path('/sys/kernel/debug/accele-dma-pin')
PTR=0xc0710000
LAST=0xc0723000+(13000-1)*32
SRC=0xc0789000

def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def word(b,offset):return struct.unpack_from('<I',b,offset)[0]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('out','handler','firmware','image','dma_module','prior_run',
              'readback0','readback1'):
        p.add_argument('--'+n.replace('_','-'),required=True,type=Path)
    a=p.parse_args()
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    need(sha(a.handler.read_bytes())==HANDLER and
         sha(a.firmware.read_bytes())==FIRMWARE and
         sha(a.image.read_bytes())==IMAGE and
         sha(a.dma_module.read_bytes())==PIN,'exact inputs')
    payload=a.image.read_bytes();digest=fnv(payload)
    need(len(payload)==19*PAGE and digest==0x83ab0c8b and
         payload[15*PAGE:]==b'\xa5'*(4*PAGE),'upload image')
    pre=json.loads((a.out/'preflight.json').read_text())
    death=json.loads((a.out/'death-intent.json').read_text())
    run=a.out/'halt'
    held_page=(run/'held-page.bin').read_bytes()
    need(death['held_page_sha256']==sha(held_page) and
         word(held_page,0xa4c)==0x544c4148 and
         word(held_page,0xa50)==0x444c4548,
         'held DMA checkpoint')
    card=select(BDF,'accele160',driver='myrsread')
    old=select(OLD,'dac960pg')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    host,=DEVICE.glob('host*/scsi_host/host*')
    need(old['driver'] is None and pre['boot_id']==death['boot_id']==boot and
         pre['card']==card and pre['old']==old and
         pre['image_sha256']==death['image_sha256']==IMAGE and
         pre['firmware_sha256']==FIRMWARE and
         pre['handler_sha256']==HANDLER and
         pre['fnv']==f'0x{digest:08x}' and
         (host/'stock_descriptor').read_text().startswith('state=0 ') and
         not list(DEVICE.glob('host*/target*/*/block/*')) and
         not Path('/proc',str(death['pid'])).exists(),
         'same-boot card and dead host process')
    for rd in (a.readback0,a.readback1):verify_read(rd,boot,card,old)
    prior=json.loads((a.prior_run/'result.json').read_text())
    prior_pre=json.loads((a.prior_run/'preflight.json').read_text())
    prior_mode=prior.get('mode','halt')
    ptrace=struct.unpack_from('<68I',
            (a.prior_run/prior_mode/'irq-stack-after.bin').read_bytes(),3072)
    prior_regs=ptrace[44:52]
    need(prior['boot_id']==prior_pre['boot_id']==boot and
         prior['full_audits'] and prior['owner_restored'] and
         prior['page_restored'] and prior['stage_restored'] and
         pre['prior_channel0']==[f'0x{x:08x}' for x in prior_regs],
         'same-boot prior audited channel')
    need(all(Path('/sys/module',n+'_command').exists() for n in
             ('release','copy','digest','admit')) and
         Path('/sys/module/dma_pin').exists() and
         not Path('/sys/module/reserve_command').exists(),
         'retained modules')
    receipts=json.loads((run/'copy-receipts.json').read_text())
    need(len(receipts)==19 and all(r==dict(index=i,
             sha256=sha(payload[i*PAGE:(i+1)*PAGE]),
             fnv=f'0x{fnv(payload[i*PAGE:(i+1)*PAGE]):08x}')
             for i,r in enumerate(receipts)) and
         word((run/'digest-page.bin').read_bytes(),0x830)==0x48534148 and
         struct.unpack_from('<4I',(run/'digest-page.bin').read_bytes(),0x830)==
             (0x48534148,0x16161071,19,digest) and
         all(fields(run/(n+'-status.txt')).get('done')=='1' and
             fields(run/(n+'-status.txt')).get('status')=='0' and
             fields(run/(n+'-status.txt')).get('residual')=='0'
             for n in ('copy','digest','ram-admit')),
         'upload copy/digest/admit receipts')
    initial_pin=fields(PIN_DEBUG/'status')
    bus=int(initial_pin['bus_addr'],16)
    need(all(initial_pin[k]==death['pin_status'][k] for k in
             ('bdf','bus_addr','length','armed','verified','released',
              'guard_changes')) and
         initial_pin['bdf']==BDF and initial_pin['armed']=='1' and
         initial_pin['verified']=='0' and initial_pin['released']=='0' and
         initial_pin['guard_changes']=='0','retained pinned allocation')
    denied=0
    try:(PIN_DEBUG/'release').write_text('release\n')
    except OSError as exc:denied=exc.errno
    need(denied==errno.EBUSY,'release before recovery must be denied')
    save(a.out/'death-observation.json',dict(pid=death['pid'],
         process_absent=True,boot_id=boot,pin_status=initial_pin,
         premature_release_errno=denied,admit_status=status('ram-admit')))
    before=(a.out/'page-before.bin').read_bytes()
    reserved=(a.out/'page-reserved.bin').read_bytes()
    owner=(a.out/'owner-before.bin').read_bytes()
    owned=(a.out/'owner-reserved.bin').read_bytes()
    stage_before=(a.out/'stage-before.bin').read_bytes()
    need(all(len(x)==PAGE for x in (before,reserved,owner,owned,stage_before)) and
         before==a.handler.read_bytes()[0xf000-0xe1d8:]+
                 b'\xff'*(PAGE-len(a.handler.read_bytes()[0xf000-0xe1d8:])) and
         struct.unpack_from('<4I',reserved,0x840)==
                 (0x56525352,PTR,0x80000,0x96016004),
         'saved handler/grant baseline')
    first=(PTR-0xc0000000)//0x8000
    for i in range(256):
        bc,bo=word(owner,0x2a0+i*4),word(owner,0x6a0+i*4)
        rc,ro=word(owned,0x2a0+i*4),word(owned,0x6a0+i*4)
        need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo))
             and (not first<=i<first+16 or (bc,bo)==(0,0)),
             f'grant owner {i}')
    cfg=(DEVICE/'config').open('r+b',buffering=0)
    res=(DEVICE/'resource0').open('r+b',buffering=0)
    bar=mmap.mmap(res.fileno(),2*PAGE)
    cfg.seek(0x44);found=word(cfg.read(4),0)
    need(found in (0xc000e000,0xc0384000) or
         (found==0xc0000000 and (run/'recovery-initial-page.bin').exists()),
         'expected SIGKILL or retained-retry aperture mapping')
    def translate(addr):
        cfg.seek(0x44);cfg.write(struct.pack('<I',addr));cfg.seek(0x44)
        need(word(cfg.read(4),0)==addr,'PIATVR readback')
    def snap(addr):
        translate(addr);return bytes(bar[PAGE:2*PAGE])
    def write(addr,offset,b):
        translate(addr);bar[PAGE+offset:PAGE+offset+len(b)]=b
        need(bytes(bar[PAGE+offset:PAGE+offset+len(b)])==b,'BAR writeback')
    def ownercheck(ref):
        got=snap(0xc0384000)
        need(got[0x2a0:0xaa0]==ref[0x2a0:0xaa0],'owner words')
        return got
    try:
        need(ownercheck(owned)[0x2a0:0xaa0]==owned[0x2a0:0xaa0] and
             snap(PTR+0x7e000)==stage_before,'held grant/stage')
        current=snap(0xc000e000)
        (run/'recovery-initial-page.bin').write_bytes(current)
        external=word(current,0xa50)==0x444c4548
        need((external and word(current,0xa4c)==0x544c4148) or
             (not external and word(current,0xa50)==0x544c4148 and
              word(current,0xa4c)==0x544c4148),
             'held or fallback terminal state; retain pin/grant')
        if external:
            time.sleep(.1)
            held_again=snap(0xc000e000)
            (run/'recovery-held-page.bin').write_bytes(held_again)
            need(word(held_again,0xa4c)==0x544c4148 and
                 word(held_again,0xa50)==0x444c4548 and
                 fields(PIN_DEBUG/'status')['guard_changes']=='0',
                 'stable held checkpoint before independent resume')
            write(0xc000e000,0xa4c,struct.pack('<I',0x4d555352))
            (run/'resume-written-page.bin').write_bytes(snap(0xc000e000))
            need(word((run/'resume-written-page.bin').read_bytes(),0xa4c)==
                 0x4d555352,'exact resume token readback')
        terminal=0x45505845 if external else 0x544c4148
        limit=time.monotonic()+6.0
        while word(current,0xa50)!=terminal and time.monotonic()<limit:
            time.sleep(.005);current=snap(0xc000e000)
        need(word(current,0xa50)==terminal,
             'finite chain not terminal; retain pin/grant')
        time.sleep(.02);page=snap(0xc000e000)
        time.sleep(.02);need(page==snap(0xc000e000),'terminal quiet interval')
        (run/'page-after.bin').write_bytes(page)
        stack=snap(PTR+15*PAGE)
        task_stack=snap(PTR+17*PAGE)
        (run/'irq-stack-after.bin').write_bytes(stack)
        (run/'task-irq-stack-after.bin').write_bytes(task_stack)
        (run/'owner-after.bin').write_bytes(ownercheck(owned))
        trace=struct.unpack_from('<96I',stack,3072)
        words=struct.unpack_from('<8I',page,0xa40)
        diag=struct.unpack_from('<8I',page,0xa60)
        control=struct.unpack_from('<9I',page,0xa80)
        need(page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+
             reserved[0x830:0xa00] and
             page[0xaa4:]==before[0xaa4:] and
             struct.unpack_from('<8I',page,0xa00)==
                 (0x314d4152,NONCE,PTR,0x80000,19,0,digest,0) and
             control==(0x31414d44,NONCE,2048,0x314e4950,bus,
                       prior_regs[1],prior_regs[3],prior_regs[5],prior_regs[7]) and
             words[:3]==(0x3145534c,NONCE,1) and
             words[3:5]==((0x4d555352,0x45505845) if external else
                           (0x544c4148,0x544c4148)) and
             words[6:]==(0,1) and
             diag[0]==diag[3]==0xc0002100 and diag[1]==0 and
             diag[4]==trace[1] and diag[7]==1 and
             trace[0]==0x4b535452 and trace[2]==1 and
             trace[9:12]==(0,1,terminal) and
             trace[18:20]==(1,1) and trace[33:35]==(1,1) and
             trace[41:44]==(terminal,0x0a010002,0x31414d44) and
             trace[68:73]==(2,0,0,0,0) and
             trace[73:76]==(LAST,0,0) and
             trace[78:83]==(0xc0723000,SRC,LAST,13000,1) and
             20<=trace[83]==trace[84]<trace[85]<=trace[1]<=300 and
             (80<=trace[85]-trace[84]<200 if external else
              trace[85]-trace[84]==200) and
             trace[86:88]==(0,1) and
             trace[94:96]==(1,1 if external else 2) and
             trace[88:91]==trace[91:94] and trace[88]!=LAST and
             trace[44:52]==(0,LAST,0,bus+2048,0,SRC+2048,0,7) and
             trace[52:55]==(0,0xc0611320,0) and
             0xf0000000<=trace[55]<=0xfffffffc and trace[55]%4==0 and
             trace[56]==0 and trace[57] in (0xc060c6ec,PTR+0x80000) and
             trace[58:60]==(0,0x3f) and
             all(x==0 for x in trace[60:68]) and
             stack[:64]==b'\xa5'*64 and stack[-64:]==b'\xa5'*64 and
             task_stack[:64]==b'\xa5'*64 and task_stack[-64:]==b'\xa5'*64,
             'complete DMA/RTEMS/context/stock channel audits')
        dma_data=(PIN_DEBUG/'data.bin').read_bytes()
        (run/'dma-data.bin').write_bytes(dma_data)
        need(dma_data==bytes(i^0xa6 for i in range(256))+
                       b'\x5a'*(PAGE-256) and
             fields(PIN_DEBUG/'status')['guard_changes']=='0',
             'host payload and guards')
        (PIN_DEBUG/'verify').write_text('verify\n')
        pin_after=fields(PIN_DEBUG/'status')
        (run/'dma-pin-after.txt').write_text((PIN_DEBUG/'status').read_text())
        need(pin_after['armed']=='1' and pin_after['verified']=='1' and
             pin_after['payload_match']=='1' and pin_after['guard_changes']=='0',
             'pin verification')
        write(0xc000e000,0xa00,before[0xa00:0xa20])
        write(0xc000e000,0xa20,before[0xa20:0xa3c])
        write(0xc000e000,0xa40,before[0xa40:0xa60])
        write(0xc000e000,0xa60,before[0xa60:0xa80])
        write(0xc000e000,0xa80,before[0xa80:0xaa4])
        need(snap(0xc000e000)==reserved[:0x820]+before[0x820:0x830]+
             reserved[0x830:],'loader page restored under grant')
        translate(0xc0000000);release('ram-admit','admit')
        write(0xc000e000,0x820,b'\xa5'*16)
        translate(0xc0000000);command('release',a.out)
        endpage=snap(0xc000e000)
        need(struct.unpack_from('<4I',endpage,0x820)==
             (0x45455246,0x16161051,PTR,0x80000),'grant release report')
        (a.out/'owner-after.bin').write_bytes(ownercheck(owner))
        write(0xc000e000,0x820,before[0x820:0x830])
        (a.out/'page-restored.bin').write_bytes(snap(0xc000e000))
        need(snap(0xc000e000)==before and
             snap(PTR+0x7e000)==stage_before,'final page/stage')
        translate(0xc0000000);release('release','release')
        (PIN_DEBUG/'release').write_text('release\n')
        subprocess.run(['rmmod','dma_pin'],check=True)
        subprocess.run(['rmmod','copy_command'],check=True)
        subprocess.run(['rmmod','digest_command'],check=True)
        save(a.out/'result.json',dict(boot_id=boot,
             image_sha256=IMAGE,firmware_sha256=FIRMWARE,
             mode='external-resume' if external else 'fallback',
             killed_pid=death['pid'],process_absent_before_recovery=True,
             full_audits=True,owner_restored=True,page_restored=True,
             stage_restored=True,terminal_ticks=trace[1],
             stop_tick=trace[83],resume_tick=trace[85],
             resume_reason=trace[95],
             channel0=[f'0x{x:08x}' for x in trace[44:52]],
             card_after=select(BDF,'accele160'),old_after=select(OLD,'dac960pg')))
        print(json.dumps(dict(terminal_ticks=trace[1],stop_tick=trace[83],
             resume_tick=trace[85],killed_pid=death['pid'],
             audits='passed',resources='released'),indent=2))
    finally:
        translate(0xc0000000);bar.close();res.close();cfg.close()

if __name__=='__main__':main()
