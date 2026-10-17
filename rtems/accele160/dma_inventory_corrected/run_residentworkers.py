#!/usr/bin/env python3
"""Run bounded post-return two-task RTEMS lease on AcceleRAID 160."""
import argparse,fcntl,hashlib,json,mmap,struct,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/lease_probe'))
from run_lease import (BDF,OLD,PAGE,DEVICE,DEBUG,FIRMWARE,HANDLER,
                       MODULES,NONCE,need,sha,fields,fnv,status,insmod,
                       done,command,release,verify_read)
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

IMAGE='07df039f173490bac8db523f667a8bbfd276c3d4f5e4f9a8834b754ab145e711'
PAGES=19

def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('reserve_module','release_module','copy_module','digest_module',
              'admit_module','handler','firmware','image',
              'readback0','readback1','out'):
        p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    a=p.parse_args()
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for n,want in [('handler',HANDLER),('firmware',FIRMWARE),('image',IMAGE)]:
        need(sha(getattr(a,n).read_bytes())==want,f'{n} identity')
    payload=a.image.read_bytes()
    need(len(payload)==PAGES*PAGE and
         payload[15*PAGE:]==b'\xa5'*(4*PAGE),'timer image/stack layout')
    digest=fnv(payload)
    need(digest==0x6255c2c7,'whole-image FNV')
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
    a.out.mkdir(parents=True,exist_ok=False)
    save(a.out/'preflight.json',dict(boot_id=boot,card=card,old=old,
         firmware_sha256=FIRMWARE,handler_sha256=HANDLER,
         image_sha256=IMAGE,
         fnv=f'0x{digest:08x}',modules=MODULES))
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
        for number,mode in enumerate(('halt','expiry')):
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
            manifest=struct.pack('<8I',0x314d4152,NONCE,ptr,0x80000,
                                 PAGES,0,digest,0)
            side=struct.pack('<4I',0x3145534c,NONCE,1,0)+b'\xa5'*16
            write(0xc000e000,0xa00,manifest)
            write(0xc000e000,0xa20,b'\xa5'*28)
            write(0xc000e000,0xa40,side)
            write(0xc000e000,0xa60,b'\xa5'*32)
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
                write(0xc000e000,0xa4c,struct.pack('<I',0xdeadbeef))
                time.sleep(.02)
                stale=snap(0xc000e000)
                (run/'stale-page.bin').write_bytes(stale)
                stale_pending=struct.unpack_from('<I',stale,0xa50)[0]==0x59444152
                need(stale_pending,'stale ENTER changed monitor state')
            write(0xc000e000,0xa4c,struct.pack('<I',0x52544e45))
            active=None
            limit=time.monotonic()+1.0
            while time.monotonic()<limit:
                current=snap(0xc000e000)
                state=struct.unpack_from('<I',current,0xa50)[0]
                if state==0x49544341:
                    active=current;break
                if state==0x45505845:break
                time.sleep(.002)
            if active is None:
                (run/'no-active-page.bin').write_bytes(current)
            need(active is not None,'ENTER not observed after callback completion; retain grant')
            (run/'active-page.bin').write_bytes(active)
            if mode=='halt':
                write(0xc000e000,0xa4c,struct.pack('<I',0xdeadbeef))
                time.sleep(.02)
                task_stale=snap(0xc000e000)
                (run/'task-stale-page.bin').write_bytes(task_stale)
                need(struct.unpack_from('<I',task_stale,0xa50)[0]==0x49544341,
                     'RTEMS task accepted stale STOP')
                write(0xc000e000,0xa4c,struct.pack('<I',0x544c4148))
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
            need(page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+reserved[0x830:0xa00]
                 and page[0xa80:]==before[0xa80:],
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
            trace=struct.unpack_from('<68I',stack_after,3072)
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
                 trace[21]==ptr+0xc520 and trace[36]==ptr+0xc690 and
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
            if mode=='expiry':need(300<=ticks<=302,'finite hardware-timer lease')
            if mode=='halt':need(20<=ticks<300 and sidewords[3]==0x544c4148,
                                 'HALT token/finite elapsed time')
            elapsed=time.monotonic()-began
            write(0xc000e000,0xa00,before[0xa00:0xa20])
            write(0xc000e000,0xa20,before[0xa20:0xa3c])
            write(0xc000e000,0xa40,before[0xa40:0xa60])
            write(0xc000e000,0xa60,before[0xa60:0xa80])
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
                worker_sp=f'0x{trace[37]:08x}',
                dma_registers=[[f'0x{v:08x}' for v in trace[44+i*8:52+i*8]]
                               for i in range(3)],
                task_sp=f'0x{trace[22]:08x}',
                task_isr_sp=f'0x{trace[26]:08x}',
                stack_changed_bytes=sum(x!=y for x,y in
                       zip(stack_after,payload[15*PAGE:16*PAGE]))))
            if number==0:insmod(a.admit_module)
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
