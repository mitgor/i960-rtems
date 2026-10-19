"""Profile-14 extension decoder. Values are observations, never ownership grants."""
import struct
REGISTERS=[0x1400+64*c+off for c in range(3) for off in (0,12,16,20,24,28,32,36)]+[0x1600,0x104c,0x1800,0x1808,0x180c,0x1820,0x1824,0x1828]
REGISTERS += [0xc0384b6c,0xc0384b70,0xc0384b8c,0xc0384b90,0xc0384b94,0xc0384b98,0xc0384b9c,0xc0384ba0,0xc0384ba4,0xc0384ba8,0xc0384bac,0xc0384e78,0xc0384e7c,0xc049b7cc,0xc049b7d0,0xc049b7d4]
def decode(page,nonce,sequence,phase):
    if len(page)!=4096:raise ValueError('record size')
    w=struct.unpack_from('<56I',page,1024)
    if w[:8]!=(0x31474e45,1,nonce,sequence,phase,48,0,0):raise ValueError('inventory identity/sequence/phase')
    return dict(registers={f'0x{a:04x}':f'0x{v:08x}' for a,v in zip(REGISTERS,w[8:])},
        atomic=False,csr_asr_read=False,ownership_proven=False)
