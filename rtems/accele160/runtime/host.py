"""Bounded root-only RPC; invoked only by the existing PCI owner thread.
No independent mmap, stock mailbox, arbitrary address, or background PCI thread.
"""
import socket,struct,time,json,zlib,os
from pathlib import Path
ADDRESS=0xc077a000
class Runtime:
    def __init__(self,path,journal):
        self.path=Path(path);self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.bind(str(self.path));os.chmod(path,0o600);self.sock.listen(2);self.sock.setblocking(False)
        self.client=None;self.pending=None;self.data=b'';self.reply=b'';self.seq=0;self.epoch=None;self.disabled=False
        self.log=open(journal,'x',buffering=1)
        self.dma_capable=False;self.pending_dma=False;self.pending_compare=False;self.started_at=0
        self.pin=Path('/sys/kernel/debug/accele-frame-dma')
    def record(self,**kw):self.log.write(json.dumps(dict(time=time.monotonic(),**kw))+'\n')
    def dma_reply(self):
        marker=(self.pin/'marker0.bin').read_bytes()
        if len(marker)!=32:raise ValueError('DMA marker size')
        w=struct.unpack('<8I',marker)
        if w[:3]!=(0x31525044,self.epoch,self.seq):return None
        if w!=(0x31525044,self.epoch,self.seq,0,4096,ADDRESS+4096,(~self.epoch)&0xffffffff,(~self.seq)&0xffffffff):raise ValueError('DMA marker identity')
        fd=os.open(self.pin/'frame0.bin',os.O_RDONLY)
        try:page=os.pread(fd,4096,4096)
        finally:os.close(fd)
        if len(page)!=4096 or (self.pin/'marker0.bin').read_bytes()!=marker:raise ValueError('DMA reply changed')
        if struct.unpack_from('<I',page,417*4)[0]!=self.seq:raise ValueError('DMA reply sequence')
        return page
    def pump(self,snap,write):
        now=time.monotonic()
        if self.client is None:
            try:self.client,_=self.sock.accept()
            except BlockingIOError:return
            self.client.setblocking(False);self.data=b'';self.reply=b'';self.until=now+10
        try:
            if self.reply:
                n=self.client.send(self.reply);self.reply=self.reply[n:]
                if not self.reply:self.client.close();self.client=None
                return
            if self.pending:
                wpage=self.dma_reply() if self.pending_dma else snap(ADDRESS)
                if wpage is None:
                    if now>self.until:raise TimeoutError('DMA reply timeout; memory retained')
                    return
                if self.pending_compare and snap(ADDRESS)!=wpage:raise ValueError('DMA/PIO reply mismatch')
                w=struct.unpack_from('<11I',wpage,416*4)
                if w[1]==self.seq:
                    op=self.pending
                    expected_epoch=((self.epoch+1)&0xffffffff) if op==6 and not w[2] else self.epoch
                    if w[0]!=0x31525041 or w[3]!=expected_epoch or (op in (5,7) and w[4]>2048):raise ValueError('invalid application reply')
                    self.epoch=w[3];payload=wpage[432*4:432*4+w[4]] if op in (5,7) and not w[2] else b''
                    result=dict(sequence=self.seq,status=w[2],epoch=w[3],value=w[4],state=w[5],reservation=w[6],busy=w[7],poisoned=w[8],calls=w[9],started=w[10],data=payload.hex(),transport='dma' if self.pending_dma else 'pio',latency_ms=(time.monotonic()-self.started_at)*1000)
                    self.record(event='reply',**result);self.reply=(json.dumps(result)+'\n').encode();self.pending=None
                elif now>self.until:raise TimeoutError('application timeout; memory retained')
                return
            if now>self.until:raise TimeoutError('incomplete request')
            b=self.client.recv(4097-len(self.data))
            if not b:self.client.close();self.client=None;return
            self.data+=b
            if len(self.data)>4096:raise ValueError('oversize request')
            if b'\n' not in self.data:
                if now>self.until:raise TimeoutError('incomplete request')
                return
            req=json.loads(self.data);op=req['op'];payload=bytes.fromhex(req.get('data',''));transport=req.get('transport','pio')
            if transport not in ('pio','dma','dma-check') or (transport!='pio' and op not in (5,7)):raise ValueError('reply transport')
            if self.disabled:raise ValueError('runtime quarantined')
            if type(op)!=int or not 1<=op<=9 or len(payload)>1500:raise ValueError('request bounds')
            if self.epoch is None:
                page=snap(ADDRESS);w=struct.unpack_from('<11I',page,416*4)
                if w[0]!=0x31525041 or not w[3] or w[1]:raise ValueError('runtime identity/owner')
                self.dma_capable=struct.unpack_from('<I',page,427*4)[0]==0x31414d44
                self.epoch=w[3]
            if transport!='pio' and not self.dma_capable:raise ValueError('kernel lacks reply DMA')
            if self.seq==0xffffffff:raise ValueError('sequence exhausted')
            self.seq+=1
            if payload:write(ADDRESS,64,payload)
            write(ADDRESS,4,struct.pack('<15I',self.epoch,op,len(payload),zlib.crc32(payload),int(transport!='pio'),*([0]*10)))
            self.record(event='request',seq=self.seq,epoch=self.epoch,op=op,data=payload.hex(),transport=transport)
            self.pending_dma=transport!='pio';self.pending_compare=transport=='dma-check';self.started_at=time.monotonic()
            self.pending=op # Set before publication: failed write completion is uncertain.
            write(ADDRESS,0,struct.pack('<I',self.seq))
        except BlockingIOError:pass
        except (BrokenPipeError,ConnectionResetError) as e:
            # A reply may outlive its Unix client. A completed card operation
            # stays completed; retire only the dead peer and accept reconnect.
            # If a transport write itself was uncertain, retain/quarantine it.
            if self.pending:self.disabled=True
            self.record(event='client_disconnect',retained=self.disabled,error=str(e))
            self.pending=None;self.reply=b'';self.client.close();self.client=None
        except (OSError,ValueError,KeyError,TypeError,TimeoutError) as e:
            if self.pending:self.disabled=True
            self.pending=None;self.record(event='error',error=str(e),retained=self.disabled)
            self.reply=(json.dumps(dict(error=str(e)))+'\n').encode()
    def close(self):
        if self.client:self.client.close()
        self.sock.close();self.path.unlink(missing_ok=True);self.log.close()
