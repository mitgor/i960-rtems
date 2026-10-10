#!/usr/bin/env python3
"""Explicit hardware test of the foreground RTEMS service mode and TCP reuse."""
import argparse,hashlib,json,socket,subprocess,sys,time
from pathlib import Path
from live_cleanup_test import wait_for,clean_host
from run import verify_close
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 a.output.mkdir(exist_ok=False);out=a.output/'relay';records=[]
 with (a.output/'relay.log').open('w') as log:
  proc=subprocess.Popen([sys.executable,str(HERE/'relay.py'),'--payload',str(a.payload),'--module',str(a.module),'--output',str(out),'--serve','15'],stdout=log,stderr=subprocess.STDOUT)
  try:
   wait_for(lambda:(out/'serve-start.json').exists() or proc.poll() is not None,30);assert proc.poll() is None
   for index in range(12):
    payload=('RTEMS service connection %02d\n'%index).encode()*8
    with socket.create_connection(('10.196.0.2',9600),timeout=5) as s:
     s.settimeout(5);s.sendall(payload);reply=bytearray()
     while len(reply)<len(payload):
      chunk=s.recv(4096);assert chunk;reply+=chunk
     assert reply==payload
    records.append(dict(connection=index,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest()))
   with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
    s.settimeout(5);payload=b'RTEMS service UDP '*50;s.sendto(payload,('10.196.0.2',9601));reply,source=s.recvfrom(4096);assert reply==payload and source==('10.196.0.2',9601)
   assert proc.wait(timeout=30)==0
  finally:
   if proc.poll() is None:proc.terminate();proc.wait(timeout=30)
 verify_close(out/'close');clean_host()
 (a.output/'service-test.json').write_text(json.dumps(dict(valid=True,tcp_connections=records,udp_bytes=len(payload),restored=True,unloaded=True),indent=2)+'\n')
 print('RTEMS serve: 12 sequential TCP connections and UDP passed; restored and unloaded.',flush=True)
if __name__=='__main__':main()
