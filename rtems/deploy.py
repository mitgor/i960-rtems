#!/usr/bin/env python3
"""Install sources and build RAM-session artifacts on the Linux build host.

Does not load a module, run on the card, reboot, or change networking.
Use a NEW destination; installed toolchain defaults to /home/mit/i960/tools/bin.
"""
import argparse,shlex,subprocess,tarfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--host',default='mit@192.168.2.75');p.add_argument('--destination',required=True);p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');a=p.parse_args()
 dest=a.destination
 if not dest.startswith('/') or dest=='/':raise ValueError('absolute dedicated destination required')
 def ssh(command):subprocess.run(['ssh','-o','BatchMode=yes',a.host,command],check=True)
 q=shlex.quote;ssh('mkdir '+q(dest))
 with tempfile.TemporaryDirectory() as tmp:
  archive=Path(tmp)/'project.tar'
  def filter_tar(info):return None if '__pycache__' in info.name.split('/') or Path(info.name).name.startswith('._') or Path(info.name).name=='.DS_Store' or info.name.endswith(('.pyc','.o','.elf','.ko')) else info
  with tarfile.open(archive,'w') as t:
   for rel in ['rtems','host/dump','host/loadrun','host/session','loader/runtime','artifacts/software-loader-20261010/target/runner.bin']:
    t.add(ROOT/rel,arcname='project/'+rel,filter=filter_tar)
   for path in sorted((ROOT/'artifacts/rtems-20261011/sources').iterdir()):
    if path.suffix in ('.bz2','.gz','.diff'):t.add(path,arcname='sources/'+path.name)
  with archive.open('rb') as f:subprocess.run(['ssh','-o','BatchMode=yes',a.host,'tar -xf - -C '+q(dest)],stdin=f,check=True)
 ssh('python3 '+q(dest+'/project/rtems/build.py')+' --work '+q(dest)+' --cross '+q(a.cross)+' --profile net > '+q(dest+'/build.log')+' 2>&1')
 ssh('python3 '+q(dest+'/project/rtems/transport/build.py')+' --out '+q(dest+'/module'))
 ssh('make -C /lib/modules/$(uname -r)/build M='+q(dest+'/module')+' modules > '+q(dest+'/module-build.log')+' 2>&1')
 subprocess.run(['scp',str(ROOT/'rtems/serve.sh'),a.host+':'+dest+'/serve.sh'],check=True)
 ssh('chmod 755 '+q(dest+'/serve.sh'))
 print('Built:',dest+'/net/kernel.bin','and',dest+'/module/dac960rtems.ko')
if __name__=='__main__':main()
