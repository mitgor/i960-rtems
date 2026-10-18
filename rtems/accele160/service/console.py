#!/usr/bin/env python3
"""RTEMS prompt via the sole host owner. Run on Linux through ssh -t."""
import argparse,socket,sys

def request(path,command):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(7);s.connect(path);s.sendall((command+'\n').encode('ascii'))
        data=b''
        while True:
            part=s.recv(1024)
            if not part:break
            data+=part
            if len(data)>4096:raise ValueError('oversized supervisor reply')
        return data.decode('ascii')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--socket',default='/run/i960-rtems-console.sock')
    p.add_argument('command',nargs='?');a=p.parse_args()
    if a.command:
        try:print(request(a.socket,a.command),end='')
        except (OSError,ValueError) as e:
            print('console:',e,file=sys.stderr);return 1
        return 0
    print('AcceleRAID RTEMS diagnostic prompt (help; quit disconnects)')
    while True:
        try:line=input('rtems> ').strip()
        except (EOFError,KeyboardInterrupt):print();return
        if line in ('quit','exit'):return
        if not line:continue
        try:print(request(a.socket,line),end='')
        except (OSError,ValueError) as e:print('console:',e)
if __name__=='__main__':raise SystemExit(main())
