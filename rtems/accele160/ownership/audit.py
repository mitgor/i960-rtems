#!/usr/bin/env python3
"""Decode observational evidence; never promote quiet registers into ownership."""
import json,struct,sys

def audit(data):
    if data['schema']!=1 or len(data['samples'])!=3:raise ValueError('capture schema/count')
    results=[];boots=set();last=-1
    for row in data['samples']:
        boots.add(row['boot_id'])
        if row['monotonic']<=last:raise ValueError('sample order')
        last=row['monotonic']
        regs={}
        for bdf,ident,typ in [('0000:37:09.0',(0x8086,0x2962),1),('0000:37:09.1',(0x1069,0x50),0)]:
            d=row['devices'][bdf];raw=bytes.fromhex(d['config'])
            if len(raw)!=64 or struct.unpack_from('<HH',raw)!=ident or raw[14]&127!=typ:
                raise ValueError('PCI identity/header')
            regs[bdf]=raw
        bridge=regs['0000:37:09.0'];endpoint=regs['0000:37:09.1']
        sacr=bytes.fromhex(row['devices']['0000:37:09.0']['sacr'])
        if len(sacr)!=4:raise ValueError('SACR length')
        value=struct.unpack('<I',sacr)[0];bcr=struct.unpack_from('<H',bridge,62)[0]
        if row['services']!='active\nactive' or 'idle=1' not in row['apps'].splitlines() or 'zone_loaned=0' not in row['mem'].splitlines():
            raise ValueError('normal service not idle/healthy')
        results.append(dict(bridge_control=hex(bcr),secondary_reset_asserted=bool(bcr&64),
            primary_bus=bridge[24],secondary_bus=bridge[25],subordinate_bus=bridge[26],
            secondary_arbiter=hex(value),external_grants_disabled=all((value>>(2+2*i))&3==3 for i in range(6)),
            external_priorities=[(value>>(2+2*i))&3 for i in range(6)],
            endpoint_bus_master_enabled=bool(struct.unpack_from('<H',endpoint,4)[0]&4)))
    if len(boots)!=1:raise ValueError('boot changed')
    return dict(boot_id=next(iter(boots)),samples=results,prompt_preserved=True,
        permanent_scsi_exclusion_proven=False,aau_ownership_proven=False,
        new_ram_grant=False,core_engine_state_measured=False)
if __name__=='__main__':
    with open(sys.argv[1]) as f:print(json.dumps(audit(json.load(f)),indent=2))
