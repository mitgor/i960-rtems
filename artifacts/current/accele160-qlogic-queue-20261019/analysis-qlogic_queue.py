"""Fixed firmware-RAM observations, with no pointer traversal or RAM grants."""
import struct
ADDRESSES=[0xc0600d00+x for x in (0x28,0x2c,0x30,0x34,0x38,0x3c,0x40,0x44,0x48,0x4c,0x50)]+[0xc0498280,0xc0498284,0xc049828c]
def decode(page,nonce,sequence,phase):
    if len(page)!=4096:raise ValueError('record size')
    w=struct.unpack_from('<32I',page,352*4)
    if w[:8]!=(0x314d5251,1,nonce,sequence,phase,0,0xc0600d00,14) or any(w[22:]):raise ValueError('queue identity/refusal/count/reserved')
    v=w[8:22];req=(v[9]&65535,v[9]>>16);rsp=(v[10]&65535,v[10]>>16)
    layout=(v[0]==0x8bf00000 and v[3:7]==(0xc0600df0,256,0xc0604df0,128))
    pointers=(0<=v[7]-v[3]<16384 and (v[7]-v[3])%64==0 and 0<=v[8]-v[5]<8192 and (v[8]-v[5])%64==0)
    indices=all(x<256 for x in req) and all(x<128 for x in rsp)
    return dict(registers={hex(a):f'0x{x:08x}' for a,x in zip(ADDRESSES,v)},
        expected_layout=layout,ring_pointers_in_range=pointers,indices_in_range=indices,
        request_indices=req,response_indices=rsp,pending_head=hex(v[1]),pending_tail=hex(v[2]),
        channel0_counters=[x&65535 for x in v[11:14]],
        software_indices_equal=req[0]==req[1] and rsp[0]==rsp[1],
        atomic=False,hardware_drained=False,ownership_proven=False)
