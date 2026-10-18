"""Bounded Unix socket front-end. Only the owning runner touches PCI.

Requests are ASCII command names, one per connection. No addresses or payloads
are accepted. pump() runs on the owner thread; no mmap calls from socket threads.
"""
import json, os, secrets, socket, struct, time
from pathlib import Path
COMMANDS = ('help','version','uptime','tasks','mem','apps','stats')
ADDRESS = 0xc0774000  # odd aperture exposes the reserved c0775000 page
MAGIC = 0x31435653

class Service:
    def __init__(self, path, journal, defer=False):
        self.path=Path(path)
        if self.path.exists():raise RuntimeError("console endpoint already exists; inspect owner")
        self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        # Never unlink an existing owner endpoint.
        self.started=False
        if not defer:self.start()
        self.clients=[];self.pending=None;self.seq=0
        self.epoch=secrets.randbelow(0xfffffffe)+1
        self.log=open(journal,'x',buffering=1)
        self.disabled=False;self.testing=False
    def start(self):
        self.sock.bind(str(self.path));os.chmod(self.path,0o600)
        self.sock.listen(8);self.sock.setblocking(False);self.started=True
    def record(self, **data):
        self.log.write(json.dumps(dict(time=time.monotonic(),**data))+'\n')
    def initialize(self,write):
        write(ADDRESS,0,struct.pack('<16I',0,1,self.epoch,*([0]*13)))
        self.record(event='initialize',epoch=self.epoch,address=ADDRESS+4096)
    def reply(self,c,text):
        c['out']=text.encode('ascii');c['until']=time.monotonic()+5
    def pump(self,snap,write):
        now=time.monotonic()
        for _ in range(8):
            try:conn,_=self.sock.accept()
            except BlockingIOError:break
            conn.setblocking(False)
            if len(self.clients)>=8:conn.close();continue
            self.clients.append(dict(conn=conn,data=b'',out=None,until=now+5))
        for c in list(self.clients):
            if now>c['until']:
                c['conn'].close();self.clients.remove(c);continue
            try:
                if c.get('closing'):
                    if not c['conn'].recv(1024):
                        c['conn'].close();self.clients.remove(c)
                elif c['out'] is not None:
                    n=c['conn'].send(c['out']);c['out']=c['out'][n:]
                    if not c['out']:
                        c['conn'].shutdown(socket.SHUT_WR)
                        c['out']=None;c['closing']=True
                elif 'command' not in c:
                    b=c['conn'].recv(129-len(c['data']))
                    if not b:c['conn'].close();self.clients.remove(c);continue
                    c['data']+=b
                    if len(c['data'])>128:self.reply(c,'error: command too long\n')
                    elif b'\n' in c['data']:
                        command=c['data'].decode('ascii',errors='replace').strip()
                        if command not in COMMANDS:self.reply(c,'error: unknown command\n')
                        else:c['command']=command
            except BlockingIOError:pass
            except OSError:
                c['conn'].close();self.clients.remove(c)
        if self.pending:
            c,seq,started=self.pending
            page=snap(ADDRESS);w=struct.unpack_from('<32I',page)
            if w[16]==seq:
                if w[18]!=self.epoch or w[19]>768 or w[24]!=MAGIC:
                    self.disabled=True;self.reply(c,'error: invalid card reply; console quarantined\n')
                else:
                    text=page[128:128+w[19]].decode('ascii',errors='replace')
                    self.reply(c,text)
                    self.record(event='reply',command=c['command'],seq=seq,epoch=self.epoch,
                        latency_ms=(now-started)*1000,status=w[17],wire=page[:896].hex(),text=text)
                self.pending=None
            elif now-started>5:
                self.disabled=True;self.reply(c,'error: card reply timeout; console quarantined\n')
                self.record(event='timeout',seq=seq);self.pending=None
        if not self.pending and not self.testing:
            for c in self.clients:
                if 'command' in c and c['out'] is None and not c.get('closing'):
                    if self.disabled:self.reply(c,'error: console quarantined\n');continue
                    self.seq+=1
                    if self.seq>0xffffffff:self.disabled=True;break
                    write(ADDRESS,4,struct.pack('<15I',1,self.epoch,COMMANDS.index(c['command'])+1,*([0]*12)))
                    write(ADDRESS,0,struct.pack('<I',self.seq))
                    self.pending=(c,self.seq,now);break
    def selftest(self,snap,write):
        self.testing=True
        try:
            while self.pending:
                self.pump(snap,write);time.sleep(.002)
            if self.disabled:raise RuntimeError("console quarantined before selftest")
            self._selftest(snap,write)
        finally:self.testing=False
    def _selftest(self,snap,write):
        """Owner-thread physical protocol gate, before engine admission."""
        def call(seq,op,epoch=None,length=0,reserved=0,want=0):
            epoch=self.epoch if epoch is None else epoch
            wire=[1,epoch,op,length]+[0]*10+[reserved]
            write(ADDRESS,4,struct.pack('<15I',*wire))
            write(ADDRESS,0,struct.pack('<I',seq))
            start=time.monotonic()
            while time.monotonic()-start<5:
                page=snap(ADDRESS);w=struct.unpack_from('<32I',page)
                if w[16]==seq and w[18]==epoch:break
                time.sleep(.002)
            else:raise RuntimeError('service selftest timeout')
            if w[17]!=want or w[19]>768 or w[24]!=MAGIC:
                raise RuntimeError('service selftest invalid reply')
            self.record(event='selftest',seq=seq,opcode=op,expected=want,
                latency_ms=(time.monotonic()-start)*1000,wire=page[:896].hex())
            return page[64:896]
        for op in range(1,8):
            self.seq+=1;first=call(self.seq,op)
            # Exact duplicate is read-only and retains the original timestamp.
            time.sleep(.02)
            if call(self.seq,op)!=first:raise RuntimeError('duplicate changed response')
        call(self.seq+100,1,epoch=self.epoch^1,want=1)
        call(self.seq+101,1,want=2)
        call(self.seq-1,1,want=2)
        self.seq+=1;call(self.seq,1,length=0xffffffff,want=3)
        self.seq+=1;call(self.seq,99,want=4)
        self.seq+=1;call(self.seq,1,reserved=1,want=3)
        self.seq+=1;call(self.seq,2)
        self.record(event='selftest_pass',seq=self.seq)

    def close(self):
        for c in self.clients:c['conn'].close()
        self.sock.close()
        if self.started:self.path.unlink(missing_ok=True)
        self.log.close()
