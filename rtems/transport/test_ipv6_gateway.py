#!/usr/bin/env python3
"""Unprivileged IPv6 journal/rollback tests; no real networking is modified."""
import json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import ipv6_gateway as gateway
class GatewayTests(unittest.TestCase):
 def exercise(self,fail_at=None):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);conf=out/'conf';rules=set();installed=0
   before={'all/forwarding':'0','default/forwarding':'0','uplink0/forwarding':'0','lo/forwarding':'1','uplink0/accept_ra':'0'}
   for rel,value in before.items():
    path=conf/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value+'\n')
   def command(*args):
    nonlocal installed
    if args==('ip','-6','-j','route'):return json.dumps([dict(dst='default',dev='uplink0')])
    if args[0]=='ip6tables-save':return ''
    if args[0]=='ip':return ''
    assert args[0]=='ip6tables' and args[3]=='-I';undo=list(args);undo[3]='-D';rules.add(tuple(undo));installed+=1
    if fail_at==installed:raise RuntimeError('injected failure after rule installation')
    return ''
   def run(args,**kwargs):
    assert args[0]=='ip6tables' and args[3] in ('-C','-D')
    deletion=list(args);deletion[3]='-D';key=tuple(deletion);exists=key in rules
    if args[3]=='-D':rules.discard(key)
    return subprocess.CompletedProcess(args,0 if exists else 1)
   with patch.object(gateway,'CONF',conf),patch.object(gateway,'command',command),patch.object(gateway.subprocess,'run',run):
    if fail_at:
     with self.assertRaises(RuntimeError):gateway.IPv6Gateway(out,True)
    else:
     instance=gateway.IPv6Gateway(out,True)
     self.assertEqual((conf/'all/forwarding').read_text(),'1\n');self.assertEqual((conf/'uplink0/accept_ra').read_text(),'2\n');self.assertEqual(len(rules),4)
     instance.close();gateway.cleanup(out) # Idempotent replay after close.
    self.assertFalse(rules)
    self.assertEqual({rel:(conf/rel).read_text().strip() for rel in before},before)
 def test_normal_and_idempotent(self):self.exercise()
 def test_each_rule_install_failure(self):
  for n in range(1,5):
   with self.subTest(boundary=n):self.exercise(n)
 def test_foreign_rule_rejected_before_mutation(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);gateway.journal(out/'ipv6-gateway-journal.json',dict(uplink='uplink0',undo=[['ip6tables','-F']],sysctls=[]))
   with patch.object(gateway.subprocess,'run') as run:
    with self.assertRaises(ValueError):gateway.cleanup(out)
    run.assert_not_called()
if __name__=='__main__':unittest.main()
