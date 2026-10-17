#!/usr/bin/env python3
"""Run retained RTEMS Doom admission and a bounded real-frame test."""
import argparse,fcntl,hashlib,json,mmap,struct,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/lease_probe'))
from run_lease import (BDF,OLD,PAGE,DEVICE,DEBUG,FIRMWARE,HANDLER,
                       MODULES,NONCE,need,sha,fields,fnv,status,insmod,
                       done,command,release,verify_read)
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

IMAGE='957e49dc912153ddc0f80f3f22e1276df20e023c3e6ae427efe1b6c96778cdde'
KERNEL='9b9a848dc099a2d43db1752561caaf7320b925988a2313a502209f54c231d88e'
EXPECTED_FNV=0x6fa5dc25
PAGES=29

def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('reserve_module','release_module','copy_module','digest_module',
              'admit_module','handler','firmware','kernel','image',
              'readback0','readback1','template','relocations','wad','out'):
        p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    p.add_argument('--frames',type=int,choices=(1,32),default=1)
    p.add_argument('--fps-manifest',type=Path)
    p.add_argument('--startup-oracle',type=Path)
    a=p.parse_args()
    if a.frames==32:
        need(a.fps_manifest is not None and a.startup_oracle is not None,
             'FPS manifest and native startup oracle required')
        fps_manifest=json.loads(a.fps_manifest.read_text())
        need(fps_manifest['frames']==32 and
             fps_manifest['source_sha256']==sha(Path(__file__).with_name('app.c').read_bytes()),
             'FPS source/manifest identity')
        kernel_sha=fps_manifest['kernel_sha256']
        image_sha=fps_manifest['image_sha256']
        image_fnv=int(fps_manifest['image_fnv'],16)
        oracle_data=a.startup_oracle.read_bytes()
        need(len(oracle_data)==5043*8,'native startup oracle geometry')
        startup_oracle=list(struct.iter_unpack('<II',oracle_data))
    else:
        need(a.fps_manifest is None and a.startup_oracle is None,
             'first-frame run must omit FPS inputs')
        kernel_sha=KERNEL;image_sha=IMAGE;image_fnv=EXPECTED_FNV
        startup_oracle=None
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for n,want in [('handler',HANDLER),('firmware',FIRMWARE),
                   ('kernel',kernel_sha),('image',image_sha)]:
        need(sha(getattr(a,n).read_bytes())==want,f'{n} identity')
    payload=a.image.read_bytes()
    need(len(payload)==PAGES*PAGE and
         payload[:20*PAGE]==a.kernel.read_bytes()[:20*PAGE] and
         payload[20*PAGE:]==b'\xa5'*(9*PAGE),'RTEMS image/stack layout')
    digest=fnv(payload)
    need(digest==image_fnv,'whole-image FNV')
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
         image_sha256=image_sha,kernel_sha256=kernel_sha,
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
        need(stock_before!=bytes(PAGE),'stock page preimage')
        (a.out/'upper-before.bin').write_bytes(upper_before)
        (a.out/'stock-before.bin').write_bytes(stock_before)
        sample_indices=[1+32*i for i in range(64)]+[2047]
        samples_before=b''.join(snap(0xc0800000+index*PAGE-PAGE)
                                for index in sample_indices)
        # Prior admitted images and guarded allocations legitimately survive a
        # reset. Check stability without assuming their preimage is a pattern.
        odd_pages=range(1,2048,2)
        odd_first=b''.join(snap(0xc0800000+(index-1)*PAGE)
                           for index in odd_pages)
        odd_second=b''.join(snap(0xc0800000+(index-1)*PAGE)
                            for index in odd_pages)
        need(odd_first==odd_second,'upper bank changed during preflight')
        save(a.out/'bank-preflight.json',dict(
            odd_pages=len(odd_pages),bytes=len(odd_first),
            first_sha256=sha(odd_first),second_sha256=sha(odd_second),
            first_page_sha256=sha(odd_first[:PAGE]),
            upper_sample_sha256=sha(upper_before),
            upper_sample_matches_pattern=upper_before==upper_pattern))
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
        need(bank[0:2]==(0x314b4e42,0) and bank[2]==2048 and bank[3]==0x800000 and
             bank[4]==bank[5]==bank[6] and bank[7:11]==(2048,0,2048,0)
             and bank[11]!=0 and bank[12:14]==(0,0) and
             bank[14]==bank[15], 'full-bank proof')
        need(claim[:3]==(0x314d5241,2048,0x833aedc5) and claim[3]==0 and
             claim[6]==0 and claim[10:13]==(900000,6291456,65536) and
             claim[7]>=0xc0800000 and claim[9]<0xc1000000 and
             claim[13:16]==(0x101,0x102,0x103), 'guarded arena allocations')
        need(bridge_words[6:8]==(0x31475242,0x161610e1), 'bridge identity')
        wire=struct.unpack_from('<16I',cur,0xc00)
        need(wire[:13]==(0,)*12+(0x161610e1,) and
             wire[14]>=0xc0810000 and wire[14]<0xc0ff0000 and
             wire[15]==4096,'card-request WAD channel identity')
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
        def transact(op,offset=0,data=b'',expected_status=0,wire_n=None):
            nonlocal seq
            n=len(data) if wire_n is None else wire_n
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
        # The card now owns each file request. Reply fields and inbound bytes
        # are published before the reply sequence; a separate cache readback
        # proves both success and no-copy rejection on the physical card.
        request_seq=0;wad_receipts=[];cache_expected=bytearray(PAGE)
        need(len(wad)==28795076,'pinned Freedoom length')
        words=transact(5,len(wad),expected_status=10,wire_n=0)
        need(words[18:20]==(0,0),'invalid EOF request did not publish')
        def wad_query(offset,n,mode='good'):
            nonlocal seq,request_seq
            need(n>0 and n<=PAGE and offset+n<=len(wad),'host WAD query bounds')
            seq+=1;expected_request=request_seq+1
            descriptor=struct.pack('<5I',5,offset,n,0,0x161610e1)
            write(0xc000e000,0xb84,descriptor)
            write(0xc000e000,0xb80,struct.pack('<I',seq))
            started=time.monotonic()
            while time.monotonic()-started<5:
                page=snap(0xc000e000)
                req=struct.unpack_from('<16I',page,0xc00)
                if req[0]==expected_request:break
                need(struct.unpack_from('<I',page,0xba0)[0]!=seq,
                     'WAD bridge acknowledged without request')
                time.sleep(.002)
            else:raise RuntimeError('card did not publish WAD request')
            request_seq=expected_request
            need(req[1:4]==(offset,n,1) and req[12]==0x161610e1 and
                 req[9]==0x444e4550 and req[14]==wire[14] and
                 req[15]==PAGE,'card-owned WAD request descriptor')
            part=wad[offset:offset+n]
            if mode=='stop':
                write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))
                want=15
            elif mode=='timeout':
                want=16
            else:
                write(0xc078a000,0,part)
                checksum=fnv(part)^(1 if mode=='bad-fnv' else 0)
                write(0xc000e000,0xc14,
                      struct.pack('<4I',offset,n,checksum,0))
                write(0xc000e000,0xc10,
                      struct.pack('<I',request_seq-1 if mode=='stale' else request_seq))
                want={'good':0,'bad-fnv':12,'stale':11}[mode]
            started=time.monotonic()
            while time.monotonic()-started<12:
                page=snap(0xc000e000)
                words=struct.unpack_from('<20I',page,0xb80)
                if words[8]==seq:break
                need(status('ram-admit').get('done')=='0','callback escaped during WAD read')
                time.sleep(.005)
            else:raise RuntimeError(f'WAD request timeout mode={mode}')
            response=struct.unpack_from('<16I',page,0xc00)
            need(words[9]==want and words[17]==1 and response[9]==want,
                 f'WAD {mode} status/arena guard: bridge={words[9]} wire={response[9]}')
            if want==0:
                need(words[10]==fnv(part) and response[10:12]==(fnv(part),n),
                     'WAD accepted payload receipt')
                cache_expected[:n]=part
            else:
                need(words[10]==0 and response[11]==0,'WAD rejected without copy')
            record=dict(seq=seq,request_seq=request_seq,offset=offset,n=n,
                        mode=mode,status=want,source_sha256=sha(part),
                        source_fnv=f'0x{fnv(part):08x}',
                        card_value=words[10],card_good=words[18],card_bad=words[19],
                        tick=struct.unpack_from('<I',page,0xb50)[0])
            wad_receipts.append(record)
            receipts.append(dict(seq=seq,op=5,offset=offset,n=n,
                                 status=words[9],value=words[10]))
            if mode!='stop':
                cached=transact(6,0,bytes(PAGE))
                out=snap(0xc078c000)
                need(out==cache_expected and fnv(out)==cached[10],
                     f'WAD cache readback after {mode}')
            return record
        directory=struct.unpack_from('<I',wad,8)[0]
        offsets=[(0,512),(directory,4096),(len(wad)-4096,4096),
                 (len(wad)-17,17),(4093,4096)]
        offsets += [((i*104729+9176)%(len(wad)-4096),4096) for i in range(32)]
        for off,n in offsets:wad_query(off,n)
        wad_query(0x12345,2048,'bad-fnv')
        wad_query(0x23456,1024,'stale')
        began_timeout=time.monotonic()
        wad_query(0x34567,512,'timeout')
        need(4.5<=time.monotonic()-began_timeout<12,
             'bounded WAD timeout duration')
        wad_query(0x45678,4096) # recovery after all three rejection classes
        # Run the admitted Doom entry exactly once. Its WAD callbacks own the
        # request sequence; the host answers immutable file slices only. The
        # first real frame is copied and exits via the owned 210 boundary.
        seq+=1;engine_seq=seq;engine_reads=[]
        write(0xc000e000,0xb84,
              struct.pack('<5I',7,0,0,fnv(b''),0x161610e1))
        write(0xc000e000,0xb80,struct.pack('<I',engine_seq))
        began_engine=time.monotonic();last_owner_audit=0
        last_request=began_engine
        last_capture=0
        trace_samples=[]
        while time.monotonic()-began_engine<1830:
            page=snap(0xc000e000)
            req=struct.unpack_from('<16I',page,0xc00)
            words=struct.unpack_from('<20I',page,0xb80)
            er=struct.unpack_from('<16I',page,0xc40)
            trace=struct.unpack_from('<16I',page,0xcc0)
            if time.monotonic()-last_capture>=1:
                (run/'engine-latest-page.bin').write_bytes(page)
                trace_samples.append(dict(elapsed_s=round(time.monotonic()-began_engine,3),
                                          words=[f'0x{x:08x}' for x in trace],
                                          reads=len(engine_reads)))
                if len(trace_samples)%10==0:
                    save(run/'engine-trace.json',trace_samples)
                last_capture=time.monotonic()
            if trace[0]==0x31435254 and trace[14]:
                (run/'engine-fault-page.bin').write_bytes(page)
                (run/'engine-fault-bss-page.bin').write_bytes(snap(0xc0718000))
                save(run/'engine-trace.json',trace_samples)
                save(run/'engine-reads.json',engine_reads)
                write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))
                raise RuntimeError(f'Doom owner/ISR fault 0x{trace[14]:x}; '
                                   'STOP published, grant retained')
            if req[0]==request_seq+1 and req[9]==0x444e4550:
                off,n=req[1:3]
                need(req[3]==1 and req[12]==0x161610e1 and
                     req[14]==wire[14] and req[15]==PAGE and
                     0<n<=PAGE and off+n<=len(wad),
                     'bounded engine WAD request')
                part=wad[off:off+n]
                if startup_oracle is not None and len(engine_reads)<len(startup_oracle):
                    need((off,n)==startup_oracle[len(engine_reads)],
                         f'native startup WAD request {len(engine_reads)+1}')
                write(0xc078a000,0,part)
                write(0xc000e000,0xc14,struct.pack('<4I',off,n,fnv(part),0))
                write(0xc000e000,0xc10,struct.pack('<I',req[0]))
                request_seq=req[0]
                last_request=time.monotonic()
                engine_reads.append(dict(request_seq=request_seq,offset=off,
                                         n=n,source_sha256=sha(part),
                                         source_fnv=f'0x{fnv(part):08x}'))
                if len(engine_reads)%100==0:
                    ownercheck(owned)
                    need(select(OLD,'dac960pg')['driver'] is None,
                         'old card touched during Doom')
                    save(run/'engine-reads.json',engine_reads)
                    print(f'Doom WAD reads: {len(engine_reads)}, '
                          f'elapsed {time.monotonic()-began_engine:.1f}s',
                          flush=True)
            elif req[0]>request_seq+1:
                raise RuntimeError('engine WAD request sequence skipped')
            if words[8]==engine_seq:break
            if time.monotonic()-last_request>120:
                (run/'engine-stall-page.bin').write_bytes(page)
                save(run/'engine-trace.json',trace_samples)
                # BAR0's second 4 KiB window exposes the page after PIATVR.
                (run/'engine-rip-samples.bin').write_bytes(snap(0xc0771000))
                save(run/'engine-stall.json',dict(
                    elapsed_seconds=time.monotonic()-began_engine,
                    idle_seconds=time.monotonic()-last_request,
                    reads=len(engine_reads),
                    engine_report=[f'0x{x:08x}' for x in er]))
                save(run/'engine-reads.json',engine_reads)
                write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))
                raise RuntimeError('Doom engine stopped making WAD/frame progress; STOP published')
            need(er[0] in (0xffffffff,0,0x314d5246) and
                 struct.unpack_from('<I',page,0xb58)[0]==0,
                 'retained Doom instance faulted')
            if time.monotonic()-last_owner_audit>5:
                need(status('ram-admit').get('done')=='0',
                     'Doom callback escaped before first frame')
                last_owner_audit=time.monotonic()
            time.sleep(.002)
        else:raise RuntimeError('bounded first-frame host deadline')
        save(run/'engine-reads.json',engine_reads)
        save(run/'engine-trace.json',trace_samples)
        if startup_oracle is not None:
            need(len(engine_reads)>=len(startup_oracle),
                 'native startup WAD request count')
        (run/'engine-ack-page.bin').write_bytes(page)
        receipts.append(dict(seq=engine_seq,op=7,offset=0,n=0,
                             status=words[9],value=words[10]))
        result_words=struct.unpack_from('<12I',page,0xc80)
        need(words[9:11]==(0,0x454e4702) and er[0:2]==
             (0x314d5246,2) and er[4:6]==(0x454e4702,a.frames) and
             er[9:11]==(0,1) and er[11]==er[12] and
             result_words[0:3]==(0x454e4750,2,6291456) and
             result_words[5]==a.frames and result_words[9:12]==(2,1,210),
             'bounded real Doom frame return/cleanup')
        game_pages=[]
        for index in range(16):
            got=transact(3,index,bytes(PAGE))
            out=snap(0xc078c000)
            need(fnv(out)==got[10],f'Doom frame page {index}')
            game_pages.append(out)
        game_frame=b''.join(game_pages)
        need(fnv(game_frame)==er[6] and
             len(set(game_frame[:64000]))>32 and
             (not result_words[3] or fnv(game_frame[:64000])==result_words[3]) and
             (not result_words[4] or fnv(game_frame[64000:64768])==result_words[4]),
             'complete real Doom frame and palette')
        frame_timing=None
        if a.frames>1:
            frame_ticks=struct.unpack_from('<'+str(a.frames)+'I',game_frame,64768)
            need(all(frame_ticks[i]>=frame_ticks[i-1] for i in range(1,a.frames)) and
                 frame_ticks[-1]>frame_ticks[0], 'monotonic card frame timer')
            elapsed_ticks=frame_ticks[-1]-frame_ticks[0]
            frame_timing=dict(frames=a.frames,timer_hz=100,
                              first_tick=frame_ticks[0],last_tick=frame_ticks[-1],
                              elapsed_ticks=elapsed_ticks,
                              render_fps=(a.frames-1)*100/elapsed_ticks,
                              interframe_ticks=[frame_ticks[i]-frame_ticks[i-1]
                                                for i in range(1,a.frames)])
            save(run/'frame-timing.json',frame_timing)
        (run/'game-frame.bin').write_bytes(game_frame)
        (run/'game-frame.pgm').write_bytes(
            b'P5\n320 200\n255\n'+game_frame[:64000])
        ownercheck(owned)
        page=snap(0xc000e000)
        (run/'prestop-page.bin').write_bytes(page)
        first=claim[4]
        time.sleep(.25)
        later=snap(0xc000e000)
        heart=struct.unpack_from('<16I',later,0xb40)
        need(heart[4]>first and heart[5:7]==(0,0) and
             status('ram-admit').get('done')=='0','live RTEMS heartbeat')
        wad_query(0x56789,512,'stop')
        save(run/'wad-receipts.json',wad_receipts)
        save(run/'bridge-receipts.json',receipts)
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
        final_bridge=struct.unpack_from('<20I',page,0xb80)
        need(final_bridge[18:20]==(38+len(engine_reads),4),
             'WAD success/rejection counters')
        save(a.out/'result.json',dict(boot_id=boot,image_sha256=image_sha,
            kernel_sha256=kernel_sha,firmware_sha256=FIRMWARE,
            full_audits_before=True,bank_report=[f'0x{x:08x}' for x in bank],
            claim_report=[f'0x{x:08x}' for x in state],
            bridge_report=[f'0x{x:08x}' for x in struct.unpack_from('<20I',page,0xb80)],
            upload_bytes=len(admission),upload_commands=sum(x['op']==1 for x in receipts),
            frame_sha256=sha(frame),frame_fnv=f'0x{fnv(frame):08x}',
            wad_requests=len(wad_receipts),wad_good=final_bridge[18],
            wad_bad=final_bridge[19],
            engine_wad_reads=len(engine_reads),
            engine_elapsed_seconds=time.monotonic()-began_engine,
            game_frame_sha256=sha(game_frame),
            game_frame_fnv=f'0x{fnv(game_frame):08x}',
            frame_timing=frame_timing,
            engine_report=[f'0x{x:08x}' for x in er],
            engine_results=[f'0x{x:08x}' for x in result_words],
            heartbeat_before=first,heartbeat_after=heart[4],
            release='reboot-only',grant_retained=True,
            card=select(BDF,'accele160'),old=select(OLD,'dac960pg')))
        print(f'Real Doom {a.frames}-frame run captured; WAD, cleanup and STOP passed')
    finally:
        translate(original);bar.close();res.close();cfg.close()

if __name__=='__main__':main()
