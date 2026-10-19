"""Profile 15 exact-device config observation; never an ownership grant."""
import struct

def decode(page,nonce,sequence,phase):
    if len(page)!=4096:raise ValueError('record size')
    w=struct.unpack_from('<20I',page,320*4)
    if w[:5]!=(0x31494350,1,nonce,sequence,phase):raise ValueError('config identity/sequence/phase')
    if w[5]!=0 or w[6]!=w[7] or w[8]!=5 or w[9]!=0 or any(w[15:]):raise ValueError('config incomplete/refused/restore failed')
    if w[10]!=0x10161077 or w[14]!=0xfff00000:raise ValueError('device identity/BAR mismatch')
    return dict(selector_before=hex(w[6]),selector_after=hex(w[7]),
        config={f'0x{a:02x}':f'0x{v:08x}' for a,v in zip((0,4,8,16,20),w[10:15])},
        device_config_writes=False,ownership_proven=False)
