#!/usr/bin/env python3
"""Resume an already retained AcceleRAID Doom bridge after host-only failure."""
from run_bridge import *

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('template','relocations','wad','out'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    need(status('ram-admit').get('done')=='0' and
         status('ram-admit').get('started')=='1','no retained bridge')
    need(select(BDF,'accele160')['driver']=='myrsread' and
         select(OLD,'dac960pg')['driver'] is None,'card selection')
    run=a.out/'persist'
    cur=(run/'ready-page.bin').read_bytes()
    owned=(a.out/'owner-reserved.bin').read_bytes()
    def pattern(index,word):
        return 0x7e960160^(index*0x85ebca6b&0xffffffff)^(word*0xc2b2ae35&0xffffffff)
    cfg=(DEVICE/'config').open('r+b',buffering=0)
    res=(DEVICE/'resource0').open('r+b',buffering=0)
    bar=mmap.mmap(res.fileno(),2*PAGE)
    cfg.seek(0x44);original=struct.unpack('<I',cfg.read(4))[0]
    need(original==0xc0000000,'PIATVR')
    def translate(addr):
        cfg.seek(0x44);cfg.write(struct.pack('<I',addr));cfg.seek(0x44)
        need(struct.unpack('<I',cfg.read(4))[0]==addr,'PIATVR readback')
    def snap(addr):
        translate(addr);return bytes(bar[PAGE:2*PAGE])
    def write(addr,off,data):
        translate(addr);bar[PAGE+off:PAGE+off+len(data)]=data
        need(bytes(bar[PAGE+off:PAGE+off+len(data)])==data,'PCI writeback')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    try:
        live=snap(0xc000e000)
        need(live[0xb00:0xb40]==cur[0xb00:0xb40] and
             live[0xb80:0xbd0]==cur[0xb80:0xbd0] and
             live[0xb40:0xb50]==cur[0xb40:0xb50],
             'retained bank/claim/bridge changed since capture')
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
