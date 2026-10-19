#!/usr/bin/env python3
"""Evidence rejection and no-promotion tests using a physical capture fixture."""
import copy,json,sys,unittest
from pathlib import Path
from audit import audit
FIXTURE=Path(__file__).resolve().parents[3]/'artifacts/current/accele160-engine-audit-20261019/live.json'
class Evidence(unittest.TestCase):
    def setUp(self):self.data=json.loads(FIXTURE.read_text())
    def test_physical(self):
        r=audit(self.data)
        self.assertTrue(r['prompt_preserved'])
        self.assertFalse(r['permanent_scsi_exclusion_proven'])
        self.assertTrue(all(not x['secondary_reset_asserted'] and not x['external_grants_disabled'] for x in r['samples']))
    def test_reject(self):
        for kind in ('boot','order','identity','short','sacr','service','idle','loan'):
            d=copy.deepcopy(self.data);r=d['samples'][-1]
            if kind=='boot':r['boot_id']='other-boot'
            if kind=='order':r['monotonic']=0
            if kind=='identity':r['devices']['0000:37:09.0']['config']='00'*64
            if kind=='short':r['devices']['0000:37:09.1']['config']='00'
            if kind=='sacr':r['devices']['0000:37:09.0']['sacr']='00'
            if kind=='service':r['services']='inactive\nactive'
            if kind=='idle':r['apps']='idle=0'
            if kind=='loan':r['mem']='zone_loaned=1'
            with self.subTest(kind=kind),self.assertRaises(ValueError):audit(d)
    def test_reset_and_denial_are_not_ownership(self):
        for r in self.data['samples']:
            d=r['devices']['0000:37:09.0'];h=bytearray.fromhex(d['config']);h[62]|=64
            d['config']=h.hex();d['sacr']='fc3f0000'
        r=audit(self.data)
        self.assertTrue(all(x['secondary_reset_asserted'] and x['external_grants_disabled'] for x in r['samples']))
        for key in ('permanent_scsi_exclusion_proven','aau_ownership_proven','new_ram_grant'):
            self.assertFalse(r[key])
if __name__=='__main__':unittest.main()
