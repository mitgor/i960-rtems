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
    def record(self,**kw):self.log.write(json.dumps(dict(time=time.monotonic(),**kw))+'\n')
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
                wpage=snap(ADDRESS);w=struct.unpack_from('<11I',wpage,416*4)
                if w[1]==self.seq:
                    op=self.pending
                    if w[0]!=0x31525041 or (op in (5,7) and w[4]>2048):raise ValueError('invalid application reply')
                    self.epoch=w[3];payload=wpage[432*4:432*4+w[4]] if op in (5,7) and not w[2] else b''
                    result=dict(sequence=self.seq,status=w[2],epoch=w[3],value=w[4],state=w[5],reservation=w[6],busy=w[7],poisoned=w[8],calls=w[9],started=w[10],data=payload.hex())
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
            req=json.loads(self.data);op=req['op'];payload=bytes.fromhex(req.get('data',''))
            if self.disabled:raise ValueError('runtime quarantined')
            if type(op)!=int or not 1<=op<=8 or len(payload)>1500:raise ValueError('request bounds')
            if self.epoch is None:
                page=snap(ADDRESS);w=struct.unpack_from('<11I',page,416*4)
                if w[0]!=0x31525041 or not w[3] or w[1]:raise ValueError('runtime identity/owner')
                self.epoch=w[3]
            if self.seq==0xffffffff:raise ValueError('sequence exhausted')
            self.seq+=1
            if payload:write(ADDRESS,64,payload)
            write(ADDRESS,4,struct.pack('<15I',self.epoch,op,len(payload),zlib.crc32(payload),*([0]*11)))
            self.record(event='request',seq=self.seq,epoch=self.epoch,op=op,data=payload.hex())
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
