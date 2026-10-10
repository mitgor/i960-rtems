#!/usr/bin/env python3
"""Explicit hardware tests for clean SIGTERM, SIGKILL journal cleanup and fatal exit.

Runs on Linux as root. Uses actual RAM payloads and temporary TUN/NAT routing.
Requires exclusive ownership of the card; use a new output directory.
"""
import argparse,errno,json,os,signal,struct,subprocess,sys,time
from pathlib import Path
from run import Board,DBG,verify_close
HERE=Path(__file__).resolve().parent

def wait_for(predicate,timeout):
 end=time.monotonic()+timeout
 while not predicate():
  if time.monotonic()>end:raise TimeoutError('live test condition not reached')
  time.sleep(.1)

def clean_host():
 assert not Path('/sys/module/dac960rtems').exists()
 assert not Path('/sys/class/net/i960rt0').exists()
 assert 'i960rt0' not in subprocess.check_output(['iptables-save'],text=True)
 assert not Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert os.geteuid()==0;a.output.mkdir(exist_ok=False)
 forward=Path('/proc/sys/net/ipv4/ip_forward').read_text();report={}
 for name,sig in [('sigterm',signal.SIGTERM),('sigkill',signal.SIGKILL)]:
  out=a.output/name
  with (a.output/(name+'.log')).open('w') as log:
   proc=subprocess.Popen([sys.executable,str(HERE/'relay.py'),'--payload',str(a.payload),'--module',str(a.module),'--output',str(out),'--duration','120','--internet'],stdout=log,stderr=subprocess.STDOUT)
   try:
    wait_for(lambda:(out/'local-network.json').exists() or proc.poll() is not None,30)
    assert proc.poll() is None,'relay failed before signal';time.sleep(1)
    proc.send_signal(sig);code=proc.wait(timeout=40)
   finally:
    if proc.poll() is None:proc.terminate();proc.wait(timeout=30)
  if sig==signal.SIGKILL:
   assert code==-signal.SIGKILL
   wait_for(lambda:DBG.exists() and 'SESSION CLOSE rc=0 pending=0 exec-dirty=0 stage-dirty=0' in (DBG/'result.txt').read_text(),10)
   subprocess.run([sys.executable,str(HERE/'cleanup.py'),str(out)],check=True)
   verify_close(out/'after-kill-close')
  else:
   assert code!=0;verify_close(out/'close')
   assert json.loads((out/'cleanup.json').read_text())['errors']==[]
  clean_host();assert Path('/proc/sys/net/ipv4/ip_forward').read_text()==forward
  report[name]=dict(exit_code=code,restored=True,unloaded=True,network_restored=True)
  print(name,'passed',flush=True)
 board=Board(a.payload,a.module,a.output/'invalid-operation')
 try:
  try:board.step(struct.pack('<4I',0x314d5452,99,0,0))
  except OSError as exc:
   assert exc.errno==errno.ENODATA,exc
   # The outer runner preserves the explicit fatal code for diagnosis.
   data=(a.output/'invalid-operation/failure-000001/dram-hook-a5.bin').read_bytes()
   assert struct.pack('<I',0xf0050002) in data,data.hex()
   report['invalid_operation']=dict(errno=exc.errno,fatal='F0050002',rejected=True)
  else:raise AssertionError('invalid operation accepted')
 finally:report['invalid_operation_close']=board.close()
 clean_host();(a.output/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
