#!/usr/bin/env python3
"""Fault-path tests for reversible host changes; actual routing tested separately."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import public_ipv6 as p
class Routing(unittest.TestCase):
 def test_rollback_and_success(self):
  for fail in (False,True):
   with tempfile.TemporaryDirectory() as d:
    calls=[];present=False
    def run(*args):
     nonlocal present
     calls.append(args)
     if args[:4]==('ip','-j','-6','addr'):
      a=[dict(local='2a02:8106:40:9000::1',prefixlen=64,scope='global')]
      if present:a.append(dict(local='2a02:8106:40:9000::960',prefixlen=128,scope='global',dadfailed=fail))
      return json.dumps([dict(addr_info=a)])
     if args[:4]==('ip','-6','addr','add'):present=True
     if args[:4]==('ip','-6','addr','del'):present=False
     if args==('ip','-j','link','show'):return '[{"ifname":"lan"},{"ifname":"tun"},{"ifname":"lo"}]'
     if args[:3]==('nft','-j','list'):return '{"nftables":[]}'
     if args[:2]==('sysctl','-n'):return '0'
     return ''
    with patch.object(p,'STATE',Path(d)/'state'),patch.object(p,'run',run),patch.object(p.subprocess,'run') as nft:
     if fail:
      with self.assertRaisesRegex(RuntimeError,'duplicate'):p.apply('2a02:8106:40:9000::960','lan','tun')
      nft.assert_not_called()
     else:
      s=p.apply('2a02:8106:40:9000::960','lan','tun');self.assertTrue(s['proxy'])
      self.assertIn('tcp dport 80 accept',nft.call_args.kwargs['input'])
      self.assertNotIn('9600',nft.call_args.kwargs['input'])
      with self.assertRaisesRegex(RuntimeError,'existing routing'):p.apply('2a02:8106:40:9000::960','lan','tun')
      p.remove()
     self.assertFalse(p.STATE.exists());self.assertFalse(present)
     self.assertNotIn(('ip','-6','route','flush'),calls)
 def test_reject_non_global(self):
  with self.assertRaises(ValueError):p.apply('fd96::2','lan','tun')
if __name__=='__main__':unittest.main()
