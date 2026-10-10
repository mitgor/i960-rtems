from pathlib import Path
import subprocess, re, datetime, hashlib, json
root=Path('/home/mit/i960-analysis.7jVBmy')
out=root/('snapshot-fresh-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir()
def run(*a):return subprocess.check_output(a)
assert not Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists()
assert not Path('/sys/module/dac960dump').exists()
(out/'boot-id.txt').write_text(Path('/proc/sys/kernel/random/boot_id').read_text())
images=[bytearray(),bytearray()]
for off in range(0,0x80000,0xf000):
 n=min(0xf000,0x80000-off); d=out/f'{off:05x}';d.mkdir()
 run('sudo','-n','insmod',str(root/'dump/dac960dump.ko'),'attempt=1',f'length={n}',f'flash_offset={off}')
 for name in ['result.txt','enquiry-before.bin','read-a5.bin','read-5a.bin','enquiry-after.bin']:
  (d/name).write_bytes(run('sudo','-n','cat','/sys/kernel/debug/dac960dump/'+name))
 s=(d/'result.txt').read_text(); print(s,flush=True)
 assert 'experiment-result=0 pending=0' in s
 matches=re.findall(r'complete op=(\w+) id=(\w+) status=(\w+) changed=\d+ guard-changed=(\d+)',s)
 assert matches==[('1c','0001','0000','0'),('20','0002','0000','0'),('20','0003','0000','0'),('1c','0004','0000','0')],matches
 a=(d/'read-a5.bin').read_bytes();b=(d/'read-5a.bin').read_bytes();assert len(a)==len(b)==n and a==b
 run('sudo','-n','rmmod','dac960dump');images[0]+=a;images[1]+=b
for i,a in enumerate(images): (out/f'image-window-{i}.bin').write_bytes(a)
a=images[0]; b=(root/'prl29/Fgj40729.img.raw').read_bytes()
print('OUTPUT',out,'SHA256',hashlib.sha256(a).hexdigest(),'FW_OFFSET',a.find(b[:32]),'ZIP_OFFSET',a.find(b'PK\x03\x04'),flush=True)
