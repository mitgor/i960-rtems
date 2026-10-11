#!/usr/bin/env python3
"""Two native processes exchange CTL1 through shared RAM; no card access."""
import ctypes as C,json,mmap,os,struct,subprocess,sys,tempfile,time
from pathlib import Path
from protocol import request,response
from test_control import State,Hooks,Barrier,Quiesce,U,Slot
HERE=Path(__file__).resolve().parent

def mapped(path,library):
    fd=os.open(path,os.O_RDWR);m=mmap.mmap(fd,128);os.close(fd)
    req=Slot.from_buffer(m,0);res=Slot.from_buffer(m,64);lib=C.CDLL(library)
    lib.ctl_poll.argtypes=[C.POINTER(State),C.POINTER(U),C.POINTER(U),C.POINTER(Hooks)]
    lib.sim_store.argtypes=[C.POINTER(U),U];lib.sim_load.argtypes=[C.POINTER(U)];lib.sim_load.restype=U
    return m,req,res,lib

def target(path,library):
    m,req,res,lib=mapped(path,library);state=State();lib.ctl_init(C.byref(state),123)
    barrier=Barrier(('sim_barrier',lib));stop=Quiesce(lambda _:1);hooks=Hooks(barrier,stop,None)
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        lib.ctl_tick(C.byref(state));lib.ctl_poll(C.byref(state),req,res,C.byref(hooks))
        if state.stopped:return
        time.sleep(.001)
    raise TimeoutError('simulated target deadline')

def main():
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'slots';path.write_bytes(bytes(128));library=str(Path(tmp)/'control.so')
        subprocess.run(['cc','-std=c11','-shared','-fPIC',str(HERE/'control.c'),str(HERE/'sim_bridge.c'),'-o',library],check=True)
        m,req,res,lib=mapped(path,library)
        child=subprocess.Popen([sys.executable,__file__,'target',str(path),library])
        results=[]
        try:
            for seq,op,arg in [(1,1,0x12345678),(2,0,0),(3,2,0)]:
                words=struct.unpack('<16I',request(123,seq,op,arg))
                lib.sim_store(req,0)
                for i in range(1,16):req[i]=words[i]
                lib.sim_store(req,seq)
                deadline=time.monotonic()+3
                while lib.sim_load(res)!=seq:
                    if time.monotonic()>deadline:raise TimeoutError('host response deadline')
                    time.sleep(.001)
                data=bytes(res)
                if lib.sim_load(res)!=seq:raise RuntimeError('torn response')
                result=response(data,123,seq);assert result['status']==0;results.append(result)
                time.sleep(.05)
            child.wait(timeout=3);assert child.returncode==0
            assert results[0]['value']==0x12345678 and results[1]['heartbeat']>results[0]['heartbeat'] and results[2]['stopped']
            print(json.dumps(dict(passed=True,backend='native shared-memory simulation; no MMIO or firmware calls',results=results),indent=2))
        finally:
            if child.poll() is None:child.kill();child.wait()

if __name__=='__main__':
    if len(sys.argv)>1:target(sys.argv[2],sys.argv[3])
    else:main()
