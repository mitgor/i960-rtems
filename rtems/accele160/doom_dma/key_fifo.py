"""Host half of the bounded single-producer card keyboard protocol.

Only the owning bridge calls submit(), synchronously with its PCI window.
No browser thread or gateway can touch the ring or hardware ACKs.
"""
import struct

OFFSET=0xe80
MAGIC=0x3146424b
EPOCH=0x161610e1
CAPACITY=16


def guard(i):return (0x4b475244 ^ (i*0x10204081)) & 0xffffffff


def snapshot(page, published, run_id, mode):
    words=struct.unpack_from('<96I',page,OFFSET)
    if words[:4]!=(MAGIC,EPOCH,1,CAPACITY) or words[15]!=(~MAGIC&0xffffffff):
        raise ValueError('keyboard FIFO identity')
    if words[80:]!=tuple(guard(i) for i in range(16)):
        raise ValueError('keyboard FIFO guards')
    if words[4]!=published or not 0<=words[5]<=published or words[7]!=run_id or words[8] or words[14]!=int(mode=='fifo'):
        raise ValueError('keyboard FIFO ownership/run/mode')
    if words[6]>words[5] or words[9]>16 or published-words[5]>(16 if mode=='fifo' else 1):
        raise ValueError('keyboard FIFO counters/depth')
    return words


def configure(page, write, published, run_id, mode):
    words=struct.unpack_from('<96I',page,OFFSET)
    old_mode='fifo' if words[14] else 'mailbox'
    snapshot(page,published,run_id,old_mode)
    if words[5]!=published:
        raise ValueError('keyboard mode change with pending input')
    write(0xc000e000,OFFSET+14*4,struct.pack('<I',int(mode=='fifo')))


def submit(write, published, acked, run_id, mode, events):
    limit=CAPACITY if mode=='fifo' else 1
    if not 0<=published-acked<=limit or len(events)>limit-(published-acked):
        raise ValueError('keyboard FIFO full; never overwrite')
    if any(type(e) is not int or not 0<=e<=511 for e in events):
        raise ValueError('keyboard event')
    if published+len(events)>=0xfffffffe:
        raise ValueError('keyboard sequence exhaustion')
    if not events:return published
    for event in events:
        published+=1
        if mode=='fifo':
            base=OFFSET+(16+((published-1)&15)*4)*4
            write(0xc000e000,base,struct.pack('<4I',published,run_id,event,~published&0xffffffff))
        else:
            write(0xc000e000,0xd2c,struct.pack('<I',event))
    write(0xc000e000,0xd28,struct.pack('<I',published))
    # Exact PCI writeback is still performed by the owner's write() helper.
    # Tail publication happens after every descriptor and the diagnostic mirror.
    write(0xc000e000,OFFSET+4*4,struct.pack('<I',published))
    return published


def pending(page, published, run_id, mode):
    words=snapshot(page,published,run_id,mode)
    if mode=='fifo':
        for seq in range(words[5]+1,published+1):
            base=16+((seq-1)&15)*4
            if words[base]!=seq or words[base+1]!=run_id or words[base+2]&~511 or words[base+3]!=(~seq&0xffffffff):
                raise ValueError('keyboard pending descriptor identity')
    return published-words[5]
