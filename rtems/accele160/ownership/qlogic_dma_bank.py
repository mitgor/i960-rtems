"""Paused DMA bank observations: no DMA stop or memory-ownership claim."""
import struct
import importlib.util
from pathlib import Path
OFFSETS=(0x80,0x84,0x86,0xc0,0xc4,0xc6)
NAMES=('command_config','command_status','command_fifo_status','data_config','data_status','data_fifo_status')
def decode(page,nonce,sequence,phase):
    spec=importlib.util.spec_from_file_location('qlogic_pause',Path(__file__).with_name('qlogic_pause.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    pause=mod.decode(page,nonce,sequence,phase)
    w=struct.unpack_from('<48I',page,464*4)
    if w[:5]!=(0x31424451,1,nonce,1,0) or w[10:12]!=(2,12) or any(w[12:16])+any(w[28:]):
        raise ValueError('DMA bank identity/result/count/reserved')
    if w[5]!=pause['conf1'] or w[6]!=(w[5]|0x300) or w[7]!=w[6] or w[8]!=w[5] or w[9]!=pause['hccr_paused']:
        raise ValueError('DMA bank selection/restoration/pause')
    if any(v>65535 for v in w[16:28]):raise ValueError('DMA register width')
    samples=[dict(zip(NAMES,w[start:start+6])) for start in (16,22)]
    return dict(pause=pause,origin_sequence=1,bank_writes=2,register_reads=12,
                conf1_saved=w[5],conf1_selected=w[7],conf1_restored=w[8],hccr_still_paused=w[9],
                physical_offsets=list(OFFSETS),samples=samples,samples_equal=samples[0]==samples[1],
                hardware_drained=False,ownership_proven=False)
