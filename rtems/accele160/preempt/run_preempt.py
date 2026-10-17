#!/usr/bin/env python3
"""Run bounded timer-preempted RTEMS workers through AcceleRAID RAM operation 13."""
import argparse,fcntl,hashlib,json,mmap,struct,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/lease_probe'))
from run_lease import (BDF,OLD,PAGE,DEVICE,DEBUG,FIRMWARE,HANDLER,
                       MODULES,NONCE,need,sha,fields,fnv,status,insmod,
                       done,command,release,verify_read)
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

IMAGE='514dfc5b1c8ea1a2ef114ad421f88a12f015a7669dea8af70981dfead107405f'
KERNEL='3f211bf02b85e911836259cd7f83be27b4ffb0c4e93d2aa1c80d89e669bd4f7f'
PAGES=27

def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('reserve_module','release_module','copy_module','digest_module',
              'admit_module','handler','firmware','kernel','image',
              'readback0','readback1','out'):
        p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    a=p.parse_args()
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for n,want in [('handler',HANDLER),('firmware',FIRMWARE),
                   ('kernel',KERNEL),('image',IMAGE)]:
        need(sha(getattr(a,n).read_bytes())==want,f'{n} identity')
    payload=a.image.read_bytes()
    need(len(payload)==PAGES*PAGE and
         payload[:20*PAGE]==a.kernel.read_bytes()[:20*PAGE] and
         payload[20*PAGE:]==b'\xa5'*(7*PAGE),'RTEMS image/stack layout')
    digest=fnv(payload)
    need(digest==0x91f3da52,'whole-image FNV')
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
         image_sha256=IMAGE,kernel_sha256=KERNEL,
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
        for number,mode in enumerate(('stop','timeout')):
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
            ready=False
            while time.monotonic()-began<3:
                cur=snap(0xc000e000)
                if struct.unpack_from('<I',cur,0xa50)[0]==0x59444152:
                    ready=True;break
                if status('ram-admit').get('done')=='1':break
                time.sleep(.002)
            (run/'ready-page.bin').write_bytes(cur)
            (run/'ready-status.txt').write_text(
                (DEBUG/'accele-ram-admit/status').read_text())
            need(ready and status('ram-admit').get('done')=='0',
                 'RTEMS READY missing or early completion; retain grant')
            stale_pending=None
            if mode=='stop':
                write(0xc000e000,0xa4c,struct.pack('<I',0xdeadbeef))
                time.sleep(.005)
                stale_pending=status('ram-admit').get('done')=='0'
                (run/'stale-page.bin').write_bytes(snap(0xc000e000))
                need(stale_pending,'stale STOP ended RTEMS task')
                write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))
            translate(original)
            done('ram-admit',run,0,30)
            elapsed=time.monotonic()-began
            page=snap(0xc000e000)
            (run/'page-after.bin').write_bytes(page)
            irq_stack_after=snap(ptr+21*PAGE)
            worker0_stack_after=snap(ptr+23*PAGE)
            worker1_stack_after=snap(ptr+25*PAGE)
            stack_after=snap(ptr+26*PAGE)
            (run/'irq-stack-after.bin').write_bytes(irq_stack_after)
            (run/'entry-stack-after.bin').write_bytes(stack_after)
            (run/'worker0-irq-stack-after.bin').write_bytes(worker0_stack_after)
            (run/'worker1-irq-stack-after.bin').write_bytes(worker1_stack_after)
            (run/'owner-after.bin').write_bytes(ownercheck(owned))
            need(page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+reserved[0x830:0xa00]
                 and page[0xa80:]==before[0xa80:],
                 'loader page bounds')
            flag=0x504f5453 if mode=='stop' else 0x454d4954
            need(struct.unpack_from('<8I',page,0xa00)==
                 (0x314d4152,NONCE,ptr,0x80000,PAGES,0,digest,0),
                 'manifest')
            need(struct.unpack_from('<7I',page,0xa20)==
                 (0x314e5552,NONCE,0x31454e4f,ptr,PAGES,digest,flag),
                 'RTEMS admission report')
            sidewords=struct.unpack_from('<8I',page,0xa40)
            if mode=='stop':
                need(sidewords==(0x3145534c,NONCE,1,0x504f5453,
                     0x59444152,0x214b4341,NONCE,1),'RTEMS STOP ACK')
            else:
                need(sidewords==(0x3145534c,NONCE,1,0,0x454d4954)+
                     (0xa5a5a5a5,)*3,'RTEMS timeout')
            fw,preflight,entry_after,restored,ticks,irq_sp,handoffs,cleanup=struct.unpack_from(
                '<8I',page,0xa60)
            trace=struct.unpack_from('<28I',irq_stack_after)
            need(fw==restored and preflight==0 and
                 ptr+26*PAGE<=entry_after<ptr+27*PAGE and
                 irq_sp==trace[13] and
                 ticks>=6 and cleanup==1 and handoffs>=2 and
                 irq_stack_after!=payload[21*PAGE:22*PAGE] and
                 trace[0]==0x54504d45 and trace[1]==ticks and
                 trace[2]==handoffs and trace[3]>0 and
                 trace[7]==trace[8] and trace[9]==trace[10] and
                 trace[11]==trace[12] and trace[9]>0 and trace[11]>0 and
                 ptr+22*PAGE+192<=trace[14]<ptr+24*PAGE and
                 ptr+24*PAGE+192<=trace[15]<ptr+26*PAGE and
                 trace[19]==0x10c7 and trace[20]==0x80000 and
                 trace[21]==0xaaaaaaaa and trace[22]==0 and
                 trace[23]==0 and trace[24]==0 and trace[26]==0 and
                 trace[27]==1 and
                 worker0_stack_after[-64:]==b'\xa5'*64 and
                 worker1_stack_after[-64:]==b'\xa5'*64,
                 'RTEMS preempted workers, drained continuations or timer restoration')
            if mode=='timeout':
                need(ticks>=120 and trace[6]==60,
                     'sustained autonomous preemption or finite controller deadline')
            write(0xc000e000,0xa00,before[0xa00:0xa20])
            write(0xc000e000,0xa20,before[0xa20:0xa3c])
            write(0xc000e000,0xa40,before[0xa40:0xa60])
            write(0xc000e000,0xa60,before[0xa60:0xa80])
            need(snap(0xc000e000)==
                 reserved[:0x820]+before[0x820:0x830]+reserved[0x830:],
                 'loader page restore under grant')
            translate(original);release('ram-admit','admit')
            results.append(dict(mode=mode,elapsed_ms=round(elapsed*1000,3),
                stale_pending=stale_pending,firmware_sp=f'0x{fw:08x}',
                entry_sp=f'0x{entry_after:08x}',
                restored_sp=f'0x{restored:08x}',
                irq_sp=f'0x{irq_sp:08x}',ticks=ticks,
                handoffs=handoffs,cleanup=cleanup,
                worker_trace=[f'0x{x:08x}' for x in trace],
                irq_stack_changed_bytes=sum(x!=y for x,y in
                    zip(irq_stack_after,payload[21*PAGE:22*PAGE])),
                entry_stack_pci_sample_sha256=sha(stack_after)))
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
