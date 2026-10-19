#!/usr/bin/env python3
"""Bounded TUN-to-owner relay. Local routing only; no NAT or firewall changes.
Configure externally: ip addr add 10.196.0.1/30 dev accele0;
 ip -6 addr add fd96:196:960::1/64 dev accele0; ip link set accele0 mtu 1500 up.
"""
import argparse,os,fcntl,struct,select,time,json
from client import Client
p=argparse.ArgumentParser();p.add_argument('--name',default='accele0');p.add_argument('--seconds',type=float,default=0);a=p.parse_args()
if not 0<=a.seconds<=28800:raise SystemExit('duration 0 (service lifetime) or up to 28800 seconds required')
fd=os.open('/dev/net/tun',os.O_RDWR|os.O_NONBLOCK)
fcntl.ioctl(fd,0x400454ca,struct.pack('16sH',a.name.encode(),0x1001))
c=Client();end=time.monotonic()+a.seconds if a.seconds else float('inf');rx=tx=drops=0
try:
 while time.monotonic()<end:
  ready,_,_=select.select([fd],[],[],.02);packet=b''
  if ready:
   try:packet=os.read(fd,1501)
   except BlockingIOError:pass
  if len(packet)>1500:drops+=1;continue
  result=c.call(5,packet);rx+=bool(packet);data=bytes.fromhex(result['data'])
  while data:
   if len(data)<4:raise RuntimeError('short packet framing')
   n=struct.unpack_from('<I',data)[0]
   if not 0<n<=1500 or len(data)<4+n:raise RuntimeError('packet bounds')
   try:
    if os.write(fd,data[4:4+n])!=n:raise RuntimeError('partial TUN packet')
    tx+=1
   except BlockingIOError:drops+=1
   data=data[4+n:]
finally:
 os.close(fd);print(json.dumps(dict(rx=rx,tx=tx,host_drops=drops)))
