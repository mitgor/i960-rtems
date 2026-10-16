#!/usr/bin/env python3
"""Reject a bad digest or page count within one retained AcceleRAID 160 grant."""
import argparse
import fcntl
import hashlib
import json
import mmap
from pathlib import Path
import struct
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'rtems/transport'))
from card_select import select

BDF = '0000:37:09.1'
OLD = '0000:37:04.1'
IMAGE_SHA = '665cb1210ed92b373b43d1a126cc547860cd58c0e95a9905f26f697005c708a0'
MODULE_SHA = {'reserve': 'd5dc1cf2dddba559ea4ff5ebf7bac1ae32f462f27dd968b8964f0cd20b47c945',
              'release': 'bbfbe079b86ba1503efcfcce4c0c7ee5e1ad2fc662ded669766bdb7d38a3ecfa',
              'copy': '6dd7dc40be4c51e65dce65978b3fdda3256e54928034d7acfe451a946caf1ec6',
              'digest': 'db97abc60007d96017c4aaed6f86f5f155988b2948993f2f5b3f81cc964ad6b1'}
DBG = Path('/sys/kernel/debug')
DEVICE = Path('/sys/bus/pci/devices') / BDF
PAGE = 4096


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok: raise RuntimeError(message)


def fields(path):
    return dict(w.split('=', 1) for w in path.read_text().split())


def fnv(data):
    value = 0x811c9dc5
    for byte in data: value = ((value ^ byte) * 0x01000193) & 0xffffffff
    return value


def status(name):
    return fields(DBG / f'accele-{name}/status')


def module_start(name, out, expected_status=0):
    need(status(name).get('started') == '0', f'{name} already started')
    (DBG / f'accele-{name}/start').write_text('probe\n')
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        s = status(name)
        if s.get('done') == '1': break
        time.sleep(.05)
    out.write_text((DBG / f'accele-{name}/status').read_text())
    need(s.get('done') == '1' and s.get('status') == str(expected_status) and s.get('residual') == '0', f'{name} pending or failed; retain resources')
    return s


def module_release(name):
    (DBG / f'accele-{name}/release').write_text('release\n')
    need(status(name).get('released') == '1', f'{name} companion release failed')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('reserve_module','release_module','copy_module','digest_module','image','readback0','readback1','out'):
        p.add_argument('--' + key.replace('_','-'), type=Path, required=True)
    p.add_argument("--mode", choices=("bad-hash", "bad-count"), required=True)
    a = p.parse_args()
    lock = open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    need(sha(a.image) == IMAGE_SHA, 'wrong firmware image')
    for name in MODULE_SHA:
        need(sha(getattr(a, name + '_module')) == MODULE_SHA[name], f'wrong {name} module')
        need(not (DBG / f'accele-{name}').exists() and not Path('/sys/module',name+'_command').exists(), f'{name} already present')
    card = select(BDF,'accele160',driver='myrsread'); old = select(OLD,'dac960pg')
    need(old['driver'] is None, 'old card bound')
    need(not list(DEVICE.glob('host*/target*/*/block/*')), 'block device present')
    host, = DEVICE.glob('host*/scsi_host/host*')
    need((host/'stock_descriptor').read_text().startswith('state=0 '), 'descriptor active')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for rd in (a.readback0,a.readback1):
        request = json.loads((rd/'request.json').read_text()); result=json.loads((rd/'result.json').read_text())
        state=fields(rd/'status.txt')
        need(request['boot_id']==boot and result['sha256']==IMAGE_SHA and sha(rd/'data.bin')==IMAGE_SHA and
             result['card_after']==card and result['old_after']==old and
             all(state.get(x)=='0' for x in ('status','residual','guard_changes')), 'paired flash audit')
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'preflight.json').write_text(json.dumps(dict(boot_id=boot,card=card,old_card=old,
        image_sha256=IMAGE_SHA,module_sha256=MODULE_SHA,readbacks=[str(a.readback0),str(a.readback1)]),indent=2)+'\n')
    cfg=(DEVICE/'config').open('r+b',buffering=0); res=(DEVICE/'resource0').open('r+b',buffering=0)
    bar=mmap.mmap(res.fileno(),PAGE*2)
    cfg.seek(0x44); original=struct.unpack('<I',cfg.read(4))[0]
    need(original==0xc0000000,'PIATVR unexpected')
    def translate(addr):
        cfg.seek(0x44);cfg.write(struct.pack('<I',addr));cfg.seek(0x44)
        need(struct.unpack('<I',cfg.read(4))[0]==addr,'PIATVR readback')
    def snap(addr):
        translate(addr);return bytes(bar[PAGE:2*PAGE])
    def write(addr,offset,data):
        translate(addr);bar[PAGE+offset:PAGE+offset+len(data)]=data
        need(bytes(bar[PAGE+offset:PAGE+offset+len(data)])==data,'MMIO readback')
    try:
        tb=snap(0xc0384000);(a.out/'table-before.bin').write_bytes(tb)
        before=snap(0xc000e000);(a.out/'page-before.bin').write_bytes(before)
        need(before==b'\xff'*PAGE,'loader page not erased')
        write(0xc000e000,0x820,b'\xa5'*16)
        translate(original)
        subprocess.run(['insmod',str(a.reserve_module),'bdf='+BDF],check=True)
        subprocess.run(['insmod',str(a.release_module),'bdf='+BDF],check=True)
        subprocess.run(['insmod',str(a.copy_module),'bdf='+BDF],check=True)
        subprocess.run(['insmod',str(a.digest_module),'bdf='+BDF],check=True)
        module_start('reserve',a.out/'reserve-status.txt')
        reserved=snap(0xc000e000);(a.out/'page-reserved.bin').write_bytes(reserved)
        ptr=struct.unpack_from('<I',reserved,0x828)[0]
        need(ptr==0xc0710000 and struct.unpack_from('<4I',reserved,0x840)==(0x56525352,ptr,0x80000,0x96016004),'grant record')
        tr=snap(0xc0384000);(a.out/'table-reserved.bin').write_bytes(tr)
        first=(ptr-0xc0000000)//0x8000
        for i in range(256):
            bc,bo=struct.unpack_from('<I',tb,0x2a0+i*4)[0],struct.unpack_from('<I',tb,0x6a0+i*4)[0]
            rc,ro=struct.unpack_from('<I',tr,0x2a0+i*4)[0],struct.unpack_from('<I',tr,0x6a0+i*4)[0]
            need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo)),'grant metadata')
            if first<=i<first+16: need((bc,bo)==(0,0),'grant overlap')
        write(0xc000e000,0x820,before[0x820:0x830]);translate(original)
        module_release('reserve')
        stage_addr=ptr+0x7e000;stage_before=snap(stage_addr);(a.out/'staging-before.bin').write_bytes(stage_before)
        for ordinal,index in enumerate((0,1)):
            pattern=bytes(((i*53+0x96+index)^(i>>3))&0xff for i in range(PAGE))
            digest=fnv(pattern)
            write(stage_addr,0,pattern)
            stage_readback=snap(stage_addr);(a.out/f'staging-{index}-readback.bin').write_bytes(stage_readback)
            need(stage_readback==pattern,'stage readback')
            control=struct.pack('<4I',0x59504f43,0x16161061,index,digest)
            write(0xc000e000,0x860,control)
            write(0xc000e000,0x820,b'\xa5'*16)
            translate(original)
            module_start('copy',a.out/f'copy-{index}-status.txt')
            result=snap(0xc000e000)
            (a.out/f'copy-{index}-page.bin').write_bytes(result)
            need(struct.unpack_from('<4I',result,0x820)==(0x59504f43,0x16161061,index,digest),'copy digest')
            need(result[0x860:0x870]==control,'copy control')
            need(result[:0x820]==reserved[:0x820] and result[0x830:0x860]==reserved[0x830:0x860] and result[0x870:]==reserved[0x870:],'loader page drift')
            write(0xc000e000,0x860,before[0x860:0x870]);write(0xc000e000,0x820,before[0x820:0x830])
            need(snap(0xc0384000)[0x2a0:0xaa0]==tr[0x2a0:0xaa0],'owner drift')
            translate(original);module_release('copy')
            if ordinal==0:
                subprocess.run(['rmmod','copy_command'],check=True)
                subprocess.run(['insmod',str(a.copy_module),'bdf='+BDF],check=True)
        write(stage_addr,0,stage_before)
        stage_restored=snap(stage_addr);(a.out/'staging-restored.bin').write_bytes(stage_restored)
        need(stage_restored==stage_before,'stage restoration')
        image = b''.join(bytes(((i*53+0x96+index)^(i>>3))&0xff for i in range(PAGE)) for index in (0,1))
        whole_hash = fnv(image)
        digest_count = 2 if a.mode == 'bad-hash' else 128
        requested_hash = whole_hash ^ 1 if a.mode == 'bad-hash' else whole_hash
        target_before=snap(ptr);(a.out/'target-before-digest.bin').write_bytes(target_before)
        need(target_before == image[PAGE:2*PAGE], 'independent odd page-1 readback')
        hash_control = struct.pack('<4I',0x48534148,0x16161071,digest_count,requested_hash)
        write(0xc000e000,0x870,hash_control)
        write(0xc000e000,0x830,b'\xa5'*16)
        translate(original)
        module_start('digest',a.out/'digest-status.txt',expected_status=2)
        hash_page=snap(0xc000e000);(a.out/'digest-page.bin').write_bytes(hash_page)
        need(hash_page[0x830:0x840] == b'\xa5'*16, 'rejected digest modified result')
        need(hash_page[0x870:0x880]==hash_control,'digest control')
        expected_hash_page=bytearray(reserved)
        expected_hash_page[0x820:0x830]=before[0x820:0x830]
        expected_hash_page[0x830:0x840]=b'\xa5'*16
        expected_hash_page[0x870:0x880]=hash_control
        need(hash_page==expected_hash_page,'rejected digest changed loader page outside records')
        target_after=snap(ptr);(a.out/'target-after-digest.bin').write_bytes(target_after)
        need(target_after == target_before, 'rejected digest modified page 1')
        write(0xc000e000,0x870,before[0x870:0x880])
        write(0xc000e000,0x830,before[0x830:0x840])
        translate(original);module_release('digest')
        subprocess.run(['rmmod','digest_command'],check=True)
        need(snap(0xc0384000)[0x2a0:0xaa0]==tr[0x2a0:0xaa0],'owner drift after copies')
        write(0xc000e000,0x820,b'\xa5'*16);translate(original)
        module_start('release',a.out/'release-status.txt')
        after=snap(0xc000e000);(a.out/'page-after.bin').write_bytes(after)
        need(struct.unpack_from('<4I',after,0x820)==(0x45455246,0x16161051,ptr,0x80000),'release result')
        ta=snap(0xc0384000);(a.out/'table-after.bin').write_bytes(ta)
        need(tb[0x2a0:0xaa0]==ta[0x2a0:0xaa0],'metadata restoration')
        write(0xc000e000,0x820,before[0x820:0x830])
        page_restored=snap(0xc000e000);(a.out/'page-restored.bin').write_bytes(page_restored)
        need(page_restored==before,'loader page restoration')
        translate(original);module_release('release')
        for name in ('copy','release','reserve'):
            subprocess.run(['rmmod',name+'_command'],check=True)
        (a.out/'result.json').write_text(json.dumps(dict(pointer=f'0x{ptr:08x}',indexes=[0,1],mode=a.mode,digest_rejected=True,
          checksums=[f'0x{fnv(bytes(((i*53+0x96+index)^(i>>3))&0xff for i in range(PAGE))):08x}' for index in (0,1)],whole_digest=f'0x{whole_hash:08x}',
          metadata_restored=True,loader_page_restored=True,staging_restored=True,
          card_after=select(BDF,'accele160'),old_after=select(OLD,'dac960pg')),indent=2)+'\n')
        print(f'owned_image_digest={a.mode} rejected=1 target_unchanged=1 owner_restored=1 stage_restored=1 page_restored=1')
    finally:
        translate(original);bar.close();res.close();cfg.close()


if __name__=='__main__':
    main()
