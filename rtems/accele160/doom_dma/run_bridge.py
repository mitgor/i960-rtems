#!/usr/bin/env python3
"""Run retained RTEMS Doom with checked live two-slot frame capture."""
import argparse,os,fcntl,hashlib,json,mmap,signal,struct,subprocess,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/lease_probe'))
from run_lease import (BDF,OLD,PAGE,DEVICE,DEBUG,FIRMWARE,HANDLER,
                       MODULES,NONCE,need,sha,fields,fnv,status,insmod,
                       done,command,release,verify_read)
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select,require_unbound_or_absent
from browser import BrowserSession
import key_fifo
sys.path.insert(0,str(ROOT/'rtems/residentnet'))
from presentation_profile import decode as decode_profile

IMAGE='957e49dc912153ddc0f80f3f22e1276df20e023c3e6ae427efe1b6c96778cdde'
KERNEL='9b9a848dc099a2d43db1752561caaf7320b925988a2313a502209f54c231d88e'
EXPECTED_FNV=0x6fa5dc25
PAGES=29

def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def main():
    global fnv
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('reserve_module','release_module','copy_module','digest_module',
              'admit_module','handler','firmware','kernel','image',
              'readback0','readback1','template','relocations','wad','out','engine_manifest','dma_module'):
        p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    p.add_argument('--frames',type=int,choices=(32,),default=32)
    p.add_argument('--persistent',action='store_true')
    p.add_argument('--reusable',action='store_true')
    p.add_argument('--restart-cycles',type=int,default=0,help='acceptance: automatically run this many games, then globally stop')
    p.add_argument('--flat-benchmark',action='store_true',help='four games textured/flat/flat/textured; F6 transition probe in game 1')
    p.add_argument('--keyboard-mode',choices=('mailbox','fifo'),default='mailbox')
    p.add_argument('--keyboard-selftest',action='store_true',help='enable authenticated bounded pending-input STOP probe')
    p.add_argument('--quit-game',type=int,default=0,help='acceptance: inject F10/Y instead of STOP in this run')
    p.add_argument('--max-frames',type=int,default=0,help='request graceful STOP after this many frames; 0 plays until STOP')
    p.add_argument('--capture-all',action='store_true',help='retain every full frame during acceptance tests')
    p.add_argument('--disconnect-seconds',type=float,default=300)
    p.add_argument('--fps-manifest',type=Path)
    p.add_argument('--startup-oracle',type=Path)
    p.add_argument('--port',type=int,default=0,
                   help='serve checked live frames and bounded browser keys')
    p.add_argument('--paired-frames',type=int,choices=(4,32),default=4)
    p.add_argument('--stall-generation',type=int,default=0)
    p.add_argument('--card-fnv',choices=('on','off'),default='on',help='optional per-frame card FNV; all guards, ownership and system audits stay enabled')
    a=p.parse_args()
    need(not a.reusable or a.persistent,'reusable requires persistent')
    need(a.restart_cycles>=0 and (not a.restart_cycles or (a.reusable and a.max_frames>=40)),'restart test bounds')
    need(not a.flat_benchmark or (a.reusable and a.restart_cycles==4 and a.max_frames>=128 and not a.quit_game),'flat benchmark bounds')
    need(not a.quit_game or (a.restart_cycles and 1<=a.quit_game<=a.restart_cycles),'bounded Quit test requires restart cycles')
    need(a.max_frames>=0 and a.disconnect_seconds>=5,'session bounds')
    signal_stop=threading.Event()
    if a.persistent:
        for sig in (signal.SIGINT,signal.SIGTERM):
            signal.signal(sig,lambda *_:signal_stop.set())
    terminal_schema=0;terminal_test=0;terminal_nonce=0
    service_schema=0
    keyboard_fifo_schema=0
    modules=dict(MODULES)
    if a.frames==32:
        need(a.fps_manifest is not None and a.startup_oracle is not None,
             'FPS manifest and native startup oracle required')
        fps_manifest=json.loads(a.fps_manifest.read_text())
        if 'admit_module_sha256' in fps_manifest:
            need(fps_manifest['admit_source_sha256']==sha((ROOT/'host/accele160/ram_admit/admit_command.c').read_bytes()),'private admission queue source identity')
            modules['admit']=fps_manifest['admit_module_sha256']
        terminal_schema=fps_manifest.get('terminal_schema',0)
        terminal_test=fps_manifest.get('terminal_test',0)
        need(terminal_schema in (0,1) and terminal_test in (0,1,2,3,4,5,6,7) and (terminal_schema or not terminal_test),'terminal profile')
        if terminal_schema:
            need(set(fps_manifest['terminal_sources'])=={'policy.h','card.inc','terminal.S','host.py'},'terminal source set')
            for name,digest in fps_manifest['terminal_sources'].items():
                need(sha((Path(__file__).parent.parent/'fault'/name).read_bytes())==digest,'terminal source identity')
            import importlib.util
            spec=importlib.util.spec_from_file_location('accele_terminal',Path(__file__).parent.parent/'fault/host.py')
            terminal=importlib.util.module_from_spec(spec);spec.loader.exec_module(terminal)
        service_schema=fps_manifest.get('service_schema',0)
        need(service_schema in (0,1),'service schema')
        if service_schema:
            need(set(fps_manifest['service_sources'])=={'protocol.h','card.inc','host.py'},'complete service source identities')
            for name,digest in fps_manifest['service_sources'].items():
                need(sha((Path(__file__).parent.parent/'service'/name).read_bytes())==digest,'service source identity')
        keyboard_fifo_schema=fps_manifest.get('keyboard_fifo_schema',0)
        need(keyboard_fifo_schema in (0,1),'keyboard FIFO schema')
        if keyboard_fifo_schema:
            need(fps_manifest['key_fifo_sha256']==sha(Path(__file__).with_name('key_fifo.h').read_bytes()),'keyboard FIFO source identity')
        need(bool(fps_manifest.get('reusable'))==a.reusable and fps_manifest['frames']==(0 if a.persistent else 32) and
             bool(fps_manifest.get('persistent'))==a.persistent and
             fps_manifest['source_sha256']==sha(Path(__file__).with_name('app.c').read_bytes()),
             'FPS source/manifest identity')
        for name,key in [('fnv_host.so','native_fnv_sha256'),('frame_dma.h','dma_source_sha256'),('copy.h','copy_sha256'),('engine_identity.h','engine_identity_sha256')]:
            need(sha(Path(__file__).with_name(name).read_bytes())==fps_manifest[key],f'{name} identity')
        need(sha(a.engine_manifest.read_bytes())==fps_manifest['engine_manifest_sha256'],'engine manifest identity')
        need(sha(a.dma_module.read_bytes())==fps_manifest['dma_module_sha256'],'DMA module identity')
        from fast_fnv import fnv as native_fnv
        fnv=native_fnv
        engine_manifest=json.loads(a.engine_manifest.read_text())
        need(bool(engine_manifest.get('persistent_play'))==a.persistent,
             'persistent kernel/engine agreement')
        need(engine_manifest.get('card_profile','accele160')=='accele160',
             'Doom image card profile must be AcceleRAID 160')
        need(not a.flat_benchmark or engine_manifest.get('runtime_flat'),'flat benchmark engine option')
        need(engine_manifest['double_buffer'] and engine_manifest['direct_frame'] and engine_manifest['no_fnv'],'admitted direct double-buffer engine')
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
    need(a.keyboard_mode=='mailbox' or keyboard_fifo_schema==1,'kernel lacks bounded keyboard FIFO')
    need(not a.keyboard_selftest or keyboard_fifo_schema==1,'keyboard selftest requires FIFO kernel')
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
    for n,want in modules.items():
        path=getattr(a,n+'_module')
        debug='ram-admit' if n=='admit' else n
        need(sha(path.read_bytes())==want and
             not Path('/sys/module',n+'_command').exists() and
             not (DEBUG/f'accele-{debug}').exists(),f'{n} module preflight')
    card=select(BDF,'accele160',driver='myrsread')
    old=require_unbound_or_absent(OLD,'dac960pg')
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
         fnv=f'0x{digest:08x}',modules=modules))
    cfg=(DEVICE/'config').open('r+b',buffering=0)
    res=(DEVICE/'resource0').open('r+b',buffering=0)
    bar=mmap.mmap(res.fileno(),2*PAGE)
    cfg.seek(0x44);original=struct.unpack('<I',cfg.read(4))[0]
    need(original==0xc0000000,'PIATVR unexpected')
    def translate(addr):
        cfg.seek(0x44);cfg.write(struct.pack('<I',addr));cfg.seek(0x44)
        need(struct.unpack('<I',cfg.read(4))[0]==addr,'PIATVR readback')
    def snap(addr):
        translate(addr);data=bytes(bar[PAGE:2*PAGE])
        pump_service()
        return data
    def write(addr,off,data):
        translate(addr);bar[PAGE+off:PAGE+off+len(data)]=data
        need(bytes(bar[PAGE+off:PAGE+off+len(data)])==data,'PCI writeback')
    def ownercheck(base):
        got=snap(0xc0384000)
        need(got[0x2a0:0xaa0]==base[0x2a0:0xaa0],
             'allocator count/owner changed')
        return got
    active_owner=False
    quiescent=False
    browser=None;control_file=None;service=None;service_pumping=False
    def pump_service():
        nonlocal service_pumping
        if service and service.started and not service.testing and not service_pumping:
            service_pumping=True
            try:service.pump(snap,write)
            finally:service_pumping=False
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
        for n in modules:insmod(getattr(a,n+'_module'))
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
        need(not Path('/sys/module/dma_frames').exists(),'frame pin module already loaded')
        subprocess.run(['insmod',str(a.dma_module)],check=True)
        pin_dir=Path('/sys/kernel/debug/accele-frame-dma')
        pin=fields(pin_dir/'status')
        need(pin['bdf']==BDF and pin['bytes']=='65536' and pin['total']=='77824' and pin['guard_changes']=='0' and pin['retained']=='1','guarded permanent DMA targets')
        buses=[int(pin['bus0'],16),int(pin['bus1'],16)]
        need(all(0x10000<=x<=0xfffe0000 and not x%4096 for x in buses) and abs(buses[0]-buses[1])>=77824,'disjoint DMA targets')
        (run/'dma-pin-before.txt').write_text((pin_dir/'status').read_text())
        denied=subprocess.run(['rmmod','dma_frames'],capture_output=True,text=True)
        need(denied.returncode!=0 and Path('/sys/module/dma_frames').exists(),'DMA pin must reject unload before reset')
        (run/'dma-pin-release-denied.txt').write_text(denied.stderr)
        need(fields(pin_dir/'status')==pin,'pin unchanged after denied unload')
        dma_control=struct.pack('<16I',0x31464d44,0x161610e1,*buses,65536,0x314d5241,a.paired_frames,int(a.card_fnv=='off'),*([0]*8))
        write(0xc000e000,0xd40,dma_control)
        write(0xc000e000,0xa00,manifest)
        write(0xc000e000,0xa20,b'\xa5'*28)
        write(0xc000e000,0xa40,side)
        write(0xc000e000,0xa60,b'\xa5'*32)
        if terminal_schema:terminal_nonce=terminal.initialize(write)
        if service_schema:
            sys.path.insert(0,str(Path(__file__).parent.parent/'service'))
            from host import Service
            service=Service('/run/i960-rtems-console.sock',a.out/'console.jsonl',defer=True)
            service.initialize(write)
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
        active_owner=True
        if a.port and terminal_test in (0,5):
            need(1024<=a.port<=65535,'browser port range')
            browser=BrowserSession(a.port,runtime_flat=bool(engine_manifest.get('runtime_flat')),
                keyboard_mode=a.keyboard_mode,keyboard_fifo=bool(keyboard_fifo_schema),keyboard_test=a.keyboard_selftest)
            if a.reusable:
                control_file=Path('/run/i960-doom-control.json')
                fd=os.open(control_file,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                with os.fdopen(fd,'w') as out:json.dump(dict(pid=os.getpid(),boot_id=boot,port=browser.port,token=browser.token),out)
            print(f'Browser session: http://192.168.2.75:{a.port}/',flush=True)
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
        if terminal_test in (1,2,3,4,6,7):
            def deny_dma_release():
                p=subprocess.run(['rmmod','dma_frames'],capture_output=True,text=True)
                return dict(returncode=p.returncode,stderr=p.stderr)

            terminal_result=terminal.exercise(snap,write,terminal_nonce,terminal_test,
                a.out/'terminal',lambda:status('ram-admit'),lambda:fields(pin_dir/'status'),
                nmi=lambda:bar.__setitem__(slice(0x20,0x24),struct.pack('<I',0x80000000)),
                mu_read=lambda:struct.unpack_from('<3I',bar,0x20),
                frame_read=lambda slot:(pin_dir/f'frame{slot}.bin').read_bytes(),
                deny_release=deny_dma_release)
            (a.out/'terminal'/'owner-after.bin').write_bytes(ownercheck(owned))
            save(a.out/'result.json',dict(terminal=terminal_result,boot_id=boot,
                 kernel_sha256=kernel_sha,image_sha256=image_sha,release='reboot-only',
                 card=select(BDF,'accele160'),old=require_unbound_or_absent(OLD,'dac960pg')))
            quiescent=True # terminal park, not QUIE or driver completion
            return
        runtime_seq=0;runtime_samples=[]
        def runtime_audit(label,phase=0):
            nonlocal runtime_seq
            if terminal_test!=5:return
            if not phase:runtime_seq+=1
            row=terminal.runtime_sample(snap,write,terminal_nonce,runtime_seq,
                a.out/('owned-'+label+'.bin'),phase)
            row['label']=label;runtime_samples.append(row)
            save(a.out/'owned-runtime.json',runtime_samples)
        runtime_audit('ready')
        template=a.template.read_bytes();relocs=a.relocations.read_bytes()
        wad=a.wad.read_bytes()
        need(sha(template)==engine_manifest['template_sha256'] and len(template)==engine_manifest['file_bytes'],'exact Doom template')
        need(sha(relocs)==engine_manifest['metadata_sha256'] and len(relocs)==engine_manifest['metadata_bytes'],'exact relocations')
        need(sha(wad)=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
             and sha(wad[:512])=='93bd1ddcfc43fbf233207876f5cfcbaef4cf4e64a1093efa47be9517d93214bd','exact Freedoom WAD')
        admission=template+bytes(engine_manifest['metadata_offset']-len(template))+relocs
        need(len(admission)==engine_manifest['admission_bytes']<=900000,'admission geometry')
        if service:
            service.selftest(snap,write);service.start()
        seq=0;receipts=[];heartbeat=0;last_heartbeat=0
        def pump_heartbeat():
            nonlocal heartbeat,last_heartbeat
            now=time.monotonic()
            pump_service()
            if a.reusable and now-last_heartbeat>=.5:
                heartbeat+=1;write(0xc000e000,0xd34,struct.pack('<I',heartbeat));last_heartbeat=now
        def transact(op,offset=0,data=b'',expected_status=0,wire_n=None):
            nonlocal seq
            pump_heartbeat()
            n=len(data) if wire_n is None else wire_n
            if data:write(0xc078a000,0,data)
            seq+=1
            descriptor=struct.pack('<5I',op,offset,n,fnv(data),0x161610e1)
            write(0xc000e000,0xb84,descriptor)
            write(0xc000e000,0xb80,struct.pack('<I',seq))
            started=time.monotonic()
            while time.monotonic()-started<90:
                pump_heartbeat()
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
        need(words[12]==1 and words[14]==claim[7]+engine_manifest['entry'] and
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
                pump_heartbeat()
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
        game_run=1;global_frames=0;global_seen=[0,0];global_key=0;total_reads=0
        games=[];boot_run=run
        while True:
            keyboard_mode=a.keyboard_mode
            if a.reusable:
                run=boot_run/f'game-{game_run:04d}';run.mkdir()
                if browser:keyboard_mode=browser.begin_game(game_run)
            if keyboard_fifo_schema:
                key_fifo.configure(snap(0xc000e000),write,global_key,game_run,keyboard_mode)
            # One admitted image per game; all transport state remains boot-owned.
            seq+=1;engine_seq=seq;engine_reads=[]
            write(0xc000e000,0xb84,
                  struct.pack('<5I',7,0,0,fnv(b''),0x161610e1))
            write(0xc000e000,0xb80,struct.pack('<I',engine_seq))
            began_engine=time.monotonic();last_owner_audit=0
            stop_reason=None;stop_started=0;quit_events=0;flat_events=0
            flat_schedule=([(8,448),(8,192),(20,448),(20,192)] if game_run==1 else [(8,448),(8,192)] if game_run in (2,3) else [])
            last_request=began_engine
            last_capture=0
            trace_samples=[]
            live_seen=list(global_seen);generation_origin=global_frames
            live_receipts=[];frame_count=0;read_count=0
            frame_journal=(run/'live-frame-receipts.jsonl').open('a',buffering=1)
            read_journal=(run/'engine-reads.jsonl').open('a',buffering=1)
            key_out_seq=global_key
            key_acked=global_key;key_batches=0;key_max_depth=0
            key_journal=(run/'keyboard-receipts.jsonl').open('a',buffering=1)
            live_dir=run/'live-frames';live_dir.mkdir()
            def read_card_bytes(ptr,n):
                need(n==65536 and ptr&8191==4096 and
                     0xc0810000<=ptr and ptr+15*8192+PAGE<=0xc0ff0000,
                     'live striped slot address/length')
                # This PIATVR aperture exposes the odd 4 KiB page in every 8 KiB
                # pair. The card stages exactly one frame page in each odd page.
                return b''.join(snap(ptr+i*8192-PAGE) for i in range(16))
            while a.persistent or time.monotonic()-began_engine<1830:
                pump_service()
                page=snap(0xc000e000)
                req=struct.unpack_from('<16I',page,0xc00)
                words=struct.unpack_from('<20I',page,0xb80)
                er=struct.unpack_from('<16I',page,0xc40)
                trace=struct.unpack_from('<16I',page,0xcc0)
                live=struct.unpack_from('<16I',page,0xd00)
                now=time.monotonic()
                if a.quit_game==game_run and frame_count>=a.max_frames+64:
                    raise RuntimeError('menu Quit test frame deadline')
                if a.persistent:
                    if now-last_heartbeat>=.5:
                        heartbeat+=1
                        write(0xc000e000,0xd34,struct.pack('<I',heartbeat))
                        last_heartbeat=now
                    reason=('signal' if signal_stop.is_set() else
                            'browser STOP' if browser and browser.stop.is_set() else
                            'browser disconnected' if browser and browser.disconnected(a.disconnect_seconds) else
                            'frame limit' if a.max_frames and frame_count>=a.max_frames and game_run!=a.quit_game else None)
                    if reason and stop_reason is None:
                        stop_reason=reason;stop_started=now
                        write(0xc000e000,0xa7c,struct.pack('<I',0x504f5453))
                        print('Stopping Doom:',reason,flush=True)
                    if stop_started and now-stop_started>30:
                        raise RuntimeError('engine STOP deadline; retain resources')
                elif browser and browser.stop.is_set():
                    raise RuntimeError('browser STOP requested')
                if keyboard_fifo_schema:
                    kbd=key_fifo.snapshot(page,key_out_seq,game_run,keyboard_mode)
                    need(kbd[5]>=key_acked,'keyboard ACK monotonic')
                    if kbd[5]!=key_acked:
                        key_journal.write(json.dumps(dict(op='ack',seq=kbd[5],card_tick=kbd[10],card_frame=kbd[11],host_ns=time.monotonic_ns()))+'\n')
                        key_acked=kbd[5]
                    key_max_depth=max(key_max_depth,key_out_seq-key_acked)
                    available=(16 if keyboard_mode=='fifo' else 1)-(key_out_seq-key_acked)
                    if browser:
                        with browser.lock:
                            browser.keyboard_stats=dict(published=key_out_seq,acked=kbd[5],discarded=kbd[6],run_id=kbd[7],card_max_depth=kbd[9])
                    if browser and browser.keyboard_stop_after_batch.is_set() and available<16:
                        available=0
                else:
                    available=int(live[12]==key_out_seq)
                keys=[]
                for _ in range(available if stop_reason is None else 0):
                    key=None
                    if game_run==a.quit_game and frame_count>=40 and quit_events<4:
                        key=(196|256,196,121|256,121)[quit_events];quit_events+=1
                    elif a.flat_benchmark and flat_events<len(flat_schedule) and frame_count>=flat_schedule[flat_events][0]:
                        key=flat_schedule[flat_events][1];flat_events+=1
                    elif browser and not a.flat_benchmark:key=browser.next_key()
                    if key is None:break
                    keys.append(key)
                if keys:
                    if keyboard_fifo_schema:
                        key_out_seq=key_fifo.submit(write,key_out_seq,key_acked,game_run,keyboard_mode,keys)
                        key_batches+=1;key_max_depth=max(key_max_depth,key_out_seq-key_acked)
                        key_journal.write(json.dumps(dict(op='submit',last_seq=key_out_seq,events=keys,acked=key_acked,host_ns=time.monotonic_ns()))+'\n')
                        if browser and browser.keyboard_stop_after_batch.is_set():
                            need(a.keyboard_selftest and keyboard_mode=='fifo' and len(keys)==16,'bounded keyboard STOP probe')
                            browser.keyboard_stop_after_batch.clear();browser.stop.set()
                            stop_reason='keyboard pending STOP probe';stop_started=time.monotonic()
                            write(0xc000e000,0xa7c,struct.pack('<I',0x504f5453))
                            print('Stopping Doom with a published 16-entry keyboard batch',flush=True)
                    else:
                        key=keys[0]
                        write(0xc000e000,0xd2c,struct.pack('<I',key))
                        key_out_seq+=1
                        write(0xc000e000,0xd28,struct.pack('<I',key_out_seq))
                need(live[:2]==(0x3145564c,0x161610e1),
                     'live frame channel identity')
                need(live[14]!=live[15] and
                     abs(live[14]-live[15])>=17*8192,
                     'disjoint live frame slots')
                for slot,base in ((0,2),(1,6)):
                    generation=live[base]
                    if generation==live_seen[slot]:continue
                    if generation!=generation_origin+frame_count+1:continue
                    local_frame=generation-generation_origin
                    need(generation>live_seen[slot], 'live slot generation monotonic')
                    need((a.persistent or local_frame<=a.frames) and (local_frame-1)&1==slot and
                         live[base+3]==live_seen[slot],
                         'live frame ownership/ACK')
                    marker=(pin_dir/f'marker{slot}.bin').read_bytes()
                    marker_words=struct.unpack('<8I',marker)
                    source=claim[7]+engine_manifest['play_offset']+slot*65536
                    expected_marker=(0x31505044,0x161610e1,generation,slot,65536,source,live[base+2],(~generation)&0xffffffff)
                    if marker_words!=expected_marker:continue
                    observed_ns=time.monotonic_ns()
                    fd=os.open(pin_dir/f'frame{slot}.bin',os.O_RDONLY)
                    try:capture=os.pread(fd,77824,0)
                    finally:os.close(fd)
                    need(len(capture)==77824 and capture[:4096]==b'\xa5'*4096 and capture[69664:]==b'\xa5'*(77824-69664),'full DMA guards')
                    need(capture[69632:69664]==marker and (pin_dir/f'marker{slot}.bin').read_bytes()==marker,'immutable DMA completion marker')
                    image=capture[4096:69632]
                    retain=not a.persistent or a.capture_all or local_frame<=max(32,a.paired_frames) or generation%300==0
                    if retain:(run/f'dma-frame-{generation:04d}.bin').write_bytes(capture)
                    if local_frame<=a.paired_frames:
                        pio=read_card_bytes(live[14+slot],65536)
                        need(pio==image,'complete paired DMA/PIO frame')
                    (run/'dma-pin-latest.txt').write_text((pin_dir/'status').read_text())
                    need(fields(pin_dir/'status')['guard_changes']=='0','both DMA buffer guards')

                    host_hash=fnv(image)
                    need((host_hash if a.card_fnv=='on' else 0)==live[base+1],
                         'declared live frame payload checksum mode')
                    if retain:(live_dir/f'frame-{generation:04d}.bin').write_bytes(image)
                    if a.persistent:(live_dir/'latest.bin').write_bytes(image)
                    profile=decode_profile(image,local_frame,options=engine_manifest)
                    if a.flat_benchmark:
                        if local_frame<=8:need(profile['flat_planes']==0,'initial textured mode')
                        if local_frame>=32:
                            need(profile['flat_planes']==int(game_run in (2,3)),'confirmed benchmark mode')
                            need(profile['flat_switches']==(2 if game_run==1 else 1 if game_run in (2,3) else 0),'confirmed F6 count')
                    if browser:browser.publish(generation,image,profile)
                    receipt=dict(profile=profile,generation=generation,local_frame=local_frame,game_run=game_run,slot=slot,
                        card_tick=live[base+2],fnv=f'0x{host_hash:08x}',
                        card_fnv=f'0x{live[base+1]:08x}',card_fnv_mode=a.card_fnv,
                        sha256=sha(image),observed_ns=observed_ns,
                        observed_to_http_ns=time.monotonic_ns()-observed_ns,
                        paired_pio=local_frame<=a.paired_frames,source=source)
                    frame_count=local_frame
                    if local_frame==32:runtime_audit('game-%d-frame32'%game_run)
                    live_receipts.append(receipt)
                    frame_journal.write(json.dumps(receipt)+'\n')
                    if a.persistent and len(live_receipts)>64:del live_receipts[:-64]
                    if generation==a.stall_generation:
                        stalled=time.monotonic()
                        time.sleep(3)
                        again=(pin_dir/f'frame{slot}.bin').read_bytes()
                        need(again==capture and (pin_dir/f'marker{slot}.bin').read_bytes()==marker,'stalled host buffer remains immutable')
                        save(run/'dma-stall.json',dict(generation=generation,seconds=time.monotonic()-stalled,unchanged=True))
                    write(0xc000e000,0xd00+(base+3)*4,
                          struct.pack('<I',generation))
                    live_seen[slot]=generation
                    last_request=time.monotonic()
                    if a.persistent and generation%100==0:
                        window=live_receipts[-60:]
                        dt=window[-1]['card_tick']-window[0]['card_tick']
                        save(a.out/'progress.json',dict(frames=frame_count,wad_reads=read_count,
                             card_fps=(len(window)-1)*100/dt if dt else 0,
                             elapsed_s=time.monotonic()-began_engine,stop_reason=stop_reason))
                if time.monotonic()-last_capture>=1:
                    (run/'engine-latest-page.bin').write_bytes(page)
                    trace_samples.append(dict(elapsed_s=round(time.monotonic()-began_engine,3),
                                              words=[f'0x{x:08x}' for x in trace],
                                              reads=len(engine_reads)))
                    if len(trace_samples)%10==0:
                        save(run/'engine-trace.json',trace_samples)
                    if a.persistent and len(trace_samples)>600:del trace_samples[:-600]
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
                    if startup_oracle is not None and read_count<len(startup_oracle):
                        need((off,n)==startup_oracle[read_count],
                             f'native startup WAD request {read_count+1}')
                    write(0xc078a000,0,part)
                    write(0xc000e000,0xc14,struct.pack('<4I',off,n,fnv(part),0))
                    write(0xc000e000,0xc10,struct.pack('<I',req[0]))
                    request_seq=req[0]
                    last_request=time.monotonic()
                    read_count+=1
                    row=dict(request_seq=request_seq,offset=off,
                                             n=n,source_sha256=sha(part),
                                             source_fnv=f'0x{fnv(part):08x}')
                    engine_reads.append(row);read_journal.write(json.dumps(row)+'\n')
                    if a.persistent and len(engine_reads)>256:del engine_reads[:-256]
                    if read_count%100==0:
                        ownercheck(owned)
                        need(require_unbound_or_absent(OLD,'dac960pg')['driver'] is None,
                             'old card touched during Doom')
                        save(run/'engine-reads.json',engine_reads)
                        print(f'Doom WAD reads: {read_count}, '
                              f'elapsed {time.monotonic()-began_engine:.1f}s',
                              flush=True)
                elif req[0]>request_seq+1:
                    raise RuntimeError('engine WAD request sequence skipped')
                if words[8]==engine_seq and (a.persistent or frame_count==a.frames):break
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
                    ownercheck(owned)
                    need(require_unbound_or_absent(OLD,'dac960pg')['driver'] is None,'old card touched during play')
                    need(status('ram-admit').get('done')=='0',
                         'Doom callback escaped before first frame')
                    last_owner_audit=time.monotonic()
                time.sleep(.002)
            else:raise RuntimeError('bounded first-frame host deadline')
            save(run/'engine-reads.json',engine_reads)
            save(run/'engine-trace.json',trace_samples)
            save(run/'live-frame-receipts.json',live_receipts)
            frame_journal.close();read_journal.close()
            need(a.persistent or (frame_count==a.frames and
                 sorted(r['generation'] for r in live_receipts)==list(range(1,a.frames+1))),
                 'all live frames captured exactly once')
            if startup_oracle is not None:
                need((a.persistent and stop_reason and not frame_count) or read_count>=len(startup_oracle),
                     'native startup WAD request count')
            (run/'engine-ack-page.bin').write_bytes(page)
            receipts.append(dict(seq=engine_seq,op=7,offset=0,n=0,
                                 status=words[9],value=words[10]))
            result_words=struct.unpack_from('<12I',page,0xc80)
            need(words[9:11]==((31 if a.persistent else 0),0x454e4702) and er[0:2]==
                 (0x314d5246,2) and er[4:6]==(0x454e4702,frame_count) and
                 er[9:11]==(0,1) and er[11]==er[12] and
                 result_words[0:3]==(0x454e4750,2,6291456) and
                 result_words[5] in ((frame_count,frame_count+1) if a.persistent else (a.frames,)) and result_words[9:12]==(2,1,210),
                 'bounded real Doom frame return/cleanup')
            game_pages=[]
            for index in range(16):
                got=transact(3,index,bytes(PAGE))
                out=snap(0xc078c000)
                need(fnv(out)==got[10],f'Doom frame page {index}')
                game_pages.append(out)
            game_frame=b''.join(game_pages)
            need((not frame_count or fnv(game_frame)==er[6]) and
                 len(set(game_frame[:64000]))>32 and
                 (not frame_count or sha(game_frame)==live_receipts[-1]['sha256']) and
                 (not result_words[3] or fnv(game_frame[:64000])==result_words[3]) and
                 (not result_words[4] or fnv(game_frame[64000:64768])==result_words[4]),
                 'complete real Doom frame and palette')
            frame_timing=None
            if frame_count>1:
                frame_ticks=([r['card_tick'] for r in live_receipts] if a.persistent else
                             struct.unpack_from('<'+str(a.frames)+'I',page,0xe00))
                need(all(frame_ticks[i]>=frame_ticks[i-1] for i in range(1,len(frame_ticks))) and
                     frame_ticks[-1]>frame_ticks[0], 'monotonic card frame timer')
                elapsed_ticks=frame_ticks[-1]-frame_ticks[0]
                frame_timing=dict(frames=len(frame_ticks),timer_hz=100,
                                  first_tick=frame_ticks[0],last_tick=frame_ticks[-1],
                                  elapsed_ticks=elapsed_ticks,
                                  render_fps=(len(frame_ticks)-1)*100/elapsed_ticks,
                                  interframe_ticks=[frame_ticks[i]-frame_ticks[i-1]
                                                    for i in range(1,len(frame_ticks))])
                save(run/'frame-timing.json',frame_timing)
            (run/'game-frame.bin').write_bytes(game_frame)
            (run/'game-frame.pgm').write_bytes(
                b'P5\n320 200\n255\n'+game_frame[:64000])
            ownercheck(owned)
            page=snap(0xc000e000)
            (run/'prestop-page.bin').write_bytes(page)
            keyboard_result=None
            if keyboard_fifo_schema:
                kbd=key_fifo.snapshot(page,key_out_seq,game_run,keyboard_mode)
                waiting=key_fifo.pending(page,key_out_seq,game_run,keyboard_mode)
                need(kbd[5]==kbd[6]+kbd[13] and struct.unpack_from('<I',page,0xd30)[0]==kbd[5],'keyboard consumed/discarded conservation')
                keyboard_result=dict(mode=keyboard_mode,published=key_out_seq,acked=kbd[5],consumed=kbd[13],
                    discarded=kbd[6],pending=waiting,max_depth=key_max_depth,card_max_depth=kbd[9],batches=key_batches)
                key_acked=kbd[5]
                if browser:
                    with browser.lock:browser.keyboard_stats=dict(keyboard_result,run_id=game_run)
            key_journal.close()
            first=claim[4]
            time.sleep(.25)
            later=snap(0xc000e000)
            heart=struct.unpack_from('<16I',later,0xb40)
            need(heart[4]>first and heart[5:7]==(0,0) and
                 status('ram-admit').get('done')=='0','live RTEMS heartbeat')
            total_reads+=read_count
            global_frames+=frame_count;global_seen=list(live_seen);global_key=key_out_seq
            game_result=dict(game_run=game_run,frames=frame_count,global_frames=global_frames,
                wad_reads=read_count,request_seq=request_seq,key_sent=key_out_seq,key_acked=key_acked if keyboard_fifo_schema else live[12],keyboard=keyboard_result,
                reason=stop_reason or 'menu Quit',frame_timing=frame_timing,
                elapsed_s=time.monotonic()-began_engine,frame_sha256=sha(game_frame),
                engine_report=list(er),engine_results=list(result_words))
            if a.reusable:
                # All boot invariants and exact final image are checked each game.
                need(struct.unpack_from('<16I',later,0xb00)==bank,'retained full-bank proof')
                need(fields(pin_dir/'status')['guard_changes']=='0','idle DMA guards')
                # These are outside ARENA_END (0xc0ff0000). Earlier samples
                # inside the arena can legitimately become DMA staging/heap.
                for index in range(2033,2048,2):
                    expected=struct.pack('<1024I',*(pattern(index,w) for w in range(1024)))
                    need(snap(0xc0800000+(index-1)*PAGE)==expected,'idle untouched upper tail')
                data=struct.pack('<4I',global_frames,request_seq,game_run+1,global_key)
                transact(9,game_run,data)
                idle_page=snap(0xc000e000);(run/'idle-verified.bin').write_bytes(idle_page)
                dma_idle=struct.unpack_from('<32I',idle_page,0xd80)
                need(dma_idle[:3]==(0x31464d44,0x161610e1,0) and dma_idle[11]==global_frames and dma_idle[14:16]==(0,0),'per-game DMA drain')
                transact(7,expected_status=20) # a retired image cannot be entered twice
                if global_seen[0]:
                    write(0xc000e000,0xd14,struct.pack('<I',global_seen[0]-1))
                    transact(8,game_run,data,expected_status=45)
                    write(0xc000e000,0xd14,struct.pack('<I',global_seen[0]))
                    transact(9,game_run,data)
                # Malformed/stale requests must leave the retired image admitted.
                for offset,values,want in ((game_run-1,(global_frames,request_seq,game_run+1,global_key),40),
                    (game_run,(global_frames+1,request_seq,game_run+1,global_key),42),
                    (game_run,(global_frames,request_seq+1,game_run+1,global_key),43),
                    (game_run,(global_frames,request_seq,game_run+1,global_key+1),44)):
                    rejected=transact(8,offset,struct.pack('<4I',*values),expected_status=want)
                    need(rejected[12]==1,'rejection did not retire admission')
                runtime_audit('game-%d-idle'%game_run)
                game_result['idle_verified']=True
                if service:
                    service.record(event='idle_gate',game_run=game_run)
                    service.selftest(snap,write)
            save(run/'game-result.json',game_result);games.append(game_result)
            save(a.out/'games.json',games)
            if not a.reusable or signal_stop.is_set() or (a.restart_cycles and game_run>=a.restart_cycles):break
            if browser:browser.idle(game_run)
            print(f'Game {game_run} parked with {frame_count} frames; RTEMS and DMA ownership retained',flush=True)
            idle_started=time.monotonic()
            while not a.restart_cycles and not signal_stop.is_set() and not (browser and browser.restart.is_set()):
                pump_heartbeat();ownercheck(owned)
                page=snap(0xc000e000)
                need(struct.unpack_from('<I',page,0xb58)[0]==0 and status('ram-admit').get('done')=='0','idle owner fault')
                time.sleep(.1)
            if signal_stop.is_set():break
            rearmed=transact(8,game_run,struct.pack('<4I',global_frames,request_seq,game_run+1,global_key))
            need(rearmed[12:14]==(0,0) and rearmed[11]==0,'fresh admission gate')
            save(run/'rearm.json',dict(next_run=game_run+1,discarded_key=struct.unpack_from('<I',snap(0xc000e000),0xbdc)[0],idle_seconds=time.monotonic()-idle_started))
            game_run+=1
            # Original data + zero BSS + original relocation words, never the retired image.
            for off in range(0,len(admission),PAGE):transact(1,off,admission[off:off+PAGE])
            admitted_words=transact(4)
            need(admitted_words[12]==1 and admitted_words[14]==claim[7]+engine_manifest['entry'],'fresh relocated admission')
            transact(2,0,wad[:512])
        run=boot_run
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
        dma_state=struct.unpack_from('<32I',page,0xd80)
        need(dma_state[:3]==(0x31464d44,0x161610e1,0) and dma_state[11]==global_frames and dma_state[14:16]==(0,0),'all DMA sources drained before STOP')
        need(fields(pin_dir/'status')['guard_changes']=='0','final two-buffer guards')
        (run/'dma-pin-final.txt').write_text((pin_dir/'status').read_text())
        runtime_audit('quiescent',1)
        quiescent=True
        need(struct.unpack_from('<16I',page,0xb00)==bank,
             'full-bank audit retained')
        need(snap(0xc0384000)[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
             'grant ownership retained')
        need(require_unbound_or_absent(OLD,'dac960pg')['driver'] is None,'old card untouched')
        final_bridge=struct.unpack_from('<20I',page,0xb80)
        need(final_bridge[18:20]==(38+total_reads,4),
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
            reusable=a.reusable,games=games,persistent=a.persistent,frames=global_frames,stop_reason=stop_reason or 'engine quit',
            key_sequence_sent=key_out_seq,key_sequence_acked=struct.unpack_from('<I',page,0xd30)[0],
            engine_wad_reads=read_count,
            engine_elapsed_seconds=time.monotonic()-began_engine,
            game_frame_sha256=sha(game_frame),
            game_frame_fnv=f'0x{fnv(game_frame):08x}',
            frame_timing=frame_timing,dma_frames=dma_state[11],paired_frames=a.paired_frames,card_fnv_mode=a.card_fnv,
            dma_module_sha256=sha(a.dma_module.read_bytes()),
            engine_report=[f'0x{x:08x}' for x in er],
            engine_results=[f'0x{x:08x}' for x in result_words],
            heartbeat_before=first,heartbeat_after=heart[4],
            release='reboot-only',grant_retained=True,
            card=select(BDF,'accele160'),old=require_unbound_or_absent(OLD,'dac960pg')))
        print(f'Real Doom {frame_count}-frame run captured; WAD, cleanup and STOP passed')
    except BaseException as error:
        if active_owner and not quiescent:
            try:
                write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))
                started=time.monotonic()
                while time.monotonic()-started<20:
                    page=snap(0xc000e000)
                    if struct.unpack_from('<I',page,0xb54)[0]==0x45495551:
                        break
                    time.sleep(.01)
                (a.out/'persist'/'failure-stop-page.bin').write_bytes(page)
                save(a.out/'persist'/'failure-stop.json',dict(
                    error=repr(error),quiescent=struct.unpack_from('<I',page,0xb54)[0]==0x45495551,
                    status=status('ram-admit')))
            except Exception as stop_error:
                save(a.out/'persist'/'failure-stop.json',dict(
                    error=repr(error),stop_error=repr(stop_error)))
        raise
    finally:
        if service:service.close()
        if control_file and control_file.exists():
            try:
                if json.loads(control_file.read_text()).get('pid')==os.getpid():control_file.unlink()
            except (ValueError,OSError):pass
        if browser:browser.close()
        translate(original);bar.close();res.close();cfg.close()

if __name__=='__main__':main()
