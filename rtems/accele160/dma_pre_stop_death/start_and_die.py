#!/usr/bin/env python3
"""Start finite DMA and kill its host owner at DMA_BUSY before any STOP."""
import argparse,errno,fcntl,hashlib,json,mmap,os,signal,struct,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/lease_probe'))
from run_lease import (BDF,OLD,PAGE,DEVICE,DEBUG,FIRMWARE,HANDLER,
                       MODULES,NONCE,need,sha,fields,fnv,status,insmod,
                       done,command,release,verify_read)
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

IMAGE='0477635a365a3ff40ca7b35759860884ec0aef7663ce70c72842c23dbe28427c'
PIN='1ef0b6c44c8dceb2c1b820b61ac17a1d3096c6be87dc3978cf2dcb296fe89690'
PIN_DEBUG=Path('/sys/kernel/debug/accele-dma-pin')
PAGES=19

def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def save_durable(path,obj):
    with path.open('w') as f:
        json.dump(obj,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('reserve_module','release_module','copy_module','digest_module',
              'admit_module','handler','firmware','image',
              'readback0','readback1','out','dma_module'):
        p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    p.add_argument('--mode',choices=('expiry',),required=True)
    p.add_argument('--prior-run',type=Path,required=True)
    p.add_argument('--die-at-active',action='store_true',required=True)
    a=p.parse_args()
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for n,want in [('handler',HANDLER),('firmware',FIRMWARE),('image',IMAGE)]:
        need(sha(getattr(a,n).read_bytes())==want,f'{n} identity')
    payload=a.image.read_bytes()
    need(len(payload)==PAGES*PAGE and
         payload[15*PAGE:]==b'\xa5'*(4*PAGE),'timer image/stack layout')
    digest=fnv(payload)
    need(digest==0xc161927d,'whole-image FNV')
    need(sha(a.dma_module.read_bytes())==PIN and
         not Path('/sys/module/dma_pin').exists() and not PIN_DEBUG.exists(),
         'DMA pin module preflight')
    for n,want in MODULES.items():
        path=getattr(a,n+'_module')
        debug='ram-admit' if n=='admit' else n
        need(sha(path.read_bytes())==want and
             not Path('/sys/module',n+'_command').exists() and
             not (DEBUG/f'accele-{debug}').exists(),f'{n} module preflight')
    card=select(BDF,'accele160',driver='myrsread')
    old=select(OLD,'dac960pg')
    need(old['driver'] is None,'old card bound')
    need(not list(DEVICE.glob('host*/target*/*/block/*')),'block device')
    host,=DEVICE.glob('host*/scsi_host/host*')
    need((host/'stock_descriptor').read_text().startswith('state=0 '),
         'stock descriptor active')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for rd in (a.readback0,a.readback1):verify_read(rd,boot,card,old)
    prior_result=json.loads((a.prior_run/'result.json').read_text())
    prior_pre=json.loads((a.prior_run/'preflight.json').read_text())
    prior_mode=(prior_result['runs'][0]['mode'] if 'runs' in prior_result
                else prior_result.get('mode','halt'))
    need(prior_mode in ('halt','expiry'),'prior terminal mode')
    prior_trace=struct.unpack_from('<68I',
             (a.prior_run/prior_mode/'irq-stack-after.bin').read_bytes(),3072)
    prior_regs=prior_trace[44:52]
    need(prior_pre['boot_id']==prior_result['boot_id']==boot and
         prior_pre['card']==prior_result['card_after']==card and
         prior_pre['old']==prior_result['old_after']==old and
         prior_result['owner_restored'] and prior_result['page_restored'] and
         prior_result['stage_restored'] and prior_result['full_audits'] and
         (prior_result['runs'][0]['mode']==prior_mode if 'runs' in prior_result
          else prior_result.get('process_absent_before_recovery') and
               prior_result.get('channel0')==
               [f'0x{x:08x}' for x in prior_regs]) and
         prior_trace[43]==0x31414d44 and
         (prior_regs==(0,)*8 or
          (prior_regs[0]==0 and prior_regs[1]>=0xc0710000 and
           prior_regs[1]<0xc0790000 and prior_regs[2]==0 and
           prior_regs[3]>=0xf0000000 and prior_regs[4]==0 and
           prior_regs[5]>=0xc0710000 and prior_regs[5]<0xc0790000 and
           prior_regs[6:8]==(0,7))),
         'prior audited channel-0 state')
    a.out.mkdir(parents=True,exist_ok=False)
    save(a.out/'preflight.json',dict(boot_id=boot,card=card,old=old,
         firmware_sha256=FIRMWARE,handler_sha256=HANDLER,
         image_sha256=IMAGE,
         fnv=f'0x{digest:08x}',modules=MODULES,
         prior_channel0=[f'0x{x:08x}' for x in prior_regs],
         prior_run=str(a.prior_run)))
    cfg=(DEVICE/'config').open('r+b',buffering=0)
    res=(DEVICE/'resource0').open('r+b',buffering=0)
    bar=mmap.mmap(res.fileno(),2*PAGE)
    cfg.seek(0x44);original=struct.unpack('<I',cfg.read(4))[0]
    need(original==0xc0000000,'PIATVR unexpected')
    def translate(addr):
        cfg.seek(0x44);cfg.write(struct.pack('<I',addr));cfg.seek(0x44)
        need(struct.unpack('<I',cfg.read(4))[0]==addr,'PIATVR readback')
    def snap(addr):
        translate(addr);return bytes(bar[PAGE:2*PAGE])
    def write(addr,off,data):
        translate(addr);bar[PAGE+off:PAGE+off+len(data)]=data
        need(bytes(bar[PAGE+off:PAGE+off+len(data)])==data,'PCI writeback')
    def ownercheck(base):
        got=snap(0xc0384000)
        need(got[0x2a0:0xaa0]==base[0x2a0:0xaa0],
             'allocator count/owner changed')
        return got
    try:
        before=snap(0xc000e000);owner=snap(0xc0384000)
        (a.out/'page-before.bin').write_bytes(before)
        (a.out/'owner-before.bin').write_bytes(owner)
        tail=a.handler.read_bytes()[0xf000-0xe1d8:]
        need(before==tail+b'\xff'*(PAGE-len(tail)),'exact handler tail/page')
        for n in MODULES:insmod(getattr(a,n+'_module'))
        write(0xc000e000,0x820,b'\xa5'*16)
        translate(original);command('reserve',a.out)
        reserved=snap(0xc000e000)
        (a.out/'page-reserved.bin').write_bytes(reserved)
        ptr=struct.unpack_from('<I',reserved,0x828)[0]
        need(ptr==0xc0710000 and struct.unpack_from('<4I',reserved,0x840)==
             (0x56525352,ptr,0x80000,0x96016004),'grant')
        owned=snap(0xc0384000)
        (a.out/'owner-reserved.bin').write_bytes(owned)
        first=(ptr-0xc0000000)//0x8000
        for i in range(256):
            bc,bo=(struct.unpack_from('<I',owner,0x2a0+i*4)[0],
                   struct.unpack_from('<I',owner,0x6a0+i*4)[0])
            rc,ro=(struct.unpack_from('<I',owned,0x2a0+i*4)[0],
                   struct.unpack_from('<I',owned,0x6a0+i*4)[0])
            need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo)),
                 'owner grant metadata')
            if first<=i<first+16:need((bc,bo)==(0,0),'grant overlap')
        write(0xc000e000,0x820,before[0x820:0x830])
        translate(original);release('reserve','reserve')
        stage=ptr+0x7e000;stage_before=snap(stage)
        (a.out/'stage-before.bin').write_bytes(stage_before)
        results=[]
        for number,mode in enumerate((a.mode,)):
            run=a.out/mode;run.mkdir()
            copy_receipts=[]
            for index in range(PAGES):
                page=payload[index*PAGE:(index+1)*PAGE]
                write(stage,0,page)
                need(snap(stage)==page,'staging readback')
                control=struct.pack('<4I',0x59504f43,0x16161061,index,fnv(page))
                write(0xc000e000,0x860,control)
                write(0xc000e000,0x820,b'\xa5'*16)
                translate(original);command('copy',run)
                cp=snap(0xc000e000)
                need(struct.unpack_from('<4I',cp,0x820)==
                     (0x59504f43,0x16161061,index,fnv(page)),
                     'copy report')
                if index&1:
                    need(snap(ptr+index*PAGE)==page,'odd target readback')
                ownercheck(owned)
                copy_receipts.append(dict(index=index,sha256=sha(page),
                                          fnv=f'0x{fnv(page):08x}'))
                write(0xc000e000,0x860,before[0x860:0x870])
                write(0xc000e000,0x820,before[0x820:0x830])
                write(stage,0,stage_before)
                need(snap(stage)==stage_before,'stage restore')
                translate(original);release('copy','copy')
                insmod(a.copy_module)
            save(run/'copy-receipts.json',copy_receipts)
            control=struct.pack('<4I',0x48534148,0x16161071,PAGES,digest)
            write(0xc000e000,0x870,control)
            write(0xc000e000,0x830,b'\xa5'*16)
            translate(original);command('digest',run)
            dp=snap(0xc000e000)
            (run/'digest-page.bin').write_bytes(dp)
            need(struct.unpack_from('<4I',dp,0x830)==
                 (0x48534148,0x16161071,PAGES,digest),'whole card digest')
            write(0xc000e000,0x870,before[0x870:0x880])
            write(0xc000e000,0x830,before[0x830:0x840])
            translate(original);release('digest','digest')
            insmod(a.digest_module)
            subprocess.run(['insmod',str(a.dma_module)],check=True)
            pin=fields(PIN_DEBUG/'status')
            bus=int(pin['bus_addr'],16)
            need(pin['bdf']==BDF and pin['length']=='256' and
                 pin['armed']=='0' and pin['verified']=='0' and
                 pin['guard_changes']=='0' and pin['payload_match']=='0' and
                 bus>=0x10000 and bus<=0xfffffe00 and bus%32==0,
                 'pinned host DMA target')
            (run/'dma-pin-before.txt').write_text((PIN_DEBUG/'status').read_text())
            (PIN_DEBUG/'arm').write_text('arm\n')
            dma_control=struct.pack('<9I',0x31414d44,NONCE,2048,0x314e4950,bus,
                                    prior_regs[1],prior_regs[3],prior_regs[5],
                                    prior_regs[7])
            need(struct.unpack_from('<4I',dma_control,20)==
                 (prior_regs[1],prior_regs[3],prior_regs[5],prior_regs[7]),
                 'exact channel-0 prior-state encoding')
            manifest=struct.pack('<8I',0x314d4152,NONCE,ptr,0x80000,
                                 PAGES,0,digest,0)
            side=struct.pack('<4I',0x3145534c,NONCE,1,0)+b'\xa5'*16
            write(0xc000e000,0xa00,manifest)
            write(0xc000e000,0xa20,b'\xa5'*28)
            write(0xc000e000,0xa40,side)
            write(0xc000e000,0xa60,b'\xa5'*32)
            write(0xc000e000,0xa80,dma_control)
            translate(original)
            need(status('ram-admit').get('started')=='0','admit started')
            (DEBUG/'accele-ram-admit/start').write_text('probe\n')
            began=time.monotonic()
            done('ram-admit',run,0,5)
            callback_ms=(time.monotonic()-began)*1000
            armed_page=snap(0xc000e000)
            (run/'callback-returned-page.bin').write_bytes(armed_page)
            need(struct.unpack_from('<7I',armed_page,0xa20)==
                 (0x314e5552,NONCE,0x31454e4f,ptr,PAGES,digest,0x4d524141) and
                 struct.unpack_from('<5I',armed_page,0xa40)==
                 (0x3145534c,NONCE,1,0,0x59444152),
                 'op13 did not return with monitor armed; retain grant')
            # No firmware command while the monitor owns timer 1. All actions
            # below are direct host PCI writes/reads of the saved loader page.
            stale_pending=None
            if mode=='halt':
                stale_pending=True  # previous finite gate already proved stale ENTER
            write(0xc000e000,0xa4c,struct.pack('<I',0x52544e45))
            active=None
            limit=time.monotonic()+1.0
            while time.monotonic()<limit:
                current=snap(0xc000e000)
                state=struct.unpack_from('<I',current,0xa50)[0]
                if state==0x59535542:
                    active=current;break
                if state==0x45505845:break
                time.sleep(.002)
            if active is None:
                (run/'no-active-page.bin').write_bytes(current)
            need(active is not None,'DMA_BUSY not observed after callback completion; retain grant')
            (run/'active-page.bin').write_bytes(active)
            save_durable(a.out/'death-intent.json',dict(pid=os.getpid(),
                 boot_id=boot,image_sha256=IMAGE,
                 pin_status=fields(PIN_DEBUG/'status'),
                 active_page_sha256=sha(active),
                 state='SIGKILL immediately after DMA_BUSY; no STOP sent'))
            os.kill(os.getpid(),signal.SIGKILL)
            raise RuntimeError('SIGKILL unexpectedly returned')
            if mode=='halt':
                write(0xc000e000,0xa4c,struct.pack('<I',0x544c4148))
            held=None
            limit=time.monotonic()+1.0
            while time.monotonic()<limit:
                current=snap(0xc000e000)
                if struct.unpack_from('<I',current,0xa50)[0]==0x444c4548:
                    held=current;break
                time.sleep(.002)
            need(held is not None,'DMA_HELD not observed; retain pin/grant')
            (run/'held-page.bin').write_bytes(held)
            (run/'held-owner.bin').write_bytes(ownercheck(owned))
            (run/'held-pin.txt').write_text((PIN_DEBUG/'status').read_text())
            held_pin=fields(PIN_DEBUG/'status')
            need(held_pin['armed']=='1' and held_pin['verified']=='0' and
                 held_pin['released']=='0' and held_pin['guard_changes']=='0',
                 'pinned allocation during hold')
            deadline_start=time.monotonic()
            time.sleep(.15)
            deadline_ms=(time.monotonic()-deadline_start)*1000
            timed_out=snap(0xc000e000)
            (run/'host-timeout-page.bin').write_bytes(timed_out)
            need(struct.unpack_from('<I',timed_out,0xa50)[0]==0x444c4548 and
                 150<=deadline_ms<500,
                 'host wait deadline crossed while DMA held')
            denied=0
            try:
                (PIN_DEBUG/'release').write_text('release\n')
            except OSError as exc:
                denied=exc.errno
            need(denied==errno.EBUSY,'premature pin release must be denied')
            (run/'release-denied.json').write_text(json.dumps(
                dict(errno=denied,deadline_ms=round(deadline_ms,3)),indent=2)+'\n')
            after_denial=fields(PIN_DEBUG/'status')
            need(all(after_denial[k]==held_pin[k] for k in
                     ('bdf','bus_addr','length','armed','verified',
                      'released','guard_changes')) and
                 ownercheck(owned)==(run/'held-owner.bin').read_bytes(),
                 'pin and grant retained after timeout/release denial')
            terminal=0x544c4148 if mode=='halt' else 0x45505845
            finished=None
            limit=time.monotonic()+6.0
            while time.monotonic()<limit:
                current=snap(0xc000e000)
                if struct.unpack_from('<I',current,0xa50)[0]==terminal:
                    finished=current;break
                time.sleep(.002)
            need(finished is not None,'callback-free monitor not terminal; retain grant')
            # Observe a quiet interval after the ISR publishes terminal state;
            # only then read stack evidence or submit any firmware command.
            time.sleep(.02)
            page=snap(0xc000e000)
            time.sleep(.02)
            need(page==snap(0xc000e000),'terminal state changed after quiet interval')
            (run/'page-after.bin').write_bytes(page)
            stack_after=snap(ptr+15*PAGE)
            (run/'irq-stack-after.bin').write_bytes(stack_after)
            (run/'owner-after.bin').write_bytes(ownercheck(owned))
            expected=reserved[:0x820]+before[0x820:0x830]+reserved[0x830:]
            need(page[:0xa00]==expected[:0xa00] and
                 page[0xa80:0xaa4]==dma_control and
                 page[0xaa4:]==expected[0xaa4:],
                 'loader page bounds')
            need(struct.unpack_from('<8I',page,0xa00)==
                 (0x314d4152,NONCE,ptr,0x80000,PAGES,0,digest,0),
                 'manifest')
            need(struct.unpack_from('<7I',page,0xa20)==
                 (0x314e5552,NONCE,0x31454e4f,ptr,PAGES,digest,0x4d524141),
                 'asynchronous arm report')
            sidewords=struct.unpack_from('<8I',page,0xa40)
            fw,preflight,entry_after,restored,ticks,irq_sp,progress_diag,restore_ok=struct.unpack_from(
                '<8I',page,0xa60)
            trace=struct.unpack_from('<95I',stack_after,3072)
            entries=trace[2]
            task_stack_after=snap(ptr+17*PAGE)
            (run/'task-irq-stack-after.bin').write_bytes(task_stack_after)
            need(sidewords[0:3]==(0x3145534c,NONCE,1) and
                 sidewords[4]==terminal and sidewords[5]==trace[4] and
                 sidewords[6]==0 and sidewords[7]==1 and
                 fw==restored==0xc0002100 and
                 ptr+18*PAGE<=entry_after<ptr+19*PAGE and
                 preflight==0 and ptr+15*PAGE+192<=irq_sp<ptr+16*PAGE and
                 entries==1 and progress_diag==trace[20] and restore_ok==1 and
                 trace[0]==0x4b535452 and trace[1]==ticks and
                 trace[2]==entries and trace[3]<ticks and
                 0xc0000100<=trace[4]<ptr and
                 (trace[5]&0x1f0000)==0 and
                 trace[7]==0x12 and trace[8]==irq_sp and
                 trace[9]==0 and trace[10]==1 and trace[11]==terminal and
                 trace[12]==((trace[14]&~0x1f0000)|(trace[13]&0x1f0000)) and
                 trace[15]==1 and trace[16]==20 and trace[17]==1 and
                 trace[18]==1 and trace[19]==1 and trace[20]>0 and
                 ptr<=trace[21]<ptr+15*PAGE and
                 trace[23]<=trace[22]<trace[24] and trace[25]>0 and
                 ptr+17*PAGE+192<=trace[26]<ptr+18*PAGE and
                 trace[27]==ticks and trace[28]==1 and
                 trace[29]==0 and trace[30]==0 and trace[32]==0 and
                 trace[31]==terminal and
                 trace[33:35]==(1,1) and trace[35]>0 and
                 ptr<=trace[21]<ptr+15*PAGE and ptr<=trace[36]<ptr+15*PAGE and
                 trace[38]<=trace[37]<trace[39] and
                 trace[40]>0 and trace[40]<=trace[25] and
                 trace[41]==terminal and trace[42]==0x0a010002 and
                 trace[36]!=trace[21] and
                 task_stack_after[:64]==b'\xa5'*64 and
                 task_stack_after[-64:]==b'\xa5'*64 and
                 stack_after[:64]==b'\xa5'*64 and
                 stack_after[-64:]==b'\xa5'*64 and
                 trace[43]==0x31414d44,
                 'callback-free ISR/stack/context/restoration')
            need(trace[68:73]==(2,0,0,0,0) and
                 trace[73]==trace[80] and trace[74]==0 and trace[75]==0 and
                 trace[76]>0 and trace[77]==bus and
                 trace[78]==0xc0723000 and trace[78]%32==0 and
                 trace[79]==0xc0789000 and
                 trace[44]==0 and trace[45]==trace[80] and
                 trace[46]==0 and trace[47]==bus+2048 and
                 trace[48]==0 and trace[49]==0xc0789800 and
                 trace[50]==0 and
                 trace[51]==7 and
                 trace[52:55]==(0,0xc0611320,0) and
                 trace[56:60]==(0,0xc060c6ec,0,0x3f) and
                 all(x==0 for x in trace[60:68]) and
                 trace[80]==0xc0723000+(13000-1)*32 and
                 trace[81]==13000 and trace[82]==1 and
                 20<=trace[83]==trace[84]<trace[85]<ticks and
                 80<=trace[85]-trace[84]<=82 and
                 trace[86:88]==(0,1) and trace[94]==1 and
                 trace[88:91]==trace[91:94] and
                 trace[88]!=trace[80],
                 'DMA suspend, stable hold, resume and final drain')
            dma_data=(PIN_DEBUG/'data.bin').read_bytes()
            (run/'dma-data.bin').write_bytes(dma_data)
            need(len(dma_data)==PAGE and
                 dma_data[:256]==bytes(i^0xa6 for i in range(256)) and
                 dma_data[256:]==b'\x5a'*(PAGE-256),
                 'pinned host payload')
            (PIN_DEBUG/'verify').write_text('verify\n')
            pin_after=fields(PIN_DEBUG/'status')
            (run/'dma-pin-after.txt').write_text((PIN_DEBUG/'status').read_text())
            need(pin_after['verified']=='1' and pin_after['guard_changes']=='0' and
                 pin_after['payload_match']=='1','DMA host guard/verification')
            if mode=='expiry':need(300<=ticks<=302,'finite hardware-timer lease')
            if mode=='halt':need(20<=ticks<300 and sidewords[3]==0x544c4148,
                                 'HALT token/finite elapsed time')
            elapsed=time.monotonic()-began
            write(0xc000e000,0xa00,before[0xa00:0xa20])
            write(0xc000e000,0xa20,before[0xa20:0xa3c])
            write(0xc000e000,0xa40,before[0xa40:0xa60])
            write(0xc000e000,0xa60,before[0xa60:0xa80])
            write(0xc000e000,0xa80,before[0xa80:0xaa4])
            need(snap(0xc000e000)==
                 reserved[:0x820]+before[0x820:0x830]+reserved[0x830:],
                 'loader page restore under grant')
            translate(original);release('ram-admit','admit')
            results.append(dict(mode=mode,elapsed_ms=round(elapsed*1000,3),
                callback_ms=round(callback_ms,3),stale_pending=stale_pending,
                firmware_sp=f'0x{fw:08x}',entry_sp=f'0x{entry_after:08x}',
                restored_sp=f'0x{restored:08x}',irq_sp=f'0x{irq_sp:08x}',
                ticks=ticks,entries=entries,restore_ok=restore_ok,
                frame=f'0x{trace[4]:08x}',frame_pc=f'0x{trace[5]:08x}',
                frame_vector=f'0x{trace[7]:08x}',
                rtems_clock_tick=trace[16],rtems_callback_after_enter=trace[17],
                task_progress=trace[20],task_irq_count=trace[25],
                worker_progress=trace[35],worker_irq_count=trace[40],
                dma_bus=f'0x{bus:08x}',dma_polls=trace[76],stop_seen_active=trace[82],
                stop_seen_tick=trace[83],chain_descriptors=trace[81],
                suspend_tick=trace[84],resume_tick=trace[85],
                host_timeout_ms=round(deadline_ms,3),
                premature_release_errno=denied,
                hold_dar=f'0x{trace[88]:08x}',hold_bcr=trace[89],
                hold_ndar=f'0x{trace[90]:08x}',
                worker_sp=f'0x{trace[37]:08x}',
                dma_registers=[[f'0x{v:08x}' for v in trace[44+i*8:52+i*8]]
                               for i in range(3)],
                task_sp=f'0x{trace[22]:08x}',
                task_isr_sp=f'0x{trace[26]:08x}',
                stack_changed_bytes=sum(x!=y for x,y in
                       zip(stack_after,payload[15*PAGE:16*PAGE]))))
        write(0xc000e000,0x820,b'\xa5'*16)
        translate(original);command('release',a.out)
        endpage=snap(0xc000e000)
        need(struct.unpack_from('<4I',endpage,0x820)==
             (0x45455246,0x16161051,ptr,0x80000),'grant release')
        (a.out/'owner-after.bin').write_bytes(ownercheck(owner))
        write(0xc000e000,0x820,before[0x820:0x830])
        restored_page=snap(0xc000e000)
        (a.out/'page-restored.bin').write_bytes(restored_page)
        need(restored_page==before and snap(stage)==stage_before,
             'final page/stage restore')
        translate(original);release('release','release')
        (PIN_DEBUG/'release').write_text('release\n')
        subprocess.run(['rmmod','dma_pin'],check=True)
        subprocess.run(['rmmod','copy_command'],check=True)
        subprocess.run(['rmmod','digest_command'],check=True)
        save(a.out/'result.json',dict(boot_id=boot,runs=results,
             firmware_sha256=FIRMWARE,image_sha256=IMAGE,
             full_audits=True,owner_restored=True,page_restored=True,
             stage_restored=True,card_after=select(BDF,'accele160'),
             old_after=select(OLD,'dac960pg')))
        print(json.dumps(results,indent=2))
    finally:
        translate(original);bar.close();res.close();cfg.close()

if __name__=='__main__':main()
