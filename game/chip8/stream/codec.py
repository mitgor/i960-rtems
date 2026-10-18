"""CHIP-8 packed packet; independent of Doom's indexed/palette framebuffer."""
import struct
MAGIC=0x31424643
PAYLOAD=512

def validate_payload(raw, frame=None):
    if len(raw)!=512:raise ValueError('CHIP-8 payload length')
    w=struct.unpack_from('<8I',raw)
    q=struct.unpack_from('<8I',raw,304)
    if w[0]!=0x31473843 or w[1]>4 or w[2]>1000 or w[4]>65535 or w[5]>65535 or w[6]>255 or w[7]>255:
        raise ValueError('CHIP-8 state')
    if q[:2]!=(0x31503843,1) or not 0<q[2]<0xfffffffe or q[3]>65535 or not 1<=q[5]<=4000 :
        raise ValueError('CHIP-8 metadata/padding')
    n,updates,start,reserved=struct.unpack_from('<4I',raw,336)
    if not 1<=n<=8 or updates<n or reserved or any(raw[352+16*n:]):raise ValueError('CHIP-8 trace bounds/padding')
    trace=list(struct.iter_unpack('<4I',raw[352:352+16*n]))
    if any(c>1000 or k>65535 or t>15 or seen>q[4] for c,k,t,seen in trace):raise ValueError('CHIP-8 trace fields')
    if frame is not None and q[2]!=frame:raise ValueError('CHIP-8 frame generation')
    return dict(status=w[1],executed=w[2],total=w[3],pc=w[4],index=w[5],delay=w[6],sound=w[7],
                frame=q[2],held=q[3],input_seen=q[4],cpu_hz=q[5],clock_ms=q[6],dropped_ms=q[7],trace=trace,updates=updates,start_ms=start)

def validate_frame(packet):
    if len(packet)!=544:raise ValueError('CHIP-8 browser packet length')
    w=struct.unpack_from('<8I',packet)
    if w[:2]!=(MAGIC,1) or not w[2] or not w[3] or w[4:]!=(64,32,512,0):raise ValueError('CHIP-8 browser header')
    validate_payload(packet[32:])
    return w[2:4]

def packet(raw,epoch,generation):
    validate_payload(raw)
    return struct.pack('<8I',MAGIC,1,epoch,generation,64,32,512,0)+raw
