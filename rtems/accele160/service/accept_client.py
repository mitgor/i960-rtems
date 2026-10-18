#!/usr/bin/env python3
"""Exercise only the supervisor socket, including abandoned/slow clients."""
import argparse,json,socket,time
from pathlib import Path
from console import request
p=argparse.ArgumentParser();p.add_argument('--socket',default='/run/i960-rtems-console.sock');p.add_argument('--seconds',type=int,default=160);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
rows=[];end=time.monotonic()+a.seconds
for command in ('help','version','uptime','tasks','mem','apps','stats','unknown','x'*129):
    start=time.monotonic()
    try:text=request(a.socket,command)
    except OSError as e:
        rows.append(dict(command=command,error=str(e)));a.out.write_text(json.dumps(rows,indent=2)+'\n');raise
    rows.append(dict(command=command,seconds=time.monotonic()-start,text=text))
    assert ('error:' in text)==(command=='unknown' or len(command)>128)
# Abandoned incomplete request and abandoned complete request cannot stop owner.
for payload in (b'par',b'uptime\n'):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:s.connect(a.socket);s.sendall(payload)
# Slow clients consume only fixed slots, then expire without blocking PCI service.
slow=[]
for _ in range(8):
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.connect(a.socket);s.sendall(b'p');slow.append(s);time.sleep(.03)
time.sleep(5.5)
for s in slow:s.close()
while time.monotonic()<end:
    for command in ('uptime','apps','stats','tasks'):
        start=time.monotonic()
        try:text=request(a.socket,command)
        except OSError as e:rows.append(dict(error=str(e)));break
        rows.append(dict(command=command,seconds=time.monotonic()-start,text=text))
    a.out.write_text(json.dumps(rows,indent=2)+'\n');time.sleep(.5)
a.out.write_text(json.dumps(rows,indent=2)+'\n')
print('client exchanges',len(rows))
