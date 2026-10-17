#!/usr/bin/env python3
"""Run reboot-only, retained 8 MiB RTEMS claim on AcceleRAID 160."""
import argparse,fcntl,hashlib,json,mmap,struct,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/lease_probe'))
from run_lease import (BDF,OLD,PAGE,DEVICE,DEBUG,FIRMWARE,HANDLER,
                       MODULES,NONCE,need,sha,fields,fnv,status,insmod,
                       done,command,release,verify_read)
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

IMAGE='752215d534c8c4d5998f5cdb8edb1d03929905dc480cc54bd110e47fa6f21304'
KERNEL='b94183cd5d971d66c7a39b98de8837556d450ceb2d4883e5ec9813b5c720eb40'
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
    need(digest==0x42836020,'whole-image FNV')
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
        upper_before=snap(0xc0f00000);stock_before=snap(0xc0010000)
        need(upper_before==bytes(PAGE) and stock_before!=bytes(PAGE),
             'upper/stock page preimages')
        (a.out/'upper-before.bin').write_bytes(upper_before)
        (a.out/'stock-before.bin').write_bytes(stock_before)
        sample_indices=[1+32*i for i in range(64)]+[2047]
        samples_before=b''.join(snap(0xc0800000+index*PAGE-PAGE)
                                for index in sample_indices)
        need(samples_before==bytes(len(samples_before)),
             'upper-bank odd-page samples are not zero')
        (a.out/'samples-before.bin').write_bytes(samples_before)
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
        scratch0_before=snap(0xc0732000);scratch1_before=snap(0xc0734000)
        (a.out/'scratch0-before.bin').write_bytes(scratch0_before)
        (a.out/'scratch1-before.bin').write_bytes(scratch1_before)
        stage=ptr+0x7e000;stage_before=snap(stage)
        (a.out/'stage-before.bin').write_bytes(stage_before)
        run=a.out/'persist';run.mkdir()
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
        while time.monotonic()-began<90:
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
        def marker(page,word):
            return 0x7e960160^(page*0x85ebca6b&0xffffffff)^(word*0xc2b2ae35&0xffffffff)
        def wordhash():
            h=0x811c9dc5
            for page in range(2048):
                for word in range(1024):h=((h^marker(page,word))*0x01000193)&0xffffffff
            return h
        claim_words=struct.unpack_from('<8I',cur,0xb40)
        bank=struct.unpack_from('<16I',cur,0xb00)
        need(bank[:4]==(0x314b4e42,0,53,0x800000) and
             bank[4]==bank[5]==bank[6] and bank[7:11]==(2048,0,2048,0)
             and bank[11]==0xfefecffb and bank[12:14]==(0,0) and
             bank[14]==bank[15],'full-bank proof before permanent claim')
        need(claim_words[:4]==(0x314d5241,2048,wordhash(),0) and
             claim_words[6]==0,'retained claim report')
        odd_hash=hashlib.sha256()
        for index in range(1,2048,2):
            actual=snap(0xc0800000+(index-1)*PAGE)
            expected=struct.pack('<1024I',*(marker(index,w) for w in range(1024)))
            need(actual==expected,f'upper page {index} pattern')
            odd_hash.update(actual)
        (run/'ready-page.bin').write_bytes(cur)
        first=claim_words[4]
        time.sleep(.25)
        later=snap(0xc000e000)
        latter=struct.unpack_from('<8I',later,0xb40)
        need(latter[4]>first and latter[5]==0 and latter[6]==0 and
             status('ram-admit').get('done')=='0','live independent RTEMS heartbeat')
        write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))
        began_stop=time.monotonic()
        while time.monotonic()-began_stop<20:
            page=snap(0xc000e000)
            state=struct.unpack_from('<8I',page,0xb40)
            if state[5]==0x45495551:break
            time.sleep(.01)
        (run/'quiescent-page.bin').write_bytes(page)
        (run/'admit-pending-status.txt').write_text(
            (DEBUG/'accele-ram-admit/status').read_text())
        need(state[5]==0x45495551 and state[6]==0 and
             status('ram-admit').get('done')=='0','reboot-only quiescent ownership')
        need(struct.unpack_from('<I',page,0xa54)[0]==0x214b4341,
             'STOP acknowledged')
        need(struct.unpack_from('<16I',page,0xb00)==bank,
             'full-bank proof report retained')
        need(snap(0xc0384000)[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
             'grant remains owned')
        need(select(OLD,'dac960pg')['driver'] is None,'old card bound')
        save(a.out/'result.json',dict(boot_id=boot,
             image_sha256=IMAGE,kernel_sha256=KERNEL,
             firmware_sha256=FIRMWARE,full_audits_before=True,
             arena_bytes=8*1024*1024,odd_pages_checked=1024,
             odd_pages_sha256=odd_hash.hexdigest(),
             bank_report=[f'0x{x:08x}' for x in bank],
             claim_report=[f'0x{x:08x}' for x in state],
             heartbeat_before=first,heartbeat_after=latter[4],
             release='reboot-only',grant_retained=True,
             card=select(BDF,'accele160'),old=select(OLD,'dac960pg')))
        print('retained RTEMS claimed 8 MiB; STOP quiescent; reboot required')
    finally:
        translate(original);bar.close();res.close();cfg.close()

if __name__=='__main__':main()
