"""Read-only chip indices compared with sequential firmware RAM observations."""
import importlib.util
import struct
from pathlib import Path

def sibling(name,page,nonce,sequence,phase):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.decode(page,nonce,sequence,phase)

def decode(page,nonce,sequence,phase):
    config=sibling('qlogic_config',page,nonce,sequence,phase)
    queue=sibling('qlogic_queue',page,nonce,sequence,phase)
    if not (int(config['config']['0x04'],16)&2) or queue['registers']['0xc0600d28']!='0x8bf00000':
        raise ValueError('chip prerequisites')
    w=struct.unpack_from('<32I',page,384*4)
    if w[:8]!=(0x31504351,1,nonce,sequence,phase,0,12,0) or any(w[20:]) or any(v>65535 for v in w[8:20]):
        raise ValueError('chip identity/refusal/count/width/reserved')
    a,b=w[8:14],w[14:20]
    stable=a==b and a[:2]==a[4:] and b[:2]==b[4:]
    quiet=all(v==0 for v in (a[0],a[1],a[4],a[5],b[0],b[1],b[4],b[5]))
    req,rsp=b[2:4];swreq=queue['request_indices'];swrsp=queue['response_indices']
    return dict(config=config,software=queue,raw_samples=[a,b],stable=stable,status_zero=quiet,
        chip_request_consumer=req,chip_response_producer=rsp,
        indices_in_range=req<256 and rsp<128,
        request_consumer_matches_cache=req==swreq[1],response_producer_matches_cache=rsp==swrsp[0],
        request_ring_equal_observed=req==swreq[0],response_ring_equal_observed=rsp==swrsp[1],
        atomic=False,hardware_drained=False,ownership_proven=False)
