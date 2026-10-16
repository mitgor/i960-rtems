#!/usr/bin/env python3
import gzip,hashlib,json,subprocess,time
from pathlib import Path
r=Path(__file__).resolve().parent;host='mit@192.168.2.75';remote='/home/mit/i960-divplay-20261016'
for i in range(20):
 x=subprocess.run(['ssh','-o','ConnectTimeout=5',host,'cat /proc/sys/kernel/random/boot_id'],capture_output=True,text=True)
 if not x.returncode:break
 time.sleep(20)
else:raise RuntimeError('Host did not return')
boot=x.stdout.strip();print('Host returned',boot,flush=True)
x=subprocess.run(['ssh',host,'bash '+remote+'/restore.sh'],check=True,capture_output=True,text=True)
(r/'restore-launch.log').write_text(x.stdout+x.stderr)
url='http://[2a02:8106:40:9000:f662:19ee:dbad:1f1e]:8080/'
for i in range(30):
 x=subprocess.run(['curl','-g','--noproxy','*','--max-time','10','-sS','-D',str(r/'restored-http-headers.txt'),'-o',str(r/'restored-http-body.html'),'-w','%{http_code}',url],capture_output=True,text=True)
 if x.returncode==0 and x.stdout=='200':break
 time.sleep(10)
else:raise RuntimeError('Public HTTP did not become healthy')
raw=(r/'restored-http-headers.txt').read_bytes()
(r/'restored-http-headers.raw.gz').write_bytes(gzip.compress(raw,mtime=0))
(r/'restored-http-headers.txt').write_text(raw.decode().replace('\r\n','\n').rstrip()+'\n')
(r/'restoration.json').write_text(json.dumps(dict(boot_id=boot,url=url,http_status=200,body_bytes=(r/'restored-http-body.html').stat().st_size,body_sha256=hashlib.sha256((r/'restored-http-body.html').read_bytes()).hexdigest()),indent=2)+'\n')
print('Public IPv6 HTTP200 restored',flush=True)
