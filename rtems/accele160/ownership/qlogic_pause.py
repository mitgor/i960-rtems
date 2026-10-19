"""One-shot pause acknowledgement is not proof of DMA stop or RAM ownership."""
import struct
import importlib.util
from pathlib import Path

def decode(page,nonce,sequence,phase):
    spec=importlib.util.spec_from_file_location('qlogic_chip',Path(__file__).with_name('qlogic_chip.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    chip=mod.decode(page,nonce,sequence,phase)
    w=struct.unpack_from('<48I',page,416*4)
    if w[:8]!=(0x31535051,1,nonce,sequence,phase,0,1,1) or any(w[25:]):
        raise ValueError('pause refused/failed/identity/reserved')
    if not (1<=w[12]<=10000 and 1<=w[14]<=10000 and w[15]==2):
        raise ValueError('pause poll/write counts')
    if any(w[i]>65535 for i in (8,9,10,11,13,16,17,18,19,20,21,22)):
        raise ValueError('pause register width')
    if w[8]&0x300 or w[9]&1 or w[10]&0x4e0 or w[11]!=(w[10]|0x20) or w[13]!=w[10]:
        raise ValueError('pause transition')
    if w[16:19]!=w[8:11] or w[19] or w[20]&1 or w[21]>=256 or w[22]>=128:
        raise ValueError('pause restored state')
    if sequence==1 and phase==0 and (w[20]!=chip['raw_samples'][0][1] or w[21]!=chip['chip_request_consumer'] or w[22]!=chip['chip_response_producer']):
        raise ValueError('pause changed queues/semaphore')
    return dict(chip=chip,one_shot=True,origin_sequence=w[7],conf1=w[8],icr=w[9],
        hccr_before=w[10],hccr_paused=w[11],hccr_released=w[13],
        pause_polls=w[12],release_polls=w[14],chip_writes=w[15],
        after=dict(conf1=w[16],icr=w[17],hccr=w[18],isr=w[19],semaphore=w[20],request_consumer=w[21],response_producer=w[22]),
        ticks_before=w[23],ticks_after=w[24],hardware_drained=False,ownership_proven=False)
