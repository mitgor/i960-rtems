#!/usr/bin/env python3
"""Play card-executed Tetris in an SSH terminal; Linux handles input/display only."""
import argparse,collections,fcntl,gzip,hashlib,json,os,select,signal,struct,subprocess,sys,termios,time,tty
from pathlib import Path
from session import Session,bio
from tetris_wire import request,split
from live_test import capture,DBG
from validate import verify_close
from tetris_replay import stats
PERIOD=50_000_000
TRACE=struct.Struct('<QQQ256s2160s') # start since loop, call duration, lateness, request, response

class Keys:
    """Incremental CSI/SS3 decoding; bounded queue, urgent quit, no escape injection."""
    def __init__(self):
        self.queue=collections.deque();self.escape=b'';self.escape_at=0
        self.dropped=0;self.quit=False;self.interrupt=False
    def feed(self,data,now):
        if self.escape and now-self.escape_at>100_000_000:self.escape=b''
        for c in data:
            if self.escape:
                self.escape+=bytes([c])
                if self.escape in (b'\x1b[',b'\x1bO'):continue
                if len(self.escape)>2 and 0x40<=c<=0x7e:
                    key={b'\x1b[A':'w',b'\x1b[B':'s',b'\x1b[C':'d',b'\x1b[D':'a',b'\x1bOA':'w',b'\x1bOB':'s',b'\x1bOC':'d',b'\x1bOD':'a'}.get(self.escape)
                    self.escape=b''
                    if key:self.add(key)
                elif len(self.escape)>32 or (len(self.escape)==2 and c not in (91,79)):self.escape=b''
                continue
            if c==27:self.escape=b'\x1b';self.escape_at=now
            elif c in (3,4):self.interrupt=True;self.quit=True;self.queue.clear()
            elif c in b'adwsrq ':self.add('s' if c==32 else chr(c))
    def add(self,key):
        if key=='q':self.quit=True;self.queue.clear()
        elif key=='r':self.queue.clear();self.queue.append(key)
        elif len(self.queue)<32:self.queue.append(key)
        else:self.dropped+=1
    def take(self):return 'q' if self.quit else self.queue.popleft() if self.queue else ''

class Ticks:
    def __init__(self,now):self.last=now;self.remainder=0;self.dropped=0
    def take(self,now):
        elapsed=max(0,now-self.last)+self.remainder;self.last=now
        ticks,self.remainder=divmod(elapsed,PERIOD)
        self.dropped+=max(0,ticks-20)
        return min(ticks,20)
    def reset(self,now):self.last=now;self.remainder=0

class Renderer:
    def __init__(self):self.previous=None;self.size=None
    def draw(self,frame,size,detail):
        if len(frame)!=1920 or any(c<32 or c>126 for c in frame):raise ValueError('unsafe framebuffer')
        changed=size!=self.size;self.size=size
        if size.columns<80 or size.lines<24:
            self.previous=None
            return b'\x1b[H\x1b[2J'+b'Resize to at least 80x24; q quits'[:max(0,size.columns-1)] if changed else b''
        rows=[frame[i:i+80] for i in range(0,1920,80)]
        rows[22]=b'a/d: move  w: rotate  s/Space: drop  Arrows work  r: restart  q/Ctrl-C: quit'.ljust(80)
        rows[23]=detail.encode('ascii')[:80].ljust(80)
        output=bytearray(b'\x1b[2J' if changed or self.previous is None else b'')
        for i,row in enumerate(rows):
            if self.previous is None or row!=self.previous[i]:output.extend(f'\x1b[{i+1};1H'.encode()+row)
        self.previous=rows
        return bytes(output)

class Terminal:
    def __enter__(self):
        self.saved=termios.tcgetattr(0);tty.setraw(0)
        try:os.write(1,b'\x1b[?1049h\x1b[?25l\x1b[?7l')
        except BaseException:termios.tcsetattr(0,termios.TCSANOW,self.saved);raise
        return self
    def __exit__(self,*args):
        try:os.write(1,b'\x1b[?7h\x1b[?25h\x1b[?1049l')
        except OSError:pass # hung-up SSH PTY no longer accepts output
        try:termios.tcsetattr(0,termios.TCSANOW,self.saved)
        except termios.error:pass # PTY can disappear on hangup

def write_all(data):
    while data:
        n=os.write(1,data)
        if not n:raise OSError('terminal output closed')
        data=data[n:]

def play(session,code,seed,out,stop):
    keys=Keys();render=Renderer();state=None;frame=b' '*1920
    started=time.monotonic_ns();ticks=Ticks(started);due=started
    times=[];late=0;maxlate=0;skipped=0;restarts=0;reason='signal';sequence=0
    last_report=started;small=False;controls=collections.Counter()
    with gzip.open(out/'frames.bin.gz','xb',compresslevel=1) as trace,Terminal():
        while not stop['signal']:
            now=time.monotonic_ns()
            timeout=max(0,(due-now)/1e9)
            readable,_,_=select.select([0],[],[],min(timeout,.05))
            if readable:
                data=os.read(0,4096)
                if not data:reason='eof';break
                keys.feed(data,time.monotonic_ns())
            now=time.monotonic_ns()
            if now<due and not keys.quit:continue
            size=os.get_terminal_size(1)
            if (size.columns<80 or size.lines<24) and not keys.quit:
                write_all(render.draw(frame,size,''));small=True;ticks.reset(now);due=now+PERIOD;continue
            if small:ticks.reset(now);small=False
            key=keys.take();controls[key or 'idle']+=1
            elapsed=ticks.take(now)
            if state is None or key=='r':
                incoming=request(seed=seed);ticks.reset(now)
                if key=='r':restarts+=1
            else:incoming=request(state,key=ord(key) if key else 0,ticks=elapsed)
            # Quit pressed before first frame still gets a bounded initialized state.
            sequence+=1;block=bio.prepare(code,incoming,8192,sequence)[bio.OFFSET:]
            call=time.monotonic_ns();status,response,_=session.step(block);done=time.monotonic_ns()
            if status:raise RuntimeError(f'card rejected request: BIO status {status}')
            state,text=split(response);frame=response[240:]
            duration=done-call;lateness=max(0,done-(due+PERIOD));times.append(duration)
            late+=bool(lateness);maxlate=max(maxlate,lateness)
            trace.write(TRACE.pack(call-started,duration,lateness,incoming,response))
            detail=f'i960 card | 20 Hz | {duration/1e6:.1f} ms | queued {len(keys.queue)} | dropped {keys.dropped}'
            write_all(render.draw(frame,size,detail))
            if done-last_report>=1_000_000_000:
                trace.flush()
                report=dict(pid=os.getpid(),frames=sequence,elapsed_s=(done-started)/1e9,restarts=restarts,phase=struct.unpack_from('<I',state,32)[0],input_dropped=keys.dropped)
                (out/'progress.tmp').write_text(json.dumps(report));os.replace(out/'progress.tmp',out/'progress.json')
                (out/'latest-frame.txt').write_text(text);last_report=done
            if struct.unpack_from('<I',state,32)[0]==2:reason='ctrl-c' if keys.interrupt else 'quit';break
            due+=PERIOD
            if done>due+PERIOD:
                missed=(done-due)//PERIOD;skipped+=missed;due+=missed*PERIOD
        if stop['signal']:reason=signal.Signals(stop['signal']).name
    ended=time.monotonic_ns()
    if state is not None:
        (out/'latest-state.bin').write_bytes(state);(out/'latest-frame.txt').write_text(text)
    return dict(frames=sequence,elapsed_s=(ended-started)/1e9,latency=stats(times) if times else None,
                late_frames=late,max_late_ms=maxlate/1e6,skipped_render_slots=skipped,
                dropped_ticks=ticks.dropped,input_dropped=keys.dropped,restarts=restarts,
                controls=dict(controls),exit_reason=reason)

def run(a):
    if os.geteuid()!=0:raise ValueError('run with sudo on the Linux card host')
    if not os.isatty(0) or not os.isatty(1):raise ValueError('needs a terminal; use ssh -t')
    if not 0<=a.seed<=0xffffffff:raise ValueError('seed outside uint32')
    code=a.payload.read_bytes();image=bio.prepare(code,b'',8192,1)
    a.output.mkdir(parents=True,exist_ok=False)
    stop={'signal':0};handlers={}
    for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP]:
        handlers[sig]=signal.signal(sig,lambda n,f:stop.update(signal=n))
    summary={};loaded=False;session=None;error=None
    with open('/run/lock/i960-loadrun.lock','w') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if any(Path('/sys/module/'+m).exists() for m in ['dac960dump','dac960loadrun','dac960program','dac960session']):raise RuntimeError('another controller module is loaded')
            if Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists():raise RuntimeError('controller already bound')
            name='i960/terminal-'+hashlib.sha256(image).hexdigest()+'.bin'
            fw=Path('/lib/firmware')/name;fw.parent.mkdir(exist_ok=True);fw.write_bytes(image)
            metadata=dict(pid=os.getpid(),seed=a.seed,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),payload_sha256=hashlib.sha256(code).hexdigest(),module_sha256=hashlib.sha256(a.module.read_bytes()).hexdigest())
            (a.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
            subprocess.run(['insmod',str(a.module),'firmware_name='+name,'pointer_check=1','runtime_check=1','stage_check=1','buffer_io=1',f'payload_argument={bio.BASE}'],check=True)
            loaded=True;capture(a.output/'preflight')
            if 'experiment-result=0 pending=0;' not in (a.output/'preflight/result.txt').read_text():raise RuntimeError('controller preflight failed')
            session=Session();capture(a.output/'open')
            summary=play(session,code,a.seed,a.output,stop)
        except BaseException as e:
            error=e;summary['error']=repr(e)
        finally:
            if session is not None:
                try:session.close()
                except BaseException as e:error=error or e;summary['close_error']=repr(e)
            if loaded:
                try:
                    capture(a.output/'close');verify_close(a.output/'close')
                    summary['restored']=True
                    subprocess.run(['rmmod','dac960session'],check=True)
                    summary['unloaded']=True
                except BaseException as e:error=error or e;summary['cleanup_error']=repr(e)
            summary['driver_bound']=Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists()
            (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
            for sig,handler in handlers.items():signal.signal(sig,handler)
    if error:raise error
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--payload',required=True,type=Path);p.add_argument('--module',required=True,type=Path)
    p.add_argument('--seed',type=lambda s:int(s,0),default=1)
    p.add_argument('--output',type=Path,default=Path.home()/'i960-tetris-sessions'/time.strftime('%Y%m%d-%H%M%S'))
    a=p.parse_args()
    try:
        result=run(a);print(f"Tetris finished: {result.get('frames',0)} frames. Captures: {a.output}")
    except (Exception,KeyboardInterrupt) as e:
        print(f'Tetris stopped: {e}. Inspect {a.output}; no execution was retried.',file=sys.stderr);return 1
    return 0
if __name__=='__main__':sys.exit(main())
