#!/usr/bin/env python3
"""Explicit real-SSH PTY test. Keys are sent to the same client used by a human."""
import argparse,errno,fcntl,gzip,json,os,pty,re,select,signal,struct,subprocess,termios,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=15);p.add_argument('--name',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--disconnect',action='store_true');p.add_argument('--ctrl-c',action='store_true');p.add_argument('--resize',action='store_true');p.add_argument('--launcher',action='store_true');a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.name) or a.seconds<=0:raise ValueError('invalid test name/duration')
    a.output.mkdir(parents=True)
    master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',24,80,0,0))
    command=f'cd /home/mit/i960-tetris-t4 && before=$(stty -g); sudo -n python3 terminal.py --payload /home/mit/i960-tetris-t2/loader/runtime/tetris_payload.bin --module /home/mit/i960-session-t5/dac960session.ko --output /home/mit/i960-tetris-t4/{a.name}; result=$?; if [ "$(stty -g)" = "$before" ]; then echo TTY_RESTORED; else echo TTY_CHANGED; fi; exit "$result"'
    if a.launcher:
        command=command.replace('sudo -n python3 terminal.py --payload /home/mit/i960-tetris-t2/loader/runtime/tetris_payload.bin --module /home/mit/i960-session-t5/dac960session.ko', '/home/mit/i960-tetris-t4/play.sh')
    proc=subprocess.Popen(['ssh','-tt','-o','BatchMode=yes','-o','ServerAliveInterval=10','mit@192.168.2.75',command],stdin=slave,stdout=slave,stderr=slave,start_new_session=True)
    os.close(slave);started=time.monotonic();ready=None;lastkey=0;index=0;sentquit=False;tail=b'';events=[];lastreport=0
    resized=False;expanded=False
    keys=[b'a',b'd',b'w',b's',b'\x1b[D',b'\x1b[C',b'\x1b[A',b'\x1b[B',b' ']
    with gzip.open(a.output/'terminal.bin.gz','wb',compresslevel=1) as transcript:
        while proc.poll() is None:
            now=time.monotonic()
            if now-started>a.seconds+30:proc.kill();raise RuntimeError('SSH client timeout')
            readable,_,_=select.select([master],[],[],.025)
            if readable:
                try:data=os.read(master,65536)
                except OSError as e:
                    if e.errno==errno.EIO:break
                    raise
                if not data:break
                transcript.write(data);tail=(tail+data)[-16384:]
                if ready is None and b'i960 card' in tail:ready=time.monotonic();print('READY',a.name,flush=True)
            if ready is not None:
                elapsed=now-ready
                if a.resize and elapsed>=2 and not resized:
                    fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',12,40,0,0));os.kill(proc.pid,signal.SIGWINCH)
                    events.append(dict(at=elapsed,action='resize-40x12'));resized=True
                if a.resize and elapsed>=4 and not expanded:
                    fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',24,80,0,0));os.kill(proc.pid,signal.SIGWINCH)
                    events.append(dict(at=elapsed,action='resize-80x24'));expanded=True
                if elapsed>=a.seconds and not sentquit:
                    if a.disconnect:proc.kill();events.append(dict(at=elapsed,action='ssh-process-killed'));break
                    data=b'\x03' if a.ctrl_c else b'q';os.write(master,data);sentquit=True;events.append(dict(at=elapsed,key=data.hex()))
                elif not sentquit and now-lastkey>=.25:
                    if index%100==99:data=b'r'
                    elif index==12:data=b'a'*128 # exercise bounded queue overflow
                    else:data=keys[index%len(keys)]
                    os.write(master,data);events.append(dict(at=elapsed,key=data.hex()));index+=1;lastkey=now
                if elapsed-lastreport>=60:print('RUNNING',a.name,round(elapsed),flush=True);lastreport=elapsed
        code=proc.wait(timeout=15)
        # Collect final shell/TTY-restoration text even if SSH exited just before
        # the loop polled it; do not mistake buffered output for missing cleanup.
        while select.select([master],[],[],0)[0]:
            try:data=os.read(master,65536)
            except OSError as e:
                if e.errno==errno.EIO:break
                raise
            if not data:break
            transcript.write(data);tail=(tail+data)[-16384:]
    os.close(master)
    summary=dict(name=a.name,exit_code=code,ready=ready is not None,elapsed_s=time.monotonic()-started,tty_restored=b'TTY_RESTORED' in tail,disconnected=a.disconnect,events=events)
    (a.output/'ssh-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    if not a.disconnect:
        assert code==0 and summary['tty_restored'],tail.decode(errors='replace')
    print('DONE',a.name,code,flush=True)
if __name__=='__main__':main()
