#!/usr/bin/env python3
"""Run Doom image admission and transport on retained RTEMS on AcceleRAID 160."""
import argparse,fcntl,hashlib,json,mmap,struct,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/lease_probe'))
from run_lease import (BDF,OLD,PAGE,DEVICE,DEBUG,FIRMWARE,HANDLER,
                       MODULES,NONCE,need,sha,fields,fnv,status,insmod,
                       done,command,release,verify_read)
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

IMAGE='6b625a81c60a084c1cf3d0ba61d1dcbaa7dac23832333a3fa0eaeb8a03f80863'
KERNEL='faafdf8c98d1e4e38cacaff1a869ff111ff6ba558a6ca433e0c6940d88fa7015'
EXPECTED_FNV=0x3a62a5d7
PAGES=27

def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('reserve_module','release_module','copy_module','digest_module',
              'admit_module','handler','firmware','kernel','image',
              'readback0','readback1','template','relocations','wad','out'):
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
    need(digest==EXPECTED_FNV,'whole-image FNV')
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
        def pattern(index,word):
            return 0x7e960160^(index*0x85ebca6b&0xffffffff)^(word*0xc2b2ae35&0xffffffff)
        upper_pattern=struct.pack('<1024I',*(pattern(1793,w) for w in range(1024)))
        need(upper_before==upper_pattern and stock_before!=bytes(PAGE),
             'retained-pattern/stock page preimages')
        (a.out/'upper-before.bin').write_bytes(upper_before)
        (a.out/'stock-before.bin').write_bytes(stock_before)
        sample_indices=[1+32*i for i in range(64)]+[2047]
        samples_before=b''.join(snap(0xc0800000+index*PAGE-PAGE)
                                for index in sample_indices)
        for pos,index in enumerate(sample_indices):
            if index>=16:
                expected=struct.pack('<1024I',*(pattern(index,w) for w in range(1024)))
                need(samples_before[pos*PAGE:(pos+1)*PAGE]==expected,
                     f'upper-bank preflight page {index}')
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
        bank=struct.unpack_from('<16I',cur,0xb00)
        claim=struct.unpack_from('<16I',cur,0xb40)
        bridge_words=struct.unpack_from('<20I',cur,0xb80)
        need(bank[0:2]==(0x314b4e42,0) and bank[2]>=53 and bank[3]==0x800000 and
             bank[4]==bank[5]==bank[6] and bank[7:11]==(2048,0,2048,0)
             and bank[11]!=0 and bank[12:14]==(0,0) and
             bank[14]==bank[15], 'full-bank proof')
        need(claim[:3]==(0x314d5241,2048,0x833aedc5) and claim[3]==0 and
             claim[6]==0 and claim[10:13]==(900000,6291456,65536) and
             claim[7]>=0xc0800000 and claim[9]<0xc1000000 and
             claim[13:16]==(0x101,0x102,0x103), 'guarded arena allocations')
        need(bridge_words[6:8]==(0x31475242,0x161610e1), 'bridge identity')
        # The three pinned allocations replace the initial page pattern. Sample
        # the untouched upper tail and verify the full pre-claim bank report.
        for index in (1793,1857,1919,2047):
            expected=struct.pack('<1024I',*(pattern(index,w) for w in range(1024)))
            need(snap(0xc0800000+(index-1)*PAGE)==expected,
                 f'untouched upper page {index}')
        template=a.template.read_bytes();relocs=a.relocations.read_bytes()
        wad=a.wad.read_bytes()
        need(sha(template)=='9f2472c900bb724e7a69b2490e083c4c633520e1d525623398db2e36f2c1e173'
             and len(template)==431864,'exact Doom template')
        need(sha(relocs)=='4a0408886fe0a840b866219b62c0c1d19c7b6b6dcbc61574155fe88f49ba1a94'
             and len(relocs)==53472,'exact relocations')
        need(sha(wad)=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
             and sha(wad[:512])=='93bd1ddcfc43fbf233207876f5cfcbaef4cf4e64a1093efa47be9517d93214bd',
             'exact Freedoom WAD')
        admission=template+bytes(814320-len(template))+relocs
        need(len(admission)==867792,'admission geometry')
        seq=0;receipts=[]
        def transact(op,offset=0,data=b'',expected_status=0):
            nonlocal seq
            n=len(data)
            if data:write(0xc078a000,0,data)
            seq+=1
            descriptor=struct.pack('<5I',op,offset,n,fnv(data),0x161610e1)
            write(0xc000e000,0xb84,descriptor)
            write(0xc000e000,0xb80,struct.pack('<I',seq))
            started=time.monotonic()
            while time.monotonic()-started<90:
                page=snap(0xc000e000)
                words=struct.unpack_from('<20I',page,0xb80)
                if words[8]==seq:break
                need(status('ram-admit').get('done')=='0','retained callback escaped')
                time.sleep(.005)
            else:raise RuntimeError(f'bridge timeout op={op} seq={seq}')
            need(words[9]==expected_status,
                 f'bridge op={op} seq={seq} status={words[9]} wanted={expected_status}')
            need(words[17]==1,'arena guard validation')
            receipts.append(dict(seq=seq,op=op,offset=offset,n=n,
                                 status=words[9],value=words[10]))
            return words
        # Rejected admission must leave the image unadmitted.
        words=transact(4,expected_status=1)
        need(words[12]==0 and words[11]==0,'premature admission rejected')
        for off in range(0,len(admission),PAGE):
            part=admission[off:off+PAGE]
            words=transact(1,off,part)
            need(words[10]==off+len(part) and words[11]==off+len(part),
                 f'upload progress {off}')
        words=transact(4)
        need(words[12]==1 and words[14]==claim[7]+355776 and
             words[15]==len(admission),'Doom engine relocated/admitted')
        invalid=bytearray(wad[:512]);invalid[0]^=1
        words=transact(2,0,invalid,expected_status=7)
        need(words[13]==0,'bad WAD rejected')
        words=transact(2,0,wad[:512])
        need(words[13]==1 and words[10]==struct.unpack_from('<I',wad,4)[0],
             'WAD header admitted')
        pages=[]
        for index in range(16):
            words=transact(3,index,bytes(PAGE))
            out=snap(0xc078c000)
            need(fnv(out)==words[10],f'frame page {index} receipt')
            pages.append(out)
        frame=b''.join(pages)
        expected=bytes((((x>>3)^(y>>3)^wad[(x+y)&511])&255)
                       for y in range(200) for x in range(320))+bytes(1536)
        need(frame==expected and fnv(frame)==words[16],
             'independent diagnostic framebuffer oracle')
        (run/'frame.bin').write_bytes(frame)
        (run/'frame.pgm').write_bytes(b'P5\n320 200\n255\n'+frame[:64000])
        save(run/'bridge-receipts.json',receipts)
        page=snap(0xc000e000)
        (run/'prestop-page.bin').write_bytes(page)
        first=claim[4]
        time.sleep(.25)
        later=snap(0xc000e000)
        heart=struct.unpack_from('<16I',later,0xb40)
        need(heart[4]>first and heart[5]==0 and heart[6]==0 and
             status('ram-admit').get('done')=='0','live RTEMS heartbeat')
        write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))
        started=time.monotonic()
        while time.monotonic()-started<20:
            page=snap(0xc000e000)
            state=struct.unpack_from('<16I',page,0xb40)
            if state[5]==0x45495551:break
            time.sleep(.01)
        (run/'quiescent-page.bin').write_bytes(page)
        (run/'admit-pending-status.txt').write_text(
            (DEBUG/'accele-ram-admit/status').read_text())
        need(state[5]==0x45495551 and state[6]==0 and
             status('ram-admit').get('done')=='0' and
             struct.unpack_from('<I',page,0xa54)[0]==0x214b4341,
             'reboot-only quiescent ownership')
        need(struct.unpack_from('<16I',page,0xb00)==bank,
             'full-bank audit retained')
        need(snap(0xc0384000)[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
             'grant ownership retained')
        need(select(OLD,'dac960pg')['driver'] is None,'old card untouched')
        save(a.out/'result.json',dict(boot_id=boot,image_sha256=IMAGE,
            kernel_sha256=KERNEL,firmware_sha256=FIRMWARE,
            full_audits_before=True,bank_report=[f'0x{x:08x}' for x in bank],
            claim_report=[f'0x{x:08x}' for x in state],
            bridge_report=[f'0x{x:08x}' for x in struct.unpack_from('<20I',page,0xb80)],
            upload_bytes=len(admission),upload_commands=sum(x['op']==1 for x in receipts),
            frame_sha256=sha(frame),frame_fnv=f'0x{fnv(frame):08x}',
            heartbeat_before=first,heartbeat_after=heart[4],
            release='reboot-only',grant_retained=True,
            card=select(BDF,'accele160'),old=select(OLD,'dac960pg')))
        print('Doom image admitted; WAD header and diagnostic frame round-trip passed; STOP quiescent')
    finally:
        translate(original);bar.close();res.close();cfg.close()

if __name__=='__main__':main()
