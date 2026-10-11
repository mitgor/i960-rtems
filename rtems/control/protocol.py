"""Host framing for the transport-neutral CTL1 prototype; no live MMIO backend."""
import struct
MAGIC=0x314c5443
VERSION=1

def checksum(words):
    h=2166136261
    for w in words:
        for b in struct.pack('<I',w):
            h=((h^b)*16777619)&0xffffffff
    return h

def request(epoch,sequence,operation=0,argument=0):
    if not 0<epoch<=0xffffffff or not 0<sequence<=0xffffffff:
        raise ValueError('nonzero 32-bit epoch and sequence required')
    words=[sequence,MAGIC,VERSION,epoch,operation,argument,0]+[0]*9
    words[6]=checksum(words[:6])
    return struct.pack('<16I',*words)

def response(data,epoch,sequence):
    if len(data)!=64:raise ValueError('response length')
    w=struct.unpack('<16I',data)
    if w[:4]!=(sequence,MAGIC,VERSION,epoch) or w[8]!=checksum(w[:8]) or any(w[9:]):
        raise ValueError('stale or corrupt response')
    return dict(status=w[4],value=w[5],stopped=bool(w[6]),heartbeat=w[7])
