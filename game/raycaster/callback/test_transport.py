#!/usr/bin/env python3
"""The polling candidate must change exactly one literal in the accepted driver."""
import tempfile
from pathlib import Path
from build_transport import build
with tempfile.TemporaryDirectory() as d:
 root=Path(d);build(root/'base');build(root/'fast',True)
 base=root/'base';fast=root/'fast'
 assert {p.name for p in base.iterdir()}=={p.name for p in fast.iterdir()}
 for p in base.iterdir():
  if p.name=='callback-transport.json':continue
  a=p.read_bytes();b=(fast/p.name).read_bytes()
  if p.name=='dac960rtems.c':
   old=b'output & 1, 50, WAIT_US);';new=b'output & 1, 20, WAIT_US);'
   assert a.count(old)==1 and a.replace(old,new)==b
   assert b'#define WAIT_US 2000000u' in b
  else:assert a==b,p.name
 print('PASS: only ODB polling interval changes; deadline, validation and transaction sources identical')
