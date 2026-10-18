"""Every frame checked against unchanged C8G1 native code and committed input.

The card supplies a bounded execution trace, not trusted pixels or key states.
Validate its clock budget and input sequence before replaying the guest core.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from host import Native,request
from codec import validate_payload
class Oracle:
    def __init__(self,rom,hz=500,library=None):
        self.core=Native() if library is None else Native(library)
        self.core.step(request(op=0,seed=1,rom=rom));self.hz=hz;self.events=[]
        self.base=0
        self.frame=self.seen=self.held=self.pressed=self.updates=0
        self.cycles=self.ticks=self.budget_ms=0;self.last=None;self.dropped=0
    def submit(self,events):
        if any(type(e) is not int or not 0<=e<=511 or (e&255)>15 for e in events):raise ValueError('oracle key')
        if len(self.events)+len(events)>32:raise ValueError("bounded oracle input backlog")
        self.events.extend(events)
    def check(self,raw):
        q=validate_payload(raw,self.frame+1)
        if q['cpu_hz']!=self.hz:raise ValueError('guest rate changed')
        last=self.last if self.last is not None else q['start_ms']
        elapsed=((q['clock_ms']-last)&0xffffffff)-((q['dropped_ms']-self.dropped)&0xffffffff)
        if elapsed<0:raise ValueError('invalid clock clamp')
        self.budget_ms+=elapsed
        for cycles,keys,ticks,seen in q['trace']:
            if not self.seen<=seen<=self.base+len(self.events):raise ValueError('input consumption sequence')
            for event in self.events[self.seen-self.base:seen-self.base]:
                key=event&255
                if event&256:self.held|=1<<key;self.pressed|=1<<key
                else:self.held&=~(1<<key)
            self.seen=seen
            if keys!=self.held|self.pressed:raise ValueError('input latch replay')
            reply=self.core.step(request(cycles=cycles,keys=keys,ticks=ticks))
            if cycles:self.pressed=0
            self.cycles+=cycles;self.ticks+=ticks;self.updates+=1
        if reply!=raw[:304]:raise ValueError('native CHIP-8 response mismatch')
        if (q['held'],q['input_seen'],q['updates'])!=(self.held,self.seen,self.updates):raise ValueError('player counters')
        if (self.cycles,self.ticks)!=(self.budget_ms*self.hz//1000,self.budget_ms*60//1000):raise ValueError('guest clock budget')
        del self.events[:self.seen-self.base];self.base=self.seen
        self.frame+=1;self.last=q['clock_ms'];self.dropped=q['dropped_ms']
        return q
